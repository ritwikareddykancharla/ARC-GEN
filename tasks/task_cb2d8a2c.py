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

"""ARC task cb2d8a2c: a green path weaves around red bars.

Rule: the background is 8. One green (3) seed sits on a grid edge, away from
the corners. Straight red (2) bars run perpendicular to the seed's direction.
Each bar is attached to exactly one side edge. Each bar has n blue (1) cells
that alternate with red, starting at the attached end. In the output every 1
becomes 2. A green path leaves the seed and runs straight inward. At each bar
the clearance is k = n + 1. The path stops k cells before the bar. It then
moves sideways until it is k cells past the bar's free end. Then it resumes
its original direction. After the last bar it runs to the opposite edge.

Scope: all four seed edges are supported. Each scene is built in a canonical
frame where the path runs downwards. It is then rotated or reflected into
place. There are 1-4 bars by default, and up to 7 if requested and the length
allows. Each sampled bar has 1-4 ones. Consecutive bars usually alternate
sides, but they may share a side. The lateral size is 7-30 by default and
5-30 if given. The length runs from the tight packing of the bar layout up
to 30, and the slack is spread over the leading, inner and trailing gaps.
Sizes beyond the fixture range are synthetic extensions of the same rule.
A sidestep target may land on the grid border (lateral coordinate 0 or
width-1); the first test fixture includes such an intermediate detour.
Ending at a far-edge corner is a synthetic extension not shown in fixtures.
Explicit bars may contain more than four blue markers when space permits;
the sampler caps this at four. Floating bars are not generated.
Neither are distractor bars that the path never meets.
"""

import random

import common


_DIRECTIONS = ("down", "up", "right", "left")
_BAR_WEIGHTS = (1, 2, 2, 3, 3, 3, 4, 4)
_MAX_ONES = 4


def _int(name, v):
  """Rejects bools and non-integers explicitly."""
  if isinstance(v, bool) or not isinstance(v, int):
    raise ValueError(name + " must be an integer")
  return v


def _orient(canon, direction, length, width):
  """Maps a canonical grid (length rows, width cols; path moves down)."""
  if direction in ("down", "up"):
    g = common.grid(width, length, 8)
  else:
    g = common.grid(length, width, 8)
  for r in range(length):
    for c in range(width):
      v = canon[r][c]
      if direction == "down":
        g[r][c] = v
      elif direction == "up":
        g[length - 1 - r][c] = v
      elif direction == "right":
        g[c][r] = v
      else:
        g[c][length - 1 - r] = v
  return g


def _render(direction, length, width, seed, bars):
  """Draws input and output from latent parameters in the canonical frame."""
  canon_in = [[8] * width for _ in range(length)]
  canon_in[0][seed] = 3
  for (row, side, size, ones) in bars:
    if side == "L":
      cols, edge, step = range(size), 0, 1
    else:
      cols, edge, step = range(width - size, width), width - 1, -1
    for c in cols:
      canon_in[row][c] = 2
    for j in range(ones):
      canon_in[row][edge + step * 2 * j] = 1
  canon_out = [[2 if v == 1 else v for v in r] for r in canon_in]
  y, x = 0, seed
  for (row, side, size, ones) in bars:
    k = ones + 1
    stop = row - k
    while y < stop:
      y += 1
      canon_out[y][x] = 3
    target = size - 1 + k if side == "L" else width - size - k
    st = 1 if target > x else -1
    while x != target:
      x += st
      canon_out[y][x] = 3
  while y < length - 1:
    y += 1
    canon_out[y][x] = 3
  return (_orient(canon_in, direction, length, width),
          _orient(canon_out, direction, length, width))


def _options(ones, x, width):
  """Free-end ranges for a bar with `ones` 1s when the path is at column x.

  The bar must cover x, must hold its alternating 1s, and must be at least
  2 cells long. The sidestep target (free end +/- k) must stay inside the
  grid. Together these keep the bar off the opposite side edge.
  """
  k = ones + 1
  opts = []
  lo, hi = max(x, 2 * ones - 2, 1), width - 1 - k
  if lo <= hi:
    opts.append(("L", lo, hi))
  lo, hi = k, min(x, width - 2 * ones + 1, width - 2)
  if lo <= hi:
    opts.append(("R", lo, hi))
  return opts


def _check(length, width, seed, bars):
  """Validates explicit or sampled latent parameters; returns bar tuples.

  The first sidestep row must be at least 1. Every later sidestep row must
  be at least 2 rows past the previous bar, so the green path never touches
  a bar. Bars need at least 2 cells and must hold their alternating 1s.
  """
  _int("length", length)
  _int("width", width)
  _int("seed", seed)
  if not (5 <= length <= 30 and 5 <= width <= 30):
    raise ValueError("length and width must be in 5..30")
  if not 1 <= seed <= width - 2:
    raise ValueError("seed must avoid the corners")
  if not isinstance(bars, (list, tuple)) or not bars:
    raise ValueError("at least one bar is required")
  out, x, prev = [], seed, None
  for bar in bars:
    if not isinstance(bar, (list, tuple)) or len(bar) != 4:
      raise ValueError("each bar must be (row, side, size, ones)")
    row, side, size, ones = bar
    _int("bar row", row)
    _int("bar size", size)
    _int("bar ones", ones)
    if not isinstance(side, str) or side not in ("L", "R"):
      raise ValueError("bar side must be 'L' or 'R'")
    k = ones + 1
    if ones < 1 or size < max(2, 2 * ones - 1):
      raise ValueError("bar must have >= 2 cells and hold its alternating 1s")
    floor = 1 if prev is None else prev + 2
    if row - k < floor:
      raise ValueError("bar too close to the seed or the previous bar")
    if side == "L":
      lo_c, hi_c, target = 0, size - 1, size - 1 + k
    else:
      lo_c, hi_c, target = width - size, width - 1, width - size - k
    if not lo_c <= x <= hi_c:
      raise ValueError("path must meet every bar")
    if not 0 <= target < width:
      raise ValueError("sidestep would leave the grid")
    out.append((row, side, size, ones))
    x, prev = target, row
  if prev > length - 2:
    raise ValueError("last bar must leave room before the far edge")
  return out


def _sample(length, width, seed, num_bars):
  """Constructs a random layout that honours the given constraints.

  Each step is constructive. A bar with a single 1 is always laterally
  feasible when width >= 5. The length budget reserves 4 rows per remaining
  bar. So no rejection loop or fallback scene is needed.
  """
  if length is not None and not 5 <= length <= 30:
    raise ValueError("length must be in 5..30")
  if width is None:
    lo = 7 if seed is None else max(7, seed + 2)
    if lo > 30:
      raise ValueError("seed too large for any width")
    width = random.randint(lo, 30)
  if not 5 <= width <= 30:
    raise ValueError("width must be in 5..30")
  if seed is None:
    seed = random.randint(1, width - 2)
  if not 1 <= seed <= width - 2:
    raise ValueError("seed must avoid the corners")
  cap = 30 if length is None else length
  max_nb = (cap - 1) // 4
  if num_bars is None:
    nb = random.choice([n for n in _BAR_WEIGHTS if n <= max_nb])
  else:
    if not 1 <= num_bars <= max_nb:
      raise ValueError("num_bars does not fit the length")
    nb = num_bars
  x, used, plan, prev_side = seed, 0, [], None
  for i in range(nb):
    rem = nb - 1 - i
    choices = []
    for n in range(1, _MAX_ONES + 1):
      cost = n + 2 if i == 0 else n + 3
      if used + cost + 4 * rem + 2 > cap:
        continue
      opts = _options(n, x, width)
      if opts:
        choices.append((n, cost, opts))
    n, cost, opts = random.choice(choices)
    choice = random.choice(opts)
    if prev_side is not None and len(opts) == 2 and random.random() < 0.75:
      choice = [o for o in opts if o[0] != prev_side][0]
    side, lo, hi = choice
    v = random.randint(lo, hi)
    if side == "L":
      size, x = v + 1, v + n + 1
    else:
      size, x = width - v, v - n - 1
    plan.append((side, size, n))
    used += cost
    prev_side = side
  # `used` is the last bar row under tight packing; one row must follow it.
  min_len = used + 2
  if length is None:
    length = random.randint(min_len, 30)
  gaps = [0] * (nb + 1)
  for _ in range(length - min_len):
    gaps[random.randrange(nb + 1)] += 1
  bars, row = [], 0
  for i, (side, size, n) in enumerate(plan):
    k = n + 1
    row = k + 1 + gaps[i] if i == 0 else row + 2 + k + gaps[i]
    bars.append((row, side, size, n))
  return length, width, seed, bars


def generate(direction=None, length=None, width=None, seed=None, bars=None,
             num_bars=None):
  """Returns an input/output pair.

  Args:
    direction: path direction, one of "down", "up", "right", "left". The
      seed sits on the opposite edge.
    length: grid extent along the path direction (5..30).
    width: grid extent across the path direction (5..30). For "right" and
      "left" this is the grid height.
    seed: lateral coordinate of the seed in the canonical frame. It must
      be in 1..width-2.
    bars: list of (row, side, size, ones) in the canonical frame. Row is the
      distance from the seed edge. Side "L" attaches the bar at lateral
      coordinate 0 and "R" attaches it at width-1. Size is the bar length
      and ones is the number of 1 cells. If bars is given, length, width and
      seed are required. If bars is None, the other given values act as
      constraints on the random scene.
    num_bars: number of bars for random sampling. It must equal len(bars)
      when bars is given.

  Integer controls must be plain ints; bools and floats raise ValueError.
  """
  if direction is None:
    direction = random.choice(_DIRECTIONS)
  if not isinstance(direction, str) or direction not in _DIRECTIONS:
    raise ValueError("unknown direction")
  for name, v in (("length", length), ("width", width), ("seed", seed),
                  ("num_bars", num_bars)):
    if v is not None:
      _int(name, v)
  if bars is None:
    length, width, seed, bars = _sample(length, width, seed, num_bars)
  else:
    if length is None or width is None or seed is None:
      raise ValueError("explicit bars need length, width and seed")
    if not isinstance(bars, (list, tuple)):
      raise ValueError("bars must be a list of bar tuples")
    if num_bars is not None and num_bars != len(bars):
      raise ValueError("num_bars disagrees with bars")
  bars = _check(length, width, seed, bars)
  inp, out = _render(direction, length, width, seed, bars)
  return {"input": inp, "output": out}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate("down", 19, 13, 8, [(7, "R", 7, 4)]),
      generate("right", 19, 17, 3, [(6, "L", 7, 1), (16, "R", 10, 3)]),
      generate("down", 19, 19, 4,
               [(4, "L", 7, 1), (10, "R", 15, 2), (16, "L", 6, 2)]),
      generate("right", 19, 12, 4, [(5, "L", 6, 2), (14, "R", 6, 1)]),
  ]
  test = [
      generate("left", 26, 14, 6,
               [(8, "L", 10, 3), (18, "R", 9, 2), (24, "L", 6, 1)]),
      generate("down", 29, 16, 8,
               [(3, "R", 12, 1), (9, "L", 7, 2), (17, "R", 10, 3),
                (27, "L", 9, 4)]),
  ]
  return {"train": train, "test": test}
