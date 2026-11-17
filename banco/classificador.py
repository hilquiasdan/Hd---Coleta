"""Etapa 5: matéria pelo cabeçalho do caderno; senão por palavras-chave. Sem confiança -> 'revisar'."""
import os, re, sys, yaml
from comum import RAIZ
sys.path.insert(0, os.path.join(RAIZ, 'lib')); import classif
M = yaml.safe_load(open(os.path.join(RAIZ, 'materias.yaml')))
ACEITAS = set(M['aceitas']); CAB = [(re.compile(k, re.I), v) for k, v in M['cabecalhos'].items()]; SFORA = re.compile(M['secoes_fora'], re.I); FORA = re.compile(M['fora'], re.I)
def pontua(t):
    sc = {}
    for d, (forte, fraco) in classif.K.items():
        sc[d] = (3 * len(re.findall(forte, t, re.I)) if forte else 0) + (len(re.findall(fraco, t, re.I)) if fraco else 0)
    return sorted(sc.items(), key=lambda kv: -kv[1])
def classifica(it):
    t = it['enunciado'] + ' ' + ' '.join(it.get('alternativas', [])); ctx = it.get('texto_base', '')
    if it.get('sec') and SFORA.search(it['sec']): return None
    d = next((v for r, v in CAB if it.get('sec') and r.search(it['sec'])), None)
    if not d:
        cmd = it.get('comando') or ''
        d = classif.classifica(cmd, '') if cmd else None
        if d not in ACEITAS or not re.search(classif.K[d][0], t + ' ' + ctx[-300:], re.I):
            d = classif.classifica(t, ctx)
            if not cmd:                                                        # sem cabeçalho e sem comando: só aceita com folga clara
                (d1, s1), (d2, s2) = pontua(t + ' ' + ctx[-300:])[:2]
                if d1 in ACEITAS and (s1 < 3 or s1 < 1.5 * s2): return 'revisar'
        if d not in ACEITAS: return None                                       # matéria fora do curso
        if d != 'Língua Portuguesa' and not re.search(classif.K[d][0], t + ' ' + ctx[-300:], re.I): return 'revisar'
    if d not in ('Língua Portuguesa', 'Noções de Informática') and FORA.search(t + ' ' + ctx[-300:]): return None
    if not it.get('sec') and d != 'Língua Portuguesa' and re.search(r'assinale a (frase|op[çc][ãa]o) em que|termo sublinhado|cita[çc][õo]es de pessoas|reescrita|forma verbal|corretamente acentuad|norma culta|sentido do texto', t, re.I): return 'revisar'
    return d
