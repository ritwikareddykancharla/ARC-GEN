"""Learn symmetry priorities for band analogies instead of hidden tie order.

Pure geometry is tried before geometry-plus-recolouring, as in this family.
Each stage has its own unknown ordering of the eight D4 operations. All 8!
priorities are compared compactly, avoiding a hard-coded mirror preference.
"""
from functools import lru_cache
from itertools import permutations
import numpy as np
from .augmentation import transformed
from .colour_evidence import MissingColourEvidence

_PRIORITIES=np.array(list(permutations(range(8))),dtype=np.uint8)


@lru_cache(maxsize=255)
def _first_choices(mask):
    if not mask:raise ValueError('Empty symmetry mask')
    fits=((mask>>_PRIORITIES)&1)!=0
    return _PRIORITIES[np.arange(len(_PRIORITIES)),np.argmax(fits,axis=1)]


def _groups(indices):
    groups=[]
    for i in indices:
        if not groups or i!=groups[-1][-1]+1:groups.append([])
        groups[-1].append(i)
    return groups


def analogy_bands(g,bg,d4):
    h,w=len(g),len(g[0]);columns=d4%2==0
    rows=_groups([r for r,row in enumerate(g) if any(v!=bg for v in row)])
    cols=_groups([c for c in range(w) if any(g[r][c]!=bg for r in range(h))])
    strips,bands=(cols,rows) if columns else (rows,cols)
    if len(strips)!=3 or not bands:raise MissingColourEvidence('b0722778: expected three strips')
    first=(d4%4 in (0,1)) != (d4>=4)
    al,bl,cl=strips if first else strips[::-1]
    span=len(cl)
    if any(len(s)!=2 for s in strips) or any(len(b)!=2 for b in bands):
        raise MissingColourEvidence('b0722778: expected 2x2 band blocks')
    def block(strip,band):
        return [[g[r][c] for c in strip] for r in band] if columns else [[g[r][c] for c in band] for r in strip]
    result=[]
    for band in bands:
        a,b,c=(block(strip,band) for strip in (al,bl,cl))
        pure={};mapped={}
        for action in range(8):
            ta=transformed(a,action,list(range(10)))
            tc=transformed(c,action,list(range(10)))
            if ta==b:pure[action]=tc
            mapping={};consistent=True
            for row1,row2 in zip(ta,b):
                for u,v in zip(row1,row2):
                    if u in mapping and mapping[u]!=v:consistent=False
                    mapping[u]=v
            if consistent:mapped[action]=[[mapping.get(v,v) for v in row] for row in tc]
        stage,options=('pure',pure) if pure else ('mapped',mapped)
        if not options:raise MissingColourEvidence('b0722778: no band transformation')
        result.append((band,stage,options))
    return columns,(h,span) if columns else (span,w),result


def require_analogy_evidence(demonstrations,queries,palette,d4):
    bg=palette[0]
    alive={stage:np.ones(len(_PRIORITIES),dtype=bool) for stage in ('pure','mapped')}
    for demo in demonstrations:
        columns,(h,w),bands=analogy_bands(demo['input'],bg,d4)
        expected=demo['output']
        if len(expected)!=h or any(len(row)!=w for row in expected):
            raise MissingColourEvidence('b0722778: wrong demonstration output shape')
        rebuilt=[[bg]*w for _ in range(h)]
        for band,stage,options in bands:
            answer=[expected[r][:] for r in band] if columns else [[row[c] for c in band] for row in expected]
            good=sum(1<<i for i,v in options.items() if v==answer)
            mask=sum(1<<i for i in options)
            alive[stage]&=((good>>_first_choices(mask))&1)!=0
            if columns:
                for r,row in zip(band,answer):rebuilt[r]=row
            else:
                for r,row in enumerate(answer):
                    for c,v in zip(band,row):rebuilt[r][c]=v
        if rebuilt!=expected:raise MissingColourEvidence('b0722778: changed separator cells')
    if not all(np.any(v) for v in alive.values()):
        raise MissingColourEvidence('b0722778: demonstrations have inconsistent operation priorities')
    for query in queries:
        _,_,bands=analogy_bands(query['input'],bg,d4)
        for band,stage,options in bands:
            mask=sum(1<<i for i in options)
            actions=np.unique(_first_choices(mask)[alive[stage]])
            if len({tuple(map(tuple,options[int(i)])) for i in actions})!=1:
                raise MissingColourEvidence('b0722778: demonstrations leave analogy operation ambiguous')
