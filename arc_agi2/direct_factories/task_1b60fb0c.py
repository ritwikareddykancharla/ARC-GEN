def build_program(d4, palette):
    # Transform the two possible rotation centres, not the input grid.
    centres = []
    for c in (9, 10):
        y, x = str(c), str(c)
        if d4 >= 4:
            x = f'(E - {x})'
        for _ in range(d4 % 4):
            y, x = x, f'(E - {y})'
        centres.append(f'({y}, {x})')
    return '''BG = %d
FG = %d
FILL = %d

def solve(demonstrations, grid):
    h, w = len(grid), len(grid[0])
    E = 2 * (h - 1)
    cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == FG}
    candidates = []
    for cy2, cx2 in [%s]:
        closure = set()
        valid = True
        for r, c in cells:
            orbit = set()
            y, x = r, c
            for _ in range(4):
                if not (0 <= y < h and 0 <= x < w):
                    valid = False
                    break
                orbit.add((y, x))
                yy2, xx2 = cy2 + 2*x - cx2, cx2 - 2*y + cy2
                if yy2 %% 2 or xx2 %% 2:
                    valid = False
                    break
                y, x = yy2 // 2, xx2 // 2
            if not valid or len(orbit & cells) < min(3, len(orbit)):
                valid = False
                break
            closure.update(orbit)
        if valid:
            out = [row[:] for row in grid]
            for r, c in closure - cells:
                if out[r][c] == BG: out[r][c] = FILL
            if out not in candidates: candidates.append(out)
    if len(candidates) != 1:
        raise ValueError('Rotation centre does not determine a unique completion')
    return candidates[0]
''' % (palette[0], palette[1], palette[2], ', '.join(centres))
