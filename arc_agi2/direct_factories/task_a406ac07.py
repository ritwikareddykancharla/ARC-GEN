def build_program(d4, palette):
    return f'''BG = {int(palette[0])}

def solve(demonstrations, grid):
    h, w = len(grid), len(grid[0])
    border_row = next(r for r in (0, h-1) if all(v != BG for v in grid[r]))
    border_col = next(c for c in (0, w-1) if all(grid[r][c] != BG for r in range(h)))
    out = [row[:] for row in grid]
    for r in range(h):
        if r == border_row:
            continue
        for c in range(w):
            if c != border_col and grid[r][border_col] == grid[border_row][c]:
                out[r][c] = grid[r][border_col]
    return out
'''
