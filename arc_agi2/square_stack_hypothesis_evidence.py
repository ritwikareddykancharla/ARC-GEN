"""Square counts from disjoint maximal blocks; output pixels computed by coverage."""
from collections import Counter
from itertools import product
from arc_agi2.colour_evidence import MissingColourEvidence, IntrinsicQueryEvidence


def features(g):
    h,w=len(g),len(g[0]);hist=Counter(v for row in g for v in row);groups={};has_block={}
    for color in hist:
        has_block[color]=any(all(g[y][x]==color for y in (r,r+1) for x in (c,c+1)) for r in range(h-1) for c in range(w-1))
        found=[]
        for r in range(h):
            for c in range(w):
                if g[r][c]!=color or (r and g[r-1][c]==color) or (c and g[r][c-1]==color):continue
                size=1
                while c+size<w and g[r][c+size]==color:size+=1
                if size not in (2,3,4) or r+size>h:continue
                box={(y,x) for y in range(r,r+size) for x in range(c,c+size)}
                if any(g[y][x]!=color for y,x in box):continue
                rim={(y+dy,x+dx) for y,x in box for dy,dx in ((1,0),(-1,0),(0,1),(0,-1))}-box
                if any(0<=y<h and 0<=x<w and g[y][x]==color for y,x in rim):continue
                found.append(size)
        if found and len(set(found))==1 and len(found)*found[0]**2==hist[color]:groups[color]=(found[0],len(found))
    options=[]
    # Try background/noise roles first, unlike the source's size-group Cartesian product.
    for bg in hist:
        for noise in [None]+[c for c in hist if c!=bg]:
            if noise is not None and has_block[noise]:continue
            selected=set(hist)-{bg,noise}
            if len(selected)!=3 or not selected<=groups.keys():continue
            if {groups[c][0] for c in selected}!={2,3,4}:continue
            options.append((bg,{groups[c][0]:(c,groups[c][1]) for c in selected}))
    if len(options)!=1:raise ValueError('Background/noise roles not uniquely visible')
    return options[0]


def render(data,mode,ac,sr,af):
    bg,sizes=data;count=max(n for c,n in sizes.values())
    if mode=='cap':count=min(count,2*sizes[4][1])
    stack_sizes=[[s for s,(c,n) in sizes.items() if n>i] for i in range(count)]
    length=sum(max(ss)+1 for ss in stack_sizes);depth=5
    out=[[bg]*(length if ac else depth) for _ in range(depth if ac else length)]
    for r,row in enumerate(out):
        for c in range(len(row)):
            along=c if ac else r;across=r if ac else c
            if sr:along=length-1-along
            if af:across=depth-1-across
            offset=0
            for ss in stack_sizes:
                width=max(ss)+1
                if offset<=along<offset+width:
                    cover=[s for s in ss if along-offset<s and across<s]
                    if cover:row[c]=sizes[min(cover)][0]
                    break
                offset+=width
    return out


def require_evidence(demonstrations,queries,palette=None):
    if not demonstrations:raise MissingColourEvidence('b1986d4b: missing demonstrations')
    alive=list(product(('all','cap'),(False,True),(False,True),(False,True)))
    try:
        for pair in demonstrations:
            data=features(pair['input']);alive=[p for p in alive if render(data,*p)==pair['output']]
        if not alive:raise ValueError('No demonstrated hypothesis')
        for q in queries:
            try:data=features(q['input'])
            except ValueError as exc:raise IntrinsicQueryEvidence('b1986d4b: '+str(exc)) from exc
            if len({tuple(map(tuple,render(data,*p))) for p in alive})!=1:raise ValueError('Unresolved stack cap or orientation')
    except IntrinsicQueryEvidence:raise
    except ValueError as e:raise MissingColourEvidence('b1986d4b: '+str(e)) from e
