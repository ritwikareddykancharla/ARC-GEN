def build_program(d4, palette):
    bg = int(palette[6])
    template = '''
BG = __BG__


def _components(g, colour):
    H = len(g)
    W = len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for y in range(H):
        for x in range(W):
            if g[y][x] == colour and not seen[y][x]:
                stack = [(y, x)]
                seen[y][x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == colour:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                comps.append(sorted(cells))
    return comps


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def solve(demonstrations, grid):
    g = [list(map(int, r)) for r in grid]
    H = len(g)
    W = len(g[0])
    counts = {}
    for r in g:
        for v in r:
            counts[v] = counts.get(v, 0) + 1
    bg = BG
    if counts.get(bg, 0) == 0:
        bg = max(sorted(counts), key=lambda k: counts[k])
    colours = sorted(c for c in counts if c != bg)
    out = [row[:] for row in g]
    placements = []
    for c in colours:
        comps = _components(g, c)
        if not comps:
            continue
        def score(cells):
            ys = [p[0] for p in cells]
            xs = [p[1] for p in cells]
            area = (max(ys) - min(ys) + 1) * (max(xs) - min(xs) + 1)
            return (len(cells), 1 if area == len(cells) else 0)
        block = max(comps, key=score)
        ys = [p[0] for p in block]
        xs = [p[1] for p in block]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        for comp in comps:
            if comp is block:
                continue
            for (y, x) in comp:
                out[y][x] = bg
                oy = (y0 - y) if y < y0 else (y - y1) if y > y1 else 0
                ox = (x0 - x) if x < x0 else (x - x1) if x > x1 else 0
                ty = y0 - 1 if y < y0 else y1 + 1
                tx = x0 - 1 if x < x0 else x1 + 1
                if oy > ox:
                    # attach to the block face lying in the row direction
                    tx = _clamp(x, x0, x1)
                elif ox > oy:
                    # attach to the block face lying in the column direction
                    ty = _clamp(y, y0, y1)
                # equal nonzero offsets (outside the generator domain): diagonal corner cell
                if oy == 0 and ox == 0:
                    ty, tx = y, x
                placements.append((ty, tx, c))
    for ty, tx, c in placements:
        if 0 <= ty < H and 0 <= tx < W:
            out[ty][tx] = c
    return out
'''
    return template.replace('__BG__', str(bg))
