"""ENEM 2009-2017 (eduagarcia/enem_challenge): só Linguagens em português, sem imagem, para revisão."""
import json, re, urllib.request, io
import pandas as pd
cfg = json.load(urllib.request.urlopen('https://huggingface.co/api/datasets/eduagarcia/enem_challenge/parquet', timeout=60))
df = pd.concat([pd.read_parquet(io.BytesIO(urllib.request.urlopen(u, timeout=120).read())) for c in cfg.values() for s in c.values() for u in s])
out = []
for _, r in df.iterrows():
    q = str(r['question']); ano = str(r['exam_year']); n = int(r['question_number'])
    if bool(r.get('nullified')) or re.search(r'\[\[placeholder\]\]|figura|imagem|gr[áa]fico|tabela|charge|tirinha|quadrinho|cartum|foto|pintura|\bobra\b|poema|romance|soneto|verso|m[úu]sica|cano', q, re.I): continue
    if re.search(r'\b(the|and|you|el|los|las|una|para el)\b', q[:400]): continue
    ch = r['choices']; tx = [str(t).strip() for t in ch['text']]; lb = list(ch['label'])
    k = str(r['answerKey']).strip()
    if k not in lb or len(tx) != 5: continue
    out.append({'id': 'enem:%s:%d' % (ano, n), 'fonte': 'ENEM %s (INEP)' % ano, 'ano': int(ano[:4]), 'materia': 'Língua Portuguesa', 'num': n,
                'enunciado': q.strip(), 'alternativas': tx, 'gabarito': lb.index(k)})
print(len(out))
json.dump(out, open('banco/externas/candidatas3.json', 'w'), ensure_ascii=False, indent=0)
