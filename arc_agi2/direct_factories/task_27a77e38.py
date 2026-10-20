def build_program(d4, palette):
    k = int(d4) % 4
    # In the canonical frame the coloured block is above the divider (top side).
    # A horizontal mirror (d4>=4) keeps the top side on top and fixes the odd centre column.
    # Each clockwise rotation moves top -> right -> bottom -> left.
    side = ['top', 'right', 'bottom', 'left'][k]
    div = int(palette[5])
    src = '''import numpy as np

SIDE = %r
DIV = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    if SIDE in ('top', 'bottom'):
        lines = [y for y in range(h) if np.all(g[y, :] == DIV)]
        if not lines:
            lines = [y for y in range(1, h) if np.all(g[y, :] == g[y, 0])]
        if SIDE == 'top':
            y = lines[0] if lines else h // 2
            block = g[:y, :]
            target = (h - 1, (w - 1) // 2)
        else:
            y = lines[-1] if lines else h // 2
            block = g[y + 1:, :]
            target = (0, (w - 1) // 2)
    else:
        lines = [x for x in range(w) if np.all(g[:, x] == DIV)]
        if not lines:
            lines = [x for x in range(1, w) if np.all(g[:, x] == g[0, x])]
        if SIDE == 'left':
            x = lines[0] if lines else w // 2
            block = g[:, :x]
            target = ((h - 1) // 2, w - 1)
        else:
            x = lines[-1] if lines else w // 2
            block = g[:, x + 1:]
            target = ((h - 1) // 2, 0)
    if block.size == 0:
        return out.tolist()
    vals, counts = np.unique(block, return_counts=True)
    best = int(vals[int(np.argmax(counts))])
    out[target[0], target[1]] = best
    return out.tolist()
''' % (side, div)
    return src
