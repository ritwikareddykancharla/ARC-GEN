def build_program(d4, palette):
    bg = int(palette[8])
    tail = int(palette[1])
    hub = int(palette[4])
    template = '''import numpy as np

BG = __BG__
TAIL = __TAIL__
HUB = __HUB__
STEPS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(g):
    H, W = g.shape
    seen = np.zeros((H, W), bool)
    comps = []
    for y in range(H):
        for x in range(W):
            if g[y, x] != BG and not seen[y, x]:
                stack = [(y, x)]
                seen[y, x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] != BG:
                                seen[ny, nx] = True
                                stack.append((ny, nx))
                comps.append(sorted(cells))
    return comps


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    moves = []
    for cells in _components(g):
        cs = set(cells)
        cands = [(y, x) for (y, x) in cells if all((y + a, x + b) in cs for a, b in STEPS4)]
        if not cands:
            continue
        hubs = [p for p in cands if g[p[0], p[1]] == HUB]
        cy, cx = (hubs or cands)[0]
        head = {(cy, cx)} | {(cy + a, cx + b) for a, b in STEPS4}
        tails = [p for p in cells if p not in head and g[p[0], p[1]] == TAIL]
        if not tails:
            tails = [p for p in cells if p not in head]
        if not tails:
            continue
        my = sum(p[0] for p in tails) / len(tails)
        mx = sum(p[1] for p in tails) / len(tails)
        ddy = cy - my
        ddx = cx - mx
        if abs(ddy) > abs(ddx):
            dy, dx = (1 if ddy > 0 else -1), 0
        elif abs(ddx) > abs(ddy):
            dy, dx = 0, (1 if ddx > 0 else -1)
        else:
            continue
        if dy > 0:
            s = H - 1 - (cy + 1)
        elif dy < 0:
            s = cy - 1
        elif dx > 0:
            s = W - 1 - (cx + 1)
        else:
            s = cx - 1
        moves.append((cells, cy, cx, head, dy * s, dx * s))
    for cells, cy, cx, head, oy, ox in moves:
        for y, x in cells:
            out[y, x] = BG
    for cells, cy, cx, head, oy, ox in moves:
        for y, x in cells:
            if (y, x) in head:
                ny, nx = 2 * cy - y + oy, 2 * cx - x + ox
            else:
                ny, nx = y + oy, x + ox
            if 0 <= ny < H and 0 <= nx < W:
                out[ny, nx] = g[y, x]
    return out.tolist()
'''
    return template.replace('__BG__', str(bg)).replace('__TAIL__', str(tail)).replace('__HUB__', str(hub))
