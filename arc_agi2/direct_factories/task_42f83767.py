def build_program(d4, palette):
    # Where the canonical top edge (legend + stencil strip) lands, and whether
    # the canonical left->right legend order runs against the visible axis.
    table = {
        0: ('top', False),
        1: ('right', False),
        2: ('bottom', True),
        3: ('left', True),
        4: ('top', True),
        5: ('right', True),
        6: ('bottom', False),
        7: ('left', False),
    }
    edge, rev = table[int(d4) % 8]
    bg = int(palette[0])
    grey = int(palette[5])
    n_expr = 'W' if edge in ('top', 'bottom') else 'H'
    if rev:
        q = '(N - 1 - pos)'
        q0 = '(N - p1)'
        q1 = '(N - p0)'
    else:
        q = 'pos'
        q0 = 'p0'
        q1 = 'p1'
    if edge == 'top':
        at = 'g[depth, %s]' % q
        blk = 'g[d0:d1, %s:%s]' % (q0, q1)
        dep = 'rr'
    elif edge == 'bottom':
        at = 'g[H - 1 - depth, %s]' % q
        blk = 'g[H - d1:H - d0, %s:%s]' % (q0, q1)
        dep = 'H - 1 - rr'
    elif edge == 'left':
        at = 'g[%s, depth]' % q
        blk = 'g[%s:%s, d0:d1]' % (q0, q1)
        dep = 'cc'
    else:
        at = 'g[%s, W - 1 - depth]' % q
        blk = 'g[%s:%s, W - d1:W - d0]' % (q0, q1)
        dep = 'W - 1 - cc'
    template = '''import numpy as np

BG = __BG__
GREY = __GREY__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    # N = length of the legend edge (__EDGE__ side of the visible grid)
    N = __N__

    def at(depth, pos):
        # depth: distance from the legend edge; pos: index in legend order
        return int(__AT__)

    def strip_block(d0, d1, p0, p1):
        return __BLK__

    # Legend swatches: 2-wide squares every 3 cells along the legend edge.
    swatches = []
    while 3 * len(swatches) + 1 < N:
        v = at(0, 3 * len(swatches))
        if v == BG or v == GREY or v in swatches:
            break
        swatches.append(v)
    k = len(swatches)
    if k == 0:
        return g.tolist()
    # Edge length N = (3 + L + 1) * k - 1  ->  stencil side L
    L = (N + 1) // k - 4
    if L < 1:
        return g.tolist()
    start = 3 * k
    stencils = []
    for i in range(k):
        p0 = start + (L + 1) * i
        b = strip_block(0, L, p0, p0 + L)
        stencils.append(b == GREY)

    # Mosaic: bounding box of non-background cells beyond the stencil strip.
    rr, cc = np.indices(g.shape)
    depth = __DEP__
    mask = (g != BG) & (depth >= L)
    pts = np.argwhere(mask)
    if len(pts) == 0:
        return g.tolist()
    y0, x0 = pts.min(0)
    y1, x1 = pts.max(0)
    mos = g[y0:y1 + 1, x0:x1 + 1]
    mh, mw = mos.shape
    sh, sw = stencils[0].shape
    out = np.full((mh * sh, mw * sw), BG, dtype=int)
    for r in range(mh):
        for c in range(mw):
            col = int(mos[r, c])
            if col not in swatches:
                continue
            st = stencils[swatches.index(col)]
            if st.shape != (sh, sw):
                continue
            sub = out[r * sh:(r + 1) * sh, c * sw:(c + 1) * sw]
            sub[st] = col
    return out.tolist()
'''
    prog = template.replace('__BG__', str(bg))
    prog = prog.replace('__GREY__', str(grey))
    prog = prog.replace('__EDGE__', edge)
    prog = prog.replace('__N__', n_expr)
    prog = prog.replace('__AT__', at)
    prog = prog.replace('__BLK__', blk)
    prog = prog.replace('__DEP__', dep)
    return prog
