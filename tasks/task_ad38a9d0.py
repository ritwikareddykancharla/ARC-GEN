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


def _sample_positions(colors, max_nodes=4096):
  """Pack exact silhouettes with edge clearance; diagonal contact is allowed."""
  shapes = {
      2: [(0, 0), (1, 0), (2, 0)],
      3: [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
      4: [(0, 0), (0, 1), (1, 1)],
      5: [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],
      8: [(0, 0), (0, 1), (1, 1), (1, 2)],
      9: [(0, 0), (1, 0)],
  }
  options = []
  for color in colors:
    shape = shapes[color]
    choices = []
    for r in range(9 - max(y for y, x in shape)):
      for c in range(9 - max(x for y, x in shape)):
        cells = {(r+y, c+x) for y, x in shape}
        margin = {(y+dy, x+dx) for y, x in cells
                  for dy, dx in ((0, 0), (0, 1), (0, -1), (1, 0), (-1, 0))}
        mask = sum(1 << (y*9+x) for y, x in cells)
        blocked = sum(1 << (y*9+x) for y, x in margin
                      if 0 <= y < 9 and 0 <= x < 9)
        choices.append((r, c, mask, blocked))
    options.append(common.shuffle(choices))
  order = sorted(range(len(colors)), key=lambda i: -len(shapes[colors[i]]))
  positions, nodes = [None] * len(colors), 0

  def search(depth, blocked):
    nonlocal nodes
    if nodes >= max_nodes: return False
    nodes += 1
    if depth == len(order): return True
    i = order[depth]
    for r, c, cells, margin in options[i]:
      if cells & blocked: continue
      positions[i] = r, c
      if search(depth + 1, blocked | margin): return True
      if nodes >= max_nodes: break
    return False

  if not search(0, 0): return None
  return [p[0] for p in positions], [p[1] for p in positions]


def generate(rows=None, cols=None, colors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    rows: The rows of the shapes.
    cols: The columns of the shapes.
    colors: The colors of the shapes.
  """

  def draw():
    index = -1
    bad = False
    grid, output = common.grids(9, 9, 7)
    hidden = common.grid(9, 9, -1)
    def put(r, c, color):
      nonlocal index, bad, grid, output, hidden
      if grid[r][c] != 7: bad = True
      grid[r][c] = 6
      output[r][c] = color
      hidden[r][c] = index
    for row, col, color in zip(rows, cols, colors):
      index += 1
      if color == 2:
        put(row, col, 2)
        put(row + 1, col, 2)
        put(row + 2, col, 2)
      if color == 3:
        put(row, col + 1, 3)
        put(row + 1, col, 3)
        put(row + 1, col + 1, 3)
        put(row + 1, col + 2, 3)
        put(row + 2, col + 1, 3)
      if color == 4:
        put(row, col, 4)
        put(row, col + 1, 4)
        put(row + 1, col + 1, 4)
      if color == 5:
        put(row, col, 5)
        put(row, col + 1, 5)
        put(row, col + 2, 5)
        put(row + 1, col, 5)
        put(row + 1, col + 1, 5)
        put(row + 1, col + 2, 5)
      if color == 8:
        put(row, col, 8)
        put(row, col + 1, 8)
        put(row + 1, col + 1, 8)
        put(row + 1, col + 2, 8)
      if color == 9:
        put(row, col, 9)
        put(row + 1, col, 9)
    # Check that no two colors share an adjacent edge.
    for r in range(9):
      for c in range(8):
        if hidden[r][c] == -1 or hidden[r][c + 1] == -1: continue
        if hidden[r][c] != hidden[r][c + 1]: bad = True
    for r in range(8):
      for c in range(9):
        if hidden[r][c] == -1 or hidden[r + 1][c] == -1: continue
        if hidden[r][c] != hidden[r + 1][c]: bad = True
    if bad: return None, None
    return grid, output

  if rows is None:
    extra = common.randint(0, 2)
    for _ in range(256):
      colors = [2, 3, 4, 5, 8, 9]
      colors += common.sample(colors, extra)
      colors = common.shuffle(colors)
      placement = _sample_positions(colors)
      if placement is None: continue
      rows, cols = placement
      grid, _ = draw()
      if grid: break
    else:
      raise RuntimeError("bounded sampler failed to place all shapes")

  grid, output = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(rows=[0, 0, 2, 2, 3, 4, 6, 7], cols=[0, 4, 2, 8, 6, 1, 7, 4],
               colors=[4, 8, 3, 2, 9, 2, 4, 5]),
      generate(rows=[1, 1, 2, 5, 6, 7], cols=[0, 4, 6, 4, 8, 1],
               colors=[3, 9, 4, 8, 2, 5]),
  ]
  test = [
      generate(rows=[0, 0, 2, 3, 6, 6, 7], cols=[0, 4, 8, 3, 0, 7, 5],
               colors=[3, 8, 2, 5, 4, 4, 9]),
  ]
  return {"train": train, "test": test}
