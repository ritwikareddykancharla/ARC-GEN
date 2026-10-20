def build_program(d4, palette):
    bg = int(palette[7])
    div = int(palette[6])
    mark = int(palette[2])
    c5 = int(palette[5])
    c8 = int(palette[8])
    s8 = 1 if (d4 % 8) < 4 else -1
    src = '''import numpy as np

BG = __BG__
DIV = __DIV__
MARK = __MARK__
C5 = __C5__
C8 = __C8__
S8 = __S8__

# Visible clockwise ring around the centre panel (screen coordinates).
RING = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]


def _spans(cuts, n):
    edges = [-1] + sorted(cuts) + [n]
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        if b - a > 1:
            out.append((a + 1, b - 1))
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    # Already-solved board: return a 16x16 plain background canvas.
    if np.any(g == C5) or np.any(g == C8):
        return [[BG] * 16 for _ in range(16)]
    rows = [y for y in range(H) if np.all(g[y, :] == DIV)]
    cols = [x for x in range(W) if np.all(g[:, x] == DIV)]
    ys = _spans(rows, H)
    xs = _spans(cols, W)
    out = g.copy()
    if len(ys) != 3 or len(xs) != 3:
        return out.tolist()
    pos = {}
    for i in range(3):
        for j in range(3):
            pos[(i - 1, j - 1)] = (ys[i][0], xs[j][0], ys[i][1], xs[j][1])

    def content(b):
        return g[b[0]:b[2] + 1, b[1]:b[3] + 1]

    centre = pos[(0, 0)]
    motif = content(centre)
    mask = (motif != BG) & (motif != DIV)
    d = None
    for k in RING:
        if np.any(content(pos[k]) == MARK):
            d = k
            break
    if d is None:
        return out.tolist()
    opp = (-d[0], -d[1])
    idx = RING.index(opp)
    for colour, step in ((C8, S8), (C5, -S8)):
        tgt = RING[(idx + step) % 8]
        b = pos[tgt]
        h = min(b[2] - b[0] + 1, mask.shape[0])
        w = min(b[3] - b[1] + 1, mask.shape[1])
        patch = np.where(mask[:h, :w], colour, BG)
        out[b[0]:b[0] + h, b[1]:b[1] + w] = patch
    return out.tolist()
'''
    src = (src.replace('__BG__', str(bg))
              .replace('__DIV__', str(div))
              .replace('__MARK__', str(mark))
              .replace('__C5__', str(c5))
              .replace('__C8__', str(c8))
              .replace('__S8__', str(s8)))
    return src
