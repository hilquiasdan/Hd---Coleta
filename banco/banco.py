"""Etapa 6: SQLite com hash único do enunciado (sem acento/espaço/maiúscula) + exportação JSON para o site."""
import os, json, sqlite3, hashlib, re
from comum import RAIZ, norm
DB = os.path.join(RAIZ, 'banco.sqlite')
def con():
    c = sqlite3.connect(DB)
    c.executescript('''CREATE TABLE IF NOT EXISTS questoes(id INTEGER PRIMARY KEY, hash_enunciado TEXT UNIQUE, banca TEXT, ano INT, orgao TEXT, cargo TEXT,
      materia TEXT, texto_base TEXT, comando TEXT, enunciado TEXT, tipo TEXT, alternativas TEXT, resposta TEXT, url_fonte TEXT, origem TEXT DEFAULT 'real',
      prova_id TEXT, numero INT, status TEXT DEFAULT 'ok');
      CREATE TABLE IF NOT EXISTS revisar(id INTEGER PRIMARY KEY, motivo TEXT, dados TEXT);''')
    return c
def hash_q(enunciado, alternativas=()):
    return hashlib.sha1((norm(enunciado) + '|' + '|'.join(norm(a) for a in alternativas)).encode()).hexdigest()
def grava(c, q):
    """q: dict com os campos da tabela. Devolve 'novo' | 'duplicata' | 'conflito'"""
    h = hash_q(q['enunciado'], q.get('alternativas') or [])
    r = c.execute('SELECT resposta FROM questoes WHERE hash_enunciado=?', (h,)).fetchone()
    if r:
        if r[0] != q['resposta']:
            c.execute('INSERT INTO revisar(motivo,dados) VALUES(?,?)', ('gabaritos diferentes em duas fontes', json.dumps(q, ensure_ascii=False)))
            c.execute("UPDATE questoes SET status='revisar' WHERE hash_enunciado=?", (h,)); return 'conflito'
        return 'duplicata'
    c.execute('''INSERT INTO questoes(hash_enunciado,banca,ano,orgao,cargo,materia,texto_base,comando,enunciado,tipo,alternativas,resposta,url_fonte,origem,prova_id,numero)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (h, q['banca'], q.get('ano'), q.get('orgao'), q.get('cargo'), q['materia'], q.get('texto_base', ''), q.get('comando', ''),
      q['enunciado'], q['tipo'], json.dumps(q.get('alternativas') or [], ensure_ascii=False), q['resposta'], q.get('url_fonte', ''), q.get('origem', 'real'), q['prova_id'], q.get('numero')))
    return 'novo'
def importa_site(c, arq):
    """traz as questões que o site já tem, para não duplicar"""
    D = json.load(open(arq)); n = 0
    for pid, v in D.items():
        ctx = v['j'].get('ctx', [])
        for q in v['j']['q']:
            tb = ctx[q['c']] if q.get('c') is not None and q['c'] < len(ctx) else ''
            r = grava(c, {'banca': v['banca'], 'ano': v.get('ano'), 'orgao': v.get('orgao'), 'cargo': v.get('cargo'), 'materia': q['d'], 'texto_base': tb,
                          'enunciado': q.get('t') or q.get('e'), 'tipo': 'certo_errado' if v.get('tipo') == 'CE' else 'multipla', 'alternativas': q.get('a') or [],
                          'resposta': q['g'], 'url_fonte': 'site', 'prova_id': pid, 'numero': q.get('n')})
            n += r == 'novo'
    c.commit(); return n
def exporta(c, arq, meta):
    """Só as questões novas (as do site continuam como estão), no formato da aba 'Questões Cebraspe' do site (filtros por banca/prova/matéria e sorteio já existem lá)."""
    out = {}
    for row in c.execute("SELECT prova_id,banca,ano,orgao,cargo,materia,texto_base,enunciado,tipo,alternativas,resposta,numero FROM questoes WHERE status='ok' AND url_fonte!='site' ORDER BY prova_id,numero"):
        pid, banca, ano, org, cg, mat, tb, en, tipo, alts, resp, n = row
        m = meta.get(pid, {})
        p = out.setdefault(pid, {'titulo': m.get('titulo') or cg, 'orgao': org, 'cargo': cg, 'ano': ano, 'tipo': 'CE' if tipo == 'certo_errado' else 'ME',
                                 'ordem': m.get('ordem', 500), 'banca': banca, 'gt': m.get('gt', 'definitivo'), 'total': 0, 'j': {'ctx': [], 'q': []}})
        ci = None
        if tb:
            if tb not in p['j']['ctx']: p['j']['ctx'].append(tb)
            ci = p['j']['ctx'].index(tb)
        item = {'n': n, 'd': mat, 'g': resp, 'c': ci}
        if tipo == 'certo_errado': item['t'] = en
        else: item['e'] = en; item['a'] = json.loads(alts)
        p['j']['q'].append(item); p['total'] += 1
    json.dump(out, open(arq, 'w'), ensure_ascii=False, separators=(',', ':')); return out
