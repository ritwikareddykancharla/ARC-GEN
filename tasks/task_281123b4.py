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


def _dimension(value, name, limit):
  """Returns a validated explicit or sampled panel dimension."""
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{name} must be an int, got {value!r}")
  if not 1 <= value <= limit:
    raise ValueError(f"{name} must be in 1..{limit} so grids fit 30x30, got {value}")
  return value


def _mask(values, name, size):
  """Validates an explicit or sampled Boolean panel mask."""
  if len(values) != size:
    raise ValueError(f"{name} has {len(values)} values; width * height is {size}")
  if any(v not in (0, 1) for v in values):
    raise ValueError(f"{name} must contain only 0/1 or False/True values")
  return values


def generate(top=None, upper=None, lower=None, bottom=None, width=None, height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    top: Boolean values for the top grid.
    upper: Boolean values for the upper grid.
    lower: Boolean values for the lower grid.
    bottom: Boolean values for the top grid.
    width: Width of the output grid (panel width), 1..6. None samples 4..6,
      or uses the legacy 4 when a mask is given.
    height: Height of the output grid (panel height), 1..30. None samples
      4..30, or uses the legacy 4 when a mask is given.

  Masks left as None are sampled; explicit values are never replaced.
  """
  explicit = any(m is not None for m in (top, upper, lower, bottom))
  if width is None:
    width = 4 if explicit else common.randint(4, 6)
  if height is None:
    height = 4 if explicit else common.randint(4, 30)
  width = _dimension(width, "width", 6)
  height = _dimension(height, "height", 30)
  size = width * height
  if top is None:
    top = [common.randint(0, 1) for _ in range(size)]
  if upper is None:
    upper = [common.randint(0, 1) for _ in range(size)]
  if lower is None:
    lower = [common.randint(0, 1) for _ in range(size)]
  if bottom is None:
    bottom = [common.randint(0, 1) for _ in range(size)]
  top = _mask(top, "top", size)
  upper = _mask(upper, "upper", size)
  lower = _mask(lower, "lower", size)
  bottom = _mask(bottom, "bottom", size)

  grid = common.grid(4 * width + 3, height)
  output = common.grid(width, height)
  for i in range(height):
    grid[i][3 * width + 2] = grid[i][2 * width + 1] = grid[i][width] = 3
  for i in range(len(upper)):
    if upper[i]:
      grid[i // width][width + 1 + i % width] = 5
      output[i // width][i % width] = 5
  for i in range(len(top)):
    if top[i]:
      grid[i // width][i % width] = 8
      output[i // width][i % width] = 8
  for i in range(len(bottom)):
    if bottom[i]:
      grid[i // width][3 * width + 3 + i % width] = 4
      output[i // width][i % width] = 4
  for i in range(len(lower)):
    if lower[i]:
      grid[i // width][2 * width + 2 + i % width] = 9
      output[i // width][i % width] = 9
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(top=[0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0],
               upper=[1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0],
               lower=[1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0],
               bottom=[1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0]),
      generate(top=[0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0],
               upper=[1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1],
               lower=[0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1],
               bottom=[1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0]),
      generate(top=[1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1],
               upper=[1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0],
               lower=[1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
               bottom=[1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0]),
      generate(top=[0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0],
               upper=[0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1],
               lower=[0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0],
               bottom=[1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0]),
      generate(top=[1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0],
               upper=[1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1],
               lower=[1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0],
               bottom=[1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1]),
      generate(top=[0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1],
               upper=[1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0],
               lower=[1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0],
               bottom=[1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0]),
  ]
  test = [
      generate(top=[1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1],
               upper=[1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1],
               lower=[1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0],
               bottom=[0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0]),
  ]
  return {"train": train, "test": test}
