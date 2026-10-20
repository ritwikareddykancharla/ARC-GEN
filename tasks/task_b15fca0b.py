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

"""ARC-GEN style generator for task b15fca0b.

Rule: the grid has a black (0) background, blue (1) walls and exactly two red
(2) cells. The output paints yellow (4) every cell of the shortest 4-connected
path between the two red cells through empty cells. The red cells keep their
colour. Nothing else changes.

Scene model (stated in a "comb" frame, which may be transposed):
  * Columns alternate between open lanes and wall blocks:
    lane_0, wall_1, lane_1, ..., wall_n, lane_n. Interior lanes are exactly 1
    column wide. The two outer lanes may be wider (1 or 2 when sampled).
    Each wall block is 1 or 2 columns thick when sampled.
  * Each wall block spans the full height. It is solid except for one or
    more openings, which are row intervals. An opening can sit at the top,
    at the bottom or in the middle. A wall can also have openings at both
    ends; one of them is then a distractor.
  * Optional lane blocks are extra wall segments drawn across the full width
    of a lane. Random mode anchors them at the top or bottom edge, as dead-end
    caps like the capped middle lane in one training pair. Explicit mode also
    accepts mid-lane intervals. Blocks only remove cells, and the drawn path
    is checked to avoid them, so they never change the answer.
  * One red cell sits in lane_0 and the other sits in lane_n.

The path crosses each wall along one row of one of its openings and moves
vertically inside lanes. Leftward detours are strictly longer, so the
horizontal length is fixed. The shortest path is therefore given by the
crossing rows x_1..x_n that minimise sum |x_{k+1} - x_k|, where x_0 is the
start row and x_{n+1} the end row. A small 1-D dynamic programme picks these
rows from the latent openings and counts the optimal choices.

A scene is accepted only if exactly one choice is optimal. In a wide outer
lane the red cell must sit on the inner column or level with its crossing
row; otherwise several staircase paths would tie. A row change inside a thick
wall opening would imply an equally cheap alternative crossing row, and the
uniqueness test excludes that. Under these conditions the shortest path is
unique. Lane blocks only delete cells, so a path that survives them stays the
unique shortest one. The answer is drawn explicitly as a polyline from the
latent crossing rows; no solver is run on the input.

In random mode the endpoint rows are sometimes snapped level with their
crossing row, as in the test pair. Distractor lane caps are added after the
base scene is certified. Any cap that would cut the path is dropped instead
of rejecting the scene.

Sizes: comb height 3..30 (default sampling 4..18). Random mode takes 1..14
walls (default sampling 1..7). Explicit mode is bounded only by the total
width, which is always kept at most 30. Grids larger than the fixtures (10x10)
and wall counts above 4 are synthetic extensions of the same corridor
mechanism.

All integer controls must be genuine Python ints. bool and float values are
rejected with ValueError, and so are malformed structures.
"""

import random

import common

MAX_WALLS = 14


def _is_int(v):
  """True for genuine integers (bool is excluded)."""
  return isinstance(v, int) and not isinstance(v, bool)


def _int_seq(value, length, name):
  """Return value as a tuple of ints of the given length, else ValueError."""
  if not isinstance(value, (list, tuple)):
    raise ValueError("%s must be a list or tuple" % name)
  if length is not None and len(value) != length:
    raise ValueError("%s must have %d entries" % (name, length))
  for v in value:
    if not _is_int(v):
      raise ValueError("%s entries must be integers" % name)
  return tuple(value)


def _normalise_walls(walls):
  """Check and normalise the explicit wall description."""
  if not isinstance(walls, (list, tuple)):
    raise ValueError("walls must be a list")
  out = []
  for w in walls:
    if not isinstance(w, (list, tuple)) or len(w) != 2:
      raise ValueError("each wall must be (thickness, openings)")
    thick, openings = w
    if not _is_int(thick):
      raise ValueError("wall thickness must be an integer")
    if not isinstance(openings, (list, tuple)):
      raise ValueError("wall openings must be a list")
    ops = [_int_seq(o, 2, "opening") for o in openings]
    out.append((thick, ops))
  return out


def _layers(height, walls):
  """Return the sorted open rows of every wall, or None if malformed."""
  layers = []
  for thick, openings in walls:
    if thick < 1:
      return None
    rows = set()
    for lo, hi in openings:
      if not 0 <= lo <= hi < height:
        return None
      rows.update(range(lo, hi + 1))
    if not rows or len(rows) == height:
      return None
    layers.append(sorted(rows))
  return layers


def _crossings(start_row, layers, end_row):
  """Return the unique optimal crossing rows, or None if absent/ambiguous."""
  prev = {start_row: (0, 1, None)}
  history = [prev]
  for layer in layers + [[end_row]]:
    cur = {}
    for x in layer:
      best, cnt, pred = None, 0, None
      for p, (c, k, _) in prev.items():
        v = c + abs(x - p)
        if best is None or v < best:
          best, cnt, pred = v, k, p
        elif v == best:
          cnt += k
      cur[x] = (best, min(cnt, 2), pred)
    history.append(cur)
    prev = cur
  if prev[end_row][1] != 1:
    return None
  xs = []
  x = end_row
  for idx in range(len(history) - 1, 1, -1):
    x = history[idx][x][2]
    xs.append(x)
  xs.reverse()
  return xs


def _build(height, lane_widths, walls, start, end, transpose,
           lane_blocks=None):
  """Build the input/output pair from latent parameters; None if invalid."""
  n = len(walls)
  if n < 1 or len(lane_widths) != n + 1:
    return None
  if height < 3 or height > 30:
    return None
  if any(w < 1 for w in lane_widths):
    return None
  # Interior lanes wider than 1 would allow staircase ties the DP ignores.
  if any(w != 1 for w in lane_widths[1:-1]):
    return None
  layers = _layers(height, walls)
  if layers is None:
    return None
  lane_cols, wall_cols, c = [], [], 0
  for i in range(n):
    lane_cols.append(c)
    c += lane_widths[i]
    wall_cols.append(c)
    c += walls[i][0]
  lane_cols.append(c)
  c += lane_widths[n]
  width = c
  if width > 30:
    return None
  sr, so = start
  er, eo = end
  if not (0 <= sr < height and 0 <= so < lane_widths[0]):
    return None
  if not (0 <= er < height and 0 <= eo < lane_widths[n]):
    return None
  xs = _crossings(sr, layers, er)
  if xs is None:
    return None
  # Wide outer lanes: an endpoint away from the wall must be level with the
  # crossing, otherwise several staircase paths would tie.
  if so != lane_widths[0] - 1 and sr != xs[0]:
    return None
  if eo != 0 and er != xs[-1]:
    return None
  grid = common.grid(width, height, 0)
  for i, (t, _) in enumerate(walls):
    open_rows = set(layers[i])
    for r in range(height):
      if r not in open_rows:
        for dc in range(t):
          grid[r][wall_cols[i] + dc] = 1
  for li, lo, hi in (lane_blocks or []):
    if not (0 <= li <= n and 0 <= lo <= hi < height):
      return None
    for r in range(lo, hi + 1):
      for dc in range(lane_widths[li]):
        grid[r][lane_cols[li] + dc] = 1
  s = (sr, lane_cols[0] + so)
  e = (er, lane_cols[n] + eo)
  if grid[s[0]][s[1]] != 0 or grid[e[0]][e[1]] != 0:
    return None
  grid[s[0]][s[1]] = 2
  grid[e[0]][e[1]] = 2
  out = [row[:] for row in grid]
  cells = []
  pos = [s[0], s[1]]

  def walk(tr, tc):
    while pos[0] != tr:
      pos[0] += 1 if tr > pos[0] else -1
      cells.append((pos[0], pos[1]))
    while pos[1] != tc:
      pos[1] += 1 if tc > pos[1] else -1
      cells.append((pos[0], pos[1]))

  for i in range(n):
    walk(xs[i], pos[1])
    walk(xs[i], lane_cols[i + 1])
  walk(er, pos[1])
  walk(er, e[1])
  if not cells or cells[-1] != e:
    return None
  for r, cc in cells[:-1]:
    if out[r][cc] != 0:
      return None
    out[r][cc] = 4
  if transpose:
    grid = [list(col) for col in zip(*grid)]
    out = [list(col) for col in zip(*out)]
  return {"input": grid, "output": out}


def _sample_openings(height, kind):
  """Sample the opening intervals of one wall of the given kind."""
  maxk = max(1, (height - 2) // 2)
  if kind == "top":
    k = random.randint(1, maxk)
    return [(0, k - 1)]
  if kind == "bottom":
    k = random.randint(1, maxk)
    return [(height - k, height - 1)]
  if kind == "middle":
    k = random.randint(1, max(1, min(2, height - 3)))
    lo = random.randint(1, height - 1 - k)
    return [(lo, lo + k - 1)]
  kd = max(1, (height - 2) // 3)
  k1, k2 = random.randint(1, kd), random.randint(1, kd)
  return [(0, k1 - 1), (height - k2, height - 1)]


def _sample_scene(height, num_walls, transpose):
  """Sample latent comb parameters (endpoint offsets are chosen later)."""
  if height is None:
    height = random.randint(4, 18)
  n = num_walls if num_walls is not None else random.randint(1, 7)
  lanes = [random.choice([1, 1, 1, 2])] + [1] * (n - 1)
  lanes.append(random.choice([1, 1, 1, 2]))
  walls = []
  side = random.choice(["top", "bottom"])
  for i in range(n):
    roll = random.random()
    if i == 0 or roll < 0.65:
      kind = side if i == 0 else ("bottom" if side == "top" else "top")
      side = kind
    elif roll < 0.75:
      kind = side
    elif roll < 0.87:
      kind = "middle"
    else:
      kind = "double"
    thick = 1 if random.random() < 0.8 else 2
    walls.append((thick, _sample_openings(height, kind)))
  # Keep the total width within 30 by thinning walls and outer lanes.
  # With n <= 14 the minimum width 2n+1 <= 29, so this always terminates.
  while sum(lanes) + sum(t for t, _ in walls) > 30:
    thick_idx = [i for i, (t, _) in enumerate(walls) if t > 1]
    if thick_idx:
      i = random.choice(thick_idx)
      walls[i] = (1, walls[i][1])
    elif lanes[0] > 1:
      lanes[0] = 1
    else:
      lanes[-1] = 1
  rows = (random.randint(0, height - 1), random.randint(0, height - 1))
  blocks = []
  for _ in range(random.choice([0, 1, 1, 2, 2, 3])):
    li = random.randint(0, n)
    k = random.randint(1, max(1, height // 3))
    if random.random() < 0.5:
      blocks.append((li, 0, k - 1))
    else:
      blocks.append((li, height - k, height - 1))
  if transpose is None:
    transpose = random.random() < 0.5
  return height, lanes, walls, rows, bool(transpose), blocks


def generate(height=None, lane_widths=None, walls=None, start=None, end=None,
             transpose=None, lane_blocks=None, num_walls=None):
  """Generate one input/output pair.

  Two modes are supported.

  Explicit mode (walls given): height, lane_widths, walls, start and end are
  all required; transpose defaults to False and lane_blocks to none. The
  number of walls is bounded only by the total width of 30.

  Random mode (walls is None): height, num_walls and transpose act as
  optional controls; every other aspect is sampled. Passing lane_widths,
  start, end or lane_blocks without walls is rejected with ValueError.

  Args:
    height: number of rows in the comb frame (int, 3..30).
    lane_widths: n+1 lane widths, left to right. Interior lanes must be 1.
    walls: n pairs (thickness, [(lo, hi), ...]). Each gives a wall block's
      thickness and its open row intervals (inclusive, inside the grid).
    start: (row, column offset inside lane 0) of the first red cell.
    end: (row, column offset inside the last lane) of the second red cell.
    transpose: None or bool. If True, the comb frame is transposed
      (horizontal walls).
    lane_blocks: optional list of (lane_index, lo, hi) wall segments drawn
      across the full width of a lane. These are dead-end distractors. Any
      interval is accepted, but the path must avoid them.
    num_walls: number of wall blocks n (int, 1..14) in random mode; in
      explicit mode it must equal len(walls) if given.
  """
  if transpose is not None and not isinstance(transpose, bool):
    raise ValueError("transpose must be None or a bool")
  if height is not None and not _is_int(height):
    raise ValueError("height must be an integer")
  if num_walls is not None and not _is_int(num_walls):
    raise ValueError("num_walls must be an integer")
  if walls is not None:
    wl = _normalise_walls(walls)
    if num_walls is not None and num_walls != len(wl):
      raise ValueError("num_walls disagrees with len(walls)")
    if height is None or lane_widths is None or start is None or end is None:
      raise ValueError("explicit mode needs height, lane_widths, start, end")
    lanes = list(_int_seq(lane_widths, None, "lane_widths"))
    st = _int_seq(start, 2, "start")
    en = _int_seq(end, 2, "end")
    blocks = None
    if lane_blocks is not None:
      if not isinstance(lane_blocks, (list, tuple)):
        raise ValueError("lane_blocks must be a list")
      blocks = [_int_seq(b, 3, "lane_block") for b in lane_blocks]
    result = _build(height, lanes, wl, st, en, bool(transpose), blocks)
    if result is None:
      raise ValueError("latent parameters give an invalid or ambiguous scene")
    return result
  if (lane_widths is not None or start is not None or end is not None
      or lane_blocks is not None):
    raise ValueError("lane_widths/start/end/lane_blocks require explicit walls")
  if height is not None and not 3 <= height <= 30:
    raise ValueError("height must be in 3..30")
  if num_walls is not None and not 1 <= num_walls <= MAX_WALLS:
    raise ValueError("num_walls must be in 1..%d" % MAX_WALLS)
  for _ in range(2000):
    h, lanes, wl, rows, tr, blocks = _sample_scene(height, num_walls,
                                                  transpose)
    layers = _layers(h, wl)
    if layers is None:
      continue
    sr, er = rows
    xs = _crossings(sr, layers, er)
    if xs is None:
      continue
    # Sometimes snap an endpoint level with its crossing row (test-like).
    if random.random() < 0.35:
      xs2 = _crossings(xs[0], layers, er)
      if xs2 is not None and xs2[0] == xs[0]:
        sr, xs = xs[0], xs2
    if random.random() < 0.35:
      xs2 = _crossings(sr, layers, xs[-1])
      if xs2 is not None and xs2[-1] == xs[-1]:
        er, xs = xs[-1], xs2
    so = lanes[0] - 1
    if lanes[0] > 1 and sr == xs[0]:
      so = random.randint(0, lanes[0] - 1)
    eo = 0
    if lanes[-1] > 1 and er == xs[-1]:
      eo = random.randint(0, lanes[-1] - 1)
    base = _build(h, lanes, wl, (sr, so), (er, eo), tr, [])
    if base is None:
      continue
    kept = []
    for b in blocks:
      trial = _build(h, lanes, wl, (sr, so), (er, eo), tr, kept + [b])
      if trial is not None:
        kept.append(b)
        base = trial
    return base
  raise RuntimeError("could not sample an unambiguous scene")


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(height=6, lane_widths=[1, 1, 2],
               walls=[(1, [(0, 0)]), (1, [(5, 5)])],
               start=(5, 0), end=(0, 0), transpose=True),
      generate(height=5, lane_widths=[1, 1, 1],
               walls=[(1, [(0, 1)]), (1, [(3, 4)])],
               start=(4, 0), end=(0, 0), transpose=False),
      generate(height=6, lane_widths=[1, 1, 2],
               walls=[(1, [(4, 5)]), (1, [(0, 2)])],
               start=(0, 0), end=(5, 0), transpose=True),
      generate(height=10, lane_widths=[1, 1, 1, 1, 1],
               walls=[(1, [(0, 3)]), (2, [(5, 9)]), (1, [(0, 3)]),
                      (1, [(5, 9)])],
               start=(9, 0), end=(0, 0), transpose=False),
      generate(height=5, lane_widths=[1, 1, 1],
               walls=[(1, [(4, 4)]), (1, [(4, 4)])],
               start=(0, 0), end=(0, 0), transpose=False,
               lane_blocks=[(1, 0, 0)]),
  ]
  test = [
      generate(height=10, lane_widths=[1, 1, 1, 1, 2],
               walls=[(1, [(5, 9)]), (1, [(0, 1)]), (1, [(5, 5)]),
                      (1, [(0, 0), (9, 9)])],
               start=(0, 0), end=(0, 1), transpose=False),
  ]
  return {"train": train, "test": test}
