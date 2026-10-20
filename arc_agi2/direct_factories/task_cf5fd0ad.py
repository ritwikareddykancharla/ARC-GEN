def _rot_cw(m):
    n = len(m)
    return [[m[n - 1 - j][i] for j in range(n)] for i in range(n)]


def _apply_d4(m, d4):
    m = [list(r) for r in m]
    if d4 >= 4:
        m = [list(reversed(r)) for r in m]
    for _ in range(d4 % 4):
        m = _rot_cw(m)
    return m


def build_program(d4, palette):
    d4 = int(d4) % 8
    # Native layout: quadrant id -> number of np.rot90 (counter-clockwise) turns.
    # 0 = top-left (180), 1 = top-right (clockwise), 2 = bottom-left (counter-clockwise), 3 = bottom-right (identity).
    native_k = {0: 2, 1: 3, 2: 1, 3: 0}
    # Move the quadrant positions with the same D4 map that is applied to every grid.
    ids = _apply_d4([[0, 1], [2, 3]], d4)
    reflect = d4 >= 4
    layout = []
    for qi in range(2):
        for qj in range(2):
            k = native_k[ids[qi][qj]]
            # Conjugating a rotation by a rotation leaves it unchanged.
            # Conjugating it by a reflection reverses the turn direction.
            if reflect:
                k = (-k) % 4
            layout.append((qi, qj, k))
    lines = []
    lines.append('import numpy as np')
    lines.append('from collections import Counter')
    lines.append('')
    lines.append('# (quadrant_row, quadrant_col, np.rot90 turns of the visible input)')
    lines.append('LAYOUT = ' + repr(layout))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])')
    lines.append('    out = np.full((4 * h, 4 * w), bg, dtype=int)')
    lines.append('    for qi, qj, k in LAYOUT:')
    lines.append('        blk = np.rot90(g, k)')
    lines.append('        bh, bw = blk.shape')
    lines.append('        tile = np.tile(blk, (2, 2))')
    lines.append('        y0 = qi * 2 * bh')
    lines.append('        x0 = qj * 2 * bw')
    lines.append('        out[y0:y0 + 2 * bh, x0:x0 + 2 * bw] = tile')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
