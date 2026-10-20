def build_program(d4, palette):
    base = {
        1: [(0, 0), (0, 1), (1, 0), (1, 1)],
        2: [(0, 1), (1, 0), (1, 1)],
        3: [(0, 0), (0, 1), (1, 1)],
        4: [(0, 0), (1, 0), (1, 1)],
    }

    def tf(cells):
        pts = list(cells)
        if d4 >= 4:
            pts = [(r, -c) for r, c in pts]
        for _ in range(d4 % 4):
            pts = [(c, -r) for r, c in pts]
        f = min(pts)
        return sorted((r - f[0], c - f[1]) for r, c in pts)

    shapes = [(int(palette[k]), tf(base[k])) for k in (1, 2, 3, 4)]
    fg = int(palette[8])
    lines = []
    lines.append('SHAPES = ' + repr(shapes))
    lines.append('FG = ' + repr(fg))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    H = len(grid)')
    lines.append('    W = len(grid[0]) if H else 0')
    lines.append('    target = set((r, c) for r in range(H) for c in range(W) if grid[r][c] == FG)')
    lines.append('    order = sorted(target)')
    lines.append('    covered = set()')
    lines.append('    placed = []')
    lines.append('    def rec(i):')
    lines.append('        while i < len(order) and order[i] in covered:')
    lines.append('            i += 1')
    lines.append('        if i == len(order):')
    lines.append('            return True')
    lines.append('        r, c = order[i]')
    lines.append('        for col, offs in SHAPES:')
    lines.append('            cells = [(r + dr, c + dc) for dr, dc in offs]')
    lines.append('            if all(q in target and q not in covered for q in cells):')
    lines.append('                covered.update(cells)')
    lines.append('                placed.append((col, cells))')
    lines.append('                if rec(i + 1):')
    lines.append('                    return True')
    lines.append('                placed.pop()')
    lines.append('                covered.difference_update(cells)')
    lines.append('        return False')
    lines.append('    out = [list(row) for row in grid]')
    lines.append('    if rec(0):')
    lines.append('        for col, cells in placed:')
    lines.append('            for y, x in cells:')
    lines.append('                out[y][x] = col')
    lines.append('    return out')
    return '\n'.join(lines) + '\n'
