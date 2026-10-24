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

"""Generator for ARC task ecb67b6d.

Rule: the grid has background 7 and grey (5) shapes.  Shapes are taken as
8-connected components (diagonal contact counts).  A shape is recoloured
entirely to 8 when it contains a straight diagonal run of at least three
5-cells in either diagonal direction; every other shape stays 5.  Nothing
moves and nothing is added.

Scope: grids from 5x4 up to 30x30 with several separated shapes drawn from
two families.  "Diagonal" shapes contain a 3+ diagonal run (pure diagonal
lines, diagonal lines with extra attached cells, orthogonal blobs with a
diagonal tail).  "Plain" shapes never contain such a run (singletons,
dominoes, two-cell diagonal pairs, rectangles, L-shapes, zig-zags and small
random blobs); they act as distractors, including near misses such as
2-cell diagonals and zig-zags.  Shapes are always separated by at least one
background cell in every direction so each shape is its own component.
"""

import random

import common

BACKGROUND = 7
FOREGROUND = 5
RECOLOUR = 8

NEIGHBOURS8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0),
               (1, 1)]


def _has_diagonal_run(cells, length=3):
  """True when the cell set holds a straight diagonal run of `length` cells."""
  cellset = set(cells)
  for (r, c) in cellset:
    for dr, dc in ((1, 1), (1, -1)):
      if all((r + k * dr, c + k * dc) in cellset for k in range(length)):
        return True
  return False


def _normalise(cells):
  """Shifts a cell collection so its bounding box starts at (0, 0)."""
  min_r = min(r for r, _ in cells)
  min_c = min(c for _, c in cells)
  return sorted({(r - min_r, c - min_c) for r, c in cells})


def _bbox(cells):
  rows = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
  cols = max(c for _, c in cells) - min(c for _, c in cells) + 1
  return rows, cols


def _random_flip(cells):
  """Applies a random horizontal / vertical flip, then normalises."""
  if random.random() < 0.5:
    cells = [(r, -c) for r, c in cells]
  if random.random() < 0.5:
    cells = [(-r, c) for r, c in cells]
  return _normalise(cells)


# ---------------------------------------------------------------------------
# Shapes that DO contain a diagonal run of three (recoloured to 8).
# ---------------------------------------------------------------------------


def _diag_line(n=None):
  n = n if n is not None else random.randint(3, 6)
  cells = [(k, k) for k in range(n)]
  return _random_flip(cells)


def _diag_decorated():
  """Diagonal line plus one to three extra attached cells (like train 1)."""
  for _ in range(20):
    cells = set(_diag_line(random.randint(3, 5)))
    extras = random.randint(1, 3)
    for _ in range(extras):
      r, c = random.choice(sorted(cells))
      dr, dc = random.choice(NEIGHBOURS8)
      cells.add((r + dr, c + dc))
    cells = _normalise(cells)
    rows, cols = _bbox(cells)
    if rows <= 6 and cols <= 6 and _has_diagonal_run(cells):
      return _random_flip(cells)
  return _diag_line()


def _blob_with_tail():
  """Orthogonal block whose corner continues into a 2-cell diagonal tail."""
  h = random.randint(1, 3)
  w = random.randint(1, 3)
  if h * w == 1:
    w = 2
  cells = {(r, c) for r in range(h) for c in range(w)}
  if random.random() < 0.4 and h >= 2 and w >= 2:
    cells.discard((0, 0))  # L-shape instead of a full rectangle
  cells.add((h, w))
  cells.add((h + 1, w + 1))
  return _random_flip(sorted(cells))


def _irregular_shape(want_diagonal):
  """Grow larger 8-connected shapes, keeping the requested diagonal predicate."""
  for _ in range(120):
    cells = {(0,0),(1,1),(2,2)} if want_diagonal else {(0,0)}
    size = random.randint(7, 18)
    for _ in range(150):
      if len(cells) >= size:
        return _random_flip(sorted(cells))
      r,c = random.choice(sorted(cells))
      dr,dc = random.choice(NEIGHBOURS8)
      proposed = cells | {(r+dr,c+dc)}
      h,w = _bbox(_normalise(proposed))
      if max(h,w) > 9: continue
      if not want_diagonal and _has_diagonal_run(proposed): continue
      cells = proposed
  raise RuntimeError('could not grow requested irregular shape')


def _random_diag_shape():
  if random.random() < 0.35:
    return _irregular_shape(True)
  roll = random.random()
  if roll < 0.40:
    return _diag_line()
  if roll < 0.75:
    return _diag_decorated()
  return _blob_with_tail()


# ---------------------------------------------------------------------------
# Shapes that do NOT contain a diagonal run of three (stay 5).
# ---------------------------------------------------------------------------


def _singleton():
  return [(0, 0)]


def _domino():
  return [(0, 0), (0, 1)] if random.random() < 0.5 else [(0, 0), (1, 0)]


def _diag_pair():
  return [(0, 0), (1, 1)] if random.random() < 0.5 else [(0, 1), (1, 0)]


def _rect():
  h = random.randint(1, 4)
  w = random.randint(1, 4)
  if h * w == 1:
    w = random.randint(2, 4)
  return [(r, c) for r in range(h) for c in range(w)]


def _ell():
  a = random.randint(2, 5)
  b = random.randint(2, 5)
  cells = {(r, 0) for r in range(a)} | {(a - 1, c) for c in range(b)}
  return _random_flip(sorted(cells))


def _zigzag():
  n = random.randint(3, 6)
  if random.random() < 0.5:
    cells = [(k % 2, k) for k in range(n)]
  else:
    cells = [(k, k % 2) for k in range(n)]
  return _random_flip(cells)


def _plain_blob():
  for _ in range(25):
    size = random.randint(3, 6)
    cells = {(0, 0)}
    while len(cells) < size:
      r, c = random.choice(sorted(cells))
      dr, dc = random.choice(NEIGHBOURS8)
      cells.add((r + dr, c + dc))
    cells = _normalise(cells)
    rows, cols = _bbox(cells)
    if rows <= 4 and cols <= 4 and not _has_diagonal_run(cells):
      return cells
  return _rect()


def _random_plain_shape():
  if random.random() < 0.35:
    return _irregular_shape(False)
  roll = random.random()
  if roll < 0.15:
    cells = _singleton()
  elif roll < 0.25:
    cells = _domino()
  elif roll < 0.37:
    cells = _diag_pair()
  elif roll < 0.52:
    cells = _rect()
  elif roll < 0.66:
    cells = _ell()
  elif roll < 0.82:
    cells = _zigzag()
  else:
    cells = _plain_blob()
  if _has_diagonal_run(cells):  # should never happen; stay safe
    cells = _singleton()
  return cells


# ---------------------------------------------------------------------------
# Scene assembly.
# ---------------------------------------------------------------------------


def _place(halo, shape, width, height, tries=40):
  """Places a normalised shape at a random spot avoiding the halo set."""
  rows, cols = _bbox(shape)
  if rows > height or cols > width:
    return None
  for _ in range(tries):
    oy = random.randint(0, height - rows)
    ox = random.randint(0, width - cols)
    placed = [(r + oy, c + ox) for r, c in shape]
    if any(p in halo for p in placed):
      continue
    for (r, c) in placed:
      for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
          halo.add((r + dr, c + dc))
    return placed
  return None


def _random_scene(width, height):
  """Returns a list of (kind, cells) with 8-separated shapes."""
  area = width * height
  target = max(2, int(round(area / random.uniform(9.0, 18.0))))
  frac = random.uniform(0.25, 0.6)
  n_diag = max(1, int(round(target * frac)))
  n_plain = max(1, target - n_diag)
  specs = [("diag", _random_diag_shape()) for _ in range(n_diag)]
  specs += [("plain", _random_plain_shape()) for _ in range(n_plain)]
  random.shuffle(specs)
  halo = set()
  shapes = []
  for kind, cells in specs:
    placed = _place(halo, cells, width, height)
    if placed is not None:
      shapes.append((kind, placed))
  return shapes


def generate(width=None, height=None, shapes=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: grid width (sampled 5..30 when None).
    height: grid height (sampled 4..30 when None).
    shapes: optional explicit list of shapes, each a list of (row, col)
      cells of a single 8-connected grey component.  Shapes must not
      overlap and should be separated by at least one background cell so
      that each listed shape is its own component.  When None, a fresh
      random scene of diagonal and plain shapes is constructed.
  """
  if shapes is None:
    kinds = None
    for _ in range(80):
      w = width if width is not None else random.randint(5, 30)
      h = height if height is not None else random.randint(4, 30)
      scene = _random_scene(w, h)
      present = {kind for kind, _ in scene}
      if "diag" in present and "plain" in present:
        width, height = w, h
        kinds = [kind for kind, _ in scene]
        shapes = [cells for _, cells in scene]
        break
    if kinds is None:
      raise RuntimeError("could not place both shape classes; no fixed fallback")
  else:
    if width is None or height is None:
      raise ValueError("width and height are required with explicit shapes")
    kinds = ["diag" if _has_diagonal_run(cells) else "plain"
             for cells in shapes]

  grid = common.grid(width, height, BACKGROUND)
  output = common.grid(width, height, BACKGROUND)
  seen = set()
  for kind, cells in zip(kinds, shapes):
    colour = RECOLOUR if kind == "diag" else FOREGROUND
    for (r, c) in cells:
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError("shape cell out of bounds")
      if (r, c) in seen:
        raise ValueError("overlapping shapes")
      seen.add((r, c))
      grid[r][c] = FOREGROUND
      output[r][c] = colour
  return {"input": grid, "output": output}


def validate():
  """Validates the generator against the original train/test fixtures."""
  train = [
      generate(width=8, height=6, shapes=[
          [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (5, 1), (5, 2)],
          [(0, 2), (1, 2), (1, 3), (0, 4)],
          [(0, 7), (1, 6), (2, 5), (2, 6), (3, 4), (3, 6), (4, 6)],
      ]),
      generate(width=5, height=4, shapes=[
          [(0, 3), (1, 1), (1, 2), (2, 0), (2, 1)],
          [(3, 3), (3, 4)],
      ]),
      generate(width=11, height=12, shapes=[
          [(r, c) for r in range(1, 5) for c in range(0, 2)],
          [(0, 4), (0, 5), (1, 4), (1, 5), (2, 5)],
          [(0, 8), (1, 9), (1, 10), (2, 10)],
          [(2, 7)],
          [(4, 5), (4, 6), (5, 6), (6, 6), (7, 6)],
          [(4, 10), (5, 9), (6, 8)],
          [(6, 1)],
          [(6, 3), (6, 4), (7, 4)],
          [(8, 0), (9, 0), (9, 1), (10, 1), (10, 2), (11, 1), (11, 2),
           (11, 3)],
          [(9, 4), (10, 5), (9, 6), (10, 7), (9, 8), (10, 9)],
          [(8, 10)],
      ]),
  ]
  test = [
      generate(width=19, height=16, shapes=[
          [(0, 1), (0, 2), (1, 2), (2, 2), (3, 3), (4, 3), (5, 3), (5, 1),
           (6, 1), (6, 2), (6, 4)],
          [(0, 8), (0, 9), (0, 10), (0, 11), (1, 11), (1, 12), (1, 13),
           (0, 14)],
          [(1, 16), (2, 15), (2, 16), (3, 15), (3, 17), (4, 17), (4, 18),
           (5, 17), (5, 18), (6, 18), (7, 17)],
          [(2, 7), (2, 9), (3, 7), (3, 8), (4, 9), (5, 10)],
          [(3, 0)],
          [(2, 5)],
          [(4, 5)],
          [(3, 13)],
          [(6, 14), (6, 15)],
          [(7, 6), (7, 7), (8, 5), (8, 6), (8, 8), (8, 9), (9, 6), (9, 7),
           (9, 10), (10, 10)],
          [(7, 11), (7, 12), (8, 12), (8, 13)],
          [(8, 2)],
          [(9, 16), (10, 17), (10, 18), (11, 17), (12, 17), (12, 18)],
          [(10, 0), (11, 1), (11, 2), (11, 3), (12, 1), (13, 1), (13, 2)],
          [(10, 12)],
          [(11, 8), (12, 8), (12, 9), (13, 6), (13, 8), (13, 9), (14, 5),
           (14, 6), (14, 8), (15, 6), (15, 7)],
          [(12, 14), (13, 11), (13, 12), (13, 13), (13, 15), (14, 14),
           (14, 15), (14, 16), (15, 14)],
          [(14, 18)],
      ]),
  ]
  return {"train": train, "test": test}
