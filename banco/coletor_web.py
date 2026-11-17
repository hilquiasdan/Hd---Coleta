"""Etapa 2: coletores de sites de questões (um módulo por site, mesmo formato de saída).
Hoje nenhum site de questões está ativo: os candidatos testados exigem login, são pagos ou bloqueiam robôs/captcha
(QConcursos, TEC, Gran, Aprova, Questões Estratégicas, PCI). Para ativar um site que permita coleta, crie uma função
que devolva itens no formato: {enunciado, texto_base, alternativas, resposta, banca, ano, orgao, cargo, materia, url_fonte}."""
SITES = {}
def coleta(site): return SITES[site]() if site in SITES else []
