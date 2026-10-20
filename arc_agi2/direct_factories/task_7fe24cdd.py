def build_program(d4, palette):
    # The original output is a pinwheel: the input sits unchanged in the top-left
    # quadrant, and the other three quadrants are its 90/180/270 degree clockwise
    # rotations about the centre of the 2s x 2s canvas. Any D4 transform maps the
    # set of rotations about the centre onto itself. So the transformed output is
    # still the 4-fold rotation orbit of an untransformed copy of the visible input.
    # Only the quadrant holding that copy changes: it is the image of the top-left
    # corner under the D4 map.
    corners = [(0, 0), (0, 1), (1, 1), (1, 0)]  # TL, TR, BR, BL in clockwise order
    idx = 1 if d4 >= 4 else 0                   # reversing each row sends TL to TR
    idx = (idx + (d4 % 4)) % 4                  # each clockwise turn advances one corner
    qr, qc = corners[idx]
    lines = [
        'def solve(demonstrations, grid):',
        '    g = [list(row) for row in grid]',
        '    s = len(g)',
        '    w = len(g[0]) if s else 0',
        '    n = 2 * max(s, w)',
        '    out = [[0] * n for _ in range(n)]',
        '    off_r = %d * s' % qr,
        '    off_c = %d * w' % qc,
        '    for r in range(s):',
        '        for c in range(w):',
        '            v = g[r][c]',
        '            R = r + off_r',
        '            C = c + off_c',
        '            for _ in range(4):',
        '                if 0 <= R < n and 0 <= C < n:',
        '                    out[R][C] = v',
        '                R, C = C, n - 1 - R',
        '    return out',
    ]
    return '\n'.join(lines) + '\n'
