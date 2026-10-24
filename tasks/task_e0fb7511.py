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

import random

import common


MAX_ATTEMPTS = 200


def _dimension(value, name):
  """Returns a validated canvas dimension."""
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{name} must be an int, got {value!r}")
  if not 1 <= value <= 30:
    raise ValueError(f"{name} must be in 1..30, got {value}")
  return value


def default_min_marked(width, height):
  """The legacy 13-of-169 azure floor, scaled with area (at least one pair)."""
  return max(2, round(13 * width * height / 169))


def generate(colors=None, width=None, height=None, density=None,
             min_marked=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: 0/1 cells row by row (width * height values); black (0) cells on
      blue (1). Explicit scenes are labelled as given, never filtered.
    width: Canvas width, 1..30. None samples 6..30, or uses the legacy 13
      when colors is given.
    height: Canvas height, 1..30. None samples 6..30, or uses the legacy 13
      when colors is given.
    density: Black probability per cell for sampled scenes, 0 < density < 1.
      None samples 0.15..0.35 once per call (fixtures: 0.16..0.31).
    min_marked: Sampling-clarity floor on the number of azure (8) cells in
      sampled scenes. None uses default_min_marked(width, height), which is
      the legacy 13 at 13x13. Layouts are redrawn at most MAX_ATTEMPTS times.
  """

  def draw(cells):
    grid, output = common.grids(width, height)
    for i, color in enumerate(cells):
      output[i // width][i % width] = grid[i // width][i % width] = color
    for row in range(height):
      for col in range(width):
        if grid[row][col]: continue
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
          if common.get_pixel(grid, row + dr, col + dc) == 0:
            output[row][col] = 8
    return grid, output

  explicit = colors is not None
  if explicit and (density is not None or min_marked is not None):
    raise ValueError("density and min_marked apply only to sampled scenes")
  if width is None:
    width = 13 if explicit else common.randint(6, 30)
  if height is None:
    height = 13 if explicit else common.randint(6, 30)
  width, height = _dimension(width, "width"), _dimension(height, "height")

  if explicit:
    if len(colors) != width * height:
      raise ValueError(f"colors has {len(colors)} values; width * height is {width * height}")
    if any(type(c) is not int or c not in (0, 1) for c in colors):
      raise ValueError("colors must contain only 0 (black) and 1 (blue)")
    grid, output = draw(colors)
    return {"input": grid, "output": output}

  if density is None:
    density = random.uniform(0.15, 0.35)
  if isinstance(density, bool) or not isinstance(density, (int, float)) or not 0 < density < 1:
    raise ValueError(f"density must be a number strictly between 0 and 1, got {density!r}")
  if min_marked is None:
    min_marked = default_min_marked(width, height)
  if isinstance(min_marked, bool) or not isinstance(min_marked, int) or min_marked < 0:
    raise ValueError(f"min_marked must be a non-negative int, got {min_marked!r}")
  if min_marked > width * height or (min_marked and width * height < 2):
    raise ValueError(f"min_marked={min_marked} cannot be met on a {width}x{height} canvas")
  for _ in range(MAX_ATTEMPTS):
    cells = [0 if random.random() < density else 1 for _ in range(width * height)]
    grid, output = draw(cells)
    if common.flatten(output).count(8) >= min_marked:
      return {"input": grid, "output": output}
  raise RuntimeError(f"No {width}x{height} scene at density {density:.3f} reached "
                     f"{min_marked} azure cells in {MAX_ATTEMPTS} attempts")


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1,
                       1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 1,
                       1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1,
                       1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1,
                       1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1,
                       1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1,
                       1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1,
                       1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0,
                       1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1,
                       0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1,
                       0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1,
                       1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1,
                       1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1]),
      generate(colors=[1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1,
                       1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                       1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1,
                       1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0,
                       1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1,
                       0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                       1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1,
                       0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1,
                       1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                       1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1,
                       1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1,
                       0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1,
                       1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1]),
      generate(colors=[1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1,
                       1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0,
                       1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                       1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1,
                       1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                       0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1,
                       0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1,
                       1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0,
                       1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0,
                       0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1,
                       1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1,
                       1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1,
                       0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1]),
  ]
  test = [
      generate(colors=[1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1,
                       0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0,
                       1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0,
                       0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1,
                       1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1,
                       1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0,
                       1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0,
                       1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0,
                       1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0,
                       1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1,
                       0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1,
                       1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0,
                       1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1]),
  ]
  return {"train": train, "test": test}
