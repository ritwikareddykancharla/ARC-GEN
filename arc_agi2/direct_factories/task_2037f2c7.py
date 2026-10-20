def build_program(d4, palette):
    bg = int(palette[0])
    mark = int(palette[8])
    k = int(d4) % 4
    # Original 'rows' of the figure become visible rows when the rotation
    # count is even and visible columns when it is odd. Reflection keeps the axis.
    crop_rows = (k % 2 == 0)
    src = '''
BG = __BG__
MARK = __MARK__
CROP_ROWS = __CROP__


def _components(g, H, W):
    seen = [[False] * W for _ in range(H)]
    comps = []
    for y in range(H):
        for x in range(W):
            if g[y][x] != BG and not seen[y][x]:
                seen[y][x] = True
                stack = [(y, x)]
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] != BG:
                                seen[ny][nx] = True
                                stack.append((ny, nx))
                comps.append(sorted(cells))
    return comps


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0])
    comps = _components(g, H, W)
    if not comps:
        return [[BG]]
    best_size = max(len(c) for c in comps)
    tmpl = [c for c in comps if len(c) == best_size][0]
    tset = set(tmpl)
    ty0 = min(y for y, _ in tmpl); ty1 = max(y for y, _ in tmpl)
    tx0 = min(x for _, x in tmpl); tx1 = max(x for _, x in tmpl)
    th = ty1 - ty0 + 1
    tw = tx1 - tx0 + 1
    T = [[BG] * tw for _ in range(th)]
    for y, x in tmpl:
        T[y - ty0][x - tx0] = g[y][x]
    dam = [(y, x) for y in range(H) for x in range(W)
           if g[y][x] != BG and (y, x) not in tset]
    D = [[BG] * tw for _ in range(th)]
    if dam:
        dy0 = min(y for y, _ in dam); dy1 = max(y for y, _ in dam)
        dx0 = min(x for _, x in dam); dx1 = max(x for _, x in dam)
        best = None
        for oy in range(dy1 - th + 1, dy0 + 1):
            for ox in range(dx1 - tw + 1, dx0 + 1):
                ok = True
                for y, x in dam:
                    ry, rx = y - oy, x - ox
                    if not (0 <= ry < th and 0 <= rx < tw) or T[ry][rx] != g[y][x]:
                        ok = False
                        break
                if ok:
                    best = (oy, ox)
        if best is not None:
            oy, ox = best
            for y, x in dam:
                D[y - oy][x - ox] = g[y][x]
    miss = [[T[r][c] != BG and D[r][c] == BG for c in range(tw)] for r in range(th)]
    full = [[MARK if miss[r][c] else BG for c in range(tw)] for r in range(th)]
    if CROP_ROWS:
        rows = [r for r in range(th) if any(miss[r])]
        if not rows:
            return full
        return [list(full[r]) for r in range(min(rows), max(rows) + 1)]
    else:
        cols = [c for c in range(tw) if any(miss[r][c] for r in range(th))]
        if not cols:
            return full
        c0, c1 = min(cols), max(cols)
        return [full[r][c0:c1 + 1] for r in range(th)]
'''
    src = src.replace('__BG__', repr(bg)).replace('__MARK__', repr(mark)).replace('__CROP__', repr(crop_rows))
    return src
