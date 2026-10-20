TEMPLATE = '''import numpy as np

BG = __BG__
SEALED = __C3__
OPEN = __C4__


def _periods(n):
    return [m for m in range(1, n) if (n + 1) % (m + 1) == 0]


def _fallback(g):
    H, W = g.shape
    out = g.copy()
    seen = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            if g[y, x] == BG and not seen[y, x]:
                stack = [(y, x)]
                seen[y, x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and g[ny, nx] == BG and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                ys = [c[0] for c in cells]
                xs = [c[1] for c in cells]
                area = (max(ys) - min(ys) + 1) * (max(xs) - min(xs) + 1)
                col = SEALED if len(cells) == area else OPEN
                for cy, cx in cells:
                    out[cy, cx] = col
    return out.tolist()


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    nb = g != BG
    best = None
    for mr in _periods(H):
        rl = np.array([(r % (mr + 1)) == mr for r in range(H)])
        for mc in _periods(W):
            cl = np.array([(c % (mc + 1)) == mc for c in range(W)])
            onl = rl[:, None] | cl[None, :]
            if np.any(nb & ~onl):
                continue
            if not all(nb[r, :].any() for r in range(H) if rl[r]):
                continue
            if not all(nb[:, c].any() for c in range(W) if cl[c]):
                continue
            key = (mr + mc, mr, mc)
            if best is None or key > best[0]:
                best = (key, mr, mc, rl, cl, onl)
    if best is None:
        return _fallback(g)
    _, mr, mc, rl, cl, onl = best
    pr, pc = mr + 1, mc + 1
    nR = (H + 1) // pr
    nC = (W + 1) // pc
    openroom = np.zeros((nR, nC), bool)
    out = g.copy()
    gaps = (~nb) & onl
    for r, c in zip(*np.nonzero(gaps)):
        out[r, c] = OPEN
        k = r // pr
        j = c // pc
        if rl[r] and not cl[c]:
            openroom[k, j] = True
            if k + 1 < nR:
                openroom[k + 1, j] = True
        elif cl[c] and not rl[r]:
            openroom[k, j] = True
            if j + 1 < nC:
                openroom[k, j + 1] = True
    rooms = (~nb) & (~onl)
    for r, c in zip(*np.nonzero(rooms)):
        out[r, c] = OPEN if openroom[r // pr, c // pc] else SEALED
    return [[int(v) for v in row] for row in out.tolist()]
'''


def build_program(d4, palette):
    pal = list(palette)
    src = TEMPLATE
    src = src.replace('__BG__', str(int(pal[0])))
    src = src.replace('__C3__', str(int(pal[3])))
    src = src.replace('__C4__', str(int(pal[4])))
    return src
