def build_program(d4, palette):
    bg = int(palette[0])
    st = int(palette[8])
    template = '''BG = __BG__
ST = __ST__
DIRS = ((0, 1), (0, -1), (1, 0), (-1, 0))


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    comp_id = {}
    comps = []
    for y in range(H):
        for x in range(W):
            if g[y][x] != ST or (y, x) in comp_id:
                continue
            idx = len(comps)
            comp_id[(y, x)] = idx
            stack = [(y, x)]
            members = [(y, x)]
            while stack:
                cy, cx = stack.pop()
                for a in (-1, 0, 1):
                    for b in (-1, 0, 1):
                        ny, nx = cy + a, cx + b
                        if 0 <= ny < H and 0 <= nx < W and g[ny][nx] == ST and (ny, nx) not in comp_id:
                            comp_id[(ny, nx)] = idx
                            stack.append((ny, nx))
                            members.append((ny, nx))
            comps.append(sorted(members))
    legends = []
    for y in range(H):
        for x in range(W):
            s = g[y][x]
            if s == BG or s == ST:
                continue
            for dy, dx in DIRS:
                ty, tx = y + dy, x + dx
                if not (0 <= ty < H and 0 <= tx < W):
                    continue
                t = g[ty][tx]
                if t == BG or t == ST or t == s:
                    continue
                ay, ax = ty + dy, tx + dx
                if not (0 <= ay < H and 0 <= ax < W):
                    continue
                ids = set()
                for ny in range(ay - 1, ay + 2):
                    for nx in range(ax - 1, ax + 2):
                        if (ny, nx) in comp_id:
                            ids.add(comp_id[(ny, nx)])
                if not ids:
                    continue
                cells = [p for i in sorted(ids) for p in comps[i]]
                offs = [(p[0] - ay, p[1] - ax) for p in cells]
                legends.append((s, t, offs, [(y, x), (ty, tx)] + cells))
    legend_cells = set()
    for leg in legends:
        legend_cells.update(leg[3])
    mapping = {}
    for s, t, offs, _ in legends:
        mapping[s] = (t, offs)
    out = [row[:] for row in g]
    for (y, x) in legend_cells:
        out[y][x] = BG
    for y in range(H):
        for x in range(W):
            if g[y][x] in mapping:
                out[y][x] = BG
    for s, (t, offs) in mapping.items():
        for y in range(H):
            for x in range(W):
                if g[y][x] == s and (y, x) not in legend_cells:
                    for oy, ox in offs:
                        ny, nx = y + oy, x + ox
                        if 0 <= ny < H and 0 <= nx < W:
                            out[ny][nx] = t
    return out
'''
    return template.replace('__BG__', str(bg)).replace('__ST__', str(st))
