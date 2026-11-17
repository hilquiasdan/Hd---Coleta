"""Etapa 3: PDF -> páginas com posição (PyMuPDF) -> itens separados pela numeração.
Cebraspe Certo/Errado: cada item guarda o texto-base e o comando. Múltipla escolha: enunciado + alternativas A-E."""
import os, sys, re, fitz
from comum import RAIZ
sys.path.insert(0, os.path.join(RAIZ, 'lib'))
import parse, me2, gab as gabm, gab2
from monta import limpa, comando, blocos
X = {}
for m in (parse, me2, gabm, gab2): m.X = X
def paginas(pdf):
    doc = fitz.open(stream=pdf, filetype='pdf'); out = []
    for pg in doc:
        d = pg.get_text('dict'); ls = {}
        for b in d['blocks']:
            for l in b.get('lines', []):
                for s in l['spans']:
                    t = s['text']
                    if not t: continue
                    y = round(s['origin'][1]); k = next((k for k in ls if abs(k - y) <= 2), y)
                    bold = 1 if (s['flags'] & 16 or re.search(r'bold|black|heavy|semibold', s['font'], re.I)) else 0
                    ls.setdefault(k, []).append([round(s['origin'][0], 1), round(s['size']), bold, t, round(s['bbox'][2] - s['bbox'][0], 1)])
        out.append({'w': round(pg.rect.width), 'l': [[y, sorted(v)] for y, v in sorted(ls.items())]})
    return out
def texto(nome, n=2):
    return ' '.join(' '.join(s[3] for s in segs) for P in X[nome][:n] for y, segs in P['l'])
def itens(nome, pags, banca):
    """devolve (tipo, lista de itens, maior número lido)"""
    X[nome] = pags
    if banca == 'Cebraspe':
        try:
            it, cx = parse.parse_ce([nome])
            if len(it) >= 20:
                out = []
                for n in sorted(it):
                    i = it[n]; tb = cx[i['c']] if i['c'] is not None else ''
                    t = blocos([x for x in i['ls'] if not x.startswith('\n')]) + ''.join(x for x in i['ls'] if x.startswith('\n'))
                    out.append({'n': n, 'enunciado': t, 'texto_base': limpa(tb), 'comando': comando(tb) if tb else '', 'sec': ''})
                return 'certo_errado', out, max(it)
        except Exception: pass
        # múltipla escolha da Cebraspe: prova e gabarito definitivo vêm do mesmo CDN (caderno matriz). Conferido em SERES/PE 2017: 52 de 52.
        # Se houver mais de um gabarito diferente para a mesma prova, gabarito.escolhe recusa (versão ambígua).
        try: qs, T = parse.parse_me(nome)
        except Exception: return None, [], 0
        out = []
        for n in sorted(qs):
            q = qs[n]; alts = [limpa(parse.junta(q['a'].get(L, []))) for L in 'ABCDE']
            if not all(alts): continue
            e = blocos(q['e']); ref = re.findall(r'texto ([A-Z0-9]+[A-Z0-9-]*)', e); tb = T.get(ref[0], '') if ref else ''
            if ref and not tb: continue
            out.append({'n': n, 'enunciado': e, 'alternativas': alts, 'texto_base': limpa(tb), 'comando': '', 'sec': ''})
        return ('multipla', out, max(qs)) if len(out) >= 20 else (None, [], 0)
    try: qs = me2.parse(nome)
    except Exception: return None, [], 0
    out = []
    for n in sorted(qs):
        q = qs[n]; alts = [limpa(me2.junta(q['a'].get(L, []))) for L in 'ABCDE']
        e = blocos(q['e'])
        tb = q.get('ctx', '') if re.search(r'\btexto\b|trecho|fragmento|excerto|poema|cr[ôo]nica|artigo', e, re.I) else ''
        out.append({'n': n, 'enunciado': e, 'alternativas': [a for a in alts if a], 'texto_base': limpa(tb), 'comando': '', 'sec': q.get('sec', '')})
    return 'multipla', out, (max(qs) if qs else 0)
