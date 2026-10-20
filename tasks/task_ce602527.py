# Copyright 2025 Google LLC
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

_MAX_SCENE_ATTEMPTS = 20000
_MAX_SPRITE_ATTEMPTS = 2000


def _color_cells(grid, color):
  cells = set()
  for r, row in enumerate(grid):
    for c, value in enumerate(row):
      if value == color: cells.add((r, c))
  return cells


def _scaled_match(clue, source, height, width, scale=2):
  """True if source's bbox shape, scaled, can be placed (possibly hanging off
  the grid at any integer offset) so its in-grid cells are exactly clue."""
  if not clue or not source: return False
  r0 = min(r for r, _ in source)
  c0 = min(c for _, c in source)
  tall = scale * (max(r for r, _ in source) - r0 + 1)
  wide = scale * (max(c for _, c in source) - c0 + 1)
  scaled = [(scale * (r - r0) + dr, scale * (c - c0) + dc)
            for r, c in source for dr in range(scale) for dc in range(scale)]
  cr0, cr1 = min(r for r, _ in clue), max(r for r, _ in clue)
  cc0, cc1 = min(c for _, c in clue), max(c for _, c in clue)
  if cr1 - cr0 + 1 > tall or cc1 - cc0 + 1 > wide: return False
  for oy in range(cr1 - tall + 1, cr0 + 1):
    for ox in range(cc1 - wide + 1, cc0 + 1):
      visible = set()
      for r, c in scaled:
        rr, cc = r + oy, c + ox
        if 0 <= rr < height and 0 <= cc < width: visible.add((rr, cc))
      if visible == clue: return True
  return False


def _uniquely_determined(grid, bgcolor, magcolor, srccolor):
  """Solver-independent uniqueness: background is the strict mode and exactly
  one source colour explains all feasible clues at scale 2."""
  height, width = len(grid), len(grid[0])
  counts = {}
  for row in grid:
    for value in row:
      counts[value] = counts.get(value, 0) + 1
  bgcount = counts.get(bgcolor, 0)
  if any(v >= bgcount for k, v in counts.items() if k != bgcolor): return False
  groups = {k: _color_cells(grid, k) for k in counts if k != bgcolor}
  pairs = [(a, b) for a in groups for b in groups
           if a != b and _scaled_match(groups[a], groups[b], height, width)]
  return (magcolor, srccolor) in pairs and {source for _, source in pairs} == {srccolor}


def generate(width=None, height=None, rows=None, cols=None, idxs=None,
             brows=None, bcols=None, magrow=None, magcol=None, colors=None,
             magcolor=None, bgcolor=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the width of the (square) grid
    height: the height of the (square) grid
    rows: a list of vertical coordinates where pixels should be placed
    cols: a list of horizontal coordinates where pixels should be placed
    idxs: a list of indices of the sprites
    brows: a list of vertical coordinates where sprites should be placed
    bcols: a list of horizontal coordinates where sprites should be placed
    magrow: the vertical coordinate where the magnified sprite should be
    magcol: the horizontal coordinate where the magnified sprite should be
    colors: a list of colors to be used
    magcolor: a digit representing a magnified color to be used
    bgcolor: a digit representing a background color to be used
  """

  def draw(b, mrow, mcol, mcolor):
    legal = True
    wide = max([c for c, i in zip(cols, idxs) if not i]) + 1
    tall = max([r for r, i in zip(rows, idxs) if not i]) + 1
    grid = common.grid(width, height, b)
    output = common.grid(wide, tall, b)
    some_hidden = False
    for row, col, idx in zip(rows, cols, idxs):
      r, c = brows[idx] + row, bcols[idx] + col
      if grid[r][c] != b: legal = False
      grid[r][c] = colors[idx]
      if idx: continue  # Not the magnified sprite.
      output[row][col] = colors[idx]
      for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        r, c = mrow + 2 * row + dr, mcol + 2 * col + dc
        if common.get_pixel(grid, r, c) == -1: some_hidden = True
        if common.get_pixel(grid, r, c) not in [b, -1]: legal = False
        common.draw(grid, r, c, mcolor)
    # Repaired: require that SOME scaled cell is hidden (checked once, after
    # all pixels), instead of requiring the first processed pixel to be hidden.
    if not some_hidden: legal = False
    return grid, output, legal

  if rows is None:
    width, height = common.randint(15, 19), common.randint(15, 19)
    bgcolor = common.random_color()
    magcolor = common.random_color(exclude=[bgcolor])
    colors = common.random_colors(2, exclude=[bgcolor, magcolor])
    for _ in range(_MAX_SCENE_ATTEMPTS):
      rows, cols, idxs, brows, bcols = [], [], [], [], []
      ok = True
      for idx in range(2):
        wide, tall = common.randint(3, 5), common.randint(3, 5)
        for _ in range(_MAX_SPRITE_ATTEMPTS):
          xrows, xcols = common.conway_sprite(wide, tall, wide + tall)
          if common.diagonally_connected(list(zip(xrows, xcols))): break
        else:
          ok = False
          break
        rows.extend(xrows)
        cols.extend(xcols)
        idxs.extend([idx] * len(xrows))
        brows.append(common.randint(0, height - tall))
        bcols.append(common.randint(0, width - wide))
        if idx: continue
        magrow = common.randint(0, height - 2 * tall)
        magcol = common.randint(0, width - 2 * wide)
        if common.randint(0, 1):
          magrow = -2 if common.randint(0, 1) else height - 2 * tall + 2
        else:
          magcol = -2 if common.randint(0, 1) else width - 2 * wide + 2
      if not ok: continue
      ingrid, _, legal = draw(bgcolor, magrow, magcol, magcolor)
      if not legal: continue
      if _uniquely_determined(ingrid, bgcolor, magcolor, colors[0]): break
    else:
      raise RuntimeError("Could not sample an unambiguous scene")

  grid, output, _ = draw(bgcolor, magrow, magcol, magcolor)
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(width=17, height=17,
               rows=[0, 0, 0, 0, 0, 1, 1, 1, 2, 3, 3, 3, 4, 4, 4, 4, 4,
                     0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 3, 4, 4, 4, 4, 4],
               cols=[0, 1, 2, 3, 4, 0, 2, 4, 4, 0, 2, 4, 0, 1, 2, 3, 4,
                     0, 1, 3, 4, 0, 4, 0, 1, 2, 3, 4, 2, 0, 1, 2, 3, 4],
               idxs=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
               brows=[3, 2], bcols=[3, 11], magrow=9, magcol=3,
               colors=[2, 3], magcolor=8, bgcolor=1),
      generate(width=18, height=18,
               rows=[0, 1, 1, 1, 2, 3, 3, 3, 4, 0, 0, 1, 1, 1, 1, 1, 2, 2],
               cols=[1, 0, 1, 2, 1, 0, 1, 2, 1, 1, 3, 0, 1, 2, 3, 4, 1, 3],
               idxs=[0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
               brows=[8, 4], bcols=[11, 3], magrow=10, magcol=-1,
               colors=[4, 3], magcolor=6, bgcolor=8),
      generate(width=17, height=19,
               rows=[0, 0, 0, 1, 2, 2, 2, 3, 4, 4, 4,
                     0, 0, 0, 1, 1, 1, 1, 1, 2],
               cols=[0, 1, 2, 0, 0, 1, 2, 2, 0, 1, 2,
                     0, 2, 4, 0, 1, 2, 3, 4, 2],
               idxs=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     1, 1, 1, 1, 1, 1, 1, 1, 1],
               brows=[2, 10], bcols=[4, 8], magrow=13, magcol=-2,
               colors=[8, 3], magcolor=1, bgcolor=2),
      generate(width=17, height=15,
               rows=[0, 0, 0, 1, 1, 1, 1, 2, 2, 2,
                     0, 0, 1, 1, 1, 1, 2, 2, 3, 3, 3, 3],
               cols=[1, 2, 3, 0, 1, 3, 4, 1, 2, 3,
                     0, 3, 0, 1, 2, 3, 0, 3, 0, 1, 2, 3],
               idxs=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
               brows=[9, 2], bcols=[8, 5], magrow=9, magcol=-3,
               colors=[3, 8], magcolor=2, bgcolor=1),
  ]
  test = [
      generate(width=18, height=18,
               rows=[0, 1, 1, 1, 2, 3, 3, 3, 0, 0, 0, 1, 1, 1, 2, 2, 2],
               cols=[1, 0, 1, 2, 1, 0, 1, 2, 0, 2, 3, 0, 1, 3, 0, 2, 3],
               idxs=[0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
               brows=[5, 2], bcols=[2, 9], magrow=12, magcol=6,
               colors=[6, 1], magcolor=8, bgcolor=3),
  ]
  return {"train": train, "test": test}
