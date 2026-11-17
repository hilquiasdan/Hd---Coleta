"""Fase 2 — questões inéditas (Certo/Errado, estilo Cebraspe) com gabarito explicado.
IA local e gratuita (Ollama). Nada vai para o site sem revisão: tudo sai com status "pendente".

Uso: python gerador.py SAIDA.json [parte] [partes]
  env ALVO (aprovadas por parte, padrão 3), LIMITE_SEG (tempo máximo), MODELO.

Travas (a questão só é aprovada se passar em todas):
  1. Base em lei seca: a questão nasce de um artigo real baixado do Planalto (nada de memória).
  2. Gabarito sorteado antes (metade Certo, metade Errado) e a IA tem de obedecer.
  3. Nível de concurso: tamanho mínimo, caso concreto ou exceção/prazo/competência; nada óbvio.
  4. Originalidade: não copia mais de 12 palavras seguidas da lei nem se parece com questão oficial
     ou com outra já criada.
  5. Teste cego: em outra rodada, a IA lê só o item e o trecho da lei e precisa chegar ao mesmo gabarito.
  6. Sem dupla interpretação: a IA é questionada se o item admite outra leitura; se admitir, sai.
  7. Gabarito explicado passa pelas mesmas travas do comenta.py (artigo existe e tem relação,
     nenhum número ou data fora do enunciado ou da lei, nada vago).
"""
import json, os, random, re, sys, time, hashlib
import comenta as cm

AQUI = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(AQUI, "fase2_dados.json")))
LEI_DA_MATERIA = {"Execução Penal": ["lep"], "Direito Penal": ["cp"], "Direito Processual Penal": ["cpp"],
                  "Direito Constitucional": ["cf"], "Direito Administrativo": ["l8112", "l9784", "l8429", "l14133"],
                  "Legislação Especial": ["l11343", "l8072", "l9455", "l10826", "l13869", "l12850", "l11340", "l7716"],
                  "Noções de Direitos Humanos e Participação Social": ["cf"]}
COMPLEXO = re.compile(r"situa[cç][aã]o hipot[eé]tica|\b[A-Z][a-zà-ú]+,? (?:servidor|agente|policial|preso|condenad|reeducand|juiz|delegad|que|foi|era|estava|praticou|cometeu|cumpre)|salvo|exceto|exceç|exclusiv|somente|apenas|independentemente|vedad|proibid|prazo|\bdias?\b|\bmeses\b|\banos\b|compet[eê]|privativ|facultad|obrigat[oó]ri|dispensad|ressalvad", re.I)


def palavras_seq(a, b, n=13):
    wa = re.findall(r"\w+", cm.sem_acento(a)); sb = " " + " ".join(re.findall(r"\w+", cm.sem_acento(b))) + " "
    return any((" " + " ".join(wa[i:i + n]) + " ") in sb for i in range(0, max(0, len(wa) - n + 1)))


def shingles(t):
    w = re.findall(r"\w+", cm.sem_acento(t)); return {" ".join(w[i:i + 3]) for i in range(len(w) - 2)}


def parecido(a, b):
    A, B = shingles(a), shingles(b)
    return bool(A and B) and len(A & B) / len(A | B) > 0.45


def escolhe_tema(rng):
    ms = list(D["materias"]); m = rng.choices(ms, weights=[D["materias"][x]["peso"] for x in ms])[0]
    temas = D["materias"][m]["temas"]; t = rng.choices([x[0] for x in temas], weights=[x[1] for x in temas])[0]
    return m, t


def artigos_do_tema(m, tema, rng):
    """artigos da lei da matéria mais ligados ao tema (busca no texto oficial)"""
    leis = LEI_DA_MATERIA.get(m, [])
    alvo = cm.palavras(tema)
    cands = []
    for k in leis:
        arts = cm.baixa_lei(k) or {}
        for a, txt in arts.items():
            if len(txt) < 120: continue
            com = cm.palavras(txt) & alvo
            if com: cands.append((len(com) + rng.random(), k, a, txt))
    cands.sort(reverse=True)
    return cands[:6]


def nome_lei(k):
    return {"cf": "CF", "cp": "CP", "cpp": "CPP", "lep": "LEP"}.get(k, "Lei " + re.sub(r"(\d+)(\d{3})$", r"\1.\2", k[1:]))


SIS = ("Você é elaborador de provas da banca Cebraspe para concursos de Polícia Penal. Escreve itens de "
       "Certo ou Errado difíceis, técnicos e sem ambiguidade, em português do Brasil. Responda SOMENTE em JSON.")


def cria(m, tema, art, gab, exemplos):
    k, a, txt = art[1], art[2], art[3]
    ex = "\n".join("- %s (gabarito: %s)" % (e["t"], "Certo" if e["g"] == "C" else "Errado") for e in exemplos[:3])
    pede = (
        "MATÉRIA: %s\nTEMA DO EDITAL: %s\nTRECHO DA LEI (%s, art. %s):\n%s\n\n"
        "EXEMPLOS REAIS DE ITENS DA BANCA (só para o estilo, não copie):\n%s\n\n"
        "Escreva UM item inédito de Certo ou Errado sobre esse trecho, com GABARITO %s.\n"
        "Regras: nível de concurso difícil; prefira uma situação hipotética com personagem (ex.: 'Carlos, preso em regime fechado, ...') "
        "ou a cobrança de exceção, prazo, competência ou condição; o item deve poder ser julgado SÓ com o trecho de lei acima; "
        "%s; não copie frases da lei (reescreva); não use 'de acordo com o texto'; entre 250 e 650 caracteres.\n"
        'JSON: {"item":"...","gabarito":"C" ou "E","explicacao":"2 a 5 frases explicando o gabarito com base no artigo",'
        '"fundamento":[{"lei":"%s","artigo":"%s"}],"pegadinha":"qual detalhe o item cobra"}'
    ) % (m, tema, nome_lei(k), a, txt[:1800], ex, "CERTO" if gab == "C" else "ERRADO",
         "se for ERRADO, o erro deve ser UMA troca precisa (prazo, órgão, exceção, palavra como 'sempre/somente/vedado') que o trecho de lei desmente"
         if gab == "E" else "se for CERTO, tudo no item deve estar fiel ao trecho, mas escrito de outro jeito",
         nome_lei(k), a)
    out = cm.ollama([{"role": "system", "content": SIS}, {"role": "user", "content": pede}])
    try:
        return json.loads(out)
    except Exception:
        return None


def julga_com_lei(item, txt):
    out = cm.ollama([{"role": "system", "content": cm.SIS}, {"role": "user", "content":
        "TRECHO DE LEI:\n" + txt[:1800] + "\n\nCom base apenas nesse trecho, julgue o item:\n" + item + '\n\nJSON: {"resposta":"C" ou "E"}'}])
    try:
        return str(json.loads(out).get("resposta", "")).strip().upper()[:1]
    except Exception:
        return ""


def ambiguo(item, txt):
    out = cm.ollama([{"role": "system", "content": cm.SIS}, {"role": "user", "content":
        "TRECHO DE LEI:\n" + txt[:1800] + "\n\nITEM:\n" + item +
        "\n\nEsse item admite mais de uma interpretação razoável, depende de jurisprudência ou doutrina controversa, "
        'ou não pode ser julgado só com o trecho? JSON: {"ambiguo":true ou false,"motivo":"..."}'}])
    try:
        return bool(json.loads(out).get("ambiguo", True))
    except Exception:
        return True


def main():
    sai = sys.argv[1]; parte = int(sys.argv[2]) if len(sys.argv) > 2 else 0; partes = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    alvo = int(os.environ.get("ALVO", "3")); lim = time.time() + int(os.environ.get("LIMITE_SEG", "19000"))
    rng = random.Random(1000 + parte * 7919 + int(time.time()) // 86400)
    feitas = json.load(open(sai)) if os.path.exists(sai) else []
    oficiais = [e["t"] for v in D["exemplos"].values() for e in v]
    tent = 0; motivos = {}
    while sum(1 for x in feitas if x["status"] == "pendente") < alvo and time.time() < lim:
        tent += 1
        m, tema = escolhe_tema(rng); arts = artigos_do_tema(m, tema, rng)
        if not arts:
            motivos["sem lei seca para o tema"] = motivos.get("sem lei seca para o tema", 0) + 1; continue
        art = rng.choice(arts[:3]); gab = "C" if (tent + parte) % 2 else "E"
        r = cria(m, tema, art, gab, D["exemplos"].get(m, []))
        def sai_(mot):
            motivos[mot] = motivos.get(mot, 0) + 1; print(tent, "descartada:", mot, flush=True)
        if not r or not isinstance(r, dict) or not r.get("item"): sai_("sem resposta"); continue
        item = re.sub(r"\s+", " ", str(r["item"])).strip()
        if str(r.get("gabarito", "")).upper()[:1] != gab: sai_("gabarito diferente do pedido"); continue
        if not (220 <= len(item) <= 900): sai_("tamanho"); continue
        if not COMPLEXO.search(item): sai_("simples demais (sem caso, exceção, prazo ou competência)"); continue
        if palavras_seq(item, art[3]): sai_("copia a lei"); continue
        if any(parecido(item, o) for o in oficiais + [x["item"] for x in feitas]): sai_("parecida com outra questão"); continue
        if julga_com_lei(item, art[3]) != gab: sai_("teste cego falhou"); continue
        if ambiguo(item, art[3]): sai_("pode ter dupla interpretação"); continue
        it = {"k": "x", "tipo": "CE", "g": gab, "texto": item, "ctx": "", "materia": m}
        ok, mot, funds = cm.verifica(it, {"conclusao": gab, "comentario": r.get("explicacao", ""), "fundamento": r.get("fundamento") or []},
                                     [(0, art[1], art[2], art[3])])
        if not ok: sai_("explicação: " + mot); continue
        dificil = cm.cego({"tipo": "CE", "texto": item, "ctx": ""}) != gab  # sem a lei, a IA erraria: questão exigente
        feitas.append({"id": "in_" + hashlib.sha1(item.encode()).hexdigest()[:12], "materia": m, "tema": tema, "tipo": "CE",
                       "item": item, "g": gab, "explicacao": str(r.get("explicacao", "")).strip(), "fundamento": funds,
                       "pegadinha": str(r.get("pegadinha", ""))[:200], "dificil": dificil,
                       "origem": "inedita", "status": "pendente", "modelo": cm.MODELO, "banca_estilo": "Cebraspe"})
        json.dump(feitas, open(sai, "w"), ensure_ascii=False, indent=1)
        print(tent, "APROVADA", m, "|", tema, flush=True)
    print("RESUMO tentativas=%d aprovadas=%d motivos=%s" % (tent, sum(1 for x in feitas if x["status"] == "pendente"), json.dumps(motivos, ensure_ascii=False)))


if __name__ == "__main__":
    main()
