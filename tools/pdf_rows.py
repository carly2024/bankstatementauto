import json,sys
def rows(items):
    # dedupe
    seen=set();its=[]
    for x,y,s in items:
        k=(x,y,s)
        if k in seen: continue
        seen.add(k); its.append((x,y,s))
    dates=sorted([(y,x) for x,y,s in its if s=='2026' and x<90],reverse=True)
    # row anchor y = date y; collect items within [y-12.5, y+12.5) closest-anchor assignment
    out=[]
    ys=[d[0] for d in dates]
    for ri,(dy,_) in enumerate(dates,1):
        sel=[]
        for x,y,s in its:
            if y>1000: continue
            # nearest anchor
            a=min(ys,key=lambda v:abs(v-y))
            if a==dy and abs(y-dy)<=14 and 55<x<1000: sel.append((x,y,s))
        sel.sort(key=lambda t:(-t[1],t[0]))
        txt=' '.join(s for x,y,s in sel)
        out.append((ri,txt))
    return out
if __name__=='__main__':
    pages=json.load(open(sys.argv[1]))
    pn=int(sys.argv[2])
    for ri,t in rows(pages[pn-1]): print(pn,ri,t)
