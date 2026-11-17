"""Etapa 4: cruza itens e gabarito definitivo (escolhe a versão certa do caderno) e descarta anulados."""
import re
from extrator import X, gabm, gab2, texto
TOK = re.compile(r'TIPO[\s_-]*0?(\d)\b|CADERNO[\s_-]*0?(\d{1,2})\b|VERS[ÃA]O[\s_-]*(\d|[A-D])\b|PROVA[\s_-]+(\d)\b', re.I)
def tokens(s): return {next(g for g in m.groups() if g).upper() for m in TOK.finditer(s or '')}
def versoes(nome, pags):
    X[nome] = pags; vs = []
    try: vs += [(l, d) for l, d in gab2.versoes(nome)]
    except Exception: pass
    try:
        d = gabm.gab(nome)
        if len(d) >= 10: vs.append(('(único) ' + nome, d))
    except Exception: pass
    return vs
def cargo_num(s):
    m = re.search(r'CARGO\s*:?\s*0*(\d+)', s or '', re.I); return m.group(1) if m else None
def escolhe(tipo, nums, nome_prova, desc_prova, cands):
    """cands: [(rotulo, dict, desc_arquivo)] -> (gabarito, motivo)"""
    validos = set('CEX') if tipo == 'certo_errado' else set('ABCDEX')
    bons = []
    for rot, d, dsc in cands:
        if not d: continue
        cov = sum(1 for n in nums if d.get(n) in validos) / max(1, len(nums))
        if cov >= 0.9 and abs(max(d) - max(nums)) <= 2: bons.append((rot, d, dsc))
    if not bons: return None, 'sem gabarito compatível'
    cn = cargo_num(desc_prova)
    if cn: bons = [b for b in bons if cargo_num(b[2] + ' ' + b[0]) in (None, cn)] or bons
    def diferem(a, b): return sum(1 for n in nums if a.get(n) != b.get(n)) > len(nums) * 0.05
    if len(bons) == 1 or not any(diferem(bons[0][1], b[1]) for b in bons[1:]): return bons[0][1], ''
    tp = tokens(desc_prova + ' ' + nome_prova) or tokens(texto(nome_prova, 1))
    pal = lambda x: {w for w in re.findall(r'[a-zà-ú]{4,}', (x or '').lower())} - {'prova', 'tipo', 'caderno', 'gabarito', 'oficial', 'definitivo', 'objetiva', 'concurso', 'cargo', 'para', 'público'}
    wp = pal(desc_prova + ' ' + nome_prova.replace('_', ' '))
    def nota(b):
        tb = tokens(b[0] + ' ' + b[2]); return (bool(tp & tb) if tp and tb else 0) * 10 - (5 if tp and tb and not (tp & tb) else 0) + len(wp & pal(b[0]))
    bons.sort(key=nota, reverse=True)
    if nota(bons[0]) > nota(bons[1]) and (not tp or tp & tokens(bons[0][0] + ' ' + bons[0][2])): return bons[0][1], ''
    return None, 'versão do caderno ambígua'
