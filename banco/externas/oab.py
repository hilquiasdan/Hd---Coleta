"""Baixa as questões do Exame de Ordem (dataset público eduagarcia/oab_exams, Hugging Face),
fica só com as áreas do edital da Polícia Penal PE, tira anuladas e as provavelmente desatualizadas
(mudanças legais de 2019 e 2024) e grava banco/externas/oab_filtradas.json para revisão."""
import json, re, urllib.request, io
import pandas as pd
API = "https://huggingface.co/api/datasets/eduagarcia/oab_exams/parquet/default/train"
urls = json.load(urllib.request.urlopen(API, timeout=60))
df = pd.concat([pd.read_parquet(io.BytesIO(urllib.request.urlopen(u, timeout=120).read())) for u in urls])
print("total", len(df), "| tipos:", df["question_type"].value_counts().to_dict())
MAPA = {"CRIMINAL": "Direito Penal", "CRIMINAL-PROCEDURE": "Direito Processual Penal", "CONSTITUTIONAL": "Direito Constitucional",
        "ADMINISTRATIVE": "Direito Administrativo", "HUMAN-RIGHTS": "Noções de Direitos Humanos e Participação Social"}
VELHO = re.compile(r"sa[íi]da tempor|exame criminol|progress[ãa]o|regime disciplinar diferenciado|\brdd\b|livramento condicional|hediond|"
                   r"tr[áa]fico privilegiado|juiz das garantias|acordo de n[ãa]o persecu|lei 8\.666|8666|improbidade|lei de licita", re.I)
out, motivos = [], {}
for _, r in df.iterrows():
    tipo = str(r["question_type"]).upper()
    if tipo not in MAPA: continue
    if bool(r.get("nullified")): motivos["anulada"] = motivos.get("anulada", 0) + 1; continue
    ch = r["choices"]; textos = list(ch["text"]); labels = list(ch["label"])
    q = str(r["question"]).strip(); gab = str(r["answerKey"]).strip()
    if gab not in labels or len(textos) < 4: motivos["sem gabarito"] = motivos.get("sem gabarito", 0) + 1; continue
    tudo = q + " " + " ".join(textos)
    ano = str(r["exam_id"])[:4]
    if int(ano or 0) < 2024 and VELHO.search(tudo): motivos["pode estar desatualizada"] = motivos.get("pode estar desatualizada", 0) + 1; continue
    out.append({"id": "oab:" + str(r["id"]), "exame": str(r["exam_id"]), "ano": ano, "materia": MAPA[tipo], "enunciado": q,
                "alternativas": [str(t).strip() for t in textos], "gabarito": labels.index(gab)})
print("filtradas", len(out), "| descartadas:", motivos)
json.dump(out, open("banco/externas/oab_filtradas.json", "w"), ensure_ascii=False, indent=0)
