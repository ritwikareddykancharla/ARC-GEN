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

"""ARC-GEN style generator for task da515329.

Rule: the input holds one hollow plus sign of colour 8. Its centre cell is
empty, and it has four arms of equal length L pointing up, right, down and
left. The output fills the canvas with four interleaved clockwise spirals, one
grown from each arm.

Each arm uses the same turtle program, with L' = max(L, 2):
  1. Walk L' cells from the centre along the arm direction.
  2. For k = 0, 1, 2, ..., let a = 4k + 2 and repeat:
     - turn right and walk a cells;
     - turn right and walk L' - 2 cells;
     - turn left and walk L' cells.
  3. Stop once a exceeds 2 * (H + W) + 10.
Cells that fall outside the grid are clipped.

Scope:
- Grid height and width are sampled from 10 to 30. They are square half of the
  time, like every original example, and rectangular otherwise.
- The plus centre is placed anywhere such that the whole input plus fits.
- The arm length L is 1 to 4, which are the lengths seen in the examples.
- The colour is fixed to 8 on background 0.
"""

import random

import common


def _cw(d):
  return (d[1], -d[0])


def _ccw(d):
  return (-d[1], d[0])


def _draw_spirals(out, height, width, cy, cx, length, color):
  """Draws the four arm spirals onto out in place."""
  lp = max(length, 2)
  lim = 2 * (height + width) + 10
  for d0 in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
    pos = [cy, cx]

    def walk(n, d):
      for _ in range(n):
        pos[0] += d[0]
        pos[1] += d[1]
        if 0 <= pos[0] < height and 0 <= pos[1] < width:
          out[pos[0]][pos[1]] = color

    d = d0
    walk(lp, d)
    k = 0
    while True:
      a = 4 * k + 2
      if a > lim:
        break
      d = _cw(d)
      walk(a, d)
      d = _cw(d)
      walk(lp - 2, d)
      d = _ccw(d)
      walk(lp, d)
      k += 1


def generate(height=None, width=None, cy=None, cx=None, length=None):
  """Generates one input/output pair.

  Args:
    height: number of grid rows (10..30). Sampled when None.
    width: number of grid columns (10..30). Sampled when None.
    cy: row of the empty centre of the plus. Sampled when None.
    cx: column of the empty centre of the plus. Sampled when None.
    length: arm length L of the plus (1..4). Sampled when None.

  Returns:
    A dict with keys "input" and "output", each a list of integer rows.
  """
  color = 8
  if length is None:
    length = random.randint(1, 4)
  if height is None and width is None:
    if random.random() < 0.5:
      height = width = random.randint(10, 30)
    else:
      height = random.randint(10, 30)
      width = random.randint(10, 30)
  elif height is None:
    height = random.randint(10, 30)
  elif width is None:
    width = random.randint(10, 30)
  if cy is None:
    cy = random.randint(length, height - 1 - length)
  if cx is None:
    cx = random.randint(length, width - 1 - length)

  grid = common.grid(width, height, 0)
  for d in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
    for i in range(1, length + 1):
      grid[cy + d[0] * i][cx + d[1] * i] = color
  out = [row[:] for row in grid]
  _draw_spirals(out, height, width, cy, cx, length, color)
  return {"input": grid, "output": out}


def validate():
  """Rebuilds the canonical fixtures from their latent parameters."""
  train = [
      generate(height=12, width=12, cy=4, cx=5, length=1),
      generate(height=22, width=22, cy=9, cx=9, length=3),
      generate(height=16, width=16, cy=7, cx=6, length=2),
  ]
  test = [
      generate(height=26, width=26, cy=12, cx=10, length=4),
  ]
  return {"train": train, "test": test}
