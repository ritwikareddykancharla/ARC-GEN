def build_program(d4, palette):
    red = int(palette[2])
    blue = int(palette[1])
    bg = int(palette[0])
    src = '''# Visible-coordinate solver (d4=%d has no effect on this rule).
# The rule recolours every edge-isolated red cell to blue. A cell's four
# edge neighbours (up, down, left, right) are the same set under every
# rotation and reflection, so the solver needs no axis or direction.
RED = %d
BLUE = %d
BG = %d

def solve(demonstrations, grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [list(row) for row in grid]
    for y in range(h):
        for x in range(w):
            if grid[y][x] != RED:
                continue
            isolated = True
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and grid[ny][nx] == RED:
                    isolated = False
                    break
            if isolated:
                out[y][x] = BLUE
    return out
''' % (int(d4), red, blue, bg)
    return src
