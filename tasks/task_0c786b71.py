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


def _dimension(value, name):
  """Returns a validated input dimension (output is twice as large, <= 30)."""
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{name} must be an int, got {value!r}")
  if not 1 <= value <= 15:
    raise ValueError(f"{name} must be in 1..15 so the output fits 30x30, got {value}")
  return value


def generate(colors=None, width=None, height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: The colors of the input pixels, row by row (width * height values
      in 0..9).
    width: Input width, 1..15 (the output is twice as wide). None samples
      2..15, or uses the legacy 4 when colors is given.
    height: Input height, 1..15 (the output is twice as tall). None samples
      2..15, or uses the legacy 3 when colors is given.

  With explicit dimensions the colours consume the RNG exactly like the
  legacy 4x3 constructor. Explicit values are never replaced.
  """

  explicit = colors is not None
  if width is None:
    width = 4 if explicit else common.randint(2, 15)
  if height is None:
    height = 3 if explicit else common.randint(2, 15)
  width, height = _dimension(width, "width"), _dimension(height, "height")
  if colors is None:
    raw_colors = common.random_colors(3)
    colors = [raw_colors[common.randint(0, 2)] for _ in range(width * height)]
  if len(colors) != width * height:
    raise ValueError(f"colors has {len(colors)} values; width * height is {width * height}")
  if any(isinstance(c, bool) or not isinstance(c, int) or not 0 <= c <= 9 for c in colors):
    raise ValueError("colors must be ints in 0..9")

  grid, output = common.grid(width, height), common.grid(2 * width, 2 * height)
  for r in range(height):
    for c in range(width):
      color = colors[r * width + c]
      grid[r][c] = color
      output[r + height][c + width] = color
      output[r + height][width - 1 - c] = color
      output[height - 1 - r][c + width] = color
      output[height - 1 - r][width - 1 - c] = color
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[5, 5, 9, 9, 9, 5, 5, 5, 5, 7, 5, 7]),
      generate(colors=[6, 2, 4, 2, 2, 2, 6, 6, 6, 4, 2, 4]),
      generate(colors=[3, 3, 5, 5, 5, 8, 5, 8, 8, 8, 5, 8]),
  ]
  test = [
      generate(colors=[8, 5, 7, 8, 7, 7, 8, 8, 5, 5, 8, 5]),
  ]
  return {"train": train, "test": test}
