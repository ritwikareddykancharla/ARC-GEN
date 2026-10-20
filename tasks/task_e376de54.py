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

"""Generator for ARC task e376de54: equalise parallel segments to the middle one.

Rule: the input holds an odd number of parallel straight segments on a
background of 7. They can be horizontal, vertical, or diagonal. One end of every
segment lies on a common anchor line that runs across the segments. Order the
segments across their direction and take the middle one. Its length is the
target. Every segment keeps its anchored end and is shortened or extended to the
target length. Cells that are removed become background.

Scope: native square grids of side 10..30 with a sampled background. Original
fixtures retain their 16x16 canvas and background 7. A scene has 3 or 5
segments and uses one of four orientations: horizontal, vertical, anti-diagonal
(down-left) or main diagonal (down-right). Either end can be the anchor. Spacing
across the segments is irregular, but neighbouring anchors are at least 2 apart,
so lines never touch, even diagonally. Colours come in contiguous groups of 1 to
3 colours. Randomly sampled segments stay inside the grid at both their original
length and the target length.
"""

import random

import common

ORIENTATIONS = ("horizontal", "vertical", "antidiagonal", "diagonal")


def _step(orientation, sign):
  """Unit step from the anchor cell along the segment."""
  if orientation == "horizontal":
    return (0, sign)
  if orientation == "vertical":
    return (sign, 0)
  if orientation == "antidiagonal":
    return (sign, -sign)
  return (sign, sign)


def _anchor_cell(orientation, anchor, offset):
  """Anchor cell of the segment at a perpendicular offset.

  horizontal: anchor is the shared column and offset is the row.
  vertical: anchor is the shared row and offset is the column.
  antidiagonal: anchor is c = y - x and offset is the row.
  diagonal: anchor is c = y + x and offset is the row.
  """
  if orientation == "horizontal":
    return (offset, anchor)
  if orientation == "vertical":
    return (anchor, offset)
  if orientation == "antidiagonal":
    return (offset, offset - anchor)
  return (offset, anchor - offset)


def _room(cell, step, size):
  y, x = cell
  n = 0
  while 0 <= y < size and 0 <= x < size:
    n += 1
    y += step[0]
    x += step[1]
  return n


def _draw(grid, cell, step, length, color):
  y, x = cell
  for _ in range(length):
    if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
      grid[y][x] = color
    y += step[0]
    x += step[1]


def _colors(k, background):
  groups = random.randint(1, min(3, k))
  palette = random.sample([c for c in range(10) if c != background], groups)
  cuts = sorted(random.sample(range(1, k), groups - 1))
  bounds = [0] + cuts + [k]
  colors = []
  for i in range(groups):
    colors += [palette[i]] * (bounds[i + 1] - bounds[i])
  return colors


def _sample(size, background):
  orientation = random.choice(ORIENTATIONS)
  sign = random.choice((1, -1))
  k = random.choice((3, 5))
  if orientation in ("horizontal", "vertical"):
    if sign == 1:
      anchor = random.randint(0, size - 5)
    else:
      anchor = random.randint(4, size - 1)
  elif orientation == "antidiagonal":
    anchor = random.randint(-(size - 6), size - 6)
  else:
    anchor = random.randint(5, 2 * size - 7)
  step = _step(orientation, sign)
  cands = []
  for o in range(size):
    y, x = _anchor_cell(orientation, anchor, o)
    if 0 <= y < size and 0 <= x < size and _room((y, x), step, size) >= 4:
      cands.append(o)
  if len(cands) < 2 * k - 1:
    return None
  offsets = None
  for _ in range(100):
    pick = sorted(random.sample(cands, k))
    if all(b - a >= 2 for a, b in zip(pick, pick[1:])):
      offsets = pick
      break
  if offsets is None:
    return None
  rooms = [_room(_anchor_cell(orientation, anchor, o), step, size)
           for o in offsets]
  target = random.randint(2, min(rooms))
  lengths = [random.randint(2, r) for r in rooms]
  lengths[k // 2] = target
  if all(n == target for n in lengths):
    return None
  return orientation, sign, anchor, offsets, lengths, _colors(k, background)


def generate(orientation=None, sign=None, anchor=None, offsets=None,
             lengths=None, colors=None, size=None, background=None):
  """Build one input/output pair.

  Args:
    orientation: one of "horizontal", "vertical", "antidiagonal" (cells along
      y + x = const) or "diagonal" (cells along y - x = const).
    sign: +1 or -1, which picks the step from the anchor along the segment.
      horizontal (0, s); vertical (s, 0); antidiagonal (s, -s); diagonal (s, s).
    anchor: shared coordinate of the anchor line (see _anchor_cell).
    offsets: perpendicular positions of the segments (rows or columns).
    lengths: input length of each segment, aligned with offsets.
    colors: colour of each segment, aligned with offsets.
    size: grid side (sampled from 10..30; explicit fixtures default to 16).
    background: sampled background colour; explicit fixtures default to 7.
  """
  if size is None:
    size = random.randint(10, 30) if orientation is None else 16
  if background is None:
    background = random.randrange(10) if orientation is None else 7
  if not 10 <= size <= 30 or background not in range(10):
    raise ValueError("size must be 10..30 and background an ARC colour")
  if orientation is None:
    if any(v is not None for v in (sign, anchor, offsets, lengths, colors)):
      raise ValueError("explicit segment parameters require an orientation")
    scene = None
    for _ in range(500):
      scene = _sample(size, background)
      if scene is not None:
        break
    if scene is None:
      raise RuntimeError("could not sample non-touching segments in requested grid")
    orientation, sign, anchor, offsets, lengths, colors = scene
  order = sorted(range(len(offsets)), key=lambda i: offsets[i])
  offsets = [offsets[i] for i in order]
  lengths = [lengths[i] for i in order]
  colors = [colors[i] for i in order]
  step = _step(orientation, sign)
  target = lengths[len(offsets) // 2]
  inp = common.grid(size, size, background)
  out = common.grid(size, size, background)
  for o, n, c in zip(offsets, lengths, colors):
    cell = _anchor_cell(orientation, anchor, o)
    _draw(inp, cell, step, n, c)
    _draw(out, cell, step, target, c)
  return {"input": inp, "output": out}


def validate():
  """Rebuild the canonical fixtures from explicit latent parameters."""
  train = [
      generate("antidiagonal", -1, 7, [7, 9, 11, 13, 15], [3, 2, 6, 9, 4],
               [2, 2, 9, 1, 1]),
      generate("horizontal", 1, 3, [2, 6, 8], [2, 7, 12], [5, 9, 3]),
      generate("vertical", 1, 2, [2, 5, 7, 9, 13], [2, 4, 4, 3, 6],
               [8, 8, 8, 8, 8]),
  ]
  test = [
      generate("antidiagonal", 1, -3, [2, 4, 6, 9, 11], [4, 3, 4, 5, 5],
               [8, 8, 6, 6, 6]),
  ]
  return {"train": train, "test": test}
