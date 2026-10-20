def build_program(d4, palette):
    line_out = int(palette[5])
    node_out = int(palette[3])
    src = '''from collections import deque, Counter

LINE_OUT = %d
NODE_OUT = %d
EIGHT = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
FOUR = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def _components(g, color, diagonal):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    steps = EIGHT if diagonal else FOUR
    out = []
    for y in range(H):
        for x in range(W):
            if seen[y][x] or g[y][x] != color:
                continue
            seen[y][x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in steps:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == color:
                        seen[ny][nx] = True
                        q.append((ny, nx))
            out.append(sorted(cells))
    return out

def _is_square(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    h = max(ys) - min(ys) + 1
    w = max(xs) - min(xs) + 1
    return h == w and len(cells) == h * w

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H, W = len(g), len(g[0])
    cnt = Counter(v for row in g for v in row)
    bg = cnt.most_common(1)[0][0]
    cols = sorted(c for c in cnt if c != bg)
    comps4 = {c: _components(g, c, False) for c in cols}
    block_cols = [c for c in cols if all(_is_square(cc) for cc in comps4[c])]
    line_cols = [c for c in cols if c not in block_cols]
    if not line_cols or len(block_cols) < 2:
        return [row[:] for row in g]
    line_c = line_cols[0]
    # endpoint colour: exactly two blocks (fewest); node colour: the other one
    block_cols.sort(key=lambda c: (len(comps4[c]) != 2, len(comps4[c]), c))
    end_c = block_cols[0]
    node_c = [c for c in block_cols if c != end_c][0]
    pieces = []
    for cc in comps4[end_c]:
        pieces.append(('end', cc))
    for cc in comps4[node_c]:
        pieces.append(('node', cc))
    for cc in _components(g, line_c, True):
        pieces.append(('line', cc))
    lab = [[-1] * W for _ in range(H)]
    for i, (_, cc) in enumerate(pieces):
        for y, x in cc:
            lab[y][x] = i
    adj = [set() for _ in pieces]
    for i, (_, cc) in enumerate(pieces):
        for y, x in cc:
            for dy, dx in EIGHT:
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W:
                    j = lab[ny][nx]
                    if j >= 0 and j != i:
                        adj[i].add(j)
    ends = [i for i, p in enumerate(pieces) if p[0] == 'end']
    if len(ends) < 2:
        return [row[:] for row in g]
    start, goal = ends[0], ends[1]
    prev = {start: None}
    dq = deque([start])
    while dq:
        u = dq.popleft()
        if u == goal:
            break
        for v in sorted(adj[u]):
            if v in prev:
                continue
            if pieces[v][0] == 'end' and v != goal:
                continue
            prev[v] = u
            dq.append(v)
    out = [row[:] for row in g]
    if goal not in prev:
        return out
    u = goal
    while u is not None:
        kind, cells = pieces[u]
        if kind == 'line':
            for y, x in cells:
                out[y][x] = LINE_OUT
        elif kind == 'node':
            for y, x in cells:
                out[y][x] = NODE_OUT
        u = prev[u]
    return out
''' % (line_out, node_out)
    return src
