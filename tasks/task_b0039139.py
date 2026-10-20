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

"""ARC task b0039139: replicate a motif once per bar.

The input holds four panels split by full lines of colour 1. The panels are
stacked vertically (divider rows) or placed side by side (divider columns).
  1. A colour-4 motif. Its tight bounding box fills the panel, leaving a
     one-cell border of 0.
  2. n separated colour-3 dominoes (bars) on 0.
  3. A solid block of colour A.
  4. A solid block of colour B.

The output is built as follows:
  - Crop the motif to its bounding box.
  - Paint shape cells A and empty cells B.
  - Lay out n copies along the panel direction.
  - Put a one-cell line of B between neighbouring copies.

Scope:
  - Both orientations are sampled.
  - Motif sizes are 2..6 x 2..5. Motifs are random connected shapes with at
    least one hole cell and a tight bounding box.
  - The bar count is 2..6. Bars are vertical or horizontal dominoes. No two
    bars touch, even diagonally.
  - Panel lengths vary.
  - A and B are distinct colours from 2..9.
"""

import random

import common


def _transpose(g):
  return [list(r) for r in zip(*g)]


def _random_motif(h, w):
  """Connected 0/1 motif of size h x w.

  Every row and column holds a shape cell, and at least one cell is empty.
  """
  for _ in range(300):
    k = random.randint(max(h, w), h * w - 1)
    start = (random.randrange(h), random.randrange(w))
    cells = {start}
    while len(cells) < k:
      frontier = []
      for (r, c) in cells:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
          nr, nc = r + dr, c + dc
          if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in cells:
            frontier.append((nr, nc))
      if not frontier:
        break
      cells.add(random.choice(frontier))
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    if len(rows) == h and len(cols) == w and len(cells) < h * w:
      return [[1 if (r, c) in cells else 0 for c in range(w)] for r in range(h)]
  m = [[1] * w for _ in range(h)]
  m[0][0] = 0
  return m


def _place_bars(n, height, length):
  """Place n dominoes inside a 0-bordered height x length panel.

  No two dominoes touch, even diagonally. Returns None if placement fails.
  """
  for _ in range(100):
    bars, used = [], set()
    ok = True
    for _ in range(n):
      placed = False
      for _ in range(200):
        vert = random.random() < 0.5
        r = random.randint(1, height - 2)
        c = random.randint(1, length - 2)
        cells = [(r, c), (r + 1, c)] if vert else [(r, c), (r, c + 1)]
        if any(not (1 <= rr <= height - 2 and 1 <= cc <= length - 2)
               for rr, cc in cells):
          continue
        if any((rr + dr, cc + dc) in used for rr, cc in cells
               for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
          continue
        bars.append(cells)
        used.update(cells)
        placed = True
        break
      if not placed:
        ok = False
        break
    if ok:
      return bars
  return None


def generate(stacked=None, motif=None, bars=None, len2=None, len3=None,
             len4=None, color_a=None, color_b=None):
  """Build one input/output pair.

  Args:
    stacked: True when panels are stacked vertically (divider rows). False
      when panels sit side by side (divider columns).
    motif: 0/1 rows of the cropped motif in its native orientation.
    bars: list of bars. Each bar is a pair of (row, col) cells in native
      panel-2 local coordinates.
    len2: panel-2 length along the layout direction.
    len3: panel-3 length along the layout direction.
    len4: panel-4 length along the layout direction.
    color_a: colour of panel 3. Shape cells take this colour.
    color_b: colour of panel 4. Empty cells and separators take this colour.
  """
  if stacked is None:
    stacked = random.random() < 0.5
  if color_a is None:
    color_a = random.choice([c for c in range(2, 10) if c != color_b])
  if color_b is None:
    color_b = random.choice([c for c in range(2, 10) if c != color_a])
  if color_a == color_b or color_a not in range(2, 10) or color_b not in range(2, 10):
    raise ValueError("A and B must be distinct colours from 2..9")
  if motif is None:
    if any(v is not None for v in (bars, len2, len3, len4)):
      raise ValueError("explicit bars or panel lengths require an explicit motif")
    for _ in range(100):
      h = random.randint(2, 6)  # cross extent (horizontal frame)
      w = random.randint(2, 5)  # along extent (horizontal frame)
      nmax = min(6, 31 // (w + 1))
      n = random.randint(2, nmax)
      budget = 30 - (w + 2) - 3
      l2 = random.randint(4, min(10, budget - 4))
      hb = _place_bars(n, h + 2, l2)
      if hb is None:
        continue
      rest = budget - l2
      l3 = random.randint(2, min(8, rest - 2))
      l4 = random.randint(2, min(8, rest - l3))
      mh = _random_motif(h, w)
      break
    else:
      raise RuntimeError("could not place bars within the scene budget")
    if stacked:
      motif = _transpose(mh)
      bars = [[(c, r) for r, c in b] for b in hb]
    else:
      motif = mh
      bars = hb
    len2, len3, len4 = l2, l3, l4
  # Convert to the horizontal frame: cross axis = rows, layout axis = cols.
  if stacked:
    mh = _transpose(motif)
    hb = [[(c, r) for r, c in b] for b in bars]
  else:
    mh = [list(r) for r in motif]
    hb = [list(b) for b in bars]
  h, w = len(mh), len(mh[0])
  height = h + 2
  width = (w + 2) + len2 + len3 + len4 + 3
  grid = common.grid(width, height, 0)
  for r in range(h):
    for c in range(w):
      if mh[r][c]:
        grid[r + 1][c + 1] = 4
  x = w + 2
  for r in range(height):
    grid[r][x] = 1
  p2 = x + 1
  for b in hb:
    for r, c in b:
      grid[r][p2 + c] = 3
  x = p2 + len2
  for r in range(height):
    grid[r][x] = 1
  for c in range(x + 1, x + 1 + len3):
    for r in range(height):
      grid[r][c] = color_a
  x = x + 1 + len3
  for r in range(height):
    grid[r][x] = 1
  for c in range(x + 1, x + 1 + len4):
    for r in range(height):
      grid[r][c] = color_b
  n = len(hb)
  out = common.grid(n * w + n - 1, h, color_b)
  for i in range(n):
    for r in range(h):
      for c in range(w):
        out[r][i * (w + 1) + c] = color_a if mh[r][c] else color_b
  if stacked:
    grid = _transpose(grid)
    out = _transpose(out)
  return {"input": grid, "output": out}


def validate():
  """Rebuild the canonical fixtures from explicit latent parameters."""
  v2 = lambda r, c: [(r, c), (r + 1, c)]
  h2 = lambda r, c: [(r, c), (r, c + 1)]
  train = [
      generate(stacked=True, motif=[[1, 1], [1, 0]],
               bars=[v2(1, 1), v2(1, 3)], len2=4, len3=4, len4=3,
               color_a=2, color_b=9),
      generate(stacked=False, motif=[[1, 1, 1], [0, 1, 0], [1, 1, 1]],
               bars=[v2(1, 1), v2(1, 3), v2(1, 5)], len2=7, len3=5, len4=3,
               color_a=8, color_b=3),
      generate(stacked=False,
               motif=[[1, 1, 0], [1, 0, 0], [1, 1, 1], [0, 1, 0]],
               bars=[v2(1, 1), v2(1, 3), h2(4, 1), h2(4, 4)], len2=7,
               len3=6, len4=6, color_a=6, color_b=4),
      generate(stacked=False, motif=[[1, 1, 1], [1, 0, 1]],
               bars=[v2(1, 1), v2(1, 3)], len2=6, len3=5, len4=4,
               color_a=2, color_b=8),
  ]
  test = [
      generate(stacked=True,
               motif=[[1, 1, 0, 1, 1], [1, 0, 0, 0, 1], [1, 1, 1, 1, 1]],
               bars=[v2(1, 1), v2(1, 3), v2(1, 5), h2(4, 1), h2(4, 4)],
               len2=6, len3=6, len4=6, color_a=8, color_b=7),
      generate(stacked=False,
               motif=[[1, 1, 0, 1], [0, 1, 0, 1], [0, 1, 1, 1], [0, 1, 0, 1],
                      [1, 1, 0, 1]],
               bars=[h2(1, 1), h2(1, 4), h2(3, 1), h2(3, 4), h2(5, 1),
                     h2(5, 4)],
               len2=7, len3=8, len4=5, color_a=5, color_b=2),
  ]
  return {"train": train, "test": test}
