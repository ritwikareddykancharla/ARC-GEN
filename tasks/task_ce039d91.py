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

# Worst measured acceptance is ~29% per scene (4x3); 1,000 proposals
# fail with probability < 1e-140 on any valid canvas.
PROPOSALS = 1000


def generate(colors=None, width=None, height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: A list of colors to use (row-major, width * height entries).
    width: Grid width; 10 for supplied colors, otherwise a random even 4..30.
    height: Grid height; 10 for supplied colors, otherwise random 3..30.
  """

  if colors is None:
    width = 2 * common.randint(2, 15) if width is None else width
    height = common.randint(3, 30) if height is None else height
    if width % 2 or not (4 <= width <= 30 and 3 <= height <= 30):
      raise ValueError("Random width must be even 4..30 and height 3..30")
    for _ in range(PROPOSALS):
      pair, single = common.randint(5, 18), common.randint(4, 15)
      grid = common.grid(width, height)
      for row in range(height):
        for col in range(width):
          if common.randint(1, 100) <= pair:
            grid[row][col] = grid[row][width - 1 - col] = 5
          elif common.randint(1, 100) <= single:
            grid[row][col] = 5
      cells = common.flatten(grid)
      grey = cells.count(5)
      mirrored = sum(1 for row in grid for col in range(width)
                     if row[col] and row[width - 1 - col])
      # Black must remain the modal background, and both outcomes must show.
      if 0 < mirrored < grey and 2 * grey < len(cells): break
    else:
      raise RuntimeError("No valid ce039d91 scene within the proposal budget")
    colors = cells
  else:
    width = 10 if width is None else width
    height = 10 if height is None else height
    if len(colors) != width * height:
      raise ValueError("Expected width * height colors")

  grid, output = common.grids(width, height)
  for i, color in enumerate(colors):
    grid[i // width][i % width] = color
  for row in range(height):
    for col in range(width):
      if not grid[row][col]: continue
      output[row][col] = 1 if grid[row][width - 1 - col] else 5
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[0, 0, 0, 0, 0, 5, 0, 0, 0, 0,
                       0, 5, 0, 0, 0, 0, 0, 0, 5, 5,
                       0, 0, 0, 5, 5, 5, 5, 0, 0, 0,
                       0, 0, 0, 0, 5, 5, 0, 0, 0, 0,
                       0, 0, 0, 0, 5, 0, 0, 0, 0, 0,
                       0, 0, 5, 0, 0, 0, 0, 5, 0, 0,
                       0, 0, 0, 0, 0, 5, 0, 0, 0, 0,
                       0, 0, 5, 0, 5, 5, 5, 0, 0, 0,
                       0, 5, 0, 0, 5, 5, 0, 0, 5, 0,
                       5, 0, 0, 0, 5, 5, 0, 0, 0, 5]),
      generate(colors=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 5, 5, 0, 0, 0, 0,
                       0, 0, 0, 0, 5, 5, 0, 0, 0, 0,
                       0, 0, 0, 5, 5, 5, 5, 0, 0, 0,
                       0, 0, 0, 0, 5, 0, 0, 5, 0, 0,
                       5, 0, 0, 0, 0, 0, 0, 0, 0, 5,
                       0, 0, 0, 0, 5, 5, 5, 0, 0, 0,
                       0, 5, 0, 5, 5, 5, 5, 0, 0, 0,
                       0, 0, 0, 5, 5, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
      generate(colors=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 5, 0, 0, 5, 5, 0, 0, 5, 0,
                       0, 0, 0, 5, 0, 0, 5, 0, 0, 0,
                       0, 0, 5, 0, 0, 0, 0, 5, 0, 0,
                       0, 0, 0, 5, 0, 5, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 5, 0, 0, 0, 0,
                       0, 0, 0, 0, 5, 5, 0, 0, 0, 0,
                       5, 0, 0, 0, 5, 5, 0, 0, 0, 5,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 5, 0, 0, 0, 0, 0, 5]),
      generate(colors=[0, 0, 5, 0, 0, 0, 5, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 5, 0, 0, 0,
                       0, 0, 0, 0, 5, 0, 0, 0, 0, 0,
                       0, 0, 5, 5, 5, 5, 5, 5, 0, 0,
                       0, 0, 0, 5, 0, 0, 0, 5, 0, 0,
                       0, 0, 0, 0, 5, 5, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
  ]
  test = [
      generate(colors=[0, 5, 0, 0, 0, 0, 0, 0, 5, 0,
                       0, 0, 0, 0, 5, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 5, 0, 0, 0, 0, 0,
                       0, 5, 0, 0, 0, 0, 0, 5, 0, 0,
                       0, 0, 0, 0, 5, 5, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 5, 0, 0, 0, 0,
                       0, 5, 0, 5, 5, 5, 5, 0, 5, 0,
                       0, 0, 0, 0, 5, 5, 0, 0, 0, 0,
                       0, 0, 0, 5, 5, 5, 5, 5, 0, 0,
                       0, 0, 5, 5, 5, 5, 5, 0, 0, 0]),
  ]
  return {"train": train, "test": test}
