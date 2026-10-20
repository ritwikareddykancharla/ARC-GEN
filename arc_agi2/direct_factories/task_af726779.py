def build_program(d4, palette):
    pal = [int(palette[i]) for i in range(10)]
    bg = pal[3]
    first = pal[6]
    second = pal[7]
    k = int(d4) % 4
    # Canonical growth goes +row. A row-reversal leaves this unchanged.
    # Each clockwise rotation maps the vector (dr, dc) to (dc, -dr):
    # k=0 down, k=1 left, k=2 up, k=3 right.
    if k == 0:
        axis, step = 0, 1
    elif k == 1:
        axis, step = 1, -1
    elif k == 2:
        axis, step = 0, -1
    else:
        axis, step = 1, 1
    template = '''
BG = @BG@
FIRST = @FIRST@
SECOND = @SECOND@
AXIS = @AXIS@
STEP = @STEP@


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    if H == 0 or W == 0:
        return out
    if AXIS == 0:
        n_lines = H
        length = W
    else:
        n_lines = W
        length = H

    def cell(p, q):
        if AXIS == 0:
            return g[p][q]
        return g[q][p]

    def put(p, q, v):
        if AXIS == 0:
            out[p][q] = v
        else:
            out[q][p] = v

    lines = [p for p in range(n_lines) if any(cell(p, q) != BG for q in range(length))]
    if not lines:
        return out
    p = lines[0] if STEP > 0 else lines[-1]
    prev = [cell(p, q) != BG for q in range(length)]
    k = 0
    while 0 <= p + 2 * STEP < n_lines:
        new = [False] * length
        for q in range(1, length - 1):
            if prev[q - 1] and prev[q + 1] and not prev[q]:
                new[q] = True
        if not any(new):
            break
        p += 2 * STEP
        colour = FIRST if k % 2 == 0 else SECOND
        for q in range(length):
            if new[q]:
                put(p, q, colour)
        prev = new
        k += 1
    return out
'''
    code = template.replace('@BG@', repr(bg)).replace('@FIRST@', repr(first)).replace('@SECOND@', repr(second)).replace('@AXIS@', repr(axis)).replace('@STEP@', repr(step))
    return code
