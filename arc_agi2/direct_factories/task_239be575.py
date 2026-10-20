def build_program(d4, palette):
    bg = int(palette[0])
    red = int(palette[2])
    cyan = int(palette[8])
    src = '''
RED = %d
CYAN = %d
BG = %d

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    reds = [(y, x) for y in range(H) for x in range(W) if g[y][x] == RED]
    if not reds:
        return [[BG]]
    # flood fill (4-connected) from the first red square through red/azure cells
    start = reds[0]
    # gather the full first red block (4-connected red component)
    seen = set([start])
    stack = [start]
    while stack:
        y, x = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and (ny, nx) not in seen:
                v = g[ny][nx]
                if v == RED or v == CYAN:
                    seen.add((ny, nx))
                    stack.append((ny, nx))
    connected = all(c in seen for c in reds)
    return [[CYAN if connected else BG]]
''' % (red, cyan, bg)
    return src
