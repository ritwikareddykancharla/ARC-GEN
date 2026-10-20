"""Restore occluded symmetry from demonstration-supported axis and extent."""
TEMPLATE = '''import numpy as np
BG = __BG__


def _options(grid):
    g=np.asarray(grid,dtype=int)
    if g.ndim!=2 or not g.size:raise ValueError('Expected rectangular grid')
    colours=[int(v) for v in np.unique(g) if v!=BG]
    if len(colours)!=2:raise ValueError('Expected sprite and occluder colours')
    h,w=g.shape;options={}
    for occ in colours:
        hy,hx=np.where(g==occ)
        bh,bw=int(hy.max()-hy.min()+1),int(hx.max()-hx.min()+1)
        if len(hy)!=bh*bw:continue
        shape=next(c for c in colours if c!=occ);sy,sx=np.where(g==shape)
        for axis,n,span in ((0,h,bh),(1,w,bw)):
            outputs=set()
            for s in range(2*n-1):
                my,mx=(s-hy,hx) if axis==0 else (hy,s-hx)
                if not np.all((my>=0)&(my<h)&(mx>=0)&(mx<w)):continue
                if np.any(g[my,mx]==occ):continue
                py,px=(s-sy,sx) if axis==0 else (sy,s-sx)
                if not np.all((py>=0)&(py<h)&(px>=0)&(px<w)):continue
                mirrored=g[py,px]
                if np.any((mirrored!=occ)&(mirrored!=shape)):continue
                out=g.copy();out[hy,hx]=np.where(g[my,mx]==shape,shape,BG)
                outputs.add(tuple(tuple(int(v) for v in row) for row in out))
            if outputs:options.setdefault((axis,span),set()).update(outputs)
    return options


def solve(demonstrations,grid):
    if not demonstrations:raise ValueError('Demonstrations required to identify removed rectangle')
    alive=None
    for p in demonstrations:
        expected=tuple(tuple(row) for row in p['output'])
        matching={rule for rule,outs in _options(p['input']).items() if outs=={expected}}
        alive=matching if alive is None else alive&matching
    if not alive:raise ValueError('No common demonstrated mirror/rectangle rule')
    options=_options(grid)
    if any(rule not in options for rule in alive):raise ValueError('Demonstrated rule has no valid query restoration')
    answers=set().union(*(options[rule] for rule in alive))
    if len(answers)!=1:raise ValueError('Ambiguous occluder or mirror reconstruction')
    return [list(row) for row in next(iter(answers))]
'''


def build_program(d4,palette):
    return TEMPLATE.replace('__BG__',str(int(palette[0])))
