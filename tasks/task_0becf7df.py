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


def _connected(grid):
  """Iterative 4-connectivity of all nonzero cells (common.connected is recursive)."""
  cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
  if not cells: return False
  stack = [next(iter(cells))]
  seen = {stack[0]}
  while stack:
    r, c = stack.pop()
    for cell in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
      if cell in cells and cell not in seen:
        seen.add(cell)
        stack.append(cell)
  return len(seen) == len(cells)


def generate(colors=None, width=None, height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: A list of colors to use (row-major, `width` cells per row).
    width: Canvas width; random scenes sample it independently in 7..30.
    height: Canvas height; random scenes sample it independently in 7..30.
  """

  if colors is None:
    width = common.randint(7, 30) if width is None else width
    height = common.randint(7, 30) if height is None else height
    if not (7 <= width <= 30 and 7 <= height <= 30):
      raise ValueError('Random dimensions must be 7..30')
    legend = common.random_colors(4)
    # The drawing occupies rows 1..height-2 and columns 2..width-3, as the
    # original 10x10 scenes use rows 1..8 and columns 2..7. Stroke counts grow
    # with the region so that larger canvases keep a comparable ink density.
    rows, cols = height - 2, width - 4
    mean_stroke = (rows + cols) / 4 + 1
    target = max(10, round(10 * rows * cols / mean_stroke / (48 / 4.5)))
    for _ in range(200):
      grid = common.grid(width, height)
      i = 0
      while i < target or len(set(common.flatten(grid))) < 5:
        if i >= 10 * target: break
        color = common.choice(legend + [0])
        if common.randint(0, 1):
          row = common.randint(0, rows - 1)
          length = common.randint(1, cols)
          col = common.randint(0, cols - length)
          for c in range(col, col + length):
            grid[1 + row][2 + c] = color
        else:
          col = common.randint(0, cols - 1)
          length = common.randint(1, rows)
          row = common.randint(0, rows - length)
          for r in range(row, row + length):
            grid[1 + r][2 + col] = color
        i += 1
      if len(set(common.flatten(grid))) < 5: continue
      if grid[0][2] or grid[1][2] or grid[2][2]: continue
      if _connected(grid): break
    else:
      raise RuntimeError('Cannot sample a connected legend scene; retry')
    grid[0][0] = legend[0]
    grid[0][1] = legend[1]
    grid[1][0] = legend[2]
    grid[1][1] = legend[3]
    colors = common.flatten(grid)
  else:
    width = 10 if width is None else width
    height = len(colors) // width if height is None else height
    if width * height != len(colors):
      raise ValueError('colors must contain width * height cells')

  grid, output = common.grids(width, height)
  a, b, c, d = colors[0], colors[1], colors[width], colors[width + 1]
  for i, color in enumerate(colors):
    grid[i // width][i % width] = color
    if i in [0, 1, width, width + 1]: output[i // width][i % width] = color
    else:
      if color == a: output[i // width][i % width] = b
      elif color == b: output[i // width][i % width] = a
      elif color == c: output[i // width][i % width] = d
      elif color == d: output[i // width][i % width] = c
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[1, 3, 0, 0, 0, 0, 0, 0, 0, 0,
                       2, 8, 0, 0, 0, 0, 1, 0, 0, 0,
                       0, 0, 0, 0, 1, 1, 1, 0, 0, 0,
                       0, 0, 0, 0, 1, 1, 1, 0, 0, 0,
                       0, 0, 3, 3, 3, 3, 1, 8, 0, 0,
                       0, 0, 3, 3, 2, 0, 8, 8, 0, 0,
                       0, 0, 0, 0, 2, 0, 8, 8, 0, 0,
                       0, 0, 0, 0, 2, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 2, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
      generate(colors=[4, 2, 0, 0, 0, 0, 0, 0, 0, 0,
                       3, 7, 0, 0, 0, 0, 4, 0, 0, 0,
                       0, 0, 0, 0, 0, 3, 4, 4, 0, 0,
                       0, 0, 0, 0, 0, 3, 2, 4, 0, 0,
                       0, 0, 0, 7, 7, 3, 2, 4, 0, 0,
                       0, 0, 0, 7, 3, 3, 2, 0, 0, 0,
                       0, 0, 0, 7, 0, 0, 2, 2, 0, 0,
                       0, 0, 0, 7, 7, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
      generate(colors=[9, 4, 0, 0, 0, 0, 0, 0, 0, 0,
                       7, 6, 0, 0, 0, 9, 9, 0, 0, 0,
                       0, 0, 0, 0, 0, 7, 9, 0, 0, 0,
                       0, 0, 0, 0, 0, 4, 0, 0, 0, 0,
                       0, 0, 0, 0, 7, 4, 0, 0, 0, 0,
                       0, 0, 0, 6, 6, 7, 0, 0, 0, 0,
                       0, 0, 0, 7, 6, 6, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
  ]
  test = [
      generate(colors=[8, 9, 0, 0, 0, 0, 0, 0, 0, 0,
                       2, 4, 0, 0, 0, 9, 9, 0, 0, 0,
                       0, 0, 0, 8, 8, 8, 9, 0, 0, 0,
                       0, 0, 0, 2, 8, 8, 9, 0, 0, 0,
                       0, 0, 0, 2, 4, 2, 0, 0, 0, 0,
                       0, 0, 0, 2, 2, 4, 0, 0, 0, 0,
                       0, 0, 0, 2, 4, 4, 0, 0, 0, 0,
                       0, 0, 0, 9, 4, 4, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 4, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
  ]
  return {"train": train, "test": test}
