def build_program(d4, palette):
    d4 = int(d4) % 8
    bg = int(palette[0])
    fg = int(palette[8])
    flipped = d4 >= 4
    rot = d4 % 4
    # The canonical output is the N x N identity (main diagonal).
    # A row reversal turns the main diagonal into the anti-diagonal.
    # Each clockwise quarter turn also swaps main and anti-diagonal.
    # So the visible diagonal is the anti-diagonal iff exactly one of these holds.
    anti = (flipped != (rot % 2 == 1))
    lines = []
    lines.append('BG = %d' % bg)
    lines.append('FG = %d' % fg)
    lines.append('ANTI = %s' % ('True' if anti else 'False'))
    lines.append('')
    lines.append('def _count_objects(grid):')
    lines.append('    h = len(grid)')
    lines.append('    w = len(grid[0]) if h else 0')
    lines.append('    seen = [[False] * w for _ in range(h)]')
    lines.append('    count = 0')
    lines.append('    for y in range(h):')
    lines.append('        for x in range(w):')
    lines.append('            if grid[y][x] != BG and not seen[y][x]:')
    lines.append('                count += 1')
    lines.append('                seen[y][x] = True')
    lines.append('                stack = [(y, x)]')
    lines.append('                while stack:')
    lines.append('                    cy, cx = stack.pop()')
    lines.append('                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):')
    lines.append('                        ny, nx = cy + dy, cx + dx')
    lines.append('                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and grid[ny][nx] != BG:')
    lines.append('                            seen[ny][nx] = True')
    lines.append('                            stack.append((ny, nx))')
    lines.append('    return count')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = [list(map(int, row)) for row in grid]')
    lines.append('    n = _count_objects(g)')
    lines.append('    out = [[BG] * n for _ in range(n)]')
    lines.append('    for i in range(n):')
    lines.append('        j = (n - 1 - i) if ANTI else i')
    lines.append('        out[i][j] = FG')
    lines.append('    return out')
    return '\n'.join(lines) + '\n'
