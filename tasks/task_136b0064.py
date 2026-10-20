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

"""ARC task 136b0064: glyph program drawn as a staircase path.

Rule: the left glyph panel is 7 columns wide. A yellow (4) divider sits in
column 7. Left of it is a stack of 3x3 glyphs in two columns (x 0-2 and
x 4-6), one glyph every 4 rows. Right of it is an empty output panel with a
single grey (5) start marker in row 0. The output is that right panel with a
path drawn from the marker. The glyphs are read as a program: left column top
to bottom, then right column top to bottom. Each glyph adds one segment of
its own colour:
  1 (caret): step down one row, then 3 cells to the right
  2 (cup):   step down one row, then 2 cells to the left
  3 (Y):     step down one row, then 4 cells to the left
  6 (T):     2 cells straight down
A horizontal segment starts in the current column, and the current column
becomes its last cell. A vertical segment hangs below the current cell.

Scope: output width 7..22, the number of glyph rows (2-7, so the height is 4*rows-1, from 7 to
27), the marker column and the glyph sequence are all sampled. Both glyph
columns are always full, as in every original example. The sequence is built
step by step so that the path stays inside the output columns and the
output height.
"""

import random

import common


GLYPHS = {
    1: [[1, 1, 0], [1, 0, 1], [0, 1, 0]],
    2: [[2, 0, 2], [2, 0, 2], [2, 2, 2]],
    3: [[3, 3, 3], [0, 3, 0], [3, 0, 3]],
    6: [[6, 0, 6], [0, 6, 0], [0, 6, 0]],
}

# colour -> (dx per cell, length); dx == 0 means straight down.
MOVES = {1: (1, 3), 2: (-1, 2), 3: (-1, 4), 6: (0, 2)}


def _sample_sequence(rows, start, canvas_width):
  """Builds 2*rows glyph colours whose path stays in bounds."""
  height = 4 * rows - 1
  total = 2 * rows
  # Rows consumed = total + number_of_6s, and this must be <= height - 1.
  down_budget = height - 1 - total
  seq, x, downs = [], start, 0
  for _ in range(total):
    options = []
    if x + 2 < canvas_width:
      options.append(1)
    if x - 1 >= 0:
      options.append(2)
    if x - 3 >= 0:
      options.append(3)
    if downs < down_budget:
      options.append(6)
    colour = random.choice(options)
    dx, length = MOVES[colour]
    if dx == 0:
      downs += 1
    else:
      x += dx * (length - 1)
    seq.append(colour)
  return seq


def generate(left=None, right=None, start=None, rows=None, canvas_width=None):
  """Returns an input/output pair.

  Args:
    left: glyph colours (from 1, 2, 3, 6) in the left column, top to bottom.
    right: glyph colours in the right column, top to bottom. It must have the
      same length as left.
    start: marker column inside the output panel.
    rows: the number of glyph rows, 2..7.
    canvas_width: output width, 7..22; sampled for random scenes, 7 for explicit programs.
  """
  if (left is None) != (right is None):
    raise ValueError("both glyph columns must be supplied together")
  if canvas_width is None:
    canvas_width = random.randint(7, 22) if left is None else 7
  if not 7 <= canvas_width <= 22:
    raise ValueError("canvas_width must be 7..22")
  if start is not None and not 0 <= start < canvas_width:
    raise ValueError("start outside canvas")
  if left is None:
    if rows is None:
      rows = random.randint(2, 7)
    if start is None:
      start = random.randrange(canvas_width)
    if not 2 <= rows <= 7:
      raise ValueError("rows must be 2..7")
    seq = _sample_sequence(rows, start, canvas_width)
    left, right = seq[:rows], seq[rows:]
  else:
    if len(left) != len(right) or (rows is not None and rows != len(left)):
      raise ValueError("glyph columns and rows must agree")
    rows = len(left)
    if start is None:
      start = random.randrange(canvas_width)
  height = 4 * rows - 1
  grid = common.grid(8 + canvas_width, height, 0)
  for r in range(height):
    grid[r][7] = 4
  grid[0][8 + start] = 5
  for col_x, column in ((0, left), (4, right)):
    for i, colour in enumerate(column):
      shape = GLYPHS[colour]
      for dr in range(3):
        for dc in range(3):
          if shape[dr][dc]:
            grid[4 * i + dr][col_x + dc] = shape[dr][dc]
  output = common.grid(canvas_width, height, 0)
  output[0][start] = 5
  y, x = 0, start
  for colour in list(left) + list(right):
    dx, length = MOVES[colour]
    if dx == 0:
      for k in range(1, length + 1):
        if 0 <= y + k < height:
          output[y + k][x] = colour
      y += length
    else:
      y += 1
      for k in range(length):
        if 0 <= y < height and 0 <= x + k * dx < canvas_width:
          output[y][x + k * dx] = colour
      x += dx * (length - 1)
  return {"input": grid, "output": output}


def validate():
  """Rebuilds the original task fixtures from their latent parameters."""
  train = [
      generate(left=[2, 1, 1, 6], right=[6, 3, 6, 1], start=1),
      generate(left=[1, 6], right=[2, 3], start=3),
      generate(left=[2, 6, 2], right=[6, 1, 6], start=4),
  ]
  test = [
      generate(left=[1, 2, 6, 3, 6], right=[1, 1, 6, 3, 2], start=2),
  ]
  return {"train": train, "test": test}
