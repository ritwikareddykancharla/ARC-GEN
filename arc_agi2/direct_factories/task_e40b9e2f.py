def build_program(d4, palette):
    bg = int(palette[0])
    src = """BG = __BG__


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    cells = [(y, x, g[y][x]) for y in range(H) for x in range(W) if g[y][x] != BG]
    if not cells:
        return g
    n = len(cells)
    sy = sum(2 * y for y, x, c in cells)
    sx = sum(2 * x for y, x, c in cells)

    def build(cy2, cx2):
        # centre in doubled (half-cell) visible coordinates
        if (cy2 - cx2) % 2:
            return None
        out = [row[:] for row in g]
        added = 0
        for y, x, c in cells:
            dy = 2 * y - cy2
            dx = 2 * x - cx2
            for _ in range(3):
                dy, dx = dx, -dy
                ty = dy + cy2
                tx = dx + cx2
                if ty % 2 or tx % 2:
                    return None
                ny = ty // 2
                nx = tx // 2
                if ny < 0 or ny >= H or nx < 0 or nx >= W:
                    return None
                v = out[ny][nx]
                if v == BG:
                    out[ny][nx] = c
                    added += 1
                elif v != c:
                    return None
        return added, out

    best = None
    winners = set()
    for cy2 in range(2 * H):
        for cx2 in range(2 * W):
            r = build(cy2, cx2)
            if r is None:
                continue
            added, out = r
            encoded = tuple(tuple(row) for row in out)
            if best is None or added < best:
                best = added
                winners = {encoded}
            elif added == best:
                winners.add(encoded)
    if len(winners) != 1:
        raise ValueError("Pinwheel has no unique minimum-addition completion")
    return [list(row) for row in next(iter(winners))]
"""
    return src.replace('__BG__', str(bg))
