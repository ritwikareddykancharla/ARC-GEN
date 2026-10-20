def build_program(d4, palette):
    bg = int(palette[0])
    vertical = (int(d4) % 4) in (1, 3)
    src = '''import numpy as np

BG = __BG__
VERTICAL = __VERT__
MAXLEN = 6


def _split(seg, line_len):
    # Two corner legends on the same edge can touch when both have the maximal
    # length 6 and the edge has length 12; split such a merged full-edge run.
    n = len(seg)
    if n > MAXLEN and n == line_len and n % 2 == 0 and n // 2 <= MAXLEN:
        return [seg[:n // 2], seg[n // 2:]]
    return [seg]


def _find(strips, c):
    for s in strips:
        if c in s:
            return s, s.index(c)
    return None, None


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    strips = []
    in_strip = np.zeros((H, W), dtype=bool)
    if not VERTICAL:
        # legends are horizontal runs; stamps are translated along rows
        for y in range(H):
            x = 0
            while x < W:
                if g[y, x] != BG:
                    x0 = x
                    while x < W and g[y, x] != BG:
                        x += 1
                    if x - x0 >= 2:
                        in_strip[y, x0:x] = True
                        seg = [int(v) for v in g[y, x0:x]]
                        strips.extend(_split(seg, W))
                else:
                    x += 1
        for y in range(H):
            for x in range(W):
                if g[y, x] != BG and not in_strip[y, x]:
                    s, i = _find(strips, int(g[y, x]))
                    if s is None:
                        continue
                    start = x - i
                    for k, v in enumerate(s):
                        xx = start + k
                        if 0 <= xx < W:
                            out[y, xx] = v
    else:
        # legends are vertical runs; stamps are translated along columns
        for x in range(W):
            y = 0
            while y < H:
                if g[y, x] != BG:
                    y0 = y
                    while y < H and g[y, x] != BG:
                        y += 1
                    if y - y0 >= 2:
                        in_strip[y0:y, x] = True
                        seg = [int(v) for v in g[y0:y, x]]
                        strips.extend(_split(seg, H))
                else:
                    y += 1
        for x in range(W):
            for y in range(H):
                if g[y, x] != BG and not in_strip[y, x]:
                    s, i = _find(strips, int(g[y, x]))
                    if s is None:
                        continue
                    start = y - i
                    for k, v in enumerate(s):
                        yy = start + k
                        if 0 <= yy < H:
                            out[yy, x] = v
    return out.tolist()
'''
    return src.replace('__BG__', str(bg)).replace('__VERT__', 'True' if vertical else 'False')
