def build_program(d4, palette):
    """Emit a visible-coordinate solver for d5c634a2 under (d4, palette).

    Canonical rule: the input holds T-tetrominoes (a 3-cell bar plus a
    1-cell stem at the bar centre). Ts whose stem is above the bar are
    tallied in colour 3 at (0,0),(2,0),(0,2),(2,2) of a 3x6 canvas, in
    that order. Ts whose stem is below the bar are tallied in colour 1 at
    the same corners shifted three columns to the right.

    The factory maps the canonical stem direction and every tally cell
    forward through the same D4 used by arc_agi2.augmentation.transformed:
    columns are reversed when d4 >= 4, then the grid is rotated clockwise
    (d4 % 4) times. The emitted solver then works on visible coordinates
    only. It has no inverse wrapper and reads no demonstration labels.
    """
    flip = d4 >= 4
    turns = d4 % 4

    def fwd_cell(r, c, h, w):
        if flip:
            c = w - 1 - c
        for _ in range(turns):
            r, c, h, w = c, h - 1 - r, w, h
        return r, c

    def fwd_vec(dr, dc):
        if flip:
            dc = -dc
        for _ in range(turns):
            dr, dc = dc, -dr
        return dr, dc

    out_h, out_w = (3, 6) if turns % 2 == 0 else (6, 3)
    corners = [(0, 0), (2, 0), (0, 2), (2, 2)]
    up_slots = [fwd_cell(r, c, 3, 6) for r, c in corners]
    down_slots = [fwd_cell(r, c + 3, 3, 6) for r, c in corners]
    up_vec = fwd_vec(-1, 0)        # bar centre -> stem, for an 'up' T
    bar_vec = fwd_vec(0, 1)        # along the bar

    src = [
        'import numpy as np',
        '',
        'BG = %d' % int(palette[0]),
        'FG = %d' % int(palette[2]),
        'UP_COLOUR = %d' % int(palette[3]),
        'DOWN_COLOUR = %d' % int(palette[1]),
        'OUT_SHAPE = (%d, %d)' % (out_h, out_w),
        'UP_SLOTS = %r' % (up_slots,),
        'DOWN_SLOTS = %r' % (down_slots,),
        'UP_VEC = %r' % (up_vec,),
        'BAR_VEC = %r' % (bar_vec,),
        '',
        '',
        'def solve(demonstrations, grid):',
        '    g = np.asarray(grid, dtype=int)',
        '    h, w = g.shape',
        '',
        '    def fg(r, c):',
        '        return 0 <= r < h and 0 <= c < w and g[r, c] == FG',
        '',
        '    br, bc = BAR_VEC',
        '    tallies = {1: 0, -1: 0}',
        '    # Count Ts by their stems. A stem cell s with direction d is a',
        '    # foreground cell where:',
        '    #   - the bar centre s-d is foreground,',
        '    #   - both bar neighbours of that centre are foreground,',
        '    #   - s has no foreground neighbour along the bar axis,',
        '    #   - s+d is not foreground.',
        '    # This counts every T exactly once, including two bars that touch',
        '    # or share a cell along one border row.',
        '    for r in range(h):',
        '        for c in range(w):',
        '            if not fg(r, c):',
        '                continue',
        '            for sign in (1, -1):',
        '                dr, dc = UP_VEC[0] * sign, UP_VEC[1] * sign',
        '                cr, cc = r - dr, c - dc',
        '                if not (fg(cr, cc) and fg(cr + br, cc + bc) and fg(cr - br, cc - bc)):',
        '                    continue',
        '                if fg(r + br, c + bc) or fg(r - br, c - bc) or fg(r + dr, c + dc):',
        '                    continue',
        '                tallies[sign] += 1',
        '    out = np.full(OUT_SHAPE, BG, dtype=int)',
        '    for slots, colour, n in ((UP_SLOTS, UP_COLOUR, tallies[1]), (DOWN_SLOTS, DOWN_COLOUR, tallies[-1])):',
        '        for y, x in slots[:min(n, len(slots))]:',
        '            out[y, x] = colour',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(src)
