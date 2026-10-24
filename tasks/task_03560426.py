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


def _composition(total, parts, low, high):
  """A random composition of total into parts values, each in low..high."""
  values = []
  for i in range(parts):
    rest = parts - i - 1
    value = common.randint(max(low, total - high * rest),
                           min(high, total - low * rest))
    values.append(value)
    total -= value
  return common.shuffle(values)


def _fixed_width_boxes(width, height):
  """Box widths 1..5 and heights 2..8 that exactly span width and chain.

  With n boxes and one optional trailing blank column, the widths sum to
  width - (n - 1) - blank, which must lie in n..5n. The output chain needs
  sum(heights) - (n - 1) <= height, so heights total 2n..min(8n, height+n-1).
  Every feasible (n, blank) pair and total is reachable.
  """
  options = {}
  for n in range(3, min(8, height - 1) + 1):
    blanks = [b for b in (0, 1) if n <= width - (n - 1) - b <= 5 * n]
    if blanks: options[n] = blanks
  if not options:
    raise ValueError('No box chain fits a %dx%d canvas' % (height, width))
  n = common.choice(sorted(options))
  blank = common.choice(options[n])
  widths = _composition(width - (n - 1) - blank, n, 1, 5)
  heights = _composition(common.randint(2 * n, min(8 * n, height + n - 1)),
                         n, 2, 8)
  return widths, heights


def generate(widths=None, heights=None, colors=None, width=None, height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    widths: The widths of the boxes.
    heights: The heights of the boxes.
    colors: The colors of the boxes.
    width: Canvas width (10 for the original pairs); random scenes take the
      width spanned by the boxes, which is at most 30.
    height: Canvas height (10 for the original pairs); random 6..30.
  """

  def draw():
    grid, output = common.grids(width, height)
    grid_col, output_row, output_col = 0, 0, 0
    for box_width, box_height, color in zip(widths, heights, colors):
      for r in range(box_height):
        for c in range(box_width):
          if grid_col + c >= width: return None, None
          if output_row + r >= height: return None, None
          grid[height - 1 - r][grid_col + c] = color
          output[output_row + r][output_col + c] = color
      grid_col += box_width + 1
      output_col += box_width - 1
      output_row += box_height - 1
    # As in the original pairs, the row of boxes starts at the left edge and
    # ends at the right edge or one blank column before it.
    if grid_col not in [width, width + 1]: return None, None
    return grid, output

  if widths is None:
    fixed_width, fixed_height = width, height
    if fixed_height is not None and not 6 <= fixed_height <= 30:
      raise ValueError('Random height must be 6..30')
    if fixed_width is not None and not 5 <= fixed_width <= 30:
      raise ValueError('Random width must be 5..30')
    if fixed_width is not None:
      # A fixed width is built directly from feasible compositions rather
      # than by rejection, which almost never finds short, wide scenes.
      height = common.randint(6, 30) if fixed_height is None else fixed_height
      widths, heights = _fixed_width_boxes(fixed_width, height)
      width = fixed_width
      colors = common.random_colors(len(widths))
      grid, _ = draw()
      if not grid: raise RuntimeError('Composition failed to chain; retry')
    else:
      # Caps below only prune values that cannot fit: the diagonal output
      # chain needs heights of at least 2 that overlap by one row, i.e.
      # sum(heights) - (n - 1) <= height.
      for _ in range(1000):
        height = common.randint(6, 30) if fixed_height is None else fixed_height
        num_boxes = common.randint(3, min(8, height - 1))
        widths = [common.randint(1, 5) for _ in range(num_boxes)]
        span = sum(widths) + num_boxes - 1
        width = span + common.randint(0, 1)
        if width > 30: continue
        max_height = min(8, height - 2, height - num_boxes + 1)
        heights = [common.randint(2, max_height) for _ in range(num_boxes)]
        colors = common.random_colors(num_boxes)
        grid, _ = draw()
        if grid: break
      else:
        raise RuntimeError('Cannot chain the sampled boxes; retry')
  width = 10 if width is None else width
  height = 10 if height is None else height

  grid, output = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(widths=[3, 2, 3], heights=[4, 2, 2], colors=[8, 7, 2]),
      generate(widths=[2, 2, 2, 1], heights=[3, 2, 2, 4], colors=[1, 2, 3, 4]),
      generate(widths=[4, 1, 3], heights=[2, 5, 3], colors=[4, 2, 3]),
  ]
  test = [
      generate(widths=[1, 2, 1, 2], heights=[4, 3, 3, 2], colors=[7, 8, 6, 3]),
  ]
  return {"train": train, "test": test}
