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

"""ARC task 5adee1b2: legend-coloured frames around shapes.

Rule: a legend sits in the bottom-left corner. Each legend entry is a 2-cell
vertical bar of shape colour a in column 0. Next to it, on the same rows, is a
bar of paint colour b in column 1. Entries are stacked upward from the bottom
edge, with one blank row between entries. For every canvas shape of colour a,
grow its bounding box by one cell on each side and clip it at the grid edge.
Inside that box, the background cells that are 4-connected to the box border
through background are painted b. Holes that the shape fully encloses stay 0.
The legend is left unchanged.

Scope of random generation:
- Sides are 14 to 30 by default. Explicit sides of 10 to 30 are accepted.
  Sides other than the fixture sizes (20 and 26) are synthetic extensions.
- There are 1 to 3 legend pairs by default, and 1 to 4 on request. All 2k
  colours are distinct.
- There are 2 to 6 shapes by default, and 1 to 8 on request. Every legend
  colour is used by at least one shape.
- Each shape is one 4-connected component. All shapes of one colour share one
  randomly built, mirror-symmetric template. The template is 4-6 rows by
  3/5/7 columns, and about 70% of templates contain a guaranteed enclosed
  hole.
- Shapes may be cropped by one cell at any grid edge, like the test fixture's
  right-edge shape.
- Grown boxes never overlap each other and never contain legend cells.
- Background 0 is always the most frequent colour.

Not supported: shapes whose colour is missing from the legend, legends
elsewhere than the bottom-left, and multi-colour shapes.
"""

import random

import common

_MIN_SIDE = 10
_MAX_SIDE = 30


def _outside(grid, y0, x0, y1, x1):
  """Background cells in the box that are 4-connected to the box border."""
  seen = set()
  stack = []
  for y in range(y0, y1 + 1):
    for x in range(x0, x1 + 1):
      if (y in (y0, y1) or x in (x0, x1)) and grid[y][x] == 0:
        seen.add((y, x))
        stack.append((y, x))
  while stack:
    y, x = stack.pop()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
      ny, nx = y + dy, x + dx
      if (y0 <= ny <= y1 and x0 <= nx <= x1 and (ny, nx) not in seen
          and grid[ny][nx] == 0):
        seen.add((ny, nx))
        stack.append((ny, nx))
  return seen


def _connected(cells):
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    y, x = stack.pop()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
      n = (y + dy, x + dx)
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _legend_cells(height, legend):
  cells = []
  k = len(legend)
  for i, (a, b) in enumerate(legend):
    top = height - 3 * (k - i) + 1
    for y in (top, top + 1):
      cells.append((y, 0, a))
      cells.append((y, 1, b))
  return cells


def _visible(height, width, shape):
  r, c, _, pattern = shape
  cells = []
  for dr, row in enumerate(pattern):
    for dc, ch in enumerate(row):
      y, x = r + dr, c + dc
      if ch == "#" and 0 <= y < height and 0 <= x < width:
        cells.append((y, x))
  return cells


def _grown_box(height, width, cells):
  ys = [y for y, _ in cells]
  xs = [x for _, x in cells]
  return (max(0, min(ys) - 1), max(0, min(xs) - 1),
          min(height - 1, max(ys) + 1), min(width - 1, max(xs) + 1))


def _to_strings(m):
  return ["".join("#" if v else "." for v in row) for row in m]


def _spine_pattern(h, w, hole):
  """Always-valid symmetric connected template spanning the full h x w box.

  The centre column is the spine. Each row extends symmetrically from it. An
  optional hole is cut from the spine and walled in on both sides.
  """
  cc = w // 2
  half = w // 2
  rad = [random.randint(0, half) for _ in range(h)]
  rad[random.randrange(h)] = half
  hole_rows = []
  if hole and h >= 3 and w >= 3:
    length = random.randint(1, h - 2)
    r0 = random.randint(1, h - 1 - length)
    hole_rows = list(range(r0, r0 + length))
    for r in range(r0 - 1, r0 + length + 1):
      rad[r] = max(rad[r], 1)
  m = [[0] * w for _ in range(h)]
  for r in range(h):
    for c in range(cc - rad[r], cc + rad[r] + 1):
      m[r][c] = 1
  for r in hole_rows:
    m[r][cc] = 0
  return m


def _make_pattern(h, w, hole):
  """Random mirror-symmetric 4-connected template filling an h x w box."""
  for _ in range(300):
    m = [[0] * w for _ in range(h)]
    for r in range(h):
      for c in range((w + 1) // 2):
        v = 1 if random.random() < 0.55 else 0
        m[r][c] = v
        m[r][w - 1 - c] = v
    if hole:
      cc = w // 2
      length = random.randint(1, h - 3)
      r0 = random.randint(1, h - 1 - length)
      for r in range(r0, r0 + length):
        m[r][cc] = 0
        m[r][cc - 1] = 1
        m[r][cc + 1] = 1
      m[r0 - 1][cc] = 1
      m[r0 + length][cc] = 1
    cells = [(r, c) for r in range(h) for c in range(w) if m[r][c]]
    if not any(m[0]) or not any(m[h - 1]):
      continue
    if not any(m[r][0] for r in range(h)):
      continue
    dens = len(cells) / float(h * w)
    if dens < 0.35 or dens > 0.8 or not _connected(cells):
      continue
    pad = [[0] * (w + 2)] + [[0] + row + [0] for row in m] + [[0] * (w + 2)]
    out = _outside(pad, 0, 0, h + 1, w + 1)
    enclosed = any(pad[y][x] == 0 and (y, x) not in out
                   for y in range(1, h + 1) for x in range(1, w + 1))
    if hole and not enclosed:
      continue
    return _to_strings(m)
  return _to_strings(_spine_pattern(h, w, hole))


def _place(height, width, colour, pattern, legend_cells, boxes):
  """Tries to place one shape. Returns (shape, grown_box) or None."""
  h, w = len(pattern), len(pattern[0])
  if h > height or w > width:
    return None
  for _ in range(150):
    r = random.randint(0, height - h)
    c = random.randint(0, width - w)
    if random.random() < 0.15:
      side = random.choice(("top", "bottom", "left", "right"))
      if side == "top":
        r = -1
      elif side == "bottom":
        r = height - h + 1
      elif side == "left":
        c = -1
      else:
        c = width - w + 1
    shape = (r, c, colour, pattern)
    vis = _visible(height, width, shape)
    if len(vis) < 4 or not _connected(vis):
      continue
    ys = [y for y, _ in vis]
    xs = [x for _, x in vis]
    if max(ys) - min(ys) < 1 or max(xs) - min(xs) < 1:
      continue
    box = _grown_box(height, width, vis)
    if any(box[0] <= y <= box[2] and box[1] <= x <= box[3]
           for y, x in legend_cells):
      continue
    if any(not (box[2] < o[0] or o[2] < box[0] or box[3] < o[1]
                or o[3] < box[1]) for o in boxes):
      continue
    return shape, box
  return None


def _background_dominant(height, width, legend, shapes):
  counts = {}
  for a, b in legend:
    counts[a] = counts.get(a, 0) + 2
    counts[b] = counts.get(b, 0) + 2
  for shape in shapes:
    n = len(_visible(height, width, shape))
    counts[shape[2]] = counts.get(shape[2], 0) + n
  zeros = height * width - sum(counts.values())
  return zeros > max(counts.values())


def _random_scene(height, width, legend, num_pairs, num_shapes):
  for attempt in range(300):
    simple = attempt >= 150
    if legend is not None:
      leg = list(legend)
    else:
      if num_pairs is not None:
        k = num_pairs
      else:
        choices = [c for c in (1, 2, 2, 2, 2, 3)
                   if num_shapes is None or c <= num_shapes]
        k = random.choice(choices)
      cols = random.sample(range(1, 10), 2 * k)
      leg = [(cols[2 * i], cols[2 * i + 1]) for i in range(k)]
    k = len(leg)
    H = height if height is not None else random.randint(max(14, 3 * k + 1),
                                                         _MAX_SIDE)
    W = width if width is not None else random.randint(14, _MAX_SIDE)
    if num_shapes is not None:
      n = num_shapes
    elif simple:
      n = max(k, 2)
    else:
      n = random.randint(max(2, k), max(6, k))
    patterns = {}
    used = set()
    for a, _ in leg:
      p = None
      for _ in range(20):
        if simple:
          h, w = 4, 3
        else:
          h = random.randint(4, 6)
          w = random.choice([3, 5, 5, 5, 7])
        p = _make_pattern(h, w, random.random() < 0.7)
        if tuple(p) not in used:
          break
      used.add(tuple(p))
      patterns[a] = p
    shape_colours = [a for a, _ in leg]
    colours = shape_colours + [random.choice(shape_colours)
                               for _ in range(n - k)]
    leg_cells = set((y, x) for y, x, _ in _legend_cells(H, leg))
    boxes = []
    placed = []
    for a in colours:
      res = _place(H, W, a, patterns[a], leg_cells, boxes)
      if res is None:
        break
      placed.append(res[0])
      boxes.append(res[1])
    if len(placed) != len(colours):
      continue
    if not _background_dominant(H, W, leg, placed):
      continue
    random.shuffle(placed)
    return H, W, leg, placed
  raise ValueError("could not place the requested shapes; relax the "
                   "size, legend or shape-count constraints")


def _check_side(value, lo, name):
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError("%s must be an integer" % name)
  if not lo <= value <= _MAX_SIDE:
    raise ValueError("%s must be in [%d, %d]" % (name, lo, _MAX_SIDE))


def _check_legend(legend):
  leg = []
  for pair in legend:
    a, b = pair
    for v in (a, b):
      if isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 9:
        raise ValueError("legend colours must be integers 1..9")
    if a == b:
      raise ValueError("legend shape and paint colours must differ")
    leg.append((a, b))
  if not leg:
    raise ValueError("legend must contain at least one pair")
  if len(set(a for a, _ in leg)) != len(leg):
    raise ValueError("legend shape colours must be distinct")
  return leg


def _check_shapes(shapes, legend):
  keys = set(a for a, _ in legend)
  out = []
  for shape in shapes:
    r, c, colour, pattern = shape
    if colour not in keys:
      raise ValueError("shape colour %r is not in the legend" % (colour,))
    pattern = list(pattern)
    if (not pattern or not pattern[0] or
        any(len(row) != len(pattern[0]) for row in pattern)):
      raise ValueError("shape pattern must be a non-empty rectangle")
    if any(ch not in "#." for row in pattern for ch in row):
      raise ValueError("shape pattern may only contain '#' and '.'")
    out.append((r, c, colour, pattern))
  return out


def _check_layout(height, width, legend, shapes):
  """Validate the visible geometry, including clipped explicit scenes."""
  if not shapes:
    raise ValueError("at least one shape is required")
  legend_cells = {(y, x) for y, x, _ in _legend_cells(height, legend)}
  boxes = []
  for shape in shapes:
    if type(shape[0]) is not int or type(shape[1]) is not int:
      raise ValueError("shape origins must be integers")
    cells = _visible(height, width, shape)
    if not cells or not _connected(cells):
      raise ValueError("visible shape must be nonempty and 4-connected")
    box = _grown_box(height, width, cells)
    if any(box[0] <= y <= box[2] and box[1] <= x <= box[3]
           for y, x in legend_cells):
      raise ValueError("grown shape box intersects the legend")
    if any(not (box[2] < o[0] or o[2] < box[0] or
                box[3] < o[1] or o[3] < box[1]) for o in boxes):
      raise ValueError("grown shape boxes must be disjoint")
    boxes.append(box)
  if not _background_dominant(height, width, legend, shapes):
    raise ValueError("background must be the unique most common colour")


def generate(height=None, width=None, legend=None, shapes=None,
             num_pairs=None, num_shapes=None):
  """Builds one input/output pair.

  Args:
    height: grid height (rows). Random (14..30) if None. Random generation
      accepts explicit values of 10..30. Explicit scenes accept 1..30.
    width: grid width (columns). Same ranges as height.
    legend: list of (shape_colour, paint_colour) pairs, listed top to bottom.
      The bottom pair sits on rows height-2 and height-1, and each earlier
      pair sits three rows higher. Colours are in 1..9 and shape colours are
      distinct. If given without shapes, random shapes are built for this
      legend.
    shapes: list of (row, col, colour, pattern). The pattern is a list of
      strings where '#' marks shape cells. The top-left cell goes at
      (row, col), and any cells outside the grid are cropped. Supplying shapes
      requires height, width and legend. Grown boxes must be disjoint and
      avoid the legend; visible shapes must remain connected.
    num_pairs: number of legend pairs for random generation (1..4). Must
      match len(legend) if both are given.
    num_shapes: number of canvas shapes for random generation (1..8, and at
      least the number of legend pairs). Must match len(shapes) if both are
      given.
  """
  if shapes is not None:
    if height is None or width is None or legend is None:
      raise ValueError("explicit shapes require height, width and legend")
    _check_side(height, 1, "height")
    _check_side(width, 1, "width")
    legend = _check_legend(legend)
    if num_pairs is not None and num_pairs != len(legend):
      raise ValueError("num_pairs does not match legend")
    if num_shapes is not None and num_shapes != len(shapes):
      raise ValueError("num_shapes does not match shapes")
    if 3 * len(legend) - 1 > height or width < 2:
      raise ValueError("legend does not fit in the grid")
    shapes = _check_shapes(shapes, legend)
    _check_layout(height, width, legend, shapes)
  else:
    if height is not None:
      _check_side(height, _MIN_SIDE, "height")
    if width is not None:
      _check_side(width, _MIN_SIDE, "width")
    if legend is not None:
      legend = _check_legend(legend)
      if num_pairs is not None and num_pairs != len(legend):
        raise ValueError("num_pairs does not match legend")
      k = len(legend)
    elif num_pairs is not None:
      if (isinstance(num_pairs, bool) or not isinstance(num_pairs, int)
          or not 1 <= num_pairs <= 4):
        raise ValueError("num_pairs must be in [1, 4]")
      k = num_pairs
    else:
      k = None
    if k is not None:
      if 3 * k + 1 > (height if height is not None else _MAX_SIDE):
        raise ValueError("legend does not fit in the grid height")
    if num_shapes is not None:
      if (isinstance(num_shapes, bool) or not isinstance(num_shapes, int)
          or not 1 <= num_shapes <= 8):
        raise ValueError("num_shapes must be in [1, 8]")
      if k is not None and num_shapes < k:
        raise ValueError("num_shapes must be at least the number of pairs")
    height, width, legend, shapes = _random_scene(height, width, legend,
                                                  num_pairs, num_shapes)
  grid = common.grid(width, height, 0)
  for y, x, v in _legend_cells(height, legend):
    grid[y][x] = v
  for shape in shapes:
    for y, x in _visible(height, width, shape):
      grid[y][x] = shape[2]
  paint = dict(legend)
  out = [row[:] for row in grid]
  for shape in shapes:
    vis = _visible(height, width, shape)
    if not vis:
      continue
    y0, x0, y1, x1 = _grown_box(height, width, vis)
    for y, x in _outside(grid, y0, x0, y1, x1):
      out[y][x] = paint[shape[2]]
  return {"input": grid, "output": out}


def validate():
  """Rebuilds the canonical train and test pairs from explicit latents."""
  p1 = [".###.", ".#.#.", "##.##", ".#.#.", "#####"]
  p2 = ["##.##", ".#.#.", ".###.", "..#..", ".###."]
  p3 = [".#.#.", "#####", ".#.#.", "##.##", ".###."]
  p4 = [".#.#.", ".#.#.", "##.##", ".###.", "..#.."]
  t2 = ["##.##", ".###.", ".#.#.", "##.##", ".###."]
  t4 = [".###.", "##.##", ".#.#.", ".#.#.", "#####"]
  train = [
      generate(height=20, width=20, legend=[(3, 1), (4, 2)],
               shapes=[(2, 3, 3, p1), (2, 12, 4, p2), (11, 8, 4, p2)]),
      generate(height=20, width=20, legend=[(8, 3), (1, 2)],
               shapes=[(2, 3, 8, p3), (1, 12, 8, p3), (8, 10, 1, p4),
                       (15, 7, 1, p4)]),
  ]
  test = [
      generate(height=26, width=26, legend=[(2, 3), (4, 8)],
               shapes=[(2, 2, 2, t2), (2, 10, 4, t4), (3, 19, 2, t2),
                       (11, 22, 4, t4), (12, 5, 2, t2), (18, 14, 4, t4)]),
  ]
  return {"train": train, "test": test}
