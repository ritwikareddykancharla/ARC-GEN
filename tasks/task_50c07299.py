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


def generate(row=None, length=None, height=None, width=None):
  """Returns input and output grids according to the given parameters.

  Args:
    row: Row of the line (offset of its lower-left cell along the diagonal).
    length: Length of the line.
    height: Height of the canvas (16 when row is given and height is not).
    width: Width of the canvas (16 when row is given and width is not).
  """

  if row is None:
    # The segment stays on the anti-diagonal through the bottom-left corner,
    # as in every fixture; only the canvas size is free. The diagonal has
    # min(height, width) cells and must hold the segment and its successor.
    if height is None: height = common.randint(5, 30)
    if width is None: width = common.randint(5, 30)
    cells = min(height, width)
    if cells < 3 or (length is not None and length * 2 + 1 > cells):
      raise ValueError("Canvas diagonal cannot hold the segment and its successor")
    if length is None: length = common.randint(1, (cells - 1) // 2)
    row = common.randint(0, cells - 1 - length * 2)
  else:
    if height is None: height = 16
    if width is None: width = 16
    if length is None or row < 0 or length < 1:
      raise ValueError("Explicit row needs a positive length")
    if row + 2 * length + 1 > min(height, width):
      raise ValueError("Segment and successor leave the canvas diagonal")

  grid, output = common.grids(width, height, 7)
  for i in range(length):
    grid[height - 1 - row - i][row + i] = 2
  for i in range(length + 1):
    output[height - 1 - row - i - length][row + i + length] = 2
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(row=1, length=2),
      generate(row=0, length=1),
      generate(row=3, length=3),
  ]
  test = [
      generate(row=6, length=4),
  ]
  return {"train": train, "test": test}
