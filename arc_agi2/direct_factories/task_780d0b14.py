def build_program(d4, palette):
    bg = int(palette[0])
    src = '''
import numpy as np

BG = __BG__

def _runs(flags):
    out = []
    start = None
    for i, f in enumerate(list(flags) + [True]):
        if not f and start is None:
            start = i
        elif f and start is not None:
            out.append((start, i - 1))
            start = None
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    # Divider lines: complete rows / complete columns of the background colour.
    row_div = [bool(np.all(g[y, :] == BG)) for y in range(h)]
    col_div = [bool(np.all(g[:, x] == BG)) for x in range(w)]
    # Consecutive divider lines merge; maximal non-divider runs are panel bands.
    rb = _runs(row_div)
    cb = _runs(col_div)
    if not rb or not cb:
        return [[BG]]
    out = []
    for (y0, y1) in rb:
        line = []
        for (x0, x1) in cb:
            p = g[y0:y1 + 1, x0:x1 + 1]
            vals = p[p != BG]
            if vals.size == 0:
                line.append(BG)
                continue
            counts = {}
            for v in vals.tolist():
                counts[v] = counts.get(v, 0) + 1
            best = max(counts.values())
            # Ties do not occur in the generator domain (one colour per panel);
            # smallest colour is only a deterministic fallback.
            line.append(min(c for c, n in counts.items() if n == best))
        out.append(line)
    return out
'''
    return src.replace('__BG__', str(bg))
