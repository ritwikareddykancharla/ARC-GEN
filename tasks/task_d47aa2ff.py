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

"""Generator.

Rule (unchanged): two equal panels side by side, separated by a full grey
column. The right panel repeats the left panel's dots except that some dots
have moved. The output is the left panel with each moved dot's old cell red (2)
and its new cell blue (1).

Native batch c7d4/d47a widens the sampled domain only:

* panel height 3..30 and width 3..14, sampled independently (was 10x10); the
  whole input is H x (2W + 1), so it stays within 30 columns;
* 1..6 dot colours (was 2..3), every one present;
* 2..max(2, HW // 9) dots (was 5..10), placed one at a time;
* 1..min(colours, dots - 1) movers (was 1..2).

Kept because the rule or its unique correspondence depends on them (see the
batch report): dot colours exclude 0, 1, 2 and 5, so markers and divider never
collide with dots; at most one mover per colour, so each red cell pairs with
exactly one blue cell; dots start at Chebyshev distance >= 2; no destination
lands on any dot's old cell or on another destination; every scene has at
least one mover and at least one stationary dot (so every demonstration shows
both markers and the kept dots); displacement stays within the legacy 5x5
window without the four corner jumps (no larger move is demonstrated).

Explicit ``rows/cols/colors/rdiffs/cdiffs`` keep the legacy 10x10 panels
unless ``height`` and ``width`` are given. Invalid explicit scenes raise
``ValueError`` (the legacy code returned ``None`` grids). Sampling retries are
bounded and raise ``RuntimeError``; there is no fallback.
"""

import common

MIN_H, MAX_H = 3, 30
MIN_W, MAX_W = 3, 14
DOT_COLORS = (3, 4, 6, 7, 8, 9)
OFFSETS = tuple((dr, dc) for dr in range(-2, 3) for dc in range(-2, 3)
                if (dr, dc) != (0, 0) and not (abs(dr) == 2 and abs(dc) == 2))
ATTEMPTS = 200


def _dimension(value, name, low, high):
  if value is None:
    return common.randint(low, high)
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{name} must be an int")
  if not low <= value <= high:
    raise ValueError(f"{name} must be in {low}..{high}")
  return value


def _sample(height, width):
  """One attempt at a scene; returns (rows, cols, colors, rdiffs, cdiffs) or None."""
  num_colors = common.randint(1, len(DOT_COLORS))
  low = max(num_colors, 2)
  high = max(low, height * width // 9)
  pixels = common.randint(low, high)
  # Sequential placement at Chebyshev distance >= 2.
  free = [(r, c) for r in range(height) for c in range(width)]
  spots = []
  for _ in range(pixels):
    if not free:
      return None
    r, c = common.choice(free)
    spots.append((r, c))
    free = [(fr, fc) for fr, fc in free if abs(fr - r) > 1 or abs(fc - c) > 1]
  subset = common.sample(list(DOT_COLORS), num_colors)
  colors = subset + common.choices(subset, pixels - num_colors)
  common.shuffle(colors)
  movers = common.randint(1, min(num_colors, pixels - 1))
  moved = []
  for color in common.sample(subset, movers):
    moved.append(common.choice([i for i in range(pixels) if colors[i] == color]))
  taken = set(spots)
  rdiffs, cdiffs = [0] * pixels, [0] * pixels
  for i in moved:
    r, c = spots[i]
    options = [(dr, dc) for dr, dc in OFFSETS
               if 0 <= r + dr < height and 0 <= c + dc < width
               and (r + dr, c + dc) not in taken]
    if not options:
      return None
    rdiffs[i], cdiffs[i] = common.choice(options)
    taken.add((r + rdiffs[i], c + cdiffs[i]))
  return ([r for r, _ in spots], [c for _, c in spots], colors, rdiffs, cdiffs)


def generate(rows=None, cols=None, colors=None, rdiffs=None, cdiffs=None,
             height=None, width=None):
  """Returns input and output grids according to the given parameters.

  Args:
    rows: The rows of the pixels.
    cols: The cols of the pixels.
    colors: The colors of the pixels.
    rdiffs: The differences of the rows.
    cdiffs: The differences of the cols.
    height: Panel height, 3..30 (random if omitted; 10 with explicit pixels).
    width: Panel width, 3..14 (random if omitted; 10 with explicit pixels).
  """

  def draw():
    # We want there to be lots of spacing between the pixels, at least initially
    if common.overlaps(rows, cols, [2] * len(rows), [2] * len(cols)):
      return None, None
    # We also want to make sure that only one of each color moves.
    colors_moved = [color for color, rdiff, cdiff in zip(colors, rdiffs, cdiffs) if rdiff != 0 or cdiff != 0]
    if len(colors_moved) != len(set(colors_moved)): return None, None
    # Now we can draw.
    grid, output = common.grid(2 * width + 1, height), common.grid(width, height)
    for row in range(height):
      grid[row][width] = 5
    for row, col, color, rdiff, cdiff in zip(rows, cols, colors, rdiffs, cdiffs):
      # First, check that we're in bounds.
      if row < 0 or row >= height or col < 0 or col >= width: return None, None
      if (row + rdiff < 0 or row + rdiff >= height or col + cdiff < 0 or
          col + cdiff >= width):
        return None, None
      # Second, check that we're not drawing over anything.
      if grid[row][col] != 0: return None, None
      if grid[row + rdiff][col + cdiff] != 0: return None, None
      if output[row][col] != 0: return None, None
      if output[row + rdiff][col + cdiff] != 0: return None, None
      # Third, draw the pixels.
      grid[row][col] = color
      grid[row + rdiff][col + cdiff + width + 1] = color
      if rdiff == 0 and cdiff == 0:
        output[row][col] = color
      else:
        output[row][col] = 2
        output[row + rdiff][col + cdiff] = 1
    return grid, output

  explicit = [rows, cols, colors, rdiffs, cdiffs]
  if all(v is None for v in explicit):
    height = _dimension(height, "height", MIN_H, MAX_H)
    width = _dimension(width, "width", MIN_W, MAX_W)
    for _ in range(ATTEMPTS):
      scene = _sample(height, width)
      if scene is not None:
        break
    else:
      raise RuntimeError(f"no scene within {ATTEMPTS} attempts at {height}x{width}")
    rows, cols, colors, rdiffs, cdiffs = scene
  else:
    if any(v is None for v in explicit):
      raise ValueError("give rows, cols, colors, rdiffs and cdiffs together")
    if (height is None) != (width is None):
      raise ValueError("give both height and width with explicit pixels")
    height = 10 if height is None else _dimension(height, "height", MIN_H, MAX_H)
    width = 10 if width is None else _dimension(width, "width", MIN_W, MAX_W)
    if len({len(v) for v in explicit}) != 1 or not rows:
      raise ValueError("explicit pixel lists must be non-empty and equally long")
    if any(isinstance(v, bool) or not isinstance(v, int)
           for seq in explicit for v in seq):
      raise ValueError("explicit pixel values must be ints")
    if any(color not in DOT_COLORS for color in colors):
      raise ValueError("dot colours must avoid 0, 1, 2 and 5")
    moving = [(dr, dc) != (0, 0) for dr, dc in zip(rdiffs, cdiffs)]
    if not any(moving) or all(moving):
      raise ValueError("need at least one moved and one stationary dot")
    if any(m and (dr, dc) not in OFFSETS
           for m, dr, dc in zip(moving, rdiffs, cdiffs)):
      raise ValueError("displacement outside the 5x5 window or a corner jump")

  grid, output = draw()
  if grid is None:
    raise ValueError("pixels overlap, collide, leave the panel or share a moved colour")
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(rows=[0, 1, 3, 3, 4, 5, 7, 8], cols=[3, 6, 1, 5, 7, 1, 3, 7],
               colors=[4, 8, 9, 8, 4, 4, 8, 9],
               rdiffs=[0, 0, 0, 0, 0, 0, 0, -1],
               cdiffs=[0, 0, 0, -1, 0, 0, 0, -1]),
      generate(rows=[1, 2, 2, 4, 5, 8, 8], cols=[8, 2, 5, 3, 6, 1, 7],
               colors=[6, 3, 3, 6, 3, 3, 6], rdiffs=[0, 0, 0, 0, 1, 0, 0],
               cdiffs=[0, 0, 0, 0, 0, 0, 0]),
      generate(rows=[1, 2, 3, 3, 4, 5, 8, 8], cols=[7, 3, 1, 9, 5, 3, 3, 7],
               colors=[8, 8, 3, 3, 3, 6, 8, 6],
               rdiffs=[0, 0, 0, 0, -1, 0, 0, -2],
               cdiffs=[0, 0, 0, 0, 1, 0, 0, 0]),
  ]
  test = [
      generate(rows=[0, 1, 2, 2, 4, 4, 6, 8, 8, 9],
               cols=[4, 1, 3, 7, 3, 6, 1, 4, 7, 1],
               colors=[4, 9, 4, 9, 9, 7, 4, 7, 4, 9],
               rdiffs=[1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
               cdiffs=[2, 0, 0, 0, 0, -1, 0, 0, 0, 0]),
  ]
  return {"train": train, "test": test}
