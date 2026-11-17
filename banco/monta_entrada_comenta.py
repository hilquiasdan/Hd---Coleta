"""Monta a entrada do comenta.py a partir do oficiais.json do site.
So entram questoes SEM comentario: as que ja tem justificativa oficial (campo j)
ou comentario ja aprovado (arquivo de comentarios existente) ficam de fora."""
import json, sys, os
D = json.load(open(sys.argv[1])); sai = sys.argv[2]
ja = set()
for f in sys.argv[3:]:
    if os.path.exists(f):
        ja |= {x["k"] for x in json.load(open(f)) if x.get("status") == "ok"}
out = []; pulou = 0
for pid, p in D.items():
    ctx = p["j"].get("ctx", [])
    for q in p["j"]["q"]:
        k = pid + ":" + str(q["n"])
        if q.get("j") or q.get("cm") or k in ja:
            pulou += 1; continue
        out.append({"k": k, "tipo": p["tipo"], "banca": p.get("banca"), "ano": p.get("ano"), "materia": q["d"], "g": q["g"],
                    "ctx": ctx[q["c"]] if q.get("c") is not None and q["c"] < len(ctx) else "",
                    "texto": q.get("t") or q.get("e"), "alts": q.get("a")})
json.dump(out, open(sai, "w"), ensure_ascii=False)
print("sem comentario:", len(out), "ja comentadas (puladas):", pulou)
