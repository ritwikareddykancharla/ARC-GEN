def build_program(d4, palette):
    # This rule is equivariant under every D4 transform and every colour permutation.
    # Under D4, nested solid axis-aligned rectangles map to nested solid axis-aligned
    # rectangles. Each child stays strictly inside its parent, and any corner of the
    # bounding box still lies inside the rectangle. The output is a square of
    # concentric rings, which is itself D4-symmetric.
    # Every colour role is read from visible pixels, so d4 and palette need no constants.
    _ = (d4, palette)
    program = '''
import numpy as np

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    # The outermost layer fills the whole canvas. Every nested rectangle sits at
    # offset >= 1 from its parent, so the grid border (any corner) always has the
    # background colour.
    cur = int(g[0, 0])
    colours = [cur]
    y0, x0, y1, x1 = 0, 0, H - 1, W - 1
    for _ in range(64):
        sub = g[y0:y1 + 1, x0:x1 + 1]
        ys, xs = np.nonzero(sub != cur)
        if len(ys) == 0:
            break
        ny0, nx0 = y0 + int(ys.min()), x0 + int(xs.min())
        ny1, nx1 = y0 + int(ys.max()), x0 + int(xs.max())
        if (ny0, nx0, ny1, nx1) == (y0, x0, y1, x1) and len(colours) > 1:
            break  # no strict nesting; outside the constructor domain
        y0, x0, y1, x1 = ny0, nx0, ny1, nx1
        # The child rectangle is solid, so its bounding-box corner has the child colour.
        cur = int(g[y0, x0])
        colours.append(cur)
    n = len(colours)
    size = 2 * n - 1
    out = np.full((size, size), colours[0], dtype=int)
    for k in range(1, n):
        out[k:size - k, k:size - k] = colours[k]
    return out.tolist()
'''
    return program
