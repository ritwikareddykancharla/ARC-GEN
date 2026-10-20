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

"""Generator for ARC task e872b94a: count the snake walls.

The input is a background-0 grid crossed by colour-5 "snakes": thin, winding,
4-connected paths that mostly run from one edge to another and act as walls
that split the background into pieces.  The output is a single column of
background colour whose height is (number of snakes) + 1, i.e. the number of
background pieces N walls carve out of the canvas.

Scope: snakes are laid out in disjoint parallel lanes (vertical or
horizontal orientation), separated by at least one empty lane so that no two
snakes are 4-adjacent and the 4-connected component count equals the number
of constructed snakes. Snakes span the canvas; an independent connectivity
check requires exactly N+1 background regions. Floating paths are excluded.  The
background colour 0 is always kept the strict majority colour so that the
background is unambiguous (dense, wall-dominated canvases are rejected).
"""

import random

import common

SNAKE = 5
BG = 0


def _sample_lanes(span):
  """Returns a list of (lo, hi) lane ranges separated by >= 1 empty lane."""
  max_n = min(6, max(1, span // 3))
  n = random.randint(1, max_n)
  widths = [random.randint(1, 4) for _ in range(n)]
  while sum(widths) + n - 1 > span:
    idx = max(range(n), key=lambda i: widths[i])
    widths[idx] -= 1
  slack = span - (sum(widths) + n - 1)
  slots = [0] * (n + 1)
  for _ in range(slack):
    slots[random.randrange(n + 1)] += 1
  lanes = []
  pos = slots[0]
  for i in range(n):
    lanes.append((pos, pos + widths[i] - 1))
    pos += widths[i] + 1 + slots[i + 1]
  return lanes


def _sample_snake(lo, hi, span):
  """Winds a 4-connected snake downward inside lane [lo, hi]."""
  # Full-span walls preserve the demonstrated relationship between wall
  # count and background-region count. Short floating paths do not divide
  # the canvas and therefore are not valid samples for this interpretation.
  r0, r1 = 0, span - 1
  x = random.randint(lo, hi)
  cells = []
  last_shift = False
  for r in range(r0, r1 + 1):
    if lo < hi and not last_shift and random.random() < 0.45:
      choices = [c for c in range(lo, hi + 1) if c != x]
      nx = random.choice(choices)
      for c in range(min(x, nx), max(x, nx) + 1):
        cells.append((r, c))
      x = nx
      last_shift = True
    else:
      cells.append((r, x))
      last_shift = False
  return cells


def _components(cells):
  """Counts 4-connected components of a set of (row, col) cells."""
  remaining = set(cells)
  count = 0
  while remaining:
    stack = [remaining.pop()]
    count += 1
    while stack:
      r, c = stack.pop()
      for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = (r + dr, c + dc)
        if nb in remaining:
          remaining.remove(nb)
          stack.append(nb)
  return count


def generate(width=None, height=None, snakes=None, orientation=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the width of the input grid (3..30)
    height: the height of the input grid (3..30)
    snakes: a list of snakes, each a list of (row, col) cells of colour 5;
        snakes must be internally 4-connected and pairwise non-4-adjacent,
        and must cover strictly fewer cells than the background
    orientation: 'vertical' or 'horizontal' lane direction for sampling
  """
  if snakes is None:
    for _ in range(200):
      w = width if width is not None else random.randint(3, 30)
      h = height if height is not None else random.randint(3, 30)
      orient = orientation
      if orient is None:
        orient = random.choice(["vertical", "horizontal"])
      if orient == "vertical":
        span_w, span_h = w, h
      else:
        span_w, span_h = h, w
      lanes = _sample_lanes(span_w)
      cand = [_sample_snake(lo, hi, span_h) for lo, hi in lanes]
      if orient == "horizontal":
        cand = [[(c, r) for r, c in s] for s in cand]
      flat = [cell for s in cand for cell in s]
      if len(set(flat)) != len(flat):
        continue
      if _components(flat) != len(cand):
        continue
      # All original pairs satisfy both wall-count and region-count readings.
      # Preserve both, rather than trusting the archived wall-count shortcut.
      walls = set(flat)
      empty = {(r, c) for r in range(h) for c in range(w) if (r, c) not in walls}
      if _components(empty) != len(cand) + 1:
        continue
      # Background must stay the clear majority colour.
      if (w * h - len(flat)) * 4 < len(flat) * 5:
        continue
      width, height, snakes = w, h, cand
      break
    if snakes is None:
      # Bounded fallback: one straight full-height wall in a sparse canvas.
      width = width if width is not None else 3
      height = height if height is not None else 3
      snakes = [[(r, 1) for r in range(height)]]

  grid = common.grid(width, height, BG)
  for s in snakes:
    for r, c in s:
      grid[r][c] = SNAKE
  n = len(snakes)
  output = common.grid(1, n + 1, BG)
  return {"input": grid, "output": output}


def validate():
  """Validates the generator against the canonical task fixtures."""
  train = [
      generate(width=7, height=7, snakes=[
          [(0, 1), (1, 1), (1, 2), (2, 2), (3, 1), (3, 2), (4, 1), (5, 1),
           (6, 1)],
          [(2, 5), (2, 6), (3, 5), (4, 4), (4, 5), (5, 4), (6, 4)],
      ]),
      generate(width=3, height=3, snakes=[
          [(0, 1), (1, 1), (1, 2), (2, 2)],
      ]),
      generate(width=12, height=9, snakes=[
          [(0, 1), (1, 1), (2, 1), (2, 2), (3, 2), (4, 2), (5, 0), (5, 1),
           (5, 2)],
          [(0, 5), (1, 5), (2, 4), (2, 5), (3, 4), (4, 4), (5, 4), (6, 4),
           (7, 3), (7, 4), (8, 1), (8, 2), (8, 3)],
          [(0, 8), (1, 8), (2, 7), (2, 8), (3, 7), (4, 6), (4, 7), (5, 6),
           (6, 6), (7, 6), (8, 6)],
          [(6, 9), (6, 10), (6, 11), (7, 9), (8, 9)],
      ]),
      generate(width=12, height=12, snakes=[
          [(1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (4, 2), (5, 1), (5, 2),
           (6, 1), (7, 1), (7, 2), (7, 3), (7, 4), (6, 4), (6, 5), (6, 6),
           (7, 6), (8, 6), (9, 6), (9, 5), (9, 4), (10, 4), (11, 4)],
          [(0, 7), (0, 8), (1, 8), (2, 6), (2, 7), (2, 8), (3, 6), (4, 6),
           (4, 7), (4, 8), (4, 9), (5, 9), (6, 9), (7, 9), (8, 9), (9, 9),
           (10, 8), (10, 9), (11, 8)],
          [(9, 0), (9, 1), (10, 1), (11, 1)],
      ]),
  ]
  test = [
      generate(width=10, height=9, snakes=[
          [(0, 2), (1, 2), (2, 2), (2, 3), (3, 3), (4, 1), (4, 2), (4, 3),
           (5, 1), (6, 1), (7, 1), (7, 2), (8, 2)],
          [(0, 6), (1, 6), (1, 7), (2, 7), (3, 7), (3, 8), (4, 8), (5, 6),
           (5, 7), (5, 8), (6, 6), (7, 5), (7, 6), (8, 5)],
      ]),
  ]
  return {"train": train, "test": test}
