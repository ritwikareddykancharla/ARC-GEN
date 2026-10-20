def build_program(d4, palette):
    k = int(d4) % 8
    # For each D4 index: (swap, revr, revc) such that original (r, c) is read from visible (i, j):
    # r = (j if swap else i), reversed if revr; c = (i if swap else j), reversed if revc.
    table = {
        0: (False, False, False),
        1: (True, True, False),
        2: (False, True, True),
        3: (True, False, True),
        4: (False, False, True),
        5: (True, True, True),
        6: (False, True, False),
        7: (True, False, False),
    }
    swap, revr, revc = table[k]
    # Anchor flags for the visible row axis and visible column axis.
    fr = int(revc if swap else revr)
    fc = int(revr if swap else revc)
    bg = int(palette[0])
    tl_q = (fr, fc)
    motif_q = (1 - fr, 1 - fc)
    if swap:
        fill_q = (fr, 1 - fc)
        tr_q = (1 - fr, fc)
        rows_q = tr_q
        cols_q = tl_q
    else:
        fill_q = (1 - fr, fc)
        tr_q = (fr, 1 - fc)
        rows_q = tl_q
        cols_q = tr_q
    if fr:
        mrow = 'mh - 1 - ((rv - 1 - ii) % mh)'
        frow = 'fh - 1 - ((rv - 1 - ii) * fh) // rv'
    else:
        mrow = 'ii % mh'
        frow = '(ii * fh) // rv'
    if fc:
        mcol = 'mw - 1 - ((cv - 1 - jj) % mw)'
        fcol = 'fw - 1 - ((cv - 1 - jj) * fw) // cv'
    else:
        mcol = 'jj % mw'
        fcol = '(jj * fw) // cv'
    lines = [
        'import numpy as np',
        '',
        'BG = %d' % bg,
        'ROWS_Q = (%d, %d)' % rows_q,
        'COLS_Q = (%d, %d)' % cols_q,
        'FILL_Q = (%d, %d)' % fill_q,
        'MOTIF_Q = (%d, %d)' % motif_q,
        '',
        'def _quad(g, pos):',
        '    R, C = g.shape',
        '    hr = R // 2',
        '    hc = C // 2',
        '    rs = slice(0, hr) if pos[0] == 0 else slice(hr, R)',
        '    cs = slice(0, hc) if pos[1] == 0 else slice(hc, C)',
        '    return g[rs, cs]',
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    rq = _quad(g, ROWS_Q)',
        '    cq = _quad(g, COLS_Q)',
        '    fq = _quad(g, FILL_Q)',
        '    mq = _quad(g, MOTIF_Q)',
        '    rv = int((rq != BG).sum())',
        '    cv = int((cq != BG).sum())',
        '    if rv < 1 or cv < 1 or mq.size == 0 or fq.size == 0:',
        '        return [[BG]]',
        '    mh, mw = mq.shape',
        '    fh, fw = fq.shape',
        '    ii = np.arange(rv)',
        '    jj = np.arange(cv)',
        '    mrow = ' + mrow,
        '    mcol = ' + mcol,
        '    frow = ' + frow,
        '    fcol = ' + fcol,
        '    out = mq[mrow[:, None], mcol[None, :]].copy()',
        '    fill = fq[frow[:, None], fcol[None, :]]',
        '    out = np.where(out == BG, fill, out)',
        '    return out.astype(int).tolist()',
        '',
    ]
    return '\n'.join(lines)
