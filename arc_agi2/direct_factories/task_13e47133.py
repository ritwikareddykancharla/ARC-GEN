_BODY = '''
from collections import deque, Counter

_D8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a, b) != (0, 0)]
_D4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _roles(g, H, W):
    cnt = Counter(v for row in g for v in row)
    bg = cnt.most_common(1)[0][0]
    seen = [[False] * W for _ in range(H)]
    best, div = -1, None
    for y in range(H):
        for x in range(W):
            if g[y][x] == bg or seen[y][x]:
                continue
            col = g[y][x]
            seen[y][x] = True
            dq = deque([(y, x)])
            n = 0
            while dq:
                cy, cx = dq.popleft()
                n += 1
                for dy, dx in _D4:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True
                        dq.append((ny, nx))
            if n > best:
                best, div = n, col
    return bg, div


def _regions(g, H, W, div):
    lab = [[-1] * W for _ in range(H)]
    regs = []
    for y in range(H):
        for x in range(W):
            if g[y][x] == div or lab[y][x] >= 0:
                continue
            idx = len(regs)
            lab[y][x] = idx
            cells = []
            dq = deque([(y, x)])
            while dq:
                cy, cx = dq.popleft()
                cells.append((cy, cx))
                for dy, dx in _D4:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and g[ny][nx] != div and lab[ny][nx] < 0:
                        lab[ny][nx] = idx
                        dq.append((ny, nx))
            regs.append(cells)
    return regs


def _chain(g, cells, cs, bg):
    # Corner-anchored diagonal readings. Primary key: number of coloured
    # cells (as in the constructor). Tie-break (orientation-free): fewest
    # leading background cells, then shortest reading, i.e. the reading
    # that starts closest to its corner (the generator places chains
    # flush to a corner with at most one leading background cell).
    best = None
    for (sy, sx) in sorted(cells):
        if g[sy][sx] == bg:
            continue
        for dy in (-1, 1):
            for dx in (-1, 1):
                y, x = sy, sx
                while (y + dy, x + dx) in cs:
                    y += dy
                    x += dx
                if (y + dy, x) in cs or (y, x + dx) in cs:
                    continue
                seq = []
                y2, x2 = y, x
                while (y2, x2) in cs:
                    seq.append(g[y2][x2])
                    y2 -= dy
                    x2 -= dx
                idx = [i for i, v in enumerate(seq) if v != bg]
                if not idx:
                    continue
                seq = seq[:idx[-1] + 1]
                key = (len(idx), -idx[0], -len(seq))
                if best is None or key > best[0]:
                    best = (key, seq)
    return None if best is None else best[1]


def _rings(cells, cs):
    dist = {}
    dq = deque()
    for (y, x) in cells:
        if any((y + a, x + b) not in cs for a, b in _D8):
            dist[(y, x)] = 1
            dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for a, b in _D8:
            nb = (y + a, x + b)
            if nb in cs and nb not in dist:
                dist[nb] = dist[(y, x)] + 1
                dq.append(nb)
    return dist


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H, W = len(g), len(g[0])
    out = [row[:] for row in g]
    bg, div = _roles(g, H, W)
    if div is None:
        return out
    for cells in _regions(g, H, W, div):
        cs = set(cells)
        seq = _chain(g, cells, cs, bg)
        if not seq:
            continue
        dist = _rings(cells, cs)
        L = len(seq)
        for (y, x) in cells:
            out[y][x] = seq[(dist.get((y, x), 1) - 1) % L]
    return out
'''


def build_program(d4, palette):
    header = ('# Direct-coordinate concentric ring fill (task 13e47133).\n'
              '# Episode transform: d4=%d, palette=%s.\n'
              '# Corner chains are searched on all four diagonals with an\n'
              '# orientation-free tie-break; rings use Chebyshev distance.\n'
              '# Background and divider roles are inferred from visible pixels.\n'
              % (int(d4), repr([int(c) for c in palette])))
    return header + _BODY
