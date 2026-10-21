"""Independent identifiability gate for df8cc377 (host-side evidence only).

Uses demonstration inputs/outputs and the query INPUT only; never query labels.
Independent of the factory's emitted solver:
  * background = majority colour (solver uses palette[0]);
  * frames via explicit flood-fill (solver uses bounding-box arithmetic);
  * roles by bitmask enumeration (solver uses itertools.combinations);
  * phase evidence as GF(2) linear equations solved by elimination
    (solver re-renders whole grids under the four corner hypotheses).
Statuses:
  unique                    query output identified by demos
  phase_context_shortfall   demos lack checkerboard-phase evidence the query needs
  role_ambiguous            the query input itself admits >1 role reading (intrinsic)
  no_query_reading          query input outside the visible family
  demo_unexplained / demo_role_ambiguous / demo_inconsistent   demo-side failures
"""
from collections import Counter


def _bg(g):
    return Counter(v for r in g for v in r).most_common(1)[0][0]


def _flood(g, colour):
    H, W = len(g), len(g[0])
    seen, comps = set(), []
    for y in range(H):
        for x in range(W):
            if g[y][x] == colour and (y, x) not in seen:
                st, comp = [(y, x)], []
                seen.add((y, x))
                while st:
                    cy, cx = st.pop()
                    comp.append((cy, cx))
                    for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if 0 <= ny < H and 0 <= nx < W and g[ny][nx] == colour and (ny, nx) not in seen:
                            seen.add((ny, nx))
                            st.append((ny, nx))
                comps.append(comp)
    return comps


def _frame(g, colour, bg):
    comps = _flood(g, colour)
    if len(comps) != 1:
        return None
    cells = set(comps[0])
    top = min(y for y, _ in cells); bot = max(y for y, _ in cells)
    lef = min(x for _, x in cells); rig = max(x for _, x in cells)
    if bot - top < 2 or rig - lef < 2:
        return None
    border = {(y, x) for y in range(top, bot + 1) for x in range(lef, rig + 1)
              if y in (top, bot) or x in (lef, rig)}
    if border != cells:
        return None
    ring = {(y, x) for y in range(top + 1, bot) for x in range(lef + 1, rig)
            if y in (top + 1, bot - 1) or x in (lef + 1, rig - 1)}
    if any(g[y][x] != bg for y, x in ring):
        return None
    return (top, lef, bot, rig)


def _separated(a, b):
    # True if the two rectangles keep at least one empty row/column between them.
    return a[2] + 1 < b[0] or b[2] + 1 < a[0] or a[3] + 1 < b[1] or b[3] + 1 < a[1]


def readings(g):
    bg = _bg(g)
    H, W = len(g), len(g[0])
    cnt = Counter(v for r in g for v in r if v != bg)
    cols = sorted(cnt)
    fr = {c: _frame(g, c, bg) for c in cols}
    cap = [c for c in cols if fr[c] is not None]
    want = 2 if min(H, W) <= 20 else 3
    res = []
    for m in range(1 << len(cap)):
        S = [cap[i] for i in range(len(cap)) if m >> i & 1]
        P = [c for c in cols if c not in S]
        if len(S) != want or len(P) != want:
            continue
        boxes = [fr[c] for c in S]
        if any(b[2] - b[0] + 1 > H // 2 or b[3] - b[1] + 1 > W // 2 for b in boxes):
            continue
        if any(not _separated(boxes[i], boxes[j]) for i in range(want) for j in range(i + 1, want)):
            continue
        need = [((b[2] - b[0] - 1) * (b[3] - b[1] - 1) + 1) // 2 for b in boxes]
        pc = {cnt[c]: c for c in P}
        if len(set(need)) != want or len(pc) != want or set(need) != set(pc):
            continue
        res.append({'pixels': tuple(P), 'frames': tuple((b, pc[n]) for b, n in zip(boxes, need))})
    return res


def _vec(box):
    h, w = box[2] - box[0] - 1, box[3] - box[1] - 1
    return ((h - 1) % 2, (w - 1) % 2)


def _demo_equations(inp, out):
    """Equations (va, vb, rhs) for every role reading explaining the demo output."""
    bg = _bg(inp)
    H, W = len(inp), len(inp[0])
    found = []
    for rd in readings(inp):
        interior = set()
        ok = True
        eqs = []
        for box, col in rd['frames']:
            t, l, b, r = box
            ph = 0 if out[t + 1][l + 1] == col else 1
            for y in range(t + 1, b):
                for x in range(l + 1, r):
                    interior.add((y, x))
                    exp = col if (y - t - 1 + x - l - 1) % 2 == ph else bg
                    if out[y][x] != exp:
                        ok = False
            eqs.append(_vec(box) + (ph,))
        for y in range(H):
            for x in range(W):
                if (y, x) in interior:
                    continue
                exp = bg if inp[y][x] in rd['pixels'] else inp[y][x]
                if out[y][x] != exp:
                    ok = False
        if ok:
            found.append(eqs)
    return found


def _solve_gf2(eqs):
    """Return (consistent, basis rows) after elimination over GF(2) in 2 unknowns."""
    rows = []
    for va, vb, rhs in eqs:
        v = [va, vb, rhs]
        for piv, row in rows:
            if v[piv]:
                v = [p ^ q for p, q in zip(v, row)]
        if v[0] or v[1]:
            piv = 0 if v[0] else 1
            nr = []
            for p, row in rows:
                if row[piv]:
                    row = [a ^ b for a, b in zip(row, v)]
                nr.append((p, row))
            rows = nr + [(piv, v)]
        elif v[2]:
            return False, rows
    return True, rows


def _in_span(rows, vec):
    v = list(vec) + [0]
    for piv, row in rows:
        if v[piv]:
            v = [p ^ q for p, q in zip(v, row)]
    return not (v[0] or v[1])


def gate(demos, query_input):
    eqs = []
    for d in demos:
        sets = _demo_equations(d['input'], d['output'])
        if not sets:
            return {'status': 'demo_unexplained'}
        if len({tuple(sorted(s)) for s in sets}) > 1:
            return {'status': 'demo_role_ambiguous'}
        eqs += sets[0]
    ok, rows = _solve_gf2(eqs)
    if not ok:
        return {'status': 'demo_inconsistent'}
    rq = readings(query_input)
    if not rq:
        return {'status': 'no_query_reading'}
    if len(rq) > 1:
        return {'status': 'role_ambiguous', 'readings': len(rq)}
    missing = [list(f[0]) for f in rq[0]['frames'] if not _in_span(rows, _vec(f[0]))]
    if missing:
        return {'status': 'phase_context_shortfall', 'rank': len(rows), 'unresolved_frames': missing}
    return {'status': 'unique', 'rank': len(rows)}


def require_checkerboard_phase_evidence(demonstrations, queries):
    from .colour_evidence import MissingColourEvidence, IntrinsicQueryEvidence
    for query in queries:
        result = gate(demonstrations, query['input'])
        if result['status'] in ('role_ambiguous', 'no_query_reading'):
            raise IntrinsicQueryEvidence('df8cc377: ' + result['status'])
        if result['status'] != 'unique':
            raise MissingColourEvidence('df8cc377: ' + result['status'])
