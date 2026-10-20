def build_program(d4, palette):
    # The original rule crops the top-right block of a 3x3 block arrangement.
    # Where does that corner end up after the D4 transform?
    # For d4 >= 4, rows are reversed first (horizontal flip), so TR becomes TL.
    # Each clockwise rotation then moves corners TL->TR->BR->BL->TL.
    cw = ['TL', 'TR', 'BR', 'BL']
    start = 'TL' if d4 >= 4 else 'TR'
    corner = cw[(cw.index(start) + (d4 % 4)) % 4]
    use_bottom = corner[0] == 'B'
    use_right = corner[1] == 'R'
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('USE_BOTTOM = %s' % ('True' if use_bottom else 'False'))
    lines.append('USE_RIGHT = %s' % ('True' if use_right else 'False'))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    bh = max(1, h // 3)')
    lines.append('    bw = max(1, w // 3)')
    lines.append('    r0 = h - bh if USE_BOTTOM else 0')
    lines.append('    c0 = w - bw if USE_RIGHT else 0')
    lines.append('    out = g[r0:r0 + bh, c0:c0 + bw].copy()')
    lines.append('    return out.astype(int).tolist()')
    return '\n'.join(lines) + '\n'
