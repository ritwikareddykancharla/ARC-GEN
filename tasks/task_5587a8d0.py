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

"""Generator for ARC task 5587a8d0: object sizes become concentric rings.

Rule: the input is a background-7 grid holding a few small single-colour
objects whose cell counts are pairwise distinct.  Sort the objects by size,
largest first.  With n objects the output is a (2n-1)x(2n-1) square; ring k
(cells whose distance to the nearest border is k) takes the colour of the
k-th largest object, so the largest object is the outer frame and the
smallest object is the single centre cell.

Scope: 2..6 objects, each a random 4-connected polyomino of 1..12 cells with
distinct sizes and distinct non-background colours, placed so that no two
objects touch even diagonally.  Input grids are 6..16 cells per side; the
background colour 7 is intrinsic to the task and kept fixed.  Shapes and
positions are deliberately irrelevant to the answer.
"""

import random
import common


BACKGROUND = 7


def _shape_cells(shape):
  """Returns the (dr, dc) offsets marked with '#' in a list of strings."""
  cells = []
  for dr, row in enumerate(shape):
    for dc, ch in enumerate(row):
      if ch == "#":
        cells.append((dr, dc))
  return cells


def _random_shape(size):
  """Grows a random 4-connected polyomino with `size` cells inside a box."""
  boxes = [(bh, bw) for bh in range(1, 5) for bw in range(1, 5) if bh * bw >= size]
  bh, bw = random.choice(boxes)
  cells = {(random.randrange(bh), random.randrange(bw))}
  while len(cells) < size:
    frontier = set()
    for r, c in cells:
      for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < bh and 0 <= nc < bw and (nr, nc) not in cells:
          frontier.add((nr, nc))
    cells.add(random.choice(sorted(frontier)))
  min_r = min(r for r, _ in cells)
  min_c = min(c for _, c in cells)
  cells = {(r - min_r, c - min_c) for r, c in cells}
  h = max(r for r, _ in cells) + 1
  w = max(c for _, c in cells) + 1
  return ["".join("#" if (r, c) in cells else "." for c in range(w))
          for r in range(h)]


def _place_objects(width, height, sizes, colours):
  """Tries to place polyominoes of the given sizes without 8-adjacency."""
  blocked = [[False] * width for _ in range(height)]
  objects = []
  for size, colour in zip(sizes, colours):
    shape = _random_shape(size)
    cells = _shape_cells(shape)
    sh, sw = len(shape), len(shape[0])
    if sh > height or sw > width:
      return None
    placed = False
    for _ in range(60):
      r0 = random.randint(0, height - sh)
      c0 = random.randint(0, width - sw)
      if all(not blocked[r0 + dr][c0 + dc] for dr, dc in cells):
        placed = True
        break
    if not placed:
      return None
    for dr, dc in cells:
      for ar in range(-1, 2):
        for ac in range(-1, 2):
          rr, cc = r0 + dr + ar, c0 + dc + ac
          if 0 <= rr < height and 0 <= cc < width:
            blocked[rr][cc] = True
    objects.append((colour, r0, c0, shape))
  return objects


def generate(width=None, height=None, objects=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: width of the input grid.
    height: height of the input grid.
    objects: list of (colour, row, col, shape) tuples, where shape is a list
      of equal-length strings using '#' for object cells and '.' for gaps.
      Object cell counts must be pairwise distinct.
  """
  if objects is None:
    lo = 6
    for _ in range(200):
      n = random.randint(2, 6)
      w = random.randint(lo, 16)
      h = random.randint(lo, 16)
      sizes = random.sample(range(1, 13), n)
      colours = random.sample([c for c in range(10) if c != BACKGROUND], n)
      order = list(range(n))
      random.shuffle(order)
      placed = _place_objects(w, h, [sizes[i] for i in order],
                              [colours[i] for i in order])
      if placed is not None:
        width, height, objects = w, h, placed
        break
      lo = min(16, lo + 1)
    else:
      raise RuntimeError("could not place objects")

  grid = common.grid(width, height, BACKGROUND)
  ranked = []
  for colour, r0, c0, shape in objects:
    cells = _shape_cells(shape)
    for dr, dc in cells:
      grid[r0 + dr][c0 + dc] = colour
    ranked.append((len(cells), colour))
  if len({s for s, _ in ranked}) != len(ranked):
    raise ValueError("object sizes must be distinct")
  ranked.sort(key=lambda sc: -sc[0])
  ring_colours = [colour for _, colour in ranked]
  s = 2 * len(ring_colours) - 1
  output = [[ring_colours[min(r, c, s - 1 - r, s - 1 - c)] for c in range(s)]
            for r in range(s)]
  return {"input": grid, "output": output}


def validate():
  """Validates the generator by reconstructing the canonical fixtures."""
  train = [
      generate(width=6, height=6, objects=[
          (4, 1, 3, ["##", "##"]),
          (6, 3, 0, ["#.", "##"]),
      ]),
      generate(width=9, height=9, objects=[
          (8, 0, 5, [".#", ".#", "###"]),
          (5, 2, 1, ["##", "##"]),
          (1, 5, 3, ["###", "#.#", "###"]),
      ]),
      generate(width=7, height=7, objects=[
          (8, 1, 1, ["###", "#.#", "###"]),
          (3, 1, 5, ["##"]),
          (9, 4, 5, ["#"]),
          (0, 5, 0, ["##", "##"]),
      ]),
  ]
  test = [
      generate(width=8, height=8, objects=[
          (9, 0, 2, ["#", "#"]),
          (2, 0, 5, ["###", "#.#"]),
          (5, 2, 0, ["#.", "##", "#."]),
          (8, 3, 3, ["#"]),
          (0, 4, 5, ["#..", "##.", ".##", "..#"]),
          (1, 5, 0, ["..#..", ".###.", "#####"]),
      ]),
  ]
  return {"train": train, "test": test}
