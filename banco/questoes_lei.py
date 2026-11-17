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
    "cpp": ("o Código de Processo Penal", "Direito Processual Penal", [(1, 23), (155, 250), (282, 350)]),
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


def lacuna(d, lei, mat, art, rng):
    tk = tokens(d)
    if not tk: return None
    i, f, tipo, v, un, ext = rng.choice(tk)
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
    t = d[:i] + "________" + d[f:]
    if t[:1].isupper() and t[1:2].islower(): t = t[0].lower() + t[1:]
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
        if e and len(erradas) < 4:
            erradas.append((a, e[0], e[1], e[2]))
        if len(erradas) == 4: break
    if certa is None or len(erradas) < 4: return None
    alts = [certa[1]] + [x[1] for x in erradas]
    ordem = list(range(5)); rng.shuffle(ordem); alts = [alts[k] for k in ordem]; c = ordem.index(0)
    LET = "ABCDE"
    expl = ["Correta: %s, que reproduz o art. %s." % (LET[c], certa[0])]
    for j, k in enumerate(ordem):
        if k == 0: continue
        a, _, velho, novo = erradas[k - 1]
        expl.append("%s está errada: o art. %s diz “%s”, e não “%s”." % (LET[j], a, velho, novo))
    enun = "Com base no que dispõe %s, assinale a opção correta." % lei
    return [mat, enun, alts, c, " ".join(expl)]


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
                if len(d) >= 60: disp.append((a, d))
        n0 = len(out)
        for a, d in disp:                                   # modelo 1
            q = lacuna(d, lei, mat, a, rng)
            if q: out.append(q + [k, a])
        for i in range(0, len(disp), 6):                     # modelo 2: janelas de artigos vizinhos
            q = assinale(disp[max(0, i - 6):i + 12], lei, mat, rng)
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
