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


def generate(size=None, rows=None, cols=None, thicks=None, width=None, height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    size: The size of the grid.
    rows: The rows of the boxes.
    cols: The columns of the boxes.
    thicks: The thicknesses of the boxes.
    width: Rectangular canvas width; sampled independently in 7..30.
    height: Rectangular canvas height; sampled independently in 7..30.
  """

  colors = [8, 4, 3]
  if size is not None:
    if width is not None or height is not None:
      raise ValueError('Specify size or width/height, not both')
    width = height = size
  else:
    width = common.randint(7, 30) if width is None else width
    height = common.randint(7, 30) if height is None else height
  if rows is None:
    if not (7 <= width <= 30 and 7 <= height <= 30):
      raise ValueError('Random dimensions must be 7..30')
    max_thick = 2 if min(width, height) < 9 else 3
    # A 7x7 canvas still fits one 5x5 box. Zero boxes would produce a
    # background-only identity pair that teaches none of this task's rule.
    num_boxes = common.randint(1, max(1, min(width, height) // 4 - 1))
    for _ in range(1000):
      thicks = [common.randint(1, max_thick) for _ in range(num_boxes)]
      sizes = [2 * thick + 3 for thick in thicks]
      rows = [common.randint(0, height - s) for s in sizes]
      cols = [common.randint(0, width - s) for s in sizes]
      if not common.overlaps(rows, cols, sizes, sizes, 1): break
    else:
      raise RuntimeError('Cannot pack requested boxes; retry the scene')

  grid, output = common.grids(width, height)
  for row, col, thick in zip(rows, cols, thicks):
    length = 2 * thick + 3
    for r in range(length):
      for c in range(length):
        output[row + r][col + c] = colors[thick - 1]
    grid[row + thick + 1][col + thick + 1] = 2
    output[row + thick + 1][col + thick + 1] = 2
    for i in range(length):
      output[row + i][col] = grid[row + i][col] = 2
      output[row][col + i] = grid[row][col + i] = 2
      output[row + i][col + length - 1] = grid[row + i][col + length - 1] = 2
      output[row + length - 1][col + i] = grid[row + length - 1][col + i] = 2
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(size=15, rows=[0, 10], cols=[6, 1], thicks=[3, 1]),
      generate(size=9, rows=[0], cols=[0], thicks=[2]),
      generate(size=13, rows=[0, 6], cols=[1, 5], thicks=[1, 2]),
      generate(size=7, rows=[0], cols=[0], thicks=[1]),
  ]
  test = [
      generate(size=20, rows=[0, 1, 7, 12], cols=[11, 1, 13, 5],
               thicks=[1, 3, 1, 2]),
  ]
  return {"train": train, "test": test}
