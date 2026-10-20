def build_program(d4, palette):
    k = int(d4) % 8
    # Derived by pushing O = [g | fliplr(g)] through each D4 element and
    # re-expressing it in terms of the visible input s.
    table = {
        0: ('h', 'after'),
        1: ('v', 'after'),
        2: ('h', 'before'),
        3: ('v', 'before'),
        4: ('h', 'before'),
        5: ('v', 'before'),
        6: ('h', 'after'),
        7: ('v', 'after'),
    }
    axis, side = table[k]
    src = '''import numpy as np

AXIS = %r   # 'h': width doubles (mirror across a vertical seam); 'v': height doubles
SIDE = %r   # 'after': original first (left/top), mirror second; 'before': mirror first

def _build(g, axis, side):
    g = np.asarray(g)
    h, w = g.shape
    if axis == 'h':
        out = np.zeros((h, 2 * w), dtype=g.dtype)
        mirror = g[:, ::-1]
        if side == 'after':
            out[:, :w] = g
            out[:, w:] = mirror
        else:
            out[:, :w] = mirror
            out[:, w:] = g
    else:
        out = np.zeros((2 * h, w), dtype=g.dtype)
        mirror = g[::-1, :]
        if side == 'after':
            out[:h, :] = g
            out[h:, :] = mirror
        else:
            out[:h, :] = mirror
            out[h:, :] = g
    return out

def _pairs(demonstrations):
    res = []
    for d in demonstrations or []:
        try:
            if isinstance(d, dict):
                res.append((np.asarray(d['input']), np.asarray(d['output'])))
            else:
                res.append((np.asarray(d[0]), np.asarray(d[1])))
        except Exception:
            pass
    return res

def _fits(pairs, axis, side):
    for a, b in pairs:
        try:
            o = _build(a, axis, side)
        except Exception:
            return False
        if o.shape != b.shape or not np.array_equal(o, b):
            return False
    return True

def solve(demonstrations, grid):
    g = np.asarray(grid)
    axis, side = AXIS, SIDE
    pairs = _pairs(demonstrations)
    if pairs and not _fits(pairs, axis, side):
        for ax in ('h', 'v'):
            for sd in ('after', 'before'):
                if _fits(pairs, ax, sd):
                    axis, side = ax, sd
                    break
            else:
                continue
            break
    return _build(g, axis, side).astype(int).tolist()
''' % (axis, side)
    return src
