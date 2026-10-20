def build_program(d4, palette):
    bg = int(palette[0])
    ob = int(palette[5])
    src = int(palette[8])
    ray = int(palette[2])
    st = int(palette[4])
    # rotations keep the clockwise turning of the staircases; reflections make them turn counter-clockwise
    chir = -1 if int(d4) >= 4 else 1
    code = '''import numpy as np

BG = __BG__
OB = __OB__
SRC = __SRC__
RAY = __RAY__
ST = __ST__
CHIR = __CHIR__

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    ys, xs = np.where(g == SRC)
    if len(ys) == 0:
        return out.tolist()
    cy = int((ys.min() + ys.max()) // 2)
    cx = int((xs.min() + xs.max()) // 2)

    def inb(y, x):
        return 0 <= y < H and 0 <= x < W

    def is_ob(y, x):
        return inb(y, x) and g[y, x] == OB

    # diagonal rays from each corner of the source block
    for dy in (-1, 1):
        for dx in (-1, 1):
            y, x = cy + dy, cx + dx
            while True:
                if is_ob(y + dy, x) and is_ob(y, x + dx):
                    break
                y, x = y + dy, x + dx
                if not inb(y, x) or g[y, x] == OB:
                    break
                if g[y, x] != SRC:
                    out[y, x] = RAY

    # staircases from the middle of each side, drawn after the rays
    for oy, ox in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        sy, sx = CHIR * ox, -CHIR * oy
        y, x = cy + oy, cx + ox
        dy, dx = oy, ox
        done = False
        while not done:
            for _ in range(2):
                y, x = y + dy, x + dx
                if not inb(y, x) or g[y, x] == OB:
                    done = True
                    break
                out[y, x] = ST
            if (dy, dx) == (oy, ox):
                dy, dx = sy, sx
            else:
                dy, dx = oy, ox
    return out.tolist()
'''
    code = code.replace('__BG__', str(bg)).replace('__OB__', str(ob)).replace('__SRC__', str(src))
    code = code.replace('__RAY__', str(ray)).replace('__ST__', str(st)).replace('__CHIR__', str(chir))
    return code
