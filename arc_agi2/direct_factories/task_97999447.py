def build_program(d4, palette):
    # The original rays run toward +x (to the right). Map that direction into visible coordinates.
    dr, dc = 0, 1
    if d4 >= 4:
        # Reversing each row flips the horizontal direction.
        dc = -dc
    for _ in range(d4 % 4):
        # A clockwise rotation sends (r, c) to (c, H-1-r), so a direction (dr, dc) becomes (dc, -dr).
        dr, dc = dc, -dr
    bg = int(palette[0])
    gray = int(palette[5])
    lines = [
        'import numpy as np',
        '',
        'BG = ' + repr(bg),
        'GRAY = ' + repr(gray),
        'DR = ' + repr(int(dr)),
        'DC = ' + repr(int(dc)),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    out = g.copy()',
        '    h, w = g.shape',
        '    seeds = []',
        '    for r in range(h):',
        '        for c in range(w):',
        '            v = int(g[r, c])',
        '            if v != BG:',
        '                seeds.append((r, c, v))',
        '    for r, c, v in seeds:',
        '        k = 0',
        '        rr, cc = r, c',
        '        while 0 <= rr < h and 0 <= cc < w:',
        '            out[rr, cc] = v if k % 2 == 0 else GRAY',
        '            rr += DR',
        '            cc += DC',
        '            k += 1',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
