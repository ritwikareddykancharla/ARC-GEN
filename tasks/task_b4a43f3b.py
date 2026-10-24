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

MOTIF_COLOURS = (1, 2, 3, 6)   # fixture motif palette
DIVIDER, MARK = 5, 2
SCALES = (1, 2, 3)             # motif upscale; map width is 3 * scale
MAX_MAP_HEIGHT = 10            # output height 3 * map height <= 30
MAX_SEGMENTS = 8
MAX_FREE_CELLS = 2


def _motif_masks():
  """Every 3x3 mask with all rows and columns occupied, 8-connected.

  This keeps the two properties of common.diagonally_connected_sprite masks:
  a full 3x3 span (no empty row or column) and 8-connectivity. It is
  enumerated once, so sampling needs no unbounded rejection loop. The mask
  size range widens from the helper's 4..9 cells (at most 5 deletions) to
  3..9: three-cell diagonals and other spanning triples are now included.
  """
  masks = []
  for bits in range(1, 512):
    cells = [(r, c) for r in range(3) for c in range(3) if bits >> (3 * r + c) & 1]
    if {r for r, _ in cells} != {0, 1, 2} or {c for _, c in cells} != {0, 1, 2}:
      continue
    seen, stack = {cells[0]}, [cells[0]]
    while stack:
      r, c = stack.pop()
      for p in cells:
        if p not in seen and abs(p[0] - r) <= 1 and abs(p[1] - c) <= 1:
          seen.add(p)
          stack.append(p)
    if len(seen) == len(cells):
      masks.append(cells)
  return masks


MOTIF_MASKS = _motif_masks()


def _int(value, name, low, high):
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{name} must be an int, got {value!r}")
  if not low <= value <= high:
    raise ValueError(f"{name}={value} outside {low}..{high}")
  return value


def _random_motif():
  cells = common.choice(MOTIF_MASKS)
  return "".join(str(common.choice(MOTIF_COLOURS)) if (r, c) in cells else "0"
                 for r in range(3) for c in range(3))


def _random_map(height, width):
  """A non-empty binary map: 1..8 axis segments plus 0..2 free cells, or a scatter."""
  grid = common.grid(width, height)
  if common.randint(0, 2):
    for _ in range(common.randint(1, MAX_SEGMENTS)):
      vertical = common.randint(0, 1)
      span = height if vertical else width
      length = common.randint(1, span)
      pos = common.randint(0, span - length)
      val = common.randint(0, (width if vertical else height) - 1)
      for i in range(pos, pos + length):
        grid[i if vertical else val][val if vertical else i] = MARK
    for _ in range(common.randint(0, MAX_FREE_CELLS)):
      grid[common.randint(0, height - 1)][common.randint(0, width - 1)] = MARK
  else:
    # Scatter: a uniform number 1..area of distinct marked cells, so sparse,
    # dense and full maps all occur without rejection.
    cells = [(r, c) for r in range(height) for c in range(width)]
    for r, c in common.sample(cells, common.randint(1, len(cells))):
      grid[r][c] = MARK
  return "".join(str(x) for x in common.flatten(grid))


def _check_grids(grid, output):
  for g in (grid, output):
    if not 1 <= len(g) <= 30 or not 1 <= len(g[0]) <= 30 or any(
        isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9
        for row in g for v in row):
      raise ValueError("explicit scene is not a valid ARC grid")
  return {"input": grid, "output": output}


def _legacy_draw(colors, pattern):
  """The pre-expansion complete explicit path, kept verbatim (13x6 -> 18x18).

  Its labels are unchanged: any motif digits (including the divider colour 5
  or an all-0 motif), any map (including an empty one) and any non-"0"
  pattern entry drawn as 2. Only inputs the old code crashed on, or values
  outside ARC colours, raise ValueError. Such scenes are outside the
  certified random domain.
  """
  try:
    grid, output = common.grid(6, 13), common.grid(18, 18)
    for c in range(6):
      grid[6][c] = 5
    for row in range(3):
      for col in range(3):
        common.rect(grid, 2, 2, row * 2, col * 2, int(colors[row * 3 + col]))
    for row in range(6):
      for col in range(6):
        if pattern[row * 6 + col] == "0": continue
        grid[row + 7][col] = 2
        for r in range(3):
          for c in range(3):
            output[row * 3 + r][col * 3 + c] = int(colors[r * 3 + c])
  except (IndexError, TypeError, ValueError) as exc:
    raise ValueError(f"explicit colors/pattern not drawable: {exc!r}") from exc
  return _check_grids(grid, output)


def generate(colors=None, pattern=None, scale=None, map_height=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: A list of colors to use (the 3x3 motif, row-major, 9 digits).
    pattern: A list of patterns to use (the placement map, row-major; "0" is
      empty and any other digit is drawn as a 2; its width is 3 * scale).
    scale: Upscale of the motif shown above the divider, 1..3.
    map_height: Placement map height, 1..10.

  Complete explicit colors and pattern without scale or map_height use the
  legacy 13x6 path unchanged. Otherwise explicit values are kept, never
  replaced: explicit colors or pattern default to scale 2, explicit colors
  to a 6-row map, and an explicit pattern fixes the map height.
  """

  if scale is not None:
    _int(scale, "scale", min(SCALES), max(SCALES))
  if map_height is not None:
    _int(map_height, "map_height", 1, MAX_MAP_HEIGHT)
  if colors is not None and pattern is not None and scale is None and map_height is None:
    return _legacy_draw(colors, pattern)

  if colors is not None:
    colors = "".join(str(v) for v in colors)
    if len(colors) != 9 or not colors.isdigit():
      raise ValueError("colors must be 9 digits 0..9")
  legacy = colors is not None or pattern is not None
  if scale is None:
    scale = 2 if legacy else common.choice(SCALES)
  width = 3 * scale
  if pattern is not None:
    pattern = "".join(str(v) for v in pattern)
    if not pattern.isdigit():
      raise ValueError("pattern must hold digits 0..9")
    if len(pattern) % width:
      raise ValueError(f"pattern length {len(pattern)} is not a multiple of {width}")
    height = _int(len(pattern) // width, "pattern height", 1, MAX_MAP_HEIGHT)
    if map_height is not None and map_height != height:
      raise ValueError("map_height disagrees with the pattern")
  else:
    height = map_height if map_height is not None else (
        6 if legacy else common.randint(1, MAX_MAP_HEIGHT))
  if colors is None:
    colors = _random_motif()
  if pattern is None:
    pattern = _random_map(height, width)

  grid = common.grid(width, width + 1 + height)
  output = common.grid(3 * width, 3 * height)
  for c in range(width):
    grid[width][c] = DIVIDER
  for row in range(3):
    for col in range(3):
      common.rect(grid, scale, scale, row * scale, col * scale,
                  int(colors[row * 3 + col]))
  for row in range(height):
    for col in range(width):
      if pattern[row * width + col] == "0": continue
      grid[row + width + 1][col] = MARK
      for r in range(3):
        for c in range(3):
          output[row * 3 + r][col * 3 + c] = int(colors[r * 3 + c])
  return _check_grids(grid, output)


def validate():
  """Validates the generator."""
  train = [
      generate(colors="101020320",
               pattern="000000002000022220002000000000000000"),
      generate(colors="136010221",
               pattern="000000220000220000002000000200000000"),
      generate(colors="101010333",
               pattern="000000000000002000002000022200000000"),
      generate(colors="320020061",
               pattern="000000020000002000022220000000000000"),
  ]
  test = [
      generate(colors="010303020",
               pattern="202000002000222222002000002000002000"),
  ]
  return {"train": train, "test": test}
