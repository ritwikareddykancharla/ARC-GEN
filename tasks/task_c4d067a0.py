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

"""ARC task c4d067a0: blow a small legend up to full scale.

Rule: the top-left corner holds a legend, a lattice of single pixels spaced
two cells apart (pixel (r, c) sits at (1 + 2r, 1 + 2c)). Elsewhere there is
one horizontal row of solid square blocks of side `size`. Their x-spacing is
`step`, and their colours are a run of consecutive legend cells in one legend
row. The output keeps everything and stamps every non-background legend cell
as a size x size block on a lattice of pitch `step` in both directions. The
lattice is anchored so that the existing blocks coincide with their legend
run. Stamps running past the bottom or right edge are clipped.

Scope: random background, legend shape (2..5 rows, 2..4 columns), legend
palette, empty legend cells, block size (2..4), gap between blocks (1..3),
run position and length (2..3 blocks), canvas size and block-row placement.
The anchoring run appears exactly once in the legend. Every legend row and
column contains a coloured cell. The lattice never overlaps the legend area.
"""

import random

import common


def _stamp(g, y, x, s, color):
  h, w = len(g), len(g[0])
  for yy in range(max(y, 0), min(y + s, h)):
    for xx in range(max(x, 0), min(x + s, w)):
      g[yy][xx] = color


def _count_runs(legend, run):
  n = 0
  k = len(run)
  for row in legend:
    for c in range(len(row) - k + 1):
      if row[c:c + k] == run:
        n += 1
  return n


def _legend_ok(legend, bg):
  rows, cols = len(legend), len(legend[0])
  for r in range(rows):
    if all(v == bg for v in legend[r]):
      return False
  for c in range(cols):
    if all(legend[r][c] == bg for r in range(rows)):
      return False
  return True


def _origin_ok(legend, bg, height, width, s, st, r0, c0, k, y0, x0):
  rows, cols = len(legend), len(legend[0])
  if y0 < 0 or x0 < 0 or y0 + s > height or x0 + (k - 1) * st + s > width:
    return False
  oy, ox = y0 - r0 * st, x0 - c0 * st
  if oy < 0 or ox < 0:
    return False
  # The lattice must keep clear of the legend box (with a one-cell margin).
  if not (oy > 2 * rows or ox > 2 * cols):
    return False
  for r in range(rows):
    for c in range(cols):
      if legend[r][c] != bg:
        if oy + r * st >= height or ox + c * st >= width:
          return False
  return True


def generate(width=None, height=None, background=None, legend=None,
             size=None, step=None, anchor=None, count=None, origin=None):
  """Build one input/output pair.

  Args:
    width: canvas width (14..30 when sampled).
    height: canvas height (14..30 when sampled).
    background: background colour.
    legend: legend matrix as a list of rows. Background-valued cells are empty.
    size: side length of every block (>= 2).
    step: pitch of the block lattice (> size).
    anchor: (row, col) of the legend run copied by the existing blocks.
    count: number of existing blocks, which is the run length (>= 2).
    origin: (y, x) top-left of the leftmost existing block.
  """
  for _ in range(500):
    bg = background if background is not None else random.randint(0, 9)
    if legend is None:
      rows, cols = random.randint(2, 5), random.randint(2, 4)
      others = [c for c in range(10) if c != bg]
      palette = random.sample(others, random.randint(2, 4))
      lg = [[random.choice(palette) if random.random() < 0.85 else bg
             for _ in range(cols)] for _ in range(rows)]
    else:
      lg = [list(r) for r in legend]
      rows, cols = len(lg), len(lg[0])
    if not _legend_ok(lg, bg):
      continue
    s = size if size is not None else random.randint(2, 4)
    st = step if step is not None else s + random.randint(1, 3)
    w = width if width is not None else random.randint(14, 30)
    h = height if height is not None else random.randint(14, 30)
    if anchor is None:
      cands = []
      for k in range(2, min(3, cols) + 1):
        if count is not None and k != count:
          continue
        for r in range(rows):
          for c in range(cols - k + 1):
            run = lg[r][c:c + k]
            if bg in run or _count_runs(lg, run) != 1:
              continue
            cands.append((r, c, k))
      if not cands:
        continue
      r0, c0, k = random.choice(cands)
    else:
      r0, c0 = anchor
      k = count if count is not None else 2
      run = lg[r0][c0:c0 + k]
      if len(run) != k or bg in run or _count_runs(lg, run) != 1:
        continue
    if origin is not None:
      y0, x0 = origin
      if not _origin_ok(lg, bg, h, w, s, st, r0, c0, k, y0, x0):
        continue
    else:
      spots = [(y, x) for y in range(h) for x in range(w)
               if _origin_ok(lg, bg, h, w, s, st, r0, c0, k, y, x)]
      if not spots:
        continue
      y0, x0 = random.choice(spots)
    grid = common.grid(w, h, bg)
    for r in range(rows):
      for c in range(cols):
        if lg[r][c] != bg:
          grid[1 + 2 * r][1 + 2 * c] = lg[r][c]
    for i in range(k):
      _stamp(grid, y0, x0 + i * st, s, lg[r0][c0 + i])
    out = [list(row) for row in grid]
    oy, ox = y0 - r0 * st, x0 - c0 * st
    for r in range(rows):
      for c in range(cols):
        if lg[r][c] != bg:
          _stamp(out, oy + r * st, ox + c * st, s, lg[r][c])
    return {"input": grid, "output": out}
  raise ValueError("could not construct a valid scene")


def validate():
  """Reconstruct the canonical examples from explicit latent parameters."""
  train = [
      generate(width=23, height=23, background=8,
               legend=[[4, 4], [1, 1], [1, 1]], size=3, step=5,
               anchor=(0, 0), count=2, origin=(1, 8)),
      generate(width=23, height=23, background=8,
               legend=[[2, 2, 8], [1, 1, 8], [1, 1, 3], [1, 1, 3]],
               size=2, step=3, anchor=(0, 0), count=2, origin=(4, 10)),
      generate(width=23, height=23, background=1,
               legend=[[2, 3], [3, 3], [3, 4]], size=2, step=5,
               anchor=(2, 0), count=2, origin=(20, 11)),
  ]
  test = [
      generate(width=27, height=27, background=3,
               legend=[[1, 1, 1], [4, 4, 2], [1, 4, 1], [8, 3, 3]],
               size=4, step=5, anchor=(1, 1), count=2, origin=(10, 13)),
  ]
  return {"train": train, "test": test}
