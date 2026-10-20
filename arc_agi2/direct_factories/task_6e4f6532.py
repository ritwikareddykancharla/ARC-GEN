TEMPLATE = '''import itertools

BODY = __BODY__
CORE = __CORE__
TRANSFORMS = ((1,0,0,1),(0,1,-1,0),(-1,0,0,-1),(0,-1,1,0),(1,0,0,-1),(0,-1,-1,0),(-1,0,0,1),(0,1,1,0))
STEP4 = ((1,0),(-1,0),(0,1),(0,-1))
STEP8 = STEP4 + ((1,1),(1,-1),(-1,1),(-1,-1))
PRIORITIES = tuple(itertools.permutations(range(4))) + ('any','all')

def _comps(mask, H, W, steps):
    seen = [[False] * W for _ in range(H)]
    out = []
    for y in range(H):
        for x in range(W):
            if mask[y][x] and not seen[y][x]:
                seen[y][x] = True
                stack = [(y, x)]
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in steps:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                out.append(cells)
    return out


def _norm(cells):
    my = min(y for y, _ in cells)
    mx = min(x for _, x in cells)
    return frozenset((y - my, x - mx) for y, x in cells), my, mx


def _geometry(grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0])
    counts = {}
    order = []
    for row in g:
        for v in row:
            if v not in counts:
                counts[v] = 0
                order.append(v)
            counts[v] += 1
    backgrounds = [c for c in order if counts[c] == max(counts.values())]
    if len(backgrounds) != 1:raise ValueError("Ambiguous background")
    bg = backgrounds[0]
    wall = [[False] * W for _ in range(H)]
    for col in order:
        if col == bg:
            continue
        mask = [[v == col for v in row] for row in g]
        for comp in _comps(mask, H, W, STEP4):
            if any(y in (0, H - 1) or x in (0, W - 1) for y, x in comp):
                for y, x in comp:
                    wall[y][x] = True
    free = [[g[y][x] != bg and not wall[y][x] for x in range(W)] for y in range(H)]
    seen = [[False] * W for _ in range(H)]
    ships = []
    for y in range(H):
        for x in range(W):
            if g[y][x] == BODY and free[y][x] and not seen[y][x]:
                seen[y][x] = True
                stack = [(y, x)]
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in STEP4:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and free[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                ships.append(cells)
    tmask = [[g[y][x] == CORE and not seen[y][x] for x in range(W)] for y in range(H)]
    targets = _comps(tmask, H, W, STEP8)
    tnorms = [_norm(t) for t in targets]
    canvas = [[bg if free[y][x] else g[y][x] for x in range(W)] for y in range(H)]
    return g, wall, ships, tnorms, canvas


def _predictions(grid):
    g, wall, ships, targets, base = _geometry(grid)
    H, W = len(g), len(g[0])
    if not ships or len(ships) != len(targets):
        raise ValueError('Ships and targets must correspond')
    all_choices = []
    for cells in ships:
        choices = []
        for a,b,c,d in TRANSFORMS:
            tc = {(a*y+b*x,c*y+d*x):g[y][x] for y,x in cells}
            core = [p for p,v in tc.items() if v==CORE]
            if not core:continue
            cn,cy,cx = _norm(core)
            for k,(tn,ty,tx) in enumerate(targets):
                if tn != cn:continue
                placed = {(y+ty-cy,x+tx-cx):v for (y,x),v in tc.items()}
                if any(not (0<=y<H and 0<=x<W) for y,x in placed):continue
                markers = []
                for (y,x),v in placed.items():
                    if v in (BODY,CORE):continue
                    rays = {}
                    for i,(dy,dx) in enumerate(STEP4):
                        if placed.get((y-dy,x-dx)) not in (BODY,CORE):continue
                        ry,rx=y+dy,x+dx
                        while 0<=ry<H and 0<=rx<W and not wall[ry][rx]:ry+=dy;rx+=dx
                        rays[i] = 0<=ry<H and 0<=rx<W and g[ry][rx]==v
                    markers.append(rays)
                if not markers or any(not item for item in markers):continue
                scores=[]
                for rule in PRIORITIES:
                    if rule=='any':score=sum(any(ray.values()) for ray in markers)
                    elif rule=='all':score=sum(all(ray.values()) for ray in markers)
                    else:score=sum(next(ray[i] for i in rule if i in ray) for ray in markers)
                    scores.append(score)
                choices.append((k,tuple(sorted((y,x,v) for (y,x),v in placed.items())),a*d-b*c==1,scores))
        if not choices:raise ValueError('No docking candidate')
        all_choices.append(choices)
    predictions=[]
    for ri in range(len(PRIORITIES)):
        selected=[];used=set();valid=True
        for choices in all_choices:
            best=max((item[3][ri],item[2]) for item in choices)
            winners={(item[0],item[1]) for item in choices if (item[3][ri],item[2])==best}
            if len(winners)!=1:valid=False;break
            target,cells=next(iter(winners))
            if target in used:valid=False;break
            used.add(target);selected.append(cells)
        if not valid:predictions.append(None);continue
        out=[row[:] for row in base]
        occupied=set()
        for cells in selected:
            for y,x,v in cells:
                if (y,x) in occupied:valid=False
                occupied.add((y,x));out[y][x]=v
        predictions.append(tuple(tuple(row) for row in out) if valid else None)
    return predictions


def solve(demonstrations,grid):
    if not demonstrations:raise ValueError('Demonstrations required')
    alive=set(range(len(PRIORITIES)))
    for demo in demonstrations:
        expected=tuple(tuple(row) for row in demo['output'])
        alive &= {i for i,p in enumerate(_predictions(demo['input'])) if p==expected}
    if not alive:raise ValueError('No consistent demonstrated marker rule')
    query=_predictions(grid)
    answers={query[i] for i in alive}
    if None in answers or len(answers)!=1:raise ValueError('Unresolved marker priority or docking tie')
    return [list(row) for row in next(iter(answers))]
'''


def build_program(d4,palette):
    return TEMPLATE.replace('__BODY__',str(int(palette[8]))).replace('__CORE__',str(int(palette[9])))
