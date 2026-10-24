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


def generate(colors=None, width=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: a list of digits representing the colors to be used
    width: Input strip length; random widths span 2..30. The coloured-cell
      count is bounded so the output side remains at most 30.
  """
  if colors is None:
    width = common.randint(2, 30) if width is None else width
    if not 2 <= width <= 30:
      raise ValueError('Random strip width must be 2..30')
    count = common.randint(1, min(width, 9, 30 // width))
    if common.randint(0, 1):
      colors = common.choices(common.random_colors(common.randint(1, count)), k=count)
    else:
      colors = common.random_colors(count)
    colors.extend([0] * (width - len(colors)))
    colors = common.shuffle(colors)
  elif width is not None and width != len(colors):
    raise ValueError('Explicit colors must match the requested width')

  num_colors = sum([1 for c in colors if c > 0])
  size = num_colors * len(colors)
  grid, output = common.grid(len(colors), 1), common.grid(size, size)
  for c, color in enumerate(colors):
    grid[0][c] = color
    for r in range(c, size):
      output[r][size - 1 + c - r] = color
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[1, 0, 7, 0, 0]),
      generate(colors=[0, 0, 2, 0, 0]),
      generate(colors=[4, 0, 6, 0, 8]),
      generate(colors=[0, 9, 0, 8, 4]),
      generate(colors=[0, 4, 0, 0, 0]),
  ]
  test = [
      generate(colors=[0, 6, 7, 8, 9]),
  ]
  return {"train": train, "test": test}
