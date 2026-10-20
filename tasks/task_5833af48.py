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

"""ARC task 5833af48: stamp a motif into a rectangle following a pattern.

The input is a black (0) canvas holding three separated solid pieces:
  * a square motif of size m x m made only of 2 and 8, containing both,
  * a pattern rectangle of 8 and a fill colour C. It is a bh x bw block
    layout drawn at an integer scale f, so each layout cell is an f x f
    square, with f < m,
  * a big solid rectangle of colour C of size (bh*m) x (bw*m). It is the
    largest piece.
The output is the big rectangle split into bh x bw blocks of motif size.
Where the shrunk layout holds 8, the motif is stamped: its 8s stay 8 and its
2s become C. Every other block stays plain C.

Scope: the random motif side is 3..6. The fixtures only use 3 and 4, so 5
and 6 are synthetic extensions. The scale is 1..3 and always smaller than the
motif side; scale 3 is a synthetic extension. The block layout is 2..6 rows
by 2..8 columns, limited to what fits in 30x30. C is any colour except 0, 2
and 8. The pieces sit anywhere on the canvas with at least one black cell
between them, diagonals included. Colours 2 and 8 are fixed roles of the
task.
"""

import random

import common


def _separated(a, b):
  """True if boxes (r, c, h, w) are disjoint with a gap of at least one cell."""
  r1, c1, h1, w1 = a
  r2, c2, h2, w2 = b
  return (r1 + h1 < r2 or r2 + h2 < r1 or c1 + w1 < c2 or c2 + w2 < c1)


def _random_motif(m):
  cells = [(r, c) for r in range(m) for c in range(m)]
  count = random.randint(m, m * m - 2)
  eights = set(random.sample(cells, count))
  return [[8 if (r, c) in eights else 2 for c in range(m)] for r in range(m)]


def _random_small(bh, bw):
  cells = [(r, c) for r in range(bh) for c in range(bw)]
  count = random.randint(1, bh * bw - 1)
  ones = set(random.sample(cells, count))
  return [[1 if (r, c) in ones else 0 for c in range(bw)] for r in range(bh)]


def _stack_mins(m, bh, bw, f):
  """Minimum canvas size for the stacked layout (motif+pattern band, rect)."""
  rows_min = max(m, bh * f) + 1 + bh * m
  cols_min = max(m + 1 + bw * f, bw * m)
  return rows_min, cols_min


def _check_motif(motif):
  m = len(motif)
  if m < 2 or any(len(row) != m for row in motif):
    raise ValueError("motif must be a square of side >= 2")
  values = set(v for row in motif for v in row)
  if values != {2, 8}:
    raise ValueError("motif must contain both 2 and 8 and nothing else")


def _check_small(small):
  bh = len(small)
  if bh < 1 or len(small[0]) < 1 or any(len(r) != len(small[0]) for r in small):
    raise ValueError("small must be a non-empty rectangle")
  values = set(v for row in small for v in row)
  if values != {0, 1}:
    raise ValueError("small must contain both 0 and 1 and nothing else")


def generate(motif=None, small=None, scale=None, color=None, height=None,
             width=None, motif_pos=None, pattern_pos=None, rect_pos=None):
  """Generates an input/output pair.

  Args:
    motif: square list of rows containing only 2 and 8 (both present).
    small: bh x bw block layout as rows of 0/1, where 1 means stamp the
      motif. Must contain both values.
    scale: integer enlargement of the layout in the drawn pattern
      (1 <= scale < motif side).
    color: fill colour C of the pattern and the big rectangle (not 0, 2, 8).
    height: input grid height.
    width: input grid width.
    motif_pos: (row, col) of the motif's top-left corner.
    pattern_pos: (row, col) of the pattern's top-left corner.
    rect_pos: (row, col) of the big rectangle's top-left corner.
      Any subset of the three positions may be given; the rest are sampled.
  """
  for value in (height,width):
    if value is not None and (not isinstance(value,int) or not 1<=value<=30):
      raise ValueError("grid sides must be integers in 1..30")
  if scale is not None and not isinstance(scale,int):
    raise ValueError("scale must be an integer")
  sample_motif=motif is None
  if not sample_motif:
    _check_motif(motif)
    m=len(motif)
  if small is not None:
    _check_small(small)
  if scale is not None and (scale<1 or (not sample_motif and scale>=m) or (sample_motif and scale>=6)):
    raise ValueError("scale must satisfy 1 <= scale < motif side")
  chosen = None
  for _ in range(300):
    if sample_motif:
      m=random.choice([v for v in [3,3,4,4,5,6] if scale is None or v>scale])
      motif=_random_motif(m)
    scale_pool = [s for s in [1,1,2,2,3] if s<m]
    f = scale if scale is not None else random.choice(scale_pool)
    if small is not None:
      cbh, cbw = len(small), len(small[0])
    else:
      cbh, cbw = random.randint(2, 6), random.randint(2, 8)
    rows_min, cols_min = _stack_mins(m, cbh, cbw, f)
    # Free layouts must fit the requested canvas, not merely the ARC limit.
    # Pinned positions can use other arrangements than the fallback stack.
    pinned=any(pos is not None for pos in (motif_pos,pattern_pos,rect_pos))
    min_h=max(m,cbh*f,cbh*m) if pinned and height is not None else rows_min
    min_w=max(m,cbw*f,cbw*m) if pinned and width is not None else cols_min
    if min_h <= (height if height is not None else 30) and min_w <= (width if width is not None else 30):
      chosen = (f, cbh, cbw)
      break
  if chosen is None:
    raise ValueError("motif/scale/layout cannot fit in a 30x30 grid")
  f, bh, bw = chosen
  if small is None:
    small = _random_small(bh, bw)

  if color is None:
    color = random.choice([1, 3, 4, 5, 6, 7, 9])
  if color in (0, 2, 8) or not 0 <= color <= 9:
    raise ValueError("color must be a colour other than 0, 2 and 8")

  ph, pw = bh * f, bw * f
  rh, rw = bh * m, bw * m
  rows_min, cols_min = _stack_mins(m, bh, bw, f)
  if height is None:
    height = random.randint(rows_min, min(30, rows_min + 4))
  if width is None:
    width = random.randint(cols_min, min(30, cols_min + 4))
  if not (1 <= height <= 30 and 1 <= width <= 30):
    raise ValueError("grid sides must be within 1..30")

  sizes = [(m, m), (ph, pw), (rh, rw)]
  given = [motif_pos, pattern_pos, rect_pos]
  fixed = {}
  for i, pos in enumerate(given):
    if pos is not None:
      h, w = sizes[i]
      r0, c0 = pos
      if r0 < 0 or c0 < 0 or r0 + h > height or c0 + w > width:
        raise ValueError("given position puts a piece out of bounds")
      fixed[i] = (r0, c0, h, w)
  keys = list(fixed)
  for a in range(len(keys)):
    for b in range(a + 1, len(keys)):
      if not _separated(fixed[keys[a]], fixed[keys[b]]):
        raise ValueError("given pieces touch or overlap")

  placed = None
  order = [2, 1, 0]  # Largest piece first.
  for _ in range(400):
    boxes = dict(fixed)
    ok = True
    for i in order:
      if i in boxes:
        continue
      h, w = sizes[i]
      if h > height or w > width:
        ok = False
        break
      box = (random.randint(0, height - h), random.randint(0, width - w), h, w)
      if any(not _separated(box, other) for other in boxes.values()):
        ok = False
        break
      boxes[i] = box
    if ok:
      placed = boxes
      break
  if placed is None:
    if fixed or height < rows_min or width < cols_min:
      raise ValueError("could not place the pieces with the given constraints")
    # Randomised stacked layout that always fits by construction.
    dr = random.randint(0, height - rows_min)
    dc = random.randint(0, width - cols_min)
    band = max(m, ph)
    if random.random() < 0.5:
      band_r, rect_r = dr, dr + band + 1
    else:
      rect_r, band_r = dr, dr + rh + 1
    if random.random() < 0.5:
      placed = {0: (band_r, dc, m, m), 1: (band_r, dc + m + 1, ph, pw)}
    else:
      placed = {0: (band_r, dc + pw + 1, m, m), 1: (band_r, dc, ph, pw)}
    placed[2] = (rect_r, dc, rh, rw)

  grid = common.grid(width, height, 0)
  r0, c0 = placed[0][:2]
  for r in range(m):
    for c in range(m):
      grid[r0 + r][c0 + c] = motif[r][c]
  r0, c0 = placed[1][:2]
  for r in range(ph):
    for c in range(pw):
      grid[r0 + r][c0 + c] = 8 if small[r // f][c // f] else color
  r0, c0 = placed[2][:2]
  for r in range(rh):
    for c in range(rw):
      grid[r0 + r][c0 + c] = color

  output = [[color for _ in range(rw)] for _ in range(rh)]
  for by in range(bh):
    for bx in range(bw):
      if small[by][bx]:
        for r in range(m):
          for c in range(m):
            output[by * m + r][bx * m + c] = 8 if motif[r][c] == 8 else color
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical ARC pairs from explicit latent parameters."""
  train = [
      generate(motif=[[2, 8, 2], [8, 8, 8], [2, 8, 2]],
               small=[[0, 0, 1, 0, 0], [1, 0, 0, 0, 1], [0, 0, 1, 0, 0]],
               scale=1, color=3, height=16, width=18, motif_pos=(1, 1),
               pattern_pos=(1, 5), rect_pos=(5, 1)),
      generate(motif=[[2, 8, 2, 2], [8, 8, 2, 2], [2, 8, 8, 8],
                      [2, 8, 2, 2]],
               small=[[0, 1, 0, 0], [1, 0, 0, 1]],
               scale=2, color=1, height=17, width=18, motif_pos=(1, 1),
               pattern_pos=(1, 6), rect_pos=(6, 1)),
      generate(motif=[[2, 8, 2], [8, 2, 2], [8, 8, 8]],
               small=[[0, 1, 0], [1, 0, 1]],
               scale=2, color=4, height=15, width=15, motif_pos=(1, 0),
               pattern_pos=(1, 4), rect_pos=(6, 3)),
  ]
  test = [
      generate(motif=[[2, 8, 2, 8], [8, 8, 2, 2], [2, 2, 8, 8],
                      [8, 2, 8, 8]],
               small=[[0, 1, 0, 0, 1, 0], [1, 0, 0, 0, 0, 1],
                      [0, 1, 0, 0, 1, 0]],
               scale=1, color=1, height=19, width=27, motif_pos=(1, 1),
               pattern_pos=(1, 6), rect_pos=(6, 1)),
  ]
  return {"train": train, "test": test}
