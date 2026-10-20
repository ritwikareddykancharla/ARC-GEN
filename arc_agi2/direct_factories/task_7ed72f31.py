def build_program(d4, palette):
    red = int(palette[2])
    template = '''from collections import Counter, deque

RED = __RED__


def _components(H, W, mask, diagonal):
    if diagonal:
        steps = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    else:
        steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    seen = [[False] * W for _ in range(H)]
    comps = []
    for y in range(H):
        for x in range(W):
            if mask[y][x] and not seen[y][x]:
                seen[y][x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in steps:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            q.append((ny, nx))
                comps.append(sorted(cells))
    return comps


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    if H == 0 or W == 0:
        return g
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    out = [row[:] for row in g]
    red_mask = [[g[y][x] == RED for x in range(W)] for y in range(H)]
    shape_mask = [[(g[y][x] != RED and g[y][x] != bg) for x in range(W)] for y in range(H)]
    mirrors = _components(H, W, red_mask, False)
    shapes = _components(H, W, shape_mask, True)
    for m in mirrors:
        mset = set(m)
        ys = set(c[0] for c in m)
        xs = set(c[1] for c in m)
        if len(m) == 1:
            kind = 'p'
            py, px = m[0]
        elif len(xs) == 1:
            kind = 'v'
            col = next(iter(xs))
        elif len(ys) == 1:
            kind = 'h'
            row = next(iter(ys))
        else:
            continue
        for s in shapes:
            touch = False
            for (y, x) in s:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if (y + dy, x + dx) in mset:
                            touch = True
                            break
                    if touch:
                        break
                if touch:
                    break
            if not touch:
                continue
            for (y, x) in s:
                if kind == 'p':
                    ny, nx = 2 * py - y, 2 * px - x
                elif kind == 'v':
                    ny, nx = y, 2 * col - x
                else:
                    ny, nx = 2 * row - y, x
                if 0 <= ny < H and 0 <= nx < W and out[ny][nx] == bg:
                    out[ny][nx] = g[y][x]
    return out
'''
    return template.replace('__RED__', str(red))
