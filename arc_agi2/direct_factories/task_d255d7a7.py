def build_program(d4, palette):
    pal = [int(v) for v in palette] if palette is not None else list(range(10))
    if len(pal) < 10:
        pal = pal + list(range(len(pal), 10))
    bg = pal[7]
    pipe = pal[0]
    template = '''BG = __BG__
PIPE = __PIPE__


def _components(g, H, W):
    seen = [[False] * W for _ in range(H)]
    comps = []
    for y in range(H):
        for x in range(W):
            if g[y][x] == PIPE and not seen[y][x]:
                seen[y][x] = True
                stack = [(y, x)]
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == PIPE:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                comps.append(cells)
    return comps


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    pastes = []
    for cells in _components(g, H, W):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        r0, r1, c0, c1 = min(ys), max(ys), min(xs), max(xs)
        h = r1 - r0 + 1
        w = c1 - c0 + 1
        if h == 3 and w > 3:
            # Horizontal pipe: the head occupies the pipe-coloured run of the top bbox row.
            hcols = [x for x in range(c0, c1 + 1) if g[r0][x] == PIPE]
            if not hcols:
                continue
            a, b = min(hcols), max(hcols)
            hw = b - a + 1
            na = (c1 - hw + 1) if a == c0 else c0
            for y, x in cells:
                out[y][x] = BG
            for y in range(r0, r0 + 3):
                for x in range(a, b + 1):
                    out[y][x] = BG
            for dy in range(3):
                for dx in range(hw):
                    pastes.append((r0 + dy, na + dx, g[r0 + dy][a + dx]))
        elif w == 3 and h > 3:
            # Vertical pipe: the head occupies the pipe-coloured run of the left bbox column.
            hrows = [y for y in range(r0, r1 + 1) if g[y][c0] == PIPE]
            if not hrows:
                continue
            a, b = min(hrows), max(hrows)
            hh = b - a + 1
            na = (r1 - hh + 1) if a == r0 else r0
            for y, x in cells:
                out[y][x] = BG
            for y in range(a, b + 1):
                for x in range(c0, c0 + 3):
                    out[y][x] = BG
            for dy in range(hh):
                for dx in range(3):
                    pastes.append((na + dy, c0 + dx, g[a + dy][c0 + dx]))
    for y, x, v in pastes:
        if 0 <= y < H and 0 <= x < W:
            out[y][x] = v
    return out
'''
    return template.replace('__BG__', str(bg)).replace('__PIPE__', str(pipe))
