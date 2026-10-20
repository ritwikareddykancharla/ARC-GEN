def build_program(d4, palette):
    c0 = int(palette[0])
    c1 = int(palette[1])
    c8 = int(palette[8])
    c9 = int(palette[9])
    src = '''
C0 = %d
C1 = %d
C8 = %d
C9 = %d

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0])
    pos = None
    for y in range(H):
        for x in range(W):
            if g[y][x] == C8:
                pos = (y, x)
                break
        if pos is not None:
            break
    out = [[C0] * W for _ in range(H)]
    if pos is None:
        return out
    y8, x8 = pos
    lines = []
    if x8 == 0:
        for r in range(H):
            lines.append([(r, c) for c in range(W)])
    elif x8 == W - 1:
        for r in range(H):
            lines.append([(r, W - 1 - c) for c in range(W)])
    elif y8 == 0:
        for c in range(W):
            lines.append([(r, c) for r in range(H)])
    else:
        for c in range(W):
            lines.append([(H - 1 - r, c) for r in range(H)])
    for line in lines:
        vals = [g[a][b] for (a, b) in line]
        cnt = sum(1 for v in vals if v == C1)
        if line[0] == (y8, x8):
            a, b = line[0]
            out[a][b] = C8
            for i in range(1, min(1 + cnt, len(line))):
                a, b = line[i]
                out[a][b] = C1
            ones = [i for i, v in enumerate(vals) if v == C1]
            if ones:
                last = ones[-1]
                for i in range(1 + cnt, last + 1):
                    a, b = line[i]
                    out[a][b] = C9
        else:
            for i in range(min(cnt, len(line))):
                a, b = line[i]
                out[a][b] = C1
    return out
''' % (c0, c1, c8, c9)
    return src
