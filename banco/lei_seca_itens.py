"""Itens de lei seca no padrão Cebraspe, 100% em Python (sem IA e sem custo).

Cada item nasce de um dispositivo real da lei atualizada (API pública do Congresso, normas.leg.br):
  - CERTO: o dispositivo como está na lei (com o caput quando é inciso);
  - ERRADO: o mesmo dispositivo com UMA troca que a lei desmente (prazo, quantidade, fração,
    percentual, ou "poderá"/"deverá").
O gabarito é conhecido por construção, e a explicação mostra o trecho exato da lei, então não há
como a explicação "inventar". Saída: lista de itens com status "pendente" (revisão antes do site).

Uso: python lei_seca_itens.py SAIDA.json
"""
import json, random, re, sys
import comenta as cm

LEIS = {  # lei: (nome no comando, faixas de artigos que caem na prova; None = todos)
    "lep": ("Lei n.º 7.210/1984 (Lei de Execução Penal)", None),
    "cp": ("Código Penal", [(1, 120), (312, 359)]),
    "cpp": ("Código de Processo Penal", [(1, 23), (282, 350)]),
    "l11343": ("Lei n.º 11.343/2006 (Lei de Drogas)", [(27, 64)]),
    "l8072": ("Lei n.º 8.072/1990 (Lei dos Crimes Hediondos)", None),
    "l13869": ("Lei n.º 13.869/2019 (Lei de Abuso de Autoridade)", None),
    "l10826": ("Lei n.º 10.826/2003 (Estatuto do Desarmamento)", [(12, 21)]),
    "l12850": ("Lei n.º 12.850/2013 (Organizações Criminosas)", [(1, 22)]),
    "l8112": ("Lei n.º 8.112/1990", [(5, 46), (116, 182)]),
    "l9784": ("Lei n.º 9.784/1999", None),
    "l11340": ("Lei n.º 11.340/2006 (Lei Maria da Penha)", [(5, 24)]),
}
EXT = {1: "um", 2: "dois", 3: "três", 4: "quatro", 5: "cinco", 6: "seis", 7: "sete", 8: "oito", 9: "nove", 10: "dez",
       12: "doze", 15: "quinze", 20: "vinte", 24: "vinte e quatro", 30: "trinta", 45: "quarenta e cinco", 48: "quarenta e oito",
       60: "sessenta", 72: "setenta e duas", 90: "noventa", 120: "cento e vinte", 180: "cento e oitenta"}
VAL = {"dia": [1, 2, 3, 5, 8, 10, 15, 20, 30, 45, 60, 90], "hora": [2, 6, 12, 24, 48, 72], "mes": [1, 2, 3, 6, 12, 18, 24],
       "ano": [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30], "vez": [1, 2, 3], "pessoa": [1, 2, 3, 4, 5]}
UN = r"(dias?|horas?|meses|m[eê]s|anos?|vezes|pessoas)"
NUM = re.compile(r"\b(\d{1,3})(\s*\([^)]{2,30}\))?\s+" + UN + r"\b", re.I)
FRAC = [("1/6", "um sexto"), ("1/5", "um quinto"), ("1/4", "um quarto"), ("1/3", "um terço"), ("2/5", "dois quintos"),
        ("1/2", "metade"), ("3/5", "três quintos"), ("2/3", "dois terços")]
PCT = [16, 20, 25, 30, 40, 50, 60, 70]
LIMPA = re.compile(r"\((?:[^()]*?(?:reda[cç][aã]o|inclu[ií]d|acrescid|vide|revogad|vigência|vig[eê]ncia|vetad|renumerad|par[aá]grafo [uú]nico|Lei n|Emenda|Medida Provis)[^()]*)\)", re.I)


def unidade(u):
    u = cm.sem_acento(u.lower())
    return "dia" if u.startswith("dia") else "hora" if u.startswith("hora") else "mes" if u.startswith("mes") else \
        "ano" if u.startswith("ano") else "vez" if u.startswith("vez") else "pessoa"


def no_intervalo(a, faixas):
    try:
        n = int(re.match(r"\d+", a).group())
    except Exception:
        return False
    return faixas is None or any(x <= n <= y for x, y in faixas)


def dispositivos(art_txt):
    """separa caput, incisos e parágrafos; incisos levam junto o fim do caput (até os dois-pontos)"""
    t = LIMPA.sub("", art_txt)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^Art\.\s*\d+[\dA-Z\-º°o\.]*\s*", "", t)
    if re.search(r"\b(revogad|vetad)", t[:60], re.I):
        return []
    partes = re.split(r"\s(?=(?:§\s*\d+[º°o]?|Parágrafo único\.)\s)", t)
    out = []
    for p in partes:
        p = re.sub(r"^(?:§\s*\d+[º°o]?\.?|Parágrafo único\.)\s*", "", p).strip()
        inc = re.split(r"\s(?=[IVXL]{1,6}\s*[-–]\s)", p)
        cab = inc[0].strip()
        if len(inc) == 1:
            out.append(cab)
        else:
            lead = cab.rstrip(":").strip()
            for i in inc[1:]:
                i = re.sub(r"^[IVXL]{1,6}\s*[-–]\s*", "", i).strip()
                i = re.sub(r"[;,]?\s*(?:\be|\bou)?\s*$", "", i).strip()
                out.append(lead + ": " + i)
    res = []
    for d in out:
        d = re.sub(r"\s+", " ", d).strip(" ;")
        if 60 <= len(d) <= 520 and not re.search(r"\b(revogad|vetad)|\(VETADO\)|\bart\.\s*\d", d, re.I) and re.search(r"[a-z]{4}", d):
            res.append(d.rstrip(".") + ".")
    return res


def errado(d, rng):
    """uma troca que a lei desmente; devolve (texto, explicação) ou None"""
    opc = []
    for m in NUM.finditer(d):
        n = int(m.group(1)); u = unidade(m.group(3))
        if d.count(m.group(0)) > 1: continue
        alts = [v for v in VAL[u] if v != n and abs(v - n) >= max(1, n * 0.2)]
        if not alts: continue
        alts.sort(key=lambda v: abs(v - n)); v = rng.choice(alts[:3])  # troca plausível, como a banca faz
        ext = EXT.get(v, str(v))
        if u in ("hora", "pessoa", "vez"):
            ext = re.sub(r"\bum$", "uma", re.sub(r"\bdois$", "duas", ext.replace("setenta e duas", "setenta e duas")))
        else:
            ext = ext.replace("setenta e duas", "setenta e dois")
        novo = str(v) + (" (" + ext + ")" if m.group(2) else "") + " " + m.group(3)
        if u in ("dia", "hora", "mes", "ano", "pessoa") and v == 1:
            novo = novo.replace("dias", "dia").replace("horas", "hora").replace("meses", "mês").replace("anos", "ano").replace("pessoas", "pessoa")
        opc.append((m.start(), m.end(), novo, m.group(0)))
    for a, b in FRAC:
        m = re.search(r"\b" + re.escape(a) + r"(\s*\(" + b + r"\))?", d)
        if m:
            x = rng.choice([f for f in FRAC if f[0] != a])
            opc.append((m.start(), m.end(), x[0] + (" (" + x[1] + ")" if m.group(1) else ""), m.group(0)))
    for m in re.finditer(r"\b(\d{1,2})%(\s*\([^)]{3,40}\))?", d):
        n = int(m.group(1))
        if n in PCT:
            v = rng.choice([p for p in PCT if p != n]); opc.append((m.start(), m.end(), "%d%%" % v, m.group(0)))
    for pal, troca in (("poderá", "deverá"), ("deverá", "poderá"), ("poderão", "deverão"), ("deverão", "poderão")):
        m = re.search(r"\b" + pal + r"\b", d)
        if m and d.count(pal) == 1:
            opc.append((m.start(), m.end(), troca, pal))
    if not opc:
        return None
    i, f, novo, velho = rng.choice(opc)
    return d[:i] + novo + d[f:], velho, novo


def main():
    sai = sys.argv[1]; rng = random.Random(42); itens = []; vistos = set()
    for k, (nome, faixas) in LEIS.items():
        arts = cm.baixa_lei(k) or {}
        print(k, len(arts), "artigos", flush=True)
        for a, txt in arts.items():
            if not no_intervalo(a, faixas):
                continue
            for d in dispositivos(txt):
                if d in vistos:
                    continue
                vistos.add(d)
                e = errado(d, rng)
                if not e:
                    continue  # só entra dispositivo que permite um par Certo/Errado com troca precisa
                base = {"materia_lei": k, "lei": nome, "artigo": a, "tipo": "CE", "origem": "lei_seca_hd", "status": "pendente",
                        "ctx": "Julgue o item a seguir com base na %s." % nome, "trecho": d}
                if rng.random() < .5:
                    itens.append(dict(base, item=d, g="C", explicacao="Certo. O item reproduz fielmente o art. %s da %s: “%s”" % (a, nome, d)))
                else:
                    t, velho, novo = e
                    itens.append(dict(base, item=t, g="E", explicacao="Errado. O art. %s da %s diz “%s”, e não “%s”. Texto da lei: “%s”" % (a, nome, velho, novo, d)))
    json.dump(itens, open(sai, "w"), ensure_ascii=False, indent=1)
    c = {}
    for x in itens: c[x["materia_lei"]] = c.get(x["materia_lei"], 0) + 1
    print("RESUMO itens=%d certos=%d errados=%d por_lei=%s" % (len(itens), sum(x["g"] == "C" for x in itens), sum(x["g"] == "E" for x in itens), json.dumps(c)))


if __name__ == "__main__":
    main()
