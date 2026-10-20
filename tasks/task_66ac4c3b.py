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

"""ARC task 66ac4c3b: mirror a shape across the midline of two dotted lines.

Rule: a 4-connected meandering shape in the shape colour lies directly beside
a dotted marker line in the marker colour. Further away, on the other side of
the marker line, is a second dotted line. It has the same dot positions and is
drawn in the shape colour. The output adds a copy of the shape, reflected
about the axis halfway between the two dotted lines and painted in the marker
colour. The marker line maps onto the second line, so the copy appears just
beyond it.

Scope: the shape can sit on any of the four sides (top, bottom, left or right
of the lines). The scene samples:
- the line length (10..30) and the grid breadth;
- the shape depth, the gap between the lines, and the margins;
- the dot period and offset;
- the shape's along-axis start and span;
- the shape profile;
- three distinct colours.
The shape is built as a run of depth intervals, one per along-axis position.
Consecutive intervals overlap, which keeps the shape 4-connected. This covers
staircase paths and short spurs. The fixtures are all 22x22. Other sizes and
partial-span shapes are synthetic extensions of the same rule.
"""

import random

import common

_SIDES = ("top", "bottom", "left", "right")


def _place(side, breadth, t, p):
  """Maps (along t, perpendicular p) to (row, col) for the given side."""
  if side == "top":
    return p, t
  if side == "bottom":
    return breadth - 1 - p, t
  if side == "left":
    return t, p
  return t, breadth - 1 - p


def _random_intervals(n, depth):
  """Random meandering shape profile: overlapping depth intervals."""
  d = 1 if random.random() < 0.5 else random.randint(1, depth)
  intervals = []
  for _ in range(n):
    r = random.random()
    if r < 0.3:
      nd = random.choice([x for x in range(1, depth + 1) if x != d])
      intervals.append((min(d, nd), max(d, nd)))
      d = nd
    elif r < 0.4:
      opts = [x for x in (d - 1, d + 1) if 1 <= x <= depth]
      nb = random.choice(opts)
      intervals.append((min(d, nb), max(d, nb)))
    else:
      intervals.append((d, d))
  return intervals


def _check_intervals(ivs):
  """Rejects malformed or disconnected explicit interval profiles."""
  if not ivs:
    raise ValueError("intervals must be non-empty")
  for lo, hi in ivs:
    if type(lo) is not int or type(hi) is not int or not 1 <= lo <= hi:
      raise ValueError("each interval needs 1 <= lo <= hi")
  for (a, b), (c, d) in zip(ivs, ivs[1:]):
    if max(a, c) > min(b, d):
      raise ValueError("consecutive intervals must overlap (4-connected)")


def _colors(background, shape_color, marker_color):
  """Keeps the given colours and samples distinct ones for the rest."""
  given = [c for c in (background, shape_color, marker_color)
           if c is not None]
  for c in given:
    if type(c) is not int or not 0 <= c <= 9:
      raise ValueError("colours must be in 0..9")
  if len(set(given)) != len(given):
    raise ValueError("background, shape and marker colours must differ")
  pool = [c for c in range(10) if c not in given]
  random.shuffle(pool)
  bg = background if background is not None else pool.pop()
  sc = shape_color if shape_color is not None else pool.pop()
  mc = marker_color if marker_color is not None else pool.pop()
  return bg, sc, mc


def generate(length=None, breadth=None, side=None, marker_pos=None, gap=None,
             period=None, offset=None, shape_start=None, intervals=None,
             background=None, shape_color=None, marker_color=None):
  """Builds one input/output pair.

  Args:
    length: size of the grid along the dotted lines (<= 30).
    breadth: size of the grid perpendicular to the lines (<= 30).
    side: where the shape is relative to the lines: 'top', 'bottom', 'left'
      or 'right'.
    marker_pos: perpendicular index of the marker line, counted from the
      shape's side.
    gap: distance from the marker line to the second line (>= 2).
    period: spacing of the dots along each line (>= 2).
    offset: along index of the first dot.
    shape_start: along index where the shape begins.
    intervals: list of (lo, hi) depth intervals, one per along position
      starting at shape_start. Depth 1 is adjacent to the marker line.
      Consecutive intervals must overlap.
    background: background colour.
    shape_color: colour of the shape and of the second dotted line.
    marker_color: colour of the marker line and of the mirrored copy.
  """
  if side is not None and side not in _SIDES:
    raise ValueError("side must be one of %s" % (_SIDES,))
  for name, value in (("length",length),("breadth",breadth),
                      ("marker_pos",marker_pos),("gap",gap),("period",period),
                      ("offset",offset),("shape_start",shape_start)):
    if value is not None and type(value) is not int:
      raise ValueError(name + " must be an integer")
  if any(v is not None and not 1<=v<=30 for v in (length,breadth)):
    raise ValueError("grid sides must be in 1..30")
  if intervals is not None:
    intervals = list(intervals)
    _check_intervals(intervals)
  if gap is not None and gap < 2:
    raise ValueError("gap must be >= 2")
  if period is not None and period < 2:
    raise ValueError("period must be >= 2")
  for _ in range(300):
    sd = side if side is not None else random.choice(_SIDES)
    L = length if length is not None else random.randint(10, 30)
    if not 1 <= L <= 30:
      continue
    if intervals is not None:
      ivs = list(intervals)
      D = max(hi for _, hi in ivs)
    else:
      ivs = None
      D = random.randint(2, 6)
    g = gap if gap is not None else random.randint(2, 8)
    if breadth is not None:
      P = breadth
      if marker_pos is not None:
        m = marker_pos
      else:
        if P - 1 - g - D < D:
          continue
        m = random.randint(D, min(P - 1 - g - D, D + 3))
    else:
      m = marker_pos if marker_pos is not None else D + random.randint(0, 3)
      P = m + g + D + 1 + random.randint(0, 3)
    if P > 30 or m - D < 0 or m + g + D > P - 1:
      continue
    per = period if period is not None else random.randint(2, 5)
    off = offset if offset is not None else random.randint(0, per - 1)
    if off < 0:
      continue
    dots = list(range(off, L, per))
    # At least three dots keep horizontal lines distinguishable from a pair of
    # vertical dotted columns.
    if len(dots) < 3:
      continue
    if ivs is None:
      if shape_start is not None:
        st = shape_start
        maxn = L - st
        if maxn < 3:
          continue
        n = random.randint(min(maxn, max(6, L // 2)), maxn)
      elif random.random() < 0.6:
        n, st = L, 0
      else:
        n = random.randint(max(6, L // 2), L)
        st = random.randint(0, L - n)
      ivs = _random_intervals(n, D)
      if max(hi for _, hi in ivs) < 2 or min(lo for lo, _ in ivs) != 1:
        continue
    else:
      st = shape_start if shape_start is not None else 0
    if st < 0 or st + len(ivs) > L:
      continue
    ncells = sum(hi - lo + 1 for lo, hi in ivs)
    if ncells < 3:
      continue
    if L * P - ncells - 2 * len(dots) <= ncells + 2 * len(dots):
      continue
    bg, sc, mc = _colors(background, shape_color, marker_color)
    f = m + g
    if sd in ("top", "bottom"):
      H, W = P, L
    else:
      H, W = L, P
    grid = common.grid(W, H, bg)
    for t in dots:
      r, c = _place(sd, P, t, m)
      grid[r][c] = mc
      r, c = _place(sd, P, t, f)
      grid[r][c] = sc
    mirror = []
    for i, (lo, hi) in enumerate(ivs):
      t = st + i
      for k in range(lo, hi + 1):
        r, c = _place(sd, P, t, m - k)
        grid[r][c] = sc
        mirror.append(_place(sd, P, t, f + k))
    output = [row[:] for row in grid]
    for r, c in mirror:
      output[r][c] = mc
    return {"input": grid, "output": output}
  raise ValueError("could not build a valid scene from the given parameters")


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  iv1 = [(1, 1), (1, 1), (1, 1), (1, 2), (2, 2), (2, 2), (1, 2), (1, 1),
         (1, 1), (1, 4), (4, 4), (4, 4), (1, 4), (1, 1), (1, 1), (1, 2),
         (2, 2), (2, 2), (1, 2), (1, 1), (1, 1), (1, 1)]
  iv2 = [(1, 1), (1, 1), (1, 3), (3, 3), (1, 3), (1, 1), (1, 2), (1, 2),
         (1, 1), (1, 3), (3, 3), (3, 3), (1, 3), (1, 2), (2, 2), (1, 2),
         (1, 1), (1, 3), (3, 3), (2, 3), (2, 2), (1, 2)]
  iv3 = [(1, 3), (3, 3), (3, 4), (3, 3), (1, 3), (1, 1), (1, 2), (1, 2),
         (1, 1), (1, 1), (1, 1), (1, 1), (1, 6), (6, 6), (6, 6), (6, 6),
         (1, 6), (1, 1), (1, 2), (2, 2), (1, 2), (1, 1)]
  train = [
      generate(length=22, breadth=22, side="top", marker_pos=5, gap=6,
               period=3, offset=0, shape_start=0, intervals=iv1,
               background=8, shape_color=3, marker_color=2),
      generate(length=22, breadth=22, side="left", marker_pos=4, gap=6,
               period=3, offset=0, shape_start=0, intervals=iv2,
               background=4, shape_color=1, marker_color=2),
  ]
  test = [
      generate(length=22, breadth=22, side="left", marker_pos=8, gap=6,
               period=4, offset=0, shape_start=0, intervals=iv3,
               background=3, shape_color=4, marker_color=1),
  ]
  return {"train": train, "test": test}
