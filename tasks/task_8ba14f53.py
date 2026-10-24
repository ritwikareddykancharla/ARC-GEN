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


MIN_HEIGHT, MIN_WIDTH, MAX_SIZE = 3, 6, 30
MAX_ATTEMPTS = 1000
# Hole (interior) rectangles whose area fits one box's share of the 3x3
# output; capacity overflow of the pair is still rejected by draw().
INTERIORS = [(h, w) for h in range(1, 7) for w in range(1, 7) if h * w <= 6]


def generate(rows=None, cols=None, groups=None, colors=None, height=None,
             width=None):
  """Returns input and output grids according to the given parameters.

  Args:
    rows: The rows of the pixels.
    cols: The columns of the pixels.
    groups: The groups of the pixels.
    colors: The colors of the groups.
    height: canvas rows (3..30); explicit scenes default to the legacy 4.
    width: canvas columns (6..30); explicit scenes default to the legacy 9.

  Two hollow boxes in distinct colours occupy disjoint column ranges (group 0
  on the left). The output lists each box's hole count as a run of its colour
  in a 3x3 grid, left box first, each box starting a new row. The canvas
  size, margins, gap, vertical offsets and hole rectangle are incidental;
  the 3x3 output capacity, two boxes and left-first order are kept.
  """
  for name, value, low in (("height", height, MIN_HEIGHT),
                           ("width", width, MIN_WIDTH)):
    if value is not None and (type(value) is not int
                              or not low <= value <= MAX_SIZE):
      raise ValueError(f"{name} must be an int in {low}..{MAX_SIZE}")

  def draw(tall, wide):
    grid, output = common.grid(wide, tall), common.grid(3, 3)
    # First, draw the borders.
    for row, col, group in zip(rows, cols, groups):
      for r in [-1, 0, 1]:
        for c in [-1, 0, 1]:
          grid[row + r][col + c] = colors[group]
    # Seond, clear out the black pixels.
    for row, col in zip(rows, cols):
      grid[row][col] = 0
    # Third, draw the output.
    row, col = 0, 0
    for group in [0, 1]:
      num_pixels = groups.count(group)
      for _ in range(num_pixels):
        if col == 3: row, col = row + 1, 0
        if row >= 3: return None, None
        output[row][col] = colors[group]
        col += 1
      row, col = row + 1, 0
    return grid, output

  if rows is None:
    if cols is not None or groups is not None or colors is not None:
      raise ValueError("rows, cols, groups and colors are given together")
    colors = common.random_colors(2)
    for _ in range(MAX_ATTEMPTS):
      tall = height if height is not None else common.randint(MIN_HEIGHT, MAX_SIZE)
      wide = width if width is not None else common.randint(MIN_WIDTH, MAX_SIZE)
      left = [s for s in INTERIORS if s[0] + 2 <= tall and s[1] + 5 <= wide]
      if not left: continue
      first = common.choice(left)
      right = [s for s in INTERIORS
               if s[0] + 2 <= tall and first[1] + s[1] + 4 <= wide]
      second = common.choice(right)
      shapes = [first, second]
      slack = wide - first[1] - second[1] - 4
      cuts = sorted(common.randint(0, slack) for _ in range(2))
      margins = [cuts[0], cuts[1] - cuts[0]]   # left margin, gap
      col, rows, cols, groups = 0, [], [], []
      for group, (ih, iw) in enumerate(shapes):
        col += margins[group]
        row = common.randint(0, tall - ih - 2)
        notch_row, notch_col, notch_dir = -1, -1, 0
        if ih > 1 and iw > 1:
          notch_row = common.randint(0, ih - 1)
          notch_col = common.randint(0, iw - 1)
          notch_dir = 2 * common.randint(0, 1) - 1
        for r in range(ih):
          for c in range(iw):
            if r == notch_row:
              if notch_dir == -1 and c < notch_col: continue
              if notch_dir == +1 and c > notch_col: continue
            rows.append(row + 1 + r)
            cols.append(col + 1 + c)
            groups.append(group)
        col += iw + 2
      grid, _ = draw(tall, wide)
      if grid: break
    else:
      raise RuntimeError("no two-box scene fits the 3x3 output")
  else:
    tall = 4 if height is None else height
    wide = 9 if width is None else width
    if (cols is None or groups is None or colors is None
        or not len(rows) == len(cols) == len(groups)
        or set(groups) != {0, 1} or len(colors) != 2
        or len(set(colors)) != 2
        or any(type(c) is not int or not 1 <= c <= 9 for c in colors)):
      raise ValueError("explicit scenes need two distinct colours and both groups")
    if any(not (1 <= r <= tall - 2 and 1 <= c <= wide - 2)
           for r, c in zip(rows, cols)):
      raise ValueError("a hole cell's border falls outside the canvas")
    if (max(c for c, g in zip(cols, groups) if g == 0) + 1
        >= min(c for c, g in zip(cols, groups) if g == 1) - 1):
      raise ValueError("group 0 must lie strictly left of group 1")

  grid, output = draw(tall, wide)
  if grid is None:
    raise ValueError("hole counts overflow the 3x3 output")
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(rows=[1, 1, 1, 2, 2, 2], cols=[1, 2, 6, 1, 2, 6],
               groups=[0, 0, 1, 0, 0, 1], colors=[3, 1]),
      generate(rows=[1, 2, 2, 2, 2], cols=[1, 1, 2, 6, 7],
               groups=[0, 0, 0, 1, 1], colors=[7, 8]),
      generate(rows=[1, 1, 1, 1, 2, 2], cols=[1, 2, 6, 7, 2, 6],
               groups=[0, 0, 1, 1, 0, 1], colors=[9, 5]),
      generate(rows=[1, 1], cols=[1, 5], groups=[0, 1], colors=[8, 6]),
      generate(rows=[1, 1, 1, 1, 2, 2, 2], cols=[2, 5, 6, 7, 5, 6, 7],
               groups=[0, 1, 1, 1, 1, 1, 1], colors=[4, 6]),
      generate(rows=[1, 1, 2, 2, 2], cols=[1, 5, 1, 5, 6],
               groups=[0, 1, 0, 1, 1], colors=[7, 8]),
  ]
  test = [
      generate(rows=[1, 1, 2, 2, 2], cols=[1, 7, 1, 2, 3],
               groups=[0, 1, 0, 0, 0], colors=[4, 7]),
  ]
  return {"train": train, "test": test}
