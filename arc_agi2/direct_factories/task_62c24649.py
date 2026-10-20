def build_program(d4, palette):
    bottom, right = ((False, False), (False, True), (True, True),
                     (True, False), (False, True), (True, True),
                     (True, False), (False, False))[d4]
    row = "h - 1 - rr" if bottom else "rr"
    col = "w - 1 - cc" if right else "cc"
    return f'''def solve(demonstrations, grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * (2 * w) for _ in range(2 * h)]
    for r in range(2 * h):
        rr = r if r < h else 2 * h - 1 - r
        for c in range(2 * w):
            cc = c if c < w else 2 * w - 1 - c
            out[r][c] = grid[{row}][{col}]
    return out
'''
