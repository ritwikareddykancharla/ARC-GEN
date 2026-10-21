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

"""Concentric square rings; clipped rings have gray legend swatches."""

import common


def generate(colors=None, row=None, col=None, last=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: A list of colors to use.
    row: The row of the pixel.
    col: The column of the pixel.
    last: Deprecated compatibility argument; the visible clipping rule sets swatches.
  """

  if colors is None:
    num_colors = common.randint(4, 6)
    colors = [common.randint(0, 9) for _ in range(num_colors)]
    if colors[0] == 0: colors[0] = common.random_color()
    if colors[-1] == 0: colors[-1] = common.random_color()
    row = common.randint(2 + num_colors, 17 - num_colors)
    col = common.randint(num_colors - 2, 17 - num_colors)

  grid, output = common.grids(16, 16)
  for i, color in enumerate(colors):
    output[0][i] = grid[0][i] = color
  for c in range(16):
    output[1][c] = grid[1][c] = 5
  output[row][col] = grid[row][col] = colors[0]
  for i, color in enumerate(colors):
    common.hollow_rect(output, 2 * i + 1, 2 * i + 1, row - i, col - i, color)
  # Gray the swatch of every ring clipped by the drawing canvas.
  for i in range(len(colors)):
    if row - i < 2 or row + i >= 16 or col - i < 0 or col + i >= 16:
      output[0][i] = 5
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[2, 3, 3, 4, 0, 8], row=11, col=5, last=5),
      generate(colors=[1, 2, 3, 6], row=9, col=6),
  ]
  test = [
      generate(colors=[3, 2, 0, 8, 1], row=10, col=10),
  ]
  return {"train": train, "test": test}
