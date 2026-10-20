TEMPLATE = '''from collections import Counter, deque

VY = __VY__
VX = __VX__


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    h = len(g)
    w = len(g[0])
    out = [row[:] for row in g]
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if g[y][x] != bg and not seen[y][x]:
                seen[y][x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] != bg:
                            seen[ny][nx] = True
                            q.append((ny, nx))
                comps.append(cells)
    boxes = [c for c in comps if len(c) > 1]
    markers = [c[0] for c in comps if len(c) == 1]
    if not boxes or not markers:
        return out
    cnt = Counter(g[y][x] for c in boxes for (y, x) in c)
    frame = cnt.most_common(1)[0][0]
    B = []
    for c in boxes:
        ys = [p[0] for p in c]
        xs = [p[1] for p in c]
        core = [p for p in c if g[p[0]][p[1]] != frame]
        if not core:
            continue
        cys = [p[0] for p in core]
        cxs = [p[1] for p in core]
        B.append(((min(ys), min(xs), max(ys), max(xs)),
                  (min(cys), min(cxs), max(cys), max(cxs)),
                  g[core[0][0]][core[0][1]]))
    n = len(B)
    # legend reading order: projection on the visible legend direction
    markers.sort(key=lambda p: (p[0] * VY + p[1] * VX, p[0], p[1]))
    seq = [g[y][x] for (y, x) in markers]

    def relation(a, b):
        ay0, ax0, ay1, ax1 = B[a][0]
        by0, bx0, by1, bx1 = B[b][0]
        if ay0 <= by1 and by0 <= ay1:
            if bx0 > ax1:
                lo, hi = ax1 + 1, bx0 - 1
            elif ax0 > bx1:
                lo, hi = bx1 + 1, ax0 - 1
            else:
                return None
            for k in range(n):
                if k == a or k == b:
                    continue
                ky0, kx0, ky1, kx1 = B[k][0]
                if ky0 <= ay1 and ay0 <= ky1 and kx0 <= hi and lo <= kx1:
                    return None
            return ('h', lo, hi)
        if ax0 <= bx1 and bx0 <= ax1:
            if by0 > ay1:
                lo, hi = ay1 + 1, by0 - 1
            elif ay0 > by1:
                lo, hi = by1 + 1, ay0 - 1
            else:
                return None
            for k in range(n):
                if k == a or k == b:
                    continue
                ky0, kx0, ky1, kx1 = B[k][0]
                if kx0 <= ax1 and ax0 <= kx1 and ky0 <= hi and lo <= ky1:
                    return None
            return ('v', lo, hi)
        return None

    def dist(a, b):
        return abs(B[a][0][0] - B[b][0][0]) + abs(B[a][0][1] - B[b][0][1])

    def dfs(path, i):
        if i == len(seq):
            return path
        cur = path[-1]
        cands = [k for k in range(n) if B[k][2] == seq[i] and k not in path and relation(cur, k)]
        cands.sort(key=lambda k: dist(cur, k))
        for k in cands:
            r = dfs(path + [k], i + 1)
            if r:
                return r
        return None

    path = None
    for s in range(n):
        if B[s][2] == seq[0]:
            path = dfs([s], 1)
            if path:
                break
    if path:
        for a, b in zip(path, path[1:]):
            kind, lo, hi = relation(a, b)
            cy0, cx0, cy1, cx1 = B[a][1]
            col = B[a][2]
            if kind == 'h':
                for y in range(cy0, cy1 + 1):
                    for x in range(lo, hi + 1):
                        out[y][x] = col
            else:
                for y in range(lo, hi + 1):
                    for x in range(cx0, cx1 + 1):
                        out[y][x] = col
    return out
'''


def build_program(d4, palette):
    # Original legend reads along +x (left to right) on a row near the bottom.
    vy, vx = 0, 1
    if d4 >= 4:
        vy, vx = 0, -1
    for _ in range(d4 % 4):
        # clockwise rotation maps direction (dy, dx) -> (dx, -dy)
        vy, vx = vx, -vy
    return TEMPLATE.replace('__VY__', str(vy)).replace('__VX__', str(vx))
