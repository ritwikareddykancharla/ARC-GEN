# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ARC task 221dfab4: a striped ladder grows out of a yellow edge bar.

Rule: the input has a background colour, several separated blobs of one
blob colour, and one straight yellow (4) bar lying on a grid edge. Lines
parallel to the bar are numbered by their distance d from the bar, going
away from the edge the bar touches. Within the bar's span (its range of
cross positions), the line at distance d becomes:
  d % 6 in {0, 2}: yellow (4);
  d % 6 in {1, 3, 5}: background (blob cells there are erased);
  d % 6 == 4: green (3); in addition every non-background cell anywhere
    on that whole line is recoloured green.
Everything outside the span on the other lines is unchanged.

Scope: the bar may lie on the top, bottom, left or right edge (vertical
bars give column ladders). Grid sides are 10..30, the bar length is
2..9, background and blob colours are sampled from colours other than
3 and 4. Blobs are random stacks of overlapping runs that are separated
from each other by at least one background cell and never touch the bar
line. The background always covers the majority of the grid.
"""

import copy
import random

import common

_SIDES = ("top", "bottom", "left", "right")
_PALETTE = (0, 1, 2, 5, 6, 7, 8, 9)


def _render(width, height, bg, color, side, bar_start, bar_length, cells):
  """Draws the input scene and the ladder output from latent parameters."""
  inp = common.grid(width, height, bg)
  for r, c in cells:
    inp[r][c] = color
  horizontal = side in ("top", "bottom")
  n = height if horizontal else width
  cross = width if horizontal else height
  forward = side in ("top", "left")
  span = range(bar_start, bar_start + bar_length)

  def put(g, idx, j, value):
    if horizontal:
      g[idx][j] = value
    else:
      g[j][idx] = value

  def get(g, idx, j):
    return g[idx][j] if horizontal else g[j][idx]

  bar_idx = 0 if forward else n - 1
  for j in span:
    put(inp, bar_idx, j, 4)
  out = copy.deepcopy(inp)
  for d in range(n):
    idx = d if forward else n - 1 - d
    m = d % 6
    if m % 2 == 1:
      value = bg
    elif m == 4:
      value = 3
      for j in range(cross):
        if get(inp, idx, j) != bg:
          put(out, idx, j, 3)
    else:
      value = 4
    for j in span:
      put(out, idx, j, value)
  return {"input": inp, "output": out}


def _blob_shape(max_h, max_w):
  """Returns a blob as a stack of overlapping runs (canonical frame)."""
  h = random.randint(2, max_h)
  w = random.randint(2, max_w)
  runs = [(0, w)]
  for _ in range(h - 1):
    ps, pw = runs[-1]
    ns, nw = ps, pw
    for _ in range(20):
      cs = ps + random.randint(-2, 2)
      cw = max(1, min(max_w, pw + random.randint(-3, 3)))
      if cs <= ps + pw - 1 and cs + cw - 1 >= ps:
        ns, nw = cs, cw
        break
    runs.append((ns, nw))
  lo = min(s for s, _ in runs)
  cells = []
  for a, (s, w0) in enumerate(runs):
    for b in range(s, s + w0):
      cells.append((a, b - lo))
  extent = max(b for _, b in cells) + 1
  return cells, h, extent


def _random_blobs(length, cross, coverage):
  """Places separated blobs in the canonical frame (bar on line a=0)."""
  occupied = set()
  blocked = set()
  area = length * cross
  for _ in range(300):
    if len(occupied) >= coverage * area:
      break
    shape, h, extent = _blob_shape(min(7, length - 1), min(12, cross))
    if extent > cross or h > length - 1:
      continue
    a0 = random.randint(1, length - h)
    b0 = random.randint(0, cross - extent)
    cells = [(a0 + a, b0 + b) for a, b in shape]
    if any(cell in blocked for cell in cells):
      continue
    if len(occupied) + len(cells) > 0.42 * area:
      continue
    occupied.update(cells)
    for a, b in cells:
      for da in (-1, 0, 1):
        for db in (-1, 0, 1):
          blocked.add((a + da, b + db))
  return occupied


def _to_actual(a, b, side, width, height):
  if side == "top":
    return (a, b)
  if side == "bottom":
    return (height - 1 - a, b)
  if side == "left":
    return (b, a)
  return (b, width - 1 - a)


def _parse(input_grid):
  """Extracts latent parameters from a fixture input (replay only)."""
  height, width = len(input_grid), len(input_grid[0])
  counts = {}
  for row in input_grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  bg = max(counts, key=lambda v: counts[v])
  others = [v for v in counts if v not in (bg, 4)]
  color = others[0] if others else (1 if bg != 1 else 2)
  bar = [(r, c) for r in range(height) for c in range(width)
         if input_grid[r][c] == 4]
  rows = sorted(set(r for r, _ in bar))
  cols = sorted(set(c for _, c in bar))
  if len(rows) == 1:
    side = "top" if rows[0] == 0 else "bottom"
    bar_start, bar_length = cols[0], len(cols)
  else:
    side = "left" if cols[0] == 0 else "right"
    bar_start, bar_length = rows[0], len(rows)
  cells = [(r, c) for r in range(height) for c in range(width)
           if input_grid[r][c] not in (bg, 4)]
  return width, height, bg, color, side, bar_start, bar_length, cells


def generate(width=None, height=None, bg=None, color=None, side=None,
             bar_start=None, bar_length=None, blob_cells=None,
             input_grid=None):
  """Returns an input/output pair for the ladder task.

  Args:
    width: grid width (10..30 for random scenes).
    height: grid height (10..30 for random scenes).
    bg: background colour (not 3 or 4).
    color: blob colour (not 3, 4 or bg).
    side: edge holding the yellow bar: top, bottom, left or right.
    bar_start: first cross index (column or row) covered by the bar.
    bar_length: number of cells in the bar (>= 2).
    blob_cells: explicit list of (row, col) blob cells in grid coordinates.
    input_grid: optional fixture replay; latent parameters are extracted
      from this grid and re-rendered through the constructive renderer.
  """
  if input_grid is not None:
    return _render(*_parse(input_grid))
  if side is None:
    side = random.choice(_SIDES)
  if side not in _SIDES:
    raise ValueError("side must be top, bottom, left or right")
  horizontal = side in ("top", "bottom")
  if width is None:
    width = random.randint(10, 30)
  if height is None:
    height = random.randint(10, 30)
  if not (10<=width<=30 and 10<=height<=30):
    raise ValueError("canvas dimensions must be 10..30")
  length = height if horizontal else width
  cross = width if horizontal else height
  if bg is None:
    bg = random.choice([c for c in _PALETTE if c != color])
  if color is None:
    color = random.choice([c for c in _PALETTE if c != bg])
  if bg not in _PALETTE or color not in _PALETTE or bg==color:
    raise ValueError("background/blob colours must differ and exclude 3/4")
  if bar_length is None:
    bar_length = random.randint(2, min(9, cross - 3))
  if not 2<=bar_length<=cross:
    raise ValueError("bar length must fit the grid edge")
  if bar_start is None:
    bar_start = random.randint(1, cross-bar_length-1) if bar_length<=cross-2 else 0
  if not 0<=bar_start<=cross-bar_length:
    raise ValueError("bar span must lie inside the grid edge")
  if blob_cells is None:
    span = set(range(bar_start, bar_start + bar_length))
    blobs = set()
    for _ in range(40):
      blobs = _random_blobs(length, cross, random.uniform(0.15, 0.35))
      green_hit = any(a % 6 == 4 and b not in span for a, b in blobs)
      span_hit = any(b in span for _, b in blobs)
      if green_hit and span_hit:
        break
    else:
      raise RuntimeError("could not place blobs exercising both ladder interactions")
    blob_cells = [_to_actual(a, b, side, width, height) for a, b in blobs]
  return _render(width, height, bg, color, side, bar_start, bar_length,
                 blob_cells)


def _decode(rows, width):
  """Decodes run-length rows like '1*11 8*2 1*9' into a grid."""
  grid = []
  for text in rows:
    row = []
    for token in text.split():
      value, count = token.split("*")
      row.extend([int(value)] * int(count))
    if len(row) != width:
      raise ValueError("bad fixture row width")
    grid.append(row)
  return grid


_TRAIN1 = [
    "1*22", "1*11 8*2 1*9", "1*7 8*11 1*4", "1*8 8*10 1*4",
    "1*13 8*4 1*5", "1*22", "1*4 8*3 1*15", "1*4 8*7 1*11",
    "1*3 8*14 1*5", "1*2 8*10 1*10", "1*3 8*5 1*14", "1*15 8*2 1*5",
    "1*9 8*9 1*4", "1*9 8*9 1*4", "1*12 8*4 1*6", "1*22",
    "1*4 8*3 1*15", "1*2 8*9 1*4 8*2 1*5", "1*2 8*10 1*3 8*3 1*4",
    "1*2 8*10 1*10", "1*7 8*3 1*12", "1*22", "1*2 8*3 1*17",
    "1*1 8*5 1*8 8*5 1*3", "1*2 8*5 1*4 8*8 1*3",
    "1*4 8*2 1*2 8*11 1*3", "1*9 8*3 1*10", "1*22", "1*11 4*4 1*7",
]

_TRAIN2 = [
    "8*22", "8*22", "8*4 2*3 8*1 2*3 8*5 2*4 8*2",
    "8*4 2*7 8*4 2*5 8*2", "8*6 2*4 8*6 2*4 8*2",
    "8*5 2*5 8*8 2*1 8*3", "8*2 2*11 8*9", "8*6 2*8 8*8",
    "8*6 2*7 8*9", "8*6 2*3 8*3 2*2 8*8", "8*1 2*2 8*19",
    "8*1 2*5 8*16", "8*1 2*5 8*16", "8*2 2*2 8*8 2*8 8*2",
    "8*11 2*9 8*2", "8*11 2*6 8*5", "8*22", "8*3 2*4 8*15",
    "2*7 8*15", "2*1 8*1 2*6 8*7 2*7", "8*3 2*6 8*4 2*7 8*2",
    "8*4 2*7 8*4 2*4 8*1 2*2", "8*9 2*2 8*5 2*5 8*1",
    "8*16 2*5 8*1", "8*6 2*5 8*6 2*3 8*2", "8*6 2*13 8*3",
    "8*8 2*6 8*8", "8*9 2*5 8*8", "8*2 4*3 8*17",
]

_TEST1 = [
    "8*7 4*8 8*10", "8*25", "8*25", "8*7 6*4 8*14",
    "8*3 6*8 8*4 6*5 8*5", "8*4 6*6 8*3 6*9 8*3",
    "8*5 6*2 8*8 6*7 8*3", "8*12 6*5 8*1 6*3 8*4", "8*10 6*8 8*7",
    "8*5 6*1 8*1 6*11 8*7", "8*3 6*12 8*10", "8*5 6*6 8*14", "8*25",
    "8*13 6*9 8*3", "8*15 6*8 8*2", "8*4 6*7 8*9 6*2 8*3",
    "8*3 6*9 8*6 6*4 8*3", "8*2 6*8 8*7 6*8", "8*4 6*6 8*8 6*7",
    "8*19 6*6", "8*5 6*2 8*3 6*7 8*2 6*5 8*1", "8*2 6*12 8*11",
    "8*5 6*12 8*8", "8*5 6*12 8*8", "8*8 6*9 8*8",
]

_TEST2 = [
    "2*30", "2*9 1*2 2*16 1*1 2*2", "2*8 1*4 2*14 1*3 2*1",
    "2*7 1*8 2*10 1*4 2*1", "2*7 1*8 2*3 1*2 2*5 1*4 2*1",
    "4*1 2*7 1*6 2*4 1*3 2*5 1*3 2*1",
    "4*1 2*3 1*2 2*5 1*4 2*3 1*5 2*3 1*3 2*1",
    "4*1 2*2 1*3 2*5 1*4 2*3 1*5 2*3 1*3 2*1",
    "4*1 2*2 1*4 2*4 1*3 2*4 1*4 2*4 1*2 2*2",
    "4*1 2*2 1*4 2*5 1*1 2*5 1*3 2*5 1*2 2*2",
    "2*3 1*4 2*11 1*3 2*9", "2*3 1*3 2*12 1*3 2*9",
    "2*3 1*3 2*13 1*2 2*9", "2*3 1*2 2*4 1*4 2*11 1*2 2*4",
    "2*1 1*4 2*3 1*6 2*9 1*3 2*4",
    "2*2 1*2 2*4 1*6 2*3 1*1 2*5 1*3 2*4",
    "2*2 1*2 2*2 1*8 2*2 1*2 2*4 1*4 2*4",
    "2*5 1*2 2*1 1*4 2*4 1*2 2*3 1*5 2*4",
    "2*8 1*4 2*4 1*2 2*2 1*6 2*4", "2*9 1*3 2*8 1*7 2*3",
    "2*2 1*3 2*15 1*7 2*3", "2*2 1*3 2*15 1*7 2*3",
    "2*3 1*4 2*15 1*5 2*3", "2*3 1*5 2*5 1*3 2*7 1*4 2*3",
    "2*3 1*4 2*4 1*6 2*6 1*3 2*4", "2*2 1*4 2*3 1*8 2*8 1*1 2*4",
    "2*3 1*3 2*3 1*7 2*9 1*1 2*4", "2*3 1*3 2*6 1*2 2*16", "2*30",
    "2*30",
]


def validate():
  """Rebuilds the canonical pairs via fixture-input replay."""
  train = [
      generate(input_grid=_decode(_TRAIN1, 22)),
      generate(input_grid=_decode(_TRAIN2, 22)),
  ]
  test = [
      generate(input_grid=_decode(_TEST1, 25)),
      generate(input_grid=_decode(_TEST2, 30)),
  ]
  return {"train": train, "test": test}
