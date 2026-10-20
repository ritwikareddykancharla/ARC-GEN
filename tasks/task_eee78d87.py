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

"""ARC-GEN style generator for task eee78d87.

Rule: the input has background 7 and holds one 3x3 symbol in a single colour.
The symbol is symmetric both horizontally and vertically, so four cells
describe it completely: the corner (0,0), the top-middle (0,1), the
middle-left (1,0) and the centre (1,1). The output is always a 16x16
lattice. Row and column indices that are 0 mod 3 are "lines" (L). All other
indices are "blocks" (B). Each cell kind takes colour 0 if its controlling
symbol cell is filled and colour 7 if that cell is empty:
  LL <- centre, LB <- middle-left, BL <- top-middle, BB <- corner.
Every 0 inside rows 5..10 and columns 5..10 is then recoloured to 9.

Scope: the generator samples any doubly-symmetric symbol whose bounding box
is the full 3x3 square. There are 10 such symbols. The corner bit is drawn
first with equal odds, so the corner-empty family (BB = 7) is not swamped.
It also samples the symbol position, a symbol colour other than 0, 7 and 9,
and the input size. All fixtures are 6x6, and 6x6 remains the most common
size. Random sides from 5 to 10 are a synthetic extension, and so are
explicit sides up to 30. The rule reads only the symbol's bounding box, so
the input size never changes the output.

In every fixture, top-middle filled coincides with corner empty. The
symbols with both corner and top filled are therefore a cell-wise
extrapolation. The verified explanation and transform support it, but no
fixture attests it. Pass attested_only=True to restrict sampling to the
fixture-attested family (top != corner).

The 16x16 output size, the background 7, the 0/7 palette and the 9 overlay
are fixed by the task.
"""

import random

import common


SYMBOL_COLOURS = [1, 2, 3, 4, 5, 6, 8]


def _symbol(corner, top, left, center):
  """Builds the 3x3 boolean mask of a doubly-symmetric symbol."""
  return [[corner, top, corner],
          [left, center, left],
          [corner, top, corner]]


def _valid(corner, top, left, center):
  """Checks that the symbol's bounding box is exactly 3x3."""
  del center
  return (corner or top) and (corner or left)


def _is_int(value):
  """True for genuine integers (bools and floats are excluded)."""
  return isinstance(value, int) and not isinstance(value, bool)


def _check_int(name, value):
  """Rejects a non-None control that is not a plain int."""
  if value is not None and not _is_int(value):
    raise ValueError("%s must be an int or None" % name)


def _sample_side(pos):
  """Samples one input side that can hold a symbol starting at pos."""
  lo = 5 if pos is None else max(5, pos + 3)
  return random.randint(lo, max(10, lo))


def generate(corner=None, top=None, left=None, center=None, colour=None,
             row=None, col=None, width=None, height=None,
             attested_only=None):
  """Generates one input/output pair.

  Args:
    corner: whether the symbol's four corner cells are filled (controls BB).
    top: whether the top and bottom middle cells are filled (controls BL).
    left: whether the left and right middle cells are filled (controls LB).
    center: whether the centre cell is filled (controls LL).
    colour: colour of the symbol (int, one of 1-6 or 8).
    row: top row of the symbol's 3x3 box (int, 0..height-3, at most 27).
    col: left column of the symbol's 3x3 box (int, 0..width-3, at most 27).
    width: input width (int, 5..30). Random sampling uses 5..10, or more
      when col requires it. Fixtures use 6.
    height: input height (int, 5..30). Random sampling uses 5..10, or more
      when row requires it. Fixtures use 6.
    attested_only: if True, only symbols with top != corner are allowed.
      This is the family seen in the fixtures. None or False allows all 10
      full-box symbols.

  Shape flags must be None, True or False. Any flag left as None is sampled
  so that it agrees with the flags that were given. A ValueError is raised
  if no choice gives a full 3x3 bounding box, if a control has the wrong
  type, or if the explicit arguments are inconsistent.
  """
  given = (corner, top, left, center)
  for name, flag in zip(("corner", "top", "left", "center"), given):
    if flag is not None and flag is not True and flag is not False:
      raise ValueError("%s must be True, False or None" % name)
  if attested_only is not None and attested_only is not True and (
      attested_only is not False):
    raise ValueError("attested_only must be True, False or None")
  for name, value in (("colour", colour), ("row", row), ("col", col),
                      ("width", width), ("height", height)):
    _check_int(name, value)

  options = []
  for c in (False, True):
    for t in (False, True):
      for l in (False, True):
        for m in (False, True):
          combo = (c, t, l, m)
          if not _valid(*combo):
            continue
          if attested_only and c == t:
            continue
          if all(g is None or g == v for g, v in zip(given, combo)):
            options.append(combo)
  if not options:
    raise ValueError("symbol flags are inconsistent with a full 3x3 box "
                     "(or with attested_only)")
  # Balance the corner bit first, then pick a consistent completion.
  corner_values = sorted(set(o[0] for o in options))
  chosen_corner = random.choice(corner_values)
  options = [o for o in options if o[0] == chosen_corner]
  corner, top, left, center = random.choice(options)

  if colour is None:
    colour = random.choice(SYMBOL_COLOURS)
  if colour not in SYMBOL_COLOURS:
    raise ValueError("colour must be one of %s" % SYMBOL_COLOURS)

  if row is not None and not 0 <= row <= 27:
    raise ValueError("row must be in 0..27")
  if col is not None and not 0 <= col <= 27:
    raise ValueError("col must be in 0..27")

  if width is None and height is None:
    fits_six = ((row is None or row <= 3) and (col is None or col <= 3))
    if fits_six and random.random() < 0.5:
      width, height = 6, 6
  if width is None:
    width = _sample_side(col)
  if height is None:
    height = _sample_side(row)
  if not (5 <= width <= 30 and 5 <= height <= 30):
    raise ValueError("input sides must be in 5..30")

  if row is None:
    row = random.randint(0, height - 3)
  if col is None:
    col = random.randint(0, width - 3)
  if not (row <= height - 3 and col <= width - 3):
    raise ValueError("symbol position out of bounds")

  mask = _symbol(corner, top, left, center)
  grid = common.grid(width, height, 7)
  if len(grid) != height or any(len(r) != width for r in grid):
    raise ValueError("common.grid returned unexpected dimensions")
  for r in range(3):
    for c in range(3):
      if mask[r][c]:
        grid[row + r][col + c] = colour

  # Keys are (row is a line, column is a line).
  kind = {
      (True, True): 0 if center else 7,
      (True, False): 0 if left else 7,
      (False, True): 0 if top else 7,
      (False, False): 0 if corner else 7,
  }
  output = common.grid(16, 16, 0)
  for y in range(16):
    for x in range(16):
      value = kind[(y % 3 == 0, x % 3 == 0)]
      if 5 <= y <= 10 and 5 <= x <= 10 and value == 0:
        value = 9
      output[y][x] = value
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical examples from latent parameters."""
  train = [
      generate(corner=False, top=True, left=True, center=True, colour=3,
               row=3, col=3, width=6, height=6),
      generate(corner=True, top=False, left=True, center=True, colour=1,
               row=1, col=1, width=6, height=6),
      generate(corner=True, top=False, left=False, center=True, colour=6,
               row=1, col=1, width=6, height=6),
  ]
  test = [
      generate(corner=True, top=False, left=False, center=False, colour=2,
               row=0, col=2, width=6, height=6),
  ]
  return {"train": train, "test": test}
