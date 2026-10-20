def build_program(d4, palette):
    # The visible input sits unchanged in one corner quadrant of the doubled canvas.
    # Natively that corner is bottom-right. It is mapped through the D4 transform:
    # first reverse each row if d4 >= 4, then rotate clockwise d4 % 4 times.
    cw = {'BR': 'BL', 'BL': 'TL', 'TL': 'TR', 'TR': 'BR'}
    corner = 'BR'
    if d4 >= 4:
        corner = 'BL'
    for _ in range(d4 % 4):
        corner = cw[corner]
    vq = 0 if corner[0] == 'T' else 1
    hq = 0 if corner[1] == 'L' else 1
    lines = [
        'import numpy as np',
        '',
        'VQ = %d  # quadrant row (0 = top, 1 = bottom) holding the unchanged input' % vq,
        'HQ = %d  # quadrant column (0 = left, 1 = right) holding the unchanged input' % hq,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    h, w = g.shape',
        '    out = np.zeros((2 * h, 2 * w), dtype=int)',
        '    for i in range(2):',
        '        for j in range(2):',
        '            block = g',
        '            if i != VQ:',
        '                block = block[::-1, :]',
        '            if j != HQ:',
        '                block = block[:, ::-1]',
        '            out[i * h:(i + 1) * h, j * w:(j + 1) * w] = block',
        '    return out.tolist()',
        ''
    ]
    return '\n'.join(lines)
