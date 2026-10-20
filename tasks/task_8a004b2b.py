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


def _render(width, height, rows, cols, colors, shows, wide, tall, brow, bcol,
            irow, icol, srow, scol, mag):
  grid, output = common.grid(width, height), common.grid(wide, tall)
  for r, c in [(0, 0), (0, wide - 1), (tall - 1, 0), (tall - 1, wide - 1)]:
    grid[brow + r][bcol + c] = common.yellow()
    output[r][c] = common.yellow()
  for idx, color in enumerate(colors):
    row, col = rows[idx], cols[idx]
    grid[srow + row][scol + col] = color
    for dr in range(mag):
      for dc in range(mag):
        r, c = irow + row * mag + dr, icol + col * mag + dc
        if idx in shows: grid[brow + r][bcol + c] = color
        output[r][c] = color
  return {"input": grid, "output": output}


def _key(g):
  return tuple(tuple(row) for row in g)


def _visible_outputs(grid):
  """All distinct outputs consistent with the visible input (k>=2, corners retained; edge contact permitted)."""
  bg, yel = 0, common.yellow()
  height, width = len(grid), len(grid[0])
  ys = [r for r in range(height) for c in range(width) if grid[r][c] == yel]
  xs = [c for r in range(height) for c in range(width) if grid[r][c] == yel]
  if not ys: return set()
  y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
  tmpl = {}
  for r in range(height):
    for c in range(width):
      v = grid[r][c]
      if v == bg or v == yel: continue
      if y0 <= r <= y1 and x0 <= c <= x1: continue
      tmpl[(r, c)] = v
  if not tmpl: return set()
  ty0 = min(p[0] for p in tmpl)
  tx0 = min(p[1] for p in tmpl)
  rel = {(r - ty0, c - tx0): v for (r, c), v in tmpl.items()}
  th = max(p[0] for p in rel) + 1
  tw = max(p[1] for p in rel) + 1
  crop = [list(row[x0:x1 + 1]) for row in grid[y0:y1 + 1]]
  H, W = len(crop), len(crop[0])
  corners = {(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)}
  nz = [(r, c) for r in range(H) for c in range(W)
        if crop[r][c] != bg and not ((r, c) in corners and crop[r][c] == yel)]
  outs = set()
  for k in range(2, max(H, W) + 1):
    for oy in range(0, H - k * th + 1):
      for ox in range(0, W - k * tw + 1):
        covered, shown, ok = set(), 0, True
        for (ry, rx), col in rel.items():
          cells = [(oy + k * ry + dr, ox + k * rx + dc)
                   for dr in range(k) for dc in range(k)]
          if any(p in corners for p in cells):
            ok = False
            break
          vals = {crop[r][c] for r, c in cells}
          if vals == {col}:
            shown += 1
            covered.update(cells)
          elif vals != {bg}:
            ok = False
            break
        if not ok or shown == 0: continue
        if any(p not in covered for p in nz): continue
        out = [list(row) for row in crop]
        for (ry, rx), col in rel.items():
          for dr in range(k):
            for dc in range(k):
              out[oy + k * ry + dr][ox + k * rx + dc] = col
        outs.add(_key(out))
  return outs


def generate(width=None, height=None, rows=None, cols=None, colors=None,
             shows=None, wide=None, tall=None, brow=None, bcol=None, irow=None,
             icol=None, srow=None, scol=None, mag=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the width of the input grid
    height: the height of the input grid
    rows: a list of vertical coordinates where pixels should be placed
    cols: a list of horizontal coordinates where pixels should be placed
    colors: a list of colors to be used for the pixels
    shows: a subset of pixel indices to show magnified
    wide: the width of the yellow box
    tall: the height of the yellow box
    brow: a vertical coordinate where the box should be placed
    bcol: a horizontal coordinate where the box should be placed
    irow: a vertical coordinate inside the box where the sprite should be
    icol: a horizontal coordinate inside the box where the sprite should be
    srow: a vertical coordinate where the full sprite should be
    scol: a horizontal coordinate where the full sprite should be
    mag: the magnification factor

  Random scenes are rejected unless the visible input admits exactly one
  consistent magnified placement of the sprite (bounded resampling).
  """
  if width is not None:
    return _render(width, height, rows, cols, colors, shows, wide, tall, brow,
                   bcol, irow, icol, srow, scol, mag)
  for _ in range(1000):
    width, height = common.randint(15, 20), common.randint(15, 20)
    mag = common.randint(2, min(4, (height + 1) // 5))
    w, t = common.randint(2, 7 - mag), common.randint(2, 3)
    num_pixels = common.randint(max(4, w * t // 2), w * t)
    pixels = common.continuous_creature(num_pixels, w, t)
    rows, cols = zip(*pixels)
    colors = [common.choice([1, 2, 3, 8]) for _ in pixels]
    num_show = common.randint(2, num_pixels // 2)
    shows = common.sample(range(len(pixels)), num_show)
    wide = common.randint(mag * w + 2, width)
    tall = common.randint(mag * t + 2, height - 4)
    brow = common.randint(0, height - 4 - tall)
    bcol = common.randint(0, width - wide)
    irow = common.randint(1, tall - 1 - mag * t)
    icol = common.randint(1, wide - 1 - mag * w)
    srow = height - t - 1
    scol = common.randint(1, width - 1 - w)
    example = _render(width, height, rows, cols, colors, shows, wide, tall,
                      brow, bcol, irow, icol, srow, scol, mag)
    outs = _visible_outputs(example["input"])
    if len(outs) == 1 and _key(example["output"]) in outs:
      return example
  raise RuntimeError("could not sample an unambiguous scene")


def validate():
  """Validates the generator."""
  train = [
      generate(width=17, height=17,
               rows=[0, 0, 1, 1, 1, 1, 2, 2, 2],
               cols=[0, 4, 0, 1, 3, 4, 1, 2, 3],
               colors=[3, 2, 1, 1, 1, 1, 1, 1, 1],
               shows=[0, 1, 7], wide=14, tall=9,
               brow=0, bcol=2, irow=2, icol=1, srow=12, scol=2, mag=2),
      generate(width=18, height=17,
               rows=[0, 0, 1, 1],
               cols=[0, 1, 0, 1],
               colors=[2, 3, 3, 8],
               shows=[0, 3], wide=7, tall=7,
               brow=1, bcol=2, irow=1, icol=1, srow=13, scol=10, mag=2),
      generate(width=18, height=16,
               rows=[0, 0, 0, 1, 1],
               cols=[0, 1, 2, 1, 2],
               colors=[2, 1, 1, 3, 1],
               shows=[0, 2, 3], wide=11, tall=11,
               brow=0, bcol=3, irow=3, icol=1, srow=13, scol=6, mag=3),
  ]
  test = [
      generate(width=18, height=19,
               rows=[0, 0, 1, 1, 1, 2],
               cols=[0, 2, 0, 1, 2, 1],
               colors=[8, 3, 1, 1, 1, 1],
               shows=[0, 1], wide=18, tall=14,
               brow=0, bcol=0, irow=2, icol=4, srow=15, scol=8, mag=4),
  ]
  return {"train": train, "test": test}
