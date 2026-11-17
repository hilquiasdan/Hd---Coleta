import json,re
X={}
def gab(nome):
    G={}
    for P in X[nome]:
        rows=[' '.join(s[3] for s in segs) for y,segs in P['l']]
        rows=[re.sub(r'\s+',' ',r).strip() for r in rows]
        nums=None
        for r in rows:
            m=re.match(r'^(Item|Questão|Questao)\s*(.*)$',r)
            if m: nums=[int(t) for t in re.findall(r'\d+',m.group(2))]; continue
            m=re.match(r'^Gabarito\s*(.*)$',r)
            if m and nums:
                vals=re.findall(r'\b([A-EX]|C|E)\b',m.group(1))
                for n,v in zip([n for n in nums if n>0],vals): G[n]=v
                nums=None
    return G
if __name__=='__main__':
    for k in X:
        if 'gab' in k: g=gab(k); print(k,len(g),min(g) if g else '-',max(g) if g else '-','anuladas:',[n for n,v in g.items() if v=='X'])
