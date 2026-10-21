"""Extend visible3x3 motifs until their centres enter matching bars."""
TEMPLATE = '''import numpy as np
BG = __BG__


def _components(mask):
    h,w=mask.shape;remaining=set(zip(*np.where(mask)));out=[]
    while remaining:
        seed=remaining.pop();cells={seed};todo=[seed]
        while todo:
            y,x=todo.pop()
            for q in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                if q in remaining:remaining.remove(q);cells.add(q);todo.append(q)
        out.append(cells)
    return out


def _restore(grid):
    g=np.asarray(grid,dtype=int)
    if g.ndim!=2 or not g.size:raise ValueError('Expected rectangular grid')
    h,w=g.shape;tiles=[]
    for y in range(1,h-1):
        for x in range(1,w-1):
            c=int(g[y,x]);f=int(g[y-1,x-1]);patch=g[y-1:y+2,x-1:x+2]
            if c in (BG,f) or f==BG:continue
            ring=patch.copy();ring[1,1]=f
            if np.all(ring==f):tiles.append((y,x,c,f,patch.copy()))
    if not tiles or len({t[3] for t in tiles})!=1:raise ValueError('Missing or inconsistent motifs')
    bars={};covered=np.zeros(g.shape,dtype=bool);out=np.full(g.shape,BG,dtype=int)
    for c in {t[2] for t in tiles}:
        large=[cells for cells in _components(g==c) if len(cells)>1]
        if len(large)!=1:raise ValueError('Matching bar is not unique')
        cells=large[0];ys,xs=zip(*cells);box=(min(ys),min(xs),max(ys),max(xs))
        y0,x0,y1,x1=box
        if len(cells)!=(y1-y0+1)*(x1-x0+1):raise ValueError('Matching object is not a solid bar')
        bars[c]=box;covered[y0:y1+1,x0:x1+1]=True;out[y0:y1+1,x0:x1+1]=c
    for y,x,c,f,patch in tiles:covered[y-1:y+2,x-1:x+2]=True
    if not np.array_equal(covered,g!=BG):raise ValueError('Unexplained input cells')
    used=np.zeros(g.shape,dtype=bool)
    for y,x,c,f,patch in tiles:
        y0,x0,y1,x1=bars[c]
        rows=y0<=y<=y1;cols=x0<=x<=x1
        if rows==cols:raise ValueError('Motif must face its bar along one axis')
        dy,dx=(0,1 if x<x0 else -1) if rows else (1 if y<y0 else -1,0)
        while True:
            if not(1<=y<h-1 and 1<=x<w-1):raise ValueError('Motif would leave grid')
            area=out[y-1:y+2,x-1:x+2]
            if np.any(used[y-1:y+2,x-1:x+2]) or np.any((area!=BG)&(area!=c)):raise ValueError('Motif paths collide')
            area[:]=patch;used[y-1:y+2,x-1:x+2]=True
            if y0<=y<=y1 and x0<=x<=x1:break
            if (dy>0 and y>y1) or (dy<0 and y<y0) or (dx>0 and x>x1) or (dx<0 and x<x0):raise ValueError('Motif centre jumped over bar')
            y+=3*dy;x+=3*dx
    return out.tolist()


def solve(demonstrations,grid):
    for p in demonstrations:
        if _restore(p['input'])!=p['output']:raise ValueError('Demonstration contradicts centre-entry stamping')
    return _restore(grid)
'''


def build_program(d4,palette):
    return TEMPLATE.replace('__BG__',str(int(palette[8])))
