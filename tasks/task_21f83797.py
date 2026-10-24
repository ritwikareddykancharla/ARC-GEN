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


def generate(width=None, height=None, brow=None, bcol=None, grid_width=None,
             grid_height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: The width of the box.
    height: The height of the box.
    brow: The row of the box.
    bcol: The column of the box.
    grid_width: Canvas width; random scenes sample it independently in 5..30.
    grid_height: Canvas height; random scenes sample it independently in 5..30.
  """

  if width is None:
    grid_width = common.randint(5, 30) if grid_width is None else grid_width
    grid_height = common.randint(5, 30) if grid_height is None else grid_height
    if not (5 <= grid_width <= 30 and 5 <= grid_height <= 30):
      raise ValueError('Random dimensions must be 5..30')
    # The box keeps a blank margin of at least one cell on every side, as in
    # the original 13x13 scenes (box sides 3..11, corners in rows/cols 1..11).
    width = common.randint(3, grid_width - 2)
    height = common.randint(3, grid_height - 2)
    brow = common.randint(1, grid_height - 1 - height)
    bcol = common.randint(1, grid_width - 1 - width)
  grid_width = 13 if grid_width is None else grid_width
  grid_height = 13 if grid_height is None else grid_height

  grid, output = common.grids(grid_width, grid_height)
  grid[brow][bcol] = grid[brow + height - 1][bcol + width - 1] = 2
  for r in range(height):
    for c in range(width):
      output[brow + r][bcol + c] = 1
  for i in range(grid_width):
    output[brow][i] = output[brow + height - 1][i] = 2
  for i in range(grid_height):
    output[i][bcol] = output[i][bcol + width - 1] = 2
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(width=9, height=5, brow=4, bcol=2),
      generate(width=6, height=7, brow=3, bcol=3),
  ]
  test = [
      generate(width=6, height=10, brow=1, bcol=4),
  ]
  return {"train": train, "test": test}
