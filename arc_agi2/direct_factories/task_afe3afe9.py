TEMPLATE = '''import numpy as np

BG = __BG__
LINE = __LINE__
EIGHT = __EIGHT__
ORDER = ("eight", "cw", "ccw")


def _line_side(g):
    H, W = g.shape
    edges = [("top", g[0, :]), ("bottom", g[H - 1, :]), ("left", g[:, 0]), ("right", g[:, W - 1])]
    sides=[name for name,vec in edges if np.all(vec==LINE)]
    if len(sides)!=1:raise ValueError('Expected one marked edge')
    return sides[0]


def _centers(g):
    H,W=g.shape
    colour=g[:-2,:-2]
    matches=(g[1:-1,1:-1]==BG)&(colour!=BG)&(colour!=LINE)
    for dy,dx in ((0,1),(0,2),(1,0),(1,2),(2,0),(2,1),(2,2)):
        matches &= g[dy:dy+H-2,dx:dx+W-2]==colour
    ys,xs=np.where(matches)
    return [(int(y+1),int(x+1),int(colour[y,x])) for y,x in zip(ys,xs)]


def _lattice(g):
    H, W = g.shape
    cs = _centers(g)
    if not cs:raise ValueError('No hollow square objects')
    oy = cs[0][0] % 4
    ox = cs[0][1] % 4
    if any(y%4!=oy or x%4!=ox for y,x,c in cs):raise ValueError('Inconsistent lattice')
    ny = max(1, (H - 2 - oy) // 4 + 1)
    nx = max(1, (W - 2 - ox) // 4 + 1)
    lat = np.full((ny, nx), BG, dtype=int)
    for y, x, c in cs:
        i = (y - oy) // 4
        j = (x - ox) // 4
        if 0 <= i < ny and 0 <= j < nx:
            lat[i, j] = c
    return lat


def _pack_rows(red, toward_end):
    out = np.full(red.shape, BG, dtype=int)
    w = red.shape[1]
    for r in range(red.shape[0]):
        items = [int(v) for v in red[r] if v != BG]
        k = len(items)
        if k == 0:
            continue
        if toward_end:
            out[r, w - k:] = items
        else:
            out[r, :k] = items
    return out


def _candidates(g):
    side = _line_side(g)
    lat = _lattice(g)
    ny, nx = lat.shape
    if (ny,nx)!=(7,7):raise ValueError('Expected seven by seven lattice')
    horizontal = side in ("top", "bottom")
    if not np.all((lat[:,nx//2] if horizontal else lat[ny//2,:])==BG):raise ValueError('Nonempty separator lane')
    if horizontal:
        mid = nx // 2
        red = np.delete(lat, mid, axis=1)
        lo = int(np.sum(lat[:, :mid] == EIGHT))
        hi = int(np.sum(lat[:, mid + 1:] == EIGHT))
        cw_end = side == "top"

        def pack(te):
            return _pack_rows(red, te)
    else:
        mid = ny // 2
        red = np.delete(lat, mid, axis=0)
        lo = int(np.sum(lat[:mid, :] == EIGHT))
        hi = int(np.sum(lat[mid + 1:, :] == EIGHT))
        cw_end = side == "right"

        def pack(te):
            return _pack_rows(red.T, te).T
    if bool(hi)==bool(lo):raise ValueError('Landmark must occupy one half only')
    out = {"eight":pack(hi>0)}
    if side is not None:
        out["cw"] = pack(cw_end)
        out["ccw"] = pack(not cw_end)
    return out


def solve(demonstrations, grid):
    if not demonstrations:raise ValueError('Demonstrations required')
    alive=set(ORDER)
    for p in demonstrations:
        c=_candidates(np.array(p['input'],dtype=int))
        b=np.array(p['output'],dtype=int)
        alive &= {h for h,v in c.items() if v.shape==b.shape and np.array_equal(v,b)}
    if not alive:raise ValueError('No demonstrated packing rule')
    q=_candidates(np.array(grid,dtype=int))
    if not alive.issubset(q):raise ValueError('Unresolved packing landmark')
    predictions=[q[h] for h in sorted(alive)]
    if any(not np.array_equal(p,predictions[0]) for p in predictions[1:]):raise ValueError('Unresolved packing direction')
    return predictions[0].tolist()
'''


def build_program(d4, palette):
    pal = [int(v) for v in palette]
    return (TEMPLATE.replace('__BG__', str(pal[0]))
            .replace('__LINE__', str(pal[1]))
            .replace('__EIGHT__', str(pal[8])))
