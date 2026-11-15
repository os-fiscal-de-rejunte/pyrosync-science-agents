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


def test_qualitative_evidence_preserves_availability_without_numbers():
    evidence = {
        "C": {"registros_por_sensor": [{"sensor_family": "VIIRS", "deteccoes": 42},
                                        {"sensor_family": "MODIS", "deteccoes": 0}],
              "resultado_completo": True},
        "B": {"periodos": [{"deteccoes": None}]},
        "P": {"celulas": [{"probabilidade_condicional": 0.75}]},
        "H": {"quantidade_na_amostra": 0},
    }
    result = agents.qualitative_evidence(evidence)
    assert result["C"]["sensores_com_registros"] == ["VIIRS"]
    assert result["C"]["registros_retornados"] is True
    assert result["B"]["comparacao_disponivel"] is False
    assert result["P"]["celulas_disponiveis"] is True
    assert result["H"]["registros_na_amostra"] is False
    assert not any(char.isdigit() for char in json.dumps(result, ensure_ascii=False))


def test_provider_receives_qualitative_evidence_and_sanitized_question(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "dummy-for-test")
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": json.dumps({
                "resposta": "As observações indicam registros de calor na página consultada.",
                "fontes": ["C"],
            })}}]}

    class Client:
        async def post(self, *args, **kwargs):
            captured.update(json.loads(kwargs["json"]["messages"][1]["content"]))
            return Response()

    evidence = {"C": {"registros_por_sensor": [{"sensor_family": "VIIRS", "deteccoes": 42}]}}
    result, error = asyncio.run(agents.synthesize(Client(), "Brazil", "O que aconteceu em 2025?", evidence))
    assert error is None and result["provedor"] == "Groq"
    assert "2025" not in captured["pergunta"]
    assert "42" not in json.dumps(captured["evidencias"])
