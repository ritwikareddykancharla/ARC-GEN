def build_program(d4, palette):
    seed = int(palette[2])
    fill = int(palette[1])
    bg = int(palette[0])
    # The 3x3 Chebyshev neighbourhood is invariant under every D4 transform,
    # so d4 does not change the mechanism. Only the colour roles are specialised.
    lines = []
    lines.append('SEED = %d' % seed)
    lines.append('FILL = %d' % fill)
    lines.append('BG = %d' % bg)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = [list(map(int, row)) for row in grid]')
    lines.append('    H = len(g)')
    lines.append('    W = len(g[0]) if H else 0')
    lines.append('    seeds = [(r, c) for r in range(H) for c in range(W) if g[r][c] == SEED]')
    lines.append('    out = [row[:] for row in g]')
    lines.append('    for r, c in seeds:')
    lines.append('        for dr in (-1, 0, 1):')
    lines.append('            for dc in (-1, 0, 1):')
    lines.append('                if dr == 0 and dc == 0:')
    lines.append('                    continue')
    lines.append('                rr, cc = r + dr, c + dc')
    lines.append('                if 0 <= rr < H and 0 <= cc < W and g[rr][cc] == BG:')
    lines.append('                    out[rr][cc] = FILL')
    lines.append('    return out')
    return '\n'.join(lines) + '\n'
