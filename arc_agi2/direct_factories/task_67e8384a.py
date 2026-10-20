def build_program(d4, palette):
    # Track where the original top-left output quadrant (which holds the input) lands.
    # Corners in clockwise order: 0=TL, 1=TR, 2=BR, 3=BL.
    # Indices >= 4 first reverse each row, which moves TL to TR. Each clockwise turn then advances one corner.
    start = 1 if d4 >= 4 else 0
    corner = (start + (d4 % 4)) % 4
    top = corner in (0, 1)
    left = corner in (0, 3)
    src = []
    src.append('import numpy as np')
    src.append('')
    src.append('INPUT_ON_TOP = %r' % (top,))
    src.append('INPUT_ON_LEFT = %r' % (left,))
    src.append('')
    src.append('def solve(demonstrations, grid):')
    src.append('    g = np.array(grid, dtype=int)')
    src.append('    h, w = g.shape')
    src.append('    out = np.zeros((2 * h, 2 * w), dtype=int)')
    src.append('    for vr in (0, 1):')
    src.append('        for hc in (0, 1):')
    src.append('            block = g')
    src.append('            in_top_half = (vr == 0)')
    src.append('            in_left_half = (hc == 0)')
    src.append('            if in_top_half != INPUT_ON_TOP:')
    src.append('                block = block[::-1, :]')
    src.append('            if in_left_half != INPUT_ON_LEFT:')
    src.append('                block = block[:, ::-1]')
    src.append('            out[vr * h:(vr + 1) * h, hc * w:(hc + 1) * w] = block')
    src.append('    return out.tolist()')
    return '\n'.join(src) + '\n'
