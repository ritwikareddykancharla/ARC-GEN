TEMPLATE = '''def _components(g, h, w, color):
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if g[y][x] == color and not seen[y][x]:
                stack = [(y, x)]
                seen[y][x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == color:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                comps.append(cells)
    return comps


def _features(grid):
    from itertools import product
    g = [[int(v) for v in row] for row in grid]
    h,w=len(g),len(g[0]);colours={v for row in g for v in row};groups={}
    has_block={c:any(g[r][x]==g[r+1][x]==g[r][x+1]==g[r+1][x+1]==c for r in range(h-1) for x in range(w-1)) for c in colours}
    for colour in colours:
        comps=_components(g,h,w,colour);sides=set();valid=True
        for cells in comps:
            ys=[p[0] for p in cells];xs=[p[1] for p in cells]
            side=max(ys)-min(ys)+1
            if side not in (2,3,4) or max(xs)-min(xs)+1!=side or len(cells)!=side*side:valid=False;break
            sides.add(side)
        if valid and len(sides)==1:groups[colour]=(next(iter(sides)),len(comps))
    candidates=[]
    for choice in product(*[[c for c,v in groups.items() if v[0]==size] for size in (2,3,4)]):
        remaining=colours-set(choice)
        for bg in remaining:
            noise=remaining-{bg}
            if len(noise)>1 or any(has_block[c] for c in noise):continue
            candidates.append((bg,{c:groups[c] for c in choice}))
    if len(candidates)!=1:raise ValueError('Background/noise and square roles are not uniquely visible')
    return candidates[0]


def _render(features, mode, along_cols, strip_rev, anchor_far):
    bg, squares = features
    order = sorted(squares, key=lambda c: (-squares[c][0], c))
    depth = max(s for s, _ in squares.values()) + 1
    nst = max(n for _, n in squares.values())
    if mode == 'cap':
        nst = min(nst, 2 * next(n for s, n in squares.values() if s == 4))
    stacks = []
    for i in range(nst):
        inc = [(c, squares[c][0]) for c in order if squares[c][1] > i]
        stacks.append(inc)
    length = sum(max(s for _, s in inc) + 1 for inc in stacks)
    if along_cols:
        out = [[bg] * length for _ in range(depth)]
    else:
        out = [[bg] * depth for _ in range(length)]
    x = 0
    for inc in stacks:
        for c, s in inc:
            for a in range(s):
                pa = x + a
                if strip_rev:
                    pa = length - 1 - pa
                for b in range(s):
                    pb = depth - 1 - b if anchor_far else b
                    if along_cols:
                        out[pb][pa] = c
                    else:
                        out[pa][pb] = c
        x += max(s for _, s in inc) + 1
    return out


def solve(demonstrations, grid):
    if not demonstrations:raise ValueError('Demonstrations required')
    hypotheses=[(mode,ac,sr,af) for mode in ('all','cap') for ac in (False,True) for sr in (False,True) for af in (False,True)]
    for pair in demonstrations:
        features=_features(pair['input'])
        hypotheses=[p for p in hypotheses if _render(features,*p)==pair['output']]
    if not hypotheses:raise ValueError('No demonstrated square-stack mechanism')
    features=_features(grid)
    answers={tuple(map(tuple,_render(features,*p))) for p in hypotheses}
    if len(answers)!=1:raise ValueError('Demonstrations leave stack count or orientation unresolved')
    return list(map(list,next(iter(answers))))
'''

def build_program(d4, palette):
    return TEMPLATE
