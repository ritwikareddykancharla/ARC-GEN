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


def generate(rows=None, cols=None, width=None, height=None, wide=None,
             tall=None):
  """Returns input and output grids according to the given parameters.

  Args:
    rows: The rows of the boxes.
    cols: The columns of the boxes.
    width: Grid width; 10 for supplied boxes, otherwise random 5..30.
    height: Grid height; 10 for supplied boxes, otherwise random 5..30.
    wide: Box width; 2 for supplied boxes, otherwise random 1..3.
    tall: Box height; 2 for supplied boxes, otherwise random 1..3.
  """

  def lattice(extent, side):
    # Box starts along one axis: gaps of 1..3 cells, any margins.
    most = (extent + 1) // (side + 1)
    count = common.randint(1, min(most, 6))
    gaps = [common.randint(1, 3) for _ in range(count - 1)]
    while count * side + sum(gaps) > extent:
      gaps[gaps.index(max(gaps))] -= 1
    start = common.randint(0, extent - count * side - sum(gaps))
    starts = [start]
    for gap in gaps:
      starts.append(starts[-1] + side + gap)
    return starts

  if rows is None:
    width = common.randint(5, 30) if width is None else width
    height = common.randint(5, 30) if height is None else height
    if not (5 <= width <= 30 and 5 <= height <= 30):
      raise ValueError("Random dimensions must be 5..30")
    fixed_wide, fixed_tall = wide, tall
    for _ in range(1000):
      wide = common.choice([1, 2, 2, 3]) if fixed_wide is None else fixed_wide
      tall = common.choice([1, 2, 2, 3]) if fixed_tall is None else fixed_tall
      if wide > width or tall > height: continue
      rows, cols = lattice(height, tall), lattice(width, wide)
      boxes = len(rows) * len(cols) * wide * tall
      # Need a visible gap line, and black must remain the modal colour.
      if max(len(rows), len(cols)) > 1 and 2 * boxes < width * height: break
    else:
      raise ValueError("No lattice with a gap line fits this canvas")
  width = 10 if width is None else width
  height = 10 if height is None else height
  wide = 2 if wide is None else wide
  tall = 2 if tall is None else tall

  grid, output = common.grids(width, height)
  for row in rows:
    for col in cols:
      for r in range(tall):
        for c in range(wide):
          output[row + r][col + c] = grid[row + r][col + c] = 5
  for i in range(1, len(rows)):
    for row in range(rows[i - 1] + tall, rows[i]):
      for col in range(width):
        output[row][col] = 1
  for i in range(1, len(cols)):
    for col in range(cols[i - 1] + wide, cols[i]):
      for row in range(height):
        output[row][col] = 1
  for row in range(rows[0], rows[-1] + tall):
    for col in range(cols[0], cols[-1] + wide):
      output[row][col] = 5 if output[row][col] == 5 else 2
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(rows=[0, 3, 6], cols=[2, 6]),
      generate(rows=[0, 3, 6], cols=[0, 3, 6]),
      generate(rows=[0, 4, 8], cols=[1, 4, 7]),
  ]
  test = [
      generate(rows=[1, 4, 7], cols=[1, 5, 8]),
  ]
  return {"train": train, "test": test}
