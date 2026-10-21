"""Direct-coordinate factory for ARC task 1b8318e3 (pixels dock on 2x2 boxes).

build_program(d4, palette) returns a standalone program that works in the
visible coordinates. Only the colour roles come from the palette: background
is palette[0] and the box colour is palette[5]. Every geometric operation is
D4-equivariant, so d4 is not used to choose between explanations.
"""

TEMPLATE = r'''
BG = @BG@
BOX = @BOX@
REACH = 4
NODE_BUDGET = 200000


class Undetermined(Exception):
    """Raised when the visible evidence does not fix a unique answer."""


def _parse(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    boxes = []
    pixels = []
    for y in range(h):
        for x in range(w):
            v = grid[y][x]
            if v == BOX and (y, x) not in seen:
                comp, stack = [], [(y, x)]
                seen.add((y, x))
                while stack:
                    a, b = stack.pop()
                    comp.append((a, b))
                    for na, nb in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                        if 0 <= na < h and 0 <= nb < w and grid[na][nb] == BOX and (na, nb) not in seen:
                            seen.add((na, nb))
                            stack.append((na, nb))
                y0 = min(a for a, _ in comp)
                x0 = min(b for _, b in comp)
                if sorted(comp) != [(y0, x0), (y0, x0 + 1), (y0 + 1, x0), (y0 + 1, x0 + 1)]:
                    raise Undetermined('box component is not a 2x2 block')
                boxes.append((y0, x0))
            elif v != BG and v != BOX:
                pixels.append((y, x, v))
    return h, w, boxes, pixels


def _clamp(py, px, by, bx):
    r = by - 1 if py < by else (by + 2 if py > by + 1 else py)
    c = bx - 1 if px < bx else (bx + 2 if px > bx + 1 else px)
    return r, c


def _site_clamp(py, px, by, bx, taken):
    # Rule C: the pixel's position clamped onto the box's one-cell ring.
    s = _clamp(py, px, by, bx)
    return None if s in taken else s


def _site_diagonal(py, px, by, bx, taken):
    # Rule K: king-move approach. From a corner region with unequal row and
    # column gaps the pixel moves diagonally until it is level with the box,
    # landing on the side cell next to the ring corner. If that cell is taken
    # it settles on the ring corner itself.
    r, c = _clamp(py, px, by, bx)
    a, b = abs(py - r), abs(px - c)
    if a > 0 and b > 0 and a != b:
        if a > b:
            land = (r, bx if c < bx else bx + 1)
        else:
            land = (by if r < by else by + 1, c)
        if land not in taken:
            return land
    return None if (r, c) in taken else (r, c)


RULES = (('clamp', _site_clamp), ('diagonal', _site_diagonal))


def _reaches(edges, a, b):
    stack, seen = [a], {a}
    while stack:
        u = stack.pop()
        if u == b:
            return True
        for v in edges.get(u, ()):
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return False


def _outcomes(h, w, boxes, pixels, site_fn, label=None, stop_at=None):
    """Every output grid realisable by some hidden pixel order.

    A pixel proposes only when its cheapest free site over all boxes within
    REACH (Manhattan) is unique. A contested site goes to its cheapest
    proposer; equal-cost proposers are ordered by an invisible list index,
    so each one may win provided the implied precedence stays acyclic.
    Only complete matchings are kept (incomplete scenes are never drawn).
    With label given, branches contradicting the label are pruned.
    """
    n = len(pixels)
    results = []
    seen_out = set()
    budget = [NODE_BUDGET]

    def proposals(assign):
        taken = set(s for s in assign if s is not None)
        props = {}
        for i in range(n):
            if assign[i] is not None:
                continue
            py, px, _ = pixels[i]
            best, cands = None, []
            for by, bx in boxes:
                s = site_fn(py, px, by, bx, taken)
                if s is None:
                    continue
                d = abs(s[0] - py) + abs(s[1] - px)
                if d > REACH:
                    continue
                if best is None or d < best:
                    best, cands = d, [s]
                elif d == best:
                    cands.append(s)
            if len(cands) == 1:
                props.setdefault(cands[0], []).append((best, i))
        return props

    def finish(assign):
        out = [[BG] * w for _ in range(h)]
        for by, bx in boxes:
            for dy in (0, 1):
                for dx in (0, 1):
                    out[by + dy][bx + dx] = BOX
        for (y, x), (_, _, v) in zip(assign, pixels):
            if out[y][x] != BG:
                return None
            out[y][x] = v
        return out

    def ok(i, s):
        return label is None or label[s[0]][s[1]] == pixels[i][2]

    def run_round(assign, edges):
        budget[0] -= 1
        if budget[0] < 0:
            raise Undetermined('search budget exhausted')
        if stop_at is not None and len(results) >= stop_at:
            return
        props = proposals(assign)
        if not props:
            if all(s is not None for s in assign):
                out = finish(assign)
                if out is not None and (label is None or out == label):
                    key = tuple(map(tuple, out))
                    if key not in seen_out:
                        seen_out.add(key)
                        results.append(out)
            return
        contests = []
        new_assign = list(assign)
        for s, lst in props.items():
            d0 = min(d for d, _ in lst)
            tied = [i for d, i in lst if d == d0]
            if len(tied) == 1:
                if not ok(tied[0], s):
                    return
                new_assign[tied[0]] = s
            else:
                contests.append((s, tied))
        resolve(new_assign, edges, contests, 0)

    def resolve(assign, edges, contests, k):
        if k == len(contests):
            run_round(assign, edges)
            return
        s, tied = contests[k]
        for win in tied:
            if not ok(win, s):
                continue
            others = [j for j in tied if j != win]
            if any(_reaches(edges, j, win) for j in others):
                continue
            e2 = {u: set(vs) for u, vs in edges.items()}
            e2.setdefault(win, set()).update(others)
            a2 = list(assign)
            a2[win] = s
            resolve(a2, e2, contests, k + 1)
            if stop_at is not None and len(results) >= stop_at:
                return

    run_round([None] * n, {})
    return results


def _consistent(site_fn, pair):
    gi, go = pair['input'], pair['output']
    h, w, boxes, pixels = _parse(gi)
    if len(go) != h or any(len(row) != w for row in go):
        return False
    return bool(_outcomes(h, w, boxes, pixels, site_fn, label=go, stop_at=1))


def solve(demonstrations, grid):
    grid = [list(map(int, row)) for row in grid]
    demos = [{'input': [list(map(int, r)) for r in p['input']],
              'output': [list(map(int, r)) for r in p['output']]} for p in demonstrations]
    survivors = [(name, fn) for name, fn in RULES
                 if all(_consistent(fn, p) for p in demos)]
    if not survivors:
        raise Undetermined('no docking rule explains every demonstration')
    h, w, boxes, pixels = _parse(grid)
    answers = {}
    for name, fn in survivors:
        for out in _outcomes(h, w, boxes, pixels, fn, stop_at=2):
            answers[tuple(map(tuple, out))] = out
            if len(answers) > 1:
                raise Undetermined('surviving explanations disagree on the query')
    if len(answers) != 1:
        raise Undetermined('no complete docking of the query')
    return next(iter(answers.values()))
'''


def build_program(d4, palette):
    del d4  # every operation is D4-equivariant; nothing to specialise
    bg, box = int(palette[0]), int(palette[5])
    return TEMPLATE.replace('@BG@', str(bg)).replace('@BOX@', str(box)).lstrip()
