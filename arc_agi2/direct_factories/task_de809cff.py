PROGRAM_TEMPLATE = '''
BG = __BG__
MARK = __MARK__


def _components(mask, H, W):
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
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                out.append(cells)
    return out


def _solid_core(g, c, H, W):
    # Cells lying in at least one fully-c 2x2 block. This is exactly the core
    # notion the constructor's _recognisable invariant certifies. There is no
    # run bridging, so a lone same-colour foreign pixel in a 1-cell gap can
    # never fuse two distinct rectangles.
    core = [[False] * W for _ in range(H)]
    for y in range(H - 1):
        for x in range(W - 1):
            if g[y][x] == c and g[y][x + 1] == c and g[y + 1][x] == c and g[y + 1][x + 1] == c:
                core[y][x] = core[y][x + 1] = True
                core[y + 1][x] = core[y + 1][x + 1] = True
    return core


def _rectangle_readings(g, cols, H, W):
    # Small raw-core fragments can be separated by holes/foreign pixels.
    # Enumerate partitions, retaining all rectangles consistent with the
    # observed cores and the single/domino-hole grammar.
    colour_options=[]
    for colour in cols:
        comps=[set(c) for c in _components(_solid_core(g,colour,H,W),H,W)]
        n=len(comps)
        if not n or n>10:raise ValueError('Unsupported core decomposition')
        candidates=[]
        for mask in range(1,1<<n):
            cells=set().union(*(comps[i] for i in range(n) if mask>>i&1))
            if len(cells)<9:continue
            ys,xs=zip(*cells);t,l,b,r=min(ys),min(xs),max(ys),max(xs)
            if any(any(t<=y<=b and l<=x<=r for y,x in comps[i]) for i in range(n) if not mask>>i&1):continue
            holes={(y,x) for y in range(t,b+1) for x in range(l,r+1) if g[y][x]==BG}
            valid=True
            while holes:
                stack=[holes.pop()];group=set(stack)
                while stack:
                    y,x=stack.pop()
                    for q in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                        if q in holes:holes.remove(q);group.add(q);stack.append(q)
                if len(group)>2:valid=False;break
            if valid:candidates.append((mask,(colour,t,l,b,r)))
        choices=[]
        def visit(used,rects):
            if used==(1<<n)-1:choices.append(rects);return
            first=next(i for i in range(n) if not used>>i&1)
            for mask,rect in candidates:
                if used&mask or not mask>>first&1:continue
                if any(rect[1]<=q[3]+1 and q[1]<=rect[3]+1 and rect[2]<=q[4]+1 and q[2]<=rect[4]+1 for q in rects):continue
                visit(used|mask,rects+[rect])
        visit(0,[])
        if not choices:raise ValueError('No coherent rectangle decomposition')
        colour_options.append(choices)
    readings=[[]]
    for options in colour_options:
        readings=[a+b for a in readings for b in options]
        if len(readings)>512:raise ValueError('Too many rectangle readings')
    return readings


def _overlap(a, b):
    ya, yb = max(a[1], b[1]), min(a[3], b[3])
    xa, xb = max(a[2], b[2]), min(a[4], b[4])
    if ya > yb or xa > xb:
        return None
    return ya, xa, yb, xb


def _render(grid, rects):
    g = [list(r) for r in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    counts = {}
    cols = []
    for row in g:
        for v in row:
            if v != BG:
                if v not in counts:
                    counts[v] = 0
                    cols.append(v)
                counts[v] += 1

    def share(i):
        r = rects[i]
        tot = 0
        own = 0
        for j, s in enumerate(rects):
            if j == i:
                continue
            ov = _overlap(r, s)
            if ov is None:
                continue
            ya, xa, yb, xb = ov
            for y in range(ya, yb + 1):
                for x in range(xa, xb + 1):
                    tot += 1
                    if g[y][x] == r[0]:
                        own += 1
        return own / tot if tot else 0.0

    shares = [share(i) for i in range(len(rects))]
    for i in range(len(rects)):
        for j in range(i):
            if _overlap(rects[i],rects[j]) is not None and shares[i]==shares[j]:
                raise ValueError('Unresolved overlap order')
    order = sorted(range(len(rects)), key=lambda i: shares[i])
    out = [[BG] * W for _ in range(H)]
    owner = [[-1] * W for _ in range(H)]
    for i in order:
        c, y0, x0, y1, x1 = rects[i]
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                out[y][x] = c
                owner[y][x] = i

    def frame_colour(c):
        others=[k for k in cols if k!=c]
        if len(others)!=1:raise ValueError('Expected exactly two rectangle colours')
        return others[0]

    holes = [(y, x) for y in range(H) for x in range(W)
             if owner[y][x] >= 0 and g[y][x] == BG]
    for y, x in holes:
        oc = frame_colour(rects[owner[y][x]][0])
        for yy in range(max(0, y - 1), min(H, y + 2)):
            for xx in range(max(0, x - 1), min(W, x + 2)):
                out[yy][xx] = oc
    for y, x in holes:
        out[y][x] = MARK
    return out

def solve(demonstrations, grid):
    g=[list(row) for row in grid]
    if not g or not g[0] or any(len(row)!=len(g[0]) for row in g):raise ValueError('Invalid grid')
    h,w=len(g),len(g[0]);cols={c for row in g for c in row if c!=BG}
    if len(cols)!=2:raise ValueError('Expected two rectangle colours')
    answers=set()
    for rects in _rectangle_readings(g,cols,h,w):
        try:out=_render(g,rects)
        except ValueError:continue
        answers.add(tuple(map(tuple,out)))
    if len(answers)!=1:raise ValueError('Rectangle reconstruction is ambiguous')
    return list(map(list,next(iter(answers))))

'''


def build_program(d4, palette):
    # The mechanism is isotropic: 2x2 cores, 4-connectivity, bounding boxes,
    # overlap shares and 3x3 frames are all D4-invariant. So d4 needs no
    # specialisation. Only the background and mark colour roles are fixed.
    bg = int(palette[0])
    mark = int(palette[8])
    return PROGRAM_TEMPLATE.replace('__BG__', str(bg)).replace('__MARK__', str(mark))
