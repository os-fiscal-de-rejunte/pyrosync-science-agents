# PyroSync — agentes científicos

Orquestração para responder perguntas sobre focos de calor em um país ou região usando evidências obtidas da API PyroSync. A resposta separa observações, previsão experimental, fontes indisponíveis e limitações. O texto é pensado para ser compreensível por pessoas sem formação técnica.

## Fluxo

1. **Observação histórica:** consulta o calendário FIRMS e identifica o intervalo efetivamente retornado, por sensor.
2. **Contexto temporal:** compara o mesmo intervalo em anos anteriores quando os produtos estão disponíveis. A comparação é exploratória e não garante observação sem nuvens.
3. **Previsão e clima:** consulta a saída do modelo existente por célula e preserva sua condição e seus avisos.
4. **Focos harmonizados:** consulta uma amostra do banco, restrita ao alcance das cargas. Quando o filtro regional não é compatível, informa a indisponibilidade.
5. **Revisão científica:** acrescenta limites sobre cobertura, sensores, paginação, calibração e ausência de dados.
6. **Síntese:** um provedor de linguagem pode explicar os dados; a resposta deve referenciar fontes existentes e passar por verificações simples. Sem aprovação, as evidências permanecem acessíveis.

Os agentes executam funções com ferramentas restritas; não têm acesso genérico à internet nem ao banco de relatos comunitários. O provedor de linguagem recebe apenas a pergunta, o território e as evidências públicas necessárias. Não recebe credenciais de banco ou relatos.

## Limitações científicas

- O calendário global consulta diretamente o NASA FIRMS: não equivale a uma série harmonizada.
- Detectar calor não é o mesmo que contar incêndios distintos. Ausência de detecções não prova ausência de fogo ou observação sem nuvens.
- A comparação histórica é exploratória; diferenças entre satélites, processamento, cobertura e condições atmosféricas podem alterar os números. Não declara causalidade ou anomalia validada.
- A previsão de fora do piloto MATOPIBA é extrapolação experimental e não calibrada globalmente. Um valor de célula não é uma probabilidade para todo o país nem um alerta operacional.
- A síntese de linguagem pode errar. A verificação automática limita fontes e números, mas não garante que cada frase esteja correta.

## Uso

```python
import asyncio
from datetime import date
from pyrosync_science import analyze

resultado = asyncio.run(analyze(
    "https://pyrosync-api.onrender.com", "Brazil", None,
    date(2025, 8, 1), date(2025, 8, 5), "O que os dados mostram?"
))
```

Configure `GROQ_API_KEY` ou `GEMINI_API_KEY` somente no servidor. Sem chave ou se a síntese falhar, o resultado traz as evidências e indica o erro; nenhuma chave deve entrar em Git ou no navegador. A API de linguagem pode ter limites e custos conforme a conta configurada.

Fontes: [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/), [NASA POWER](https://power.larc.nasa.gov/) e [API PyroSync](https://pyrosync-api.onrender.com/docs).
