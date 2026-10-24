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


def generate(wides=None, talls=None, brows=None, bcols=None, styles=None,
             color=None, width=None, height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    wides: The widths of the boxes.
    talls: The heights of the boxes.
    brows: The rows of the boxes.
    bcols: The columns of the boxes.
    styles: 0 for a hollow box, 1 or 2 for a diagonal across a square.
    color: The color of the boxes.
    width: Canvas width; random scenes sample it independently in 6..30.
    height: Canvas height; random scenes sample it independently in 6..30.
  """

  def draw(require_square=True):
    grid, output = common.grids(width, height, 7)
    # First, draw the boxes.
    for wide, tall, brow, bcol, style in zip(wides, talls, brows, bcols, styles):
      if style == 0:
        common.hollow_rect(grid, wide, tall, brow, bcol, color)
        common.hollow_rect(output, wide, tall, brow, bcol, color)
      if style == 1:
        for i in range(wide):
          r, c = brow + i, bcol + i
          output[r][c] = grid[r][c] = color
      if style == 2:
        for i in range(wide):
          r, c = brow + i, bcol + wide - 1 - i
          output[r][c] = grid[r][c] = color
    # Second, check that each box has a "safe" outer border.
    for wide, tall, brow, bcol in zip(wides, talls, brows, bcols):
      for r in range(brow - 1, brow + tall + 1):
        for c in range(bcol - 1, bcol + wide + 1):
          if r in [brow - 1, brow + tall] or c in [bcol - 1, bcol + wide]:
            if common.get_pixel(grid, r, c) not in [-1, 7]: return None, None
    # Third, add the red boxes where appropriate.
    num_squares = 0
    for wide, tall, brow, bcol, style in zip(wides, talls, brows, bcols, styles):
      if wide != tall or style != 0: continue
      num_squares += 1
      coords = []
      coords += [(brow - 1, bcol)]
      coords += [(brow - 1, bcol + wide - 1)]
      coords += [(brow, bcol - 1)]
      coords += [(brow, bcol + wide)]
      coords += [(brow + tall - 1, bcol - 1)]
      coords += [(brow + tall - 1, bcol + wide)]
      coords += [(brow + tall, bcol)]
      coords += [(brow + tall, bcol + wide - 1)]
      for r, c in coords:
        if common.get_pixel(output, r, c) in [-1, 2]: return None, None
        output[r][c] = 2
    if num_squares == 0 and require_square: return None, None
    return grid, output

  def separate(i, j):
    # Bounding boxes are disjoint, or one box lies strictly inside the
    # interior of a hollow box (the original 8x8 frame holding a 2x2 block).
    # Other overlaps, such as two diagonals sharing a bounding box, would draw
    # a merged shape whose square-ness differs from the boxes' own.
    def inside(a, b):
      return (styles[b] == 0 and brows[b] < brows[a] and
              bcols[b] < bcols[a] and
              brows[a] + talls[a] < brows[b] + talls[b] and
              bcols[a] + wides[a] < bcols[b] + wides[b])
    disjoint = (brows[i] + talls[i] <= brows[j] or
                brows[j] + talls[j] <= brows[i] or
                bcols[i] + wides[i] <= bcols[j] or
                bcols[j] + wides[j] <= bcols[i])
    return disjoint or inside(i, j) or inside(j, i)

  def side(limit):
    # Short sides as in the original, or occasionally a long side; the
    # original 10-cell canvas uses 8 = limit, with limit = canvas side - 2.
    if common.randint(0, 4): return None
    return common.randint(min(5, limit), limit)

  if wides is None:
    width = common.randint(6, 30) if width is None else width
    height = common.randint(6, 30) if height is None else height
    if not (6 <= width <= 30 and 6 <= height <= 30):
      raise ValueError('Random dimensions must be 6..30')
    # Two to five boxes on the original 10x10 canvas; proportionally more on
    # larger canvases.
    max_boxes = max(2, min(12, width * height // 20))
    color = common.random_color(exclude=[2, 7])
    # Small canvases rarely admit a markable square (about 2% of 6x6 scenes),
    # so the bounded budget is generous; failure raises rather than simplifying.
    for _ in range(1000):
      num_boxes = common.randint(2, max_boxes)
      wides, talls, brows, bcols, styles = [], [], [], [], []
      for _ in range(num_boxes):
        for _ in range(50):
          wide = common.randint(1, 4)
          tall = common.randint(1 if wide > 2 else 2, 4)
          long_wide, long_tall = side(width - 2), side(height - 2)
          if long_wide and long_tall:
            # Both sides long gives the original's large square (8x8).
            wide = tall = common.randint(min(5, min(width, height) - 2),
                                         min(width, height) - 2)
          elif long_wide: wide = long_wide
          elif long_tall: tall = long_tall
          style = 0 if wide != tall else common.randint(0, 2)
          wides.append(wide); talls.append(tall); styles.append(style)
          brows.append(common.randint(0, height - tall))
          bcols.append(common.randint(0, width - wide))
          last = len(wides) - 1
          if (all(separate(last, j) for j in range(last)) and
              draw(require_square=False)[0]): break
          for values in (wides, talls, brows, bcols, styles): values.pop()
      grid, _ = draw()
      if grid and len(wides) == num_boxes: break
    else:
      raise RuntimeError('Cannot place the sampled boxes; retry')
  width = 10 if width is None else width
  height = 10 if height is None else height

  grid, output = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(wides=[4, 2, 2, 4], talls=[4, 2, 2, 2], brows=[1, 1, 7, 7], bcols=[1, 7, 1, 5], styles=[0, 2, 2, 0], color=6),
      generate(wides=[3, 1, 3], talls=[3, 3, 1], brows=[2, 2, 7], bcols=[2, 7, 2], styles=[0, 0, 0], color=6),
      generate(wides=[8, 2], talls=[8, 2], brows=[1, 4], bcols=[1, 4], styles=[0, 0], color=8),
  ]
  test = [
      generate(wides=[3, 2, 3, 2, 8], talls=[3, 2, 3, 2, 1], brows=[1, 1, 5, 6, 9], bcols=[1, 6, 5, 1, 1], styles=[0, 0, 0, 0, 0], color=6),
  ]
  return {"train": train, "test": test}
