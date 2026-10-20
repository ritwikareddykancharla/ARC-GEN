def build_program(d4, palette):
    d4 = int(d4)

    def mp(r, c, H, W):
        if d4 >= 4:
            c = W - 1 - c
        for _ in range(d4 % 4):
            r, c = c, H - 1 - r
            H, W = W, H
        return r, c, H, W

    # Input strip geometry (canonical 2 x 12)
    r0, c0, _, _ = mp(0, 0, 2, 12)
    r1, c1, _, _ = mp(0, 1, 2, 12)
    r2, c2, _, _ = mp(1, 0, 2, 12)
    along = (r1 - r0, c1 - c0)
    across = (r2 - r0, c2 - c0)
    axis = 1 if along[0] == 0 else 0
    rev = (along[0] + along[1]) < 0
    top = 0 if (across[0] + across[1]) > 0 else -1

    # Output geometry (canonical 8 x 7, start at (0,3))
    sr, sc, OH, OW = mp(0, 3, 8, 7)
    fr, fc, _, _ = mp(1, 3, 8, 7)
    lr, lc, _, _ = mp(0, 4, 8, 7)
    FR, FC = fr - sr, fc - sc
    LR, LC = lr - sr, lc - sc

    bg = int(palette[0])
    fg = int(palette[2])
    st = int(palette[3])

    lines = []
    lines.append('import numpy as np')
    lines.append('BG = %d' % bg)
    lines.append('FG = %d' % fg)
    lines.append('ST = %d' % st)
    lines.append('AXIS = %d' % axis)
    lines.append('REV = %r' % bool(rev))
    lines.append('TOP = %d' % top)
    lines.append('OH = %d' % OH)
    lines.append('OW = %d' % OW)
    lines.append('SR = %d' % sr)
    lines.append('SC = %d' % sc)
    lines.append('FR = %d' % FR)
    lines.append('FC = %d' % FC)
    lines.append('LR = %d' % LR)
    lines.append('LC = %d' % LC)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid)')
    lines.append('    if AXIS == 1:')
    lines.append('        strips = [g[:, i] for i in range(g.shape[1])]')
    lines.append('    else:')
    lines.append('        strips = [g[i, :] for i in range(g.shape[0])]')
    lines.append('    if REV:')
    lines.append('        strips = strips[::-1]')
    lines.append('    pieces = []')
    lines.append('    for i, ln in enumerate(strips):')
    lines.append('        if bool((ln != BG).any()):')
    lines.append('            if pieces and pieces[-1][-1] == i - 1:')
    lines.append('                pieces[-1].append(i)')
    lines.append('            else:')
    lines.append('                pieces.append([i])')
    lines.append('    out = np.full((OH, OW), BG, dtype=int)')
    lines.append('    out[SR, SC] = ST')
    lines.append('    def put(y, dx):')
    lines.append('        r = SR + y * FR + dx * LR')
    lines.append('        c = SC + y * FC + dx * LC')
    lines.append('        if 0 <= r < OH and 0 <= c < OW:')
    lines.append('            out[r, c] = FG')
    lines.append('    y = 1')
    lines.append('    x = 0')
    lines.append('    for p in pieces:')
    lines.append('        if len(p) == 1:')
    lines.append('            for _ in range(2):')
    lines.append('                put(y, x)')
    lines.append('                y += 1')
    lines.append('        else:')
    lines.append('            first = strips[p[0]]')
    lines.append('            if first[TOP] != BG:')
    lines.append('                put(y, x)')
    lines.append('                put(y, x + 1)')
    lines.append('                x += 1')
    lines.append('            else:')
    lines.append('                put(y, x - 1)')
    lines.append('                put(y, x)')
    lines.append('                x -= 1')
    lines.append('            y += 1')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
