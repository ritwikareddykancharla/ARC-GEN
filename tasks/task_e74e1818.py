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


def _legacy_explicit(width, height, colors):
  """Historical explicit generate(width, height, colors) semantics.

  This is a compatibility path, not part of the certified random grammar. It
  runs the draw() of the generator before 238f085 verbatim, so every explicit
  call that returned a result there returns equal grids here, including
  repeated nonadjacent band colours (each contiguous run is reflected on its
  own), ink on the border (output rows 0 and height - 1 are cleared when
  height >= 3), widths below 3, height 2, a colour list shorter than the canvas
  (remaining cells are 0) and mixed-colour rows (grouped by the historical
  list(set(row)) key). Calls on which the historical code raised (an interior
  row without ink, more colours than cells, height below 2) raise ValueError.
  Values outside ARC grids (non-int or bool dimensions or colours, colours
  outside 0..9, sides above 30, empty grids) are rejected, although the
  historical code sometimes returned something for them. The factory and the
  coordinate checker are certified only on the random grammar and the
  canonical fixtures; they may disagree with legacy-only explicit scenes.
  """
  if type(width) is not int or not 1 <= width <= 30:
    raise ValueError("Explicit width must be an integer in [1, 30]")
  if type(height) is not int or not 2 <= height <= 30:
    raise ValueError("Explicit height must be an integer in [2, 30]")
  try:
    colors = list(colors)
  except TypeError:
    raise ValueError("Explicit colours must be a sequence") from None
  if len(colors) > width * height or any(type(c) is not int or not 0 <= c <= 9 for c in colors):
    raise ValueError("Explicit colours must give at most one colour in 0..9 per cell")
  filled = colors + [0] * (width * height - len(colors))
  if any(not any(filled[r * width:(r + 1) * width]) for r in range(1, height - 1)):
    raise ValueError("Every interior row of an explicit scene must contain ink")

  def draw():
    grid, output = common.grids(width, height)
    for i, color in enumerate(colors):
      grid[i // width][i % width] = color
    last, length, lengths = -1, 1, []
    for row in range(1, height - 1):
      subset = list(set(grid[row]))
      if 0 in subset: subset.remove(0)
      if subset[0] == last:
        length += 1
      else:
        if last != -1: lengths.append(length)
        last, length = subset[0], 1
    lengths.append(length)
    inrow = outrow = 1
    for length in lengths:
      outrow = outrow + length - 1
      for _ in range(length):
        output[outrow] = grid[inrow]
        inrow, outrow = inrow + 1, outrow - 1
      outrow = inrow
    return grid, output

  grid, output = draw()
  # The historical output aliased input rows; return equal, independent rows.
  return {"input": grid, "output": [row[:] for row in output]}


def generate(width=None, height=None, colors=None, *, num_bands=None, symmetric=None):
  """Reflect each monochromatic row band vertically on a rectangular canvas.

  Certified random grammar (colors=None): independent dimensions 3..30, 1..9
  bands with distinct colours, symmetric or asymmetric nonempty monochromatic
  row patterns, native black border; num_bands/symmetric are validated.
  Complete explicit width/height/colors calls keep their historical
  (pre-238f085) labels through _legacy_explicit, which is compatibility
  support only and is not covered by the certificate.
  """
  import random

  def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
      raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value

  if colors is not None:
    if width is None or height is None:
      raise ValueError("Explicit colours require width and height")
    if num_bands is not None or symmetric is not None:
      raise ValueError("Random band controls cannot accompany explicit colours")
    return _legacy_explicit(width, height, colors)
  width = random.randint(3, 30) if width is None else integer(width, 3, 30, "width")
  height = random.randint(3, 30) if height is None else integer(height, 3, 30, "height")
  if symmetric is not None and type(symmetric) is not bool:
    raise ValueError("symmetric must be a boolean")
  n = random.randint(1, min(9, height - 2)) if num_bands is None else integer(
      num_bands, 1, min(9, height - 2), "num_bands")
  cuts = [0] + sorted(random.sample(range(1, height - 2), n - 1)) + [height - 2]
  palette = random.sample(range(1, 10), n)
  grid = common.grid(width, height)
  for j, colour in enumerate(palette):
    mirror = random.choice([False, True]) if symmetric is None else symmetric
    for r in range(1 + cuts[j], 1 + cuts[j + 1]):
      positions = list(range(1, (width + 1) // 2)) if mirror else list(range(1, width - 1))
      selected = random.sample(positions, random.randint(1, len(positions)))
      for c in selected:
        grid[r][c] = colour
        if mirror: grid[r][width - 1 - c] = colour
  colors = common.flatten(grid)
  # Invariants of the certified random grammar; sampled scenes always hold them.
  if len(colors) != width * height or any(type(c) is not int or not 0 <= c <= 9 for c in colors):
    raise ValueError("Explicit colours must contain one valid colour per cell")
  grid = [list(colors[r * width:(r + 1) * width]) for r in range(height)]
  if any(grid[0]) or any(grid[-1]) or any(row[0] or row[-1] for row in grid):
    raise ValueError("A black outer border is required")
  keys = []
  for row in grid[1:-1]:
    values = set(row) - {0}
    if len(values) != 1:
      raise ValueError("Every interior row must contain exactly one nonblack colour")
    keys.append(next(iter(values)))
  runs = [(key, i + 1) for i, key in enumerate(keys) if i == 0 or key != keys[i - 1]]
  if len({key for key, _ in runs}) != len(runs):
    raise ValueError("Each colour must occupy a single contiguous band")
  output = [row[:] for row in grid]
  for j, (_, a) in enumerate(runs):
    b = runs[j + 1][1] if j + 1 < len(runs) else height - 1
    output[a:b] = [row[:] for row in reversed(grid[a:b])]
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(width=11, height=11,
               colors=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0,
                       0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0,
                       0, 0, 0, 8, 8, 8, 8, 8, 0, 0, 0,
                       0, 0, 0, 5, 0, 5, 0, 5, 0, 0, 0,
                       0, 0, 0, 5, 0, 0, 0, 5, 0, 0, 0,
                       0, 0, 0, 5, 5, 5, 5, 5, 0, 0, 0,
                       0, 0, 0, 0, 2, 2, 2, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
      generate(width=13, height=13,
               colors=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0,
                       0, 0, 0, 0, 2, 0, 2, 0, 2, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 2, 0, 2, 0, 0, 0, 0, 0,
                       0, 0, 0, 3, 0, 0, 3, 0, 0, 3, 0, 0, 0,
                       0, 0, 0, 0, 3, 3, 3, 3, 3, 0, 0, 0, 0,
                       0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0,
                       0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0,
                       0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0,
                       0, 0, 0, 0, 4, 4, 0, 4, 4, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
      generate(width=7, height=7,
               colors=[0, 0, 0, 0, 0, 0, 0,
                       0, 0, 9, 9, 9, 0, 0,
                       0, 9, 0, 9, 0, 9, 0,
                       0, 0, 4, 4, 4, 0, 0,
                       0, 3, 3, 3, 3, 3, 0,
                       0, 0, 0, 3, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0]),
  ]
  test = [
      generate(width=15, height=15,
               colors=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 2, 0, 0, 2, 0, 0, 0, 2, 0, 0, 2, 0, 0,
                       0, 0, 0, 2, 2, 2, 0, 2, 0, 2, 2, 2, 0, 0, 0,
                       0, 0, 0, 0, 0, 2, 0, 0, 0, 2, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 3, 0, 0, 0, 3, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 4, 4, 4, 4, 0, 4, 4, 4, 4, 0, 0, 0,
                       0, 0, 0, 0, 4, 0, 4, 0, 4, 0, 4, 0, 0, 0, 0,
                       0, 0, 0, 0, 4, 4, 4, 0, 4, 4, 4, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 8, 8, 8, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 8, 8, 0, 8, 8, 0, 0, 0, 0, 0,
                       0, 0, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
  ]
  return {"train": train, "test": test}
