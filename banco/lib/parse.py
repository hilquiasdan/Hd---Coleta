import json,re,collections,sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
from gab import gab
X={}
SYM={'':'→','':'→','˄':'∧','':'∧','':'∨','':'¬','':'←','':'↔','':'↔','':'⇒','':'•','':'−','':'×','':'≤','':'≥','':'≠','':'∈','':'∩','':'∪','':'∅','':'⊂','':'≡','':'→','':' '}
LIXO=re.compile(r'CEBRASPE|^\|\|.*\|\|$|Edital:|Aplicação:|^Espaço livre$|^RASCUNHO$|^\d{1,3}$|^[–-]+$|^PROVAS? OBJETIVAS?$|^PROVA OBJETIVA$',re.I)
def linhas(pages):
    """linhas na ordem de leitura: página, coluna 0 inteira, depois coluna 1"""
    out=[]
    for pi,P in enumerate(pages):
        mid=P['w']/2; buf=[]
        for y,segs in P['l']:
            segs=[s for s in segs if not (s[1]<6 and re.fullmatch(r'\d+',s[3].strip()))]   # numeração de linhas do texto
            full=segs and segs[0][0]<mid-8 and segs[-1][0]>mid and max(s[1] for s in segs)>=13
            cols={0:[],1:[]}
            for s in segs: cols[0 if (full or s[0]<mid-8) else 1].append(s)
            for c,ss in cols.items():
                if not ss: continue
                t=''
                for i,s in enumerate(ss):
                    if i and t and not t.endswith(' ') and not s[3].startswith(' ') and s[0]-(ss[i-1][0]+ss[i-1][4])>1.2: t+=' '
                    t+=s[3]
                for a,b in SYM.items(): t=t.replace(a,b)
                t=re.sub(r'[-]','',t)
                if not t.strip() or re.search(r'pciconcursos|pcimarkpci',t): continue
                if max(s[1] for s in ss)<7.5 and len(t.strip())<=3: continue   # sobrescritos/subscritos soltos
                letra=len(ss)>=2 and re.fullmatch(r'[A-E]',ss[0][3].strip() or '') is not None and (ss[1][3].strip()=='' or ss[1][0]-ss[0][0]>6)
                buf.append(dict(p=pi,c=c,x=ss[0][0],y=y,sz=max(s[1] for s in ss),t=re.sub(r'\s+',' ',t).strip(),letra=letra,bold=all(s[2] for s in ss if s[3].strip())))
        buf.sort(key=lambda l:(l['c'],l['y']))
        # base de cada coluna = menor x frequente das linhas de corpo
        for c in (0,1):
            xs=[round(l['x']) for l in buf if l['c']==c and l['sz']>=9.5]
            if xs:
                cnt=collections.Counter(xs); base=min(x for x,n in cnt.items() if n>=3) if any(n>=3 for n in cnt.values()) else min(xs)
                for l in buf:
                    if l['c']==c: l['b']=base
        out+=buf
    return out
CLIT=re.compile(r'^(se|lhe|lhes|o|a|os|as|me|te|nos|vos|lo|la|los|las|no|na|nas|ia|ão|emos|eis|ei|íamos|á|ás)\b')
def junta(ts):
    s=''
    for q in ts:
        q=q.strip()
        if not q: continue
        if re.search(r'[A-Za-zÀ-ú]-$',s) and re.match(r'^[a-zà-ú]',q):
            s=s+q if CLIT.match(q) else s[:-1]+q
        else: s+=(' ' if s else '')+q
    s=re.sub(r'§ ?(\d+)(?=[A-ZÀ-Ú])',r'§ \1º ',s)
    s=re.sub(r'\bArt\. ?(\d)(?=[A-ZÀ-Ú])',r'Art. \1º ',s)
    return re.sub(r'\s+',' ',s).strip()
def paragrafos(ls):
    """linhas de um texto-base -> parágrafos (recuo de 1ª linha, fonte pequena = referência)"""
    if not ls: return ''
    P=[];cur=None;tipo=None
    for l in ls:
        src=l['sz']<=8; ind=l['x']>=l.get('b',0)+20
        tit=bool(re.match(r'^Texto [A-Z0-9][A-Z0-9-]*$|^Texto [IVX]+$',l['t']))
        novo=cur is None or tit or tipo=='tit' or (src!=(tipo=='src')) or (not src and ind and not (cur and re.search(r'[,;]$',cur[-1])))
        if novo: cur=[];P.append([('tit' if tit else 'src' if src else 'p'),cur])
        tipo='tit' if tit else 'src' if src else 'p'; cur.append(l['t'])
    return '\n\n'.join(('⟦'+' '.join(c)+'⟧') if k=='tit' else junta(c) for k,c in P if c)
def corta_capa(L):
    """remove instruções da capa e linhas de lixo; marca seções"""
    out=[];comecou=False
    SECRE=r'CONHECIMENTOS|PROVAS? OBJETIVAS?|L[ÍI]NGUA PORTUGUESA|^--.*--$'
    capa=set(l['p'] for l in L if re.search(r'Ao receber este caderno|LEIA COM ATEN|confira (inicialmente )?se os dados',l['t'],re.I))
    L=[l for l in L if l['p'] not in capa]
    sec=[(l['p'],l['y']) for l in L if (l['sz']>=13 or re.match(r'^--.*--$',l['t'])) and re.search(SECRE,l['t'],re.I)]
    p0,y0=sec[0] if sec else (0,0)
    L=[l for l in L if (l['p'],l['y'])>=(p0,y0)]
    for l in L:
        t=l['t']
        if re.search(r'DISCURSIVA',t) and (l['sz']>=13 or t.startswith('--')): break
        if l['sz']>=13 or re.match(r'^--.*--$',t):
            comecou=True; out.append(dict(l,sec=t.strip('- ').strip())); continue
        if not comecou: continue
        if LIXO.search(t) or l['sz']<4.5: continue
        out.append(l)
    return out

def parse_ce(nomes):
    itens={};ctxs=[];ctx_atual=None;ult_longo=None
    for nome in nomes:
        L=corta_capa(linhas(X[nome])); modo='livre'; cur=None; livre=[]; esperado=None
        def fecha_livre():
            nonlocal livre,ctx_atual,ult_longo
            if not livre: return
            txt=paragrafos(livre)
            if itens and len(txt)<140 and not re.search(r'julgue|seguir|seguem|subsequente|item|itens|texto',txt,re.I):
                ult=itens[max(itens)]; ult['ls'].append('\n'+txt); livre=[]; return
            livre=[]
            if re.search(r'\btexto\b',txt,re.I) and len(txt)<400 and ult_longo and not re.search(r'^\s*⟦?Texto',txt):
                txt=ult_longo+'\n\n'+txt
            elif len(txt)>=400: ult_longo=txt.rsplit('\n\n',1)[0] if re.search(r'julgue|assinale',txt.rsplit('\n\n',1)[-1],re.I) else txt
            ctxs.append(txt); ctx_atual=len(ctxs)-1
        for l in L:
            if 'sec' in l: 
                if modo=='livre': pass
                modo='livre'; continue
            t=l['t']; b=l.get('b',0); m=re.match(r'^(\d{1,3})\s+(\S.*)$',t)
            if m and abs(l['x']-b)<=3 and (esperado is None or int(m.group(1))==esperado or (int(m.group(1))>esperado and int(m.group(1))-esperado<=4) or (int(m.group(1))==1 and 1 not in itens and esperado>1)):
                if modo=='livre': fecha_livre()
                n=int(m.group(1)); cur={'n':n,'ls':[m.group(2)],'c':ctx_atual}; itens[n]=cur; modo='item'; esperado=n+1; continue
            if modo=='item':
                dx=l['x']-b
                if 8<dx<24 and l['sz']>=9: cur['ls'].append(t); continue
                modo='livre'
            livre.append(l)
        fecha_livre()
    return itens,ctxs

def parse_me(nome):
    L=corta_capa(linhas(X[nome])); textos={}; qs={}; modo='livre'; cur=None; tx=None; letra=None
    for l in L:
        t=l['t']; b=l.get('b',0)
        if 'sec' in l: modo='livre'; tx=None; continue
        if modo=='fim': continue
        mq=re.match(r'^(QUESTÃO|Questão)\s+(\d+)$',t)
        if mq:
            n=int(mq.group(2)); cur={'n':n,'e':[],'a':{},'j':{},'jl':None,'perdido':[]}; qs[n]=cur; modo='enun'; letra=None; tx=None; continue
        mt=re.match(r'^Texto ([A-Z0-9][A-Z0-9-]*)$',t)
        if mt and modo!='enun':
            tx=mt.group(1); textos[tx]=[l]; modo='texto'; continue
        if modo=='enun':
            if l['letra'] and t[0]=='A' and cur['e']:
                letra='A'; cur['a']['A']=[t[1:].strip()]; modo='alt'; continue
            cur['e'].append(t); continue
        if modo in ('alt','fimalt'):
            if l['letra'] and letra and t[0]==chr(ord(letra)+1):
                letra=t[0]; cur['a'][letra]=[t[1:].strip()]; modo='alt'; continue
            if t.upper()=='JUSTIFICATIVAS': modo='just'; continue
            if l['x']-b>8 and l['sz']>=9: cur['a'][letra].append(t); continue
            modo='livre'
        if modo=='just':
            if t.startswith('•') or re.search(r'PROVA DISCURSIVA',t): modo='fim'; continue
            mj=re.match(r'^([A-E])\s*[-–]\s*\d?\s*(CERTO|ERRADO)\.?\s*(.*)$',t)
            if mj: cur['jl']=mj.group(1); cur['j'][mj.group(1)]=[mj.group(2)+'. '+mj.group(3)]; continue
            if -3<=l['x']-b<=30 and cur['jl'] and l['sz']>=9: cur['j'][cur['jl']].append(t); continue
            modo='livre'
        if modo in ('livre','texto') and tx: textos[tx].append(l); modo='texto'
        elif cur is not None: cur['perdido'].append((round(l['x']-b),l['sz'],t))
    T={k:paragrafos(v) for k,v in textos.items()}
    return qs,T
