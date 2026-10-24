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


def generate(colors=None, widths=None, heights=None, width=None, height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: A list of colors to use.
    widths: A list of widths to use (their sum is the grid width).
    heights: A list of heights to use (their sum is the grid height).
    width: Optional width (3..30) for a random scene; random otherwise.
    height: Optional height (3..30) for a random scene; random otherwise.
  """

  def partition(total, parts):
    # Every run is at least one cell; the last run, which contains the
    # shared corner, is at least two so its block stays visible.
    cuts = sorted(common.sample(range(1, total - 1), parts - 1))
    runs = [b - a for a, b in zip([0] + cuts, cuts + [total])]
    return runs

  if colors is None:
    if width is None and height is None:
      num_colors = common.randint(2, 9)
      width = common.randint(num_colors + 1, 30)
      height = common.randint(num_colors + 1, 30)
    else:
      # Requested shape (e.g. for shape-matched demonstrations): same domain,
      # with the colour count drawn from what that shape can hold.
      width = common.randint(3, 30) if width is None else width
      height = common.randint(3, 30) if height is None else height
      if not (3 <= width <= 30 and 3 <= height <= 30):
        raise ValueError("Random dimensions must be 3..30")
      num_colors = common.randint(2, min(9, width - 1, height - 1))
    colors = common.random_colors(num_colors)
    widths = partition(width, num_colors)
    heights = partition(height, num_colors)

  width, height = sum(widths), sum(heights)
  grid, output = common.grids(width, height)
  row, col = 0, 0
  for color, wide, tall in zip(colors, widths, heights):
    common.rect(output, wide, tall, row, col, color)
    for _ in range(wide):
      output[height - 1][col] = grid[height - 1][col] = color
      col += 1
    for _ in range(tall):
      output[row][width - 1] = grid[row][width - 1] = color
      row += 1
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[5, 6, 7, 8, 9], widths=[1, 2, 3, 1, 3], heights=[1, 2, 3, 1, 3]),
      generate(colors=[9, 8, 7, 6, 5], widths=[2, 2, 2, 2, 2], heights=[2, 2, 2, 2, 2]),
      generate(colors=[8, 4, 5, 3], widths=[2, 3, 2, 3], heights=[3, 2, 2, 3]),
  ]
  test = [
      generate(colors=[3, 4, 6, 9, 7], widths=[2, 1, 3, 2, 2], heights=[3, 2, 2, 1, 2]),
  ]
  return {"train": train, "test": test}
