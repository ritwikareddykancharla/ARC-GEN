def build_program(d4, palette):
    k = int(d4) % 4
    # Native mechanism: output = [vertical mirror of input ; input] stacked top-to-bottom.
    # The row reversal (d4>=4) commutes with this vertical stacking, so only rotation matters.
    # k=0: mirror above original; k=1: original left, mirror right;
    # k=2: original above, mirror below; k=3: mirror left, original right.
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    if k == 0:
        lines.append('    h, w = g.shape')
        lines.append('    out = np.zeros((2 * h, w), dtype=int)')
        lines.append('    out[h:, :] = g')
        lines.append('    out[:h, :] = g[::-1, :]')
    elif k == 1:
        lines.append('    h, w = g.shape')
        lines.append('    out = np.zeros((h, 2 * w), dtype=int)')
        lines.append('    out[:, :w] = g')
        lines.append('    out[:, w:] = g[:, ::-1]')
    elif k == 2:
        lines.append('    h, w = g.shape')
        lines.append('    out = np.zeros((2 * h, w), dtype=int)')
        lines.append('    out[:h, :] = g')
        lines.append('    out[h:, :] = g[::-1, :]')
    else:
        lines.append('    h, w = g.shape')
        lines.append('    out = np.zeros((h, 2 * w), dtype=int)')
        lines.append('    out[:, w:] = g')
        lines.append('    out[:, :w] = g[:, ::-1]')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
