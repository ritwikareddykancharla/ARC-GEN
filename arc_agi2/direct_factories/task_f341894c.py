def build_program(d4, palette):
    bg = int(palette[8])
    mark = int(palette[7])
    one = int(palette[1])
    six = int(palette[6])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('MARK = %d' % mark)
    lines.append('ONE = %d' % one)
    lines.append('SIX = %d' % six)
    lines.append('')
    lines.append('''def solve(demonstrations, grid):
    g = [list(map(int, r)) for r in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [r[:] for r in g]
    row_marks = [[x for x in range(W) if g[y][x] == MARK] for y in range(H)]
    col_marks = [[y for y in range(H) if g[y][x] == MARK] for x in range(W)]

    def is_dom(v):
        return v == ONE or v == SIX

    # Candidate pairs: orthogonally adjacent cells of opposite domino colours
    # whose shared line (row if side by side, column if stacked) holds a mark.
    edges = []
    deg = {}
    for y in range(H):
        for x in range(W):
            if not is_dom(g[y][x]):
                continue
            for ny, nx, horiz in ((y, x + 1, True), (y + 1, x, False)):
                if ny >= H or nx >= W:
                    continue
                v = g[ny][nx]
                if not is_dom(v) or v == g[y][x]:
                    continue
                marks = row_marks[y] if horiz else col_marks[x]
                if not marks:
                    continue
                edges.append(((y, x), (ny, nx), horiz))
                deg[(y, x)] = deg.get((y, x), 0) + 1
                deg[(ny, nx)] = deg.get((ny, nx), 0) + 1

    used = set()
    pairs = []
    # Unambiguous pairs first, then any remaining ones in scan order.
    for e in edges:
        a, b, _ = e
        if deg[a] == 1 and deg[b] == 1:
            pairs.append(e)
            used.add(a)
            used.add(b)
    for e in edges:
        a, b, _ = e
        if a in used or b in used:
            continue
        pairs.append(e)
        used.add(a)
        used.add(b)

    for a, b, horiz in pairs:
        if horiz:
            positions = row_marks[a[0]]
            pa, pb = a[1], b[1]
        else:
            positions = col_marks[a[1]]
            pa, pb = a[0], b[0]
        best = None
        hits = 0
        for p in positions:
            da = abs(p - pa)
            db = abs(p - pb)
            d = min(da, db)
            end = a if da < db else b
            if best is None or d < best[0]:
                best = (d, end)
                hits = 1
            elif d == best[0]:
                hits += 1
        if best is None or hits != 1:
            continue  # no unique nearest mark: leave unchanged
        end = best[1]
        other = b if end == a else a
        out[end[0]][end[1]] = SIX
        out[other[0]][other[1]] = ONE
    return out
''')
    return '\n'.join(lines)
