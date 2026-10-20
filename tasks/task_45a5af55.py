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

"""Generator for ARC task 45a5af55: horizontal colour stripes to nested rings.

Rule: every input row is a single solid colour, so the input is a top-to-bottom
list of H colours.  The output is a square of side N = 2 * (H - 1) made of
concentric square rings; ring d (cells at Chebyshev distance d from the border)
takes the colour of input row d.  Ring H - 2 is the 2x2 centre.  The last input
row always repeats the colour of the row above it and is not used.  Input width
plays no role.

Scope: 2..15 rings (H in 3..16, output side 4..30), any width 1..30, runs of
same-coloured rings of varying length, repeated colours in non-adjacent runs,
at least two distinct colours.  Not supported: non-solid rows, H < 3, or
inputs whose last row differs from its predecessor.
"""

import random

import common


def _build_input(rings, width):
  """Solid rows: one row per ring plus a duplicate of the last ring colour."""
  rows = list(rings) + [rings[-1]]
  return [[c] * width for c in rows]


def _build_output(rings):
  """Square of side 2 * len(rings); ring d is coloured rings[d]."""
  n = 2 * len(rings)
  grid = common.grid(n, n, rings[0])
  for y in range(n):
    for x in range(n):
      d = min(y, x, n - 1 - y, n - 1 - x)
      grid[y][x] = rings[d]
  return grid


def _sample_rings(count):
  """Runs of same-coloured rings; adjacent runs differ in colour."""
  rings = []
  prev = None
  while len(rings) < count:
    remaining = count - len(rings)
    run = random.randint(1, min(5, remaining))
    choices = [c for c in range(10) if c != prev]
    colour = random.choice(choices)
    rings.extend([colour] * run)
    prev = colour
  return rings


def generate(width=None, rings=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the number of columns of the input grid (1..30).
    rings: list of ring colours from the outside inwards; the input has
      len(rings) + 1 rows (the last row duplicates rings[-1]) and the output
      has side 2 * len(rings).
  """
  if width is None:
    width = random.randint(3, 30)
  if rings is None:
    for _ in range(100):
      count = random.randint(2, 15)
      candidate = _sample_rings(count)
      if len(set(candidate)) >= 2:
        rings = candidate
        break
    if rings is None:
      rings = [random.randrange(10)] * 3 + [random.randrange(10)]
      if rings[0] == rings[-1]:
        rings[-1] = (rings[-1] + 1) % 10
  return {"input": _build_input(rings, width), "output": _build_output(rings)}


def validate():
  """Validates the generator against the original task fixtures."""
  train = [
      generate(width=14, rings=[8, 8, 2, 2, 2, 2, 2, 6, 8, 8, 1, 1, 2]),
      generate(width=12, rings=[2, 3, 2, 2, 3, 2, 1, 2, 2, 2, 2, 8]),
  ]
  test = [
      generate(width=11, rings=[3, 3, 8, 8, 8, 2, 8, 8, 3, 7, 7, 5, 8]),
  ]
  return {"train": train, "test": test}
