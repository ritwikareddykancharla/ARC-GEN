def build_program(d4, palette):
    base = {1: (0, 1), 2: (0, -2), 7: (-2, 0), 9: (2, 0)}
    moves = {}
    for c, (dy, dx) in base.items():
        if d4 >= 4:
            dx = -dx
        for _ in range(d4 % 4):
            dy, dx = dx, -dy
        moves[int(palette[c])] = (int(dy), int(dx))
    bg = int(palette[8])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = ' + repr(bg))
    lines.append('MOVES = ' + repr(moves))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    out = np.full_like(g, BG)')
    lines.append('    for c in sorted(set(int(v) for v in np.unique(g)) - {BG}):')
    lines.append('        dy, dx = MOVES.get(c, (0, 0))')
    lines.append('        ys, xs = np.where(g == c)')
    lines.append('        for y, x in zip(ys.tolist(), xs.tolist()):')
    lines.append('            ny, nx = y + dy, x + dx')
    lines.append('            if 0 <= ny < H and 0 <= nx < W:')
    lines.append('                out[ny, nx] = c')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
