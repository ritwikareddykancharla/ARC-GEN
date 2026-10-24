# Copyright 2025 Google LLC
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


def generate(rows=None, cols=None, color=None, size=None, height=None, width=None):
  """Returns input and output grids according to the given parameters.

  Args:
    rows: a list of vertical coordinates where pixels should be placed
    cols: a list of horizontal coordinates where pixels should be placed
    color: a digit representing a color to be used
    size: optional square size; height and width also allow rectangles (2..5).
      Random inputs vary both dimensions; explicit fixture coordinates default to 3x3.
  """
  if size is not None and (height is not None or width is not None):
    raise ValueError('Use size or height/width, not both')
  if size is not None:
    height = width = size
  height = height if height is not None else (common.randint(2, 5) if rows is None else 3)
  width = width if width is not None else (common.randint(2, 5) if rows is None else 3)
  if not (2 <= height <= 5 and 2 <= width <= 5):
    raise ValueError('Input dimensions must be 2..5 so the squared output fits ARC')
  if rows is None:
    pixels = common.sample(common.all_pixels(width, height), common.randint(2, height * width - 1))
    rows, cols = zip(*pixels)
    color = common.random_color()

  grid, output = common.grid(width, height), common.grid(width * width, height * height)
  for r, c in zip(rows, cols):
    grid[r][c] = color
    for rr, cc in zip(rows, cols):
      output[rr * height + r][cc * width + c] = color
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(rows=[0, 0, 1, 1, 1, 2, 2], cols=[1, 2, 0, 1, 2, 1, 2], color=7),
      generate(rows=[0, 0, 2], cols=[0, 2, 1], color=4),
      generate(rows=[1, 2, 2], cols=[2, 0, 2], color=2),
      generate(rows=[0, 0, 1, 2, 2], cols=[0, 1, 0, 1, 2], color=6),
      generate(rows=[0, 0, 0, 2, 2], cols=[0, 1, 2, 1, 2], color=2),
  ]
  test = [
      generate(rows=[0, 0, 1, 1, 2, 2], cols=[0, 2, 0, 2, 0, 1], color=7),
  ]
  return {"train": train, "test": test}
