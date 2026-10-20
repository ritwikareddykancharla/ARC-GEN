"""Visible-coordinate wallpaper recovery; no guessed residue or crop fallback."""
PROGRAM = '''import itertools
import numpy as np


def _recover(grid):
    g=np.asarray(grid,dtype=int)
    if g.ndim!=2 or not g.size:raise ValueError('Expected rectangular grid')
    h,w=g.shape
    rectangles=[]
    for colour in np.unique(g):
        ys,xs=np.where(g==colour)
        y0,y1,x0,x1=int(ys.min()),int(ys.max()),int(xs.min()),int(xs.max())
        bh,bw=y1-y0+1,x1-x0+1
        if bh>=2 and bw>=2 and len(ys)==bh*bw:rectangles.append((bh*bw,y0,x0,y1,x1))
    predictions=set();unknown=False
    periods=[(a,b) for a in range(1,min(h,16)+1) for b in range(1,min(w,16)+1) if a*b<=16]
    for count in (2,3):
        for blocks in itertools.combinations(rectangles,count):
            sizes=sorted((b[3]-b[1]+1,b[4]-b[2]+1) for b in blocks)
            if any(a[0]>b[0] or a[1]>b[1] or a==b for a,b in zip(sizes,sizes[1:])):continue
            big=max(blocks)
            if sum(b[0]==big[0] for b in blocks)!=1:continue
            mask=np.zeros(g.shape,dtype=bool)
            for _,y0,x0,y1,x1 in blocks:mask[y0:y1+1,x0:x1+1]=True
            ys,xs=np.where(~mask);vals=g[ys,xs]
            _,y0,x0,y1,x1=big
            by=np.arange(y0,y1+1)[:,None];bx=np.arange(x0,x1+1)[None,:]
            for py,px in periods:
                keys=(ys%py)*px+xs%px;n=py*px
                lo=np.full(n,10,dtype=int);hi=np.full(n,-1,dtype=int)
                np.minimum.at(lo,keys,vals);np.maximum.at(hi,keys,vals)
                observed=hi>=0
                if np.any(lo[observed]!=hi[observed]):continue
                needed=(by%py)*px+bx%px
                if not np.all(observed[needed]):unknown=True;continue
                predictions.add(tuple(tuple(int(v) for v in row) for row in lo[needed]))
    if unknown or len(predictions)!=1:raise ValueError('Visible wallpaper does not determine a unique patch')
    return [list(row) for row in next(iter(predictions))]


def solve(demonstrations,grid):
    for pair in demonstrations:
        if _recover(pair['input'])!=pair['output']:raise ValueError('Wallpaper rule contradicts demonstration')
    return _recover(grid)
'''


def build_program(d4,palette):
    return PROGRAM
