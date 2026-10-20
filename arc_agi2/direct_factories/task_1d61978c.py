def build_program(d4, palette):
    bg = int(palette[7])
    major = int(palette[8])
    minor = int(palette[2])
    src = '''import numpy as np

BG = %d
MAJOR = %d
MINOR = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    m = g != BG

    def occ(y, x):
        return 0 <= y < H and 0 <= x < W and bool(m[y, x])

    fam_a = []  # cells continuing along (+1,+1)/(-1,-1)
    fam_b = []  # cells continuing along (+1,-1)/(-1,+1)
    for y in range(H):
        for x in range(W):
            if not m[y, x]:
                continue
            a = occ(y + 1, x + 1) or occ(y - 1, x - 1)
            b = occ(y + 1, x - 1) or occ(y - 1, x + 1)
            if a and not b:
                fam_a.append((y, x))
            elif b and not a:
                fam_b.append((y, x))
            elif a and b:
                # ambiguous (not produced by the generator): pick the direction
                # with the longer run through this cell
                def run(dy, dx):
                    n = 0
                    yy, xx = y + dy, x + dx
                    while occ(yy, xx):
                        n += 1
                        yy += dy
                        xx += dx
                    return n
                la = run(1, 1) + run(-1, -1)
                lb = run(1, -1) + run(-1, 1)
                (fam_a if la >= lb else fam_b).append((y, x))
    out = g.copy()
    if len(fam_a) >= len(fam_b):
        big, small = fam_a, fam_b
    else:
        big, small = fam_b, fam_a
    for y, x in big:
        out[y, x] = MAJOR
    for y, x in small:
        out[y, x] = MINOR
    return out.tolist()
''' % (bg, major, minor)
    return src
