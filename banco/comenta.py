"""Gabarito comentado gerado por IA local (Ollama), sem custo de API.

Uso: python comenta.py ENTRADA.json SAIDA.json [parte] [partes]

Travas de qualidade (o comentario so e aceito se passar em todas):
  1. A IA recebe o gabarito oficial e precisa concluir o mesmo resultado.
  2. O texto nao pode contradizer o gabarito ("esta correto" num item Errado etc.).
  3. Todo artigo citado de lei que temos em lei seca (Planalto) precisa existir,
     e o texto do artigo precisa ter relacao com o comentario.
  4. Tamanho e assunto minimos (o comentario precisa falar do item).
Alem disso registra se a IA, sem ver o gabarito, acertaria o item (confianca).
Nada e publicado como definitivo: tudo entra como "gerado - em revisao".
"""
import json, os, re, sys, time, hashlib, unicodedata
import requests

OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODELO = os.environ.get("MODELO", "qwen2.5:14b")
AQUI = os.path.dirname(os.path.abspath(__file__))
CACHE_LEIS = os.path.join(AQUI, "cache", "leis")

P = "https://www.planalto.gov.br/ccivil_03/"
LEIS = {
    "cf": (P + "constituicao/constituicao.htm", ["cf", "constituicao", "constituicao federal", "cf/88", "crfb"]),
    "cp": (P + "decreto-lei/del2848compilado.htm", ["cp", "codigo penal", "decreto-lei 2.848", "dl 2.848"]),
    "cpp": (P + "decreto-lei/del3689compilado.htm", ["cpp", "codigo de processo penal", "decreto-lei 3.689"]),
    "lep": (P + "leis/l7210.htm", ["lep", "lei de execucao penal", "lei 7.210", "lei 7210"]),
    "l8429": (P + "leis/l8429.htm", ["lei 8.429", "lei de improbidade", "lia", "lei 8429"]),
    "l8112": (P + "leis/l8112cons.htm", ["lei 8.112", "lei 8112", "estatuto dos servidores"]),
    "l9784": (P + "leis/l9784.htm", ["lei 9.784", "lei 9784", "lei do processo administrativo"]),
    "l11343": (P + "_ato2004-2006/2006/lei/l11343.htm", ["lei 11.343", "lei de drogas", "lei 11343"]),
    "l8072": (P + "leis/l8072.htm", ["lei 8.072", "lei dos crimes hediondos", "lei 8072"]),
    "l9455": (P + "leis/l9455.htm", ["lei 9.455", "lei de tortura", "lei 9455"]),
    "l10826": (P + "leis/2003/l10.826.htm", ["lei 10.826", "estatuto do desarmamento", "lei 10826"]),
    "l13869": (P + "_ato2019-2022/2019/lei/l13869.htm", ["lei 13.869", "lei de abuso de autoridade", "lei 13869"]),
    "l12850": (P + "_ato2011-2014/2013/lei/l12850.htm", ["lei 12.850", "lei de organizacoes criminosas", "lei 12850"]),
    "l8069": (P + "leis/l8069.htm", ["eca", "lei 8.069", "estatuto da crianca e do adolescente", "lei 8069"]),
    "l11340": (P + "_ato2004-2006/2006/lei/l11340.htm", ["lei 11.340", "lei maria da penha", "lei 11340"]),
    "l9099": (P + "leis/l9099.htm", ["lei 9.099", "lei dos juizados especiais", "lei 9099"]),
    "l12527": (P + "_ato2011-2014/2011/lei/l12527.htm", ["lei 12.527", "lai", "lei de acesso a informacao", "lei 12527"]),
    "l7716": (P + "leis/l7716.htm", ["lei 7.716", "lei 7716", "lei do racismo"]),
    "l14133": (P + "_ato2019-2022/2021/lei/l14133.htm", ["lei 14.133", "lei 14133", "lei de licitacoes"]),
}


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()


def norm_lei(nome):
    n = re.sub(r"\s+", " ", sem_acento(nome).replace("n.", "").replace("nº", "").replace("no ", "")).strip(" .")
    n = re.sub(r"/\d{2,4}$", "", n).strip()
    for k, (_, al) in LEIS.items():
        for a in al:
            if n == a or n.startswith(a + " ") or n.startswith(a + ","):
                return k
    return None


def baixa_lei(k):
    os.makedirs(CACHE_LEIS, exist_ok=True)
    arq = os.path.join(CACHE_LEIS, k + ".json")
    if os.path.exists(arq):
        return json.load(open(arq))
    url = LEIS[k][0]
    time.sleep(3)
    try:
        r = requests.get(url, timeout=60, headers={"User-Agent": "HD-Concursos-estudo/1.0"})
    except requests.RequestException:
        return None
    if r.status_code in (403, 429):
        print("BLOQUEADO", url, r.status_code); return None
    if r.status_code != 200:
        return None
    r.encoding = r.apparent_encoding or "latin-1"
    h = re.sub(r"(?is)<(strike|s|del)\b.*?</\1>", " ", r.text)  # tira texto revogado
    t = re.sub(r"(?s)<[^>]+>", " ", h)
    t = re.sub(r"&nbsp;|&#160;", " ", t)
    t = re.sub(r"\s+", " ", t)
    arts = {}
    pedacos = re.split(r"(?=\bArt\.\s*\d)", t)
    for p in pedacos:
        m = re.match(r"Art\.\s*(\d+(?:\.\d+)?)\s*[º°o]?\s*(?:-\s*([A-Z])\b)?", p)
        if not m:
            continue
        num = m.group(1).replace(".", "") + ("-" + m.group(2) if m.group(2) else "")
        if num not in arts:
            arts[num] = p[:3000]
    json.dump(arts, open(arq, "w"), ensure_ascii=False)
    return arts


def palavras(s):
    return {w for w in re.findall(r"[a-z]{5,}", sem_acento(s))} - {"artigo", "sobre", "sendo", "quando", "devem", "podera", "poderao", "item", "questao", "assertiva", "afirmativa", "gabarito", "correta", "errado", "certo", "porque", "portanto", "conforme", "previsto", "prevista", "segundo", "acordo"}


_IDX = None


def indice():
    """Todos os artigos das leis do Planalto, para achar os artigos ligados ao item."""
    global _IDX
    if _IDX is None:
        _IDX = []
        for k in LEIS:
            arts = baixa_lei(k) or {}
            for a, t in arts.items():
                _IDX.append((k, a, t, palavras(t)))
        print("lei seca carregada:", len(_IDX), "artigos", flush=True)
    return _IDX


def artigos_ligados(it, n=3):
    alvo = palavras(it["texto"] + " " + " ".join(it.get("alts") or []) + " " + (it.get("ctx") or "")[-600:])
    if len(alvo) < 3:
        return []
    import math
    tot = len(indice()) or 1
    df = {}
    for _, _, _, w in _IDX:
        for x in w & alvo:
            df[x] = df.get(x, 0) + 1
    res = []
    for k, a, t, w in _IDX:
        com = w & alvo
        if len(com) < 3:
            continue
        sc = sum(math.log(tot / (1 + df[x])) for x in com) / (1 + math.log(1 + len(w)) * 0.3)
        res.append((sc, k, a, t))
    res.sort(reverse=True)
    return [r for r in res[:n] if r[0] > 6]


def ollama(msgs, fmt=True):
    corpo = {"model": MODELO, "messages": msgs, "stream": False,
             "options": {"temperature": 0.1, "num_ctx": 4096, "num_predict": 450}}
    if fmt:
        corpo["format"] = "json"
    for t in range(3):
        try:
            r = requests.post(OLLAMA + "/api/chat", json=corpo, timeout=900)
            return r.json()["message"]["content"]
        except Exception as e:
            print("ollama erro", e); time.sleep(10)
    return ""


SIS = ("Você é professor de concursos públicos (Polícia Penal, banca Cebraspe e outras). "
       "Explique em português do Brasil, com precisão técnica e linguagem simples. "
       "Nunca invente artigos de lei, súmulas ou números. Se não tiver certeza do artigo, não cite artigo. "
       "Responda SOMENTE em JSON.")


def enunciado(it):
    s = ""
    if it.get("ctx"):
        s += "TEXTO/COMANDO:\n" + it["ctx"][:3500] + "\n\n"
    if it["tipo"] == "CE":
        s += "ITEM (julgue Certo ou Errado):\n" + it["texto"]
    else:
        s += "QUESTÃO:\n" + it["texto"] + "\n" + "\n".join("%s) %s" % ("ABCDE"[i], a) for i, a in enumerate(it.get("alts") or []))
    return s


def cego(it):
    if it["tipo"] == "CE":
        pede = 'Julgue o item. JSON: {"resposta":"C" ou "E"}'
    else:
        pede = 'Escolha a alternativa correta. JSON: {"resposta":"A","B","C","D" ou "E"}'
    out = ollama([{"role": "system", "content": SIS}, {"role": "user", "content": enunciado(it) + "\n\n" + pede}])
    try:
        return str(json.loads(out).get("resposta", "")).strip().upper()[:1]
    except Exception:
        return ""


def explica(it, trechos):
    if it["tipo"] == "CE":
        gab = "CERTO" if it["g"] == "C" else "ERRADO"
        pede = ("O gabarito oficial deste item é %s. Explique por que o item está %s. "
                "Se estiver errado, diga exatamente qual trecho está errado e qual seria o correto. " % (gab, gab.lower()))
        conc = '"conclusao":"C" ou "E"'
    else:
        pede = ("O gabarito oficial é a letra %s. Explique por que a %s está correta e, em uma frase cada, "
                "o erro das outras alternativas. " % (it["g"], it["g"]))
        conc = '"conclusao":"letra correta"'
    pede += ("Use de 2 a 6 frases curtas. JSON: {%s, \"comentario\":\"texto\", "
             "\"fundamento\":[{\"lei\":\"nome da lei, ex.: CF, CP, CPP, LEP, Lei 8.429\",\"artigo\":\"número\"}]} "
             "(fundamento pode ser lista vazia se não houver artigo de lei).") % conc
    lei = ""
    if trechos:
        lei = "\n\nTRECHOS DA LEI SECA QUE PODEM SER PERTINENTES (use somente se realmente tratarem do assunto; cite pelo nome da lei e número do artigo):\n" + "\n".join(
            "[%s, art. %s] %s" % (k.upper().replace("L", "Lei ", 1) if k.startswith("l") and k[1:].isdigit() else k.upper(), a, t[:700]) for _, k, a, t in trechos)
    pede += " Explique o motivo jurídico/técnico exato; não use explicações vagas como 'a lei não especifica'. Não cite datas, números de leis ou portarias que não estejam no enunciado ou nos trechos."
    out = ollama([{"role": "system", "content": SIS}, {"role": "user", "content": enunciado(it) + lei + "\n\n" + pede}])
    try:
        return json.loads(out)
    except Exception:
        return None


CONTRA_E = re.compile(r"\b(o item|a assertiva|a afirma[cç][aã]o|o enunciado)\s+(est[aá]|é|e)\s+(corret|cert|verdadeir)", re.I)
CONTRA_C = re.compile(r"\b(o item|a assertiva|a afirma[cç][aã]o|o enunciado)\s+(est[aá]|é|e)\s+(incorret|errad|fals)", re.I)


VAGO = re.compile(r"n[aã]o especifica|n[aã]o contempla|processos? mais amplos?|entre outros|de acordo com a legisla[cç][aã]o,|conceito bem estabelecido", re.I)


def nums(s):
    return set(re.findall(r"\d+(?:[.,/]\d+)*", s or ""))


def verifica(it, r, trechos=()):
    if not r or not isinstance(r, dict):
        return False, "sem resposta", []
    com0 = str(r.get("comentario", ""))
    base_txt = (it["texto"] or "") + " " + (it.get("ctx") or "") + " " + " ".join(it.get("alts") or []) + " " + " ".join(t for _, _, _, t in trechos)
    extra = nums(com0) - nums(base_txt)
    ok_arts = {a for _, _, a, _ in trechos}
    extra = {x for x in extra if x not in ok_arts}
    for f in (r.get("fundamento") or []):
        if isinstance(f, dict):
            extra.discard(str(f.get("artigo", "")).strip())
    if extra:
        return False, "numero/data que nao esta no enunciado nem na lei (%s)" % ",".join(sorted(extra))[:40], []
    if VAGO.search(com0):
        return False, "explicacao vaga", []
    com = str(r.get("comentario", "")).strip()
    conc = str(r.get("conclusao", "")).strip().upper()[:1]
    if conc != it["g"]:
        return False, "conclusao diferente do gabarito", []
    if len(com) < 120 or len(com) > 1600:
        return False, "tamanho fora do padrao", []
    if it["tipo"] == "CE":
        if it["g"] == "E" and CONTRA_E.search(com) and not re.search(r"incorret", com, re.I):
            return False, "texto contradiz o gabarito", []
        if it["g"] == "C" and CONTRA_C.search(com):
            return False, "texto contradiz o gabarito", []
    else:
        m = re.search(r"\b(?:alternativa|letra)\s+([A-E])\b[^.]{0,40}\b(?:é|e|está)\s+(?:a\s+)?corret", com, re.I)
        if m and m.group(1).upper() != it["g"]:
            return False, "texto aponta outra letra", []
    base = palavras(it["texto"] + " " + (it.get("ctx") or "")[-800:] + " " + " ".join(it.get("alts") or []))
    if base and len(palavras(com) & base) < 2:
        return False, "comentario nao fala do item", []
    funds = []
    for f in (r.get("fundamento") or [])[:4]:
        if not isinstance(f, dict):
            continue
        lei = str(f.get("lei", "")).strip(); art = re.sub(r"[^\dA-Z\-]", "", str(f.get("artigo", "")).upper().replace("º", ""))
        if not lei or not art:
            continue
        k = norm_lei(lei)
        if not k:
            funds.append({"lei": lei, "artigo": art, "verificado": False}); continue
        arts = baixa_lei(k)
        if arts is None:
            funds.append({"lei": lei, "artigo": art, "verificado": False}); continue
        if art not in arts:
            return False, "artigo citado nao existe (%s art. %s)" % (lei, art), []
        ligacao = palavras(arts[art]) & (palavras(com) | base)
        if len(ligacao) < 2:
            return False, "artigo citado nao tem relacao (%s art. %s)" % (lei, art), []
        funds.append({"lei": lei, "artigo": art, "verificado": True})
    # artigo citado no texto mas fora do fundamento tambem e conferido
    for m in re.finditer(r"art(?:igo)?\.?\s*(\d+)\s*[º°o]?(?:[^.;]{0,25}?)\b(da|do)\s+(CF|CP|CPP|LEP|Constitui[cç][aã]o[^,.;]{0,15}|C[oó]digo Penal|C[oó]digo de Processo Penal|Lei\s+n?[º°.]?\s*[\d.]+)", com, re.I):
        k = norm_lei(m.group(3))
        if k:
            arts = baixa_lei(k)
            if arts is not None and m.group(1) not in arts:
                return False, "artigo no texto nao existe (%s)" % m.group(0)[:40], []
    return True, "", funds


def main():
    ent, sai = sys.argv[1], sys.argv[2]
    parte = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    partes = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    itens = [it for i, it in enumerate(json.load(open(ent))) if i % partes == parte]
    feitos = {}
    if os.path.exists(sai):
        for x in json.load(open(sai)):
            feitos[x["k"]] = x
    lim = time.time() + int(os.environ.get("LIMITE_SEG", "19000"))
    for n, it in enumerate(itens):
        if it["k"] in feitos:
            continue
        if time.time() > lim:
            print("tempo esgotado, parando com seguranca"); break
        c = cego(it)
        ok, motivo, funds = False, "", []
        trechos = artigos_ligados(it) if it.get("materia") not in ("Língua Portuguesa", "Raciocínio Lógico") else []
        if c != it["g"]:
            motivo = "IA nao acertou o item sozinha (baixa confianca)"
        else:
            for tent in range(2):  # 2 tentativas; so aceita se passar nas travas
                r = explica(it, trechos)
                ok, motivo, funds = verifica(it, r, trechos)
                if ok:
                    break
        reg = {"k": it["k"], "g": it["g"], "acordo_cego": c == it["g"], "status": "ok" if ok else "descartado", "motivo": motivo,
               "modelo": MODELO, "h": hashlib.sha1((it["texto"] or "").encode()).hexdigest()[:12]}
        if ok:
            reg["comentario"] = str(r["comentario"]).strip(); reg["fundamento"] = funds
        feitos[it["k"]] = reg
        json.dump(list(feitos.values()), open(sai, "w"), ensure_ascii=False)
        print(n + 1, len(itens), reg["status"], motivo, "cego_ok" if reg["acordo_cego"] else "cego_dif", flush=True)
    v = list(feitos.values())
    print("RESUMO ok=%d descartados=%d acordo_cego=%d de %d" % (
        sum(x["status"] == "ok" for x in v), sum(x["status"] != "ok" for x in v), sum(x["acordo_cego"] for x in v), len(v)))


if __name__ == "__main__":
    main()
