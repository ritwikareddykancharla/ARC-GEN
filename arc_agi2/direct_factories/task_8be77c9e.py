def build_program(d4, palette):
    k = int(d4) % 4
    if k == 0:
        seam = 'below'
        body = '    out = np.concatenate([g, g[::-1, :]], axis=0)\n'
    elif k == 1:
        seam = 'left'
        body = '    out = np.concatenate([g[:, ::-1], g], axis=1)\n'
    elif k == 2:
        seam = 'above'
        body = '    out = np.concatenate([g[::-1, :], g], axis=0)\n'
    else:
        seam = 'right'
        body = '    out = np.concatenate([g, g[:, ::-1]], axis=1)\n'
    src = (
        'import numpy as np\n'
        '\n'
        '# Mirror the input across a seam on its ' + seam + ' side and attach the\n'
        '# reflected copy there. The output keeps the input untouched and adds its\n'
        '# mirror image directly across the seam.\n'
        'def solve(demonstrations, grid):\n'
        '    g = np.array(grid, dtype=int)\n'
        + body +
        '    return out.astype(int).tolist()\n'
    )
    return src
