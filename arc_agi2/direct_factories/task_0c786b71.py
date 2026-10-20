def build_program(d4, palette):
    # Quadrants in clockwise order; one clockwise rotation moves a quadrant one step forward.
    cycle = [(True, True), (True, False), (False, False), (False, True)]  # (top?, left?) for TL, TR, BR, BL
    # In the original task the unflipped input sits bottom-right (index 2).
    # A horizontal flip (d4 >= 4) moves it to bottom-left (index 3) before rotation.
    start = 3 if d4 >= 4 else 2
    top, left = cycle[(start + (d4 % 4)) % 4]
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('ANCHOR_TOP = %r' % bool(top))
    lines.append('ANCHOR_LEFT = %r' % bool(left))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    a = np.array(grid, dtype=int)')
    lines.append('    h, w = a.shape')
    lines.append('    out = np.zeros((2 * h, 2 * w), dtype=int)')
    lines.append('    # Choose the quadrant that holds the unflipped copy and the half that receives the mirror.')
    lines.append('    r0 = 0 if ANCHOR_TOP else h')
    lines.append('    c0 = 0 if ANCHOR_LEFT else w')
    lines.append('    rm = h if ANCHOR_TOP else 0')
    lines.append('    cm = w if ANCHOR_LEFT else 0')
    lines.append('    # Place the input unchanged in its anchor quadrant.')
    lines.append('    out[r0:r0 + h, c0:c0 + w] = a')
    lines.append('    # Put a left/right mirror beside it to complete the anchor half.')
    lines.append('    out[r0:r0 + h, cm:cm + w] = a[:, ::-1]')
    lines.append('    # Reflect the finished half top/bottom to fill the other half.')
    lines.append('    out[rm:rm + h, :] = out[r0:r0 + h, :][::-1, :]')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
