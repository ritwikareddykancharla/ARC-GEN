def build_program(d4, palette):
    k = int(d4) % 8
    # Native mechanism: a 1xN row with the seed at the centre c. The output is NxN.
    # The depth t is the distance from the input edge; s is the lateral index along that edge.
    # Red cells: t == |s-c|. Blue cells: t > |s-c| and (t - x_native + c) % 4 == 0.
    # x_native is s when the lateral axis keeps its direction, and 2c - s when it is reversed.
    # That gives the blue test (t + SIGN*(s-c)) % 4 == 0, with SIGN=-1 (kept) or +1 (reversed).
    edges = ['top', 'right', 'bottom', 'left', 'top', 'right', 'bottom', 'left']
    signs = [-1, -1, 1, 1, 1, 1, -1, -1]
    edge = edges[k]
    sign = signs[k]
    bg = int(palette[0])
    blue = int(palette[1])
    red = int(palette[2])
    template = '''from collections import Counter

EDGE = __EDGE__
SIGN = __SIGN__
BG_DEFAULT = __BG__
BLUE = __BLUE__
RED_DEFAULT = __RED__


def solve(demonstrations, grid):
    rows = [list(r) for r in grid]
    H = len(rows)
    W = len(rows[0]) if H else 0
    if H == 1:
        line = list(rows[0])
    elif W == 1:
        line = [r[0] for r in rows]
    else:
        if EDGE == 'top':
            line = list(rows[0])
        elif EDGE == 'bottom':
            line = list(rows[-1])
        elif EDGE == 'left':
            line = [r[0] for r in rows]
        else:
            line = [r[-1] for r in rows]
    N = len(line)
    cnt = Counter(line)
    if BG_DEFAULT in cnt:
        bg = BG_DEFAULT
    else:
        bg = cnt.most_common(1)[0][0]
    seeds = [i for i, v in enumerate(line) if v != bg]
    if seeds:
        c = seeds[0]
        red = line[c]
    else:
        c = N // 2
        red = RED_DEFAULT
    out = [[bg] * N for _ in range(N)]
    for Y in range(N):
        for X in range(N):
            if EDGE == 'top':
                t, s = Y, X
            elif EDGE == 'bottom':
                t, s = N - 1 - Y, X
            elif EDGE == 'left':
                t, s = X, Y
            else:
                t, s = N - 1 - X, Y
            d = abs(s - c)
            if t == d:
                out[Y][X] = red
            elif t > d and (t + SIGN * (s - c)) % 4 == 0:
                out[Y][X] = BLUE
    for i in range(N):
        if EDGE == 'top':
            out[0][i] = line[i]
        elif EDGE == 'bottom':
            out[N - 1][i] = line[i]
        elif EDGE == 'left':
            out[i][0] = line[i]
        else:
            out[i][N - 1] = line[i]
    return out
'''
    prog = template.replace('__EDGE__', repr(edge))
    prog = prog.replace('__SIGN__', repr(sign))
    prog = prog.replace('__BG__', repr(bg))
    prog = prog.replace('__BLUE__', repr(blue))
    prog = prog.replace('__RED__', repr(red))
    return prog
