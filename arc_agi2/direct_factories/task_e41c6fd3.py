def build_program(d4, palette):
    axis = 0 if d4 % 2 == 0 else 1
    dest = "r + shift, c" if axis == 0 else "r, c + shift"
    return f'''BG = {int(palette[0])}
ANCHOR = {int(palette[8])}

def solve(demonstrations, grid):
    h, w = len(grid), len(grid[0])
    objects = {{}}
    for r, row in enumerate(grid):
        for c, colour in enumerate(row):
            if colour != BG:
                objects.setdefault(colour, []).append((r, c))
    alignment = min(p[{axis}] for p in objects[ANCHOR])
    out = [[BG] * w for _ in range(h)]
    for colour, cells in objects.items():
        shift = alignment - min(p[{axis}] for p in cells)
        for r, c in cells:
            y, x = {dest}
            out[y][x] = colour
    return out
'''
