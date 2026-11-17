import json,re,collections,sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
X={}
def linhas(pages):
    out=[]
    for pi,P in enumerate(pages):
        w=P['w']; mid=w/2
        rows=[]  # junta linhas com y quase igual
        for y,segs in P['l']:
            if rows and y-rows[-1][0]<=2: rows[-1][1].extend(segs)
            else: rows.append([y,list(segs)])
        n2=sum(1 for y,s in rows if any(x[0]>mid-5 for x in s))
        twocol=n2>len(rows)*0.3
        buf=[]
        for y,segs in rows:
            segs=sorted(segs,key=lambda s:s[0])
            if twocol and not (segs[0][0]<mid-5 and any(s[0]<mid<s[0]+s[4]-3 for s in segs)):
                C={0:[s for s in segs if s[0]<mid-5],1:[s for s in segs if s[0]>=mid-5]}
            else: C={0:segs}
            for c,ss in C.items():
                if not ss: continue
                t=''
                for i,s in enumerate(ss):
                    if i and t and not t.endswith(' ') and not s[3].startswith(' ') and s[0]-(ss[i-1][0]+ss[i-1][4])>1.2: t+=' '
                    t+=s[3]
                t=re.sub(r'[-]','',t); t=re.sub(r'\s+',' ',t).strip()
                if not t or re.search(r'pcimarkpci|pciconcursos',t): continue
                buf.append(dict(p=pi,c=c,x=ss[0][0],y=y,sz=max(s[1] for s in ss),t=t))
        buf.sort(key=lambda l:(l['c'],l['y'])); out+=buf
    return out
QL=re.compile(r'^(?:QUEST[ÃA]O|Quest[ãa]o)\s*0*(\d{1,3})\s*[:.–-]?\s*(.*)$')
QI=re.compile(r'^0*(\d{1,3})\s*(?:[.)]|\s[–-])\s*(\S.*)$')
AL=re.compile(r'^\(?([A-Ea-e])\s*[).]\s*(.*)$')
QB=re.compile(r'^0*(\d{1,3})()$')
def candidatos(L):
    C=[]; base={}
    for l in L:
        k=(l['p'],l['c']); base[k]=min(base.get(k,9999),l['x'])
    for i,l in enumerate(L):
        m=QL.match(l['t']) or QI.match(l['t']) or (QB.match(l['t']) if l['x']-base[(l['p'],l['c'])]<=6 else None)
        if m: C.append((i,int(m.group(1)),m.group(2) or ''))
    return C
def cadeia(C,Apos=None):
    """sequência 1,2,3...; a próxima questão só vale se a anterior já mostrou alternativa (A)), salvo se não houver outra opção"""
    import bisect
    Apos=Apos or []
    def tem_alt(i,j):
        k=bisect.bisect_right(Apos,i); return k<len(Apos) and Apos[k]<j
    best=[]
    for s0,c0 in enumerate(C):
        if c0[1]!=1: continue
        ch=[c0]; exp=2; pos=s0
        while True:
            cand=[(k,c) for k,c in enumerate(C) if k>pos and c[1]==exp]
            if not cand: break
            boa=[(k,c) for k,c in cand if tem_alt(ch[-1][0],c[0])]
            k,c=(boa[0] if boa else cand[0]); ch.append(c); pos=k; exp+=1
        if len(ch)>len(best) or (len(ch)==len(best) and best and c0[0]>best[0][0]): best=ch
    return best
LIXO=re.compile(r'^(Página|Pág\.)\s*\d|^www\.|RASCUNHO|^Espaço para rascunho|^Cargo:|^\d+ de \d+$',re.I)
def junta(ts):
    s=''
    for q in ts:
        q=q.strip()
        if not q: continue
        if re.search(r'[A-Za-zÀ-ú]-$',s) and re.match(r'^[a-zà-ú]',q): s=s[:-1]+q
        else: s+=(' ' if s else '')+q
    return re.sub(r'\s+',' ',s).strip()
def parse(nome):
    L=[l for l in linhas(X[nome]) if not LIXO.search(l['t'])]
    Apos=[i for i,l in enumerate(L) if re.match(r'^\(?[Aa]\s*[).]',l['t'])]
    ch=cadeia(candidatos(L),Apos); idx={i:(n,r) for i,n,r in ch}
    qs={}; livre=[]; cur=None; letra=None; modo='livre'; sec=''; ultimo_txt=''
    SECRE=re.compile(r'^(L[ÍI]NGUA PORTUGUESA|PORTUGU[ÊE]S|RACIOC[ÍI]NIO|MATEM[ÁA]TICA|INFORM[ÁA]TICA|NO[ÇC][ÕO]ES|CONHECIMENTOS|DIREITO|LEGISLA[ÇC][ÃA]O|[ÉE]TICA|DIREITOS HUMANOS|HIST[ÓO]RIA|GEOGRAFIA|ATUALIDADES|ADMINISTRA|EXECU[ÇC][ÃA]O PENAL|CRIMINOLOGIA|SEGURAN[ÇC]A)',re.I)
    first=ch[0][0] if ch else 0
    for i,l in enumerate(L):
        t=l['t']
        if i<first: 
            continue
        if len(t)<70 and SECRE.search(t.upper()) and (t.upper()==t or (l.get('sz',0)>=11 and len(t)<45 and not re.search(r'[.?:]$',t))): sec=t.upper(); 
        if i in idx:
            if livre:
                tx=junta([x['t'] for x in livre])
                if len(tx)>=200: ultimo_txt=tx
            livre=[]
            n,r=idx[i]; cur={'n':n,'e':[r] if r else [],'a':{},'sec':sec,'ctx':ultimo_txt}; qs[n]=cur; modo='enun'; letra=None; continue
        if cur is None: continue
        if re.fullmatch(r'\d{1,3}',t): continue
        m=AL.match(t)
        if m and modo in ('enun','alt'):
            L2=m.group(1).upper()
            if (letra is None and L2=='A' and (cur['e'] or modo=='enun')) or (letra and L2==chr(ord(letra)+1)):
                letra=L2; cur['a'][L2]=[m.group(2)]; modo='alt'; continue
        if modo=='enun': cur['e'].append(t); continue
        if modo=='alt':
            ult=junta(cur['a'][letra])
            if (not re.search(r'[.;?!]$',ult) or re.match(r'^[a-zà-ú(]',t)) and len(cur['a'][letra])<5:
                cur['a'][letra].append(t); continue
            modo='livre'
        livre.append(l)
    return qs
if __name__=='__main__':
    for k in sorted(X):
        if not k.endswith('_prova') or k=='e15_prova': continue
        qs=parse(k); bons=[n for n,q in qs.items() if len(q['a'])>=4 and q['e']]
        print(k, 'questões', len(qs), 'max', max(qs) if qs else 0, 'com alternativas', len(bons), 'alts', collections.Counter(len(q['a']) for q in qs.values()))
