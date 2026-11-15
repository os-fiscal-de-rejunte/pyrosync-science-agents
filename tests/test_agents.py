import asyncio
import json
from datetime import date

from pyrosync_science import agents


def test_review_preserves_important_scientific_limits():
    notes = agents.review_evidence({"camada": "firms_consulta_direta", "proximo_inicio": "2025-01-06"},
                                   {"status": "experimental"}, {"features": []})
    assert any("não foi harmonizado" in item for item in notes)
    assert any("primeira página" in item for item in notes)
    assert any("não calibrada" in item for item in notes)
    assert any("não demonstra ausência" in item for item in notes)


def test_rejects_unreferenced_ai_claim(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "dummy-for-test")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": json.dumps({"resposta": "Uma resposta sem suporte por fontes.", "fontes": ["X"]})}}]}

    class Client:
        async def post(self, *args, **kwargs):
            return Response()

    result, error = asyncio.run(agents.synthesize(Client(), "Brazil", "O que aconteceu?", {"C": {}}))
    assert result is None and "revisão" in error


def test_rejects_ai_numerical_claims(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "dummy-for-test")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": json.dumps({"resposta": "Foram detectados 999 focos nesta região.", "fontes": ["C"]})}}]}

    class Client:
        async def post(self, *args, **kwargs):
            return Response()

    result, _ = asyncio.run(agents.synthesize(Client(), "Brazil", "O que aconteceu?", {"C": {}}))
    assert result is None


def test_missing_sensor_is_not_treated_as_zero(monkeypatch):
    async def get_json(client, path, params):
        return ({"resultado_completo": True, "disponibilidade": [{"instrumento": "MODIS", "disponivel": True}], "registros": []}, None)
    monkeypatch.setattr(agents, "get_json", get_json)
    result = asyncio.run(agents.compare_history("https://example.org", "Brazil", None,
                                                date(2025, 1, 1), date(2025, 1, 5), "VIIRS"))
    assert all(period["deteccoes"] is None for period in result["periodos"])


def test_deterministic_fallback_never_invents_values():
    evidence = {"C": {"registros_por_sensor": [{"sensor_family": "MODIS", "deteccoes": 3}]},
                "P": {"celulas": []}, "B": {"periodos": []}}
    result = agents.deterministic_summary(evidence)
    assert "3 registros MODIS" in result["texto"]
    assert "não confirma uma anomalia" in result["texto"]
    assert result["fontes"] == ["C", "P", "B"]
