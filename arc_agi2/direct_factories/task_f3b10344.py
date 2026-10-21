"""Direct visible-coordinate factory for ARC-GEN f3b10344 (same-colour bridges).

v7 (second independent review).  The emitted program enumerates visible rival
bridge rules = ALIGNMENT x BLOCKER, keeps every rule that reproduces every
demonstration exactly, and answers only when all survivors agree on the full
query output.  No first/majority choice, no D4-supplied choice, no skipping of
demonstrations and no fallback when nothing survives.

v6 hard-coded the constructor's "equal centre" pairing test although the
canonical train demonstrations contain no uncentred same-colour pair, so the
pairing condition was a hidden parameter.  v7 makes it a rival ("overlap").
"""

_BODY = r'''

# Rival rules.  A rule is (ALIGNMENT, BLOCKER).  Every rule pairs same-colour
# solid rectangles that face each other across a background gap and bridges
# gap x (shared span minus one cell at each end), painting background cells only.
#   ALIGNMENT centred : the two rectangles have the same centre on the shared axis
#                       (constructor reading)
#             overlap : any positive shared span (centred pairs included)
#   BLOCKER   trim_any  : bridge rectangle must be all background (constructor)
#             trim_same : bridge rectangle holds no cell of the pair's colour
#             span_any  : whole shared-span gap must be all background
#             span_same : whole shared-span gap holds no cell of the pair's colour
#             none      : always bridge
ALIGNMENTS = ('centred', 'overlap')
BLOCKERS = ('trim_any', 'trim_same', 'span_any', 'span_same', 'none')
HYPOTHESES = tuple((a, b) for a in ALIGNMENTS for b in BLOCKERS)


class Undetermined(Exception):
    pass


def _as_grid(v):
    g = [[int(c) for c in row] for row in v]
    if not g or not g[0] or any(len(r) != len(g[0]) for r in g):
        raise Undetermined('malformed grid')
    return g


def _boxes(g):
    H = len(g)
    W = len(g[0])
    seen = [[False] * W for _ in range(H)]
    boxes = []
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c == BG or seen[y][x]:
                continue
            if c == BR:
                raise Undetermined('bridge colour present in an input')
            seen[y][x] = True
            stack = [(y, x)]
            y0 = y1 = y
            x0 = x1 = x
            count = 0
            while stack:
                cy, cx = stack.pop()
                count += 1
                if cy < y0:
                    y0 = cy
                if cy > y1:
                    y1 = cy
                if cx < x0:
                    x0 = cx
                if cx > x1:
                    x1 = cx
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny = cy + dy
                    nx = cx + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == c:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            if count != (y1 - y0 + 1) * (x1 - x0 + 1):
                raise Undetermined('object is not a solid rectangle')
            boxes.append((c, y0, x0, y1, x1))
    return boxes


def _candidates(g):
    """Yield (colour, centred, bridge, span); rectangles inclusive (y0, x0, y1, x1)."""
    boxes = _boxes(g)
    n = len(boxes)
    out = []
    for i in range(n):
        ca, ay0, ax0, ay1, ax1 = boxes[i]
        for j in range(i + 1, n):
            cb, by0, bx0, by1, bx1 = boxes[j]
            if ca != cb:
                continue
            s0 = max(ay0, by0)
            s1 = min(ay1, by1)
            if s0 <= s1:
                # rows overlap, so the boxes face across columns
                if ax1 < bx0:
                    g0, g1 = ax1 + 1, bx0 - 1
                else:
                    g0, g1 = bx1 + 1, ax0 - 1
                out.append((ca, ay0 + ay1 == by0 + by1, (s0 + 1, g0, s1 - 1, g1), (s0, g0, s1, g1)))
            s0 = max(ax0, bx0)
            s1 = min(ax1, bx1)
            if s0 <= s1:
                # columns overlap, so the boxes face across rows
                if ay1 < by0:
                    g0, g1 = ay1 + 1, by0 - 1
                else:
                    g0, g1 = by1 + 1, ay0 - 1
                out.append((ca, ax0 + ax1 == bx0 + bx1, (g0, s0 + 1, g1, s1 - 1), (g0, s0, g1, s1)))
    return out


def _cells(g, r):
    y0, x0, y1, x1 = r
    return [g[y][x] for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]


def _apply(g, hyp):
    align, block = hyp
    fills = []
    for colour, centred, bridge, span in _candidates(g):
        if align == 'centred' and not centred:
            continue
        if bridge[0] > bridge[2] or bridge[1] > bridge[3]:
            continue
        if block == 'trim_any':
            ok = all(v == BG for v in _cells(g, bridge))
        elif block == 'trim_same':
            ok = all(v != colour for v in _cells(g, bridge))
        elif block == 'span_any':
            ok = all(v == BG for v in _cells(g, span))
        elif block == 'span_same':
            ok = all(v != colour for v in _cells(g, span))
        else:
            ok = True
        if ok:
            fills.append(bridge)
    out = [row[:] for row in g]
    for y0, x0, y1, x1 in fills:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if g[y][x] == BG:
                    out[y][x] = BR
    return out


def solve(demonstrations, grid):
    q = _as_grid(grid)
    demos = []
    for d in demonstrations:
        demos.append((_as_grid(d['input']), _as_grid(d['output'])))
    if not demos:
        raise Undetermined('no demonstrations')
    survivors = []
    for hyp in HYPOTHESES:
        if all(_apply(di, hyp) == do for di, do in demos):
            survivors.append(hyp)
    if not survivors:
        raise Undetermined('no bridge rule reproduces every demonstration')
    answers = []
    for hyp in survivors:
        a = _apply(q, hyp)
        if a not in answers:
            answers.append(a)
    if len(answers) != 1:
        raise Undetermined('demonstration-consistent bridge rules disagree on the query')
    answer = answers[0]
    if answer != q and not any(di != do for di, do in demos):
        # The bridge colour is never shown by the demonstrations.
        raise Undetermined('bridge colour not demonstrated')
    return answer
'''


def build_program(d4, palette):
    bg = int(palette[0])
    br = int(palette[8])
    head = [
        '# f3b10344 same-colour bridges in visible coordinates (D4 index %d).' % int(d4),
        '# Alignment, gap, shared span and one-cell trim are D4-invariant, so',
        '# rows and columns are treated alike; D4 selects nothing.',
        'BG = %d' % bg,
        'BR = %d' % br,
    ]
    return '\n'.join(head) + _BODY
