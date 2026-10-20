def build_program(d4, palette):
    # Original mechanism: the tally dots start two cells inside the frame's RIGHT edge
    # (direction (0,+1)) on the frame's middle row and step two cells back toward the left.
    # Map that start direction through the episode's D4: optional horizontal flip first,
    # then clockwise quarter turns, where (dr, dc) -> (dc, -dr).
    dr, dc = 0, 1
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    # palette is not needed: background, frame and shape colours are all read from the pixels.
    return TEMPLATE.replace('__DR__', str(dr)).replace('__DC__', str(dc))


TEMPLATE = '''from collections import Counter

DR = __DR__
DC = __DC__


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    seen = [[False] * W for _ in range(H)]
    comps = []
    for y in range(H):
        for x in range(W):
            if g[y][x] != bg and not seen[y][x]:
                c = g[y][x]
                stack = [(y, x)]
                seen[y][x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == c:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                comps.append((c, cells))
    frames = []
    smalls = []
    for c, cells in comps:
        y0 = min(p[0] for p in cells)
        y1 = max(p[0] for p in cells)
        x0 = min(p[1] for p in cells)
        x1 = max(p[1] for p in cells)
        ok = (y1 - y0 + 1) >= 3 and (x1 - x0 + 1) >= 3
        if ok:
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    edge = yy == y0 or yy == y1 or xx == x0 or xx == x1
                    v = g[yy][xx]
                    if (edge and v != c) or ((not edge) and v != bg):
                        ok = False
                        break
                if not ok:
                    break
        if ok:
            frames.append((c, (y0, x0, y1, x1)))
        else:
            smalls.append((c, cells))
    out = [row[:] for row in g]
    for c, cells in smalls:
        for y, x in cells:
            out[y][x] = bg
    tally = Counter(c for c, _ in smalls)
    for c, (y0, x0, y1, x1) in frames:
        n = tally.get(c, 0)
        my = (y0 + y1) // 2
        mx = (x0 + x1) // 2
        for i in range(n):
            if DR == 0:
                r = my
                cc = (x1 - 2 - 2 * i) if DC > 0 else (x0 + 2 + 2 * i)
                if not (x0 < cc < x1):
                    break
            else:
                cc = mx
                r = (y1 - 2 - 2 * i) if DR > 0 else (y0 + 2 + 2 * i)
                if not (y0 < r < y1):
                    break
            out[r][cc] = c
    return out
'''
