import sys,re,json,collections
sys.path.insert(0,__import__('os').path.dirname(__file__))
import me2
from me2 import junta
from gab2 import versoes,rows
from monta import limpa
import monta as _m
LEIS=r'Lei n[º°o.]*\s*(10\.826|11\.343|8\.072|9\.455|13\.869|12\.850|11\.340|9\.613|7\.716|9\.296|7\.960|13\.964|9\.099|8\.069|10\.741|9\.605|9\.503|13\.675)'
def classifica(t):
    if re.search(LEIS,t,re.I): return 'Legislação Especial'
    if re.search(r'Lei n[º°o.]*\s*7\.210|execução penal|\bLEP\b',t,re.I): return 'Execução Penal'
    if re.search(r'C[óo]digo de Processo Penal|\bCPP\b',t): return 'Direito Processual Penal'
    if re.search(r'C[óo]digo Penal',t): return 'Direito Penal'
    if re.search(r'Constitui[çc][ãa]o Federal|Constitui[çc][ãa]o da Rep[úu]blica|\bCF\b|CF/88',t): return 'Direito Constitucional'
    if re.search(r'Lei n[º°o.]*\s*8\.112|Lei n[º°o.]*\s*8\.429|Lei n[º°o.]*\s*9\.784|Lei n[º°o.]*\s*14\.133',t,re.I): return 'Direito Administrativo'
    d=_m.classifica(t)
    if d=='Execução Penal' and not re.search(r'execu[çc][ãa]o (da )?pena|penitenci|estabelecimento penal|prisional|remi[çc][ãa]o|livramento|progress[ãa]o|regime (fechado|semiaberto|aberto)|sa[íi]da tempor|falta (grave|disciplinar)|sentenciado|apenado|egress|CNPCP|DEPEN|Mandela|pol[íi]cia penal|custodiad',t,re.I):
        if re.search(r'pris[ãa]o|flagrante|inqu[ée]rito|den[úu]ncia|a[çc][ãa]o penal|processo',t,re.I): return 'Direito Processual Penal'
        if re.search(r'crime|pena|delito|il[íi]cit',t,re.I): return 'Direito Penal'
    return d
LP,INF,RL,ADM,CON,PEN,PP,EP,DH,ET,LE,LEST,CG='Língua Portuguesa','Noções de Informática','Raciocínio Lógico','Direito Administrativo','Direito Constitucional','Direito Penal','Direito Processual Penal','Execução Penal','Noções de Direitos Humanos e Participação Social','Ética no Serviço Público','Legislação Especial','Legislação Estadual','Conhecimentos Gerais'
def gab_e4():
    a="C C A D C A B B D A C B D C C A A D D C A B C D A D A C B".split()
    b="A D A A D B A C D B B C C B A B C A C D C D B D C A C B C B".split()
    ns=[n for n in range(1,31) if n!=12]; G=dict(zip(ns,a)); G[12]='X'; G.update(dict(zip(range(31,61),b))); return G
def gab_e2():
    R=rows('e2_gab'); i=R.index('24 - Policial Penal'); G={}
    for r in R[i+1:i+9]:
        for n,a in re.findall(r'0*(\d+) - ([A-EX*])',r): G[int(n)]=a
    return G
PROVAS=[
 dict(k='e0',id='fgv_seap_ba_24',titulo='Agente Penitenciário BA',orgao='SEAP/BA',banca='FGV',ano=2024,gab=lambda: versoes('e0_gab')[0][1],gt='preliminar'),
 dict(k='e1',id='fgv_sejusp_mg_22',titulo='Agente de Segurança Penitenciário MG',orgao='SEJUSP/MG',banca='FGV',ano=2022,gab=lambda: versoes('e1_gab')[0][1],gt='definitivo'),
 dict(k='e2',id='fundatec_pprs_26',titulo='Policial Penal RS',orgao='Polícia Penal/RS',banca='Fundatec',ano=2026,gab=gab_e2,gt='preliminar'),
 dict(k='e3',id='fundatec_susepe_22',titulo='Agente Penitenciário RS',orgao='SUSEPE/RS',banca='Fundatec',ano=2022,gab=lambda: versoes('e3_gab')[1][1],gt='definitivo'),
 dict(k='e4',id='selecon_sejusp_mg_22',titulo='Policial Penal MG',orgao='SEJUSP/MG',banca='Selecon',ano=2022,gab=gab_e4,gt='oficial'),
 dict(k='e5',id='ibfc_iapen_ac_23',titulo='Agente de Polícia Penal AC',orgao='IAPEN/AC',banca='IBFC',ano=2023,gab=lambda: versoes('e5_gab')[1][1],gt='preliminar'),
 # AOCP SEJUS/CE 2017 retirada: diagramação em duas colunas lado a lado não dá leitura confiável da numeração
 # dict(k='e7',id='aocp_sejus_ce_17',titulo='Agente Penitenciário CE',orgao='SEJUS/CE',banca='AOCP',ano=2017,gab=lambda: versoes('e7_gab')[0][1],gt='preliminar'),
 dict(k='e8',id='fepese_sap_sc_19',titulo='Agente Penitenciário SC',orgao='SAP/SC',banca='Fepese',ano=2019,gab=lambda: versoes('e8_gab')[0][1],gt='definitivo'),
 dict(k='e9',id='ibfc_seds_mg_14',titulo='Agente de Segurança Penitenciário MG',orgao='SEDS/MG',banca='IBFC',ano=2014,gab=lambda: versoes('e9_gab')[0][1],gt='definitivo'),
 dict(k='e11',id='vunesp_sejus_es_13',titulo='Agente Penitenciário ES',orgao='SEJUS/ES',banca='Vunesp',ano=2013,gab=lambda: versoes('e11_gab')[4][1],gt='definitivo'),
 dict(k='e17',id='fepese_sjc_sc_13',titulo='Agente Penitenciário SC',orgao='SJC/SC',banca='Fepese',ano=2013,gab=lambda: versoes('e17_gab')[0][1],gt='definitivo')]
SECMAP=[(r'PORTUGU',LP),(r'RACIOC|MATEM',RL),(r'INFORM',INF),(r'DIREITOS HUMANOS',DH),(r'[ÉE]TICA',ET),(r'EXECU[ÇC][ÃA]O PENAL|PENITENCI|SISTEMA PRISIONAL',EP),(r'PROCESSO PENAL|PROCESSUAL',PP),(r'LEGISLA[ÇC][ÃA]O (PENAL )?ESPECIAL|LEIS? ESPECIA',LE),(r'CONSTITUCIONAL(?! E)',CON),(r'ADMINISTRATIV',ADM),(r'DIREITO PENAL(?! E)',PEN),(r'HIST[ÓO]RIA|GEOGRAF|ATUALIDADES|CONHECIMENTOS GERAIS|REALIDADE',CG)]
RUIM=re.compile(r'\bfigura\b|imagem|gr[áa]fico|charge|tirinha|quadrinho|ilustra[çc]|fotografia|\blinhas? \d|\bl\. ?\d|cartum|ícone|planilha a seguir|tabela a seguir|abaixo representad',re.I)
TXT=re.compile(r'\btexto\b|\btrecho\b|fragmento|excerto|poema|crônica|par[áa]grafo|\bverso\b',re.I)
MARK=re.compile(r'^\s*(Check-square|SQUARE|\(\s*X\s*\)|\(\s*\))\s*',re.I)
def limpa_alt(s):
    s=re.sub(r'\s+(Secretaria de Estado[^|]*|Estado de Santa Catarina.*|[A-ZÁÉÍÓÚÂÊÔÃÕÇ ]{12,})$','',s)
    return limpa(s)
def monta(P):
    qs=me2.parse(P['k']+'_prova'); G=P['gab'](); out={'ctx':[],'q':[]}; fora=collections.Counter(); ctxi={}
    for n in sorted(qs):
        q=qs[n]; e=junta(q['e']); alts={}
        marcada=None
        for L,v in sorted(q['a'].items()):
            t=junta(v); m=MARK.match(t)
            if m:
                if re.search(r'Check|X',m.group(1),re.I): marcada=L
                t=t[m.end():]
            alts[L]=limpa_alt(t)
        g=marcada or G.get(n)
        if P['k'] in ('e8','e17') and G.get(n) and marcada and G.get(n)!=marcada and G.get(n) not in 'X*': g=G.get(n)
        if g in (None,'X','*','-'): fora['anulada/sem gabarito']+=1; continue
        letras=[L for L in 'ABCDE' if L in alts]
        if len(letras)<4 or letras!=list('ABCDE')[:len(letras)] or g not in letras: fora['alternativas']+=1; continue
        if len(e)<15 or any(len(alts[L])<1 for L in letras): fora['curta']+=1; continue
        if RUIM.search(e+' '+' '.join(alts.values())): fora['figura/linha']+=1; continue
        c=None
        if TXT.search(e) and not re.search(r'texto (a seguir|abaixo)|seguinte texto|leia (com atenção )?o texto',e,re.I) and len(e)<600:
            if not q['ctx']: fora['sem texto']+=1; continue
            k=q['ctx']
            if re.search(r'SQUARE|Check-square|\(\s*X\s*\)',k): fora['texto ruim']+=1; continue
            if k not in ctxi: ctxi[k]=len(out['ctx']); out['ctx'].append(limpa(k))
            c=ctxi[k]
        ds=None
        for rx,dd in SECMAP:
            if q['sec'] and re.search(rx,q['sec'],re.I): ds=dd; break
        dt=classifica(e+' '+' '.join(alts.values()))
        d=LP if c is not None else (dt if dt!=CG else (ds or CG))
        item={'n':n,'d':d,'g':g,'e':blocos_rom(e),'a':[alts[L] for L in letras]}
        if c is not None: item['c']=c
        out['q'].append(item)
    return out,fora
def blocos_rom(e):
    e=re.sub(r'\s(?=(?:I{1,3}|IV|V|VI{0,3})[.)–-]\s)','\n',e)
    e=re.sub(r'\s(?=\d\.\s[A-ZÁÉÍÓÚ])','\n',e)
    return e
if __name__=='__main__':
    tot=0; D={}
    for i,P in enumerate(PROVAS):
        o,f=monta(P); tot+=len(o['q'])
        print(P['id'],len(o['q']),dict(f),collections.Counter(q['d'] for q in o['q']).most_common(4))
    print('TOTAL',tot)
