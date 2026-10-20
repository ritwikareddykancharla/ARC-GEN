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

"""ARC task 963f59bc: grow single-cell markers into mirrored copies of a shape.

Rule: the input holds one blue (1) shape, which may fall into several
4-connected pieces, plus single-cell markers of other colours. If a marker's
row crosses the shape's bounding box, the shape is reflected left-right.
Otherwise the marker's column crosses the box, and the shape is reflected
top-bottom. The mirror axis is placed so that the shape cell on the marker's
row or column lands exactly on the marker. The reflected shape is painted in
the marker's colour and clipped to the grid. The original shape is unchanged.

Scope: random scenes build a tight, 8-connected random shape from two king-move
walks (one spanning every row, one spanning every column) plus random 8-adjacent
growth. Its bounding box is 3..5 per side by default (3..8 on request). Each
scene has 1..3 markers by default (up to 4 on request). Every marker sits on a
distinct side of the shape (right, left, below, above) and has a distinct
colour from 2..9. The fixtures show only right and below markers. Left and
above markers are synthetic extensions, and the default side choice is biased
toward right and below. The grid is sized from the space the copies need:
10..30 per side when sampled, or exactly as requested. Sizes outside the
fixtures' 11..16 range are synthetic extensions.

By default, every marker's row (or column) contains exactly one shape cell, as
in all fixtures. The 'nearest cell' tie-break for lines holding several shape
cells is unverified, so such lines are opt-in through allow_multi_anchor.

Every sampled copy fits fully inside the grid and is separated from the shape
by at least one empty line. Copies never overlap the shape, each other or other
markers. On the explicit path such overlaps are rejected, because they would
make the output depend on painting order. A sampled shape is never symmetric
under either axis reflection or 180-degree rotation. Thus its copies distinguish
reflection from translation and 180-degree rotation. Explicit shapes with fully
specified markers retain symmetric cases for canonical reconstruction. Clipped copies are never sampled, but they are
rendered when passed explicitly, as the rule allows.

Role identification: in every emitted input the background (0) is the strict
most frequent colour, and the shape colour (1) strictly outnumbers every
marker colour. Scenes violating this (e.g. tiny explicit grids where the shape
covers most cells) are rejected, since background and shape could not be told
apart from the input alone.
"""

import random

import common


BACKGROUND = 0
SHAPE_COLOR = 1
MARKER_COLORS = (2, 3, 4, 5, 6, 7, 8, 9)
SIDES = ('right', 'left', 'down', 'up')
HORIZONTAL = ('right', 'left')


def _require_int(name, v):
  if type(v) is not int:
    raise ValueError(name + ' must be an int')


def _normalize_cells(seq, k, name):
  """Turn a sequence of k-length int sequences into a list of tuples."""
  if not isinstance(seq, (list, tuple)):
    raise ValueError(name + ' must be a list or tuple')
  out = []
  for p in seq:
    try:
      t = tuple(p)
    except TypeError:
      raise ValueError(name + ' entries must be sequences')
    if len(t) != k:
      raise ValueError(name + ' entries must have length %d' % k)
    for v in t:
      _require_int(name + ' entry', v)
    out.append(t)
  return out


def _bbox(shape):
  rows = [r for r, _ in shape]
  cols = [c for _, c in shape]
  return min(rows), min(cols), max(rows), max(cols)


def _sym_lr(shape):
  _, x0, _, x1 = _bbox(shape)
  s = set(shape)
  return s == {(r, x0 + x1 - c) for r, c in s}


def _sym_ud(shape):
  y0, _, y1, _ = _bbox(shape)
  s = set(shape)
  return s == {(y0 + y1 - r, c) for r, c in s}


def _sym_rot(shape):
  y0, x0, y1, x1 = _bbox(shape)
  s = set(shape)
  return s == {(y0 + y1 - r, x0 + x1 - c) for r, c in s}


def _anchor_cells(shape, my, mx):
  """Shape cells on the marker's row (horizontal) or column (vertical)."""
  y0, x0, y1, x1 = _bbox(shape)
  if y0 <= my <= y1:
    return 'h', [(r, c) for r, c in shape if r == my]
  if x0 <= mx <= x1:
    return 'v', [(r, c) for r, c in shape if c == mx]
  raise ValueError('marker must share a row or column with the shape box')


def _mirror(shape, my, mx):
  """Cells of the shape reflected so that its anchor lands on (my, mx)."""
  kind, cands = _anchor_cells(shape, my, mx)
  if not cands:
    raise ValueError('no shape cell on the marker row or column')
  if kind == 'h':
    _, cx = min(cands, key=lambda p: abs(p[1] - mx))
    s = mx + cx
    return [(r, s - c) for r, c in shape]
  cy, _ = min(cands, key=lambda p: abs(p[0] - my))
  s = my + cy
  return [(s - r, c) for r, c in shape]


def _roles_identifiable(width, height, shape, markers):
  """Background strictly most frequent; shape strictly beats each marker."""
  counts = {}
  for _, _, colour in markers:
    counts[colour] = counts.get(colour, 0) + 1
  n_bg = width * height - len(shape) - len(markers)
  if n_bg <= len(shape):
    return False
  if counts and max(counts.values()) >= len(shape):
    return False
  return True


def _render(width, height, shape, markers, allow_multi_anchor=False):
  """Paint the input and build the output from the latent scene."""
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError('grid size out of range')
  if not shape or len(set(shape)) != len(shape):
    raise ValueError('shape must be a non-empty set of cells')
  if not markers:
    raise ValueError('at least one marker is required')
  for r, c in shape:
    if not (0 <= r < height and 0 <= c < width):
      raise ValueError('shape cell outside grid')
  y0, x0, y1, x1 = _bbox(shape)
  shape_set = set(shape)
  occupied = set(shape)
  inp = common.grid(width, height, BACKGROUND)
  for r, c in shape:
    inp[r][c] = SHAPE_COLOR
  for r, c, colour in markers:
    if not (0 <= r < height and 0 <= c < width):
      raise ValueError('marker outside grid')
    if (r, c) in occupied:
      raise ValueError('marker collides with another cell')
    if y0 <= r <= y1 and x0 <= c <= x1:
      raise ValueError('marker inside the shape bounding box')
    if colour not in MARKER_COLORS:
      raise ValueError('marker colour must be in 2..9')
    _, cands = _anchor_cells(shape, r, c)
    if not cands:
      raise ValueError('no shape cell on the marker row or column')
    if len(cands) != 1 and not allow_multi_anchor:
      raise ValueError('marker line holds several shape cells')
    occupied.add((r, c))
    inp[r][c] = colour
  if not _roles_identifiable(width, height, shape, markers):
    raise ValueError('background must be the strict most frequent colour and the '
                     'shape must outnumber every marker colour')
  marker_cells = {(r, c) for r, c, _ in markers}
  copies = []
  for r, c, colour in markers:
    cells = {(rr, cc) for rr, cc in _mirror(shape, r, c)
             if 0 <= rr < height and 0 <= cc < width}
    if cells & shape_set:
      raise ValueError('a copy overlaps the shape')
    if (cells & marker_cells) - {(r, c)}:
      raise ValueError('a copy covers another marker')
    for other in copies:
      if cells & other:
        raise ValueError('two copies overlap')
    copies.append(cells)
  out = [row[:] for row in inp]
  for (r, c, colour), cells in zip(markers, copies):
    for rr, cc in cells:
      out[rr][cc] = colour
  return {'input': inp, 'output': out}


def _connected8(cells):
  cells = set(cells)
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        p = (r + dr, c + dc)
        if p in cells and p not in seen:
          seen.add(p)
          stack.append(p)
  return len(seen) == len(cells)


def _has_anchor_line(cells, side, allow_multi):
  lines = {}
  if side in HORIZONTAL:
    for r, _ in cells:
      lines[r] = lines.get(r, 0) + 1
  else:
    for _, c in cells:
      lines[c] = lines.get(c, 0) + 1
  if allow_multi:
    return bool(lines)
  return any(v == 1 for v in lines.values())


def _clamp(v, lo, hi):
  return max(lo, min(hi, v))


def _random_shape(bh, bw, sides, allow_multi):
  """Random tight 8-connected shape in a bh x bw box, or None."""
  for _ in range(200):
    cells = set()
    c = random.randrange(bw)
    for r in range(bh):
      cells.add((r, c))
      c = _clamp(c + random.choice((-1, 0, 1)), 0, bw - 1)
    r = random.randrange(bh)
    for c in range(bw):
      cells.add((r, c))
      r = _clamp(r + random.choice((-1, 0, 1)), 0, bh - 1)
    if not _connected8(cells):
      continue
    extra = random.randint(0, max(1, (bh * bw) // 4))
    for _ in range(extra):
      br, bc = random.choice(sorted(cells))
      nr = br + random.choice((-1, 0, 1))
      nc = bc + random.choice((-1, 0, 1))
      if 0 <= nr < bh and 0 <= nc < bw:
        cells.add((nr, nc))
    if len(cells) < 4 or len(cells) > bh * bw - 2:
      continue
    shp = sorted(cells)
    if _sym_rot(shp):
      continue
    if _sym_lr(shp):
      continue
    if _sym_ud(shp):
      continue
    if not all(_has_anchor_line(cells, s, allow_multi) for s in sides):
      continue
    return shp
  return None


def _marker_spot(side, shape, width, height, allow_multi):
  """Random marker cell on a side so the copy fits with a gap, or None."""
  y0, x0, y1, x1 = _bbox(shape)
  if side in HORIZONTAL:
    lines = list(range(y0, y1 + 1))
  else:
    lines = list(range(x0, x1 + 1))
  random.shuffle(lines)
  for line in lines:
    if side in HORIZONTAL:
      vals = [c for r, c in shape if r == line]
    else:
      vals = [r for r, c in shape if c == line]
    if not vals or (len(vals) != 1 and not allow_multi):
      continue
    if side == 'right':
      a = max(vals)
      lo, hi = 2 * x1 + 2 - a, width - 1 + x0 - a
    elif side == 'left':
      a = min(vals)
      lo, hi = x1 - a, 2 * x0 - 2 - a
    elif side == 'down':
      a = max(vals)
      lo, hi = 2 * y1 + 2 - a, height - 1 + y0 - a
    else:
      a = min(vals)
      lo, hi = y1 - a, 2 * y0 - 2 - a
    if lo <= hi:
      v = random.randint(lo, hi)
      return (line, v) if side in HORIZONTAL else (v, line)
  return None


def _side_informative(shape, side):
  return not (_sym_rot(shape) or _sym_lr(shape) or _sym_ud(shape))


def _default_sides(n):
  if n <= 3 and random.random() < 0.6:
    return ['right', 'down', random.choice(['left', 'up'])][:n]
  return random.sample(SIDES, n)


def _pick_size(fixed, minimum):
  if fixed is not None:
    return fixed if fixed >= minimum else None
  lo = max(minimum, 10)
  if lo > 30:
    return None
  return random.randint(lo, 30)


def _markers_for_shape(shape, width, height, num_markers, sides, colors,
                       allow_multi):
  pool = sides if sides is not None else list(SIDES)
  spots = {}
  for side in pool:
    if not _side_informative(shape, side):
      continue
    spot = _marker_spot(side, shape, width, height, allow_multi)
    if spot is not None:
      spots[side] = spot
  if sides is not None:
    if len(spots) != len(sides):
      raise ValueError('a requested side has no room, no anchor line, or '
                       'the shape is symmetric under its reflection')
    chosen = list(sides)
  else:
    feasible = [s for s in SIDES if s in spots]
    if not feasible:
      raise ValueError('no side of the shape can host an informative copy')
    n = num_markers
    if n is None:
      n = len(colors) if colors is not None else random.randint(
          1, min(3, len(feasible)))
    if n > len(feasible):
      raise ValueError('not enough free sides for the requested markers')
    chosen = random.sample(feasible, n)
  cols = colors if colors is not None else random.sample(MARKER_COLORS,
                                                         len(chosen))
  return [(spots[s][0], spots[s][1], c) for s, c in zip(chosen, cols)]


def generate(width=None, height=None, shape=None, markers=None,
             num_markers=None, sides=None, colors=None,
             box_height=None, box_width=None, allow_multi_anchor=False):
  """Build one example.

  Args:
    width: grid width (columns), int 1..30. Sampled from the space the copies
      need when None. Required when shape is given.
    height: grid height (rows), int 1..30. Same rules as width.
    shape: list of absolute (row, col) int cells of the blue shape. If
      markers is None, markers are sampled around this shape.
    markers: list of (row, col, colour) single-cell markers outside the shape
      box, each sharing a row or column with it. Requires shape. Cannot be
      combined with num_markers, sides, colors or box sizes. Scenes whose
      copies overlap the shape, other markers or each other, or where colour
      0 is not the strict most frequent colour, are rejected.
    num_markers: number of markers, int 1..4.
    sides: distinct sides from 'right', 'left', 'down', 'up', one per marker.
    colors: distinct int marker colours from 2..9, one per marker.
    box_height: shape bounding-box height, int 3..8 (random path only).
    box_width: shape bounding-box width, int 3..8 (random path only).
    allow_multi_anchor: bool. If True, marker lines may hold several shape
      cells and the nearest one is the anchor (unverified by the fixtures).
      If False (default), every marker line holds exactly one shape cell.
  """
  if not isinstance(allow_multi_anchor, bool):
    raise ValueError('allow_multi_anchor must be a bool')
  allow_multi = allow_multi_anchor
  for name, v in (('width', width), ('height', height)):
    if v is not None:
      _require_int(name, v)
      if not 1 <= v <= 30:
        raise ValueError('width and height must be in 1..30')
  if sides is not None:
    if not isinstance(sides, (list, tuple)):
      raise ValueError('sides must be a list or tuple')
    sides = list(sides)
    if (not sides or any(not isinstance(s, str) for s in sides)
        or len(set(sides)) != len(sides)
        or any(s not in SIDES for s in sides)):
      raise ValueError('sides must be distinct entries of SIDES')
  if num_markers is not None:
    _require_int('num_markers', num_markers)
    if not 1 <= num_markers <= 4:
      raise ValueError('num_markers must be in 1..4')
    if sides is not None and len(sides) != num_markers:
      raise ValueError('sides length differs from num_markers')
  if colors is not None:
    if not isinstance(colors, (list, tuple)):
      raise ValueError('colors must be a list or tuple')
    colors = list(colors)
    for c in colors:
      _require_int('colour', c)
    if (not 1 <= len(colors) <= 4 or len(set(colors)) != len(colors)
        or any(c not in MARKER_COLORS for c in colors)):
      raise ValueError('colors must be 1..4 distinct values in 2..9')
    if sides is not None and len(colors) != len(sides):
      raise ValueError('colors length differs from sides')
    if num_markers is not None and len(colors) != num_markers:
      raise ValueError('colors length differs from num_markers')
  for name, v in (('box_height', box_height), ('box_width', box_width)):
    if v is not None:
      _require_int(name, v)
      if not 3 <= v <= 8:
        raise ValueError('box sizes must be in 3..8')
  if markers is not None:
    if shape is None:
      raise ValueError('markers require an explicit shape')
    if any(v is not None for v in (num_markers, sides, colors)):
      raise ValueError('markers cannot be combined with sampling controls')
  if shape is not None:
    if width is None or height is None:
      raise ValueError('explicit shape requires width and height')
    if box_height is not None or box_width is not None:
      raise ValueError('box sizes cannot be combined with an explicit shape')
    shape = _normalize_cells(shape, 2, 'shape')
    if not shape:
      raise ValueError('shape must be non-empty')
    if markers is not None:
      return _render(width, height, shape,
                     _normalize_cells(markers, 3, 'markers'), allow_multi)
    return _render(width, height, shape,
                   _markers_for_shape(shape, width, height, num_markers,
                                      sides, colors, allow_multi),
                   allow_multi)
  for _ in range(300):
    if num_markers is not None:
      n = num_markers
    elif sides is not None:
      n = len(sides)
    elif colors is not None:
      n = len(colors)
    else:
      n = random.choice([1, 2, 2, 2, 3])
    sd = list(sides) if sides is not None else _default_sides(n)
    bh = box_height if box_height is not None else random.randint(3, 5)
    bw = box_width if box_width is not None else random.randint(3, 5)
    n_lr = sum(1 for s in sd if s in HORIZONTAL)
    n_ud = n - n_lr
    w = _pick_size(width, bw + (bw + 1) * n_lr)
    h = _pick_size(height, bh + (bh + 1) * n_ud)
    if w is None or h is None:
      continue
    x_lo = bw + 1 if 'left' in sd else 0
    x_hi = w - 1 - 2 * bw if 'right' in sd else w - bw
    y_lo = bh + 1 if 'up' in sd else 0
    y_hi = h - 1 - 2 * bh if 'down' in sd else h - bh
    if x_lo > x_hi or y_lo > y_hi:
      continue
    rel = _random_shape(bh, bw, sd, allow_multi)
    if rel is None:
      continue
    r0 = random.randint(y_lo, y_hi)
    c0 = random.randint(x_lo, x_hi)
    shp = [(r + r0, c + c0) for r, c in rel]
    cols = colors if colors is not None else random.sample(MARKER_COLORS, n)
    placed = []
    for side, colour in zip(sd, cols):
      spot = _marker_spot(side, shp, w, h, allow_multi)
      if spot is None:
        break
      placed.append((spot[0], spot[1], colour))
    if len(placed) != n:
      continue
    if not _roles_identifiable(w, h, shp, placed):
      continue
    return _render(w, h, shp, placed, allow_multi)
  raise ValueError('requested parameters cannot fit in the grid')


def validate():
  """Reconstruct the canonical fixtures through explicit generate calls."""
  train = [
      generate(width=12, height=12,
               shape=[(1, 4), (2, 2), (2, 4), (3, 2), (3, 3), (3, 4), (3, 5),
                      (3, 6), (4, 3)],
               markers=[(8, 5, 2)]),
      generate(width=11, height=12,
               shape=[(4, 1), (4, 2), (5, 2), (6, 1), (6, 2), (6, 3), (6, 4)],
               markers=[(5, 9, 6)]),
      generate(width=13, height=14,
               shape=[(1, 3), (1, 4), (2, 2), (3, 3), (3, 4), (4, 4)],
               markers=[(2, 11, 2), (9, 2, 8)]),
      generate(width=11, height=11,
               shape=[(0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 1), (3, 1),
                      (3, 2), (3, 3)],
               markers=[(2, 7, 3), (10, 0, 8)]),
  ]
  test = [
      generate(width=16, height=14,
               shape=[(1, 3), (2, 2), (2, 3), (3, 0), (3, 1), (3, 3), (4, 2)],
               markers=[(1, 11, 3), (9, 1, 6)]),
  ]
  return {'train': train, 'test': test}
