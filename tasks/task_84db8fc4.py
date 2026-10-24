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

# Worst measured acceptance is ~4.5% per scene (3x3); 10,000 proposals
# fail with probability < 1e-190 on any valid canvas.
PROPOSALS = 10000


def generate(colors=None, width=None, height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: The colors of the pixels (row-major, width * height entries).
    width: Grid width; 10 for supplied colors, otherwise random 3..30.
    height: Grid height; 10 for supplied colors, otherwise random 3..30.
  """

  if colors is not None:
    width = 10 if width is None else width
    height = 10 if height is None else height
    if len(colors) != width * height:
      raise ValueError("Expected width * height colors")

  def draw():
    grid, output = common.grids(width, height)
    queue = []
    for i, color in enumerate(colors):
      r, c = i // width, i % width
      output[r][c] = grid[r][c] = color
      if color == 0 and (r in [0, height - 1] or c in [0, width - 1]):
        output[r][c] = 2
        queue.append((r, c))
    while queue:
      r, c = queue.pop()
      for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nr, nc = r + dr, c + dc
        if nr < 0 or nr >= height or nc < 0 or nc >= width: continue
        if output[nr][nc] == 0:
          output[nr][nc] = 2
          queue.append((nr, nc))
    for row in range(height):
      for col in range(width):
        if output[row][col] == 0: output[row][col] = 5
    if len(set(common.flatten(output))) < 4: return None, None
    return grid, output

  if colors is None:
    width = common.randint(3, 30) if width is None else width
    height = common.randint(3, 30) if height is None else height
    if not (3 <= width <= 30 and 3 <= height <= 30):
      raise ValueError("Random dimensions must be 3..30")
    for _ in range(PROPOSALS):
      # Empty-cell and wall-colour proportions vary; the original is 1/3 each.
      empty = common.randint(25, 45)
      blue = common.randint(25, 75)
      colors = [0 if common.randint(1, 100) <= empty else
                (1 if common.randint(1, 100) <= blue else 3)
                for _ in range(width * height)]
      grid, _ = draw()
      if grid: break
    else:
      raise RuntimeError("No valid 84db8fc4 scene within the proposal budget")

  grid, output = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[0, 3, 0, 3, 0, 0, 1, 3, 3, 1,
                       0, 1, 1, 1, 1, 3, 0, 0, 1, 1,
                       0, 3, 1, 0, 1, 0, 3, 0, 3, 0,
                       3, 3, 3, 0, 0, 3, 3, 3, 0, 0,
                       1, 1, 3, 1, 3, 0, 0, 0, 1, 0,
                       1, 0, 1, 0, 3, 0, 3, 3, 0, 3,
                       0, 0, 0, 0, 1, 1, 3, 0, 1, 0,
                       3, 0, 1, 3, 3, 1, 0, 3, 0, 0,
                       1, 1, 0, 0, 1, 3, 3, 1, 1, 3,
                       0, 0, 1, 1, 0, 1, 0, 0, 0, 0]),
      generate(colors=[0, 3, 3, 0, 3, 1, 0, 1, 1, 3,
                       1, 3, 0, 0, 1, 1, 3, 1, 0, 0,
                       1, 0, 1, 0, 0, 1, 3, 0, 3, 3,
                       0, 0, 3, 3, 1, 3, 3, 3, 0, 1,
                       0, 0, 3, 3, 0, 0, 0, 0, 3, 1,
                       3, 3, 0, 0, 3, 0, 0, 0, 3, 0,
                       0, 0, 3, 3, 3, 0, 3, 0, 3, 3,
                       3, 1, 1, 1, 3, 0, 1, 1, 1, 3,
                       0, 0, 1, 3, 1, 0, 0, 3, 3, 3,
                       0, 3, 3, 0, 3, 3, 1, 3, 1, 1]),
      generate(colors=[0, 0, 0, 0, 0, 0, 3, 1, 1, 3,
                       0, 0, 3, 1, 0, 1, 1, 0, 0, 3,
                       0, 1, 0, 0, 1, 3, 3, 1, 3, 1,
                       0, 1, 3, 0, 0, 0, 0, 0, 1, 0,
                       0, 1, 3, 1, 0, 1, 0, 3, 0, 1,
                       1, 0, 0, 3, 1, 3, 1, 0, 1, 0,
                       1, 0, 0, 3, 0, 1, 0, 3, 0, 0,
                       0, 1, 0, 1, 1, 0, 3, 1, 0, 3,
                       0, 3, 1, 1, 3, 0, 0, 3, 1, 0,
                       1, 1, 3, 3, 0, 0, 1, 3, 0, 3]),
      generate(colors=[3, 1, 0, 3, 3, 3, 3, 3, 0, 3,
                       1, 0, 0, 3, 3, 0, 1, 3, 1, 1,
                       0, 1, 1, 1, 0, 3, 0, 0, 0, 3,
                       0, 1, 3, 3, 0, 3, 1, 3, 0, 0,
                       1, 3, 1, 1, 0, 1, 3, 0, 0, 0,
                       0, 1, 1, 3, 0, 0, 3, 1, 1, 3,
                       3, 0, 1, 0, 0, 0, 0, 0, 3, 0,
                       0, 0, 0, 3, 3, 1, 0, 0, 1, 3,
                       3, 3, 1, 0, 0, 1, 1, 0, 0, 1,
                       0, 1, 3, 0, 1, 1, 1, 1, 1, 3]),
  ]
  test = [
      generate(colors=[1, 0, 0, 1, 0, 1, 1, 1, 1, 3,
                       0, 0, 0, 3, 0, 3, 0, 1, 0, 0,
                       0, 1, 0, 3, 3, 0, 1, 3, 3, 3,
                       3, 1, 3, 1, 1, 0, 3, 3, 0, 1,
                       1, 1, 3, 0, 1, 3, 0, 1, 1, 0,
                       0, 3, 0, 1, 3, 0, 1, 1, 0, 3,
                       1, 1, 3, 0, 0, 3, 0, 3, 3, 3,
                       3, 1, 1, 1, 1, 3, 1, 0, 3, 1,
                       3, 0, 0, 0, 3, 3, 1, 0, 1, 1,
                       1, 0, 3, 1, 1, 0, 0, 0, 1, 0]),
  ]
  return {"train": train, "test": test}
