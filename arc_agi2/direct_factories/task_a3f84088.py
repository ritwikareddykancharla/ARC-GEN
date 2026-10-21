"""Uniform four-ring cycle; intended for the explicitly labelled teaching copy."""
TEMPLATE='''import numpy as np
BG, FRAME, NEW = __COLOURS__


def _predict(grid):
    g=np.asarray(grid,dtype=int);ys,xs=np.where(g==FRAME)
    if not len(ys):raise ValueError('Missing frame')
    a,b,c,d=int(ys.min()),int(xs.min()),int(ys.max()),int(xs.max())
    if c-a!=d-b:raise ValueError('Expected square frame')
    expected=np.full(g.shape,BG,dtype=int)
    expected[a:c+1,b]=FRAME;expected[a:c+1,d]=FRAME
    expected[a,b:d+1]=FRAME;expected[c,b:d+1]=FRAME
    if not np.array_equal(g,expected):raise ValueError('Expected one empty square frame')
    out=g.copy();cycle=(FRAME,NEW,FRAME,BG)
    for y in range(a,c+1):
        for x in range(b,d+1):out[y,x]=cycle[min(y-a,c-y,x-b,d-x)%4]
    return out


def solve(demonstrations,grid):
    if not demonstrations:raise ValueError('Demonstrations required')
    for p in demonstrations:
        if not np.array_equal(_predict(p['input']),np.asarray(p['output'])):raise ValueError('Demonstration contradicts uniform ring rule')
    return _predict(grid).tolist()
'''


def build_program(d4,palette):
    return TEMPLATE.replace('__COLOURS__',repr(tuple(int(palette[c]) for c in (0,5,2))))
