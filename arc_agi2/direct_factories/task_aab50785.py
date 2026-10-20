def build_program(d4, palette):
    # Original mechanism: in each row band, two 2x2 squares of colour 8 sit side by side.
    # The 2-row strip between them is cut out, and the strips are stacked top to bottom.
    # Under D4, the original row axis maps to visible axis (d4 % 4) % 2.
    # Input and output share the same direction mapping, so strips are always
    # ordered by ascending visible coordinate along that axis. Strip contents are
    # copied verbatim as visible sub-blocks.
    axis = (d4 % 4) % 2
    sq = int(palette[8])
    bg = int(palette[0])
    template = '''import numpy as np

SQ = __SQ__
BG = __BG__
AXIS = __AXIS__


def _squares(g):
    H, W = g.shape
    mask = g == SQ
    seen = np.zeros((H, W), dtype=bool)
    found = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                stack = [(y, x)]
                seen[y, x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                if len(cells) == 4:
                    ys = [c[0] for c in cells]
                    xs = [c[1] for c in cells]
                    if max(ys) - min(ys) == 1 and max(xs) - min(xs) == 1:
                        found.append((min(ys), min(xs)))
    return found


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    squares = _squares(g)
    groups = {}
    for y, x in squares:
        if AXIS == 0:
            key, other = y, x
        else:
            key, other = x, y
        groups.setdefault(key, []).append(other)
    strips = []
    for key in sorted(groups):
        others = sorted(groups[key])
        for i in range(0, len(others) - 1, 2):
            a, b = others[i], others[i + 1]
            if AXIS == 0:
                s = g[key:key + 2, a + 2:b]
            else:
                s = g[a + 2:b, key:key + 2]
            if s.size:
                strips.append(s)
    if not strips:
        return g.tolist()
    if AXIS == 0:
        w = max(s.shape[1] for s in strips)
        h = sum(s.shape[0] for s in strips)
        out = np.full((h, w), BG, dtype=int)
        r = 0
        for s in strips:
            out[r:r + s.shape[0], :s.shape[1]] = s
            r += s.shape[0]
    else:
        h = max(s.shape[0] for s in strips)
        w = sum(s.shape[1] for s in strips)
        out = np.full((h, w), BG, dtype=int)
        c = 0
        for s in strips:
            out[:s.shape[0], c:c + s.shape[1]] = s
            c += s.shape[1]
    return out.tolist()
'''
    return (template.replace('__SQ__', str(sq))
                    .replace('__BG__', str(bg))
                    .replace('__AXIS__', str(axis)))
