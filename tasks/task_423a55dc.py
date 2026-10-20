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

"""Generator for ARC task 423a55dc: shear a single outline left.

Each input holds one hollow outline (the 8-connected inner boundary of a
union of one to three overlapping axis-aligned rectangles) in a single colour
on a black background. The output keeps the bottom row of the shape fixed and
slides every row above it left by its vertical distance from that bottom row;
cells pushed past the left edge are dropped.

Scope: grids 7..20 per side, shape colour 1..9, outlines built from 1..3
connected rectangles (so plain rings, stepped/L-shaped rings, T-shaped rings
and tiny solid blocks all occur). Exactly one shape per grid; no multi-shape or
multi-colour scenes.
"""

import collections
import random

import common


def _union_cells(rects):
  """Returns the set of (row, col) cells covered by the rectangles."""
  cells = set()
  for (r0, c0, hh, ww) in rects:
    for r in range(r0, r0 + hh):
      for c in range(c0, c0 + ww):
        cells.add((r, c))
  return cells


def _boundary(cells):
  """Inner 8-connected boundary: cells with any 8-neighbour outside."""
  out = set()
  for (r, c) in cells:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        if (dr or dc) and (r + dr, c + dc) not in cells:
          out.add((r, c))
          break
      if (r, c) in out:
        break
  return out


def _connected4(cells):
  """True if the cell set is 4-connected."""
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  queue = collections.deque([start])
  while queue:
    r, c = queue.popleft()
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
      nxt = (r + dr, c + dc)
      if nxt in cells and nxt not in seen:
        seen.add(nxt)
        queue.append(nxt)
  return len(seen) == len(cells)


def generate(width=None, height=None, color=None, rects=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the width of the grid
    height: the height of the grid
    color: the colour of the outline shape (1..9)
    rects: list of (row, col, h, w) rectangles whose union's inner 8-boundary
      forms the shape; the union must be 4-connected and at least 2 rows tall
  """
  if rects is None:
    for _ in range(500):
      width = random.randint(7, 20)
      height = random.randint(7, 20)
      color = random.randint(1, 9)
      n = random.choice([1, 1, 2, 2, 3])
      cand = []
      ok = True
      for _ in range(n):
        placed = False
        for _ in range(40):
          hh = random.randint(1, 6)
          ww = random.randint(2, 7)
          if not cand and hh < 2: continue
          if hh > height - 2 or ww > width - 2: continue
          r0 = random.randint(1, height - hh - 1)
          c0 = random.randint(1, width - ww - 1)
          trial = cand + [(r0, c0, hh, ww)]
          cells = _union_cells(trial)
          if not _connected4(cells): continue
          # Require the new rectangle to actually add something.
          if cand and len(cells) == len(_union_cells(cand)): continue
          cand = trial
          placed = True
          break
        if not placed:
          ok = False
          break
      if not ok: continue
      cells = _union_cells(cand)
      rows = [r for r, _ in cells]
      if max(rows) - min(rows) + 1 < 2: continue
      # Keep overall shape modest so the shear is readable.
      cols = [c for _, c in cells]
      if max(cols) - min(cols) + 1 > width - 1: continue
      rects = cand
      break

  cells = _union_cells(rects)
  shape = _boundary(cells)
  grid = common.grid(width, height, 0)
  output = common.grid(width, height, 0)
  ybot = max(r for r, _ in shape)
  for (r, c) in shape:
    grid[r][c] = color
    nc = c - (ybot - r)
    if 0 <= nc < width:
      output[r][nc] = color
  return {"input": grid, "output": output}


def validate():
  """Validates the generator against the canonical fixtures."""
  train = [
      generate(width=13, height=11, color=2,
               rects=[(3, 4, 3, 5), (6, 5, 3, 5)]),
      generate(width=11, height=10, color=6, rects=[(3, 4, 5, 3)]),
      generate(width=13, height=10, color=3,
               rects=[(3, 7, 2, 3), (5, 6, 3, 5)]),
      generate(width=7, height=7, color=8, rects=[(1, 1, 2, 3)]),
      generate(width=11, height=10, color=8, rects=[(2, 2, 5, 5)]),
  ]
  test = [
      generate(width=13, height=11, color=7,
               rects=[(3, 6, 1, 3), (4, 4, 3, 5), (7, 5, 3, 5)]),
  ]
  return {"train": train, "test": test}
