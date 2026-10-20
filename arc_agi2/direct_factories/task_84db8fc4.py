def build_program(d4, palette):
    zero = int(palette[0])
    border_col = int(palette[2])
    inner_col = int(palette[5])
    src = '''from collections import deque

FILL = %d
BORDER = %d
INNER = %d

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    seen = [[False] * W for _ in range(H)]
    for sy in range(H):
        for sx in range(W):
            if g[sy][sx] != FILL or seen[sy][sx]:
                continue
            seen[sy][sx] = True
            q = deque([(sy, sx)])
            cells = []
            touches = False
            while q:
                y, x = q.popleft()
                cells.append((y, x))
                if y == 0 or x == 0 or y == H - 1 or x == W - 1:
                    touches = True
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == FILL:
                        seen[ny][nx] = True
                        q.append((ny, nx))
            col = BORDER if touches else INNER
            for y, x in cells:
                out[y][x] = col
    return out
''' % (zero, border_col, inner_col)
    return src
