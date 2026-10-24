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
    colors: A list of colors to use (row-major, width * height entries).
    width: Grid width; 10 for supplied colors, otherwise random 5..30.
    height: Grid height; 10 for supplied colors, otherwise random 5..30.
  """

  if colors is not None:
    width = 10 if width is None else width
    height = 10 if height is None else height
    if len(colors) != width * height:
      raise ValueError("Expected width * height colors")

  def draw():
    grid, output = common.grids(width, height)
    for i, color in enumerate(colors):
      output[i // width][i % width] = grid[i // width][i % width] = color
    for size in range(min(width, height), 1, -1):
      # empty[r][c]: side of the largest all-zero square ending at (r, c).
      empty = [[0] * (width + 1) for _ in range(height + 1)]
      for r in range(height):
        for c in range(width):
          if not output[r][c]:
            empty[r + 1][c + 1] = 1 + min(empty[r][c], empty[r][c + 1],
                                          empty[r + 1][c])
      coords = [(r - size + 1, c - size + 1)
                for r in range(size - 1, height)
                for c in range(size - 1, width)
                if empty[r + 1][c + 1] >= size]
      for row, col in coords:
        for r in range(row, row + size):
          for c in range(col, col + size):
            # Same-size empty squares must be disjoint (order independence).
            if output[r][c]: return None, None
            output[r][c] = 1
    return grid, output

  if colors is None:
    width = common.randint(5, 30) if width is None else width
    height = common.randint(5, 30) if height is None else height
    if not (5 <= width <= 30 and 5 <= height <= 30):
      raise ValueError("Random dimensions must be 5..30")
    area = width * height
    while True:
      grey = common.randint(62, 80)
      num_boxes = common.randint(1, max(2, min(10, area // 18)))
      sizes = [common.choice([2, 2, 2, 3, 3, 4]) for _ in range(num_boxes)]
      for _ in range(50):
        brows = [common.randint(0, height - size) for size in sizes]
        bcols = [common.randint(0, width - size) for size in sizes]
        if not common.overlaps(brows, bcols, sizes, sizes): break
      else:
        continue
      grid = common.grid(width, height)
      for row in range(height):
        for col in range(width):
          grid[row][col] = 5 if common.randint(1, 100) <= grey else 0
      for br, bc, size in zip(brows, bcols, sizes):
        for r in range(br, br + size):
          for c in range(bc, bc + size):
            grid[r][c] = 0
      colors = common.flatten(grid)
      grid, _ = draw()
      if grid: break
      colors = None

  grid, output = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[0, 5, 0, 0, 5, 0, 0, 0, 0, 0,
                       5, 5, 0, 0, 0, 5, 5, 0, 5, 0,
                       0, 0, 0, 5, 5, 0, 0, 5, 5, 5,
                       0, 0, 5, 0, 5, 5, 0, 0, 5, 0,
                       0, 5, 0, 0, 0, 0, 0, 0, 5, 0,
                       5, 0, 5, 0, 0, 5, 5, 5, 0, 5,
                       0, 0, 0, 5, 0, 5, 5, 0, 5, 0,
                       0, 0, 5, 0, 5, 5, 5, 0, 0, 0,
                       5, 0, 5, 5, 0, 5, 5, 0, 5, 0,
                       0, 0, 0, 0, 0, 0, 0, 5, 0, 0]),
      generate(colors=[5, 5, 0, 0, 0, 0, 0, 5, 0, 0,
                       0, 0, 5, 5, 0, 0, 0, 0, 5, 5,
                       5, 5, 0, 5, 0, 0, 0, 0, 5, 0,
                       0, 0, 0, 0, 5, 5, 5, 5, 0, 5,
                       0, 5, 0, 5, 0, 5, 5, 0, 5, 0,
                       5, 0, 0, 0, 0, 5, 0, 0, 5, 5,
                       5, 5, 5, 0, 5, 0, 0, 0, 0, 5,
                       0, 5, 0, 0, 0, 0, 5, 5, 5, 0,
                       5, 0, 0, 0, 0, 5, 0, 0, 5, 5,
                       5, 0, 0, 0, 0, 0, 5, 5, 0, 0]),
      generate(colors=[0, 0, 5, 0, 0, 0, 0, 5, 0, 5,
                       0, 5, 0, 0, 0, 5, 0, 0, 0, 5,
                       0, 0, 5, 0, 5, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 5, 0, 0, 0, 0, 0,
                       0, 5, 5, 0, 0, 5, 5, 5, 0, 5,
                       5, 0, 0, 5, 0, 5, 0, 0, 0, 0,
                       5, 5, 5, 5, 0, 5, 5, 5, 0, 0,
                       0, 0, 0, 5, 0, 0, 0, 0, 5, 0,
                       0, 0, 0, 0, 5, 5, 5, 5, 5, 5,
                       0, 0, 0, 0, 0, 5, 0, 0, 5, 0]),
  ]
  test = [
      generate(colors=[5, 0, 0, 0, 5, 0, 5, 0, 5, 0,
                       5, 0, 0, 5, 0, 5, 5, 0, 0, 0,
                       5, 5, 0, 5, 5, 0, 0, 5, 5, 0,
                       5, 0, 0, 0, 0, 0, 0, 5, 0, 0,
                       5, 0, 0, 0, 5, 5, 0, 0, 0, 5,
                       0, 0, 0, 0, 0, 0, 5, 5, 0, 0,
                       0, 0, 5, 5, 0, 0, 5, 5, 0, 0,
                       5, 0, 5, 0, 5, 0, 5, 0, 0, 5,
                       0, 5, 5, 0, 5, 0, 0, 5, 5, 5,
                       0, 0, 0, 5, 5, 5, 0, 0, 0, 0]),
  ]
  return {"train": train, "test": test}
