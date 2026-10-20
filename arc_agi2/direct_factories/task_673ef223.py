def build_program(d4, palette):
    horiz = (int(d4) % 4) in (1, 3)
    red = int(palette[2])
    cyan = int(palette[8])
    yellow = int(palette[4])
    src = '''import numpy as np

RED = __RED__
CYAN = __CYAN__
YELLOW = __YELLOW__
HORIZ = __HORIZ__


def _pick(bars, seed_pos):
    keys = sorted(bars.keys())
    best = None
    best_score = -1
    for k in keys:
        lo, hi = min(bars[k]), max(bars[k])
        score = sum(1 for p in seed_pos if lo <= p <= hi)
        if score > best_score:
            best_score = score
            best = k
    return best


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    ry, rx = np.nonzero(g == RED)
    sy, sx = np.nonzero(g == CYAN)
    seeds = [(int(a), int(b)) for a, b in zip(sy, sx)]
    if not HORIZ:
        # bars are vertical segments in an edge column; seeds share rows with bar A
        bars = {}
        for y, x in zip(ry, rx):
            bars.setdefault(int(x), []).append(int(y))
        if len(bars) < 2 or not seeds:
            return out.tolist()
        seed_rows = sorted(set(y for y, x in seeds))
        ax = _pick(bars, seed_rows)
        others = [k for k in bars if k != ax]
        bx = max(others, key=lambda k: abs(k - ax))
        topA = min(bars[ax])
        topB = min(bars[bx])
        for y, x in seeds:
            step = 1 if x > ax else -1
            for c in range(ax + step, x, step):
                out[y, c] = CYAN
            out[y, x] = YELLOW
        for y in seed_rows:
            rr = y - topA + topB
            if 0 <= rr < H:
                cs = range(0, bx) if bx > W // 2 else range(bx + 1, W)
                for c in cs:
                    out[rr, c] = CYAN
    else:
        # bars are horizontal segments in an edge row; seeds share columns with bar A
        bars = {}
        for y, x in zip(ry, rx):
            bars.setdefault(int(y), []).append(int(x))
        if len(bars) < 2 or not seeds:
            return out.tolist()
        seed_cols = sorted(set(x for y, x in seeds))
        ay = _pick(bars, seed_cols)
        others = [k for k in bars if k != ay]
        by = max(others, key=lambda k: abs(k - ay))
        leftA = min(bars[ay])
        leftB = min(bars[by])
        for y, x in seeds:
            step = 1 if y > ay else -1
            for r in range(ay + step, y, step):
                out[r, x] = CYAN
            out[y, x] = YELLOW
        for x in seed_cols:
            cc = x - leftA + leftB
            if 0 <= cc < W:
                rs = range(0, by) if by > H // 2 else range(by + 1, H)
                for r in rs:
                    out[r, cc] = CYAN
    return out.tolist()
'''
    src = src.replace('__RED__', str(red))
    src = src.replace('__CYAN__', str(cyan))
    src = src.replace('__YELLOW__', str(yellow))
    src = src.replace('__HORIZ__', 'True' if horiz else 'False')
    return src
