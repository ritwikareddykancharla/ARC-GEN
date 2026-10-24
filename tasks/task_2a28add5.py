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


def generate(colors=None, width=None, height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: A list of colors to use (row-major, `width` cells per row).
    width: Canvas width; random scenes sample it independently in 5..30.
    height: Canvas height; random scenes sample it independently in 5..30.
  """

  def draw():
    grid, output = common.grids(width, height, 7)
    for i, color in enumerate(colors):
      grid[i // width][i % width] = color
    for row in range(height):
      for col in range(width):
        if grid[row][col] != 6: continue
        num_left, num_right = 0, 0
        for c in range(0, col):
          if grid[row][c] != 7: num_left += 1
        for c in range(col + 1, width):
          if grid[row][c] != 7: num_right += 1
        for c in range(col - num_left, col + num_right + 1):
          output[row][c] = 8
    return grid, output

  if colors is None:
    width = common.randint(5, 30) if width is None else width
    height = common.randint(5, 30) if height is None else height
    if not (5 <= width <= 30 and 5 <= height <= 30):
      raise ValueError('Random dimensions must be 5..30')
    subset = common.sample([0, 1, 2, 3, 4, 5, 8, 9], common.randint(3, 8))
    freq = common.randint(1, 2)
    for _ in range(100):
      grid = common.grid(width, height, 7)
      for row in range(height):
        for col in range(width):
          if common.randint(0, freq): continue
          grid[row][col] = common.choice(subset)
      for row in range(height):
        if common.randint(0, 1): continue
        grid[row][common.randint(0, width - 1)] = 6
      counts = [sum(row.count(c) for row in grid) for c in range(10)]
      # Every original scene has at least one 6 anchor and a strictly
      # dominant orange background; small canvases make both worth checking.
      if counts[6] and counts[7] > max(counts[:7] + counts[8:]): break
    else:
      raise RuntimeError('Cannot sample an anchored scene; retry')
    colors = common.flatten(grid)
  else:
    width = 10 if width is None else width
    height = len(colors) // width if height is None else height
    if width * height != len(colors):
      raise ValueError('colors must contain width * height cells')

  grid, output = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[7, 7, 4, 7, 6, 7, 0, 7, 7, 7,
                       7, 5, 1, 3, 7, 7, 7, 7, 9, 1,
                       7, 2, 3, 7, 2, 7, 7, 7, 7, 7,
                       7, 8, 9, 7, 8, 7, 0, 7, 2, 8,
                       5, 9, 7, 1, 7, 5, 6, 8, 7, 8,
                       7, 2, 7, 0, 7, 7, 7, 1, 7, 6,
                       7, 7, 7, 7, 7, 7, 7, 7, 7, 4,
                       7, 7, 8, 7, 7, 4, 0, 7, 7, 5,
                       6, 7, 7, 7, 1, 2, 7, 7, 0, 4,
                       7, 7, 7, 7, 7, 2, 1, 7, 6, 7]),
      generate(colors=[7, 7, 7, 7, 7, 7, 7, 5, 7, 7,
                       7, 7, 9, 6, 7, 7, 2, 7, 7, 7,
                       7, 7, 7, 7, 7, 7, 7, 2, 9, 7,
                       2, 7, 9, 9, 7, 6, 7, 5, 7, 7,
                       7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
                       7, 7, 7, 7, 7, 2, 7, 7, 7, 7,
                       7, 5, 9, 6, 7, 7, 7, 7, 7, 9,
                       7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
                       7, 2, 7, 7, 7, 9, 7, 7, 7, 7,
                       7, 2, 2, 7, 7, 7, 7, 6, 7, 5]),
  ]
  test = [
      generate(colors=[0, 5, 7, 4, 7, 5, 1, 3, 7, 7,
                       7, 7, 7, 4, 4, 6, 5, 2, 7, 7,
                       4, 6, 2, 8, 7, 7, 8, 7, 0, 3,
                       1, 7, 7, 5, 3, 7, 6, 3, 7, 7,
                       0, 9, 7, 7, 7, 3, 7, 7, 7, 7,
                       7, 9, 3, 0, 7, 0, 5, 5, 3, 7,
                       7, 1, 7, 1, 7, 5, 5, 8, 7, 6,
                       7, 7, 7, 3, 3, 2, 7, 0, 9, 2,
                       7, 7, 0, 7, 6, 0, 7, 7, 1, 7,
                       1, 7, 4, 7, 1, 2, 7, 7, 1, 7]),
  ]
  return {"train": train, "test": test}
