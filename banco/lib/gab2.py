import json,re,sys
X={}
ANS=r'(?:[A-Ea-e]|[Xx]|\*|-)'
def rows(nome):
    out=[]
    for P in X[nome]:
        R=[]
        for y,segs in P['l']:
            if R and y-R[-1][0]<=2: R[-1][1].extend(segs)
            else: R.append([y,list(segs)])
        for y,segs in R:
            t=' '.join(s[3] for s in sorted(segs,key=lambda s:s[0])); t=re.sub(r'\s+',' ',t).strip()
            if t and 'pcimark' not in t: out.append(t)
    return out
LAB=re.compile(r'TIPO\s*\d|Tipo\s*\d|VERS[ÃA]O\s*[A-Z0-9]|Vers[ãa]o\s*\d|Prova:\s*[A-Z]|PROVA\s*0?\d\b|Cargo:|^[A-Z]{2,3} •|Gabarito|GABARITO',re.U)
def versoes(nome):
    V=[]; cur=None; lab=''; R=rows(nome); i=0
    def novo(l):
        nonlocal cur
        cur={}; V.append((l,cur))
    while i<len(R):
        t=R[i]
        if LAB.search(t) and not re.fullmatch(r'[\d\s]+',t):
            lab=t[:90]
            if cur is None or len(cur)>0: novo(lab)
            else: V[-1]=(V[-1][0]+' | '+lab,cur)
            i+=1; continue
        nums=t.split()
        if len(nums)>=3 and all(re.fullmatch(r'\d{1,3}',x) for x in nums) and i+1<len(R):
            nx=R[i+1].replace('ANULADA','X').split()
            if len(nx)<len(nums) and i+2<len(R) and re.fullmatch(r'(ANULADA\s*)+',R[i+1].strip()):
                nx=R[i+2].split(); i+=1
            if len(nx)==len(nums) and all(re.fullmatch(ANS,x) for x in nx):
                if cur is None: novo('?')
                for n,a in zip(nums,nx): cur[int(n)]=a.upper()
                i+=2; continue
        ps=re.findall(r'(?:^|\s)0*(\d{1,3})\s*[–-]?\s*('+ANS+r')(?=\s|$)',t)
        if ps and len(ps)*2>=len(t.split())*0.4:
            if cur is None: novo('?')
            for n,a in ps: cur.setdefault(int(n),a.upper())
        i+=1
    return [(l,d) for l,d in V if len(d)>=10]
if __name__=='__main__':
    for k in sorted(X):
        if k.endswith('_gab'):
            vs=versoes(k); print(k,[(l[:50],len(d),min(d),max(d)) for l,d in vs][:8])
