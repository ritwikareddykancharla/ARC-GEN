TEMPLATE = '''import numpy as np
from collections import deque

BG = @BG@
HEAD = @HEAD@
MARK = @MARK@
NB8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
NB4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def read_legends(g):
    H, W = g.shape
    dirs = {}
    for y in range(H):
        for x in range(W):
            if g[y, x] != HEAD:
                continue
            nb = []
            counts = {}
            for dy, dx in NB8:
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W:
                    c = int(g[ny, nx])
                    nb.append((c, dy, dx))
                    counts[c] = counts.get(c, 0) + 1
            if not counts:
                continue
            top = max(counts.values())
            frames = [c for c in counts if counts[c] == top]
            if len(frames) != 1:
                continue
            frame = frames[0]
            if frame in (BG, HEAD, MARK):
                continue
            tails = [(dy, dx) for c, dy, dx in nb if c not in (frame, HEAD, MARK, BG)]
            if len(tails) != 1:
                continue
            dy, dx = tails[0]
            if frame not in dirs:
                dirs[frame] = (-dy, -dx)
    return dirs


def label_background(lifted):
    H, W = lifted.shape
    lab = -np.ones((H, W), dtype=int)
    regions = []
    for y in range(H):
        for x in range(W):
            if lifted[y, x] != BG or lab[y, x] >= 0:
                continue
            rid = len(regions)
            lab[y, x] = rid
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in NB4:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and lifted[ny, nx] == BG and lab[ny, nx] < 0:
                        lab[ny, nx] = rid
                        q.append((ny, nx))
            regions.append(cells)
    return lab, regions


def wall_counts(lifted, cells):
    H, W = lifted.shape
    cnt = {}
    for y, x in cells:
        for dy, dx in NB4:
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and lifted[ny, nx] != BG:
                c = int(lifted[ny, nx])
                cnt[c] = cnt.get(c, 0) + 1
    return cnt


def slide(lifted, y, x, dy, dx):
    H, W = lifted.shape
    while 0 <= y + dy < H and 0 <= x + dx < W and lifted[y + dy, x + dx] == BG:
        if dy and dx and (lifted[y + dy, x] != BG or lifted[y, x + dx] != BG):
            break
        y += dy
        x += dx
    return y, x


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    dirs = read_legends(g)
    lifted = g.copy()
    marks = [(int(y), int(x)) for y, x in zip(*np.where(g == MARK))]
    for y, x in marks:
        lifted[y, x] = BG
    lab, regions = label_background(lifted)
    cache = {}
    targets = []
    for y, x in marks:
        rid = int(lab[y, x])
        if rid not in cache:
            cnt = wall_counts(lifted, regions[rid])
            cand = [(n, c) for c, n in cnt.items() if c in dirs]
            col = None
            if cand:
                top = max(n for n, c in cand)
                best = [c for n, c in cand if n == top]
                if len(best) == 1:
                    col = best[0]
            cache[rid] = col
        col = cache[rid]
        if col is None:
            targets.append((y, x))
        else:
            dy, dx = dirs[col]
            targets.append(slide(lifted, y, x, dy, dx))
    out = lifted.copy()
    for y, x in targets:
        out[y, x] = MARK
    return [[int(v) for v in row] for row in out.tolist()]
'''


def build_program(d4, palette):
    pal = [int(c) for c in palette]
    src = TEMPLATE.replace('@BG@', str(pal[0]))
    src = src.replace('@HEAD@', str(pal[2]))
    src = src.replace('@MARK@', str(pal[4]))
    return src
