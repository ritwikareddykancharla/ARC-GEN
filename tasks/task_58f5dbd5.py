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

"""ARC task 58f5dbd5: stamp same-coloured glyphs as holes into solid squares.

Rule: the input has a background colour, a block of solid 5x5 squares on a
stride-6 lattice (one background cell between neighbours) and a set of 3x3
glyphs. Each glyph is drawn in its own single colour and fills its full 3x3
bounding box, but it need not be connected. Every square colour has a glyph
of the same colour. Extra glyphs whose colour has no square are distractors.
The output is the bounding box of the squares, extended by one background
cell on every side. Inside each square, the inner 3x3 becomes background
exactly where the same-coloured glyph has paint. The glyph is inverted, and
it is never rotated or mirrored.

Scope: a random scene samples the following.
- The background colour.
- A square lattice of 1..4 rows by 1..4 columns, holding 2..9 squares with
  distinct colours. Lattices other than 1x3, 2x2 and 3x2 are synthetic
  extensions.
- 0..3 distractor glyph colours.
- Random glyph shapes, drawn uniformly from every 3..8-cell 3x3 mask that
  touches all four sides of its box.
- The side of the squares that the glyph block sits on (left, right, top or
  bottom), plus the glyph lattice shape, spacing, empty slots, separation
  and margins.
Fixtures are rebuilt from explicit latent square and glyph lists.
"""

import random

import common


def _mask_to_pattern(cells):
  return "/".join("".join("x" if (r, c) in cells else "." for c in range(3))
                  for r in range(3))


def _all_patterns():
  """Lists every 3..8-cell 3x3 mask whose bounding box is the full 3x3."""
  out = []
  coords = [(r, c) for r in range(3) for c in range(3)]
  for m in range(512):
    cells = {coords[i] for i in range(9) if m >> i & 1}
    if not 3 <= len(cells) <= 8:
      continue
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    if {0, 2} <= rows and {0, 2} <= cols:
      out.append(_mask_to_pattern(cells))
  return out


_PATTERNS = _all_patterns()


def _parse(pattern):
  """Turns 'xx./.x./xxx' into a list of (dy, dx) painted offsets."""
  cells = []
  rows = pattern.split("/")
  if len(rows) != 3 or any(len(row) != 3 for row in rows):
    raise ValueError("glyph pattern must be 3x3: %r" % pattern)
  if any(ch not in ".x0123456789" for row in rows for ch in row):
    raise ValueError("glyph must contain dots, x or colour digits")
  for r, row in enumerate(rows):
    for c, ch in enumerate(row):
      if ch != ".":
        cells.append((r, c))
  if not cells or {min(y for y,x in cells),max(y for y,x in cells)}!={0,2} or {min(x for y,x in cells),max(x for y,x in cells)}!={0,2}:
    raise ValueError("glyph must fill its 3x3 bounding box")
  return cells


def _draw(width, height, bg, squares, glyphs):
  grid = common.grid(width, height, bg)
  for (r, c, color) in squares:
    for dy in range(5):
      for dx in range(5):
        grid[r + dy][c + dx] = color
  for (r, c, color, pattern) in glyphs:
    for dy, dx in _parse(pattern):
      grid[r + dy][c + dx] = color
  return grid


def _bg_dominant(grid, bg):
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  return all(counts[bg] > n for v, n in counts.items() if v != bg)


def _random_scene(bg, rows_n, cols_n, num_distractors, side, fixed_width, fixed_height):
  """Samples a latent scene and honours every control that is not None."""
  for _ in range(2000):
    b = bg if bg is not None else random.randint(0, 9)
    rn = rows_n if rows_n is not None else random.randint(1, 4)
    cn = cols_n if cols_n is not None else random.randint(1, 4)
    n = rn * cn
    if n > 9:
      continue
    if n < 2 and (rows_n is None or cols_n is None):
      continue
    if num_distractors is not None:
      extra = num_distractors
    else:
      extra = random.randint(0, min(3, 9 - n))
    if n + extra > 9:
      continue
    palette = [c for c in range(10) if c != b]
    random.shuffle(palette)
    sq_colors = palette[:n]
    gl_colors = palette[:n + extra]
    random.shuffle(gl_colors)
    ng = len(gl_colors)
    gx, gy = random.choice([1, 2]), random.choice([1, 2])
    sd = side if side is not None else random.choice(
        ["left", "right", "top", "bottom"])
    sq_w, sq_h = 6 * cn - 1, 6 * rn - 1
    if sd in ("left", "right"):
      g_cols = random.randint(1, min(3, ng))
      g_rows = (ng + g_cols - 1) // g_cols
    else:
      g_rows = random.randint(1, min(3, ng))
      g_cols = (ng + g_rows - 1) // g_rows
    if random.random() < 0.3:
      # Optional spare slots, so the glyph lattice has holes.
      if sd in ("left", "right"):
        g_rows += 1
      else:
        g_cols += 1
    g_w = 3 * g_cols + gx * (g_cols - 1)
    g_h = 3 * g_rows + gy * (g_rows - 1)
    sep = random.randint(1, 3)
    if sd in ("left", "right"):
      in_w, in_h = g_w + sep + sq_w, max(g_h, sq_h)
    else:
      in_w, in_h = max(g_w, sq_w), g_h + sep + sq_h
    width = fixed_width if fixed_width is not None else in_w + 2 + random.randint(0, 2)
    height = fixed_height if fixed_height is not None else in_h + 2 + random.randint(0, 2)
    if width > 30 or height > 30 or width < in_w+2 or height < in_h+2:
      continue
    ox = random.randint(0, width - 2 - in_w)
    oy = random.randint(0, height - 2 - in_h)
    if sd in ("left", "right"):
      gy0 = 1 + oy + random.randint(0, in_h - g_h)
      sy0 = 1 + oy + random.randint(0, in_h - sq_h)
      if sd == "left":
        gx0, sx0 = 1 + ox, 1 + ox + g_w + sep
      else:
        sx0, gx0 = 1 + ox, 1 + ox + sq_w + sep
    else:
      gx0 = 1 + ox + random.randint(0, in_w - g_w)
      sx0 = 1 + ox + random.randint(0, in_w - sq_w)
      if sd == "top":
        gy0, sy0 = 1 + oy, 1 + oy + g_h + sep
      else:
        sy0, gy0 = 1 + oy, 1 + oy + sq_h + sep
    squares = []
    k = 0
    for i in range(rn):
      for j in range(cn):
        squares.append((sy0 + 6 * i, sx0 + 6 * j, sq_colors[k]))
        k += 1
    slots = [(i, j) for i in range(g_rows) for j in range(g_cols)]
    random.shuffle(slots)
    glyphs = []
    for color, (i, j) in zip(gl_colors, slots):
      glyphs.append((gy0 + (3 + gy) * i, gx0 + (3 + gx) * j, color,
                     random.choice(_PATTERNS)))
    if not _bg_dominant(_draw(width, height, b, squares, glyphs), b):
      continue
    return width, height, b, squares, glyphs
  raise ValueError("cannot fit a scene with the requested controls")


def _check_explicit(width, height, bg, squares, glyphs):
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("grid size out of range")
  if not squares:
    raise ValueError("need at least one square")
  if len({color for r,c,color in squares})!=len(squares):
    raise ValueError("squares must have distinct colours")
  occupied=set()
  for (r, c, color) in squares:
    if color not in range(10):
      raise ValueError("square colour outside 0..9")
    cells={(r+y,c+x) for y in range(5) for x in range(5)}
    if occupied & cells:
      raise ValueError("squares overlap")
    occupied |= cells
    if r < 1 or c < 1 or r + 5 > height - 1 or c + 5 > width - 1:
      raise ValueError("square needs a one-cell margin inside the grid")
    if color == bg:
      raise ValueError("square colour equals background")
  crop_y0=min(r for r,c,color in squares)-1
  crop_x0=min(c for r,c,color in squares)-1
  crop_y1=max(r for r,c,color in squares)+5
  crop_x1=max(c for r,c,color in squares)+5
  colors = [g[2] for g in glyphs]
  if len(set(colors)) != len(colors):
    raise ValueError("one glyph per colour")
  for (r, c, color, pattern) in glyphs:
    if color not in range(10):
      raise ValueError("glyph colour outside 0..9")
    cells={(r+y,c+x) for y,x in _parse(pattern)}
    if cells & occupied:
      raise ValueError("glyph overlaps another object")
    if any(crop_y0<=y<=crop_y1 and crop_x0<=x<=crop_x1 for y,x in cells):
      raise ValueError("glyphs must lie outside the output crop")
    occupied |= cells
    if r < 0 or c < 0 or r + 3 > height or c + 3 > width or color == bg:
      raise ValueError("bad glyph placement or colour")
  for (_, _, color) in squares:
    if color not in colors:
      raise ValueError("every square colour needs a glyph")


def generate(width=None, height=None, bg=None, squares=None, glyphs=None,
             rows=None, cols=None, num_distractors=None, side=None):
  """Builds one input/output pair.

  Args:
    width: grid width in columns; fixes the canvas in random mode too.
    height: grid height in rows; fixes the canvas in random mode too.
    bg: background colour. It works with both explicit and random scenes.
    squares: list of (row, col, colour) top-left corners of solid 5x5
      squares (explicit scene only).
    glyphs: list of (row, col, colour, pattern) 3x3 glyphs. The pattern is a
      string like '11./.1./111', where '.' means background (explicit scene
      only).
    rows: number of square-lattice rows, 1..4 (random scene control).
    cols: number of square-lattice columns, 1..4 (random scene control). The
      product rows*cols must be at most 9.
    num_distractors: number of glyphs whose colour has no square (random
      scene control).
    side: 'left', 'right', 'top' or 'bottom', giving where the glyph block
      lies relative to the squares (random scene control).
  """
  for value in (width,height):
    if value is not None and (not isinstance(value,int) or not 1<=value<=30):
      raise ValueError("grid sides must be integers in 1..30")
  if bg is not None and (not isinstance(bg,int) or bg not in range(10)):
    raise ValueError("bg must be 0..9")
  explicit = [width, height, squares, glyphs]
  if squares is not None or glyphs is not None:
    if any(v is None for v in explicit) or bg is None:
      raise ValueError("explicit scenes need width, height, bg, squares, "
                       "glyphs together")
    if any(v is not None for v in (rows, cols, num_distractors, side)):
      raise ValueError("random controls cannot be combined with an explicit "
                       "scene")
    _check_explicit(width, height, bg, squares, glyphs)
  else:
    if bg is not None and not 0 <= bg <= 9:
      raise ValueError("bg must be 0..9")
    for v in (rows, cols):
      if v is not None and not 1 <= v <= 4:
        raise ValueError("rows/cols must be 1..4")
    if rows is not None and cols is not None and rows * cols > 9:
      raise ValueError("at most 9 squares")
    if num_distractors is not None and not 0 <= num_distractors <= 7:
      raise ValueError("num_distractors must be 0..7")
    if side is not None and side not in ("left", "right", "top", "bottom"):
      raise ValueError("bad side")
    width, height, bg, squares, glyphs = _random_scene(
        bg, rows, cols, num_distractors, side, width, height)
  grid = _draw(width, height, bg, squares, glyphs)
  shapes = {color: _parse(pattern) for (_, _, color, pattern) in glyphs}
  y0 = min(r for r, _, _ in squares) - 1
  x0 = min(c for _, c, _ in squares) - 1
  y1 = max(r for r, _, _ in squares) + 5
  x1 = max(c for _, c, _ in squares) + 5
  output = common.grid(x1 - x0 + 1, y1 - y0 + 1, bg)
  for (r, c, color) in squares:
    for dy in range(5):
      for dx in range(5):
        output[r + dy - y0][c + dx - x0] = color
    for dy, dx in shapes.get(color, []):
      output[r + 1 + dy - y0][c + 1 + dx - x0] = bg
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=19, height=19, bg=8,
               squares=[(1, 13, 1), (7, 13, 6), (13, 13, 4)],
               glyphs=[(1, 1, 4, "444/4.4/4.4"), (1, 6, 3, "3.3/.33/3.."),
                       (5, 1, 1, "111/.1./111"), (10, 1, 9, "999/9.9/.9."),
                       (15, 1, 6, "6.6/66./6.."),
                       (15, 6, 5, "55./.55/5.5")]),
      generate(width=19, height=19, bg=4,
               squares=[(1, 1, 1), (1, 7, 2), (1, 13, 3)],
               glyphs=[(8, 1, 1, "11./.1./111"), (8, 5, 6, "66./6.6/.66"),
                       (8, 9, 8, "888/.8./888"), (12, 1, 3, "3.3/333/.33"),
                       (12, 5, 2, "2.2/22./2.2"),
                       (12, 9, 9, "9../999/99.")]),
      generate(width=23, height=19, bg=1,
               squares=[(1, 1, 8), (1, 7, 4), (7, 1, 3), (7, 7, 9)],
               glyphs=[(1, 15, 2, "222/2../.22"), (1, 19, 7, "7.7/.7./.7."),
                       (5, 15, 9, "9.9/99./.9."), (5, 19, 5, ".5./5.5/.5."),
                       (9, 15, 8, "88./88./..8"), (9, 19, 6, "666/.66/666"),
                       (13, 15, 4, "4.4/444/.4."),
                       (13, 19, 3, "333/.3./.3.")]),
  ]
  test = [
      generate(width=23, height=19, bg=3,
               squares=[(1, 11, 4), (1, 17, 8), (7, 11, 2), (7, 17, 1),
                        (13, 11, 6), (13, 17, 9)],
               glyphs=[(1, 1, 2, "22./.2./222"), (1, 5, 9, "9../.99/..9"),
                       (5, 1, 5, "5../.55/5.5"), (5, 5, 1, "111/.1./1.1"),
                       (9, 1, 8, "888/8.8/.8."), (9, 5, 7, "77./.77/77."),
                       (13, 1, 6, "6../.66/6.."),
                       (13, 5, 4, "44./.4./.44")]),
  ]
  return {"train": train, "test": test}
