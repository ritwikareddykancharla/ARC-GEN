"""Coordinate-set agreement across demonstrated overlapping-window conventions."""
from itertools import product
from .colour_evidence import MissingColourEvidence


def window_options(grid,palette):
    h,w=len(grid),len(grid[0]);bg,ink=palette[0],palette[1]
    boxes={}
    for y in range(h-2):
        for x in range(w-2):
            cells={(r,c) for r in range(y,y+3) for c in range(x,x+3)}
            if all(grid[r][c]==bg for r,c in cells):boxes[y,x]=cells
    claims=[set().union(*boxes.values()) if boxes else set()]
    for axis,sa,sb in product((0,1),(-1,1),(-1,1)):
        claimed=set()
        for key in sorted(boxes,key=lambda p:(sa*p[axis],sb*p[1-axis])):
            if not claimed & boxes[key]:claimed |= boxes[key]
        claims.append(claimed)
    return [[[ink if (r,c) in cells else v for c,v in enumerate(row)] for r,row in enumerate(grid)] for cells in claims]


def require_window_evidence(demonstrations,queries,palette):
    if not demonstrations:raise MissingColourEvidence('6cf79266: no demonstrations')
    alive=set(range(9))
    for p in demonstrations:alive &= {i for i,out in enumerate(window_options(p['input'],palette)) if out==p['output']}
    if not alive:raise MissingColourEvidence('6cf79266: no demonstrated window convention')
    for q in queries:
        variants=window_options(q['input'],palette)
        if len({tuple(map(tuple,variants[i])) for i in alive})!=1:raise MissingColourEvidence('6cf79266: unresolved overlapping windows')
