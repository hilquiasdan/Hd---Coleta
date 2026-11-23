"""Descobre bases abertas de questões (Hugging Face e GitHub) para revisão manual."""
import json, os, urllib.request, urllib.parse
def get(u, h=None):
    r = urllib.request.Request(u, headers=h or {'User-Agent': 'hd-coleta'})
    with urllib.request.urlopen(r, timeout=40) as f: return json.load(f)
out = {'hf': {}, 'gh': {}}
for q in ['concurso', 'concursos', 'questoes', 'questões', 'oab', 'enem', 'cespe', 'cebraspe', 'vestibular', 'direito', 'juridico', 'legal brazil', 'portuguese exam', 'brazilian law', 'bluex', 'provas', 'policia', 'magistratura']:
    try:
        for d in get('https://huggingface.co/api/datasets?full=true&limit=60&search=' + urllib.parse.quote(q)):
            out['hf'][d['id']] = {'downloads': d.get('downloads'), 'likes': d.get('likes'), 'tags': [t for t in d.get('tags', []) if t.startswith(('license:', 'language:', 'task_categories:', 'size_categories:'))], 'desc': (d.get('description') or '')[:300]}
    except Exception as e: out['hf']['ERRO ' + q] = str(e)
tok = os.environ.get('GH_TOKEN')
H = {'User-Agent': 'hd-coleta', 'Accept': 'application/vnd.github+json'}
if tok: H['Authorization'] = 'Bearer ' + tok
for q in ['questões concurso json', 'banco de questões concurso', 'questoes concursos dataset', 'questões OAB json', 'questões direito penal json', 'questoes cespe', 'simulado concurso questões', 'questões ENEM json', 'concurso publico questoes scraper', 'lei seca questões']:
    try:
        for r in get('https://api.github.com/search/repositories?per_page=30&q=' + urllib.parse.quote(q), H)['items']:
            out['gh'][r['full_name']] = {'stars': r['stargazers_count'], 'license': (r.get('license') or {}).get('spdx_id'), 'desc': (r.get('description') or '')[:200], 'size': r['size'], 'pushed': r['pushed_at'][:10]}
    except Exception as e: out['gh']['ERRO ' + q] = str(e)
json.dump(out, open('banco/externas/descoberta.json', 'w'), ensure_ascii=False, indent=1)
print(len(out['hf']), len(out['gh']))
