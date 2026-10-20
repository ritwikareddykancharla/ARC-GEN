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

"""ARC-GEN style generator for task 8f3a5a89.

Rule: the background is 8. A single 6 marker sits in the bottom-left corner.
There are several 1-objects, each 8-connected. The region is the set of
8-cells reachable from the 6 by 4-connected moves.

- A 1-object survives if any of its cells touches the region, including
  diagonally. Every other 1-object is erased to 8.
- Surviving objects that touch the grid border are walls.
- A region cell becomes 7 if it lies on the grid border or 8-touches a wall
  cell.
- The 6 does not act as a wall. Unreachable 8-pockets and surviving floating
  objects are left unchanged.

For 8-connected objects that are pairwise separated, touching the region
diagonally only is impossible, so the 8-touch and 4-touch survival tests
agree.

Scope:
- Sides are 10..30. Sizes 10..20 match the fixtures. Sizes 21..30 are a
  synthetic extension, sampled about 20% of the time. The grid is often
  square.
- The 6 is always at the bottom-left. The palette {1, 6, 7, 8} is fixed.

Each random scene selects one of four separator modes before retries and
retains that mode while constructing the scene:
- none;
- a full-span line wall, vertical or horizontal, 1..2 thick, with an
  optional one-cell jog;
- an L-shaped corner wall that cuts off the top-left, top-right or
  bottom-right corner;
- a border-attached box that encloses a pocket.

Line and corner separators may carry 1..2 small rectangular bulges that
point into the reachable side.

About 25% of separator placement attempts request an empty unreachable
pocket. Its border cells then stay 8, as in column 11 of the test. Other
attempts request 1..3 objects; at least one must fit, and all are erased.
Rejection sampling changes these proportions among accepted scenes.

The reachable side holds two kinds of objects:
- border-attached walls: rectangles, bars, staircases (including the
  3-cell L-tromino), corner blocks and compound bar+block shapes;
- floating blobs, which never touch the border. They are kept but not
  framed.

The reachable region is recomputed after every placement on that side. A
placement is refused if it would cut an earlier reachable-side object (or
the separator) off from the region. New empty enclosed pockets are allowed.

Some scenes deliberately place a wall two cells from the 6, so the cell
diagonal to the 6 gets framed through that wall. Objects are pairwise
separated, so they never 8-touch, and they never occupy the 6's
8-neighbourhood. The output is always derived from the latent object list
by the rule above.
"""

import random

import common

BG, ONE, MARK, FRAME = 8, 1, 6, 7
SIDES = ("top", "bottom", "left", "right")
N8 = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
MIN_SIDE, MAX_SIDE = 10, 30
SEPARATORS = ("none", "line", "corner", "box")


def _is_int(value):
  return isinstance(value, int) and not isinstance(value, bool)


def _rect_cells(r0, c0, r1, c1):
  return {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}


def _object_cells(rects, h, w):
  if not isinstance(rects, (list, tuple)) or not rects:
    raise ValueError("each object must be a non-empty rectangle list")
  cells = set()
  for rect in rects:
    if (not isinstance(rect, (list, tuple)) or len(rect) != 4 or
        not all(_is_int(v) for v in rect)):
      raise ValueError("rectangles must be integer (r0, c0, r1, c1)")
    r0, c0, r1, c1 = rect
    if r0 > r1 or c0 > c1:
      raise ValueError("rectangle corners out of order: %r" % (rect,))
    if not (0 <= r0 <= r1 < h and 0 <= c0 <= c1 < w):
      raise ValueError("rectangle out of bounds")
    cells |= _rect_cells(r0, c0, r1, c1)
  return cells


def _connected8(cells):
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dy, dx in N8:
      n = (r + dy, c + dx)
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _check_objects(h, w, objects):
  """Rejects explicit object lists that would not be distinct 1-objects."""
  owner = {}
  for i, obj in enumerate(objects):
    if not obj:
      raise ValueError("empty object")
    for r, c in obj:
      if not (0 <= r < h and 0 <= c < w):
        raise ValueError("object cell out of bounds")
      if (r, c) == (h - 1, 0):
        raise ValueError("object overlaps the 6 marker")
      if (r, c) in owner:
        raise ValueError("objects overlap")
      owner[(r, c)] = i
    if not _connected8(obj):
      raise ValueError("object is not 8-connected")
  for (r, c), i in owner.items():
    for dy, dx in N8:
      j = owner.get((r + dy, c + dx))
      if j is not None and j != i:
        raise ValueError("objects 8-touch and would merge")


def _flood(h, w, blocked, start):
  """4-connected flood over cells not in `blocked`, excluding the start."""
  seen = {start}
  stack = [start]
  region = set()
  while stack:
    y, x = stack.pop()
    for dy, dx in N4:
      ny, nx = y + dy, x + dx
      if 0 <= ny < h and 0 <= nx < w and (ny, nx) not in seen:
        if (ny, nx) not in blocked:
          seen.add((ny, nx))
          region.add((ny, nx))
          stack.append((ny, nx))
  return region


def _touches(obj, region):
  return any((r + dy, c + dx) in region for r, c in obj for dy, dx in N8)


def _on_border(h, w, r, c):
  return r in (0, h - 1) or c in (0, w - 1)


def _near_marker(h, r, c):
  """True for the 6 at (h-1, 0) and its 8-neighbourhood."""
  return h - 1 - r <= 1 and c <= 1


def _render(h, w, objects):
  """Builds input/output grids from the latent object cell sets."""
  grid = common.grid(w, h, BG)
  ones = set()
  for obj in objects:
    ones |= obj
  for r, c in ones:
    grid[r][c] = ONE
  marker = (h - 1, 0)
  grid[marker[0]][marker[1]] = MARK
  region = _flood(h, w, ones | {marker}, marker)
  out = [row[:] for row in grid]
  wall = set()
  for obj in objects:
    if not _touches(obj, region):
      for r, c in obj:
        out[r][c] = BG
    elif any(_on_border(h, w, r, c) for r, c in obj):
      wall |= obj
  for r, c in region:
    if _on_border(h, w, r, c) or any((r + dy, c + dx) in wall for dy, dx in N8):
      out[r][c] = FRAME
  return grid, out, wall


def _map(cells, side, h, w):
  """Maps (depth, along) cells measured from `side` into (row, col)."""
  out = set()
  for d, a in cells:
    if side == "top":
      out.add((d, a))
    elif side == "bottom":
      out.add((h - 1 - d, a))
    elif side == "left":
      out.add((a, d))
    else:
      out.add((a, w - 1 - d))
  return out


def _edge_shape(kind, h, w):
  side = random.choice(SIDES)
  D, A = (h, w) if side in ("top", "bottom") else (w, h)
  cells = set()
  if kind == "rect":
    dd = random.randint(1, max(1, D // 3))
    aa = random.randint(1, max(1, A // 3))
    a0 = random.randint(0, A - aa)
    cells = {(d, a) for d in range(dd) for a in range(a0, a0 + aa)}
  elif kind == "bar":
    t = random.randint(1, 2)
    length = random.randint(2, max(2, D // 2))
    a0 = random.randint(0, A - t)
    cells = {(d, a) for d in range(length) for a in range(a0, a0 + t)}
  elif kind == "stair":
    # k == 2 gives the 3-cell L-tromino seen in the fixtures.
    k = random.randint(2, min(6 + D // 10, D - 3, A - 2))
    a0 = random.randint(0, A - k - 1)
    up = random.random() < 0.5
    for i in range(k):
      depth = i + 1 if up else k - i
      cells |= {(d, a0 + i) for d in range(depth)}
    if random.random() < 0.5:
      extra = random.randint(1, k - 1)
      ea = a0 + k if up else a0 - 1
      if 0 <= ea < A:
        cells |= {(d, ea) for d in range(extra)}
  else:  # compound: bar from the edge with a block attached to its side
    t = random.randint(1, 2)
    length = random.randint(3, max(3, D // 2))
    a0 = random.randint(0, A - t)
    cells = {(d, a) for d in range(length) for a in range(a0, a0 + t)}
    bd, ba = random.randint(1, 3), random.randint(1, 3)
    d0 = random.randint(1, length - 1)
    s = a0 - ba if random.random() < 0.5 else a0 + t
    if s < 0 or s + ba > A:
      return None
    cells |= {(d, a) for d in range(d0, d0 + bd) for a in range(s, s + ba)}
  return _map(cells, side, h, w)


def _corner_shape(h, w):
  hh = random.randint(2, max(2, h // 3))
  ww = random.randint(2, max(2, w // 3))
  corner = random.choice(("tl", "tr", "br"))
  r0 = 0 if corner in ("tl", "tr") else h - hh
  c0 = 0 if corner == "tl" else w - ww
  return _rect_cells(r0, c0, r0 + hh - 1, c0 + ww - 1)


def _float_shape(h, w):
  fs = max(3, min(h, w) // 6)
  hh, ww = random.randint(1, fs), random.randint(1, fs)
  r0 = random.randint(1, h - 1 - hh)
  c0 = random.randint(1, w - 1 - ww)
  cells = _rect_cells(r0, c0, r0 + hh - 1, c0 + ww - 1)
  if random.random() < 0.5:
    side = random.choice(SIDES)
    if side == "top":
      nub = (r0 - 1, random.randint(c0, c0 + ww - 1))
    elif side == "bottom":
      nub = (r0 + hh, random.randint(c0, c0 + ww - 1))
    elif side == "left":
      nub = (random.randint(r0, r0 + hh - 1), c0 - 1)
    else:
      nub = (random.randint(r0, r0 + hh - 1), c0 + ww)
    if 1 <= nub[0] <= h - 2 and 1 <= nub[1] <= w - 2:
      cells.add(nub)
  return cells


def _marker_side_shape(h, w):
  """Border wall two cells from the 6, so the cell diagonal to the 6 is
  framed through it (as in the canonical test)."""
  dd, aa = random.randint(1, 3), random.randint(1, 4)
  if random.random() < 0.5:  # bottom edge, starting at column 2
    return _rect_cells(h - dd, 2, h - 1, 2 + aa - 1)
  return _rect_cells(h - 3 - aa + 1, 0, h - 3, dd - 1)  # left edge


def _blob_in(zone):
  """Small rectangle anchored at a random cell of `zone` (may hit border)."""
  r, c = random.choice(sorted(zone))
  hh, ww = random.randint(1, 3), random.randint(1, 3)
  return _rect_cells(r, c, r + hh - 1, c + ww - 1)


def _random_shape(h, w, kind):
  if kind == "corner":
    return _corner_shape(h, w)
  if kind == "float":
    return _float_shape(h, w)
  return _edge_shape(kind, h, w)


def _line_separator(h, w):
  t = random.randint(1, 2)
  jag = random.random() < 0.35
  d = random.choice((-1, 1))
  if random.random() < 0.5:
    c = random.randint(4, w - 5)
    if not jag:
      return _rect_cells(0, c, h - 1, c + t - 1)
    s = random.randint(2, h - 3)
    return (_rect_cells(0, c, s, c + t - 1) |
            _rect_cells(s, c + d, h - 1, c + d + t - 1))
  r = random.randint(4, h - 6)
  if not jag:
    return _rect_cells(r, 0, r + t - 1, w - 1)
  s = random.randint(2, w - 3)
  return (_rect_cells(r, 0, r + t - 1, s) |
          _rect_cells(r + d, s, r + d + t - 1, w - 1))


def _corner_separator(h, w):
  """L-shaped wall from one edge to an adjacent edge, cutting off a corner
  that does not contain the 6."""
  t = random.randint(1, 2)
  pr = random.randint(3, max(3, h // 2 - 1))
  pc = random.randint(3, max(3, w // 2 - 1))
  c0 = w - pc - t
  cells = (_rect_cells(0, c0, pr + t - 1, c0 + t - 1) |
           _rect_cells(pr, c0, pr + t - 1, w - 1))
  corner = random.choice(("tl", "tr", "br"))
  if corner == "tl":
    cells = {(r, w - 1 - c) for r, c in cells}
  elif corner == "br":
    cells = {(h - 1 - r, c) for r, c in cells}
  return cells


def _box_separator(h, w):
  """A U-shaped wall on one edge; with the border it encloses a pocket."""
  side = random.choice(SIDES)
  D, A = (h, w) if side in ("top", "bottom") else (w, h)
  t = random.randint(1, 2)
  iw = random.randint(3, max(3, min(6, A // 3)))
  idp = random.randint(2, max(2, min(5, D // 3)))
  length = iw + 2 * t
  if length > A - 2 or idp + t > D - 3:
    return None
  a0 = random.randint(0, A - length)
  cells = set()
  for d in range(idp + t):
    cells |= {(d, a) for a in range(a0, a0 + t)}
    cells |= {(d, a) for a in range(a0 + length - t, a0 + length)}
  for d in range(idp, idp + t):
    cells |= {(d, a) for a in range(a0, a0 + length)}
  return _map(cells, side, h, w)


def _add_bulges(h, w, sep, marker):
  """Attaches 1..2 small rectangles to the region-facing side of `sep`."""
  sep = set(sep)
  for _ in range(random.randint(1, 2)):
    near = _flood(h, w, sep | {marker}, marker)
    cands = sorted(n for n in near if not _near_marker(h, n[0], n[1]) and
                   any((n[0] + dy, n[1] + dx) in sep for dy, dx in N4))
    if not cands:
      return None
    r, c = random.choice(cands)
    hh, ww = random.randint(1, 3), random.randint(1, 3)
    sy, sx = random.choice((-1, 1)), random.choice((-1, 1))
    cells = {(r + sy * i, c + sx * j) for i in range(hh) for j in range(ww)}
    if any(not (0 <= rr < h and 0 <= cc < w) or _near_marker(h, rr, cc)
           for rr, cc in cells):
      continue
    if not cells <= near | sep:
      continue
    sep |= cells
  return sep


def _try_scene(h, w, sep_mode):
  marker = (h - 1, 0)
  occupied = set()
  objects = []
  kept = []  # objects that must keep touching the reachable region
  everything = {(r, c) for r in range(h) for c in range(w)}
  state = {"near": everything - {marker}}

  def separated(cells, zone):
    if not cells:
      return False
    for r, c in cells:
      if (r, c) not in zone or _near_marker(h, r, c):
        return False
      if (r, c) in occupied:
        return False
      if any((r + dy, c + dx) in occupied for dy, dx in N8):
        return False
    return True

  def place_far(cells, far):
    if not separated(cells, far):
      return False
    objects.append(cells)
    occupied.update(cells)
    return True

  def place_near(cells):
    if not separated(cells, state["near"]):
      return False
    region = _flood(h, w, occupied | cells | {marker}, marker)
    if not all(_touches(obj, region) for obj in kept + [cells]):
      return False
    objects.append(cells)
    kept.append(cells)
    occupied.update(cells)
    state["near"] = region
    return True

  if sep_mode != "none":
    if sep_mode == "line":
      sep = _line_separator(h, w)
    elif sep_mode == "corner":
      sep = _corner_separator(h, w)
    else:
      sep = _box_separator(h, w)
    if not sep or any(_near_marker(h, r, c) for r, c in sep):
      return None
    if sep_mode in ("line", "corner") and random.random() < 0.5:
      sep = _add_bulges(h, w, sep, marker)
      if sep is None:
        return None
    near = _flood(h, w, sep | {marker}, marker)
    far = everything - sep - near - {marker}
    if not far or not _touches(sep, near):
      return None
    objects.append(sep)
    kept.append(sep)
    occupied.update(sep)
    state["near"] = near
    target_far = 0 if random.random() < 0.25 else random.randint(1, 3)
    placed = 0
    for _ in range(200):
      if placed >= target_far:
        break
      if random.random() < 0.5:
        shape = _blob_in(far)
      else:
        kind = random.choice(("rect", "bar", "corner", "float"))
        shape = _random_shape(h, w, kind)
      if shape and place_far(shape, far):
        placed += 1
    if target_far and placed == 0:
      return None
  cap = min(8, 4 + (h * w) // 120)
  target = random.randint(1, cap - 1) if sep_mode != "none" else random.randint(2, cap)
  kinds = ["rect", "bar", "stair", "compound", "corner", "float"]
  placed_near = 0
  if random.random() < 0.3:
    for _ in range(10):
      if place_near(_marker_side_shape(h, w)):
        placed_near += 1
        break
  if random.random() < 0.6:
    for _ in range(40):
      if place_near(_float_shape(h, w)):
        placed_near += 1
        break
  for _ in range(250):
    if placed_near >= target:
      break
    shape = _random_shape(h, w, random.choice(kinds))
    if shape and place_near(shape):
      placed_near += 1
  if placed_near < (1 if sep_mode != "none" else 2):
    return None
  if len(occupied) >= 0.45 * h * w:
    return None
  return objects


def _sample_side():
  if random.random() < 0.8:
    return random.randint(MIN_SIDE, 20)
  return random.randint(21, MAX_SIDE)


def generate(height=None, width=None, objects=None, separator=None):
  """Generates one input/output pair.

  Args:
    height: number of rows, an integer (bool is rejected). Random scenes need
      10..30. When this is omitted, a value is sampled: 10..20 usually,
      21..30 as a synthetic extension.
    width: number of columns, with the same type and range as height.
    objects: optional explicit latent scene, used for fixture reconstruction.
      It is a list of 1-objects, and each object is a list of inclusive
      integer rectangles (r0, c0, r1, c1). Each object must be 8-connected.
      Objects must be pairwise non-8-adjacent and must not cover the marker.
      Both height and width are then required, in 1..30. The 6 marker is
      always placed at (height - 1, 0). This path is permissive: the rule is
      still applied exactly, but wall-less scenes are not rejected.
    separator: random scenes only. It is one of "none", "line", "corner"
      or "box"; None samples a mode. It cannot be combined with `objects`.
  """
  for name, value in (("height", height), ("width", width)):
    if value is not None and not _is_int(value):
      raise ValueError("%s must be an integer" % name)
  if objects is not None:
    if separator is not None:
      raise ValueError("separator applies only to random scenes")
    if height is None or width is None:
      raise ValueError("explicit objects require height and width")
    if not (1 <= height <= 30 and 1 <= width <= 30):
      raise ValueError("grid sides must be in 1..30")
    if not isinstance(objects, (list, tuple)):
      raise ValueError("objects must be a list or tuple")
    cell_objects = [_object_cells(rects, height, width) for rects in objects]
    _check_objects(height, width, cell_objects)
    grid, out, _ = _render(height, width, cell_objects)
    return {"input": grid, "output": out}
  for name, value in (("height", height), ("width", width)):
    if value is not None and not MIN_SIDE <= value <= MAX_SIDE:
      raise ValueError("%s must be in %d..%d" % (name, MIN_SIDE, MAX_SIDE))
  if separator is not None and separator not in SEPARATORS:
    raise ValueError("separator must be one of %r" % (SEPARATORS,))
  if separator is not None:
    mode = separator
  else:
    roll = random.random()
    if roll < 0.4:
      mode = "none"
    elif roll < 0.7:
      mode = "line"
    elif roll < 0.85:
      mode = "corner"
    else:
      mode = "box"
  for _ in range(500):
    if height is None and width is None and random.random() < 0.6:
      h = w = _sample_side()
    else:
      h = height if height is not None else _sample_side()
      w = width if width is not None else _sample_side()
    scene = _try_scene(h, w, mode)
    if scene is None:
      continue
    grid, out, wall = _render(h, w, scene)
    if not wall:
      continue
    return {"input": grid, "output": out}
  raise RuntimeError("could not construct a scene")


def validate():
  """Reconstructs the canonical fixtures from explicit latent objects."""
  train = [
      generate(height=16, width=16, objects=[
          [(0, 6, 15, 6)], [(0, 10, 2, 11)], [(6, 9, 8, 10)],
          [(12, 12, 15, 15)]]),
      generate(height=10, width=10, objects=[
          [(0, 4, 2, 5)], [(2, 9, 4, 9)], [(4, 0, 4, 0)],
          [(8, 6, 8, 6), (9, 5, 9, 6)]]),
      generate(height=20, width=20, objects=[
          [(0, 12, 4, 12)],
          [(3, 0, 3, 0), (4, 0, 4, 1), (5, 0, 5, 2), (6, 0, 6, 3),
           (7, 0, 7, 4), (8, 0, 8, 2)],
          [(9, 10, 9, 10), (10, 9, 11, 10)],
          [(14, 14, 19, 19)]]),
  ]
  test = [
      generate(height=12, width=12, objects=[
          [(0, 10, 3, 10), (4, 7, 5, 10), (6, 8, 6, 10), (7, 10, 8, 10),
           (9, 9, 11, 11)],
          [(11, 2, 11, 5)]]),
  ]
  return {"train": train, "test": test}
