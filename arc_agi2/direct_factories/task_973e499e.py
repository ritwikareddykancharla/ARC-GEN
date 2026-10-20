def build_program(d4, palette):
    fill = int(palette[0])
    src = '''import numpy as np

FILL = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    n, m = g.shape
    out = np.full((n * n, m * m), FILL, dtype=int)
    for i in range(n):
        for j in range(m):
            c = g[i, j]
            block = np.where(g == c, g, FILL)
            out[i * n:(i + 1) * n, j * m:(j + 1) * m] = block
    return out.tolist()
''' % fill
    return src
