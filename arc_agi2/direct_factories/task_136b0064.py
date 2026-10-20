def build_program(d4, palette):
    pal = [int(palette[c]) for c in range(10)]

    def mapv(v):
        dy, dx = v
        if d4 >= 4:
            dx = -dx
        for _ in range(d4 % 4):
            dy, dx = dx, -dy
        return (dy, dx)

    D = mapv((1, 0))
    R = mapv((0, 1))
    vert = (D[1] == 0)
    moves = {pal[1]: (1, 3), pal[2]: (-1, 2), pal[3]: (-1, 4), pal[6]: (0, 2)}
    template = '''import numpy as np
from collections import deque, Counter

PAL4 = __PAL4__
PAL5 = __PAL5__
BG = __BG__
D = __D__
R = __R__
VERT = __VERT__
MOVES = __MOVES__


def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                out.append(cells)
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    if VERT:
        scores = [int((g[:, x] == PAL4).sum()) for x in range(W)]
        idx = int(np.argmax(scores))
        if R[1] > 0:
            canvas = g[:, idx + 1:].copy()
            panel = g[:, :idx]
        else:
            canvas = g[:, :idx].copy()
            panel = g[:, idx + 1:]
    else:
        scores = [int((g[y, :] == PAL4).sum()) for y in range(H)]
        idx = int(np.argmax(scores))
        if R[0] > 0:
            canvas = g[idx + 1:, :].copy()
            panel = g[:idx, :]
        else:
            canvas = g[:idx, :].copy()
            panel = g[idx + 1:, :]
    glyphs = []
    if panel.size:
        for cells in _components(panel != BG):
            col = Counter(int(panel[y, x]) for y, x in cells).most_common(1)[0][0]
            if col not in MOVES:
                continue
            kr = min(y * R[0] + x * R[1] for y, x in cells)
            kd = min(y * D[0] + x * D[1] for y, x in cells)
            glyphs.append((kr, kd, col))
    glyphs.sort()
    ch, cw = canvas.shape
    ys, xs = np.where(canvas == PAL5)
    if len(ys) == 0:
        return canvas.tolist()
    py, px = int(ys[0]), int(xs[0])
    for _, _, col in glyphs:
        s, L = MOVES[col]
        if s == 0:
            for k in range(1, L + 1):
                y, x = py + k * D[0], px + k * D[1]
                if 0 <= y < ch and 0 <= x < cw:
                    canvas[y, x] = col
            py += L * D[0]
            px += L * D[1]
        else:
            py += D[0]
            px += D[1]
            for k in range(L):
                y, x = py + k * s * R[0], px + k * s * R[1]
                if 0 <= y < ch and 0 <= x < cw:
                    canvas[y, x] = col
            py += (L - 1) * s * R[0]
            px += (L - 1) * s * R[1]
    return canvas.tolist()
'''
    code = template.replace('__PAL4__', repr(pal[4]))
    code = code.replace('__PAL5__', repr(pal[5]))
    code = code.replace('__BG__', repr(pal[0]))
    code = code.replace('__D__', repr(tuple(int(v) for v in D)))
    code = code.replace('__R__', repr(tuple(int(v) for v in R)))
    code = code.replace('__VERT__', repr(bool(vert)))
    code = code.replace('__MOVES__', repr(moves))
    return code
