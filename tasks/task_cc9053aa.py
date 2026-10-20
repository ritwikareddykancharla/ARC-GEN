# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ARC-GEN style generator for task cc9053aa.

Rule: the background is black (0) and holds a cyan (8) lattice. The lattice
is built from full wall rows and full wall columns. Some walls have single-cell
gaps, and some internal segments are deleted. Two maroon (9) endpoints touch
the lattice from outside. One or more orange (7) cells sit strictly inside the
lattice, either in a chamber or on a wall cell.

A cyan cell that is 4-adjacent to an orange cell may not be used. The output
recolours to maroon every cell of the optimal legal route between the two
endpoints. Optimal means fewest steps first, then fewest direction changes.
The first move is not a turn. Turns on the legs that leave and enter the
endpoints do count.

Scope: random scenes sample the following.
  * The number and spacing of wall rows and columns (2-4 cells apart).
  * The margins (1-2 cells).
  * Whole deleted internal segments and single-cell gaps.
  * The number and placement of oranges.
  * The placement of the endpoints.
Native oranges are non-adjacent and avoid wall intersections. Whole boundary
segments are not deleted, though single boundary gaps are possible. Explicit
scenes can exercise wider layouts. Cyan fragments may remain away from the
solution route; connectedness of the entire lattice is not required.
Default sides range from 7 to 21. A requested width or height may be any
integer from 7 to 30.

These are synthetic extensions beyond the fixtures:
  * sizes other than 9x7 and 9x9;
  * more than four walls per axis;
  * more than two oranges.

The answer is computed from the latent lattice. Every scene must have a unique
(steps, turns) optimum, so the reference's heap-order tie-break never matters.

The random sampler has two preferences, chosen per call:
  * Detour (85% of calls). Orange blocking must change the optimal
    (steps, turns) cost. The comparison is with a search where cyan cells
    next to an orange are allowed. Orange cells themselves stay impassable in
    that comparison. The change can be extra steps or only extra turns.
  * Tie-break (40% of calls). Several shortest-length legal routes must
    exist, so the fewest-turns rule decides the answer, as in the test
    fixture.
If the preferences cannot be met within 1000 attempts, they are relaxed for
the remaining 500 attempts. Uniqueness and a non-identity output are still
required.

Explicit scenes are rejected, never silently resolved, if they are ambiguous,
unroutable, trivial (an identity pair) or malformed. Malformed means any of
the following:
  * a size or coordinate is not an exact integer;
  * an endpoint is not outside the lattice and touching it;
  * an orange lies outside the lattice interior or has no cyan neighbour;
  * a removed cell is not a lattice cell;
  * the wall indices are invalid.
"""

import collections
import heapq
import random

import numpy as np

import common

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
MIN_SIDE = 7
MAX_SIDE = 30


def _as_int(v, name):
  """Returns v as int if it is an exact integer (bool, float, str rejected)."""
  if isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer)):
    raise ValueError("%s must be an integer, got %r" % (name, v))
  return int(v)


def _nbrs(y, x, height, width):
  out = []
  for dy, dx in DIRS:
    ny, nx = y + dy, x + dx
    if 0 <= ny < height and 0 <= nx < width:
      out.append((ny, nx))
  return out


def _allowed(grid, a, b, block):
  """Walkable cells: cyan cells, minus orange-adjacent ones if block is set.

  The two endpoints are always walkable. Orange cells are never walkable.
  """
  height, width = len(grid), len(grid[0])
  allowed = set()
  for y in range(height):
    for x in range(width):
      if grid[y][x] != 8:
        continue
      if block and any(grid[ny][nx] == 7
                       for ny, nx in _nbrs(y, x, height, width)):
        continue
      allowed.add((y, x))
  allowed.add(a)
  allowed.add(b)
  return allowed


def _best_route(grid, a, b, block):
  """Returns (best_cost, number_of_optimal_routes, one_route) on the scene."""
  allowed = _allowed(grid, a, b, block)
  start = (a[0], a[1], -1)
  cost = {start: (0, 0)}
  heap = [(0, 0, start)]
  order = []
  while heap:
    s, t, st = heapq.heappop(heap)
    if cost[st] != (s, t):
      continue
    order.append(st)
    y, x, d = st
    if (y, x) == b:
      continue
    for nd, (dy, dx) in enumerate(DIRS):
      p = (y + dy, x + dx)
      if p not in allowed:
        continue
      ns = (p[0], p[1], nd)
      c = (s + 1, t + (1 if d != -1 and nd != d else 0))
      if ns not in cost or c < cost[ns]:
        cost[ns] = c
        heapq.heappush(heap, (c[0], c[1], ns))
  ends = [st for st in cost if st[:2] == b]
  if not ends:
    return None, 0, None
  best = min(cost[e] for e in ends)
  # Count the optimal paths. Every move adds one step, so the pop order is a
  # valid topological order of the optimal-cost DAG.
  cnt = {start: 1}
  pred = {}
  for st in order:
    y, x, d = st
    if (y, x) == b or st not in cnt:
      continue
    s, t = cost[st]
    for nd, (dy, dx) in enumerate(DIRS):
      p = (y + dy, x + dx)
      if p not in allowed:
        continue
      ns = (p[0], p[1], nd)
      c = (s + 1, t + (1 if d != -1 and nd != d else 0))
      if cost.get(ns) == c:
        cnt[ns] = cnt.get(ns, 0) + cnt[st]
        pred.setdefault(ns, st)
  best_ends = [e for e in ends if cost[e] == best]
  total = sum(cnt.get(e, 0) for e in best_ends)
  route = []
  cur = best_ends[0]
  while cur is not None:
    route.append(cur[:2])
    cur = pred.get(cur)
  route.reverse()
  return best, total, route


def _shortest_count(grid, a, b):
  """Number of minimum-step legal routes, ignoring turns (BFS counting)."""
  allowed = _allowed(grid, a, b, True)
  dist = {a: 0}
  cnt = {a: 1}
  queue = collections.deque([a])
  while queue:
    p = queue.popleft()
    if p == b:
      continue
    for dy, dx in DIRS:
      n = (p[0] + dy, p[1] + dx)
      if n not in allowed:
        continue
      if n not in dist:
        dist[n] = dist[p] + 1
        cnt[n] = cnt[p]
        queue.append(n)
      elif dist[n] == dist[p] + 1:
        cnt[n] += cnt[p]
  return cnt.get(b, 0)


def _draw(width, height, wall_rows, wall_cols, removed, oranges, endpoints):
  grid = common.grid(width, height, 0)
  r0, r1 = wall_rows[0], wall_rows[-1]
  c0, c1 = wall_cols[0], wall_cols[-1]
  for r in wall_rows:
    for c in range(c0, c1 + 1):
      grid[r][c] = 8
  for c in wall_cols:
    for r in range(r0, r1 + 1):
      grid[r][c] = 8
  for r, c in removed:
    grid[r][c] = 0
  for r, c in oranges:
    grid[r][c] = 7
  for r, c in endpoints:
    grid[r][c] = 9
  return grid


def _paint(grid, route):
  out = [row[:] for row in grid]
  for y, x in route:
    out[y][x] = 9
  return out


def _axis(size):
  """Samples wall positions along one axis. Returns (walls, size) or None."""
  if size is None:
    n = random.choice([2, 3, 3, 4, 4, 5])
    walls = [random.randint(1, 2)]
    for _ in range(n - 1):
      walls.append(walls[-1] + random.randint(2, 4))
    total = walls[-1] + 1 + random.randint(1, 2)
    if total < MIN_SIDE:
      return None
    return walls, total
  lo, hi = random.randint(1, 2), random.randint(1, 2)
  span = size - lo - hi - 1
  if span < 2:
    return None
  kmin = (span + 3) // 4
  kmax = min(span // 2, 8)
  if kmin > kmax:
    return None
  k = random.randint(kmin, kmax)
  gaps = [2] * k
  extra = span - 2 * k
  while extra > 0:
    i = random.choice([j for j in range(k) if gaps[j] < 4])
    gaps[i] += 1
    extra -= 1
  walls = [lo]
  for g in gaps:
    walls.append(walls[-1] + g)
  return walls, size


def _cells(cells, height, width, name):
  out = []
  if not isinstance(cells, (list, tuple)):
    raise ValueError("%s must be a list of cells" % name)
  for p in cells:
    if not isinstance(p, (list, tuple)) or len(p) != 2:
      raise ValueError("%s cell %r must be a (row, col) pair" % (name, p))
    y = _as_int(p[0], name + " row")
    x = _as_int(p[1], name + " col")
    if not (0 <= y < height and 0 <= x < width):
      raise ValueError("%s cell %r is outside the grid" % (name, (y, x)))
    out.append((y, x))
  if len(set(out)) != len(out):
    raise ValueError("duplicate %s cells" % name)
  return out


def _explicit(width, height, wall_rows, wall_cols, removed, oranges,
              endpoints):
  width = _as_int(width, "width")
  height = _as_int(height, "height")
  if not (1 <= width <= MAX_SIDE and 1 <= height <= MAX_SIDE):
    raise ValueError("width and height must be in [1, %d]" % MAX_SIDE)
  if not isinstance(wall_rows, (list, tuple)) or not isinstance(wall_cols, (list, tuple)):
    raise ValueError("wall rows and columns must be lists")
  wall_rows = sorted(_as_int(r, "wall row") for r in wall_rows)
  wall_cols = sorted(_as_int(c, "wall col") for c in wall_cols)
  if len(wall_rows) < 2 or len(wall_cols) < 2:
    raise ValueError("need at least two wall rows and two wall columns")
  for walls in (wall_rows, wall_cols):
    if any(walls[i + 1] - walls[i] < 2 for i in range(len(walls) - 1)):
      raise ValueError("wall indices must be distinct and non-adjacent")
  if (wall_rows[0] < 0 or wall_rows[-1] >= height or wall_cols[0] < 0 or
      wall_cols[-1] >= width):
    raise ValueError("walls lie outside the grid")
  r0, r1, c0, c1 = wall_rows[0], wall_rows[-1], wall_cols[0], wall_cols[-1]
  removed = _cells(removed or [], height, width, "removed")
  oranges = _cells(oranges, height, width, "orange")
  endpoints = _cells(endpoints, height, width, "endpoint")
  if len(endpoints) != 2:
    raise ValueError("exactly two distinct endpoints are required")
  if not oranges:
    raise ValueError("at least one orange cell is required")
  for r, c in removed:
    on_row = r in wall_rows and c0 <= c <= c1
    on_col = c in wall_cols and r0 <= r <= r1
    if not (on_row or on_col):
      raise ValueError("removed cell %r is not a lattice cell" % ((r, c),))
  if set(removed) & set(oranges):
    raise ValueError("orange cells must not also be listed as removed")
  for r, c in oranges:
    if not (r0 < r < r1 and c0 < c < c1):
      raise ValueError("orange %r is not strictly inside the lattice" %
                       ((r, c),))
  for r, c in endpoints:
    if r0 <= r <= r1 and c0 <= c <= c1:
      raise ValueError("endpoint %r is not outside the lattice" % ((r, c),))
  grid = _draw(width, height, wall_rows, wall_cols, removed, oranges,
               endpoints)
  for r, c in oranges:
    if not any(grid[ny][nx] == 8 for ny, nx in _nbrs(r, c, height, width)):
      raise ValueError("orange %r has no cyan neighbour" % ((r, c),))
  for r, c in endpoints:
    if not any(grid[ny][nx] == 8 for ny, nx in _nbrs(r, c, height, width)):
      raise ValueError("endpoint %r does not touch the lattice" % ((r, c),))
  a, b = sorted(endpoints)
  best, count, route = _best_route(grid, a, b, True)
  if best is None:
    raise ValueError("explicit scene has no legal route")
  if count != 1:
    raise ValueError("explicit scene has no unique (steps, turns) route")
  if len(route) < 3:
    raise ValueError("explicit scene is trivial (no cyan cell recoloured)")
  return {"input": grid, "output": _paint(grid, route)}


def generate(width=None, height=None, wall_rows=None, wall_cols=None,
             removed=None, oranges=None, endpoints=None, num_oranges=None):
  """Builds one input/output pair.

  Args:
    width: grid width, an exact int. Explicit scenes require it (1..30). In
      random mode it fixes the width (7..30), and the lattice is sampled to
      fit it.
    height: grid height. Same semantics as width.
    wall_rows: rows of full cyan horizontal walls. The first and last rows
      bound the lattice. Supplying this selects explicit mode. Explicit mode
      then also needs wall_cols, oranges, endpoints, width and height.
    wall_cols: columns of full cyan vertical walls. The first and last columns
      bound the lattice.
    removed: lattice cells cleared to black (gaps or deleted segments).
      Explicit scenes only.
    oranges: orange obstacle cells strictly inside the lattice. Explicit mode
      only.
    endpoints: the two maroon cells just outside the lattice. Explicit mode
      only.
    num_oranges: exact int in 1..4 (bool rejected). In random mode it sets the
      number of orange cells. In explicit mode it must be None or equal to
      len(oranges).
  """
  if num_oranges is not None:
    num_oranges = _as_int(num_oranges, "num_oranges")
    if not 1 <= num_oranges <= 4:
      raise ValueError("num_oranges must be in [1, 4]")
  scene = [wall_rows, wall_cols, oranges, endpoints]
  if any(v is not None for v in scene):
    if any(v is None for v in scene) or width is None or height is None:
      raise ValueError("explicit scenes need width, height, wall_rows, "
                       "wall_cols, oranges and endpoints")
    if not isinstance(oranges, (list, tuple)):
      raise ValueError("oranges must be a list of cells")
    if num_oranges is not None and num_oranges != len(oranges):
      raise ValueError("num_oranges conflicts with oranges")
    return _explicit(width, height, wall_rows, wall_cols, removed, oranges,
                     endpoints)
  if removed is not None:
    raise ValueError("removed is only meaningful for explicit scenes")
  if width is not None:
    width = _as_int(width, "width")
  if height is not None:
    height = _as_int(height, "height")
  for name, v in (("width", width), ("height", height)):
    if v is not None and not MIN_SIDE <= v <= MAX_SIDE:
      raise ValueError("%s must be in [%d, %d]" % (name, MIN_SIDE, MAX_SIDE))

  require_detour = random.random() < 0.85
  require_tiebreak = random.random() < 0.4
  for attempt in range(1500):
    strict = attempt < 1000
    ax_r = _axis(height)
    ax_c = _axis(width)
    if ax_r is None or ax_c is None:
      continue
    rows, h = ax_r
    cols, w = ax_c
    if h > MAX_SIDE or w > MAX_SIDE:
      continue
    nr, nc = len(rows), len(cols)
    if nr + nc < 5 and random.random() < 0.8:
      continue
    r0, r1, c0, c1 = rows[0], rows[-1], cols[0], cols[-1]
    rem = set()
    segments = []
    for i, r in enumerate(rows):
      boundary = i in (0, nr - 1)
      for j in range(nc - 1):
        segments.append(
            (boundary, [(r, c) for c in range(cols[j] + 1, cols[j + 1])]))
    for i, c in enumerate(cols):
      boundary = i in (0, nc - 1)
      for j in range(nr - 1):
        segments.append(
            (boundary, [(r, c) for r in range(rows[j] + 1, rows[j + 1])]))
    for boundary, cells in segments:
      u = random.random()
      if not boundary and u < 0.22:
        rem.update(cells)
      elif u < (0.1 if boundary else 0.4):
        rem.add(random.choice(cells))
    base = _draw(w, h, rows, cols, sorted(rem), [], [])
    # Drop isolated cyan leftovers.
    for y in range(h):
      for x in range(w):
        if base[y][x] == 8 and not any(base[ny][nx] == 8
                                       for ny, nx in _nbrs(y, x, h, w)):
          base[y][x] = 0
    # Orange candidates: interior non-intersection cells next to cyan.
    cands = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)
             if not (r in rows and c in cols) and
             any(base[ny][nx] == 8 for ny, nx in _nbrs(r, c, h, w))]
    n_or = num_oranges or random.choice([1, 1, 2, 2, 2, 3])
    random.shuffle(cands)
    ors = []
    for p in cands:
      if len(ors) == n_or:
        break
      if any(abs(p[0] - q[0]) + abs(p[1] - q[1]) <= 1 for q in ors):
        continue
      ors.append(p)
    if len(ors) != n_or:
      continue
    for r, c in ors:
      base[r][c] = 7
    # An orange drawn on a wall cell can strip another orange of its only
    # cyan neighbour. Every orange must still border cyan.
    if not all(any(base[ny][nx] == 8 for ny, nx in _nbrs(r, c, h, w))
               for r, c in ors):
      continue
    outs = set()
    for y in range(r0, r1 + 1):
      for x in range(c0, c1 + 1):
        if base[y][x] != 8:
          continue
        if y == r0:
          outs.add((y - 1, x))
        if y == r1:
          outs.add((y + 1, x))
        if x == c0:
          outs.add((y, x - 1))
        if x == c1:
          outs.add((y, x + 1))
    outs = sorted(outs)
    if len(outs) < 2:
      continue
    for _ in range(10):
      a, b = sorted(random.sample(outs, 2))
      if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 3:
        continue
      grid = [row[:] for row in base]
      grid[a[0]][a[1]] = 9
      grid[b[0]][b[1]] = 9
      best, count, route = _best_route(grid, a, b, True)
      if best is None or count != 1 or len(route) < 4:
        continue
      if require_detour and strict:
        unblocked, _, _ = _best_route(grid, a, b, False)
        if not best > unblocked:
          continue
      if require_tiebreak and strict:
        if _shortest_count(grid, a, b) < 2:
          continue
      return {"input": grid, "output": _paint(grid, route)}
  raise RuntimeError("failed to build a scene for the requested controls")


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=9, height=7, wall_rows=[1, 3, 5], wall_cols=[1, 3, 5, 7],
               removed=[(2, 3)], oranges=[(3, 4), (3, 6)],
               endpoints=[(1, 8), (6, 7)]),
      generate(width=9, height=7, wall_rows=[1, 3, 5], wall_cols=[1, 3, 5, 7],
               removed=[(1, 4), (3, 2), (3, 6), (4, 3), (4, 5)],
               oranges=[(2, 4)], endpoints=[(3, 0), (3, 8)]),
      generate(width=9, height=9, wall_rows=[1, 3, 5, 7], wall_cols=[1, 4, 7],
               removed=[(2, 4), (6, 4)], oranges=[(2, 2), (6, 6)],
               endpoints=[(0, 4), (8, 4)]),
  ]
  test = [
      generate(width=9, height=9, wall_rows=[1, 3, 5, 7],
               wall_cols=[1, 3, 5, 7], removed=[], oranges=[(2, 4), (4, 4)],
               endpoints=[(0, 1), (0, 7)]),
  ]
  return {"train": train, "test": test}
