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

"""Generator for ARC task 52364a65.

Rule: the grid has a background of 8 and several solid-coloured, separated
objects.  For every object, the cells lying in the two leftmost columns of
that object's bounding box are erased (set back to 8).  Objects that are only
one or two columns wide disappear entirely; nothing else changes.

Scope: grid sizes 7..18 per side by default (fixtures use 8, 9 and 11),
two to six objects with pairwise distinct non-8 colours, each object a single
4-connected polyomino (rectangles, crosses / tees / combs / corners, H and U
shapes, and random polyominoes).  Objects never touch, not even diagonally.
Every random scene contains at least one object at least three columns wide
(so something survives) and at least one object whose left edge is ragged
(some row does not reach the bounding-box left column), which rules out the
competing reading "erase the first two cells of every row".  Same-coloured
objects and non-8 backgrounds are deliberately not generated.
"""

import random

import common

BACKGROUND = 8
TRIM_COLUMNS = 2


def _normalize(cells):
  """Shifts a cell collection so its bounding box starts at (0, 0)."""
  min_y = min(y for y, _ in cells)
  min_x = min(x for _, x in cells)
  return sorted(set((y - min_y, x - min_x) for y, x in cells))


def _shape_cells(shape):
  """Converts a list of '#'/'.' strings into normalized (dy, dx) cells."""
  cells = [(y, x) for y, line in enumerate(shape)
           for x, ch in enumerate(line) if ch == "#"]
  return _normalize(cells)


def _cells_to_shape(cells):
  """Converts normalized (dy, dx) cells into a list of '#'/'.' strings."""
  cells = _normalize(cells)
  h = max(y for y, _ in cells) + 1
  w = max(x for _, x in cells) + 1
  rows = [["."] * w for _ in range(h)]
  for y, x in cells:
    rows[y][x] = "#"
  return ["".join(r) for r in rows]


def _left_ragged(cells):
  """True if some row of the object does not reach its left bbox column."""
  leftmost = {}
  for y, x in cells:
    leftmost[y] = min(x, leftmost.get(y, x))
  return any(x > 0 for x in leftmost.values())


def _rect():
  h = random.randint(1, 4)
  w = random.randint(1, 6)
  return [(y, x) for y in range(h) for x in range(w)]


def _cross():
  """Full-height bar crossing a full-width bar: plus, tee, comb or corner."""
  h = random.randint(3, 6)
  w = random.randint(3, 7)
  tv = random.randint(1, 2)
  th = random.randint(1, 2)
  cx = random.randint(0, w - tv)
  cy = random.randint(0, h - th)
  cells = set()
  for y in range(h):
    for x in range(cx, cx + tv):
      cells.add((y, x))
  for y in range(cy, cy + th):
    for x in range(w):
      cells.add((y, x))
  return list(cells)


def _hshape():
  """Two full-height side columns joined by one full-width row (H or U)."""
  h = random.randint(3, 5)
  w = random.randint(3, 6)
  cy = random.randint(0, h - 1)
  cells = set()
  for y in range(h):
    cells.add((y, 0))
    cells.add((y, w - 1))
  for x in range(w):
    cells.add((cy, x))
  return list(cells)


def _polyomino():
  """Random 4-connected polyomino grown inside a 5x6 box."""
  size = random.randint(4, 12)
  box_h, box_w = 5, 6
  cells = {(random.randint(0, box_h - 1), random.randint(0, box_w - 1))}
  while len(cells) < size:
    frontier = set()
    for y, x in cells:
      for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < box_h and 0 <= nx < box_w and (ny, nx) not in cells:
          frontier.add((ny, nx))
    cells.add(random.choice(sorted(frontier)))
  return list(cells)


def _random_cells():
  roll = random.random()
  if roll < 0.30:
    cells = _rect()
  elif roll < 0.60:
    cells = _cross()
  elif roll < 0.75:
    cells = _hshape()
  else:
    cells = _polyomino()
  return _normalize(cells)


def _random_scene(width, height):
  """Samples a grid size and a list of separated latent objects."""
  palette = [c for c in range(10) if c != BACKGROUND]
  for _ in range(200):
    w = width if width is not None else random.randint(7, 18)
    h = height if height is not None else random.randint(7, 18)
    count = random.randint(2, max(2, min(6, (w * h) // 24)))
    colours = random.sample(palette, count)
    blocked = set()
    placed = []
    for colour in colours:
      cells = _random_cells()
      bh = max(y for y, _ in cells) + 1
      bw = max(x for _, x in cells) + 1
      if bh > h or bw > w:
        continue
      for _ in range(40):
        r = random.randint(0, h - bh)
        c = random.randint(0, w - bw)
        if all((r + y, c + x) not in blocked for y, x in cells):
          placed.append((colour, r, c, cells))
          for y, x in cells:
            for dy in (-1, 0, 1):
              for dx in (-1, 0, 1):
                blocked.add((r + y + dy, c + x + dx))
          break
    if len(placed) < 2:
      continue
    if not any(max(x for _, x in cells) >= TRIM_COLUMNS
               for _, _, _, cells in placed):
      continue
    if not any(_left_ragged(cells) for _, _, _, cells in placed):
      continue
    objects = [(colour, r, c, _cells_to_shape(cells))
               for colour, r, c, cells in placed]
    return w, h, objects
  # Bounded fallback: a fixed layout with random colours.
  colours = random.sample(palette, 3)
  objects = [
      (colours[0], 1, 1, ["#####", "#####"]),
      (colours[1], 4, 2, [".....#", "######", ".....#"]),
      (colours[2], 8, 0, ["#..#", "####", "#..#"]),
  ]
  return 12, 12, objects


def generate(width=None, height=None, objects=None):
  """Returns {"input": grid, "output": grid} for task 52364a65.

  Args:
    width: grid width, or None to sample.
    height: grid height, or None to sample.
    objects: list of (colour, row, col, shape) tuples; shape is a list of
      equal-length strings of '#' (cell) and '.' (empty) giving the object's
      cells relative to its bounding-box corner (row, col).  Objects must have
      distinct non-8 colours and must not touch (8-neighbourhood).  None
      samples a fresh scene.
  """
  if objects is None:
    width, height, objects = _random_scene(width, height)
  grid = common.grid(width, height, BACKGROUND)
  output = common.grid(width, height, BACKGROUND)
  for colour, row, col, shape in objects:
    for dy, dx in _shape_cells(shape):
      grid[row + dy][col + dx] = colour
      if dx >= TRIM_COLUMNS:
        output[row + dy][col + dx] = colour
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical train/test pairs from explicit parameters."""
  train = [
      generate(width=11, height=11, objects=[
          (0, 0, 2, ["..##..", "..##..", "######", "..##..", "..##.."]),
          (3, 5, 0, ["###.", "####"]),
          (9, 6, 8, ["###", "###"]),
          (6, 8, 0, ["###..", "#####", "...##"]),
      ]),
      generate(width=9, height=9, objects=[
          (9, 0, 1, ["#####", "#####"]),
          (0, 2, 2, [".....#", "######", ".....#"]),
          (2, 5, 1, ["#####", "..##.", "..#.."]),
          (3, 7, 7, ["##", "##"]),
      ]),
  ]
  test = [
      generate(width=8, height=8, objects=[
          (6, 0, 6, ["##", "##", "##"]),
          (4, 2, 0, ["#..#", "####", "#..#"]),
          (2, 6, 0, ["###", "###"]),
          (5, 6, 4, ["####", "####"]),
      ]),
  ]
  return {"train": train, "test": test}
