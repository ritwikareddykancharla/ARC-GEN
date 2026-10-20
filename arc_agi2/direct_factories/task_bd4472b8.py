def build_program(d4, palette):
    header = ("grid[0][i]", "grid[i][w-1]", "grid[h-1][w-1-i]",
              "grid[h-1-i][0]", "grid[0][w-1-i]", "grid[h-1-i][w-1]",
              "grid[h-1][i]", "grid[i][0]")[d4]
    dimension = "w" if d4 % 2 == 0 else "h"
    assignment = (
        "out[depth] = [colour] * w",
        "for r in range(h): out[r][w-1-depth] = colour",
        "out[h-1-depth] = [colour] * w",
        "for r in range(h): out[r][depth] = colour",
    )[d4 % 4]
    return f'''def solve(demonstrations, grid):
    h, w = len(grid), len(grid[0])
    n = {dimension}
    colours = [{header} for i in range(n)]
    out = [row[:] for row in grid]
    for depth in range(2, 2*n+2):
        colour = colours[(depth-2) % n]
        {assignment}
    return out
'''
