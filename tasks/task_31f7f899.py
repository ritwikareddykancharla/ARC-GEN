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

"""ARC task 31f7f899: sort bar extents along a divider line.

Rule: the background is 8 and one full horizontal line is colour 6. Several
vertical bars cross the line. Each bar is a run of 1..3 columns of one colour,
and it covers a contiguous vertical extent that contains the line row. The
bars keep their columns and colours. Their vertical extents (top row, bottom
row) are sorted by length and handed out to the bars from left to right, so
the shortest is on the left. Equal-length extents are always identical, so
the assignment is unambiguous.

Scope: random grid sizes, line row, bar count, bar widths, gaps (including
adjacent bars of different colours), colours (repeats allowed when the bars
are not adjacent), and extents. Most scenes use bars centred on the line. Some
use off-centre extents, as in the test pair. An optional transposed
(vertical-line) layout is also sampled, which matches the transpose step in
the explained program.
"""

import random

import common

BG = 8
LINE = 6
PALETTE = [0, 1, 2, 3, 4, 5, 7, 9]


def _transpose(g):
  return [list(r) for r in zip(*g)]


def _render(width, height, line_row, bars, extents):
  g = common.grid(width, height, BG)
  for x in range(width):
    g[line_row][x] = LINE
  for (x0, w, c), (t, b) in zip(bars, extents):
    for y in range(t, b + 1):
      for x in range(x0, x0 + w):
        g[y][x] = c
  return g


def _sample_scene(requested_width, requested_height, requested_line_row):
  for _ in range(500):
    height = requested_height if requested_height is not None else random.randint(5, 30)
    width = requested_width if requested_width is not None else random.randint(5, 30)
    line_row = requested_line_row if requested_line_row is not None else random.randint(2, height - 3)
    maxup = line_row - 1
    maxdown = height - 2 - line_row
    n = random.randint(3, 6)
    if random.random() < 0.3:
      widths = [random.choice([1, 1, 2, 3]) for _ in range(n)]
    else:
      widths = [1] * n
    leftover = width - sum(widths)
    if leftover < 2:
      continue
    slots = [0] * (n + 1)
    for _ in range(leftover):
      slots[random.randint(0, n)] += 1
    colors = [random.choice(PALETTE) for _ in range(n)]
    ok = True
    bars = []
    x = slots[0]
    for i in range(n):
      if i > 0 and slots[i] == 0 and colors[i] == colors[i - 1]:
        ok = False
      bars.append((x, widths[i], colors[i]))
      x += widths[i] + slots[i + 1]
    if not ok:
      continue
    # The line colour must be the strict majority colour on the line row.
    line_count = leftover
    per = {}
    for (_, w, c) in bars:
      per[c] = per.get(c, 0) + w
    if line_count <= max(per.values()):
      continue
    centred = random.random() < 0.65
    extents = []
    for _ in range(n):
      ext = None
      for _ in range(30):
        if centred:
          h = random.randint(0, min(maxup, maxdown))
          cand = (line_row - h, line_row + h)
        else:
          cand = (line_row - random.randint(0, maxup),
                  line_row + random.randint(0, maxdown))
        length = cand[1] - cand[0]
        if all(e == cand or e[1] - e[0] != length for e in extents):
          ext = cand
          break
      if ext is None:
        ok = False
        break
      extents.append(ext)
    if not ok:
      continue
    if sorted(extents, key=lambda e: e[1] - e[0]) == extents:
      continue
    if len(set(extents)) < 2:
      continue
    full = [(b[0], b[1], b[2], e[0], e[1]) for b, e in zip(bars, extents)]
    return width, height, line_row, full
  raise RuntimeError("Could not construct unambiguous unsorted bars")


def generate(width=None, height=None, line_row=None, bars=None,
             vertical=None):
  """Build one input/output pair.

  Args:
    width: grid width in the horizontal-line frame.
    height: grid height in the horizontal-line frame.
    line_row: row index of the colour-6 divider line.
    bars: list of (x0, bar_width, colour, top, bottom) tuples, left to right.
      Each extent [top, bottom] must contain line_row.
    vertical: if True, transpose the finished scene so that the line is
      vertical.
  """
  for dimension in (width, height):
    if dimension is not None and (not isinstance(dimension, int) or not 5 <= dimension <= 30):
      raise ValueError("Native dimensions must be in 5..30")
  if bars is None:
    if line_row is not None and (height is None or not 2 <= line_row <= height - 3):
      raise ValueError("Requested line_row needs height and two-cell edge margins")
    width, height, line_row, bars = _sample_scene(width, height, line_row)
    if vertical is None:
      vertical = random.random() < 0.2
  if width is None or height is None or line_row is None or not bars:
    raise ValueError("Explicit bars require complete geometry")
  bars = sorted(bars, key=lambda b:b[0])
  occupied = set()
  by_length = {}
  for x, w, colour, top, bottom in bars:
    if not (w > 0 and 0 <= x < x+w <= width and 0 <= top <= line_row <= bottom < height and colour in PALETTE):
      raise ValueError("Invalid bar bounds or colour")
    columns = set(range(x,x+w))
    if columns & occupied:
      raise ValueError("Overlapping bars")
    occupied.update(columns)
    length = bottom-top+1
    if length in by_length and by_length[length] != (top,bottom):
      raise ValueError("Equal-length extents must be identical")
    by_length[length] = (top,bottom)
  vertical = bool(vertical)
  cols = [(b[0], b[1], b[2]) for b in bars]
  extents = [(b[3], b[4]) for b in bars]
  order = sorted(extents, key=lambda e: e[1] - e[0])
  inp = _render(width, height, line_row, cols, extents)
  out = _render(width, height, line_row, cols, order)
  if vertical:
    inp, out = _transpose(inp), _transpose(out)
  return {"input": inp, "output": out}


def validate():
  """Reconstruct the canonical pairs from explicit latent parameters."""
  train = [
      generate(width=13, height=13, line_row=6,
               bars=[(1, 1, 5, 2, 10), (6, 1, 2, 3, 9), (7, 1, 7, 4, 8),
                     (8, 1, 1, 5, 7)], vertical=False),
      generate(width=15, height=15, line_row=7,
               bars=[(2, 1, 4, 5, 9), (4, 1, 7, 3, 11), (6, 1, 5, 5, 9),
                     (8, 1, 1, 6, 8), (12, 1, 9, 2, 12)], vertical=False),
      generate(width=7, height=7, line_row=3,
               bars=[(0, 1, 4, 2, 4), (2, 1, 1, 1, 5), (4, 1, 1, 2, 4),
                     (6, 1, 7, 2, 4)], vertical=False),
  ]
  test = [
      generate(width=17, height=17, line_row=8,
               bars=[(0, 1, 9, 3, 12), (2, 3, 5, 5, 11), (7, 3, 2, 6, 10),
                     (16, 1, 7, 8, 8)], vertical=False),
  ]
  return {"train": train, "test": test}
