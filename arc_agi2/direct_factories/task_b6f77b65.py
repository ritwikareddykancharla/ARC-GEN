TEMPLATE = """DOWN = (@GR@, @GC@)
SIDE = (@LR@, @LC@)
BG = @BG@


def _step(p, d, k=1):
    return (p[0] + d[0] * k, p[1] + d[1] * k)


def _runs(cells, d):
    cs = set(cells)
    out = []
    for p in sorted(cs):
        if _step(p, d, -1) not in cs:
            run = [p]
            n = _step(p, d)
            while n in cs:
                run.append(n)
                n = _step(n, d)
            out.append(run)
    return out


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    R = len(g)
    C = len(g[0]) if R else 0

    def inside(p):
        return 0 <= p[0] < R and 0 <= p[1] < C

    def lat(p):
        return p[0] * SIDE[0] + p[1] * SIDE[1]

    def depth(p):
        return p[0] * DOWN[0] + p[1] * DOWN[1]

    legend = [(r, c) for r in range(R) for c in range(C)
              if not inside(_step((r, c), DOWN, -1))]
    legset = set(legend)
    removed = set(g[r][c] for r, c in legend if g[r][c] != BG)
    scene = {}
    for r in range(R):
        for c in range(C):
            if (r, c) not in legset and g[r][c] != BG:
                scene[(r, c)] = g[r][c]
    if not any(v in removed for v in scene.values()):
        return [row[:] for row in g]

    seen = set()
    comps = []
    for p in sorted(scene):
        if p in seen:
            continue
        col = scene[p]
        stack = [p]
        seen.add(p)
        cells = set()
        while stack:
            q = stack.pop()
            cells.add(q)
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (q[0] + d[0], q[1] + d[1])
                if n not in seen and scene.get(n) == col:
                    seen.add(n)
                    stack.append(n)
        comps.append((col, cells))

    pieces = []
    for col, cells in comps:
        poles = []
        for run in _runs(cells, DOWN):
            if len(run) >= 2:
                poles.append({'c': col, 'v': set(run), 'h': set(), 'bar': False,
                              'bot': run[-1], 'key': (lat(run[0]), depth(run[0]))})
        poles.sort(key=lambda q: q['key'])
        used = set()
        for q in poles:
            used |= q['v']
        rest = cells - used
        for run in _runs(rest, SIDE):
            before = _step(run[0], SIDE, -1)
            after = _step(run[-1], SIDE)
            fits = [q for q in poles if q['bot'] == before or q['bot'] == after]
            if fits:
                fits[0]['h'] |= set(run)
            else:
                pieces.append({'c': col, 'v': set(), 'h': set(run),
                               'bar': not poles})
        pieces.extend(poles)

    for p in pieces:
        if p['v']:
            n = _step(p['bot'], DOWN)
            if any(n in q['h'] and q['c'] != p['c'] and q['bar'] for q in pieces):
                p['v'].add(n)

    pieces = [p for p in pieces if p['c'] not in removed]

    extent = R if DOWN[0] != 0 else C
    for _ in range(extent * (len(pieces) + 1) + 1):
        stable = set()
        while True:
            occ = set()
            for i in stable:
                occ |= pieces[i]['v'] | pieces[i]['h']
            added = set()
            for i, p in enumerate(pieces):
                if i in stable:
                    continue
                cells = p['v'] | p['h']
                ok = False
                for q in cells:
                    nq = _step(q, DOWN)
                    if (not inside(nq)) or nq in occ or q in occ:
                        ok = True
                        break
                if not ok:
                    for run in _runs(cells, SIDE):
                        if _step(run[0], SIDE, -1) in occ and _step(run[-1], SIDE) in occ:
                            ok = True
                            break
                if ok:
                    added.add(i)
            if not added:
                break
            stable |= added
        if len(stable) == len(pieces):
            break
        for i, p in enumerate(pieces):
            if i not in stable:
                p['v'] = set(_step(q, DOWN) for q in p['v'])
                p['h'] = set(_step(q, DOWN) for q in p['h'])

    out = [[BG] * C for _ in range(R)]
    for field in ('v', 'h'):
        for p in pieces:
            for q in p[field]:
                if inside(q):
                    out[q[0]][q[1]] = p['c']
    for r, c in legend:
        out[r][c] = g[r][c]
    return out
"""


def build_program(d4, palette):
    d4 = int(d4) % 8
    down = (1, 0)
    side = (0, -1) if d4 >= 4 else (0, 1)
    for _ in range(d4 % 4):
        down = (down[1], -down[0])
        side = (side[1], -side[0])
    bg = int(palette[0])
    src = TEMPLATE
    src = src.replace('@GR@', str(down[0])).replace('@GC@', str(down[1]))
    src = src.replace('@LR@', str(side[0])).replace('@LC@', str(side[1]))
    src = src.replace('@BG@', str(bg))
    return src
