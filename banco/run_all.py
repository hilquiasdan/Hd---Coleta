"""Roda o pipeline inteiro: coleta -> extração -> gabarito -> classificação -> banco -> JSON do site + relatório.
Uso: python run_all.py [site ...]     TESTE=1 -> 2 provas e 20 questões por site.   SO_PROCESSA=1 -> usa só o cache."""
import os, sys, re, json, collections, random, yaml, hashlib
from comum import RAIZ, TESTE, baixa, Bloqueado
import coletor_pdf, extrator, gabarito, classificador, banco
sys.path.insert(0, os.path.join(RAIZ, 'lib')); import outras
from monta import SUSP
F = yaml.safe_load(open(os.path.join(RAIZ, 'fontes.yaml')))
SITES = sys.argv[1:] or [k for k, v in F.items() if v.get('ativo', True)]
CARGO_POL = re.compile(r'AGENTE|ESCRIV|POLIC|SOLDADO|PAPILOS|INVESTIG|INSPETOR|GUARDA|PENITENC|PENAL|T[ÉE]CNICO|AUXILIAR|ASSISTENTE|BOMBEIRO|OFICIAL', re.I)
TI_AVANCADA = re.compile(r'python|\bsql\b|minera[çc][ãa]o de dados|\bpaas\b|\biaas\b|kubernetes|docker|machine learning|big data|rede neural|algoritmo|banco de dados|\bjava\b|\btcp\b|\budp\b|\bvlan|roteador|protocolo', re.I)
CARGO_FORA = re.compile(r'PERITO|PSIC[ÓO]LOG|DENTISTA|M[ÉE]DIC|ENFERM|CIENT[ÍI]FICA|APOIO ESPECIALIZADO|TECNOLOGIA|ENGENH|CONTAB|ESTAT[ÍI]ST|ARQUITET|PROFESSOR|PEDAGOG', re.I)
def titulo(s):
    pq = {'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'a', 'o'}; w = re.sub(r'\s+', ' ', s.strip()).lower().split(' ')
    return ' '.join(x if (i and x in pq) else x[:1].upper() + x[1:] for i, x in enumerate(w) if x)
def nome_cargo(desc):
    m = re.search(r'::\s*(.+)$', desc)
    x = m.group(1) if m and m.group(1).strip() else desc
    x = re.sub(r'CARGO\s*:?\s*\d*\s*[:–-]?|\(?ADAPTADA\)?|caderno( de)? provas?|provas? objetivas?|conhecimentos (b[áa]sicos|gerais|espec[íi]ficos)|\(P\d\)|tipo\s*\w+|\.pdf|[_]+|\s-\s', ' ', x, flags=re.I)
    return titulo(re.sub(r'\s+', ' ', x).strip(' –-:()'))[:80]
def ok_item(it, tipo, mat, cargo):
    t = it['enunciado'] + ' ' + ' '.join(it.get('alternativas', [])); tb = it.get('texto_base', '')
    if outras.RUIM.search(t + ' ' + tb) or SUSP.search(it['enunciado']) or re.search(r'ℓ\.?\s?\d|\((?:R|ℓ|l|L)\.\s?\d|\blinhas?\s\d', t, re.I): return 'figura/linha do texto'
    if len(it['enunciado']) < 25 or len(it['enunciado']) > 1200: return 'item cortado'
    if re.search(r'Dados da quest[ãa]o|Alternativa correta\s*:|Coment[áa]rio do professor|Resolu[çc][ãa]o comentada', t, re.I): return 'texto de site misturado'
    if len(re.findall(r'\b(del|los|las|según|cuál|también|está|ellos|una|pero|muy|hay)\b', t, re.I)) >= 4 and not re.search(r'\b(não|são|também|está|uma)\b', t): return 'outra língua'
    if tipo == 'certo_errado' and (not re.search(r'[.?!)”"]$', it['enunciado'].strip()) or (re.match(r'^[a-zà-ú]', it['enunciado']) and not re.search(r'[:,]\s*$', tb.strip()))): return 'item cortado'
    if tipo == 'multipla' and len(it.get('alternativas', [])) < 4: return 'alternativas incompletas'
    if mat == 'Língua Portuguesa' and (len(tb) < 400 if tipo == 'certo_errado' else (re.search(r'\btexto\b|trecho', it['enunciado'], re.I) and len(tb) < 300)): return 'português sem o texto'
    if mat == 'Noções de Informática' and (not CARGO_POL.search(cargo) or TI_AVANCADA.search(t)): return 'informática fora do nível'
    return ''
def processa(site, rel, c, meta, exemplos):
    arq = os.path.join(RAIZ, 'coleta', site + '.json')
    if not os.path.exists(arq): return
    S = json.load(open(arq)); banca = S['banca']; R = rel[site]; R['aviso'] = S.get('aviso', ''); gravadas = 0
    PARTE = int(os.environ.get('PARTE', '0')); PARTES = int(os.environ.get('PARTES', '1'))
    for ic, cc in enumerate(S['concursos']):
        if PARTES > 1 and ic % PARTES != PARTE: continue  # processamento dividido em partes paralelas
        provas = [f for f in cc['arquivos'] if f['tipo'] == 'prova']; gabs = [f for f in cc['arquivos'] if f['tipo'] == 'gab']
        cands = []
        for g in gabs:
            try: b = baixa(g['url'], True)
            except Bloqueado: b = None
            if not b: continue
            try: pg = extrator.paginas(b)
            except Exception: continue
            cands += [(rot, d, g['desc']) for rot, d in gabarito.versoes(g['url'], pg)]
        for p in provas[: (2 if TESTE else None)]:
            cargo = nome_cargo(p['desc']) or titulo(cc['nome'])[:60]
            if CARGO_FORA.search(cargo + ' ' + p['desc']): R['provas fora do perfil'] += 1; continue
            try: b = baixa(p['url'], True); pg = extrator.paginas(b) if b else None
            except Exception: pg = None
            if not pg: R['provas com falha'] += 1; R['falha: PDF ilegível'] += 1; continue
            tipo, its, mx = extrator.itens(p['url'], pg, banca)
            if tipo == 'multipla': its = [i for i in its if len(i.get('alternativas', [])) >= 4]
            if not its: R['provas com falha'] += 1; R['falha: itens não separados'] += 1; continue
            nums = [i['n'] for i in its]; gab, motivo = gabarito.escolhe(tipo, nums, p['url'], p['desc'], cands)
            if not gab: R['provas com falha'] += 1; R['falha: ' + motivo] += 1; continue
            if len(its) < 0.9 * max(gab): R['provas com falha'] += 1; R['falha: menos de 90% dos itens extraídos'] += 1; continue
            pid = re.sub(r'[^a-z0-9]+', '_', (banca + '_' + cc['id']).lower())[:50] + '_' + hashlib.md5(p['url'].encode()).hexdigest()[:5]
            meta[pid] = {'titulo': cargo}; R['provas aproveitadas'] += 1
            for it in its:
                R['itens coletados'] += 1; resp = gab.get(it['n'])
                if resp not in (('C', 'E') if tipo == 'certo_errado' else tuple('ABCDE')): R['itens sem gabarito/anulados'] += 1; continue
                mat = classificador.classifica(it)
                if mat is None: R['fora das matérias do curso'] += 1; continue
                if mat == 'revisar':
                    c.execute('INSERT INTO revisar(motivo,dados) VALUES(?,?)', ('matéria não identificada', json.dumps({**it, 'resposta': resp, 'url': p['url']}, ensure_ascii=False))); R['itens em revisar'] += 1; continue
                m = ok_item(it, tipo, mat, cargo)
                if m: R['descartado: ' + m] += 1; continue
                if TESTE and gravadas >= 20: continue
                r = banco.grava(c, {'banca': banca, 'ano': cc.get('ano'), 'orgao': titulo(cc['nome'])[:90], 'cargo': cargo, 'materia': mat, 'texto_base': it.get('texto_base', ''),
                                    'comando': it.get('comando', ''), 'enunciado': it['enunciado'], 'tipo': tipo, 'alternativas': it.get('alternativas'), 'resposta': resp,
                                    'url_fonte': p['url'], 'prova_id': pid, 'numero': it['n']})
                R[{'novo': 'gravadas', 'duplicata': 'duplicatas ignoradas', 'conflito': 'itens em revisar'}[r]] += 1
                if r == 'novo':
                    gravadas += 1
                    if len(exemplos[site]) < 3 and random.random() < 0.3: exemplos[site].append({'materia': mat, 'resp': resp, 'enunciado': it['enunciado'][:220], 'alts': [a[:60] for a in it.get('alternativas', [])][:5]})
        c.commit()
if __name__ == '__main__':
    if os.environ.get('SO_PROCESSA') != '1':
        for s in SITES: coletor_pdf.coleta(s, F[s])
    c = banco.con()
    if c.execute('SELECT COUNT(*) FROM questoes').fetchone()[0] == 0 and os.path.exists(os.path.join(RAIZ, 'site_atual.json')):
        print('importadas do site:', banco.importa_site(c, os.path.join(RAIZ, 'site_atual.json')))
    rel = collections.defaultdict(collections.Counter); meta = {}; exemplos = collections.defaultdict(list)
    for s in SITES: processa(s, rel, c, meta, exemplos)
    out = banco.exporta(c, os.path.join(RAIZ, os.environ.get('SAIDA', 'saida_novas.json')), meta)
    resumo = {s: dict(r) for s, r in rel.items()}
    json.dump({'resumo': resumo, 'exemplos': exemplos, 'provas_novas': len(out), 'questoes_novas': sum(v['total'] for v in out.values())}, open(os.path.join(RAIZ, os.environ.get('RELATORIO', 'relatorio.json')), 'w'), ensure_ascii=False, indent=1)
    for s, r in resumo.items(): print(s, json.dumps(r, ensure_ascii=False))
    print('novas no JSON do site:', sum(v['total'] for v in out.values()), 'em', len(out), 'provas')
