# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generator."""

import common


def generate(colors=None, flip=None, xpose=None, height=None, width=None,
             size=None, brow=None, bcol=None):
  """Returns input and output grids according to the given parameters.

  Geometry is given before the optional flip and transpose. With explicit
  colors, unspecified geometry keeps the original 10x10 layout (square of side
  6 at row 2, column 2). Without colors, every unspecified parameter is
  sampled consistently with the specified ones.

  Args:
    colors: The colors of the pixels.
    flip: Whether to flip the grid.
    xpose: Whether to transpose the grid.
    height: The height of the canvas (before any transpose).
    width: The width of the canvas (before any transpose).
    size: The side of the grey square; always even (>= 4) so the interior
      splits into four equal quadrants.
    brow: The top row of the square.
    bcol: The left column of the square.
  """

  if colors is None:
    colors = common.random_colors(2, exclude=[5])
    if flip is None: flip = common.randint(0, 1)
    if xpose is None: xpose = common.randint(0, 1)
    # The two markers sit diagonally outside the two top corners, so the
    # canvas needs one free row above and one free column on each side.
    if height is None: height = common.randint(5 if size is None else size + 1, 30)
    if width is None: width = common.randint(6 if size is None else size + 2, 30)
    if size is None:
      if min(height - 1, width - 2) < 4:
        raise ValueError("Canvas too small for a square with markers")
      size = 2 * common.randint(2, min(height - 1, width - 2) // 2)
    if brow is None and height - size >= 1: brow = common.randint(1, height - size)
    if bcol is None and width - size - 1 >= 1: bcol = common.randint(1, width - size - 1)
  else:
    height = 10 if height is None else height
    width = 10 if width is None else width
    size = 6 if size is None else size
    brow = 2 if brow is None else brow
    bcol = 2 if bcol is None else bcol
  if (size < 4 or size % 2 or brow is None or bcol is None or brow < 1
      or bcol < 1 or brow + size > height or bcol + size + 1 > width
      or max(height, width) > 30):
    raise ValueError("Infeasible square geometry")

  half = size // 2
  bot, right = brow + size - 1, bcol + size - 1
  grid, output = common.grids(width, height)
  for i in range(size):
    for r, c in [(brow, bcol + i), (bot, bcol + i), (brow + i, bcol),
                 (brow + i, right)]:
      output[r][c] = grid[r][c] = 5
  output[brow - 1][bcol - 1] = grid[brow - 1][bcol - 1] = colors[0]
  output[brow - 1][right + 1] = grid[brow - 1][right + 1] = colors[1]
  for r in range(brow + 1, bot):
    for c in range(bcol + 1, right):
      top, left = r < brow + half, c < bcol + half
      output[r][c] = colors[0] if top == left else colors[1]
  if flip:
    grid, output = common.flip(grid), common.flip(output)
  if xpose:
    grid, output = common.transpose(grid), common.transpose(output)
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[6, 7], flip=True, xpose=True),
      generate(colors=[4, 8], flip=False, xpose=False),
      generate(colors=[3, 2], flip=False, xpose=True),
  ]
  test = [
      generate(colors=[9, 1], flip=True, xpose=False),
  ]
  return {"train": train, "test": test}
