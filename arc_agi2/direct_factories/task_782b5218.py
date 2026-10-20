"""Learn the cleared edge and fill every barrier-separated region beyond it."""
TEMPLATE='''import numpy as np
from collections import deque

BG, WALL = __BG__, __WALL__
EDGES=('top','right','bottom','left')


def _apply(grid,edge):
    g=np.asarray(grid,dtype=int)
    if g.ndim!=2 or not g.size:raise ValueError('Expected rectangular grid')
    hues=set(map(int,np.unique(g)))-{BG,WALL}
    if len(hues)!=1:raise ValueError('Expected one scatter colour')
    fill=next(iter(hues));h,w=g.shape
    if not np.any(g==WALL):raise ValueError('Missing barrier')
    seeds={'top':[(0,c) for c in range(w)],'bottom':[(h-1,c) for c in range(w)],'left':[(r,0) for r in range(h)],'right':[(r,w-1) for r in range(h)]}[edge]
    clear=np.zeros(g.shape,dtype=bool);todo=deque()
    for p in seeds:
        if g[p]!=WALL:clear[p]=True;todo.append(p)
    while todo:
        r,c=todo.popleft()
        for a,b in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if 0<=a<h and 0<=b<w and not clear[a,b] and g[a,b]!=WALL:
                clear[a,b]=True;todo.append((a,b))
    return np.where(g==WALL,WALL,np.where(clear,BG,fill))


def solve(demonstrations,grid):
    if not demonstrations:raise ValueError('Demonstrations required')
    alive=set(EDGES)
    for p in demonstrations:
        alive &= {e for e in alive if np.array_equal(_apply(p['input'],e),np.asarray(p['output']))}
    if not alive:raise ValueError('No demonstrated cleared edge')
    outputs=[_apply(grid,e) for e in sorted(alive)]
    if any(not np.array_equal(a,outputs[0]) for a in outputs[1:]):raise ValueError('Ambiguous cleared edge')
    return outputs[0].tolist()
'''


def build_program(d4,palette):
    return TEMPLATE.replace('__BG__',str(int(palette[0]))).replace('__WALL__',str(int(palette[2])))
