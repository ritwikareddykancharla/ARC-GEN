def build_program(d4, palette):
    k = int(d4) % 8
    def vis(r, c, H=10, W=10):
        if k >= 4:
            c = W - 1 - c
        for _ in range(k % 4):
            r, c = c, H - 1 - r
            H, W = W, H
        return r, c
    br, bc = vis(9, 0)
    gr, gc = vis(8, 0)
    orr, occ = vis(9, 1)
    dr, dc = gr - br, gc - bc
    er, ec = orr - br, occ - bc
    base_r_high = (br == 9)
    base_c_high = (bc == 9)
    colours = [int(palette[c]) for c in (1, 2, 3, 4)]
    bg = int(palette[0])
    lines = [
        'import numpy as np',
        'BG = ' + repr(bg),
        'COLOURS = ' + repr(colours),
        'DR, DC = ' + repr(dr) + ', ' + repr(dc),
        'ER, EC = ' + repr(er) + ', ' + repr(ec),
        'BASE_R_HIGH = ' + repr(base_r_high),
        'BASE_C_HIGH = ' + repr(base_c_high),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    h, w = g.shape',
        '    out = np.full((h, w), BG, dtype=int)',
        '    br = h - 1 if BASE_R_HIGH else 0',
        '    bc = w - 1 if BASE_C_HIGH else 0',
        '    glen = h if DR != 0 else w',
        '    olen = w if EC != 0 else h',
        '    for i, col in enumerate(COLOURS):',
        '        if i >= olen:',
        '            break',
        '        n = min(int((g == col).sum()), glen)',
        '        for j in range(n):',
        '            out[br + i * ER + j * DR, bc + i * EC + j * DC] = col',
        '    return out.tolist()',
        ''
    ]
    return '\n'.join(lines)
