def build_program(d4, palette):
    k = int(d4) % 4
    bg = int(palette[7])
    blk = int(palette[5])
    red = int(palette[2])
    cyan = int(palette[8])
    if k == 0:
        place = ['    ty = int(by1)', '    tx = int(bx1) + 1 if x8 > x2 else int(bx0) - 1']
    elif k == 2:
        place = ['    ty = int(by0)', '    tx = int(bx1) + 1 if x8 > x2 else int(bx0) - 1']
    elif k == 1:
        place = ['    tx = int(bx0)', '    ty = int(by1) + 1 if y8 > y2 else int(by0) - 1']
    else:
        place = ['    tx = int(bx1)', '    ty = int(by1) + 1 if y8 > y2 else int(by0) - 1']
    lines = [
        'import numpy as np',
        '',
        'BG = ' + repr(bg),
        'BLOCK = ' + repr(blk),
        'RED = ' + repr(red),
        'CYAN = ' + repr(cyan),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    h, w = g.shape',
        '    out = g.copy()',
        '    rp = np.argwhere(g == RED)',
        '    cp = np.argwhere(g == CYAN)',
        '    bp = np.argwhere(g == BLOCK)',
        '    if len(rp) == 0 or len(cp) == 0 or len(bp) == 0:',
        '        return out.tolist()',
        '    y2, x2 = int(rp[0][0]), int(rp[0][1])',
        '    y8, x8 = int(cp[0][0]), int(cp[0][1])',
        '    by0, bx0 = bp.min(axis=0)',
        '    by1, bx1 = bp.max(axis=0)',
        '    out[y2, x2] = BG',
        '    out[y8, x8] = RED',
    ] + place + [
        '    if 0 <= ty < h and 0 <= tx < w:',
        '        out[ty, tx] = CYAN',
        '    return out.tolist()',
    ]
    return '\n'.join(lines) + '\n'
