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

"""ARC-GEN style generator for ARC task 17829a00.

Rule: the grid has background 7, a full top border row of colour TOP and a
full bottom border row of colour BOTTOM. The interior holds small
8-connected objects of exactly those two colours. Every TOP-coloured object
slides straight up until its highest cell sits in row 1. Every
BOTTOM-coloured object slides straight down until its lowest cell sits in row
H-2. There is one exception. Suppose an object touches the left or right wall
(column 0 or W-1) and its shifted copy overlaps its original footprint. That
object keeps both footprints, so it stretches to the border instead of
sliding.

Scope: grid width and height are sampled from 10..30 (all originals are
16x16). The two border colours are sampled from the non-background colours
and the background stays 7. Each colour gets one to five random 8-connected
shapes. Some scenes add an optional wall-hugging vertical bar whose shift is
smaller than its height, which exercises the stretch exception. The
generator rejects a placement in any of these cases:
  * the object overlaps another object;
  * the object is 8-adjacent to an object of the same colour, which would
    merge the two components;
  * the object's final footprint collides with another object's final
    footprint.
The module does not support other interior colours, horizontal movement, or
stacking of objects against each other.
"""

import random

import common

BG = 7
COLOURS = [0, 1, 2, 3, 4, 5, 6, 8, 9]


def _final_cells(cells, colour, top, height, width):
  """Return the output footprint of one object."""
  rows = [r for r, _ in cells]
  if colour == top:
    shift = 1 - min(rows)
  else:
    shift = (height - 2) - max(rows)
  orig = set(cells)
  moved = {(r + shift, c) for r, c in cells}
  wall = any(c == 0 or c == width - 1 for _, c in cells)
  if wall and (orig & moved):
    return orig | moved
  return moved


def _random_shape():
  """Random 8-connected shape normalised to the origin."""
  bh = random.randint(1, 4)
  bw = random.randint(1, 3)
  size = random.randint(1, min(6, bh * bw))
  cells = {(random.randrange(bh), random.randrange(bw))}
  tries = 0
  while len(cells) < size and tries < 60:
    tries += 1
    r, c = random.choice(sorted(cells))
    nr, nc = r + random.randint(-1, 1), c + random.randint(-1, 1)
    if 0 <= nr < bh and 0 <= nc < bw:
      cells.add((nr, nc))
  mr = min(r for r, _ in cells)
  mc = min(c for _, c in cells)
  return sorted((r - mr, c - mc) for r, c in cells)


def _sample_scene(width, height, top, bottom):
  """Sample a list of (colour, cells) objects satisfying all constraints."""
  for _ in range(200):
    placed = []
    occupied = {}
    finals = set()

    def try_add(colour, cells):
      for r, c in cells:
        if not (1 <= r <= height - 2 and 0 <= c < width):
          return False
        if (r, c) in occupied:
          return False
        for dr in (-1, 0, 1):
          for dc in (-1, 0, 1):
            if occupied.get((r + dr, c + dc)) == colour:
              return False
      fin = _final_cells(cells, colour, top, height, width)
      if fin & finals:
        return False
      for cell in cells:
        occupied[cell] = colour
      finals.update(fin)
      placed.append((colour, list(cells)))
      return True

    if random.random() < 0.35:
      colour = random.choice([top, bottom])
      hb = random.randint(2, 4)
      s = random.randint(1, hb - 1)
      col = random.choice([0, width - 1])
      if colour == top:
        r0 = 1 + s
      else:
        r0 = height - 2 - s - hb + 1
      try_add(colour, [(r0 + i, col) for i in range(hb)])

    order = [top] * random.randint(1, 5) + [bottom] * random.randint(1, 5)
    random.shuffle(order)
    for colour in order:
      shape = _random_shape()
      sh = max(r for r, _ in shape) + 1
      sw = max(c for _, c in shape) + 1
      for _ in range(40):
        r0 = random.randint(1, height - 1 - sh)
        c0 = random.randint(0, width - sw)
        if try_add(colour, [(r + r0, c + c0) for r, c in shape]):
          break

    colours = {col for col, _ in placed}
    moving = any(
        _final_cells(cells, col, top, height, width) != set(cells)
        for col, cells in placed)
    if len(placed) >= 3 and moving and colours == {top, bottom}:
      return placed
  raise RuntimeError("could not place both colour groups with non-overlapping outputs")


def generate(width=None, height=None, top=None, bottom=None, objects=None):
  """Generate one input/output pair.

  Args:
    width: grid width (columns); sampled from 10..30 if None.
    height: grid height (rows); sampled from 10..30 if None.
    top: colour of the top border row and of objects that rise.
    bottom: colour of the bottom border row and of objects that sink.
    objects: optional list of (colour, [(row, col), ...]) interior objects in
      absolute coordinates; each must be 8-connected and of colour top or
      bottom. Sampled if None.
  """
  if width is None:
    width = random.randint(10, 30)
  if height is None:
    height = random.randint(10, 30)
  if top is None:
    top = random.choice([c for c in COLOURS if c != bottom])
  if bottom is None:
    bottom = random.choice([c for c in COLOURS if c != top])
  if not (10 <= width <= 30 and 10 <= height <= 30):
    raise ValueError("grid dimensions must be 10..30")
  if top not in COLOURS or bottom not in COLOURS or top == bottom:
    raise ValueError("border colours must be distinct and not background")
  if objects is None:
    objects = _sample_scene(width, height, top, bottom)

  grid = common.grid(width, height, BG)
  out = common.grid(width, height, BG)
  for c in range(width):
    grid[0][c] = top
    grid[height - 1][c] = bottom
    out[0][c] = top
    out[height - 1][c] = bottom
  for colour, cells in objects:
    for r, c in cells:
      grid[r][c] = colour
  for colour, cells in objects:
    if colour == top:
      for r, c in _final_cells(cells, colour, top, height, width):
        out[r][c] = colour
  for colour, cells in objects:
    if colour != top:
      for r, c in _final_cells(cells, colour, top, height, width):
        out[r][c] = colour
  return {"input": grid, "output": out}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=16, height=16, top=9, bottom=8, objects=[
          (9, [(3, 1), (3, 2), (4, 2)]),
          (9, [(3, 5), (4, 5), (5, 5)]),
          (9, [(3, 8), (4, 7), (4, 8), (4, 9), (5, 8)]),
          (9, [(9, 12), (10, 11), (10, 12), (10, 13), (11, 12), (12, 12)]),
          (8, [(7, 1), (8, 0), (8, 2), (9, 1), (10, 1)]),
          (8, [(8, 5), (9, 4), (9, 5), (9, 6), (10, 4), (10, 6)]),
          (8, [(9, 9), (10, 10)]),
          (8, [(10, 15), (11, 15), (12, 15)]),
          (8, [(13, 12)]),
      ]),
      generate(width=16, height=16, top=2, bottom=5, objects=[
          (2, [(3, 4), (4, 5), (5, 5)]),
          (2, [(3, 11), (3, 13), (4, 12)]),
          (2, [(6, 15), (7, 15)]),
          (2, [(10, 6), (10, 7)]),
          (5, [(5, 12), (6, 11), (6, 12), (6, 13)]),
          (5, [(8, 2), (9, 1), (9, 2), (9, 3)]),
          (5, [(10, 9), (11, 10)]),
      ]),
  ]
  test = [
      generate(width=16, height=16, top=1, bottom=4, objects=[
          (1, [(5, 0), (6, 1), (7, 2)]),
          (1, [(4, 6), (5, 6), (6, 6), (7, 5), (7, 7), (7, 8)]),
          (1, [(4, 10), (5, 9), (5, 11)]),
          (4, [(1, 12), (2, 12)]),
          (4, [(8, 15), (9, 14), (9, 15)]),
          (4, [(9, 5), (9, 6), (9, 7), (10, 4), (10, 8)]),
      ]),
  ]
  return {"train": train, "test": test}
