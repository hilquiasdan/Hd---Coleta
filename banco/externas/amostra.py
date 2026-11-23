"""Baixa amostras das bases candidatas para ver formato e licença."""
import json, urllib.request, io, subprocess, os, glob
import pandas as pd
out = {}
def card(ds):
    try: return urllib.request.urlopen('https://huggingface.co/datasets/%s/raw/main/README.md' % ds, timeout=40).read().decode('utf8', 'ignore')[:3000]
    except Exception as e: return 'sem README: %s' % e
for ds in ['Fazzioni/concursos_2.3M_with_gpt-oss', 'eduagarcia/enem_challenge', 'Victorhnb/Questoes-victor', 'SOARM1/provas', 'milktruck/OABTcleaned']:
    info = {'readme': card(ds)}
    try:
        cfgs = json.load(urllib.request.urlopen('https://huggingface.co/api/datasets/%s/parquet' % ds, timeout=60))
        info['parquet'] = cfgs
        urls = []
        for cfg, sp in cfgs.items():
            for s, us in sp.items(): urls += [(cfg, s, u) for u in us]
        tot = 0; amostras = {}
        for cfg, s, u in urls[:1]:
            info['n_arquivos'] = len(urls)
            df = pd.read_parquet(io.BytesIO(urllib.request.urlopen(u, timeout=120).read()))
            tot += len(df); amostras['%s/%s' % (cfg, s)] = {'n': len(df), 'cols': list(df.columns), 'ex': json.loads(df.head(2).to_json(orient='records', force_ascii=False))}
            if 'subject' in df.columns or 'area' in df.columns or 'question_type' in df.columns:
                for c in ('subject', 'area', 'question_type', 'disciplina', 'materia', 'banca', 'exam_id', 'year', 'ano', 'source', 'exam'):
                    if c in df.columns: amostras['%s/%s' % (cfg, s)]['cont_' + c] = df[c].astype(str).value_counts().head(40).to_dict()
        info['total'] = tot; info['amostras'] = amostras
    except Exception as e: info['erro'] = str(e)
    out[ds] = info
json.dump(out, open('banco/externas/amostra.json', 'w'), ensure_ascii=False, indent=1, default=str)
