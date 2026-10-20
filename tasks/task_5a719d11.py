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

"""ARC task 5a719d11: swap shapes between paired panels.

Full lines of colour 0 cut the grid into two columns of panels and several
panel rows. Each panel has a background colour and one small shape in
another colour. In every panel row, the left and right panels exchange
their shapes. A shape keeps its offset from the panel's top-left corner.
It is repainted in the background colour of the panel it came from, and the
original shape is erased. When both panels in a row share a background, the
incoming shapes are invisible, so both panels become blank.

Scope: two panel columns of equal width, 2..4 panel rows, and vertical and
horizontal divider thickness 1 or 2, with no border dividers. Random panel
widths are 6..12 and panel heights are 5..9, either uniform or varying per
row. Fixtures use widths 7..8 and heights 6..8, so the wider and taller
layouts are synthetic extensions. Every layout fits within 30x30.
Shapes are random cell sets kept one cell inside the panel border. Usually a
shape is one 4-connected blob. Sometimes it is two loose parts, like the
disconnected 6-shape in the test. Each shape covers less than half of its
panel, so the panel background is the majority colour. A shape's colour may
equal the partner panel's background, as it does in the fixtures. Rows with
equal backgrounds are sampled occasionally, but at least one row always has
different backgrounds.
Not generated: layouts with three or more panel columns, single-row layouts
(where dividers would be ambiguous), and panels of unequal width.
"""

import random

import common


def _cells(text):
  return [(int(t[0]), int(t[1])) for t in text.split()]


def _grow(ph, pw, size):
  """Random 4-connected cell set inside the panel interior."""
  interior = [(r, c) for r in range(1, ph - 1) for c in range(1, pw - 1)]
  cells = {random.choice(interior)}
  steps = [(0, 1), (0, -1), (1, 0), (-1, 0)]
  for _ in range(400):
    if len(cells) >= size:
      break
    r, c = random.choice(sorted(cells))
    dr, dc = random.choice(steps)
    nr, nc = r + dr, c + dc
    if 1 <= nr <= ph - 2 and 1 <= nc <= pw - 2:
      cells.add((nr, nc))
  return cells


def _shape(ph, pw, size):
  """One connected blob, or occasionally two loose parts."""
  if size >= 5 and random.random() < 0.3:
    first = size // 2
    cells = _grow(ph, pw, first) | _grow(ph, pw, size - first)
  else:
    cells = _grow(ph, pw, size)
  return sorted(cells)


def _row_count(panel_heights, backgrounds, shapes):
  counts = [len(x) for x in (panel_heights, backgrounds, shapes)
            if x is not None]
  if counts:
    if len(set(counts)) != 1:
      raise ValueError("panel_heights/backgrounds/shapes row counts differ")
    n = counts[0]
  else:
    n = random.randint(2, 4)
  if n < 2:
    raise ValueError("at least two panel rows are required")
  return n


def _sample_heights(n, hd, lows):
  """Panel heights (>= lows, >= 5) whose total fits in 30 rows."""
  budget = 30 - hd * (n - 1)
  hs = [max(5, lo) for lo in lows]
  if sum(hs) > budget:
    raise ValueError("panel rows do not fit in 30 rows")
  top = max(hs)
  if random.random() < 0.6 and top * n <= budget:
    h = random.randint(top, max(top, min(9, budget // n)))
    return [h] * n
  order = list(range(n))
  random.shuffle(order)
  for i in order:
    room = min(max(hs[i], 9) - hs[i], budget - sum(hs))
    hs[i] += random.randint(0, max(0, room))
  return hs


def generate(panel_width=None, panel_heights=None, vdiv=None, hdiv=None,
             backgrounds=None, shapes=None):
  """Build one input/output pair.

  Any argument may be given alone. Missing ones are sampled consistently
  with the given ones. Incompatible combinations raise ValueError.

  Args:
    panel_width: width of every panel (both columns).
    panel_heights: list of panel heights, one per panel row (>= 2 rows).
    vdiv: thickness of the vertical 0 divider (>= 1).
    hdiv: thickness of each horizontal 0 divider (>= 1).
    backgrounds: list of (left_bg, right_bg) per panel row, colours 1..9.
    shapes: list of ((left_colour, left_cells), (right_colour, right_cells))
      per panel row. Cells are (row, col) relative to the panel corner, and
      each colour must differ from its own panel's background.
  """
  n = _row_count(panel_heights, backgrounds, shapes)
  for name, value in (("panel_width", panel_width), ("vdiv", vdiv),
                      ("hdiv", hdiv)):
    if value is not None and (type(value) is not int or value < 1):
      raise ValueError(name + " must be a positive integer")
  if panel_heights is not None and any(type(h) is not int or h < 3
                                      for h in panel_heights):
    raise ValueError("panel heights must be integers at least 3")
  vd = random.randint(1, 2) if vdiv is None else vdiv
  hd = random.randint(1, 2) if hdiv is None else hdiv
  if vd < 1 or hd < 1:
    raise ValueError("divider thickness must be at least 1")

  # Minimum panel extents implied by explicitly supplied shapes.
  min_w, lows = 0, [0] * n
  if shapes is not None:
    for i, row in enumerate(shapes):
      if len(row) != 2:
        raise ValueError("each shape row needs a left and a right shape")
      for _, cells in row:
        if not cells:
          raise ValueError("shapes must be non-empty")
        lows[i] = max(lows[i], max(r for r, _ in cells) + 2)
        min_w = max(min_w, max(c for _, c in cells) + 2)

  if panel_width is None:
    lo, hi = max(6, min_w), min(12, (30 - vd) // 2)
    if lo > hi:
      raise ValueError("no panel width fits the requested shapes")
    pw = random.randint(lo, hi)
  else:
    pw = panel_width
  if panel_heights is None:
    heights = _sample_heights(n, hd, lows)
  else:
    heights = list(panel_heights)
  width = 2 * pw + vd
  height = sum(heights) + hd * (n - 1)
  if pw < 3 or min(heights) < 3 or width > 30 or height > 30:
    raise ValueError("layout out of bounds")

  if backgrounds is None:
    if shapes is None:
      shape_cols = [(None, None)] * n
    else:
      shape_cols = [(row[0][0], row[1][0]) for row in shapes]
    backgrounds = []
    for i in range(n):
      lcol, rcol = shape_cols[i]
      a = random.choice([c for c in range(1, 10) if c != lcol])
      if a != rcol and random.random() < 0.2:
        b = a
      else:
        b = random.choice([c for c in range(1, 10) if c not in (a, rcol)])
      backgrounds.append((a, b))
    if all(a == b for a, b in backgrounds):
      i = random.randrange(n)
      a = backgrounds[i][0]
      b = random.choice([c for c in range(1, 10)
                         if c not in (a, shape_cols[i][1])])
      backgrounds[i] = (a, b)
  else:
    backgrounds = [tuple(bg) for bg in backgrounds]
  for bg in backgrounds:
    if len(bg) != 2 or not all(type(c) is int and 1 <= c <= 9 for c in bg):
      raise ValueError("backgrounds must be pairs of colours 1..9")

  if shapes is None:
    shapes = []
    for i in range(n):
      ph = heights[i]
      interior = (ph - 2) * (pw - 2)
      if interior < 1:
        raise ValueError("panel too small to hold a shape")
      hi = max(1, min(14, interior * 2 // 3, (ph * pw - 1) // 2))
      row = []
      for bg in backgrounds[i]:
        col = random.choice([c for c in range(1, 10) if c != bg])
        size = random.randint(min(3, hi), hi)
        row.append((col, _shape(ph, pw, size)))
      shapes.append(tuple(row))

  for i in range(n):
    ph = heights[i]
    for side in range(2):
      col, cells = shapes[i][side]
      if type(col) is not int or not 1 <= col <= 9 or col == backgrounds[i][side]:
        raise ValueError("shape colour must be 1..9 and differ from its bg")
      cellset = set(tuple(p) for p in cells)
      if len(cellset) != len(cells) or 2 * len(cellset) >= ph * pw:
        raise ValueError("shape cells must be distinct and under half panel")
      for r, c in cellset:
        if not (type(r) is int and type(c) is int and
                0 <= r < ph and 0 <= c < pw):
          raise ValueError("shape cell outside its panel")

  grid = common.grid(width, height, 0)
  out = common.grid(width, height, 0)
  x0s = [0, pw + vd]
  y0 = 0
  for i in range(n):
    ph = heights[i]
    bgs = backgrounds[i]
    for side in range(2):
      for r in range(ph):
        for c in range(pw):
          grid[y0 + r][x0s[side] + c] = bgs[side]
          out[y0 + r][x0s[side] + c] = bgs[side]
    # Input: shapes in place. Output: each shape in the partner panel,
    # painted in the background colour of the panel it came from.
    for side in range(2):
      col, cells = shapes[i][side]
      other = 1 - side
      for r, c in cells:
        grid[y0 + r][x0s[side] + c] = col
        out[y0 + r][x0s[other] + c] = bgs[side]
    y0 += ph + hd
  return {"input": grid, "output": out}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  s = _cells
  train = [
      generate(panel_width=8, panel_heights=[7, 7, 7], vdiv=1, hdiv=2,
               backgrounds=[(6, 4), (2, 2), (3, 1)],
               shapes=[((4, s("22 25 32 33 34 35")),
                        (8, s("22 23 25 33 35 43 44 45"))),
                       ((3, s("13 14 15 22 23 33 43 44")),
                        (1, s("12 13 14 22 24 32 34 43 44 45 53"))),
                       ((2, s("13 22 23 33 43 52 53 54 55")),
                        (4, s("11 12 22 23 33 43 53 54 55")))]),
      generate(panel_width=8, panel_heights=[7, 7, 7], vdiv=1, hdiv=2,
               backgrounds=[(8, 8), (4, 8), (4, 2)],
               shapes=[((1, s("22 23 24 25 31 32 42 43 45")),
                        (2, s("24 31 32 33 34 35 36 44"))),
                       ((1, s("12 22 24 32 33 34 44 45")),
                        (3, s("13 21 22 23 33 43 44"))),
                       ((2, s("12 14 22 23 33 34 43")),
                        (8, s("12 13 23 33 34 35 44 45")))]),
      generate(panel_width=8, panel_heights=[8, 8], vdiv=1, hdiv=2,
               backgrounds=[(2, 4), (3, 8)],
               shapes=[((1, s("23 31 32 33 43 53 63 64 65 66")),
                        (9, s("21 31 34 41 44 51 52 53 54 55 56 64"))),
                       ((4, s("11 12 13 23 32 33 34 43")),
                        (6, s("13 14 24 26 34 35 36 46 56 66")))]),
  ]
  test = [
      generate(panel_width=7, panel_heights=[6, 6, 6, 6], vdiv=2, hdiv=2,
               backgrounds=[(8, 4), (2, 3), (4, 9), (1, 1)],
               shapes=[((1, s("11 13 14 15 21 22 23 31 33 34 35 41 45")),
                        (7, s("11 12 15 22 23 24 25 35 45"))),
                       ((8, s("11 12 22 32 33 34 35 42")),
                        (9, s("11 12 13 14 15 25 35 41 42 43 44 45"))),
                       ((6, s("11 12 15 21 35 41 44 45")),
                        (1, s("11 15 21 22 23 24 25 33 43"))),
                       ((3, s("12 22 31 32 33 34 35 42 45")),
                        (5, s("11 12 13 22 25 32 35 41 42 43")))]),
  ]
  return {"train": train, "test": test}
