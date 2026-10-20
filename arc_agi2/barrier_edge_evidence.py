"""Independent contiguous-profile check and directional scan of barrier sides."""
from .colour_evidence import MissingColourEvidence

EDGES=('top','right','bottom','left')


def profile_output(grid,edge,palette):
    bg,wall=palette[0],palette[2];h,w=len(grid),len(grid[0])
    hues=set(v for row in grid for v in row)-{bg,wall}
    if len(hues)!=1:raise ValueError('Expected one scatter colour')
    fill=next(iter(hues));out=[[bg]*w for _ in range(h)]
    if edge in ('top','bottom'):
        lines=[[(r,c) for r in (range(h) if edge=='top' else range(h-1,-1,-1))] for c in range(w)]
    else:
        lines=[[(r,c) for c in (range(w) if edge=='left' else range(w-1,-1,-1))] for r in range(h)]
    intervals=[];depth=len(lines[0])
    for line in lines:
        hits=[i for i,(r,c) in enumerate(line) if grid[r][c]==wall]
        if not hits:intervals.append(None);continue
        if hits!=list(range(hits[0],hits[-1]+1)):raise ValueError('Barrier has separate runs in scan line')
        a,b=hits[0],hits[-1];intervals.append((a,b))
        for i,(r,c) in enumerate(line):out[r][c]=wall if a<=i<=b else fill if i>b else bg
    if all(x is None for x in intervals):raise ValueError('Missing barrier')
    # Native clipped columns have no cells below the barrier. Adjacent finite
    # profiles must overlap or diagonally touch to prevent a four-neighbour leak.
    for a,b in zip(intervals,intervals[1:]):
        if a is None and b is None:continue
        if a is None:
            if b[1]!=depth-1:raise ValueError('Unsealed clipped profile')
        elif b is None:
            if a[1]!=depth-1:raise ValueError('Unsealed clipped profile')
        elif a[0]>b[1]+1 or b[0]>a[1]+1:raise ValueError('Gap between profiles')
    return out


def region_output(grid,edge,palette):
    bg,wall=palette[0],palette[2];h,w=len(grid),len(grid[0])
    hues=set(v for row in grid for v in row)-{bg,wall}
    if len(hues)!=1 or not any(wall in row for row in grid):raise ValueError('Invalid barrier colours')
    fill=next(iter(hues));unseen={(r,c) for r in range(h) for c in range(w) if grid[r][c]!=wall}
    out=[[wall if v==wall else bg for v in row] for row in grid]
    while unseen:
        seed=next(iter(unseen));unseen.remove(seed);component={seed};stack=[seed]
        while stack:
            r,c=stack.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in unseen:unseen.remove(p);component.add(p);stack.append(p)
        reaches=any({'top':r==0,'bottom':r==h-1,'left':c==0,'right':c==w-1}[edge] for r,c in component)
        if not reaches:
            for r,c in component:out[r][c]=fill
    return out


def require_barrier_edge_evidence(demonstrations,queries,palette):
    if not demonstrations:raise MissingColourEvidence('782b5218: demonstrations required')
    alive=set(EDGES)
    for p in demonstrations:
        good=set()
        for e in alive:
            try:
                if region_output(p['input'],e,palette)==p['output']:good.add(e)
            except (ValueError,IndexError):pass
        alive=good
    if not alive:raise MissingColourEvidence('782b5218: no demonstrated barrier profile')
    for q in queries:
        answers=set()
        for e in alive:
            try:answers.add(tuple(map(tuple,region_output(q['input'],e,palette))))
            except (ValueError,IndexError):pass
        if len(answers)!=1:raise MissingColourEvidence('782b5218: unresolved barrier profile')
