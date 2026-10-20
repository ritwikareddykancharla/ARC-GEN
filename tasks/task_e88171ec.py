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


def _unique_largest_zero_rectangle(grid, expected):
  """Check all >=3-sided zero rectangles, including incidental background holes.

  Row-span intersections give maximal zero runs. A smaller subrectangle cannot
  tie or beat the expected area unless its enclosing maximal run does too.
  """
  top, bottom, left, right = expected
  target_area = (bottom - top + 1) * (right - left + 1)
  found = False
  width = len(grid[0])
  for y0 in range(len(grid)):
    empty = [True] * width
    for y1 in range(y0, len(grid)):
      empty = [ok and ink == 0 for ok, ink in zip(empty, grid[y1])]
      height = y1 - y0 + 1
      if height < 3:
        continue
      start = None
      for x, ok in enumerate(empty + [False]):
        if ok and start is None:
          start = x
        elif not ok and start is not None:
          span = x - start
          if span >= 3 and height * span >= target_area:
            if (y0, y1, start, x - 1) != expected:
              return False
            found = True
          start = None
  return found


def generate(size=None, wide=None, tall=None, brow=None, bcol=None,
             colors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    size: The size of the grid.
    wide: The width of the box.
    tall: The height of the box.
    brow: The row of the box.
    bcol: The column of the box.
    colors: The colors of the background.
  """

  if size is None:
    size = common.randint(12, 24)
    color = common.random_color(exclude=[5, 8])
    wide, tall = common.randint(2, 4), common.randint(2, 4)
    brow = common.randint(3, size - tall - 3)
    bcol = common.randint(3, size - wide - 3)
    for _ in range(128):
      colors = [color if common.randint(0, 5) else 0 for _ in range(size * size)]
      if common.randint(0, 3) == 0:  # Sometimes sprinkle with grey pixels
        colors = [c if common.randint(0, 9) else 5 for c in colors]
      # Now, add extra pixels on all sides just to be safe.
      row, col = common.randint(brow, brow + tall - 1), bcol - 2
      colors[row * size + col] = color
      row, col = common.randint(brow, brow + tall - 1), bcol + wide + 1
      colors[row * size + col] = color
      row, col = brow - 2, common.randint(bcol, bcol + wide - 1)
      colors[row * size + col] = color
      row, col = brow + tall + 1, common.randint(bcol, bcol + wide - 1)
      colors[row * size + col] = color
      pair = generate(size=size, wide=wide, tall=tall, brow=brow,
                      bcol=bcol, colors=colors)
      box = (brow - 1, brow + tall, bcol - 1, bcol + wide)
      if _unique_largest_zero_rectangle(pair["input"], box):
        return pair
    raise RuntimeError("Could not sample an unambiguous zero rectangle")

  grid, output = common.grids(size, size)
  for i, color in enumerate(colors):
    output[i // size][i % size] = grid[i // size][i % size] = color
  common.rect(grid, wide + 2, tall + 2, brow - 1, bcol - 1, 0)
  common.rect(output, wide + 2, tall + 2, brow - 1, bcol - 1, 0)
  common.rect(output, wide, tall, brow, bcol, 8)
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(size=15, wide=2, tall=2, brow=4, bcol=6,
               colors=[0, 0, 2, 2, 2, 0, 2, 2, 0, 0, 0, 0, 2, 2, 2,
                       2, 2, 2, 2, 0, 2, 2, 2, 2, 0, 0, 2, 0, 2, 2,
                       2, 2, 0, 0, 2, 0, 2, 0, 2, 0, 2, 0, 2, 2, 0,
                       2, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 2, 2, 0, 2,
                       2, 0, 2, 2, 0, 0, 0, 0, 0, 2, 0, 0, 0, 2, 2,
                       0, 2, 0, 2, 2, 0, 0, 0, 0, 0, 2, 2, 0, 2, 0,
                       2, 0, 0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 2, 2, 2,
                       0, 0, 2, 2, 0, 0, 0, 2, 2, 2, 0, 2, 0, 2, 2,
                       2, 2, 2, 2, 0, 2, 2, 2, 0, 0, 2, 0, 0, 2, 2,
                       0, 0, 0, 2, 2, 2, 2, 0, 2, 0, 2, 2, 2, 2, 2,
                       2, 2, 0, 2, 2, 2, 2, 0, 0, 2, 2, 0, 0, 2, 0,
                       2, 2, 2, 0, 2, 2, 0, 0, 0, 0, 0, 0, 2, 2, 0,
                       2, 0, 2, 2, 2, 0, 0, 2, 0, 0, 2, 2, 2, 2, 2,
                       0, 2, 2, 2, 2, 0, 0, 0, 2, 2, 2, 2, 2, 2, 0,
                       0, 2, 0, 2, 0, 2, 2, 2, 2, 2, 0, 2, 2, 2, 0]),
      generate(size=19, wide=3, tall=4, brow=5, bcol=5,
               colors=[4, 0, 0, 4, 0, 0, 0, 4, 0, 0, 5, 0, 0, 0, 0, 4, 4, 4, 4,
                       0, 4, 4, 4, 4, 5, 4, 4, 0, 0, 0, 4, 4, 4, 0, 4, 0, 4, 0,
                       0, 0, 4, 4, 4, 0, 4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 4, 0, 4,
                       0, 4, 0, 4, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 5, 0, 5, 4, 4,
                       4, 0, 4, 4, 0, 0, 0, 0, 0, 4, 4, 0, 4, 0, 4, 0, 4, 0, 4,
                       4, 4, 4, 0, 0, 0, 0, 0, 0, 4, 0, 0, 4, 0, 0, 4, 4, 0, 4,
                       4, 4, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 0, 0, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 0, 0, 0, 0, 0, 4, 4, 4, 4, 5, 4, 4, 0, 5, 4,
                       4, 4, 4, 0, 0, 0, 0, 0, 0, 4, 5, 4, 4, 4, 0, 4, 0, 0, 5,
                       0, 4, 4, 4, 0, 0, 0, 0, 0, 4, 4, 0, 4, 4, 5, 4, 0, 0, 4,
                       4, 4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 0, 4, 0, 4, 0, 4, 4, 5,
                       4, 4, 4, 4, 4, 4, 4, 0, 4, 4, 5, 5, 4, 0, 4, 0, 4, 4, 5,
                       4, 4, 4, 4, 4, 5, 0, 4, 0, 4, 0, 4, 4, 0, 4, 0, 5, 4, 4,
                       5, 4, 4, 0, 4, 4, 0, 0, 4, 4, 4, 4, 4, 4, 4, 0, 4, 4, 4,
                       4, 0, 4, 0, 4, 0, 4, 4, 4, 4, 4, 4, 0, 4, 0, 4, 0, 4, 4,
                       5, 4, 4, 4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 0, 0, 4, 4, 4, 0,
                       0, 0, 4, 4, 0, 4, 4, 4, 0, 0, 4, 0, 4, 0, 0, 0, 0, 4, 4,
                       4, 0, 0, 4, 4, 5, 4, 5, 4, 5, 4, 0, 4, 4, 0, 4, 4, 5, 0,
                       4, 0, 0, 4, 4, 0, 0, 0, 5, 4, 4, 0, 0, 4, 4, 5, 4, 4, 0]),
      generate(size=16, wide=4, tall=2, brow=11, bcol=8,
               colors=[0, 0, 3, 0, 3, 3, 3, 0, 0, 0, 0, 0, 3, 3, 3, 0,
                       0, 0, 3, 0, 0, 3, 0, 3, 0, 0, 0, 3, 3, 0, 3, 3,
                       0, 3, 0, 3, 0, 3, 3, 3, 3, 3, 0, 3, 3, 3, 0, 0,
                       3, 3, 3, 3, 3, 0, 3, 0, 3, 3, 3, 3, 0, 3, 3, 3,
                       3, 3, 0, 3, 0, 0, 3, 0, 0, 3, 3, 3, 0, 0, 3, 3,
                       0, 0, 3, 3, 0, 0, 3, 3, 3, 3, 3, 0, 0, 3, 3, 0,
                       3, 0, 3, 3, 3, 0, 0, 0, 0, 3, 0, 3, 3, 3, 3, 3,
                       0, 0, 0, 0, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 0,
                       3, 3, 3, 0, 3, 3, 0, 3, 0, 3, 0, 3, 3, 3, 3, 0,
                       3, 0, 0, 3, 0, 0, 0, 0, 3, 3, 3, 3, 0, 3, 3, 3,
                       0, 0, 0, 3, 0, 3, 3, 0, 0, 0, 0, 0, 0, 3, 0, 0,
                       0, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3,
                       3, 0, 0, 0, 3, 0, 3, 0, 0, 0, 0, 0, 0, 3, 3, 3,
                       0, 0, 0, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 3,
                       3, 3, 3, 3, 3, 3, 0, 0, 0, 3, 3, 3, 3, 0, 3, 0,
                       0, 0, 0, 3, 3, 0, 0, 3, 3, 0, 3, 3, 0, 0, 3, 3]),
  ]
  test = [
      generate(size=21, wide=4, tall=3, brow=13, bcol=11,
               colors=[7, 7, 0, 0, 0, 7, 7, 7, 0, 0, 0, 7, 0, 0, 7, 7, 0, 7, 0, 7, 7,
                       7, 0, 7, 7, 7, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 0, 0, 7, 7, 0, 0,
                       7, 7, 7, 7, 7, 0, 7, 0, 0, 7, 7, 7, 7, 7, 0, 0, 7, 7, 7, 7, 0,
                       7, 0, 0, 7, 0, 7, 7, 7, 0, 0, 7, 0, 0, 0, 0, 7, 0, 0, 7, 7, 0,
                       7, 7, 7, 7, 0, 7, 7, 0, 7, 0, 7, 7, 7, 7, 0, 7, 7, 7, 7, 7, 7,
                       7, 7, 0, 7, 7, 7, 7, 0, 7, 7, 7, 7, 7, 0, 7, 7, 7, 7, 7, 7, 7,
                       0, 7, 7, 7, 0, 0, 7, 7, 7, 7, 0, 0, 7, 0, 0, 7, 7, 7, 7, 7, 7,
                       7, 0, 0, 7, 0, 0, 7, 7, 7, 7, 0, 7, 0, 7, 7, 7, 7, 0, 7, 7, 7,
                       7, 7, 7, 0, 7, 0, 7, 7, 7, 0, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 7,
                       7, 7, 7, 0, 7, 7, 7, 7, 0, 7, 0, 7, 7, 7, 7, 7, 0, 7, 7, 7, 7,
                       0, 7, 7, 0, 7, 0, 7, 0, 0, 7, 7, 7, 7, 7, 0, 7, 0, 0, 0, 7, 7,
                       7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 7, 0, 7, 7, 7, 7, 7, 7, 0, 0, 0,
                       7, 7, 0, 0, 0, 7, 7, 0, 7, 7, 0, 0, 0, 0, 0, 0, 0, 7, 0, 7, 7,
                       0, 7, 7, 0, 0, 7, 0, 0, 7, 7, 0, 0, 0, 0, 0, 0, 7, 7, 0, 0, 7,
                       7, 7, 7, 0, 7, 7, 0, 7, 7, 7, 0, 0, 0, 0, 0, 0, 0, 7, 0, 7, 0,
                       7, 0, 7, 7, 0, 7, 0, 7, 0, 7, 0, 0, 0, 0, 0, 0, 7, 7, 7, 0, 0,
                       7, 7, 7, 7, 7, 7, 0, 0, 7, 7, 0, 0, 0, 0, 0, 0, 7, 7, 0, 7, 7,
                       0, 0, 7, 7, 0, 7, 0, 0, 7, 7, 0, 0, 0, 7, 7, 0, 0, 7, 0, 0, 7,
                       7, 0, 7, 7, 7, 7, 0, 7, 7, 7, 7, 7, 7, 0, 7, 0, 0, 0, 0, 0, 0,
                       0, 7, 7, 0, 0, 7, 7, 0, 7, 0, 0, 0, 0, 7, 0, 7, 7, 7, 7, 7, 7,
                       0, 7, 7, 0, 7, 7, 7, 0, 0, 7, 7, 0, 0, 7, 7, 0, 7, 7, 0, 7, 7]),
  ]
  return {"train": train, "test": test}
