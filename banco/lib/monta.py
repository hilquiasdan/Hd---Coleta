import sys,re,json,collections
sys.path.insert(0,__import__('os').path.dirname(__file__))
from parse import *
from gab import gab
DISC=[('Execução Penal',r'execução penal|\bLEP\b|penitenci|prisional|estabelecimentos? pena|remição|CNPCP|DEPEN|egress|privad[ao]s? de liberdade|pessoas? presas?|\bpresos?\b|sentenciado|Regras de Mandela|regras mínimas|PNAISP|PEESP|PNAMPE|custodiad|Política Criminal|visitas? sociais|Código Penitenciário|SERIS|SERES'),
 ('Noções de Direitos Humanos e Participação Social',r'direitos humanos|participação social|Declaração Universal|Convenção Americana|Pacto Internacional|Decreto n\.º 8\.243'),
 ('Ética no Serviço Público',r'ética|moral|Decreto n\.º 1\.171|Lei n\.º 12\.846|sindicância'),
 ('Legislação Especial',r'legislação (penal )?especial|abuso de autoridade|lavagem de dinheiro|Estatuto do Desarmamento|Lei de Drogas|tortura|hediondo|organização criminosa|Lei n\.º 13\.964|Lei nº 13\.675|Sistema Único de Segurança|SUSP|Maria da Penha|leniência'),
 ('Direito Processual Penal',r'processo penal|processual penal|inquérito|prisão preventiva|ação penal|Código de Processo Penal|\bCPP\b|competência do júri|foro competente'),
 ('Direito Penal',r'direito penal|Código Penal|lei penal|crimes? contra|\bcrime|imputab|tipicidade|tentativa|consumad|pena (imposta|privativa)|legítima defesa'),
 ('Direito Constitucional',r'Constituição|constitucion|direitos e (das )?garantias|Poder (Executivo|Legislativo|Judiciário)|forma e do sistema de governo|segurança pública|defensoria'),
 ('Direito Administrativo',r'administração pública|administrativ|servidor|Regime Jurídico|Lei estadual n\.º 5\.247|licitaç|contrat|Lei n\.º 8\.112|improbidade|Lei n\.º 8\.429|poder de polícia|ato |licença|autorização'),
 ('Noções de Informática',r'Windows|Office|Word|Excel|navegação|navegador|informática|backup|computador|internet|correio eletrônico|nuvem|malware|vírus|planilha|Linux|segurança da informação'),
 ('Raciocínio Lógico',r'lógic|proposiç|probabilidade|urna|premissa|argumento|conjunto|crianças, designadas|tabela-verdade|quantas|maneiras|permutaç|porcentagem|\d+%|sequência'),
 ('Língua Portuguesa',r'texto|linguístic|gramatical|Manual de Redação|redação oficial|ofício|correspondências oficiais|vírgula|concordância|parágrafo|período|vocábulo|palavra'),
 ('Conhecimentos Gerais',r'história|histórico|geograf|Alagoas|Pernambuco|Estados Unidos|território|clima|econômic|ambient|capitalista|atualidade')]
def classifica(*txts):
    for t in txts:
        for d,rx in DISC:
            if t and re.search(rx,t,re.I): return d
    return 'Conhecimentos Gerais'
def comando(ctx):
    if not ctx: return ''
    p=ctx.split('\n\n'); c=[x for x in p if re.search(r'julgue|assinale|item|itens',x,re.I)]
    return c[-1] if c else p[-1]
DISC[2]=('Ética no Serviço Público',r'\bética\b|\bmoral\b|Decreto n\.º 1\.171|Lei n\.º 12\.846|sindicância')
PROVAS=[
 dict(id='seres_pe_21',titulo='Polícia Penal PE',orgao='SERES/PE',cargo='Policial Penal',ano=2022,tipo='ME',ordem=1,me='pe21_prova',gab=['pe21_gab_cg1','pe21_gab_001']),
 dict(id='seres_pe_17',titulo='Agente de Segurança Penitenciária PE',orgao='SERES/PE',cargo='Agente de Segurança Penitenciária',ano=2017,tipo='ME',ordem=2,me='pe17_prova',gab=['pe17_gab']),
 dict(id='seris_al_21',titulo='Agente Penitenciário AL',orgao='SERIS/AL',cargo='Agente Penitenciário',ano=2021,tipo='CE',ordem=3,ce=['al21_cg1','al21_cb1','al21_001'],gab=['al21_gab_cg1','al21_gab_cb1','al21_gab_001']),
 dict(id='depen_20',titulo='DEPEN · Agente Federal de Execução Penal',orgao='DEPEN',cargo='Agente Federal de Execução Penal',ano=2021,tipo='CE',ordem=4,ce=['dp20_prova'],gab=['dp20_gab_cb2','dp20_gab_008','dp20_gab_cg2']),
 dict(id='depen_15',titulo='DEPEN · Agente Penitenciário Federal',orgao='DEPEN',cargo='Agente Penitenciário Federal',ano=2015,tipo='CE',ordem=5,ce=['dp15_cb2'],gab=['dp15_cb2_gab'],extra=('dp15_cc2','dp15_cc2_gab')),
 dict(id='depen_15_esp',titulo='DEPEN · Especialista (complementares)',orgao='DEPEN',cargo='Especialista Federal em Assistência à Execução Penal',ano=2015,tipo='CE',ordem=6,ce=['dp15_cc1'],gab=['dp15_cc1_gab']),
 dict(id='depen_15_c14',titulo='DEPEN · Cargo 14 (complementares)',orgao='DEPEN',cargo='Técnico Federal de Apoio à Execução Penal',ano=2015,tipo='CE',ordem=7,ce=['dp15_cc3'],gab=['dp15_cc3_gab'])]
OVR={('seris_al_21',11):'Execução Penal',('seris_al_21',16):'Ética no Serviço Público',('seris_al_21',26):'Raciocínio Lógico',('seris_al_21',51):'Legislação Estadual',
 ('seris_al_21',55):'Legislação Estadual',('seris_al_21',58):'Legislação Estadual',('seris_al_21',89):'Legislação Especial',('seris_al_21',99):'Legislação Especial',
 ('seris_al_21',107):'Conhecimentos Gerais',('seris_al_21',114):'Conhecimentos Gerais',('depen_20',22):'Raciocínio Lógico',('depen_20',31):'Ética no Serviço Público',
 ('depen_20',37):'Direito Administrativo',('depen_20',40):'Direito Administrativo',('depen_20',50):'Direito Penal',('depen_20',60):'Direito Processual Penal',
 ('depen_20',77):'Legislação Especial',('depen_20',79):'Legislação Especial',('depen_20',99):'Legislação Especial',('depen_15',23):'Conhecimentos Gerais',
 ('depen_15',40):'Noções de Direitos Humanos e Participação Social',('depen_15',45):'Noções de Direitos Humanos e Participação Social',('depen_15_esp',71):'Execução Penal'}
def limpa(s):
    s=re.sub(r'\s+([,.;:)])',r'\1',s); s=re.sub(r'([(“])\s+',r'\1',s); return s.strip()
DROP={('seres_pe_17',7),('seres_pe_17',8),('seres_pe_17',13),('seres_pe_17',14),('seres_pe_17',15)}
LP,INF,RL,ADM,CON,PEN,PP,EP,DH,ET,LE,LEST='Língua Portuguesa','Noções de Informática','Raciocínio Lógico','Direito Administrativo','Direito Constitucional','Direito Penal','Direito Processual Penal','Execução Penal','Noções de Direitos Humanos e Participação Social','Ética no Serviço Público','Legislação Especial','Legislação Estadual'
FAIXAS={'seres_pe_17':[(1,8,LP),(10,11,INF),(12,15,RL),(16,24,ADM),(26,33,CON),(34,42,PEN),(43,51,PP),(52,56,EP),(57,57,DH),(58,60,EP)],
 'seres_pe_21':[(1,8,LP),(9,11,ET),(12,14,LEST),(15,17,INF),(20,20,RL),(21,25,ADM),(26,31,CON),(32,36,PEN),(37,37,LE),(38,42,PP),(43,47,LE),(48,55,EP),(56,56,DH),(57,59,EP),(60,60,DH)]}
def faixa(pid,n):
    for a,b,d in FAIXAS.get(pid,[]):
        if a<=n<=b: return d
ROM=re.compile(r'^(?:[IVX]{1,4}|[a-e]\))\s+\S')
def blocos(ls):
    """junta linhas; listas I, II, III / a), b) viram linhas próprias"""
    g=[[]]
    for x in ls:
        if ROM.match(x.strip()) and g[-1]: g.append([])
        g[-1].append(x)
    s='\n'.join(limpa(junta(b)) for b in g if b)
    return re.sub(r'(\n(?:[IVX]{1,4}|[a-e]\))\s[^\n]*?[.;]) (Estão|Está|Assinale|Julgue|A quantidade|Nesse caso)',r'\1\n\2',s)
def monta(P):
    G={}
    for g in P['gab']+([P['extra'][1]] if P.get('extra') else []): G.update(gab(g))
    out={'ctx':[],'q':[]}; avisos=[]
    if P['tipo']=='CE':
        it,cx=parse_ce(P['ce'])
        if P.get('extra'):
            it2,cx2=parse_ce([P['extra'][0]]); off=len(cx)
            for n,i in it2.items(): i['c']=None if i['c'] is None else i['c']+off; it[n]=i
            cx=cx+cx2
        usados={}
        bloco=None;disc=None
        for n in sorted(it):
            i=it[n]
            if (P['id'],n) in DROP: avisos.append((n,'depende de figura/fórmula')); continue
            t=blocos([x for x in i['ls'] if not x.startswith('\n')])+(''.join(x for x in i['ls'] if x.startswith('\n')))
            if i['c']!=bloco:
                bloco=i['c']; disc=OVR.get((P['id'],n)) or classifica(comando(cx[bloco]) if bloco is not None else '',t)
            g=G.get(n)
            if g not in ('C','E'): avisos.append((n,'anulada' if g=='X' else 'sem gabarito')); continue
            if bloco is not None and bloco not in usados: usados[bloco]=len(out['ctx']); out['ctx'].append(limpa(cx[bloco]))
            out['q'].append({'n':n,'d':disc,'g':g,'c':usados.get(bloco),'t':t})
    else:
        qs,T=parse_me(P['me']); usados={}
        for n in sorted(qs):
            q=qs[n]; g=G.get(n)
            if g not in list('ABCDE'): avisos.append((n,'anulada' if g=='X' else 'sem gabarito')); continue
            if (P['id'],n) in DROP: avisos.append((n,'depende de figura/fórmula')); continue
            e=blocos(q['e']); alts=[limpa(junta(q['a'].get(L,[]))) for L in 'ABCDE']
            ref=re.findall(r'texto ([A-Z0-9]+[A-Z0-9-]*)',e); c=None
            if ref and ref[0] in T:
                k=ref[0]
                if k not in usados: usados[k]=len(out['ctx']); out['ctx'].append(limpa(T[k]))
                c=usados[k]
            d=faixa(P['id'],n) or classifica(e+' '+' '.join(alts))
            item={'n':n,'d':d,'g':g,'e':e,'a':alts}
            if c is not None: item['c']=c
            js=[limpa(junta(q['j'].get(L,[]))) for L in 'ABCDE']
            if all(js): item['j']=js
            out['q'].append(item)
    return out,avisos
SUSP=re.compile(r'@@@| = ,| = e |\(\s*\)|\bP é\b(?!\w)|…|Deni|especíc|signic|conan|ecác|prossi|\bgráfico\b|\bfigura\b|\btabela\b|\bquadro\b|esquema',re.I)
