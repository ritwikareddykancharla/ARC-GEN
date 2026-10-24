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

Rule (unchanged): column 0 holds a colour legend made of contiguous runs of
distinct non-grey colours. Every non-black cell takes the legend colour of its
own row; the legend maps to itself.

Native batch c7d4/d47a widens the sampled domain only:

* canvas height 3..30 and width 3..30, sampled independently (was 10x10);
* legend height 2..H (was 7..8) at any vertical offset, including touching the
  top or bottom edge (was always one blank row above and below);
* 2..8 legend colours (was 2..4) with run lengths >= 1 (was 1..4);
* grey bounding box starting at any column >= 2 with any width that fits (was
  start column 3, width 3..5).

Kept because the rule or the demonstration evidence depends on them (see the
batch report): the legend is column 0 and contiguous; colours are distinct per
run and exclude grey; at least two legend colours (so every demonstration
refutes whole-shape recolouring); the grey shape is one 4-connected component;
its rows are exactly the legend rows (no grey cell has an undefined key, and
every legend row is used, so band-alignment readings coincide with the rule);
at least one blank column separates legend and shape; black stays the strict
modal colour.

Explicit ``colors`` keep the legacy 10x10 canvas unless ``height`` and
``width`` are given; explicit scenes outside the domain raise ``ValueError``.
Sampling retries are bounded and raise ``RuntimeError``; there is no fallback.
"""

import common

MIN_DIM, MAX_DIM = 3, 30
LEGEND_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
GREY = 5
ATTEMPTS = 200


def _dimension(value, name):
  if value is None:
    return common.randint(MIN_DIM, MAX_DIM)
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{name} must be an int")
  if not MIN_DIM <= value <= MAX_DIM:
    raise ValueError(f"{name} must be in {MIN_DIM}..{MAX_DIM}")
  return value


def _connected(cells):
  cells = set(cells)
  if not cells:
    return False
  stack = [next(iter(cells))]
  seen = {stack[0]}
  while stack:
    r, c = stack.pop()
    for p in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
      if p in cells and p not in seen:
        seen.add(p)
        stack.append(p)
  return len(seen) == len(cells)


def _black_is_modal(grid):
  counts = {}
  for row in grid:
    for color in row:
      counts[color] = counts.get(color, 0) + 1
  black = counts.get(0, 0)
  return all(black > n for color, n in counts.items() if color != 0)


def check_scene(grid):
  """Raises ValueError unless ``grid`` is in the documented input domain."""
  height, width = len(grid), len(grid[0])
  if not (MIN_DIM <= height <= MAX_DIM and MIN_DIM <= width <= MAX_DIM):
    raise ValueError("canvas outside 3..30")
  legend = [r for r in range(height) if grid[r][0]]
  if len(legend) < 2 or legend != list(range(legend[0], legend[-1] + 1)):
    raise ValueError("legend must be one contiguous run of >= 2 rows")
  runs = []
  for r in legend:
    color = grid[r][0]
    if color not in LEGEND_COLORS:
      raise ValueError("legend colours must be non-grey and non-black")
    if not runs or runs[-1] != color:
      runs.append(color)
  if len(runs) != len(set(runs)) or len(runs) < 2:
    raise ValueError("legend needs >= 2 runs of distinct colours")
  grey = []
  for r in range(height):
    for c in range(1, width):
      if grid[r][c] == 0:
        continue
      if grid[r][c] != GREY or c == 1:
        raise ValueError("off-legend cells must be grey, from column 2")
      grey.append((r, c))
  if sorted({r for r, _ in grey}) != legend:
    raise ValueError("grey rows must be exactly the legend rows")
  if not _connected(grey):
    raise ValueError("grey shape must be one 4-connected component")
  if not _black_is_modal(grid):
    raise ValueError("black must be the strict modal colour")


def _sample(height, width):
  """One attempt at a scene; returns the grid or None."""
  legend_height = common.randint(2, height)
  num_colors = common.randint(2, min(len(LEGEND_COLORS), legend_height))
  subset = common.sample(list(LEGEND_COLORS), num_colors)
  cuts = sorted(common.sample(list(range(1, legend_height)), num_colors - 1))
  segments = [b - a for a, b in zip([0] + cuts, cuts + [legend_height])]
  top = common.randint(0, height - legend_height)
  grid = common.grid(width, height)
  row = top
  for color, segment in zip(subset, segments):
    for _ in range(segment):
      grid[row][0] = color
      row += 1
  box = common.randint(1, width - 2)
  left = common.randint(2, width - box)
  grey, covered = set(), set()
  # Random horizontal and vertical runs inside the box, as in the legacy
  # constructor, until every legend row holds grey and the grey is connected.
  for _ in range(8 * (legend_height + box) + 32):
    if common.randint(0, 1):
      length = common.randint(min(2, box), box)
      pos = common.randint(0, box - length)
      r = common.randint(0, legend_height - 1)
      new = {(top + r, left + c) for c in range(pos, pos + length)}
    else:
      length = common.randint(2, legend_height)
      pos = common.randint(0, legend_height - length)
      c = common.randint(0, box - 1)
      new = {(top + r, left + c) for r in range(pos, pos + length)}
    grey |= new
    covered |= {r for r, _ in new}
    if len(covered) == legend_height and _connected(grey):
      for r, c in grey:
        grid[r][c] = GREY
      return grid if _black_is_modal(grid) else None
  return None


def generate(colors=None, height=None, width=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: A flattened input grid (row-major); 10x10 unless height and width
      are given.
    height: Canvas height, 3..30 (random if omitted).
    width: Canvas width, 3..30 (random if omitted).
  """

  if colors is None:
    height = _dimension(height, "height")
    width = _dimension(width, "width")
    for _ in range(ATTEMPTS):
      grid = _sample(height, width)
      if grid is not None:
        break
    else:
      raise RuntimeError(f"no scene within {ATTEMPTS} attempts at {height}x{width}")
    colors = common.flatten(grid)
  else:
    if (height is None) != (width is None):
      raise ValueError("give both height and width with explicit colors")
    height = 10 if height is None else _dimension(height, "height")
    width = 10 if width is None else _dimension(width, "width")
    if (len(colors) != height * width or
        any(isinstance(c, bool) or not isinstance(c, int) or not 0 <= c <= 9
            for c in colors)):
      raise ValueError("colors must be height*width ints in 0..9")

  grid, output = common.grids(width, height)
  for i, color in enumerate(colors):
    output[i // width][i % width] = grid[i // width][i % width] = color
  check_scene(grid)
  for row in range(height):
    for col in range(width):
      if output[row][col]: output[row][col] = output[row][0]
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       9, 0, 0, 0, 0, 5, 0, 0, 0, 0,
                       9, 0, 0, 0, 0, 5, 0, 0, 0, 0,
                       6, 0, 0, 0, 5, 5, 0, 0, 0, 0,
                       6, 0, 0, 5, 5, 5, 0, 0, 0, 0,
                       6, 0, 0, 5, 0, 5, 0, 0, 0, 0,
                       4, 0, 0, 0, 0, 5, 0, 0, 0, 0,
                       4, 0, 0, 0, 0, 5, 0, 0, 0, 0,
                       4, 0, 0, 0, 5, 5, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
      generate(colors=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       8, 0, 0, 0, 0, 5, 0, 0, 0, 0,
                       8, 0, 0, 0, 0, 5, 0, 0, 0, 0,
                       8, 0, 0, 5, 5, 5, 0, 0, 0, 0,
                       2, 0, 0, 5, 0, 0, 0, 0, 0, 0,
                       2, 0, 0, 5, 0, 0, 0, 0, 0, 0,
                       2, 0, 0, 5, 5, 5, 5, 0, 0, 0,
                       2, 0, 0, 0, 0, 0, 5, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
  ]
  test = [
      generate(colors=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       2, 0, 0, 0, 5, 5, 0, 5, 0, 0,
                       2, 0, 0, 5, 5, 5, 5, 5, 0, 0,
                       3, 0, 0, 5, 0, 0, 0, 0, 0, 0,
                       3, 0, 0, 5, 5, 5, 0, 0, 0, 0,
                       3, 0, 0, 0, 0, 5, 0, 0, 0, 0,
                       4, 0, 0, 5, 5, 5, 5, 0, 0, 0,
                       7, 0, 0, 5, 5, 5, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
  ]
  return {"train": train, "test": test}
