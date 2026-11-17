import os, re, json, time, random, hashlib, unicodedata, urllib.parse
import requests
RAIZ = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(RAIZ, 'cache'); os.makedirs(CACHE, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (compatible; HDConcursos-coleta/1.0; +https://hdconcursos.online)'}
TESTE = os.environ.get('TESTE') == '1'
class Bloqueado(Exception): pass
_ult = {}
def baixa(url, binario=False):
    """GET com cache local (nunca baixa a mesma URL duas vezes), pausa de 2-5 s por domínio e parada em 403/429."""
    h = hashlib.sha1(url.encode()).hexdigest(); arq = os.path.join(CACHE, h + ('.bin' if binario else '.html'))
    if os.path.exists(arq): return open(arq, 'rb').read() if binario else open(arq, encoding='utf-8', errors='ignore').read()
    dom = urllib.parse.urlparse(url).netloc; espera = _ult.get(dom, 0) + random.uniform(2, 5) - time.time()
    if espera > 0: time.sleep(espera)
    try: r = requests.get(url, headers=UA, timeout=40)
    except requests.RequestException: _ult[dom] = time.time(); return None
    _ult[dom] = time.time()
    if r.status_code in (403, 429): raise Bloqueado(f'{dom} respondeu {r.status_code}')
    if r.status_code != 200: return None
    if not binario and re.search(r'cf-turnstile|g-recaptcha|h-captcha|cf-chl', r.text[:200000], re.I) and re.search(r'download|prova|gabarito', r.text, re.I) and not re.search(r'\.pdf', r.text, re.I):
        raise Bloqueado(f'{dom} pede captcha para as provas')
    if binario: open(arq, 'wb').write(r.content); return r.content
    open(arq, 'w', encoding='utf-8').write(r.text); return r.text
def norm(s):
    s = unicodedata.normalize('NFKD', (s or '').lower()); s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '', s)
RELEVANTE = re.compile(r'pol[ií]cia|penal|penitenci|prisional|bombeir|guarda|seguran[çc]a p[úu]blica|sejus|seap|seres|seris|sds|depen|tribunal|\btj|\bmp\b|minist[ée]rio p[úu]blico|defensoria|procuradoria|agente|escriv|investigador|inspetor|delegad|soldado|oficial', re.I)
