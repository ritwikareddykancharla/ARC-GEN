def build_program(d4, palette):
    k = int(d4) % 4
    bg = int(palette[0])
    mark = int(palette[4])
    # Original legs/opening point DOWN; marker goes on the last row.
    # A horizontal flip leaves down unchanged. Each clockwise turn maps down->left->up->right.
    edge = {0: 'bottom', 1: 'left', 2: 'top', 3: 'right'}[k]
    src = '''
BG = %d
MARK = %d
EDGE = %r

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    seen = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if g[y][x] == BG or seen[y][x]:
                continue
            col = g[y][x]
            seen[y][x] = True
            stack = [(y, x)]
            y0 = y1 = y
            x0 = x1 = x
            while stack:
                cy, cx = stack.pop()
                if cy < y0: y0 = cy
                if cy > y1: y1 = cy
                if cx < x0: x0 = cx
                if cx > x1: x1 = cx
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            if EDGE == 'bottom':
                out[H - 1][(x0 + x1) // 2] = MARK
            elif EDGE == 'top':
                out[0][(x0 + x1) // 2] = MARK
            elif EDGE == 'left':
                out[(y0 + y1) // 2][0] = MARK
            else:
                out[(y0 + y1) // 2][W - 1] = MARK
    return out
''' % (bg, mark, edge)
    return src
