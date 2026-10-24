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


MAX_ATTEMPTS = 100


def _dimension(value, name, low):
  """Returns a validated canvas dimension."""
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{name} must be an int, got {value!r}")
  if not low <= value <= 30:
    raise ValueError(f"{name} must be in {low}..30, got {value}")
  return value


def placement_range(height):
  """Placements per colour: the legacy 2..8 at height 10, scaled with height.

  The maximum never exceeds the height, so no bar can outgrow the canvas.
  """
  high = min(height, max(2, 4 * height // 5))
  return min(2, high), high


def generate(colors=None, width=None, height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: The colors of the pixels, row by row (width * height values in
      0..4). Each of 1..4 must appear, at most height times.
    width: Canvas width, 4..30 (the four bar columns). None samples 4..30, or
      uses the legacy 10 when colors is given.
    height: Canvas height, 1..30. None samples 4..30, or uses the legacy 10
      when colors is given.

  Sampled scenes place each colour placement_range(height) times at random
  cells (later placements may overwrite earlier ones) and redraw at most
  MAX_ATTEMPTS times until all four colours survive. With explicit 10x10
  dimensions this consumes the RNG exactly like the legacy constructor.
  """

  explicit = colors is not None
  if width is None:
    width = 10 if explicit else common.randint(4, 30)
  if height is None:
    height = 10 if explicit else common.randint(4, 30)
  width, height = _dimension(width, "width", 4), _dimension(height, "height", 1)

  if colors is None:
    low, high = placement_range(height)
    for _ in range(MAX_ATTEMPTS):
      colors = [0] * (width * height)
      for color in range(1, 5):
        for _ in range(common.randint(low, high)):
          colors[common.randint(0, width * height - 1)] = color
      if all(colors.count(color) for color in range(1, 5)): break
    else:
      raise RuntimeError(f"No {width}x{height} scene kept all four colours in "
                         f"{MAX_ATTEMPTS} attempts")
  if len(colors) != width * height:
    raise ValueError(f"colors has {len(colors)} values; width * height is {width * height}")
  if any(type(c) is not int or c not in (0, 1, 2, 3, 4) for c in colors):
    raise ValueError("colors must contain only 0..4")
  for color in range(1, 5):
    if not 1 <= colors.count(color) <= height:
      raise ValueError(f"colour {color} must appear 1..{height} times, "
                       f"got {colors.count(color)}")

  grid, output = common.grids(width, height)
  for i, color in enumerate(colors):
    grid[i // width][i % width] = color
  for color in range(1, 5):
    for r in range(colors.count(color)):
      output[height - 1 - r][color - 1] = color
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[0, 0, 0, 0, 0, 4, 0, 3, 3, 0, 0, 1, 3, 0, 0, 0, 3, 0, 0,
                       0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 4, 3, 0, 0, 0, 2, 0, 0, 0,
                       2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 3, 0, 0, 0, 4,
                       3, 2, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 3, 0, 0, 0, 4, 0, 0,
                       4, 0, 1, 0, 1]),
      generate(colors=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4,
                       0, 2, 0, 0, 0, 0, 3, 0, 1, 4, 1, 0, 0, 0, 0, 0, 0, 1, 0,
                       0, 0, 1, 4, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 2, 0, 0,
                       0, 2, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 0, 4,
                       0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 0,
                       0, 0, 0, 0, 0]),
      generate(colors=[0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 3, 0, 0, 0, 0, 0, 3, 0, 0, 1, 0, 0, 2, 0, 0, 4,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 3, 0,
                       0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0,
                       0, 0, 4, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0]),
  ]
  test = [
      generate(colors=[0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 3, 0, 0, 2, 4, 0, 0,
                       0, 0, 3, 0, 2, 0, 0, 0, 0, 0, 3, 4, 0, 0, 1, 0, 0, 0, 1,
                       0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 3, 0, 1, 0, 3, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 3, 0, 0, 0, 0, 2,
                       4, 0, 2, 4, 2]),
  ]
  return {"train": train, "test": test}
