"""Independent coordinate-set verification of occluded reflection mechanisms."""
from .colour_evidence import MissingColourEvidence


def reflection_options(grid,palette):
    bg=palette[0];h=len(grid);w=len(grid[0]);cells={}
    if any(len(row)!=w for row in grid):raise ValueError('Ragged grid')
    for y,row in enumerate(grid):
        for x,value in enumerate(row):
            if value!=bg:cells.setdefault(value,set()).add((y,x))
    if len(cells)!=2:raise ValueError('Expected two object colours')
    options={}
    for occ,hidden in cells.items():
        ys,xs=zip(*hidden);bh,bw=max(ys)-min(ys)+1,max(xs)-min(xs)+1
        if bh*bw!=len(hidden):continue
        shape=next(c for c in cells if c!=occ);visible=cells[shape]
        for axis,extent,span in ((0,h,bh),(1,w,bw)):
            outs=set()
            for total in range(2*extent-1):
                reflect=lambda y,x:(total-y,x) if axis==0 else (y,total-x)
                partners={reflect(y,x) for y,x in hidden}
                if partners&hidden or any(not(0<=y<h and 0<=x<w) for y,x in partners):continue
                mirrored={reflect(y,x) for y,x in visible}
                if any(not(0<=y<h and 0<=x<w) for y,x in mirrored):continue
                if not mirrored<=visible|hidden:continue
                restored=visible|{(y,x) for y,x in hidden if reflect(y,x) in visible}
                if {reflect(y,x) for y,x in restored}!=restored:raise ValueError('Internal reflection inconsistency')
                outs.add(tuple(tuple(shape if (y,x) in restored else bg for x in range(w)) for y in range(h)))
            if outs:options.setdefault((axis,span),set()).update(outs)
    return options


def require_occluded_symmetry_evidence(demonstrations,queries,palette):
    try:
        if not demonstrations:raise ValueError('Demonstrations required')
        alive=None
        for p in demonstrations:
            expected=tuple(tuple(row) for row in p['output'])
            matching={r for r,outs in reflection_options(p['input'],palette).items() if outs=={expected}}
            alive=matching if alive is None else alive&matching
        if not alive:raise ValueError('No demonstrated reflection rule')
        for q in queries:
            opts=reflection_options(q['input'],palette)
            if any(r not in opts for r in alive):raise ValueError('Unsupported query')
            if len(set().union(*(opts[r] for r in alive)))!=1:raise ValueError('Ambiguous restoration')
    except (ValueError,TypeError,IndexError) as exc:raise MissingColourEvidence('3345333e: occluder/mirror mechanism not determined by demonstrations') from exc
