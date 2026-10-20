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

"""ARC task e729b7be: point-reflect a half shape about the centre marker.

Rule:
  The background is 7. A vertical line of colour 4 runs down the middle
  column cx. Row cy, the middle row, holds three 8 markers: one at each edge
  and one where the row crosses the line, at (cy, cx). A multicoloured shape
  rests against the left side of the line. The output keeps the input and
  adds a copy of the shape rotated 180 degrees about the centre marker. Each
  shape cell (y, x) is copied to (2cy - y, 2cx - x), on the right side of the
  line. The original is not changed.

Scope:
  The generator samples these latent variables:
  * the grid width and height, both odd. Random sizes are 9..29 per side.
    The fixtures are square, 15..19. Other square sizes and non-square grids
    (about 40% of default samples, with width != height) are synthetic
    extensions. The line stays in the middle column and the marker row in the
    middle row, so no reflected cell is ever clipped;
  * the shape's vertical extent, which always spans the marker row and never
    touches the top or bottom edge. About 80% of random samples place the
    extent off-centre relative to the marker row (as in all train pairs), so
    the marker, not the shape's own bounding box, must be used as the centre;
    the rest may be centred (as in the test pair);
  * a tapered row-depth profile with occasional jitter. Every row touches the
    line, and random shapes keep columns 0 and 1 empty, as in the fixtures;
  * the colouring style: border thickness, depth layers or row bands (up to
    five inner bands), and an optional spine column next to the line in its
    own colour;
  * 0-2 interior holes and an optional fringed end row (as in train 1), with
    the shape kept 4-connected.
  The shape colours come from {0,1,2,3,5,6,9}. A shape always has at least
  two colours in random mode. Every shape (random or explicit) differs from
  its own reflection about the marker row in at least MIN_MARGIN cells, so
  the 180-degree rotation is clearly separated from a plain left-right
  mirror. The line, marker and background colours are fixed at 4, 8 and 7,
  as in the task.
  Original fixtures are rebuilt from explicit shape rows (size, top, rows).
  Explicit shapes must be 4-connected and must leave (cy, 1) empty so they
  never touch the left edge marker.
"""

import copy
import random

import common

BG = 7
LINE = 4
MARK = 8
PALETTE = [0, 1, 2, 3, 5, 6, 9]
MIN_MARGIN = 3
OFF_CENTRE_RATE = 0.8


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _connected(cells):
  """True if the cell set forms one 4-connected component."""
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    y, x = stack.pop()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
      p = (y + dy, x + dx)
      if p in cells and p not in seen:
        seen.add(p)
        stack.append(p)
  return len(seen) == len(cells)


def _margin(cells, cy):
  """Counts shape cells whose reflection about row cy differs in colour."""
  return sum(1 for (y, x), col in cells.items()
             if cells.get((2 * cy - y, x)) != col)


def _parse_rows(width, height, top, rows):
  """Turns shape strings ('.' means background) into a cell dict.

  Each string covers columns 0..cx-1 and is left-padded with background.
  Raises ValueError for malformed rows, for shapes that would collide with
  the line, the markers, column 0 or the top/bottom rows, for shapes that do
  not span the marker row, for rows that do not touch the line, for reserved
  colours, for a cell at (cy, 1) touching the edge marker, for shapes that
  are not 4-connected, and for shapes that differ from their reflection
  about the marker row in fewer than MIN_MARGIN cells (rotation would be
  too close to a plain mirror).
  """
  c = (width - 1) // 2
  cy = (height - 1) // 2
  if not _is_int(top):
    raise ValueError("top must be an integer")
  if not isinstance(rows, (list, tuple)) or not rows:
    raise ValueError("rows must be a non-empty list of strings")
  if not all(isinstance(r, str) for r in rows):
    raise ValueError("every element of rows must be a string")
  bottom = top + len(rows) - 1
  if top < 1 or bottom > height - 2:
    raise ValueError("shape rows must avoid the top and bottom grid rows")
  if not top <= cy <= bottom:
    raise ValueError("shape must span the marker row")
  cells = {}
  for i, row in enumerate(rows):
    if not row or len(row) > c:
      raise ValueError("shape rows must be non-empty and left of the line")
    row = row.rjust(c, ".")
    if row[-1] == ".":
      raise ValueError("every shape row must touch the centre line")
    if row[0] != ".":
      raise ValueError("column 0 is reserved for the edge marker column")
    for x, ch in enumerate(row):
      if ch == ".":
        continue
      if not ch.isdigit() or int(ch) not in PALETTE:
        raise ValueError("shape colour must be one of %s" % PALETTE)
      cells[(top + i, x)] = int(ch)
  if (cy, 1) in cells:
    raise ValueError("cell (cy, 1) would touch the left edge marker")
  if not _connected(set(cells)):
    raise ValueError("shape must be one 4-connected component")
  if _margin(cells, cy) < MIN_MARGIN:
    raise ValueError("shape is (nearly) symmetric about the marker row")
  return cells


def _sample_once(width, height):
  """Builds one random tapered, layered shape left of the centre line.

  Returns (cells, top, bottom).
  """
  c = (width - 1) // 2
  cy = (height - 1) // 2
  w = random.randint(min(3, c - 2), c - 2)   # max depth; columns 0, 1 free
  h = random.randint(4, height - 2)
  lo = max(1, cy - h + 1)
  hi = min(cy, height - 1 - h)
  tops = list(range(lo, hi + 1))
  if random.random() < OFF_CENTRE_RATE:
    off = [t for t in tops if 2 * t + h - 1 != 2 * cy]
    if off:
      tops = off
  top = random.choice(tops)
  a, b = random.randint(1, 2), random.randint(1, 2)
  k1, k2 = random.randint(1, 2), random.randint(1, 2)
  depth = []
  for i in range(h):
    d = min(w, a + k1 * i, b + k2 * (h - 1 - i))
    if random.random() < 0.15:
      d += random.choice([-1, 1])
    depth.append(max(1, min(w, d)))
  mode = random.choice(["layers", "bands"])
  ncol = random.randint(2, 6 if mode == "bands" else 4)
  cols = random.sample(PALETTE, ncol)
  border = cols[0]
  inner = cols[1:]
  thick = min(random.choice([1, 1, 2]), max(1, max(depth) - 1))
  layer_w = random.randint(1, 2)
  spine = None
  spare = [p for p in PALETTE if p not in cols]
  if spare and random.random() < 0.4:
    spine = random.choice(spare)
  bands = sorted(random.sample(range(1, h), min(len(inner) - 1, h - 1)))
  cells = {}
  for i in range(h):
    y = top + i
    s = c - depth[i]
    for x in range(s, c):
      dist = x - s
      if dist < thick:
        col = border
      elif spine is not None and x == c - 1:
        col = spine
      elif mode == "layers":
        col = inner[min(len(inner) - 1, (dist - thick) // layer_w)]
      else:
        band = sum(1 for bnd in bands if i >= bnd)
        col = inner[band]
      cells[(y, x)] = col
  # Holes: interior row cells (both row neighbours present), never in the
  # column next to the line, and only if the shape stays 4-connected.
  for _ in range(random.choice([0, 0, 0, 1, 1, 2])):
    options = sorted(p for p in cells if p[1] < c - 1
                     and (p[0], p[1] - 1) in cells
                     and (p[0], p[1] + 1) in cells)
    random.shuffle(options)
    for p in options[:6]:
      trial = dict(cells)
      del trial[p]
      if _connected(trial):
        cells = trial
        break
  # Fringed end row: keep every other cell counted from the line (the cell
  # next to the line is always kept), as in the last row of train 1.
  if random.random() < 0.25:
    y_end = random.choice([top, top + h - 1])
    row = [x for (yy, x) in cells if yy == y_end]
    if len(row) >= 3:
      trial = {p: v for p, v in cells.items()
               if not (p[0] == y_end and (c - 1 - p[1]) % 2 == 1)}
      if _connected(trial):
        cells = trial
  return cells, top, top + h - 1


def _sample_shape(width, height):
  """Samples a multicoloured shape that is clearly not row-symmetric."""
  c = (width - 1) // 2
  cy = (height - 1) // 2
  cells, top, bottom = None, None, None
  for _ in range(60):
    cells, top, bottom = _sample_once(width, height)
    if len(set(cells.values())) >= 2 and _margin(cells, cy) >= MIN_MARGIN:
      return cells
  # Structural fallback on the last random sample (not a fixed scene). Every
  # row owns the cell (y, c-1). For each upper row whose mirror row exists,
  # recolour (y, c-1) to differ from the mirror cell. Then every non-centre
  # row contributes at least one differing cell, and h - 1 >= 3.
  present = sorted(set(cells.values()))
  for y in range(top, cy):
    m = 2 * cy - y
    if (m, c - 1) in cells:
      avoid = cells[(m, c - 1)]
      choices = [p for p in present if p != avoid]
      if not choices:
        choices = [p for p in PALETTE if p != avoid]
      cells[(y, c - 1)] = random.choice(choices)
  if len(set(cells.values())) < 2:
    # Only possible when one side has no mirror rows. The centre-row cell is
    # its own mirror, so recolouring it keeps the margin.
    old = cells[(cy, c - 1)]
    cells[(cy, c - 1)] = random.choice([p for p in PALETTE if p != old])
  return cells


def _odd_choice(lo, hi):
  return random.choice(range(lo, hi + 1, 2))


def generate(size=None, width=None, height=None, top=None, rows=None):
  """Returns an input/output pair for the point-reflection task.

  Args:
    size: Optional odd side length for a square grid. This is shorthand for
      width = height = size. It must agree with width or height if those are
      also given.
    width: Optional odd grid width. Random mode needs 9..29. Explicit rows
      need 7..29. Sampled if omitted in random mode.
    height: Optional odd grid height. Random mode needs 7..29. Explicit rows
      need 5..29. Sampled if omitted in random mode. If neither width nor
      height is given, the grid is square about 60% of the time and
      otherwise strictly non-square.
    top: Row of the first shape string. Required with rows, and rejected
      without rows.
    rows: Optional list of strings that describe the shape in columns
      0..cx-1, with '.' for background and digits for colours. Every row
      must end next to the line, column 0 and cell (cy, 1) must stay empty,
      the rows must span the marker row and avoid the first and last grid
      rows, the shape must be 4-connected, and it must differ from its
      reflection about the marker row in at least MIN_MARGIN cells. If
      omitted, a random shape is built.
  """
  for name, v in (("size", size), ("width", width), ("height", height)):
    if v is not None and not _is_int(v):
      raise ValueError("%s must be an integer" % name)
  if size is not None:
    if (width is not None and width != size) or (
        height is not None and height != size):
      raise ValueError("size conflicts with width/height")
    width = height = size
  if rows is None:
    if top is not None:
      raise ValueError("top is only meaningful together with rows")
    if width is None and height is None:
      width = _odd_choice(9, 29)
      if random.random() < 0.6:
        height = width
      else:
        height = random.choice([v for v in range(9, 30, 2) if v != width])
    elif width is None:
      width = _odd_choice(9, 29)
    elif height is None:
      height = _odd_choice(9, 29)
    if width % 2 != 1 or not 9 <= width <= 29:
      raise ValueError("random generation needs an odd width in 9..29")
    if height % 2 != 1 or not 7 <= height <= 29:
      raise ValueError("random generation needs an odd height in 7..29")
  else:
    if top is None or width is None or height is None:
      raise ValueError("rows requires top and size (or width and height)")
    if width % 2 != 1 or not 7 <= width <= 29:
      raise ValueError("width must be odd and in 7..29")
    if height % 2 != 1 or not 5 <= height <= 29:
      raise ValueError("height must be odd and in 5..29")
  c = (width - 1) // 2
  cy = (height - 1) // 2
  if rows is not None:
    cells = _parse_rows(width, height, top, rows)
  else:
    cells = _sample_shape(width, height)
  g = common.grid(width, height, BG)
  for y in range(height):
    g[y][c] = LINE
  g[cy][0] = MARK
  g[cy][c] = MARK
  g[cy][width - 1] = MARK
  for (y, x), col in cells.items():
    g[y][x] = col
  out = copy.deepcopy(g)
  for (y, x), col in cells.items():
    ny, nx = 2 * cy - y, 2 * c - x
    if 0 <= ny < height and 0 <= nx < width and out[ny][nx] == BG:
      out[ny][nx] = col
  return {"input": g, "output": out}


def validate():
  """Rebuilds the canonical train/test pairs from explicit shape rows."""
  train = [
      generate(size=17, top=3, rows=[
          "......66", ".....611", "....6113", "...61139", "...61399",
          "...61399", "..611399", "...61399", "...61139", "....6113",
          "....6161", ".....6.6"]),
      generate(size=15, top=2, rows=[
          ".....11", "....122", "...1299", "...1299", "..12999",
          "...1299", "...1299", "...1299", "....122", ".....11"]),
      generate(size=17, top=6, rows=[
          "......55", "....5599", "..559911", "..591111", "..591111",
          "..596666", "..596666", "..559966", "....5599", "......55"]),
  ]
  test = [
      generate(size=19, top=2, rows=[
          ".......33", ".....3339", ".....3009", "....33009", "...332229",
          "..3322229", "..3222229", "..3555559", "..3555559", "..3111119",
          "..3111119", "..3311119", "...336669", "....333.9", "......333"]),
  ]
  return {"train": train, "test": test}
