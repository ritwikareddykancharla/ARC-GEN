# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ARC-GEN style generator for task f8f52ecc.

Rule: the background is colour 1, bars of colour 8 are walls, and the other
colours form small pieces. Colours are processed in ascending order. For each
colour with several 4-connected pieces, the rule repeatedly links the closest
pair of pieces, measured by Manhattan distance between cells. A link is a
straight path or a single-corner L path, and it may cross background cells
only. If both L paths are open, the corner follows the orientation of a line
piece at one endpoint: a vertical piece means the vertical leg goes first,
and a horizontal piece means the horizontal leg goes first. A link is
'decided' when it is straight, when only one L is open, or when an endpoint
orientation picks the L. Decided links are preferred over undecided ones.
Walls never change, and colours that occur as a single piece never change.

Latent scene model: each repeated colour owns one hidden route. A route is a
4-connected, self-avoiding polyline given by its waypoints. The input shows
some cells of the route (the pieces), always including both route ends. The
output paints the whole route. Interior route segments have length >= 2.
The first and last segments may be one-cell end stubs (as in train 1, the
colour-9 and colour-6 routes of train 3, and the colour-2 route of test 2),
so a lone end piece can sit diagonally across a hidden corner. Each turn
goes left or right at random, so a route can be a monotone staircase or can
double back in a U shape. Each hidden gap contains at most one corner. Each
L-shaped gap is made decidable in one of three ways:
  * a wall is placed on the alternative L, so only one L is open;
  * the visible piece next to the gap is extended along the first leg, so
    the orientation rule picks the designed corner while both Ls stay open;
  * nothing is added, and the gap is decided later, once a neighbouring link
    has given an endpoint an orientation.
Every U turn gets a wall in its interior, parallel to its legs. That wall
blocks the Manhattan-closest pair across the U, so the greedy rule must take
a farther, open pair, as in train 1 and train 3.
Distractors are extra walls and single pieces in unused colours. Pieces of
different colours may touch.

Certification. The answer is always painted from the latent routes. A local
check only rejects scenes whose designed answer is not forced by the rule
under every scan-order tie-break. The check first tries a polynomial
certificate per colour, which does not enumerate interleavings. It covers
every 'design-subset' state, meaning the input plus any set of filled gaps.
In each such state it requires two things:
  (a) Some unfilled gap is a decided link. An undecided gap needs an
      unfilled, always-decided neighbour gap as a witness.
  (b) Every decided gap link draws exactly its gap cells. Every other
      decided cell pair is strictly beaten by an unfilled decided gap. That
      gap must lie between the pair's endpoints, or be fixed by a bounded
      local enumeration of the gaps that influence it.
Under (a) and (b), every greedy step fills exactly one gap, whatever the
order. So all orders end in the designed route. Commuting, independent gap
fills (for example a long dashed line) therefore cost polynomial time
instead of 2^n states. When the certificate is inconclusive, the generator
falls back to an exhaustive tie-order search with a state budget. In random
mode a scene is silently rejected if that budget is exceeded. In explicit
mode this raises a distinct ValueError.
Random mode prefers scenes that contain a non-straight decision: a hidden L
corner, or a hidden gap inside a walled U. It falls back to straight-only
scenes only late in its bounded retry budget.

Sizes: the canonical grids are 8x10, 10x10 and 12x12. Random mode samples
8..16 cells per side, and sometimes 17..30 as a synthetic extension.
Explicit sizes 5..30 are allowed. Very small grids with many colours may be
infeasible, in which case a RuntimeError is raised.
Not generated: colours left disconnected because no free path exists,
branching (tree-shaped) outcomes, links with more than one corner (the rule
cannot produce them), and scenes that depend on the reference's scan-order
tie-breaks.
"""

import collections
import random

import common

BG = 1
WALL = 8
PIECE_COLOURS = [0, 2, 3, 4, 5, 6, 7, 9]
DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]
MAX_ATTEMPTS = 300
HARD_ATTEMPTS = 200
RANDOM_SETTLE_BUDGET = 400
EXPLICIT_SETTLE_BUDGET = 5000
END_STUB_PROB = 0.3
MAX_DEP_GAPS = 8
PAIR_ENUM_LIMIT = 12
CERT_WORK = 40000


class _BudgetExceeded(Exception):
  """The tie-order simulation visited too many states to certify a scene."""


class _Inconclusive(Exception):
  """The polynomial certificate could not prove the scene forced."""


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _is_seq(v):
  return isinstance(v, (list, tuple))


def _sign(v):
  return (v > 0) - (v < 0)


def _dist(a, b):
  return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _line(p, q):
  """Inclusive straight run of cells from p to q (same row or column)."""
  if p[0] != q[0] and p[1] != q[1]:
    raise ValueError('cells %s and %s are not axis aligned'
                     % (tuple(p), tuple(q)))
  r, c = p[0], p[1]
  dr, dc = _sign(q[0] - r), _sign(q[1] - c)
  out = [(r, c)]
  while (r, c) != (q[0], q[1]):
    r += dr
    c += dc
    out.append((r, c))
  return out


def _route(waypoints):
  """Expand a waypoint polyline into its ordered list of cells."""
  pts = [tuple(p) for p in waypoints]
  cells = [pts[0]]
  for p, q in zip(pts, pts[1:]):
    cells.extend(_line(p, q)[1:])
  return cells


def _lpath(a, b, vfirst):
  """Cells strictly between a and b on the L going vertical/horizontal first."""
  corner = (b[0], a[1]) if vfirst else (a[0], b[1])
  pts = _line(a, corner)[1:] + _line(corner, b)[1:]
  return pts[:-1]


def _step(cells, i, j):
  return (cells[j][0] - cells[i][0], cells[j][1] - cells[i][1])


def _corners(cells):
  """Indices of route cells where the route turns."""
  return [i for i in range(1, len(cells) - 1)
          if _step(cells, i - 1, i) != _step(cells, i, i + 1)]


def _gaps(filled):
  """Maximal runs (start, end) of hidden route cells."""
  out, i, n = [], 0, len(filled)
  while i < n:
    if not filled[i]:
      s = i
      while i < n and not filled[i]:
        i += 1
      out.append((s, i - 1))
    else:
      i += 1
  return out


def _render(height, width, chains, walls, singletons):
  """Paint the input from the latent scene and the output from the routes."""
  grid = common.grid(width, height, BG)
  for r0, c0, r1, c1 in walls:
    for r, c in _line((r0, c0), (r1, c1)):
      grid[r][c] = WALL
  for r, c, col in singletons:
    grid[r][c] = col
  for col, _, pieces in chains:
    for r, c in pieces:
      grid[r][c] = col
  output = [row[:] for row in grid]
  for col, way, _ in chains:
    for r, c in _route(way):
      output[r][c] = col
  return grid, output


# Local consistency checks. They never produce the answer. They only reject
# scenes whose designed answer is not forced by the rule.


def _subsets(free, base):
  free = sorted(free)
  for mask in range(1 << len(free)):
    chosen = set(base)
    for t, g in enumerate(free):
      if mask >> t & 1:
        chosen.add(g)
    yield chosen


def _certify_colour(grid, col, cells, filled):
  """Polynomial proof that every greedy order paints exactly the route.

  grid is the state when col is processed: earlier colours are final and
  later colours are untouched. Raises _Inconclusive when the sufficient
  conditions (a) and (b) from the module docstring cannot be established.
  """
  h, w = len(grid), len(grid[0])
  n = len(cells)
  index = {cell: k for k, cell in enumerate(cells)}
  for r in range(h):
    for c in range(w):
      if grid[r][c] == col and (r, c) not in index:
        raise _Inconclusive()
  for k, (r, c) in enumerate(cells):
    if grid[r][c] != (col if filled[k] else BG):
      raise _Inconclusive()
    for dr, dc in DIRS:
      j = index.get((r + dr, c + dc))
      if j is not None and abs(j - k) != 1:
        raise _Inconclusive()
  gaps = _gaps(filled)
  if not gaps or gaps[0][0] < 1 or gaps[-1][1] > n - 2:
    raise _Inconclusive()
  gap_of = [None] * n
  for g, (s, e) in enumerate(gaps):
    for k in range(s, e + 1):
      gap_of[k] = g

  def coloured(k, done):
    return filled[k] or gap_of[k] in done

  def is_bg(cell, done):
    if grid[cell[0]][cell[1]] != BG:
      return False
    k = index.get(cell)
    return k is None or gap_of[k] not in done

  def axis(k, done):
    found = None
    for j in (k - 1, k + 1):
      if 0 <= j < n and coloured(j, done):
        if cells[j][1] == cells[k][1]:
          return 'v'
        found = 'h'
    return found

  def evaluate(i, j, done):
    a, b = cells[i], cells[j]
    opts = []
    for vf in (True, False):
      path = _lpath(a, b, vf)
      if all(is_bg(x, done) for x in path):
        opts.append(frozenset(path))
    if not opts:
      return None
    if a[0] == b[0] or a[1] == b[1] or len(opts) == 1:
      return ('dec', {opts[0]})
    ax, bx = axis(i, done), axis(j, done)
    if ax or bx:
      first = _lpath(a, b, ax == 'v') if ax else _lpath(b, a, bx == 'v')
      second = _lpath(b, a, bx == 'v') if bx else _lpath(a, b, ax == 'v')
      return ('dec', {frozenset(first), frozenset(second)})
    return ('amb', None)

  def deps(i, j):
    out = set()
    a, b = cells[i], cells[j]
    for vf in (True, False):
      for x in _lpath(a, b, vf):
        k = index.get(x)
        if k is not None and gap_of[k] is not None:
          out.add(gap_of[k])
    for k in (i - 1, i, i + 1, j - 1, j, j + 1):
      if 0 <= k < n and gap_of[k] is not None:
        out.add(gap_of[k])
    return out

  m = len(gaps)
  ends = [(s - 1, e + 1) for s, e in gaps]
  design = [frozenset(cells[s:e + 1]) for s, e in gaps]
  dist = [_dist(cells[i], cells[j]) for i, j in ends]
  dep = []
  for g in range(m):
    d = deps(*ends[g]) - {g}
    if len(d) > MAX_DEP_GAPS:
      raise _Inconclusive()
    dep.append(d)
  robust = [True] * m
  amb_cases = []
  for g in range(m):
    for done in _subsets(dep[g], ()):
      res = evaluate(ends[g][0], ends[g][1], done)
      if res is None:
        raise _Inconclusive()
      if res[0] == 'dec':
        if res[1] != {design[g]}:
          raise _Inconclusive()
      else:
        robust[g] = False
        amb_cases.append((g, done))
  for g, done in amb_cases:
    if not any(x not in done and robust[x] for x in dep[g]):
      raise _Inconclusive()

  design_pairs = set(ends)
  work = 0
  for i in range(n):
    for j in range(i + 2, n):
      if (i, j) in design_pairs:
        continue
      between = [g for g, (s, e) in enumerate(gaps) if s > i and e < j]
      if not between:
        continue
      forced = {gap_of[k] for k in (i, j) if gap_of[k] is not None}
      a, b = cells[i], cells[j]
      d = _dist(a, b)

      def perm_blocked(path):
        for x in path:
          if grid[x[0]][x[1]] != BG:
            return True
          k = index.get(x)
          if k is not None and gap_of[k] in forced:
            return True
        return False

      if all(perm_blocked(_lpath(a, b, vf)) for vf in (True, False)):
        continue
      if all(robust[g] and dist[g] < d for g in between):
        continue
      universe = deps(i, j) | set(between)
      for g in between:
        universe |= dep[g]
      free = universe - forced
      if len(free) > PAIR_ENUM_LIMIT:
        raise _Inconclusive()
      for done in _subsets(free, forced):
        work += 1
        if work > CERT_WORK:
          raise _Inconclusive()
        if all(g in done for g in between):
          continue
        res = evaluate(i, j, done)
        if res is None or res[0] == 'amb':
          continue
        beaten = False
        for g in universe:
          if g in done or dist[g] >= d:
            continue
          if robust[g] or (dep[g] <= universe and
                           evaluate(ends[g][0], ends[g][1], done)[0] == 'dec'):
            beaten = True
            break
        if not beaten:
          raise _Inconclusive()
  return True


def _components(grid, col):
  h, w = len(grid), len(grid[0])
  seen, comps = set(), []
  for r in range(h):
    for c in range(w):
      if grid[r][c] != col or (r, c) in seen:
        continue
      seen.add((r, c))
      stack, comp = [(r, c)], []
      while stack:
        y, x = stack.pop()
        comp.append((y, x))
        for dy, dx in DIRS:
          ny, nx = y + dy, x + dx
          if (0 <= ny < h and 0 <= nx < w and (ny, nx) not in seen
              and grid[ny][nx] == col):
            seen.add((ny, nx))
            stack.append((ny, nx))
      comps.append(comp)
  return comps


def _link_options(grid, col):
  """Every path the greedy rule may draw next, over all piece orders."""
  comps = _components(grid, col)
  if len(comps) < 2:
    return []
  gid = {}
  for i, comp in enumerate(comps):
    for cell in comp:
      gid[cell] = i

  def axis(cell):
    i, (y, x) = gid[cell], cell
    if gid.get((y - 1, x)) == i or gid.get((y + 1, x)) == i:
      return 'v'
    if gid.get((y, x - 1)) == i or gid.get((y, x + 1)) == i:
      return 'h'
    return None

  def is_open(path):
    return all(grid[r][c] == BG for r, c in path)

  pairs = []
  for i in range(len(comps)):
    for j in range(i + 1, len(comps)):
      for a in comps[i]:
        for b in comps[j]:
          pairs.append((_dist(a, b), a, b))
  pairs.sort()
  det_d, det_paths, amb_d, amb_paths = None, set(), None, set()
  for d, a, b in pairs:
    if det_d is not None and d > det_d:
      break
    opts = [p for p in (_lpath(a, b, True), _lpath(a, b, False))
            if is_open(p)]
    if not opts:
      continue
    if a[0] == b[0] or a[1] == b[1] or len(opts) == 1:
      det_d = d
      det_paths.add(frozenset(opts[0]))
      continue
    ax, bx = axis(a), axis(b)
    if ax or bx:
      first = _lpath(a, b, ax == 'v') if ax else _lpath(b, a, bx == 'v')
      second = _lpath(b, a, bx == 'v') if bx else _lpath(a, b, ax == 'v')
      det_d = d
      det_paths.update((frozenset(first), frozenset(second)))
    elif amb_d is None or d == amb_d:
      amb_d = d
      amb_paths.update((frozenset(_lpath(a, b, True)),
                        frozenset(_lpath(b, a, True))))
  return list(det_paths) if det_d is not None else list(amb_paths)


def _settle(grid, col, budget):
  """Exhaustive fallback: all final grids reachable for one colour."""
  start = tuple(tuple(row) for row in grid)
  seen, stack, finals = {start}, [start], set()
  for _ in range(budget):
    if not stack:
      return finals
    state = stack.pop()
    options = _link_options(state, col)
    if not options:
      finals.add(state)
      continue
    for path in options:
      nxt = [list(row) for row in state]
      for r, c in path:
        nxt[r][c] = col
      key = tuple(tuple(row) for row in nxt)
      if key not in seen:
        seen.add(key)
        stack.append(key)
  if stack:
    raise _BudgetExceeded()
  return finals


def _rule_reproduces(inp, out, chains, budget):
  """True when every greedy order turns inp into exactly out."""
  counts = collections.Counter(v for row in inp for v in row)
  if any(n >= counts[BG] for v, n in counts.items() if v != BG):
    return False
  routes = {}
  for col, way, pieces in chains:
    cells = _route(way)
    pset = {tuple(p) for p in pieces}
    routes[col] = (cells, [x in pset for x in cells])
  grid = [row[:] for row in inp]
  for col in sorted(set(counts) - {BG, WALL}):
    if col in routes:
      cells, filled = routes[col]
      try:
        _certify_colour(grid, col, cells, filled)
      except _Inconclusive:
        pass
      else:
        for r, c in cells:
          grid[r][c] = col
        continue
    finals = _settle(grid, col, budget)
    if len(finals) != 1:
      return False
    grid = [list(row) for row in finals.pop()]
  return grid == out


# Random scene construction.


def _pick_side():
  if random.random() < 0.85:
    return random.randint(8, 16)
  return random.randint(17, 30)


def _walk(h, w, blocked, lmax, nseg):
  """Self-avoiding route of nseg segments with random left/right turns.

  Interior segments have length >= 2 so parallel legs never touch; the first
  and last segments may be one-cell end stubs.
  """
  for _ in range(60):
    r, c = random.randrange(h), random.randrange(w)
    if (r, c) in blocked:
      continue
    cells, index, segs = [(r, c)], {(r, c): 0}, []
    d = random.choice(DIRS)
    ok = True
    for k in range(nseg):
      if k:
        d = random.choice([(d[1], d[0]), (-d[1], -d[0])])
      if (nseg >= 2 and k in (0, nseg - 1)
          and random.random() < END_STUB_PROB):
        length = 1
      else:
        length = random.randint(2, lmax)
      for _ in range(length):
        r, c = r + d[0], c + d[1]
        if not (0 <= r < h and 0 <= c < w) or (r, c) in blocked:
          ok = False
          break
        k_new = len(cells)
        for y in (r - 1, r, r + 1):
          for x in (c - 1, c, c + 1):
            j = index.get((y, x))
            if j is not None and j <= k_new - 3:
              ok = False
        if not ok:
          break
        index[(r, c)] = k_new
        cells.append((r, c))
      if not ok:
        break
      segs.append((d, length))
    if ok:
      return cells, segs
  return None


def _reveal(cells):
  """Choose visible cells: ends shown, >= 1 gap, <= 1 corner per gap."""
  n = len(cells)
  corners = _corners(cells)
  for _ in range(20):
    filled = [False] * n
    filled[0] = filled[-1] = True
    for i in range(1, n - 1):
      if random.random() < (0.35 if i in corners else 0.12):
        filled[i] = True
    for i in range(n):
      if filled[i] and random.random() < 0.25:
        j = i + random.choice([-1, 1])
        if 0 <= j < n:
          filled[j] = True
    for _ in range(n):
      multi = None
      for s, e in _gaps(filled):
        cs = [k for k in corners if s <= k <= e]
        if len(cs) >= 2:
          multi = cs
          break
      if multi is None:
        break
      filled[random.choice(multi)] = True
    if _gaps(filled):
      return filled
  return None


def _seg_starts(segs):
  """Route index of the cell where each segment starts."""
  starts, pos = [], 0
  for _, length in segs:
    starts.append(pos)
    pos += length
  return starts


def _u_turns(segs):
  """Indices k of middle segments of U turns."""
  out = []
  for k in range(1, len(segs) - 1):
    d0, d1 = segs[k - 1][0], segs[k + 1][0]
    if d0 == (-d1[0], -d1[1]):
      out.append(k)
  return out


def _attempt(h, w, nch, require_hard):
  """One try at a random scene; returns None when a constraint fails."""
  lmax = max(3, min(9, max(h, w) // 2))
  long_routes = [4, 5] if max(h, w) >= 14 else []
  routes, occupied = [], set()
  for col in random.sample(PIECE_COLOURS, nch):
    res = _walk(h, w, occupied, lmax,
                random.choice([1, 2, 2, 3, 3, 4] + long_routes))
    if res is None:
      return None
    cells, segs = res
    filled = _reveal(cells)
    if filled is None:
      return None
    routes.append((col, cells, segs, filled))
    occupied.update(cells)
  walls, wallcells = [], set()

  def inside(p):
    return 0 <= p[0] < h and 0 <= p[1] < w

  def add_bar(p, q):
    walls.append((p[0], p[1], q[0], q[1]))
    wallcells.update(_line(p, q))

  def try_bar(anchor, lmin, lmax_bar):
    for _ in range(10):
      size = random.randint(lmin, lmax_bar)
      off = random.randint(0, size - 1)
      if random.random() < 0.5:
        p = (anchor[0], anchor[1] - off)
        q = (anchor[0], anchor[1] - off + size - 1)
      else:
        p = (anchor[0] - off, anchor[1])
        q = (anchor[0] - off + size - 1, anchor[1])
      if not (inside(p) and inside(q)):
        continue
      if any(x in occupied for x in _line(p, q)):
        continue
      add_bar(p, q)
      return True
    return False

  # A wall inside every U turn, parallel to its legs, covering both legs.
  for col, cells, segs, filled in routes:
    starts = _seg_starts(segs)
    for k in _u_turns(segs):
      (d0, l0), (dm, lm), (d1, l1) = segs[k - 1], segs[k], segs[k + 1]
      p = cells[starts[k]]
      t = random.randint(1, lm - 1)
      base = (p[0] + t * dm[0], p[1] + t * dm[1])
      need = max(l0, l1)
      bar = []
      for j in range(1, need + random.randint(0, 2) + 1):
        x = (base[0] - j * d0[0], base[1] - j * d0[1])
        if not inside(x) or x in occupied:
          break
        bar.append(x)
      if len(bar) < need:
        return None
      add_bar(bar[0], bar[-1])

  # Make each L-shaped gap decidable: block the other L, orient an endpoint
  # piece along the first leg, or leave it to be decided later.
  for col, cells, segs, filled in routes:
    for k in _corners(cells):
      gap = None
      for s, e in _gaps(filled):
        if s <= k <= e:
          gap = (s, e)
      if gap is None:
        continue
      s, e = gap
      a, b = cells[s - 1], cells[e + 1]
      vfirst = cells[k] == (b[0], a[1])
      alt = _lpath(a, b, not vfirst)
      if any(x in wallcells for x in alt):
        continue
      roll = random.random()
      done = False
      if roll < 0.4:
        free = [x for x in alt if x not in occupied]
        random.shuffle(free)
        for x in free[:6]:
          if try_bar(x, 1, 4):
            done = True
            break
      if not done and roll < 0.88:
        ext = []
        if s >= 2 and _step(cells, s - 2, s - 1) == _step(cells, s - 1, s):
          ext.append(s - 2)
        if (e + 2 < len(cells)
            and _step(cells, e + 1, e + 2) == _step(cells, e, e + 1)):
          ext.append(e + 2)
        if ext:
          filled[random.choice(ext)] = True
        else:
          filled[k] = True

  # Re-check the per-route invariants: the decidability pass may have filled
  # the only gap of a route, which would silently drop a repeated colour.
  # A scene is 'hard' if some hidden gap contains a corner, or if some hidden
  # gap lies inside the cells of a walled U (legs plus middle segment).
  hard = False
  for col, cells, segs, filled in routes:
    gaps = _gaps(filled)
    if not gaps or not filled[0] or not filled[-1]:
      return None
    corners = _corners(cells)
    for s, e in gaps:
      cs = [k for k in corners if s <= k <= e]
      if len(cs) > 1:
        return None
      if cs:
        hard = True
    starts = _seg_starts(segs)
    for k in _u_turns(segs):
      lo = starts[k - 1] + 1
      hi = starts[k + 1] + segs[k + 1][1]
      if any(s <= hi and e >= lo for s, e in gaps):
        hard = True
  if require_hard and not hard:
    return None

  # Distractor walls and single pieces in unused colours.
  for _ in range(random.randint(0, 1 + max(h, w) // 8)):
    anchor = (random.randrange(h), random.randrange(w))
    if anchor not in occupied:
      try_bar(anchor, 2, max(3, min(h, w) - 2))
  used = [route[0] for route in routes]
  pool = [c for c in PIECE_COLOURS if c not in used]
  taken = occupied | wallcells
  singles = []
  for col in random.sample(pool, random.randint(0, min(4, len(pool)))):
    for _ in range(30):
      x = (random.randrange(h), random.randrange(w))
      if x not in taken:
        singles.append((x[0], x[1], col))
        taken.add(x)
        break

  chains = []
  for col, cells, segs, filled in routes:
    way = [cells[0]] + [cells[i] for i in _corners(cells)] + [cells[-1]]
    pieces = [cells[i] for i in range(len(cells)) if filled[i]]
    chains.append((col, way, pieces))
  inp, out = _render(h, w, chains, walls, singles)
  if 2 * sum(v != BG for row in inp for v in row) >= h * w:
    return None
  if inp == out:
    return None
  try:
    if not _rule_reproduces(inp, out, chains, RANDOM_SETTLE_BUDGET):
      return None
  except _BudgetExceeded:
    return None
  return chains, walls, singles


def _random_scene(height, width, num_chains):
  for attempt in range(MAX_ATTEMPTS):
    h = height if height is not None else _pick_side()
    w = width if width is not None else _pick_side()
    if num_chains is not None:
      nch = num_chains
    else:
      choices = [1, 2, 2, 3, 3]
      if h * w >= 120:
        choices += [4, 4]
      if h * w >= 300:
        choices += [5]
      nch = random.choice(choices)
    scene = _attempt(h, w, nch, attempt < HARD_ATTEMPTS)
    if scene is not None:
      return h, w, scene
  raise RuntimeError('could not build a scene for the requested size/count; '
                     'use a larger grid or fewer chains')


def _check_explicit(height, width, chains, walls, singletons):
  """Reject explicit scenes that the latent model cannot represent."""

  def inside(p):
    return 0 <= p[0] < height and 0 <= p[1] < width

  def colour_ok(col):
    return _is_int(col) and 0 <= col <= 9 and col not in (BG, WALL)

  def cell_ok(p):
    return _is_seq(p) and len(p) == 2 and all(_is_int(v) for v in p)

  if not _is_seq(chains) or not chains:
    raise ValueError('explicit mode needs a non-empty list of chains')
  wallcells = set()
  for bar in walls:
    if (not _is_seq(bar) or len(bar) != 4
        or not all(_is_int(v) for v in bar)):
      raise ValueError('walls are (r0, c0, r1, c1) integer tuples')
    p, q = (bar[0], bar[1]), (bar[2], bar[3])
    if not (inside(p) and inside(q)):
      raise ValueError('wall %s is out of bounds' % (tuple(bar),))
    wallcells.update(_line(p, q))
  routecells, colours = set(), set()
  for chain in chains:
    if not _is_seq(chain) or len(chain) != 3:
      raise ValueError('chains are (colour, waypoints, pieces) triples')
    col, way, pieces = chain
    if not colour_ok(col) or col in colours:
      raise ValueError('chain colours must be distinct ints 0..9, not 1 or 8')
    colours.add(col)
    if (not _is_seq(way) or not way or not all(cell_ok(p) for p in way)
        or not all(inside(p) for p in way)):
      raise ValueError('chain %d waypoints must be integer cells inside the '
                       'grid' % col)
    cells = _route(way)
    cellset = set(cells)
    if len(cellset) != len(cells):
      raise ValueError('chain %d route overlaps itself' % col)
    if cellset & routecells or cellset & wallcells:
      raise ValueError('chain %d route hits a wall or another route' % col)
    if not _is_seq(pieces) or not all(cell_ok(p) for p in pieces):
      raise ValueError('chain %d pieces must be a list of integer cells' % col)
    pset = {tuple(p) for p in pieces}
    if not pset <= cellset:
      raise ValueError('chain %d pieces must lie on its route' % col)
    if cells[0] not in pset or cells[-1] not in pset:
      raise ValueError('chain %d must show both route ends' % col)
    filled = [x in pset for x in cells]
    gaps = _gaps(filled)
    if not gaps:
      raise ValueError('chain %d must hide at least one route cell' % col)
    corners = _corners(cells)
    for s, e in gaps:
      if sum(1 for k in corners if s <= k <= e) > 1:
        raise ValueError('chain %d has a hidden gap with several corners'
                         % col)
    routecells |= cellset
  spots = set()
  for single in singletons:
    if not _is_seq(single) or len(single) != 3:
      raise ValueError('singletons are (row, col, colour) triples')
    r, c, col = single
    if not cell_ok((r, c)) or not inside((r, c)):
      raise ValueError('singleton (%s, %s) is invalid or out of bounds'
                       % (r, c))
    if not colour_ok(col) or col in colours:
      raise ValueError('singleton colours must be unique and unused by chains')
    if (r, c) in wallcells or (r, c) in routecells or (r, c) in spots:
      raise ValueError('singleton (%d, %d) overlaps another object' % (r, c))
    colours.add(col)
    spots.add((r, c))


def generate(height=None, width=None, chains=None, walls=None,
             singletons=None, num_chains=None):
  """Build one input/output pair.

  Args:
    height: number of rows, int 5..30. In random mode it defaults to 8..16
      (sometimes 17..30). It is required when chains is given.
    width: number of columns, int 5..30. Same defaults as height.
    chains: list of (colour, waypoints, pieces). The waypoints describe the
      hidden route polyline; consecutive waypoints must share a row or a
      column. The pieces are the route cells visible in the input. They must
      include both route ends and leave at least one hidden gap, with at
      most one corner per gap. If chains is omitted, a fresh random scene is
      sampled.
    walls: list of (r0, c0, r1, c1) straight bars of colour 8. Only valid
      together with explicit chains. They must not overlap any route cell,
      although adjacency is allowed.
    singletons: list of (row, col, colour) single pieces in unique colours
      that never change. Only valid together with explicit chains.
    num_chains: number of repeated colours (int 1..6) in random mode.

  Explicit scenes are rejected with ValueError when the rule does not force
  exactly the painted routes. A distinct message is used when the
  polynomial certificate is inconclusive and the exhaustive fallback
  exceeds its state budget.
  """
  for name, v in (('height', height), ('width', width)):
    if v is not None and (not _is_int(v) or not 5 <= v <= 30):
      raise ValueError('%s must be an int in 5..30' % name)
  if chains is None:
    if walls is not None or singletons is not None:
      raise ValueError('walls/singletons require explicit chains')
    if num_chains is not None and (not _is_int(num_chains)
                                   or not 1 <= num_chains <= 6):
      raise ValueError('num_chains must be an int in 1..6')
    height, width, scene = _random_scene(height, width, num_chains)
    chains, walls, singletons = scene
    grid, output = _render(height, width, chains, walls, singletons)
  else:
    if num_chains is not None:
      raise ValueError('num_chains is only used in random mode')
    if height is None or width is None:
      raise ValueError('explicit chains require height and width')
    if walls is not None and not _is_seq(walls):
      raise ValueError('walls must be a list of (r0, c0, r1, c1) tuples')
    if singletons is not None and not _is_seq(singletons):
      raise ValueError('singletons must be a list of (row, col, colour)')
    walls = list(walls or [])
    singletons = list(singletons or [])
    _check_explicit(height, width, chains, walls, singletons)
    grid, output = _render(height, width, chains, walls, singletons)
    if grid == output:
      raise ValueError('explicit scene does not change anything')
    try:
      forced = _rule_reproduces(grid, output, chains, EXPLICIT_SETTLE_BUDGET)
    except _BudgetExceeded:
      raise ValueError('explicit scene could not be certified: the '
                       'polynomial certificate was inconclusive and the '
                       'tie-order fallback exceeded its budget; the rule may '
                       'still be deterministic')
    if not forced:
      raise ValueError('explicit scene is not forced by the linking rule '
                       '(e.g. an unwalled U, an undecidable L, or a '
                       'shorter competing link)')
  return {'input': grid, 'output': output}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(height=10, width=10, walls=[(3, 2, 3, 7)], singletons=[],
               chains=[(2, [(1, 4), (2, 4), (2, 1), (5, 1), (5, 3)],
                        [(1, 4), (2, 4), (5, 1), (5, 3)])]),
      generate(height=10, width=10, walls=[(8, 0, 8, 2)],
               singletons=[(8, 8, 3)],
               chains=[(2, [(1, 2), (6, 2), (6, 5)],
                        [(1, 2), (3, 2), (6, 3), (6, 4), (6, 5)]),
                       (4, [(1, 7), (1, 8), (4, 8)],
                        [(1, 7), (1, 8), (4, 8)])]),
      generate(height=12, width=12, walls=[(4, 2, 4, 9), (6, 2, 6, 9)],
               singletons=[(5, 7, 3), (9, 0, 5), (9, 4, 7)],
               chains=[(9, [(2, 2), (1, 2), (1, 5)],
                        [(1, 3), (1, 5), (2, 2)]),
                       (6, [(5, 5), (5, 1), (8, 1), (8, 2)],
                        [(5, 5), (7, 1), (8, 2)]),
                       (2, [(3, 11), (8, 11), (8, 3)],
                        [(3, 11), (5, 11), (8, 3)]),
                       (4, [(11, 1), (11, 3)], [(11, 1), (11, 3)])]),
  ]
  test = [
      generate(height=8, width=10, walls=[(2, 5, 2, 5), (4, 8, 4, 9)],
               singletons=[(1, 8, 4), (4, 0, 0), (6, 8, 7), (7, 1, 3)],
               chains=[(2, [(1, 1), (1, 4), (3, 4), (3, 6)],
                        [(1, 1), (1, 4), (3, 4), (3, 6)]),
                       (5, [(5, 2), (5, 4)], [(5, 2), (5, 4)])]),
      generate(height=12, width=12, walls=[(2, 5, 2, 10), (4, 7, 4, 11)],
               singletons=[(1, 10, 7), (4, 3, 6), (10, 10, 9)],
               chains=[(4, [(1, 1), (1, 6)], [(1, 1), (1, 6)]),
                       (3, [(3, 8), (3, 6), (8, 6), (8, 8)],
                        [(3, 8), (6, 6), (8, 6), (8, 8)]),
                       (2, [(7, 1), (7, 2), (10, 2), (10, 5)],
                        [(7, 1), (7, 2), (9, 2), (10, 4), (10, 5)])]),
  ]
  return {'train': train, 'test': test}
