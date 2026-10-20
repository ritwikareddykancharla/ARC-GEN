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


def _place(rows, cols, idxs, colors, row, col, bump, size):
  grid = common.grid(size, size)
  output = common.grid(size, size)
  for r, c, idx, color in zip(rows, cols, idxs, colors):
    if idx in [-1, 0]: grid[row + r + bump][col + c] = color
    if idx in [-1, 1]: grid[row - c][col + r] = color
    if idx in [-1, 2]: grid[row + c + bump][col - r - bump] = color
    if idx in [-1, 3]: grid[row - r][col - c - bump] = color
    output[row + r + bump][col + c] = color
    output[row - c][col + r] = color
    output[row + c + bump][col - r - bump] = color
    output[row - r][col - c - bump] = color
  return grid, output


def _rule_completions(grid):
  """(added, completion) for every centre allowed by the visible rule."""
  height, width = len(grid), len(grid[0])
  cells = [(r, c, grid[r][c]) for r in range(height) for c in range(width)
           if grid[r][c] != 0]
  results = []
  for cy2 in range(2 * height):
    for cx2 in range(2 * width):
      if (cy2 - cx2) % 2: continue
      out = [list(line) for line in grid]
      added, valid = 0, True
      for r, c, color in cells:
        dy, dx = 2 * r - cy2, 2 * c - cx2
        for _ in range(3):
          dy, dx = dx, -dy
          ty, tx = dy + cy2, dx + cx2
          if ty % 2 or tx % 2:
            valid = False
            break
          nr, nc = ty // 2, tx // 2
          if nr < 0 or nr >= height or nc < 0 or nc >= width:
            valid = False
            break
          if out[nr][nc] == 0:
            out[nr][nc] = color
            added += 1
          elif out[nr][nc] != color:
            valid = False
            break
        if not valid: break
      if valid: results.append((added, out))
  return results


def _unambiguous(grid, output):
  """True iff the label is the unique fewest-added valid completion."""
  results = _rule_completions(grid)
  if not results: return False
  best = min(added for added, _ in results)
  winners = [out for added, out in results if added == best]
  return len(winners) == 1 and winners[0] == output


def generate(row=None, col=None, rows=None, cols=None, idxs=None, colors=None,
             bump=None, size=10):
  """Returns input and output grids according to the given parameters.

  Args:
    row: a vertical offset for the pinwheel
    col: a horizontal offset for the pinwheel
    rows: a list of vertical coordinates where pixels should be placed
    cols: a list of horizontal coordinates where pixels should be placed
    idxs: a list of indices into the quadrant list (-1 for all quadrants)
    colors: a list of colors to be used
    bump: whether to bump the pinwheel
    size: the width and height of the (square) input grid
  """
  if row is None:
    for _ in range(1000):
      length = common.randint(2, 4)
      bump = length == 2
      row = common.randint(length + bump, size - length - bump)
      col = common.randint(length + bump, size - length - bump)
      rows, cols, idxs = [], [], []
      for c in range(length):
        for r in range(c + 1):
          if (r > 1 or c > 1) and common.randint(0, 1): continue
          rows.append(r)
          cols.append(c)
          if length == 2:
            idxs.append(-1 if r < 1 and c < 1 else common.randint(0, 3))
          else:
            idxs.append(-1 if r < 2 and c < 2 else common.randint(0, 3))
      color_list = common.random_colors(2)
      colors = [common.choice(color_list) for _ in idxs]
      grid, output = _place(rows, cols, idxs, colors, row, col, bump, size)
      if _unambiguous(grid, output):
        return {"input": grid, "output": output}
    raise RuntimeError("no unambiguous pinwheel scene within sampling budget")

  grid, output = _place(rows, cols, idxs, colors, row, col, bump, size)
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(row=5, col=4, rows=[0, 0, 0, 1, 2], cols=[0, 1, 2, 1, 2],
               idxs=[-1, -1, 1, -1, 0], colors=[4, 7, 7, 4, 4], bump=0),
      generate(row=4, col=3, rows=[0, 1, 1], cols=[0, 0, 1],
               idxs=[-1, 0, 3], colors=[6, 6, 3], bump=1),
      generate(row=4, col=4, rows=[0, 0, 1, 2], cols=[0, 1, 1, 2],
               idxs=[-1, -1, -1, 1], colors=[8, 8, 8, 9], bump=0),
  ]
  test = [
      generate(row=4, col=4,
               rows=[0, 0, 1, 1, 1, 1, 2, 2, 3],
               cols=[0, 1, 0, 1, 2, 3, 0, 1, 1],
               idxs=[-1, -1, -1, -1, 3, 3, 3, 2, 2],
               colors=[3, 2, 2, 3, 3, 3, 2, 3, 3], bump=0),
  ]
  return {"train": train, "test": test}
