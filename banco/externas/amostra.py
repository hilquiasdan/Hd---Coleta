"""Baixa amostras das bases candidatas para ver formato e licença."""
import json, urllib.request, io, subprocess, os, glob
import pandas as pd
out = {}
def card(ds):
    try: return urllib.request.urlopen('https://huggingface.co/datasets/%s/raw/main/README.md' % ds, timeout=40).read().decode('utf8', 'ignore')[:3000]
    except Exception as e: return 'sem README: %s' % e
for ds in ['LucasGiraldi/concursos-publicos-brasil', 'russ7/oab_exams_2011_2025_combined', 'maritaca-ai/enem']:
    info = {'readme': card(ds)}
    try:
        cfgs = json.load(urllib.request.urlopen('https://huggingface.co/api/datasets/%s/parquet' % ds, timeout=60))
        info['parquet'] = cfgs
        urls = []
        for cfg, sp in cfgs.items():
            for s, us in sp.items(): urls += [(cfg, s, u) for u in us]
        tot = 0; amostras = {}
        for cfg, s, u in urls[:12]:
            df = pd.read_parquet(io.BytesIO(urllib.request.urlopen(u, timeout=120).read()))
            tot += len(df); amostras['%s/%s' % (cfg, s)] = {'n': len(df), 'cols': list(df.columns), 'ex': json.loads(df.head(2).to_json(orient='records', force_ascii=False))}
            if 'subject' in df.columns or 'area' in df.columns or 'question_type' in df.columns:
                for c in ('subject', 'area', 'question_type', 'disciplina', 'materia', 'banca', 'exam_id'):
                    if c in df.columns: amostras['%s/%s' % (cfg, s)]['cont_' + c] = df[c].astype(str).value_counts().head(40).to_dict()
        info['total'] = tot; info['amostras'] = amostras
    except Exception as e: info['erro'] = str(e)
    out[ds] = info
# repositório GitHub
try:
    subprocess.run(['git', 'clone', '--depth', '1', 'https://github.com/Samio-Santos/Sistema_Questoes_Django', '/tmp/sq'], check=True)
    fs = [f for f in glob.glob('/tmp/sq/**/*', recursive=True) if os.path.isfile(f) and f.endswith(('.json', '.csv', '.sqlite3', '.db', '.sql', '.txt', 'LICENSE'))]
    out['Samio'] = {'arquivos': [(f[7:], os.path.getsize(f)) for f in fs][:80]}
    lic = [f for f in fs if 'LICENSE' in f]
    if lic: out['Samio']['licenca'] = open(lic[0]).read()[:400]
except Exception as e: out['Samio'] = {'erro': str(e)}
json.dump(out, open('banco/externas/amostra.json', 'w'), ensure_ascii=False, indent=1, default=str)
