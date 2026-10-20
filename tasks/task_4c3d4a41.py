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

"""ARC task 4c3d4a41: slide the grey comb into the frame and rest stacks on it.

Rule: a grey (5) comb on the left has a base row and vertical teeth on every
other column. A large grey frame on the right, open on its left side next to
the comb's base, contains coloured columns aligned with the teeth spacing.
Each column has an optional grey head attached to the frame ceiling followed by
a stack of one colour. In the output the comb is erased from the left and
re-stamped inside the frame (same rows) so its teeth sit under the coloured
columns. Above each tooth, the column's colour is stacked directly on the
tooth, truncated to the available space (frame ceiling+1 .. tooth top-1), and
any unused space above it is filled with grey.

Scope: the number of teeth/columns K (3..6) and the comb base row B (4..8) are
sampled, giving grids of (B+3) x (4K+4). Tooth heights, grey head lengths,
stack lengths and distinct stack colours are random, so both truncation and
grey padding occur. Background 0 and grey 5 are fixed. The frame always sits
at the top-right, with the comb at the left starting at column 1, as in ARC.
"""

import random

import common


def generate(num_teeth=None, base_row=None, tooth_tops=None, columns=None):
  """Generates an input/output pair.

  Args:
    num_teeth: number of comb teeth (= number of coloured columns), K.
    base_row: row of the comb base B; grid height is B + 3.
    tooth_tops: list of K row indices where each tooth starts (2..B-1).
    columns: list of K tuples (grey_head, colour, count) describing each
      coloured column inside the frame, from row 1 downward.
  """
  if num_teeth is None:
    num_teeth = len(tooth_tops) if tooth_tops else random.randint(3, 6)
  k = num_teeth
  if base_row is None:
    base_row = random.randint(4, 8)
  b = base_row
  if tooth_tops is None:
    tooth_tops = [random.randint(2, b - 1) for _ in range(k)]
  if columns is None:
    colours = random.sample([1, 2, 3, 4, 6, 7, 8, 9], k)
    columns = []
    for c in colours:
      n = random.randint(1, b - 1)
      g = random.randint(0, b - 1 - n)
      columns.append((g, c, n))
  height, width = b + 3, 4 * k + 4
  fl, fr = 2 * k + 1, 4 * k + 3
  grid = common.grid(width, height, 0)
  # Frame.
  for x in range(fl, fr + 1):
    grid[0][x] = 5
    grid[height - 1][x] = 5
  for y in range(height):
    grid[y][fr] = 5
    if y not in (b - 1, b):
      grid[y][fl] = 5
  output = [row[:] for row in grid]
  # Input comb on the left and coloured columns inside the frame.
  for x in range(1, 2 * k):
    grid[b][x] = 5
  for i in range(k):
    for y in range(tooth_tops[i], b + 1):
      grid[y][1 + 2 * i] = 5
    g, c, n = columns[i]
    x = fl + 2 + 2 * i
    for y in range(1, 1 + g):
      grid[y][x] = 5
    for y in range(1 + g, 1 + g + n):
      grid[y][x] = c
  # Output: comb shifted into the frame with stacks resting on teeth.
  for x in range(fl + 2, fl + 2 * k + 1):
    output[b][x] = 5
  for i in range(k):
    x = fl + 2 + 2 * i
    t = tooth_tops[i]
    for y in range(t, b + 1):
      output[y][x] = 5
    _, c, n = columns[i]
    space = t - 1
    keep = min(n, space)
    for j in range(space):
      output[t - 1 - j][x] = c if j < keep else 5
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical ARC pairs from explicit latent parameters."""
  train = [
      generate(num_teeth=4, base_row=5, tooth_tops=[2, 3, 4, 2],
               columns=[(0, 3, 3), (0, 2, 4), (1, 4, 3), (1, 7, 2)]),
      generate(num_teeth=4, base_row=5, tooth_tops=[3, 4, 4, 2],
               columns=[(1, 4, 2), (2, 6, 2), (2, 7, 2), (1, 8, 2)]),
  ]
  test = [
      generate(num_teeth=4, base_row=5, tooth_tops=[3, 2, 2, 4],
               columns=[(2, 9, 1), (2, 6, 2), (2, 3, 2), (0, 8, 3)]),
      generate(num_teeth=4, base_row=5, tooth_tops=[4, 4, 4, 4],
               columns=[(0, 3, 3), (0, 2, 4), (1, 4, 3), (1, 7, 2)]),
  ]
  return {"train": train, "test": test}
