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


def generate(prows=None, pcols=None, colors=None, size=None, width=None,
             height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    prows: The rows of the pixels.
    pcols: The columns of the pixels.
    colors: The colors of the pixels.
    size: The size of a square grid (15 for the original pairs).
    width: Canvas width; random scenes sample it independently in 9..30.
    height: Canvas height; random scenes sample it independently in 7..30.
  """

  if size is not None:
    if width is not None or height is not None:
      raise ValueError('Specify size or width/height, not both')
    width = height = size
  if prows is None:
    width = common.randint(9, 30) if width is None else width
    height = common.randint(7, 30) if height is None else height
    if not (9 <= width <= 30 and 7 <= height <= 30):
      raise ValueError('Random dimensions must be 9..30 wide, 7..30 tall')
    # Seeds sit in rows 1..height-2, pairwise at least two rows apart, and in
    # distinct columns at least three cells from the side edges.
    num = common.randint(3, min(6, (height - 1) // 2, width - 6))
    colors = common.random_colors(num)
    # Sorted rows with gaps of at least two are, after subtracting the rank,
    # exactly the sorted num-subsets of 1..height-1-num (uniform, no retries).
    base = sorted(common.sample(range(1, height - num), num))
    prows = [r + i for i, r in enumerate(base)]
    pcols = common.sample(range(3, width - 3), num)
  width = 15 if width is None else width
  height = 15 if height is None else height

  grid, output = common.grids(width, height)
  for i, (prow, pcol, color) in enumerate(zip(prows, pcols, colors)):
    grid[prow][pcol] = color
    for c in range(width):
      output[prow][c] = color
    lb_row = 0 if i == 0 else (prow - (prow - prows[i - 1] - 1) // 2)
    ub_row = height if i + 1 == len(prows) else (prow + (prows[i + 1] - prow + 2) // 2)
    for row in range(lb_row, ub_row):
      output[row][0] = output[row][width - 1] = color
  for c in range(width):
    output[0][c] = colors[0]
    output[height - 1][c] = colors[-1]
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(prows=[3, 7, 12], pcols=[6, 8, 3], colors=[2, 7, 8]),
      generate(prows=[1, 3, 7, 9], pcols=[6, 10, 3, 5], colors=[8, 1, 2, 3]),
      generate(prows=[2, 7, 9], pcols=[3, 7, 4], colors=[3, 2, 9]),
      generate(prows=[2, 4, 11], pcols=[10, 4, 7], colors=[6, 2, 8]),
  ]
  test = [
      generate(prows=[2, 4, 9, 12], pcols=[3, 6, 11, 9], colors=[8, 2, 1, 3]),
  ]
  return {"train": train, "test": test}
