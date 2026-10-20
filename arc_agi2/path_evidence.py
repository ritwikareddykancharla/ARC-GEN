"""Visible evidence for path tie-breaks; no query labels or latent routes.

These checks address the documented competing rules, not all possible rules
consistent with a finite episode. Constructors keep their hard tie cases.
"""
from collections import deque
from .colour_evidence import MissingColourEvidence, _require_rule_agreement

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def route_evidence(g, palette):
    """Shortest-path DAG, then min/max turns within that DAG.

    Counts are capped at two, sufficient to distinguish unique from multiple
    routes. Direction changes on endpoint legs count; the first move does not.
    This is independent of the constructor's lexicographic Dijkstra solver.
    """
    h, w = len(g), len(g[0])
    wall, end, block = palette[8], palette[9], palette[7]
    ends = [(r, c) for r in range(h) for c in range(w) if g[r][c] == end]
    if len(ends) != 2:
        raise MissingColourEvidence('cc9053aa: expected two visible endpoints')
    a, b = ends
    def neighbours(p):
        for dr, dc in DIRS:
            q = p[0]+dr, p[1]+dc
            if 0 <= q[0] < h and 0 <= q[1] < w:
                yield q
    allowed = {p for p in ((r, c) for r in range(h) for c in range(w))
               if g[p[0]][p[1]] == wall
               and all(g[q[0]][q[1]] != block for q in neighbours(p))} | {a, b}
    def distances(start):
        dist, queue = {start: 0}, deque([start])
        while queue:
            p = queue.popleft()
            for q in neighbours(p):
                if q in allowed and q not in dist:
                    dist[q] = dist[p]+1
                    queue.append(q)
        return dist
    da, db = distances(a), distances(b)
    if b not in da:
        raise MissingColourEvidence('cc9053aa: no legal route')
    length = da[b]
    nodes = sorted((p for p in da if da[p]+db.get(p, length+1) == length), key=da.get)
    start = (a, -1)
    low, high, counts, total = {start: 0}, {start: 0}, {start: 1}, {a: 1}
    prev_low, prev_high = {}, {}
    for p in nodes:
        for nd, (dr, dc) in enumerate(DIRS):
            q = p[0]+dr, p[1]+dc
            if da.get(q) != da[p]+1 or da[q]+db.get(q, length+1) != length:
                continue
            total[q] = min(2, total.get(q, 0)+total.get(p, 0))
            target = (q, nd)
            for d in range(-1, 4):
                state = (p, d)
                if state not in low: continue
                turn = int(d != -1 and d != nd)
                cost = low[state]+turn
                if target not in low or cost < low[target]:
                    low[target], counts[target], prev_low[target] = cost, counts[state], state
                elif cost == low[target]:
                    counts[target] = min(2, counts[target]+counts[state])
                cost = high[state]+turn
                if target not in high or cost > high[target]:
                    high[target], prev_high[target] = cost, state
    terminal = [s for s in low if s[0] == b]
    best, worst = min(terminal, key=low.get), max(terminal, key=high.get)
    def paint(state, prev):
        out = [row[:] for row in g]
        while state is not None:
            r, c = state[0]
            out[r][c] = end
            state = prev.get(state)
        return out
    return dict(steps=length, min_turns=low[best], max_turns=high[worst],
                shortest_routes_capped=total[b],
                optimal_routes_capped=min(2, sum(counts[s] for s in terminal if low[s] == low[best])),
                minimum_turn_output=paint(best, prev_low),
                maximum_turn_output=paint(worst, prev_high))


def detour_variants(grid, palette, d4):
    """Both left/right tie conventions in visible coordinates."""
    def vector(dr, dc):
        if d4 >= 4: dc = -dc
        for _ in range(d4 % 4): dr, dc = dc, -dr
        return dr, dc
    down, right = vector(1, 0), vector(0, 1)
    h, w = len(grid), len(grid[0])
    bg, line, bar = palette[0], palette[8], palette[2]
    def inside(p): return 0 <= p[0] < h and 0 <= p[1] < w
    def at(p): return grid[p[0]][p[1]] if inside(p) else None
    def add(p, v, n=1): return p[0]+n*v[0], p[1]+n*v[1]
    starts = [p for p in ((r, c) for r in range(h) for c in range(w))
              if at(p) == line and not inside(add(p, down, -1))]
    if not starts: raise MissingColourEvidence('c87289bb: no source edge')
    outputs = []
    for tie in (-1, 1):
        out = [row[:] for row in grid]
        for p in starts:
            for _ in range(4*(h+w)**2+16):
                if at(p) == bg: out[p[0]][p[1]] = line
                below = add(p, down)
                if not inside(below): break
                if at(below) == bar:
                    distances = []
                    for sign in (-1, 1):
                        n = 1
                        while at(add(below, right, sign*n)) == bar: n += 1
                        distances.append(n)
                    sign = tie if distances[0] == distances[1] else (-1 if distances[0] < distances[1] else 1)
                    p = add(p, right, sign)
                    if not inside(p): break
                else:
                    p = below
            else:
                raise MissingColourEvidence('c87289bb: detour did not terminate')
        outputs.append(out)
    return outputs


def require_path_evidence(task_id, demonstrations, queries, palette, d4):
    if task_id == 'c87289bb':
        _require_rule_agreement(task_id, demonstrations, queries,
                                lambda g: detour_variants(g, palette, d4))
        return
    if task_id != 'cc9053aa': raise ValueError('Unknown path family '+task_id)
    taught = False
    for demo in demonstrations:
        info = route_evidence(demo['input'], palette)
        if info['optimal_routes_capped'] != 1 or info['minimum_turn_output'] != demo['output']:
            raise MissingColourEvidence('cc9053aa: demonstration does not show a unique minimum-turn shortest route')
        taught |= info['max_turns'] > info['min_turns']
    for query in queries:
        info = route_evidence(query['input'], palette)
        if info['optimal_routes_capped'] != 1:
            raise MissingColourEvidence('cc9053aa: query optimum is not unique')
        if info['max_turns'] > info['min_turns'] and not taught:
            raise MissingColourEvidence('cc9053aa: no demonstration teaches the turn tie-break')
