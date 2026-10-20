def build_program(d4, palette):
    bg = int(palette[0])
    yel = int(palette[4])
    header = 'import numpy as np\n\nBG = %d\nYEL = %d\n' % (bg, yel)
    body = '''

def _hypotheses(inner, rel, th, tw, kmin, margin):
    H, W = inner.shape
    nz = inner != BG
    res = []
    for k in range(kmin, max(H, W) + 1):
        if k * th > H - 2 * margin or k * tw > W - 2 * margin:
            continue
        for oy in range(margin, H - margin - k * th + 1):
            for ox in range(margin, W - margin - k * tw + 1):
                covered = np.zeros(inner.shape, dtype=bool)
                shown = 0
                ok = True
                for (ry, rx), col in rel.items():
                    y = oy + k * ry
                    x = ox + k * rx
                    blk = inner[y:y + k, x:x + k]
                    if bool((blk == col).all()):
                        shown += 1
                        covered[y:y + k, x:x + k] = True
                    elif not bool((blk == BG).all()):
                        ok = False
                        break
                if not ok or shown == 0:
                    continue
                if bool((nz & ~covered).any()):
                    continue
                res.append((k, oy, ox, shown))
    return res


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    ys, xs = np.where(g == YEL)
    if len(ys) == 0:
        return g.tolist()
    y0, x0, y1, x1 = int(ys.min()), int(xs.min()), int(ys.max()), int(xs.max())
    crop = g[y0:y1 + 1, x0:x1 + 1].copy()
    H, W = crop.shape
    tmpl = {}
    for y in range(g.shape[0]):
        for x in range(g.shape[1]):
            v = int(g[y, x])
            if v != BG and v != YEL and not (y0 <= y <= y1 and x0 <= x <= x1):
                tmpl[(y, x)] = v
    if not tmpl:
        return crop.tolist()
    ty0 = min(p[0] for p in tmpl)
    tx0 = min(p[1] for p in tmpl)
    rel = {(y - ty0, x - tx0): c for (y, x), c in tmpl.items()}
    th = max(p[0] for p in rel) + 1
    tw = max(p[1] for p in rel) + 1
    inner = crop.copy()
    for (r, c) in [(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]:
        if inner[r, c] == YEL:
            inner[r, c] = BG
    hyps = _hypotheses(inner, rel, th, tw, 2, 0)
    answers = set()
    for k, oy, ox, shown in hyps:
        out = crop.copy()
        for (ry, rx), col in rel.items():
            out[oy+k*ry:oy+k*(ry+1), ox+k*rx:ox+k*(rx+1)] = col
        if any(out[y,x] != YEL for y,x in [(0,0),(0,W-1),(H-1,0),(H-1,W-1)]):
            continue
        answers.add(tuple(tuple(int(v) for v in row) for row in out))
    if len(answers) != 1:
        raise ValueError("Magnified placement does not determine one output")
    return [list(row) for row in next(iter(answers))]
'''
    return header + body
