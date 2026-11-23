"""Questões novas para revisão: OAB 2017-2025 (russ7/oab_exams_2011_2025_combined, MIT) e
ENEM 2022-2024 Linguagens sem figura (maritaca-ai/enem, Apache-2.0)."""
import json, re, urllib.request, io
import pandas as pd
def pq(ds):
    cfg = json.load(urllib.request.urlopen('https://huggingface.co/api/datasets/%s/parquet' % ds, timeout=60))
    us = [u for c in cfg.values() for s in c.values() for u in s]
    return pd.concat([pd.read_parquet(io.BytesIO(urllib.request.urlopen(u, timeout=120).read())) for u in us])
MAPA = {'CRIMINAL': 'Direito Penal', 'DIREITO PENAL': 'Direito Penal', 'CRIMINAL-PROCEDURE': 'Direito Processual Penal', 'DIREITO PROCESSUAL PENAL': 'Direito Processual Penal',
        'CONSTITUTIONAL': 'Direito Constitucional', 'DIREITO CONSTITUCIONAL': 'Direito Constitucional', 'ADMINISTRATIVE': 'Direito Administrativo', 'DIREITO ADMINISTRATIVO': 'Direito Administrativo',
        'HUMAN-RIGHTS': 'Noções de Direitos Humanos e Participação Social', 'DIREITOS HUMANOS': 'Noções de Direitos Humanos e Participação Social', 'nan': '?', 'None': '?'}
df = pq('russ7/oab_exams_2011_2025_combined')
out = []
for _, r in df.iterrows():
    ano = int(str(r['exam_year'])[:4] or 0)
    if ano < 2017 or bool(r['nullified']): continue
    m = MAPA.get(str(r['question_type']))
    if not m: continue
    ch = r['choices']; tx = [str(t).strip() for t in ch['text']]; lb = list(ch['label'])
    k = r['answerKey']; g = int(k) if str(k).isdigit() else (lb.index(str(k)) if str(k) in lb else -1)
    if g < 0 or len(tx) < 4: continue
    out.append({'id': 'oab2:' + str(r['id']), 'fonte': 'Exame de Ordem %s (OAB/FGV)' % r['exam_id'], 'ano': ano, 'materia': m, 'num': int(r['question_number']),
                'enunciado': str(r['question']).strip(), 'alternativas': tx, 'gabarito': g})
print('oab', len(out))
for ano in ('2022', '2023', '2024'):
    js = [json.loads(l) for l in urllib.request.urlopen('https://huggingface.co/datasets/maritaca-ai/enem/resolve/main/%s.jsonl' % ano, timeout=60).read().decode().splitlines() if l.strip()]
    for r in js:
        n = int(re.sub(r'\D', '', r['id']) or 0)
        if n < 6 or n > 45 or r.get('figures') or '[[placeholder]]' in r['question']: continue  # 1-5 língua estrangeira; 6-45 linguagens
        out.append({'id': 'enem:%s:%d' % (ano, n), 'fonte': 'ENEM %s (INEP)' % ano, 'ano': int(ano), 'materia': 'Língua Portuguesa', 'num': n,
                    'enunciado': r['question'].strip(), 'alternativas': [str(a).strip() for a in r['alternatives']], 'gabarito': 'ABCDE'.index(r['label'])})
print('total', len(out))
json.dump(out, open('banco/externas/candidatas2.json', 'w'), ensure_ascii=False, indent=0)
