TEMPLATE = '''
BG = __BG__
AXIS = '__AXIS__'
STEP = __STEP__


def solve(demonstrations, grid):
    src = [[int(v) for v in row] for row in grid]
    H = len(src)
    W = len(src[0]) if H else 0
    out = [row[:] for row in src]
    if H == 0 or W == 0:
        return out
    if AXIS == 'v':
        edge = H - 1 if STEP == 1 else 0
        for x in range(W):
            if src[edge][x] == BG:
                continue
            for y in range(H):
                if src[y][x] != BG:
                    continue
                yy = y
                colour = None
                while 0 <= yy < H:
                    if src[yy][x] != BG:
                        colour = src[yy][x]
                        break
                    if x - 1 >= 0 and src[yy][x - 1] != BG:
                        colour = src[yy][x - 1]
                        break
                    if x + 1 < W and src[yy][x + 1] != BG:
                        colour = src[yy][x + 1]
                        break
                    yy += STEP
                if colour is not None:
                    out[y][x] = colour
    else:
        edge = W - 1 if STEP == 1 else 0
        for y in range(H):
            if src[y][edge] == BG:
                continue
            for x in range(W):
                if src[y][x] != BG:
                    continue
                xx = x
                colour = None
                while 0 <= xx < W:
                    if src[y][xx] != BG:
                        colour = src[y][xx]
                        break
                    if y - 1 >= 0 and src[y - 1][xx] != BG:
                        colour = src[y - 1][xx]
                        break
                    if y + 1 < H and src[y + 1][xx] != BG:
                        colour = src[y + 1][xx]
                        break
                    xx += STEP
                if colour is not None:
                    out[y][x] = colour
    return out
'''


def build_program(d4, palette):
    k = int(d4) % 4
    bg = int(palette[0])
    if k == 0:
        axis, step = 'v', 1
    elif k == 1:
        axis, step = 'h', -1
    elif k == 2:
        axis, step = 'v', -1
    else:
        axis, step = 'h', 1
    return TEMPLATE.replace('__BG__', str(bg)).replace('__AXIS__', axis).replace('__STEP__', str(step))
