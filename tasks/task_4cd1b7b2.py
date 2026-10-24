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


MIN_BLANKS, MAX_BLANKS = 1, 7
MAX_ATTEMPTS = 1000


def generate(colors=None, blanks=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: colors of the pixels.
    blanks: number of blank cells (sampling only, 1..7).

  Each blank is carved from a row or column that is still complete, so the
  zeros can be restored in reverse order by single-line propagation and the
  Latin completion is unique. Each carved blank permanently breaks the
  perpendicular line through it, so at most seven of the eight lines can be
  used: 1..7 is the full range of this scheme (the legacy sampler kept only
  5..6). The 4x4 grid and colours 1..4 are rule-tied and unchanged.
  """

  def solve(ingrid):
    grid = [list(row) for row in ingrid]
    changed = True
    while changed:
      changed = False
      for r in range(4):
        values = [grid[r][c] for c in range(4) if grid[r][c] != 0]
        if len(values) != 3: continue
        value = 10 - sum(values)
        for c in range(4):
          if grid[r][c] == 0: grid[r][c] = value
        changed = True
      for c in range(4):
        values = [grid[r][c] for r in range(4) if grid[r][c] != 0]
        if len(values) != 3: continue
        value = 10 - sum(values)
        for r in range(4):
          if grid[r][c] == 0: grid[r][c] = value
        changed = True
    return grid

  def create_grid():
    rows = []
    for _ in range(4):
      while True:
        candidate = common.shuffle([1, 2, 3, 4])
        good = True
        for row in rows:
          for c in range(4):
            if row[c] == candidate[c]: good = False
        if good: break
      rows.append(candidate)
    return rows

  def strip_grid(grid, limit):
    num_zeroed = 0
    strips = common.shuffle([(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)])
    for strip in strips:
      if num_zeroed == limit: break
      cdir, val = strip
      if cdir == 1 and sum([grid[val][r] for r in range(4)]) == 10:
        grid[val][common.randint(0, 3)] = 0
        num_zeroed += 1
      elif cdir == 0 and sum([grid[c][val] for c in range(4)]) == 10:
        grid[common.randint(0, 3)][val] = 0
        num_zeroed += 1
    return num_zeroed

  if colors is None:
    if blanks is None:
      blanks = common.randint(MIN_BLANKS, MAX_BLANKS)
    if (type(blanks) is not int or not MIN_BLANKS <= blanks <= MAX_BLANKS):
      raise ValueError("blanks must be an int in 1..7")
    for _ in range(MAX_ATTEMPTS):
      grid = create_grid()
      if strip_grid(grid, blanks) == blanks: break
    else:
      raise RuntimeError("no Latin square reached the requested blank count")
    colors = []
    for row in grid:
      colors.extend(row)
  elif blanks is not None:
    raise ValueError("blanks is a sampling argument; it cannot accompany colors")
  elif (len(colors) != 16
        or any(type(c) is not int or not 0 <= c <= 4 for c in colors)):
    raise ValueError("colors must be sixteen ints in 0..4")

  grid = common.grid(4, 4)
  for i, color in enumerate(colors):
    grid[i // 4][i % 4] = color
  output = solve(grid)
  if any(0 in row for row in output):
    raise ValueError("line propagation does not complete this scene")
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[0, 4, 2, 3, 4, 1, 0, 2, 0, 3, 4, 0, 3, 0, 1, 4]),
      generate(colors=[1, 0, 3, 4, 0, 0, 2, 1, 2, 1, 4, 0, 0, 3, 1, 2]),
      generate(colors=[3, 0, 2, 1, 1, 0, 0, 0, 4, 3, 0, 2, 0, 1, 4, 3]),
  ]
  test = [
      generate(colors=[0, 1, 2, 3, 0, 3, 1, 0, 3, 0, 4, 1, 0, 4, 0, 2]),
  ]
  return {"train": train, "test": test}
