"""Independent cell-set gate for Chebyshev-nearest-square attraction."""
from .colour_evidence import MissingColourEvidence

ORDERS=tuple((axis,s,t) for axis in (0,1) for s in (1,-1) for t in (1,-1))
def nearest_predictions(grid,palette):
    bg,point,block=map(int,(palette[0],palette[1],palette[2]))
    cells={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==block}
    blocks=[]
    while cells:
        seed=min(cells);cells.remove(seed);component={seed};todo=[seed]
        while todo:
            r,c=todo.pop()
            for n in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if n in cells:cells.remove(n);component.add(n);todo.append(n)
        rows=sorted({r for r,c in component});cols=sorted({c for r,c in component})
        if len(component)!=4 or len(rows)!=2 or len(cols)!=2 or rows[1]-rows[0]!=1 or cols[1]-cols[0]!=1:
            raise MissingColourEvidence('Nearest-square rule requires distinct 2x2 blocks')
        blocks.append(component)
    if not blocks:raise MissingColourEvidence('No visible square')
    points=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==point]
    answers=[]
    for axis,sign,second in ORDERS:
        def key(b):
            centre=(sum(r for r,c in b),sum(c for r,c in b))
            return sign*centre[axis],second*centre[1-axis]
        out=[[bg if v==point else int(v) for v in row] for row in grid]
        for r,c in points:
            best=min(blocks,key=lambda b:(min(max(abs(r-y),abs(c-x)) for y,x in b),key(b)))
            rows={y for y,x in best};cols={x for y,x in best}
            dest=(r,c)
            if r in rows:dest=(r,min(cols)-1 if c<min(cols) else max(cols)+1)
            elif c in cols:dest=(min(rows)-1 if r<min(rows) else max(rows)+1,c)
            y,x=dest
            if not(0<=y<len(out) and 0<=x<len(out[0])):raise MissingColourEvidence('Attraction destination outside canvas')
            out[y][x]=point
        answers.append(tuple(tuple(row) for row in out))
    return answers

def require_nearest_square_evidence(demonstrations,queries,palette):
    if not demonstrations:raise MissingColourEvidence('No demonstrations for tie convention')
    alive=set(range(8))
    for d in demonstrations:
        expected=tuple(tuple(map(int,row)) for row in d['output'])
        predictions=nearest_predictions(d['input'],palette)
        alive &= {i for i,p in enumerate(predictions) if p==expected}
    if not alive:raise MissingColourEvidence('No visible nearest-square convention fits all demos')
    for q in queries:
        predictions=nearest_predictions(q['input'],palette)
        if len({predictions[i] for i in alive})!=1:raise MissingColourEvidence('Query attraction tie unresolved by demos')
    return {'surviving_orders':len(alive)}
