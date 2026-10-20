def build_program(d4, palette):
    d4 = int(d4) % 8
    # The constructor makes two blocks symmetric about the main diagonal (b == b.T).
    # Under the D4 view that axis becomes either the main diagonal or the anti-diagonal.
    # Row reversal swaps the two diagonals. A clockwise quarter turn also swaps them.
    flips = (1 if d4 >= 4 else 0) + (d4 % 4)
    axis = 'main' if flips % 2 == 0 else 'anti'
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('AXIS = %r' % axis)
    lines.append('')
    lines.append('def _sym(b):')
    lines.append('    if AXIS == "main":')
    lines.append('        return np.array_equal(b, b.T)')
    lines.append('    # anti-diagonal symmetry: b[i][j] == b[n-1-j][n-1-i]')
    lines.append('    return np.array_equal(b, b[::-1, ::-1].T)')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    if h >= w:')
    lines.append('        s = w')
    lines.append('        blocks = [g[i * s:(i + 1) * s, :] for i in range(h // s)]')
    lines.append('    else:')
    lines.append('        s = h')
    lines.append('        blocks = [g[:, i * s:(i + 1) * s] for i in range(w // s)]')
    lines.append('    odd = [b for b in blocks if not _sym(b)]')
    lines.append('    chosen = odd[0] if odd else blocks[0]')
    lines.append('    return chosen.copy().tolist()')
    lines.append('')
    return '\n'.join(lines)
