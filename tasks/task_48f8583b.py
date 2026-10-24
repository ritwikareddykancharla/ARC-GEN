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

# The output is (H*H) x (W*W), so each input axis is limited to 2..5 (25 <= 30).
MIN_SIZE, MAX_SIZE = 2, 5
LEGACY_SIZE = 3            # explicit colours with an omitted dimension
MIN_COLORS, MAX_COLORS = 2, 4
MAX_ATTEMPTS = 200


def _int(value, name):
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{name} must be an int")
  return value


def _unique_minimum(colors):
  counts = sorted(colors.count(c) for c in set(colors))
  return counts.count(counts[0]) == 1


def generate(colors=None, height=None, width=None, num_colors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: A row-major list of the input colours (0..9). As in the legacy
      generator, explicit colours are labelled as given: the selected colour is
      the least frequent one, ties going to the smallest colour value. Random
      inputs always have a unique least frequent colour and never contain 0.
    height: Input height, 2..5. Sampled when omitted and colours are random;
      3 (legacy) when colours are explicit.
    width: Input width, 2..5, with the same defaults as height.
    num_colors: Sampling only: the size (2..4) of the colour subset the cells
      are drawn from. As in the legacy generator, not every subset colour has
      to appear, so a sampled input uses 1..num_colors colours (a one-colour
      input has a unique minimum: every cell is selected).
  """
  for name, value in (("height", height), ("width", width)):
    if value is not None and not MIN_SIZE <= _int(value, name) <= MAX_SIZE:
      raise ValueError(f"{name} must be in {MIN_SIZE}..{MAX_SIZE}")
  if colors is not None:
    if num_colors is not None:
      raise ValueError("num_colors is a sampling argument; omit it with explicit colors")
    height = LEGACY_SIZE if height is None else height
    width = LEGACY_SIZE if width is None else width
    colors = list(colors)
    if len(colors) != height * width:
      raise ValueError("colors must have height * width entries")
    for color in colors:
      if not 0 <= _int(color, "color") <= 9:
        raise ValueError("colors must be in 0..9")
  else:
    height = common.randint(MIN_SIZE, MAX_SIZE) if height is None else height
    width = common.randint(MIN_SIZE, MAX_SIZE) if width is None else width
    if num_colors is None:
      num_colors = common.randint(MIN_COLORS, MAX_COLORS)
    elif not MIN_COLORS <= _int(num_colors, "num_colors") <= MAX_COLORS:
      raise ValueError(f"num_colors must be in {MIN_COLORS}..{MAX_COLORS}")
    subset = common.random_colors(num_colors)
    for _ in range(MAX_ATTEMPTS):
      colors = common.choices(subset, height * width)
      if _unique_minimum(colors): break
    else:
      raise RuntimeError("attempt budget exhausted before a unique least frequent colour")

  grid, output = common.grid(width, height), common.grid(width * width, height * height)
  for i, color in enumerate(colors):
    grid[i // width][i % width] = color
  min_color = sorted([(colors.count(c), c) for c in set(colors)])[0][1]
  for row in range(height):
    for col in range(width):
      if colors[row * width + col] != min_color: continue
      for i, color in enumerate(colors):
        output[height * row + i // width][width * col + i % width] = color
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[3, 2, 7, 2, 2, 7, 5, 5, 7]),
      generate(colors=[8, 5, 5, 8, 8, 8, 5, 9, 9]),
      generate(colors=[7, 1, 7, 1, 7, 7, 7, 1, 7]),
      generate(colors=[1, 6, 6, 5, 1, 6, 5, 5, 5]),
      generate(colors=[9, 9, 6, 3, 8, 8, 8, 3, 3]),
      generate(colors=[4, 4, 2, 2, 2, 2, 2, 4, 2]),
  ]
  test = [
      generate(colors=[9, 7, 9, 9, 9, 7, 7, 9, 7]),
  ]
  return {"train": train, "test": test}
