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

"""ARC task 409aa875: three-cell pointers mark the cell five steps ahead.

Rule: the background (7) holds small three-cell shapes, all one colour.
Each shape is either a chevron (^, v, <, >) or an L.
- A chevron points away from its two feet, through its apex.
- An L points diagonally away from its two arms, through its corner.
For every shape, the target is the tip cell moved 5 steps in the pointing
direction.
- If the target lies on a shape cell, that whole shape is recoloured 9.
- Otherwise the target becomes 9, or 1 when two or more shapes share it.

Scope: the background is fixed at 7, as in every example. About 40% of
random scenes use the native 16x16 size. The rest use synthetic sizes, with
each side drawn from 10..30. The shape count is capped by the grid area
(at most 9). Directions come from all 8 (four chevrons and four L
orientations). The shape colour comes from a palette that excludes 7 and 1.
Some scenes start with an evenly spaced band of same-direction shapes, as in
train pair 3. Some shapes are placed on purpose so that their target falls
on an existing target (collision -> 1). Others aim at a cell of another
shape (that shape is recoloured).

Invariants:
- Shapes never touch, not even diagonally, so each is its own 8-connected
  component.
- Every random target lies inside the grid.
- When the shape colour is 9, hits on shapes are disallowed, because a
  recolouring to 9 would be invisible.
"""

import random

import common

_BG = 7
_HIT = 9
_DUP = 1
_PALETTE = [0, 2, 3, 4, 5, 6, 8, 9]
_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
         (-1, -1), (-1, 1), (1, -1), (1, 1)]
_STEP = 5
_MIN_SIDE = 7


def _cells(r, c, dy, dx):
  """Cells of a shape with tip (r, c) pointing in direction (dy, dx)."""
  if dy == 0 or dx == 0:
    py, px = dx, dy  # perpendicular offset
    return [(r, c), (r - dy + py, c - dx + px), (r - dy - py, c - dx - px)]
  return [(r, c), (r - dy, c), (r, c - dx)]


def _target(shape):
  r, c, dy, dx = shape
  return (r + _STEP * dy, c + _STEP * dx)


def _inside(p, height, width):
  return 0 <= p[0] < height and 0 <= p[1] < width


def _touches(cells, taken):
  """True if any cell is equal or 8-adjacent to a cell in taken."""
  for (r, c) in cells:
    for ar in (-1, 0, 1):
      for ac in (-1, 0, 1):
        if (r + ar, c + ac) in taken:
          return True
  return False


def _fits(shape, placed, height, width, allow_hits):
  """Shape and its target are in the grid and the shape is clear of others."""
  cells = _cells(*shape)
  if not all(_inside(p, height, width) for p in cells):
    return False
  t = _target(shape)
  if not _inside(t, height, width):
    return False
  taken = set()
  for s in placed:
    taken.update(_cells(*s))
  if _touches(cells, taken):
    return False
  if not allow_hits:
    if t in taken:
      return False
    cs = set(cells)
    if any(_target(s) in cs for s in placed):
      return False
  return True


def _render(shapes, color, width, height):
  """Build the input and output grids from the latent shapes."""
  grid = common.grid(width, height, _BG)
  owner = {}
  for i, s in enumerate(shapes):
    for (r, c) in _cells(*s):
      grid[r][c] = color
      owner[(r, c)] = i
  output = [row[:] for row in grid]
  hits = {}
  for s in shapes:
    t = _target(s)
    if _inside(t, height, width):
      hits[t] = hits.get(t, 0) + 1
  for t, n in hits.items():
    if t in owner:
      for (r, c) in _cells(*shapes[owner[t]]):
        output[r][c] = _HIT
    else:
      output[t[0]][t[1]] = _DUP if n > 1 else _HIT
  return grid, output


def _band(n, width, height, allow_hits):
  """An evenly spaced row or column of same-direction shapes."""
  d = random.choice(_DIRS)
  k = random.randint(2, min(4, n))
  gap = random.randint(3, 5)
  horizontal = random.random() < 0.5
  r0, c0 = random.randrange(height), random.randrange(width)
  band = []
  for i in range(k):
    shape = (r0 + (0 if horizontal else i * gap),
             c0 + (i * gap if horizontal else 0), d[0], d[1])
    if not _fits(shape, band, height, width, allow_hits):
      return []
    band.append(shape)
  return band


def _sample_shapes(n, width, height, allow_hits):
  """Place exactly n shapes. Some collide or hit. Returns None on failure."""
  for _ in range(200):
    placed = []
    if n >= 2 and random.random() < 0.4:
      for _ in range(30):
        placed = _band(n, width, height, allow_hits)
        if placed:
          break
    ok = True
    while len(placed) < n:
      done = False
      for _ in range(300):
        d = random.choice(_DIRS)
        roll = random.random()
        t = None
        if placed and roll < 0.25:
          t = _target(random.choice(placed))  # collision
        elif placed and allow_hits and roll < 0.45:
          t = random.choice(_cells(*random.choice(placed)))  # hit
        if t is None:
          shape = (random.randrange(height), random.randrange(width),
                   d[0], d[1])
        else:
          shape = (t[0] - _STEP * d[0], t[1] - _STEP * d[1], d[0], d[1])
        if _fits(shape, placed, height, width, allow_hits):
          placed.append(shape)
          done = True
          break
      if not done:
        ok = False
        break
    if ok:
      return placed
  return None


def _check_explicit(shapes, width, height):
  for s in shapes:
    if len(s) != 4 or (s[2], s[3]) not in _DIRS:
      raise ValueError("bad shape %r" % (s,))
    if not all(_inside(p, height, width) for p in _cells(*s)):
      raise ValueError("shape %r outside grid" % (s,))
  for i in range(len(shapes)):
    for j in range(i):
      if _touches(_cells(*shapes[i]), set(_cells(*shapes[j]))):
        raise ValueError("shapes %r and %r touch" % (shapes[i], shapes[j]))


def generate(shapes=None, color=None, width=None, height=None,
             num_shapes=None):
  """Generate one input/output pair.

  Args:
    shapes: optional list of (row, col, dy, dx) tuples. (row, col) is the
      tip cell (chevron apex or L corner). (dy, dx) is the pointing
      direction, a nonzero vector with components in {-1, 0, 1}. Shapes
      must lie in the grid and must not touch. Targets off the grid are
      skipped, as the rule specifies.
    color: optional shape colour (0-9, not 7 or 1).
    width: optional grid width. It defaults to 16 with explicit shapes and
      is sampled otherwise. It must be at least 7 for random scenes.
    height: optional grid height (same conventions as width).
    num_shapes: optional exact number of shapes for a random scene. With
      explicit shapes it must equal len(shapes).
  """
  if color is not None and (color in (_BG, _DUP) or not 0 <= color <= 9):
    raise ValueError("color must be 0-9 and not 7 or 1")
  for side in (width, height):
    if side is not None and not 1 <= side <= 30:
      raise ValueError("grid sides must be in 1..30")
  if shapes is not None:
    shapes = [tuple(s) for s in shapes]
    if num_shapes is not None and num_shapes != len(shapes):
      raise ValueError("num_shapes disagrees with shapes")
    width = 16 if width is None else width
    height = 16 if height is None else height
    _check_explicit(shapes, width, height)
    color = random.choice(_PALETTE) if color is None else color
    grid, output = _render(shapes, color, width, height)
    return {"input": grid, "output": output}

  if width is None and height is None and random.random() < 0.4:
    width, height = 16, 16
  width = random.randint(10, 30) if width is None else width
  height = random.randint(10, 30) if height is None else height
  if width < _MIN_SIDE or height < _MIN_SIDE:
    raise ValueError("random scenes need sides of at least 7")
  if num_shapes is not None and (not isinstance(num_shapes, int) or
                                not 1 <= num_shapes <= width * height // 3):
    raise ValueError("num_shapes must be positive and fit the cell count")
  for _ in range(50):
    col = random.choice(_PALETTE) if color is None else color
    if num_shapes is None:
      n_max = min(9, max(3, (width * height) // 25))
      n = random.randint(min(4, n_max), n_max)
    else:
      n = num_shapes
    placed = _sample_shapes(n, width, height, allow_hits=(col != _HIT))
    if placed is None:
      raise ValueError("could not place the requested shapes on this grid")
    grid, output = _render(placed, col, width, height)
    if grid != output:
      return {"input": grid, "output": output}
  raise ValueError("could not place the requested shapes on this grid")


def validate():
  """Reconstruct the canonical pairs from explicit latent parameters."""
  up, down, left = (-1, 0), (1, 0), (0, -1)
  train = [
      generate(shapes=[(4, 12, 1, -1), (14, 1) + up, (14, 7) + up,
                       (14, 14) + up], color=9),
      generate(shapes=[(10, 1) + up, (11, 8) + up, (12, 4) + up,
                       (13, 11) + up, (14, 1) + up, (14, 7) + up], color=0),
      generate(shapes=[(6, 5, -1, -1), (6, 8, -1, -1), (6, 11, -1, -1),
                       (6, 14, -1, -1), (11, 13, -1, -1), (14, 5, -1, -1),
                       (14, 8, -1, -1), (14, 11, -1, -1), (14, 14, -1, -1)],
               color=2),
  ]
  test = [
      generate(shapes=[(3, 2, 1, 1), (3, 9) + down, (4, 13) + left,
                       (5, 9) + up, (7, 2) + up, (13, 4) + up,
                       (14, 9, -1, 1), (14, 14) + up], color=6),
  ]
  return {"train": train, "test": test}
