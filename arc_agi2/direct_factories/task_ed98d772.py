import numpy as np


def build_program(d4, palette):
    # The visible transform of the episode: for d4>=4 reverse each row, then rotate clockwise d4%4 times.
    def _view(x):
        x = np.asarray(x)
        if d4 >= 4:
            x = x[:, ::-1]
        return np.rot90(x, -(d4 % 4))

    # Work out, in visible coordinates, which rotation of the visible input fills each visible quadrant.
    # Use a symbolic 3x3 grid of distinct labels. It only derives the layout. No fixture data is used.
    G = np.arange(9).reshape(3, 3)
    O = np.zeros((6, 6), dtype=int)
    O[:3, :3] = G
    O[:3, 3:] = np.rot90(G, 1)
    O[3:, :3] = np.rot90(G, 2)
    O[3:, 3:] = np.rot90(G, 3)
    g = _view(G)
    o = _view(O)
    quad = []
    for qi in range(2):
        row = []
        for qj in range(2):
            blk = o[3 * qi:3 * qi + 3, 3 * qj:3 * qj + 3]
            found = None
            for k in range(4):
                if np.array_equal(np.rot90(g, k), blk):
                    found = k
                    break
            if found is None:
                raise ValueError('layout derivation failed')
            row.append(found)
        quad.append(row)

    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('# QUAD_ROT[r][c] = number of counter-clockwise quarter turns of the visible input')
    lines.append('# that is stamped into visible output quadrant (r, c).')
    lines.append('QUAD_ROT = ' + repr(quad))
    lines.append('')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.asarray(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    if h != w:')
    lines.append('        raise ValueError("square input expected")')
    lines.append('    n = h')
    lines.append('    vals, cnts = np.unique(g, return_counts=True)')
    lines.append('    bg = int(vals[np.argmax(cnts)])')
    lines.append('    out = np.full((2 * n, 2 * n), bg, dtype=int)')
    lines.append('    for r in range(2):')
    lines.append('        for c in range(2):')
    lines.append('            out[r * n:(r + 1) * n, c * n:(c + 1) * n] = np.rot90(g, QUAD_ROT[r][c])')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
