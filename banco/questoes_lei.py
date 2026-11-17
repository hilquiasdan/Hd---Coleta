"""Questões de múltipla escolha (5 alternativas + comentário) no formato da aba Questões do curso,
geradas 100% em Python a partir da lei atualizada (normas.leg.br). Sem IA: o gabarito vem do texto da lei.

Modelo 1 — lacuna: o dispositivo com o prazo/pena/quantidade/fração em branco; 5 valores plausíveis.
Modelo 2 — assinale a correta: 1 dispositivo fiel + 4 dispositivos vizinhos com uma troca que a lei desmente.

Saída: lista [matéria, enunciado, [5 alternativas], índice_correto, comentário, lei, artigo]
Uso: python questoes_lei.py SAIDA.json
"""
import json, random, re, sys
import comenta as cm
import lei_seca_itens as L

LEIS = {  # lei: (como citar, matéria, faixas de artigos)
    "lep": ("a Lei n.º 7.210/1984 (Lei de Execução Penal)", "Execução Penal", None),
    "cp": ("o Código Penal", "Direito Penal", [(1, 361)]),
    "cpp": ("o Código de Processo Penal", "Direito Processual Penal", [(1, 62), (69, 91), (155, 250), (282, 350)]),
    "cf": ("a Constituição Federal de 1988", "Direito Constitucional", [(1, 17), (37, 41), (136, 144)]),
    "l8112": ("a Lei n.º 8.112/1990", "Direito Administrativo", [(1, 182)]),
    "l9784": ("a Lei n.º 9.784/1999", "Direito Administrativo", None),
    "l8429": ("a Lei n.º 8.429/1992 (Lei de Improbidade Administrativa)", "Direito Administrativo", None),
    "l11343": ("a Lei n.º 11.343/2006 (Lei de Drogas)", "Legislação Especial", [(27, 64)]),
    "l8072": ("a Lei n.º 8.072/1990 (Lei dos Crimes Hediondos)", "Legislação Especial", None),
    "l13869": ("a Lei n.º 13.869/2019 (Lei de Abuso de Autoridade)", "Legislação Especial", None),
    "l10826": ("a Lei n.º 10.826/2003 (Estatuto do Desarmamento)", "Legislação Especial", [(1, 37)]),
    "l12850": ("a Lei n.º 12.850/2013 (Lei das Organizações Criminosas)", "Legislação Especial", None),
    "l11340": ("a Lei n.º 11.340/2006 (Lei Maria da Penha)", "Legislação Especial", None),
    "l8069": ("a Lei n.º 8.069/1990 (ECA)", "Legislação Especial", [(103, 128), (171, 190)]),
    "l7716": ("a Lei n.º 7.716/1989 (crimes de preconceito)", "Legislação Especial", None),
    "l12527": ("a Lei n.º 12.527/2011 (Lei de Acesso à Informação)", "Direito Administrativo", None),
}


def tokens(d):
    """valores trocáveis do dispositivo: (início, fim, tipo, valor, unidade, tem_extenso)"""
    out = []
    for m in L.NUM.finditer(d):
        if d.count(m.group(0)) == 1:
            out.append((m.start(), m.end(), "n", int(m.group(1)), m.group(3), bool(m.group(2))))
    for a, b in L.FRAC:
        m = re.search(r"\b" + re.escape(a) + r"(\s*\(" + b + r"\))?", d)
        if m: out.append((m.start(), m.end(), "f", a, "", bool(m.group(1))))
    for m in re.finditer(r"\b(\d{1,2})%(\s*\([^)]{3,40}\))?", d):
        if int(m.group(1)) in L.PCT: out.append((m.start(), m.end(), "p", int(m.group(1)), "", False))
    return out


def escreve(tipo, v, un, ext):
    if tipo == "f":
        return v + (" (" + dict(L.FRAC)[v] + ")" if ext else "")
    if tipo == "p":
        return "%d%%" % v
    u = L.unidade(un)
    e = L.EXT.get(v, str(v))
    if u in ("hora", "pessoa", "vez"):
        e = re.sub(r"\bum$", "uma", re.sub(r"\bdois$", "duas", e))
    else:
        e = e.replace("setenta e duas", "setenta e dois")
    nome = {"dia": ("dia", "dias"), "hora": ("hora", "horas"), "mes": ("mês", "meses"), "ano": ("ano", "anos"),
            "vez": ("vez", "vezes"), "pessoa": ("pessoa", "pessoas")}[u][0 if v == 1 else 1]
    return str(v) + (" (" + e + ")" if ext else "") + " " + nome


def lacunas(d, lei, mat, art, rng):
    faixas = [(m.start(), m.end()) for m in RANGE.finditer(d)]
    tk = [t for t in tokens(d) if not any(a <= t[0] < b for a, b in faixas)]
    return [q for q in (lacuna(d, lei, mat, art, rng, t) for t in tk[:3]) if q]


def lacuna(d, lei, mat, art, rng, t):
    i, f, tipo, v, un, ext = t
    if tipo == "n":
        u = L.unidade(un); cand = [x for x in L.VAL[u] if x != v]
        cand.sort(key=lambda x: abs(x - v)); cand = cand[:6]
    elif tipo == "f":
        cand = [a for a, _ in L.FRAC if a != v]
    else:
        cand = [x for x in L.PCT if x != v]
    if len(cand) < 4: return None
    dist = rng.sample(cand, 4)
    certo = escreve(tipo, v, un, ext)
    alts = [certo] + [escreve(tipo, x, un, ext) for x in dist]
    if len(set(alts)) < 5: return None
    ordem = list(range(5)); rng.shuffle(ordem); alts = [alts[k] for k in ordem]; c = ordem.index(0)
    t = minus(d[:i] + "________" + d[f:])
    enun = "De acordo com %s, %s Assinale a opção que preenche corretamente a lacuna." % (lei, t)
    com = "Gabarito: %s. Texto da lei (art. %s): “%s” As demais opções trazem valores que não constam desse dispositivo." % (certo, art, d)
    return [mat, enun, alts, c, com]


def assinale(grupo, lei, mat, rng):
    """grupo: lista de (artigo, dispositivo) da mesma lei e de artigos próximos"""
    cand = [(a, d) for a, d in grupo if len(d) <= 320]
    if len(cand) < 5: return None
    rng.shuffle(cand)
    certa = None; erradas = []
    for a, d in cand:
        if certa is None:
            certa = (a, d); continue
        e = L.errado(d, rng)
        if not e:
            op = trocas(d)
            if op:
                i, f, novo, velho = rng.choice(op); e = (d[:i] + novo + d[f:], velho, novo)
        if e and len(erradas) < 4:
            erradas.append((a, e[0], e[1], e[2]))
        if len(erradas) == 4: break
    if certa is None or len(erradas) < 4: return None
    alts = [certa[1]] + [x[1] for x in erradas]
    if len({x[:50] for x in alts}) < 5: return None
    ordem = list(range(5)); rng.shuffle(ordem); alts = [alts[k] for k in ordem]; c = ordem.index(0)
    LET = "ABCDE"
    expl = ["Correta: %s, que reproduz o art. %s." % (LET[c], certa[0])]
    for j, k in enumerate(ordem):
        if k == 0: continue
        a, _, velho, novo = erradas[k - 1]
        expl.append("%s está errada: o art. %s diz “%s”, e não “%s”." % (LET[j], a, velho, novo))
    enun = "Com base no que dispõe %s, assinale a opção correta." % lei
    return [mat, enun, alts, c, " ".join(expl)]


ORG = [("juiz", "m"), ("Ministério Público", "m"), ("autoridade policial", "f"), ("diretor do estabelecimento", "m"), ("Defensoria Pública", "f"), ("Conselho Penitenciário", "m")]
ART = {"m": {"o": "o", "do": "do", "pelo": "pelo", "ao": "ao", "no": "no", "a": "o", "da": "do", "pela": "pelo", "à": "ao", "na": "no"},
       "f": {"o": "a", "do": "da", "pelo": "pela", "ao": "à", "no": "na", "a": "a", "da": "da", "pela": "pela", "à": "à", "na": "na"}}
ORX = re.compile(r"(?<![\wÀ-ú])(o|a|do|da|pelo|pela|ao|à|no|na|O|A|Do|Da|Pelo|Pela|Ao|À|No|Na)\s+(juiz|Ministério Público|autoridade policial|diretor do estabelecimento|Defensoria Pública|Conselho Penitenciário)\b")
PROPRIOS = {"Ministério", "União", "Estados", "Estado", "Distrito", "Município", "Municípios", "Congresso", "Senado", "Presidente", "Conselho", "Defensoria", "Poder", "Supremo", "Superior", "Tribunal", "Câmara", "Brasil", "Polícia", "Juiz"}


def minus(t):
    w = t.split(" ", 1)[0]
    if w in PROPRIOS or (len(w) > 1 and w.isupper()): return t
    if w[:1].isupper() and (len(w) == 1 or w[1:].islower()): return t[0].lower() + t[1:]
    return t


def com_artigo(prep, nome, g):
    p = ART[g][prep.lower()]
    return (p[0].upper() + p[1:] if prep[0].isupper() else p) + " " + nome


def orgaos(d):
    return [m for m in ORX.finditer(d)]


PARES = [("reclusão", "detenção"), ("detenção", "reclusão"), ("aumentada", "diminuída"), ("diminuída", "aumentada"),
         ("aumenta-se", "diminui-se"), ("diminui-se", "aumenta-se"), ("poderá", "deverá"), ("deverá", "poderá"),
         ("poderão", "deverão"), ("deverão", "poderão"), ("privativamente", "concorrentemente"), ("exclusivamente", "preferencialmente")]
RANGE = re.compile(r"de (\d+) \(([^)]+)\) (meses|anos?) a (\d+) \(([^)]+)\) (meses|anos?)|de (\d+) \(([^)]+)\) a (\d+) \(([^)]+)\) (meses|anos)")


def faixa_txt(a, b, u1, u2):
    ext = lambda v, u: L.EXT.get(v, str(v)) if not (u.startswith("ano") or u.startswith("mes")) else L.EXT.get(v, str(v)).replace("setenta e duas", "setenta e dois")
    if u1 == u2: return "de %d (%s) a %d (%s) %s" % (a, ext(a, u1), b, ext(b, u2), u2)
    return "de %d (%s) %s a %d (%s) %s" % (a, ext(a, u1), "mês" if a == 1 and u1.startswith("m") else u1, b, ext(b, u2), u2)


def trocas(d):
    """todas as trocas possíveis que a lei desmente: (início, fim, novo, velho)"""
    out = []
    ms = orgaos(d)
    nomes = {m.group(2) for m in ms}
    if len(ms) == 1:
        m = ms[0]
        for nome, g in ORG:
            if nome not in d: out.append((m.start(), m.end(), com_artigo(m.group(1), nome, g), m.group(0)))
    for a, b in PARES:
        m = list(re.finditer(r"\b" + a + r"\b", d))
        if len(m) == 1: out.append((m[0].start(), m[0].end(), b, a))
    return out


def lacuna_orgao(d, lei, mat, art, rng):
    ms = orgaos(d)
    if len(ms) != 1: return None
    m = ms[0]; prep = m.group(1)
    outros = [com_artigo(prep.lower(), n, g) for n, g in ORG if n != m.group(2) and n not in d]
    if len(outros) < 4: return None
    alts = [com_artigo(prep.lower(), m.group(2), dict(ORG)[m.group(2)])] + rng.sample(outros, 4)
    ordem = list(range(5)); rng.shuffle(ordem); alts = [alts[k] for k in ordem]; c = ordem.index(0)
    t = minus(d[:m.start()] + "________" + d[m.end():])
    enun = "De acordo com %s, %s Assinale a opção que preenche corretamente a lacuna." % (lei, t)
    return [mat, enun, alts, c, "Gabarito: %s. Texto da lei (art. %s): \u201c%s\u201d" % (m.group(0), art, d)]


def lacuna_pena(d, lei, mat, art, rng):
    m = RANGE.search(d)
    if not m or "Pena" not in d[:m.start()]: return None
    if m.group(1): a, b, u1, u2 = int(m.group(1)), int(m.group(4)), m.group(3), m.group(6)
    else: a, b, u1, u2 = int(m.group(7)), int(m.group(9)), m.group(11), m.group(11)
    am = a * (12 if u1.startswith("ano") else 1); bm = b * (12 if u2.startswith("ano") else 1)
    if am >= bm: return None
    cands = set()
    for x, y in [(1, 3), (1, 4), (2, 4), (2, 5), (2, 6), (2, 8), (3, 8), (4, 8), (4, 10), (5, 10), (6, 12), (6, 20), (8, 15), (12, 30), (1, 2), (3, 6)]:
        if (x * 12, y * 12) != (am, bm): cands.add(faixa_txt(x, y, "anos" if x > 1 else "ano", "anos"))
    for x, y in [(6, 12), (3, 12), (6, 24), (1, 6), (3, 6)]:
        if (x, y) != (am, bm): cands.add(faixa_txt(x, y, "meses", "meses" if y < 12 else "ano" if y == 12 else "anos").replace("12 (doze) ano", "1 (um) ano").replace("24 (vinte e quatro) anos", "2 (dois) anos").replace("12 (doze) meses", "1 (um) ano"))
    cands = sorted(cands); certo = d[m.start():m.end()]
    if len(cands) < 4: return None
    alts = [certo] + rng.sample(cands, 4)
    if len(set(alts)) < 5: return None
    ordem = list(range(5)); rng.shuffle(ordem); alts = [alts[k] for k in ordem]; c = ordem.index(0)
    t = minus(d[:m.start()] + "________" + d[m.end():])
    enun = "Nos termos d%s, %s Assinale a opção que preenche corretamente a lacuna." % (lei[:1] == "o" and "o " + lei[2:] or "a " + lei[2:], t)
    return [mat, enun, alts, c, "Gabarito: %s. Texto da lei (art. %s): \u201c%s\u201d" % (certo, art, d)]


def incorreta(grupo, lei, mat, rng):
    cand = [(a, d) for a, d in grupo if len(d) <= 320]
    if len(cand) < 5: return None
    rng.shuffle(cand)
    errada = None; certas = []
    for a, d in cand:
        if errada is None:
            e = L.errado(d, rng)
            if not e:
                op = trocas(d)
                if op: i, f, novo, velho = rng.choice(op); e = (d[:i] + novo + d[f:], velho, novo)
            if e: errada = (a, e[0], e[1], e[2]); continue
        if len(certas) < 4: certas.append((a, d))
    if errada is None or len(certas) < 4: return None
    alts = [errada[1]] + [x[1] for x in certas]
    if len({x[:50] for x in alts}) < 5: return None
    ordem = list(range(5)); rng.shuffle(ordem); alts = [alts[k] for k in ordem]; c = ordem.index(0)
    LET = "ABCDE"
    com = "Incorreta: %s. O art. %s diz \u201c%s\u201d, e não \u201c%s\u201d. As demais reproduzem fielmente a lei (arts. %s)." % (
        LET[c], errada[0], errada[2], errada[3], ", ".join(sorted({x[0] for x in certas}, key=lambda z: (num_art(z), z))))
    return [mat, "Com base no que dispõe %s, assinale a opção INCORRETA." % lei, alts, c, com]


def num_art(a):
    m = re.match(r"\d+", a); return int(m.group()) if m else 0


def main():
    sai = sys.argv[1]; rng = random.Random(2026); out = []; por = {}
    for k, (lei, mat, faixas) in LEIS.items():
        arts = cm.baixa_lei(k) or {}
        disp = []
        for a, txt in sorted(arts.items(), key=lambda x: (num_art(x[0]), x[0])):
            if not L.no_intervalo(a, faixas): continue
            for d in L.dispositivos(txt):
                d = re.sub(r"\s+(?:T[ÍI]TULO|CAP[ÍI]TULO|SE[ÇC][ÃA]O|Se[çc][ãa]o|Subse[çc][ãa]o|LIVRO)\b.*$", "", d)
                d = re.sub(r"^(?:\d+\s*)?[º°ª]\.?\s+", "", d).strip()
                if len(d) < 60 or not d[:1].isupper() or re.match(r"(Deste|Desta|Do |Da |Este |Esta )", d): continue
                disp.append((a, d))
        n0 = len(out)
        for a, d in disp:                                   # modelo 1 (lacunas: valor, órgão, pena)
            for q in lacunas(d, lei, mat, a, rng): out.append(q + [k, a])
            for fn in (lacuna_orgao, lacuna_pena):
                q = fn(d, lei, mat, a, rng)
                if q: out.append(q + [k, a])
        for i in range(0, len(disp), 3):                     # modelo 2: janelas de artigos vizinhos
            q = assinale(disp[max(0, i - 6):i + 12], lei, mat, rng)
            if q: out.append(q + [k, disp[i][0]])
            q = incorreta(disp[max(0, i - 6):i + 12], lei, mat, rng)
            if q: out.append(q + [k, disp[i][0]])
        por[k] = len(out) - n0
        print(k, len(arts), "artigos,", len(disp), "dispositivos,", por[k], "questões", flush=True)
    vistos = set(); fim = []
    for q in out:
        ch = q[1] + "|" + q[2][q[3]]
        if ch in vistos: continue
        vistos.add(ch); fim.append(q)
    json.dump(fim, open(sai, "w"), ensure_ascii=False)
    print("RESUMO questoes=%d por_lei=%s" % (len(fim), json.dumps(por)))


if __name__ == "__main__":
    main()
