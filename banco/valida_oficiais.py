# Auditoria automática do banco de questões oficiais antes de publicar.
# Remove o que estiver quebrado e imprime só o resumo. Uso: python3 valida_oficiais.py [--so-ver]
import json, re, sys, collections
SITE = '/home/claude/hd-site/fonte/dados/oficiais.json'; ART = '/home/claude/estudo_pppe/site_v2/oficiais.json'
OK_D = {'Execução Penal', 'Direito Penal', 'Direito Processual Penal', 'Direito Constitucional', 'Direito Administrativo', 'Legislação Especial',
        'Noções de Direitos Humanos e Participação Social', 'Ética no Serviço Público', 'Língua Portuguesa', 'Noções de Informática',
        'Raciocínio Lógico', 'Conhecimentos Gerais', 'Legislação Estadual'}            # as três últimas existem só nas provas antigas de polícia penal
LIXO = re.compile(r'pcimark|pciconcursos|CEBRASPE –|Edital:|Aplicação:|www\.|RASCUNHO|Dados da quest[ãa]o|Alternativa correta\s*:|Coment[áa]rio do professor|\|\|', re.I)
ESP = re.compile(r'\b(del|los|las|según|cuál|ellos|pero|muy|hay)\b', re.I)
def problema(v, q):
    ce = v.get('tipo') == 'CE'; t = q.get('t') if ce else q.get('e')
    if not t or len(t.strip()) < 20: return 'enunciado vazio/curto'
    if q.get('d') not in OK_D: return 'matéria fora da lista'
    if ce and q.get('g') not in ('C', 'E'): return 'gabarito inválido'
    if not ce:
        a = q.get('a') or []
        if len(a) < 4 or any(not (x or '').strip() for x in a): return 'alternativas incompletas'
        nz = [re.sub(r'\W', '', x.lower()) for x in a]
        if all(nz) and len(set(nz)) < len(nz): return 'alternativas repetidas'
        if q.get('g') not in 'ABCDE'[:len(a)]: return 'gabarito fora das alternativas'
    c = q.get('c')
    if c is not None and (not isinstance(c, int) or c >= len(v['j'].get('ctx', []))): return 'texto-base inexistente'
    tudo = t + ' ' + ' '.join(q.get('a') or [])
    if LIXO.search(tudo): return 'lixo de página/site'
    if len(ESP.findall(tudo)) >= 4: return 'outra língua'
    if re.search(r'\((?:R|ℓ|l|L)\.\s?\d|\b(?:R|ℓ)\.\s?\d|\blinhas?\s\d', t, re.I) and c is None: return 'cita linha sem texto'
    if re.search(r'\b(no|do|o) texto\b|\btrecho\b', t, re.I) and c is None and q.get('d') == 'Língua Portuguesa': return 'português sem o texto'
    return ''
D = json.load(open(SITE)); cont = collections.Counter(); prov = collections.Counter(); ex = {}
for pid, v in list(D.items()):
    if not v.get('orgao') and not v.get('titulo'): prov['prova sem nome'] += 1
    if v.get('ano') and not (1995 <= int(v['ano']) <= 2027): prov['ano estranho'] += 1
    keep = []
    for q in v['j']['q']:
        m = problema(v, q)
        if m: cont[m] += 1; ex.setdefault(m, (pid, q.get('n'), (q.get('t') or q.get('e') or '')[:90]))
        else: keep.append(q)
    v['j']['q'] = keep; v['total'] = len(keep)
    if len(keep) < 3: del D[pid]; prov['prova removida (sobrou quase nada)'] += 1
print('problemas:', dict(cont)); print('provas:', dict(prov))
for m, e in list(ex.items())[:6]: print('  ex.', m, '|', e)
print('total depois:', sum(len(v['j']['q']) for v in D.values()), 'em', len(D), 'provas')
if '--so-ver' not in sys.argv:
    s = json.dumps(D, ensure_ascii=False, separators=(',', ':')); open(SITE, 'w').write(s); open(ART, 'w').write(s)
