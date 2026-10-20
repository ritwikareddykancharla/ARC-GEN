def build_program(d4, palette):
    d4 = int(d4) % 8
    k = d4 % 4
    flipped = d4 >= 4
    # Original split axis is rows. Odd rotations turn it into visible columns.
    axis = k % 2
    # Offset of the visible first half along the non-split axis.
    # It is 1 when exactly one of (split axis reversed, other axis reversed) holds.
    # Derived per d4: 0->0,1->1,2->0,3->1,4->1,5->0,6->1,7->0
    x = (d4 % 2) ^ (1 if flipped else 0)
    fill = int(palette[9])
    lines = []
    lines.append('def solve(demonstrations, grid):')
    lines.append('    FILL = %d' % fill)
    lines.append('    AXIS = %d' % axis)
    lines.append('    X = %d' % x)
    lines.append('    g = [list(row) for row in grid]')
    lines.append('    R = len(g)')
    lines.append('    C = len(g[0]) if R else 0')
    lines.append('    out = [[FILL] * (C + 1) for _ in range(R + 1)]')
    lines.append('    if AXIS == 0:')
    lines.append('        half = R // 2')
    lines.append('        for r in range(R):')
    lines.append('            if r < half:')
    lines.append('                dr, dc = 0, X')
    lines.append('            else:')
    lines.append('                dr, dc = 1, 1 - X')
    lines.append('            for c in range(C):')
    lines.append('                out[r + dr][c + dc] = g[r][c]')
    lines.append('    else:')
    lines.append('        half = C // 2')
    lines.append('        for r in range(R):')
    lines.append('            for c in range(C):')
    lines.append('                if c < half:')
    lines.append('                    dr, dc = X, 0')
    lines.append('                else:')
    lines.append('                    dr, dc = 1 - X, 1')
    lines.append('                out[r + dr][c + dc] = g[r][c]')
    lines.append('    return out')
    return '\n'.join(lines) + '\n'
