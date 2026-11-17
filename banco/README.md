# Banco de questões HD (coleta automática)

Pipeline em Python, sem IA: `coletor_pdf.py` → `extrator.py` → `gabarito.py` → `classificador.py` → `banco.py`, tudo chamado por `run_all.py`.
Saídas: `banco.sqlite` (todas as questões), `saida_novas.json` (questões novas no formato do site) e `relatorio.json` (relatório por fonte).

## Rodar
    pip install requests beautifulsoup4 pyyaml pymupdf pytest
    TESTE=1 python run_all.py fgv aocp      # teste: 2 provas e 20 questões por site
    python run_all.py                       # todas as fontes de fontes.yaml
    python -m pytest testes -q              # testes dos extratores

## Adicionar uma banca ou concurso
1. Em `fontes.yaml`, copie um bloco `tipo: rastreio` e ajuste `inicio` (página que lista os concursos), `dominio` e `seguir` (regex dos links a seguir).
2. Confira o robots.txt do site e se ele não pede login nem captcha (o coletor para sozinho em 403/429/captcha).
3. Rode com `TESTE=1` e veja o `relatorio.json` antes de rodar em lote.
Matérias e palavras de cabeçalho ficam em `materias.yaml`.

## Agendar toda semana
Já está agendado no GitHub Actions (`.github/workflows/banco.yml`, toda segunda às 3h): roda o pipeline, guarda o banco e o relatório no branch `coleta-provas`.
Para mudar o horário, edite a linha `cron`. Para rodar na hora: aba Actions → banco-questoes → Run workflow.

## Regras
Pausa de 2–5 s entre requisições, cache local (nunca baixa a mesma URL duas vezes), para em 403/429/captcha, não coleta comentários nem resoluções,
não entra em login nem paywall. Prova com menos de 90% dos itens extraídos é marcada como falha; mesma questão com gabaritos diferentes vai para `revisar`.
