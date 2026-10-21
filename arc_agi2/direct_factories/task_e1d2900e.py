_BODY = '''

def _g(a):
    return [[int(v) for v in row] for row in a]


def _pairs(demonstrations):
    out = []
    for d in (demonstrations or []):
        if isinstance(d, dict):
            out.append((_g(d['input']), _g(d['output'])))
        else:
            out.append((_g(d[0]), _g(d[1])))
    return out


def _blocks(g):
    h = len(g)
    w = len(g[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    out = []
    for y in range(h):
        for x in range(w):
            if g[y][x] == BLK and not seen[y][x]:
                seen[y][x] = True
                stack = [(y, x)]
                ys = []
                xs = []
                while stack:
                    cy, cx = stack.pop()
                    ys.append(cy)
                    xs.append(cx)
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == BLK:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                if len(ys) != 4 or max(ys)-min(ys) != 1 or max(xs)-min(xs) != 1:
                    raise ValueError("Red objects must be distinct 2x2 squares")
                out.append((min(ys), min(xs), max(ys), max(xs)))
    if not out:
        raise ValueError("No red square")
    return out


def _pixels(g):
    h = len(g)
    w = len(g[0]) if h else 0
    return [(y, x) for y in range(h) for x in range(w) if g[y][x] == PX]


def _dest(y, x, box, h, w):
    r0, c0, r1, c1 = box
    d = None
    if r0 <= y <= r1:
        if x < c0:
            d = (y, c0 - 1)
        elif x > c1:
            d = (y, c1 + 1)
    elif c0 <= x <= c1:
        if y < r0:
            d = (r0 - 1, x)
        elif y > r1:
            d = (r1 + 1, x)
    if d is None or not (0 <= d[0] < h and 0 <= d[1] < w):
        return None
    return d


def _apply(g, moves):
    out = [row[:] for row in g]
    for s, _ in moves:
        out[s[0]][s[1]] = BG
    for _, d in moves:
        out[d[0]][d[1]] = PX
    return out


def _cheb(y, x, box):
    r0, c0, r1, c1 = box
    dy = max(r0 - y, 0, y - r1)
    dx = max(c0 - x, 0, x - c1)
    return max(dy, dx)


# The 8 D4 images of a reading-order scan: primary axis, primary sign, secondary sign.
ORDERS = [(p, s1, s2) for p in (0, 1) for s1 in (1, -1) for s2 in (1, -1)]


def _okey(box, order):
    p, s1, s2 = order
    if p == 0:
        return (s1 * box[0], s2 * box[1])
    return (s1 * box[1], s2 * box[0])


def _cheb_rule(g, order):
    # Rival mechanism: the governing block is the Chebyshev-nearest block, with ties
    # broken by a scan order that must be learned from the demonstrations. The pixel
    # slides only if that block shares its row/column band. Otherwise it is blocked.
    h = len(g)
    w = len(g[0]) if h else 0
    blocks = sorted(_blocks(g), key=lambda b: _okey(b, order))
    moves = []
    if blocks:
        for y, x in _pixels(g):
            ds = [_cheb(y, x, b) for b in blocks]
            i = ds.index(min(ds))
            d = _dest(y, x, blocks[i], h, w)
            if d is not None and d != (y, x):
                moves.append(((y, x), d))
    return _apply(g, moves)


def solve(demonstrations, grid):
    demos = _pairs(demonstrations)
    if not demos:
        raise ValueError('Demonstrations required to establish tie convention')
    fits = [o for o in ORDERS if all(_cheb_rule(i, o) == out for i, out in demos)]
    if not fits:
        raise ValueError('No demonstrated Chebyshev tie convention')
    outs = [_cheb_rule(_g(grid), o) for o in fits]
    if not all(o == outs[0] for o in outs):
        raise ValueError('Demonstrations leave query tie convention ambiguous')
    return outs[0]
'''


def build_program(d4, palette):
    bg = int(palette[0])
    px = int(palette[1])
    blk = int(palette[2])
    header = 'BG = %d\nPX = %d\nBLK = %d\n' % (bg, px, blk)
    return header + _BODY
