def build_program(d4, palette):
    d4 = int(d4) % 8
    flip = d4 >= 4
    rot = d4 % 4
    # Original quadrant index -> (quadrant row, quadrant col) in canonical layout.
    orig_pos = [(0, 0), (0, 1), (1, 0), (1, 1)]
    def move(qr, qc):
        if flip:
            qc = 1 - qc
        for _ in range(rot):
            qr, qc = qc, 1 - qr
        return (qr, qc)
    vis_pos = [move(qr, qc) for (qr, qc) in orig_pos]
    # Painting order in canonical terms: idx 0 (colour 4), 3 (colour 9), 2 (colour 6), 1 (colour 5).
    paint = [vis_pos[i] for i in (0, 3, 2, 1)]
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('# Visible quadrant positions (quadrant-row, quadrant-col), painted lowest priority first.')
    lines.append('# Roles: palette[4] quadrant, palette[9] quadrant, palette[6] quadrant, palette[5] quadrant.')
    lines.append('PAINT_ORDER = %r' % (paint,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    h, w = H // 2, W // 2')
    lines.append('    out = np.full((h, w), BG, dtype=int)')
    lines.append('    for qr, qc in PAINT_ORDER:')
    lines.append('        q = g[qr * h:(qr + 1) * h, qc * w:(qc + 1) * w]')
    lines.append('        m = q != BG')
    lines.append('        out[m] = q[m]')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
