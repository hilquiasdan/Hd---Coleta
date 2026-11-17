# HD Concursos · coleta de provas oficiais

Robôs de coleta de provas e gabaritos **públicos** de bancas de concurso, com extração das questões,
conferência do gabarito e classificação por matéria. Também gera comentários de gabarito com uma IA
local e gratuita (Ollama), com travas de verificação. Não contém material pago nem dados de alunos.

- `banco/` — scripts (ver `banco/README.md`)
- `.github/workflows/coleta.yml` — coleta por banca, com continuação automática; disparo por `banco/lote.txt`
- `.github/workflows/comenta.yml` — comentários de gabarito; disparo por `banco/comenta_pedido.txt`

Regras: respeita robots/limites, espera de 2 a 5 s entre pedidos, não passa por login, captcha ou paywall
e para ao receber 403/429.
