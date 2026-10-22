import re,sys,json
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdftypes import resolve1
def parse_strings(d):
    # yields ('Td',x,y) / ('Tj',bytes) / ('BT',) in order
    i=0;n=len(d);out=[]
    tok=re.compile(rb'BT|ET|(-?[\d.]+)\s+(-?[\d.]+)\s+Td|\(')
    while i<n:
        m=tok.search(d,i)
        if not m: break
        s=m.group(0)
        if s==b'BT': out.append(('BT',)); i=m.end()
        elif s==b'ET': i=m.end()
        elif s==b'(':
            j=m.end(); buf=bytearray(); depth=1
            while depth:
                c=d[j]
                if c==0x5c:
                    j+=1; c=d[j]
                    mp={ord('n'):10,ord('r'):13,ord('t'):9,ord('b'):8,ord('f'):12,ord('('):40,ord(')'):41,0x5c:0x5c}
                    if c in mp: buf.append(mp[c]); j+=1
                    elif 48<=c<=55:
                        k=j; v=0; cnt=0
                        while cnt<3 and 48<=d[k]<=55: v=v*8+d[k]-48;k+=1;cnt+=1
                        buf.append(v&255); j=k
                    elif c in (10,13): j+=1
                    else: buf.append(c); j+=1
                else:
                    if c==40: depth+=1
                    elif c==41:
                        depth-=1
                        if depth==0: j+=1; break
                    buf.append(c); j+=1
            out.append(('Tj',bytes(buf))); i=j
        else:
            out.append(('Td',float(m.group(1)),float(m.group(2)))); i=m.end()
    return out
def page_items(pg):
    items=[]; x=y=0
    conts=resolve1(pg.attrs['Contents']); 
    if not isinstance(conts,list): conts=[conts]
    data=b'\n'.join(resolve1(c).get_data() for c in conts)
    for t in parse_strings(data):
        if t[0]=='BT': x=y=0
        elif t[0]=='Td': x+=t[1]; y+=t[2]
        else:
            b=t[1]
            try: s=b.decode('utf-16-be')
            except: s=b.decode('latin1')
            items.append((round(x,1),round(y,1),s))
    return items
def load(path):
    doc=PDFDocument(PDFParser(open(path,'rb')))
    return [page_items(pg) for pg in PDFPage.create_pages(doc)]
if __name__=='__main__':
    pages=load(sys.argv[1])
    json.dump(pages,open(sys.argv[2],'w'),ensure_ascii=False)
    print(len(pages))
