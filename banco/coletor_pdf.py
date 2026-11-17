"""Etapa 1: acha e baixa provas e gabaritos definitivos (PDF oficial das bancas) listados em fontes.yaml.
Uso: python coletor_pdf.py [site ...]   (TESTE=1 limita a 2 provas por site)
Saída: coleta/<site>.json  -> lista de concursos {id, nome, ano, url, arquivos:[{url, tipo: prova|gab, desc}]}"""
import sys, os, re, json, yaml, urllib.parse, time
INICIO = time.time(); LIM_RASTREIO = float(os.environ.get('LIM_RASTREIO', 10800)); LIM_TOTAL = float(os.environ.get('LIM_TOTAL', 17500))
from bs4 import BeautifulSoup
from comum import baixa, Bloqueado, RELEVANTE, TESTE, RAIZ
SAI = os.path.join(RAIZ, 'coleta'); os.makedirs(SAI, exist_ok=True)
NAO_PROVA = re.compile(r'discursiv|reda[çc]|pr[áa]tic|t[íi]tulo|resultado|edital|convoca|retifica|recurso|padr[ãa]o|espelho|aptid|f[íi]sic|m[ée]dic|psico|oral|inscri|homolog|classifica|locais|cronograma|ata\b|errata|aviso|comunicado|justificativ|aprovad|rela[çc][ãa]o|lista|nomea|curso de forma|ranking|desempate|vagas|local|sala|gabarito', re.I)
def eh_gab(t): return re.search(r'gabarit', t, re.I) and not re.search(r'preliminar|provis', t, re.I)
def eh_prova(t): return re.search(r'prova|caderno|\bcad[_ -]|tipo|objetiva|quest', t, re.I) and not re.search(r'gabarit', t, re.I) and not NAO_PROVA.search(t)
API = 'https://apis.cebraspe.org.br/cebraspe/eventos'; CDN = 'https://cdn.cebraspe.org.br/concursos'
def achata(o, out):
    if isinstance(o, list): [achata(x, out) for x in o]
    elif isinstance(o, dict):
        if o.get('eventoURL'): out.append(o)
        else: [achata(x, out) for x in o.values()]
    return out
def cebraspe(cfg):
    lista = []
    for fase in ('encerrado', 'em-andamento'):
        t = baixa(f'{API}/tipo/concursos/fase/{fase}')
        if t: lista += achata(json.loads(t), [])
    out = []; nprov = 0
    for e in lista:
        cod = e['eventoURL']
        if not RELEVANTE.search(cod.replace('_', ' ') + ' ' + (e.get('eventoNomeCompleto') or '') + ' ' + (e.get('eventoNomeAbreviado') or '')) and not re.match(r'(PC|PM|PF|PRF|CBM|TJ|TRF|TRT|TRE|MP|DP|PGE|AGU|STJ|STM|TC)', cod): continue
        t = baixa(f'{API}/{cod}')
        if not t: continue
        ev = json.loads(t); arqs = (ev.get('arquivosGabarito') or []) + (ev.get('arquivosEdital') or [])
        cargos = {str(int(c['idArea'])) if str(c.get('idArea', '')).isdigit() else '': c.get('area', '') for c in (ev.get('eventoCargos') or [])}
        fs = []
        for a in arqs:
            d = a.get('descricaoArquivo') or ''; n = a.get('nomeArquivo') or ''
            if not re.search(r'pdf', n, re.I): continue
            m = re.search(r'CARGO\s*0*(\d+)', d, re.I); cg = cargos.get(m.group(1), '') if m else ''
            if re.search(r'GABARITOS? (OFICIA(L|IS) )?DEFINITIVO', d, re.I) and not re.search(r'DISCURSIV|ORAL', d, re.I): fs.append({'url': f'{CDN}/{cod}/arquivos/{n}', 'tipo': 'gab', 'desc': d + (' :: ' + cg if cg else '')})
            elif re.search(r'PROVAS? OBJETIVAS?|CADERNO D[EO] PROVA|^PROVA', d, re.I) and not NAO_PROVA.search(d) and not re.search(r'DIGITA|SUB JUDICE', d, re.I): fs.append({'url': f'{CDN}/{cod}/arquivos/{n}', 'tipo': 'prova', 'desc': d + (' :: ' + cg if cg else '')})
        if any(f['tipo'] == 'prova' for f in fs) and any(f['tipo'] == 'gab' for f in fs):
            out.append({'id': cod, 'nome': ev.get('eventoNomeCompleto') or ev.get('eventoNomeAbreviado') or cod, 'ano': ev.get('eventoAno'), 'url': f'https://www.cebraspe.org.br/concursos/{cod}', 'cargos': list(cargos.values()), 'arquivos': fs})
            nprov += sum(f['tipo'] == 'prova' for f in fs)
            if TESTE and len(out) >= 1: break
    return out
_PW = None
def render(url):
    """página que depende de JavaScript: abre num navegador sem tela (Playwright), com o mesmo cache e as mesmas pausas"""
    global _PW
    import hashlib
    from comum import CACHE, _ult
    arq = os.path.join(CACHE, hashlib.sha1(('js:' + url).encode()).hexdigest() + '.html')
    if os.path.exists(arq): return open(arq, encoding='utf-8', errors='ignore').read()
    dom = urllib.parse.urlparse(url).netloc; espera = _ult.get(dom, 0) + __import__('random').uniform(2, 5) - time.time()
    if espera > 0: time.sleep(espera)
    if _PW is None:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start(); b = p.chromium.launch(); _PW = b.new_page(user_agent='Mozilla/5.0 (compatible; HDConcursos-coleta/1.0)')
    try:
        r = _PW.goto(url, wait_until='networkidle', timeout=45000); _ult[dom] = time.time()
        if r and r.status in (403, 429): raise Bloqueado(f'{dom} respondeu {r.status}')
        h = _PW.content()
    except Bloqueado: raise
    except Exception: _ult[dom] = time.time(); return None
    if re.search(r'cf-turnstile|g-recaptcha|h-captcha|cf-chl', h, re.I) and not re.search(r'\.pdf', h, re.I): raise Bloqueado(f'{dom} pede captcha')
    open(arq, 'w', encoding='utf-8').write(h); return h
def rastreio(cfg):
    dom = cfg['dominio']; seguir = re.compile(cfg['seguir'], re.I); fila = [(u, 0) for u in cfg['inicio']]; vistos = set(); por_pag = {}; n = 0
    est = os.path.join(SAI, cfg['_site'] + '_estado.json')
    if os.path.exists(est) and not TESTE:                                   # continua de onde a rodada anterior parou
        E = json.load(open(est)); fila = [tuple(x) for x in E['fila']]; vistos = set(E['vistos']); por_pag = E['por_pag']
    while fila and n < (40 if TESTE else cfg.get('max_paginas', 400)) and time.time() - INICIO < LIM_RASTREIO:
        u, prof = fila.pop(0)
        if u in vistos: continue
        vistos.add(u)
        html = render(u) if cfg['tipo'] == 'rastreio_js' else baixa(u); n += 1
        if not html: continue
        sp = BeautifulSoup(html, 'html.parser'); tit = ' '.join(x.get_text(' ', strip=True) for x in sp.find_all(['title', 'h1', 'h2'])[:3])
        for a in sp.find_all('a', href=True):
            h = urllib.parse.urljoin(u, a['href']).split('#')[0]; txt = a.get_text(' ', strip=True); alvo = txt + ' ' + urllib.parse.unquote(h.rsplit('/', 1)[-1]); alvo_url = h
            if re.search(r'\.pdf($|\?)', h, re.I):
                if eh_gab(alvo): por_pag.setdefault(u, {'tit': tit, 'fs': []})['fs'].append({'url': h, 'tipo': 'gab', 'desc': alvo})
                elif eh_prova(alvo): por_pag.setdefault(u, {'tit': tit, 'fs': []})['fs'].append({'url': h, 'tipo': 'prova', 'desc': alvo})
            elif re.search(dom, urllib.parse.urlparse(h).netloc) and h not in vistos and prof < 4 and (seguir.search(h) or seguir.search(txt)):
                if re.search(r'login|entrar|cadastro|inscri|boleto|area-do-candidato|wp-admin|\.(jpg|png|zip|docx?)$', h, re.I): continue
                (fila.insert(0, (h, prof + 1)) if RELEVANTE.search(txt) else fila.append((h, prof + 1)))
    if not TESTE: json.dump({'fila': fila, 'vistos': sorted(vistos), 'por_pag': por_pag, 'completo': not fila}, open(est, 'w'), ensure_ascii=False)
    out = []
    for u, p in por_pag.items():
        fs = p['fs']; ctx = p['tit']
        if not (any(f['tipo'] == 'prova' for f in fs) and any(f['tipo'] == 'gab' for f in fs)): continue
        if not RELEVANTE.search(ctx + ' ' + ' '.join(f['desc'] for f in fs)): continue
        m = re.search(r'(20\d\d)', ctx + ' ' + ' '.join(f['url'] for f in fs))
        out.append({'id': re.sub(r'[^a-z0-9]+', '_', urllib.parse.urlparse(u).path.lower()).strip('_')[:60] or 'inicio', 'nome': ctx[:150], 'ano': int(m.group(1)) if m else None, 'url': u, 'arquivos': fs})
        if TESTE and len(out) >= 2: break
    return out
def coleta(site, cfg):
    aviso = ''
    cfg = dict(cfg, _site=site)
    try: res = cebraspe(cfg) if cfg['tipo'] == 'api_cebraspe' else rastreio(cfg)   # rastreio e rastreio_js
    except Bloqueado as e: res = []; aviso = str(e)
    except Exception as e: res = []; aviso = 'erro: ' + str(e)[:150]
    for c in res:
        provas = [f for f in c['arquivos'] if f['tipo'] == 'prova']
        if TESTE: c['arquivos'] = provas[:2] + [f for f in c['arquivos'] if f['tipo'] == 'gab'][:4]
        for f in c['arquivos']:
            if time.time() - INICIO > LIM_TOTAL: f['ok'] = False; continue
            try: f['ok'] = baixa(f['url'], binario=True) is not None
            except Bloqueado as e: aviso = str(e); f['ok'] = False; break
        if aviso: break
    json.dump({'site': site, 'banca': cfg['banca'], 'aviso': aviso, 'concursos': res}, open(os.path.join(SAI, site + '.json'), 'w'), ensure_ascii=False)
    print(f'{site}: {len(res)} concursos, {sum(1 for c in res for f in c["arquivos"] if f["tipo"]=="prova")} provas, {sum(1 for c in res for f in c["arquivos"] if f["tipo"]=="gab")} gabaritos' + (f' | AVISO: {aviso}' if aviso else ''))
if __name__ == '__main__':
    F = yaml.safe_load(open(os.path.join(RAIZ, 'fontes.yaml')))
    for s in (sys.argv[1:] or list(F)): coleta(s, F[s])
