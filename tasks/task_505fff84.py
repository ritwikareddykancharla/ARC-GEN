# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generator for ARC task 505fff84.

Rule: the input is a field of 0/2 noise. Some rows contain a marker pair: a
colour-1 cell with a colour-8 cell further right on the same row. Every pair
in a scene has the same gap. For each pair, in top-to-bottom row order, the
cells strictly between the 1 and the 8 are copied unchanged to form one output
row; the stacked segments form the output (height = number of pairs, width =
gap).

Scope: random scenes sample grid size, gap, pair count, pair positions and
the 0/2 noise density. Only 0 and 2 appear outside the markers, and at most
one marker pair per row, matching the original puzzle. Fixtures are rebuilt
from explicit noise grids and pair positions.
"""

import random

import common


def _copy_grid(g):
  return [list(row) for row in g]


def generate(width=None, height=None, gap=None, pairs=None, noise=None,
             density=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the width of the input grid.
    height: the height of the input grid.
    gap: the number of cells strictly between each 1 and its 8.
    pairs: a list of (row, col) positions of the colour-1 markers; the
      matching 8 is placed at col + gap + 1 on the same row.
    noise: a height x width grid of 0/2 background cells; the marker cells
      overwrite whatever lies at their positions.
    density: probability of a noise cell being 2 (random path only).
  """
  if width is None:
    width = random.randint(6, 16)
  if height is None:
    height = random.randint(3, 16)
  if gap is None:
    gap = random.randint(1, min(8, width - 2))
  if density is None:
    density = random.uniform(0.3, 0.6)
  if pairs is None:
    count = random.randint(1, min(6, height))
    rows = sorted(random.sample(range(height), count))
    pairs = [(r, random.randint(0, width - gap - 2)) for r in rows]
  if noise is None:
    noise = common.grid(width, height, 0)
    for r in range(height):
      for c in range(width):
        if random.random() < density:
          noise[r][c] = 2

  grid = _copy_grid(noise)
  output = []
  for r, c in pairs:
    grid[r][c] = 1
    grid[r][c + gap + 1] = 8
    output.append([noise[r][x] for x in range(c + 1, c + gap + 1)])
  return {"input": grid, "output": output}


def validate():
  """Validates the generator against the original ARC task examples."""
  train = [
      generate(width=12, height=6, gap=4, pairs=[(1, 2), (2, 0), (4, 2)],
               noise=[[2, 0, 2, 2, 0, 0, 0, 2, 0, 0, 2, 2],
                      [2, 0, 0, 2, 0, 2, 0, 0, 0, 2, 0, 2],
                      [0, 2, 2, 2, 2, 0, 2, 0, 0, 0, 2, 0],
                      [2, 0, 0, 0, 2, 2, 2, 0, 2, 2, 0, 0],
                      [2, 2, 0, 0, 2, 2, 2, 0, 2, 0, 2, 2],
                      [2, 0, 0, 2, 0, 2, 0, 2, 2, 2, 0, 0]]),
      generate(width=11, height=4, gap=7, pairs=[(2, 1)],
               noise=[[2, 0, 0, 0, 0, 2, 0, 0, 0, 2, 2],
                      [2, 2, 0, 0, 2, 0, 0, 2, 0, 2, 0],
                      [2, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0]]),
      generate(width=10, height=5, gap=3, pairs=[(1, 0), (3, 5)],
               noise=[[2, 2, 0, 0, 2, 2, 0, 2, 2, 0],
                      [0, 0, 2, 0, 0, 0, 2, 0, 0, 0],
                      [2, 2, 0, 0, 0, 2, 0, 0, 0, 2],
                      [2, 0, 2, 0, 0, 0, 2, 0, 0, 0],
                      [2, 2, 0, 0, 2, 2, 0, 2, 2, 0]]),
      generate(width=12, height=8, gap=6, pairs=[(0, 0), (1, 0), (2, 0)],
               noise=[[0, 2, 0, 2, 0, 0, 0, 0, 2, 0, 0, 2],
                      [0, 2, 0, 2, 0, 2, 0, 0, 0, 0, 0, 2],
                      [0, 0, 2, 2, 0, 2, 2, 0, 0, 0, 2, 2],
                      [2, 2, 0, 0, 0, 0, 2, 2, 0, 0, 2, 2],
                      [0, 2, 2, 0, 0, 0, 0, 0, 2, 2, 2, 0],
                      [0, 2, 2, 2, 2, 0, 0, 0, 0, 0, 2, 2],
                      [0, 2, 0, 2, 0, 0, 2, 0, 2, 0, 2, 2],
                      [2, 0, 0, 2, 0, 0, 2, 2, 2, 0, 0, 0]]),
      generate(width=11, height=14, gap=5,
               pairs=[(3, 2), (5, 0), (7, 3), (8, 4), (11, 1)],
               noise=[[2, 2, 2, 0, 2, 2, 0, 2, 2, 0, 2],
                      [2, 0, 0, 0, 0, 2, 2, 2, 0, 0, 0],
                      [0, 2, 2, 2, 2, 0, 2, 2, 0, 2, 2],
                      [2, 0, 0, 2, 2, 2, 0, 0, 0, 2, 0],
                      [0, 0, 2, 0, 0, 2, 0, 2, 0, 0, 0],
                      [0, 2, 2, 0, 0, 2, 0, 0, 0, 0, 2],
                      [0, 0, 0, 0, 0, 0, 2, 0, 2, 2, 2],
                      [0, 0, 2, 0, 2, 0, 0, 0, 2, 0, 0],
                      [0, 2, 0, 0, 0, 2, 2, 2, 0, 2, 0],
                      [0, 2, 0, 2, 2, 0, 2, 2, 2, 0, 0],
                      [2, 0, 0, 2, 0, 0, 0, 2, 0, 2, 0],
                      [2, 0, 2, 2, 2, 2, 2, 0, 2, 2, 0],
                      [2, 2, 2, 0, 2, 0, 0, 2, 0, 0, 2],
                      [0, 0, 2, 0, 2, 0, 2, 2, 2, 2, 0]]),
  ]
  test = [
      generate(width=14, height=9, gap=5,
               pairs=[(0, 2), (2, 1), (3, 2), (5, 1), (7, 4)],
               noise=[[2, 0, 0, 0, 2, 0, 2, 2, 0, 2, 0, 0, 0, 0],
                      [2, 2, 2, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 2],
                      [0, 0, 0, 2, 2, 0, 2, 0, 2, 0, 0, 0, 0, 2],
                      [0, 2, 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 2, 2],
                      [2, 0, 2, 0, 2, 0, 2, 2, 0, 2, 2, 2, 0, 0],
                      [0, 0, 2, 2, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2],
                      [2, 0, 0, 0, 2, 2, 0, 0, 2, 0, 2, 2, 2, 0],
                      [2, 2, 2, 2, 0, 0, 0, 2, 0, 0, 0, 0, 2, 2],
                      [0, 0, 0, 0, 2, 0, 0, 2, 2, 0, 0, 0, 2, 2]]),
  ]
  return {"train": train, "test": test}
