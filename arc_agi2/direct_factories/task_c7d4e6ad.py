def build_program(d4, palette):
    d4 = int(d4) % 8
    k = d4 % 4
    # Edges in clockwise order: 0=left, 1=top, 2=right, 3=bottom.
    # The original key column is the left edge. A row reversal (d4>=4) moves it to the right edge.
    # Each clockwise rotation moves an edge one step clockwise: left->top->right->bottom->left.
    start = 0 if d4 < 4 else 2
    edge = (start + k) % 4
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('KEY_EDGE = %d  # 0=left column, 1=top row, 2=right column, 3=bottom row' % edge)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    out = g.copy()')
    if edge == 0:
        lines.append('    # The key lies in the left column. Each non-background cell takes the key colour of its row.')
        lines.append('    for y in range(h):')
        lines.append('        key = int(g[y, 0])')
        lines.append('        for x in range(w):')
        lines.append('            if g[y, x] != BG:')
        lines.append('                out[y, x] = key')
    elif edge == 2:
        lines.append('    # The key lies in the right column. Each non-background cell takes the key colour of its row.')
        lines.append('    for y in range(h):')
        lines.append('        key = int(g[y, w - 1])')
        lines.append('        for x in range(w):')
        lines.append('            if g[y, x] != BG:')
        lines.append('                out[y, x] = key')
    elif edge == 1:
        lines.append('    # The key lies in the top row. Each non-background cell takes the key colour of its column.')
        lines.append('    for x in range(w):')
        lines.append('        key = int(g[0, x])')
        lines.append('        for y in range(h):')
        lines.append('            if g[y, x] != BG:')
        lines.append('                out[y, x] = key')
    else:
        lines.append('    # The key lies in the bottom row. Each non-background cell takes the key colour of its column.')
        lines.append('    for x in range(w):')
        lines.append('        key = int(g[h - 1, x])')
        lines.append('        for y in range(h):')
        lines.append('            if g[y, x] != BG:')
        lines.append('                out[y, x] = key')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
