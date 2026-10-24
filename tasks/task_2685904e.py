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


def generate(length=None, colors=None, height=None, divider=None, data_row=None):
  """Returns input and output grids according to the given parameters.

  Args:
    length: The length to match.
    colors: The colors of the full-width data row (its length is the width).
    height: Canvas height (10 for the original pairs); random 6..30.
    divider: Row of the grey divider (6 for the original pairs).
    data_row: Row of the data (8 for the original pairs).
  """

  def draw():
    width = len(colors)
    grid, output = common.grids(width, height)
    for c in range(length):
      output[0][c] = grid[0][c] = 8
    matches = False
    for c, color in enumerate(colors):
      output[data_row][c] = grid[data_row][c] = color
      output[divider][c] = grid[divider][c] = 5
      if colors.count(color) != length: continue
      matches = True
      for r in range(length):
        output[divider - 1 - r][c] = color
    if not matches: return None, None
    return grid, output

  if length is None:
    fixed_height = height
    if fixed_height is not None and not 6 <= fixed_height <= 30:
      raise ValueError('Random height must be 6..30')
    for _ in range(100):
      width = common.randint(4, 30)
      height = common.randint(6, 30) if fixed_height is None else fixed_height
      # Layout of the original pairs: counter bar from the top-left corner,
      # bars rising from the divider without reaching row 0, and a full-width
      # data row below the divider with at least one blank row in between.
      divider = common.randint(2, height - 3)
      data_row = common.randint(divider + 2, height - 1)
      # A counter as long as the row would itself look like a divider line.
      length = common.randint(1, min(divider - 1, width - 1))
      subset = common.sample([1, 2, 3, 4, 6, 7, 8, 9], common.randint(2, 8))
      for _ in range(20):
        colors = common.choices(subset, width)
        grid, _ = draw()
        if grid: break
      if grid: break
    else:
      raise RuntimeError('No data colour occurs exactly length times; retry')
  height = 10 if height is None else height
  divider = 6 if divider is None else divider
  data_row = 8 if data_row is None else data_row

  grid, output = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(length=2, colors=[2, 3, 3, 2, 3, 1, 1, 3, 1, 1]),
      generate(length=1, colors=[6, 6, 4, 6, 2, 1, 9, 2, 9, 4]),
      generate(length=3, colors=[4, 1, 4, 4, 6, 3, 1, 6, 3, 6]),
      generate(length=4, colors=[2, 1, 2, 1, 2, 1, 1, 2, 2, 2]),
      generate(length=3, colors=[8, 6, 4, 3, 4, 7, 3, 8, 3, 7]),
      generate(length=1, colors=[1, 3, 1, 1, 1, 1, 4, 1, 1, 1]),
  ]
  test = [
      generate(length=2, colors=[2, 3, 6, 4, 6, 2, 4, 4, 3, 9]),
  ]
  return {"train": train, "test": test}
