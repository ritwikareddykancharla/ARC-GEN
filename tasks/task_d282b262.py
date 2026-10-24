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

# Worst measured acceptance is ~63% per scene (6x6); 1,000 proposals
# fail with probability < 1e-400 on any valid canvas.
PROPOSALS = 1000


def generate(sizes=None, brows=None, bcols=None, evens=None, odds=None,
             talls=None, width=None, height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    sizes: The widths of the boxes (and heights unless talls is given).
    brows: The rows of the boxes.
    bcols: The columns of the boxes.
    evens: The "even" colors.
    odds: The "odd" colors.
    talls: Optional box heights; random boxes are rectangles of side 1..5.
    width: Grid width; 15 for supplied boxes, otherwise random 6..30.
    height: Grid height; 15 for supplied boxes, otherwise random 6..30.
  """

  if sizes is None:
    width = common.randint(6, 30) if width is None else width
    height = common.randint(6, 30) if height is None else height
    if not (6 <= width <= 30 and 6 <= height <= 30):
      raise ValueError("Random dimensions must be 6..30")
    area = width * height
    for _ in range(PROPOSALS):
      num_boxes = common.randint(1, max(2, min(9, area // 30)))
      sizes = [common.randint(1, 5) for _ in range(num_boxes)]
      talls = [common.randint(1, 5) for _ in range(num_boxes)]
      if any(w * t == 1 for w, t in zip(sizes, talls)): continue
      sizes = [min(w, width - 1) for w in sizes]
      talls = [min(t, height - 1) for t in talls]
      for _ in range(100):
        brows = [common.randint(0, height - t) for t in talls]
        bcols = [common.randint(0, width - w) for w in sizes]
        # One empty cell around every box keeps boxes 8-separated.
        if not common.overlaps(brows, bcols, sizes, talls, 1): break
      else:
        continue
      if 2 * sum(w * t for w, t in zip(sizes, talls)) < area: break
    else:
      raise RuntimeError("No valid d282b262 scene within the proposal budget")
    evens, odds = [], []
    for _ in range(num_boxes):
      colors = common.random_colors(2)
      evens, odds = evens + [colors[0]], odds + [colors[1]]
  talls = sizes if talls is None else talls
  width = 15 if width is None else width
  height = 15 if height is None else height

  grid, output = common.grids(width, height)
  entries = []
  for wide, tall, brow, bcol, even, odd in zip(sizes, talls, brows, bcols,
                                               evens, odds):
    entries.append((bcol, wide, tall, brow, even, odd))
    for r in range(tall):
      for c in range(wide):
        grid[brow + r][bcol + c] = even if (r + c) % 2 == 0 else odd
  entries = sorted(entries, reverse=True)
  lengths = [0 for _ in range(height)]
  for entry in entries:
    _, wide, tall, brow, even, odd = entry
    max_length = 0
    for r in range(brow, brow + tall):
      max_length = max(max_length, lengths[r])
    for r in range(brow, brow + tall):
      lengths[r] = max_length + wide
    bcol = width - max_length - wide
    for r in range(tall):
      for c in range(wide):
        output[brow + r][bcol + c] = even if (r + c) % 2 == 0 else odd
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(sizes=[2, 2, 2, 2, 2], brows=[2, 3, 7, 8, 10], bcols=[2, 7, 5, 1, 9], evens=[1, 5, 6, 8, 2], odds=[2, 8, 4, 9, 1]),
      generate(sizes=[3, 3, 3, 3, 3], brows=[1, 5, 7, 9], bcols=[1, 3, 8, 1], evens=[8, 2, 1, 7], odds=[3, 1, 4, 6]),
      generate(sizes=[2, 3, 3, 2, 2], brows=[1, 2, 7, 9, 12], bcols=[2, 9, 5, 11, 2], evens=[9, 3, 6, 8, 2], odds=[2, 7, 8, 5, 5]),
  ]
  test = [
      generate(sizes=[3, 5, 2, 2, 3, 2], brows=[0, 2, 5, 9, 10, 13], bcols=[3, 7, 2, 1, 7, 2], evens=[6, 2, 2, 3, 8, 1], odds=[8, 5, 1, 5, 4, 7]),
  ]
  return {"train": train, "test": test}
