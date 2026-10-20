def build_program(d4, palette):
    k = int(d4) % 4
    # Original bands are horizontal (stacked along rows). Horizontal flip keeps rows as rows;
    # each clockwise quarter turn swaps the row/column axes.
    axis = 'rows' if k % 2 == 0 else 'cols'
    bg = int(palette[0])
    src = '''import numpy as np

BG = __BG__
BAND_AXIS = '__AXIS__'


def _line_colour(vals):
    cols = [int(v) for v in vals if int(v) != BG]
    if not cols:
        return None
    counts = {}
    for c in cols:
        counts[c] = counts.get(c, 0) + 1
    best = max(counts.values())
    return min(c for c in counts if counts[c] == best)


def _group(lines_with_colour):
    bands = []
    for idx, c in lines_with_colour:
        if bands and bands[-1][0] == c and bands[-1][2] == idx - 1:
            bands[-1][2] = idx
        else:
            bands.append([c, idx, idx])
    return bands


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    if BAND_AXIS == 'rows':
        # Bands are horizontal strips stacked vertically; reverse their vertical order.
        lines = []
        for y in range(H):
            c = _line_colour(g[y, :])
            if c is not None:
                lines.append((y, c))
        if not lines:
            return out.tolist()
        bands = _group(lines)
        top, bot = lines[0][0], lines[-1][0]
        out[top:bot + 1, :] = BG
        y = top
        for c, y0, y1 in reversed(bands):
            h = y1 - y0 + 1
            out[y:y + h, :] = g[y0:y1 + 1, :]
            y += h
    else:
        # Bands are vertical strips stacked horizontally; reverse their horizontal order.
        lines = []
        for x in range(W):
            c = _line_colour(g[:, x])
            if c is not None:
                lines.append((x, c))
        if not lines:
            return out.tolist()
        bands = _group(lines)
        left, right = lines[0][0], lines[-1][0]
        out[:, left:right + 1] = BG
        x = left
        for c, x0, x1 in reversed(bands):
            w = x1 - x0 + 1
            out[:, x:x + w] = g[:, x0:x1 + 1]
            x += w
    return out.tolist()
'''
    return src.replace('__BG__', str(bg)).replace('__AXIS__', axis)
