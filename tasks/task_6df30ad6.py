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

"""ARC-GEN style generator for task 6df30ad6.

Rule: the input holds one large grey (5) 4-connected shape on a black
background, plus a scatter of single-pixel markers in several colours. The
output erases every marker. It also recolours the shape, cell for cell, with
the colour of the marker closest to the shape. Closeness is the king-move
(Chebyshev) distance to the nearest shape cell.

Scope: every original example is 10x10. Random scenes are 10x10 half of the
time. Otherwise each side is drawn from 7..16 as a synthetic extension, and
any side from 5 to 30 may be requested. The shape is a random 4-connected
blob, rectangle or straight line. There are 2 to 4 marker colours by default
(up to 8 on request), and at least 3 markers. Markers may touch the shape
diagonally but never orthogonally. Markers never touch each other, not even
diagonally. In random scenes the minimum distance is 1, 2 or 3. One to three
markers sit at that distance, and all of them share the target colour. Every
other marker is strictly farther away. Each distractor colour appears at
least once, and distractors are often more frequent than the target.

Tie handling: canonical train pair 3 has a tie at distance 2. Colour 4 sits at
(0,2) and (3,2), and colour 3 sits at (0,6). The expected output is 4. That
answer matches taking the first nearest marker in row-major order. Explicit
marker lists are resolved that way, which reproduces the fixture. Random
scenes never contain such ties.
"""

import random

import common


_SHAPE_COLOR = 5
_PALETTE = [1, 2, 3, 4, 6, 7, 8, 9]
_N4 = [(0, 1), (1, 0), (0, -1), (-1, 0)]


def _cheb(r, c, cells):
  return min(max(abs(r - a), abs(c - b)) for a, b in cells)


def _normalize(cells):
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  return sorted((r - r0, c - c0) for r, c in cells)


def _sample_dim():
  return 10 if random.random() < 0.5 else random.randint(7, 16)


def _random_shape(maxh, maxw, shape_cells=None):
  """Returns normalized cells of a random 4-connected shape, or None."""
  if shape_cells is not None:
    if shape_cells > maxh*maxw:
      return None
    cells = {(random.randrange(maxh),random.randrange(maxw))}
    while len(cells)<shape_cells:
      frontier = {(y+dy,x+dx) for y,x in cells for dy,dx in _N4
                  if 0<=y+dy<maxh and 0<=x+dx<maxw} - cells
      cells.add(random.choice(sorted(frontier)))
    return _normalize(cells)
  kind = random.choice(["blob", "blob", "rect", "line"])
  if kind == "rect":
    opts = [(h, w) for h in range(1, min(4, maxh) + 1)
            for w in range(1, min(4, maxw) + 1) if h * w >= 3]
    if not opts:
      return None
    h, w = random.choice(opts)
    return [(r, c) for r in range(h) for c in range(w)]
  if kind == "line":
    vertical = random.random() < 0.5
    limit = min(6, maxh if vertical else maxw)
    if limit < 3:
      return None
    n = random.randint(3, limit)
    if vertical:
      return [(r, 0) for r in range(n)]
    return [(0, c) for c in range(n)]
  bh, bw = random.randint(2, maxh), random.randint(2, maxw)
  size = random.randint(3, min(20, bh * bw))
  cells = {(0, 0)}
  for _ in range(500):
    if len(cells) >= size:
      break
    r, c = random.choice(sorted(cells))
    dr, dc = random.choice(_N4)
    trial = cells | {(r + dr, c + dc)}
    rs = [a for a, _ in trial]
    cs = [b for _, b in trial]
    if max(rs) - min(rs) + 1 <= bh and max(cs) - min(cs) + 1 <= bw:
      cells = trial
  if len(cells) < 3:
    return None
  return _normalize(cells)


def _spaced(r, c, pos):
  return all(max(abs(r - a), abs(c - b)) > 1 for a, b in pos)


def _random_scene(height, width, shape, num_colors, num_markers, target,
                  shape_cells=None):
  """Builds (shape, markers) with a unique nearest-marker colour."""
  cap_side = 12 if shape_cells is not None else 8
  maxh, maxw = min(cap_side, height - 2), min(cap_side, width - 2)
  cap = max(3, min(24, (height * width) // 7))
  for _ in range(400):
    k = (num_colors if num_colors is not None else
         random.randint(2,min(4,num_markers) if num_markers is not None else 4))
    tgt = target if target is not None else random.choice(_PALETTE)
    distractors = random.sample([x for x in _PALETTE if x != tgt], k - 1)
    colours = [tgt] + distractors
    if num_markers is not None:
      want = num_markers
    else:
      want = random.randint(max(3, k), max(3, k, cap))
    if shape is not None:
      cells = list(shape)
    else:
      rel = _random_shape(maxh, maxw, shape_cells)
      if rel is None:
        continue
      sh = max(r for r, _ in rel) + 1
      sw = max(c for _, c in rel) + 1
      if sh > height - 2 or sw > width - 2:
        continue
      top = random.randint(1, height - sh - 1)
      left = random.randint(1, width - sw - 1)
      cells = [(r + top, c + left) for r, c in rel]
    sset = set(cells)
    blocked = set(sset)
    for r, c in cells:
      for dr, dc in _N4:
        blocked.add((r + dr, c + dc))
    dist = {}
    for r in range(height):
      for c in range(width):
        if (r, c) not in blocked:
          dist[(r, c)] = _cheb(r, c, cells)
    if not dist:
      continue
    top_d = max(dist.values())
    choices = sorted({d for d in dist.values() if d <= 3 and d < top_d})
    if not choices:
      continue
    dmin = random.choice(choices)
    near = [p for p, d in dist.items() if d == dmin]
    far = [p for p, d in dist.items() if d > dmin]
    random.shuffle(near)
    random.shuffle(far)
    n_near = random.randint(1, min(3, want - (k - 1)))
    near_pos = []
    for r, c in near:
      if len(near_pos) >= n_near:
        break
      if _spaced(r, c, near_pos):
        near_pos.append((r, c))
    if not near_pos:
      continue
    far_pos = []
    for r, c in far:
      if len(near_pos) + len(far_pos) >= want:
        break
      if _spaced(r, c, near_pos + far_pos):
        far_pos.append((r, c))
    if len(near_pos) + len(far_pos) < want or len(far_pos) < k - 1:
      continue
    markers = [(r, c, tgt) for r, c in near_pos]
    for i, (r, c) in enumerate(far_pos):
      col = distractors[i] if i < k - 1 else random.choice(colours)
      markers.append((r, c, col))
    return cells, markers
  raise ValueError("could not construct a scene with the requested parameters")


def _target_colour(shape, markers):
  """Colour of the nearest marker; ties go to the first in row-major order."""
  best = None
  colour = _SHAPE_COLOR
  for r, c, k in sorted(markers):
    d = _cheb(r, c, shape)
    if best is None or d < best:
      best, colour = d, k
  return colour


def _render(height, width, shape, markers, color):
  grid = common.grid(width, height, 0)
  for r, c in shape:
    grid[r][c] = color
  for r, c, k in markers:
    grid[r][c] = k
  return grid


def generate(width=None, height=None, shape=None, markers=None,
             num_colors=None, num_markers=None, target_color=None,
             shape_cells=None):
  """Generates one input/output pair.

  Args:
    width: grid width. If a shape is given, it defaults to 10, widened to fit
      the shape. Otherwise it is random (10, or 7..16). Allowed range 5..30.
    height: grid height, with the same defaults as width.
    shape: list of absolute (row, col) cells of the grey shape. It should be
      4-connected and have at least 2 cells. If markers is None, random
      markers are built around it.
    markers: list of (row, col, colour) single-pixel markers. This needs
      shape and cannot be combined with num_colors, num_markers or
      target_color.
    num_colors: number of distinct marker colours in a random scene (2..8).
    num_markers: number of markers in a random scene (at least num_colors).
    target_color: colour of the nearest marker(s) in a random scene, taken
      from 1-4 and 6-9.
    shape_cells: exact random blob area in 2..100, using a box up to 12x12.
      Cannot be combined with an explicit shape.

  Returns:
    A dict with "input" and "output" grids.
  """
  if markers is not None:
    if shape is None:
      raise ValueError("markers requires an explicit shape")
    if (num_colors is not None or num_markers is not None or
        target_color is not None):
      raise ValueError("random-scene controls conflict with explicit markers")
  if shape_cells is not None:
    if shape is not None or type(shape_cells) is not int or not 2<=shape_cells<=100:
      raise ValueError("shape_cells requires random shape and integer area 2..100")
  if num_colors is not None and (type(num_colors) is not int or
                                 not 2 <= num_colors <= len(_PALETTE)):
    raise ValueError("num_colors must be in 2..8")
  if target_color is not None and (type(target_color) is not int or
                                   target_color not in _PALETTE):
    raise ValueError("target_color must be a non-grey, non-black colour")
  if num_markers is not None:
    if type(num_markers) is not int or num_markers < max(2, num_colors or 2):
      raise ValueError("num_markers must be at least num_colors")
  if shape is not None:
    shape = [tuple(p) for p in shape]
    if len(set(shape)) < 2:
      raise ValueError("shape needs at least 2 cells")
    if len(set(shape))!=len(shape) or any(type(v) is not int for p in shape for v in p):
      raise ValueError("shape cells must be unique integer coordinates")
    remaining=set(shape);todo=[remaining.pop()]
    while todo:
      y,x=todo.pop()
      for dy,dx in _N4:
        cell=y+dy,x+dx
        if cell in remaining:remaining.remove(cell);todo.append(cell)
    if remaining:
      raise ValueError("shape must be 4-connected")
    if min(min(r, c) for r, c in shape) < 0:
      raise ValueError("shape cells must be non-negative")
    need_h = max(r for r, _ in shape) + 1
    need_w = max(c for _, c in shape) + 1
    height = max(10, need_h) if height is None else height
    width = max(10, need_w) if width is None else width
    if need_h > height or need_w > width:
      raise ValueError("shape does not fit in the grid")
  else:
    height = _sample_dim() if height is None else height
    width = _sample_dim() if width is None else width
  if not (type(height) is int and type(width) is int and
          1 <= height <= 30 and 1 <= width <= 30):
    raise ValueError("grid sides must be in 1..30")
  if markers is None:
    if height < 5 or width < 5:
      raise ValueError("random scenes need sides of at least 5")
    shape, markers = _random_scene(height, width, shape, num_colors,
                                   num_markers, target_color, shape_cells)
  markers = [tuple(m) for m in markers]
  if not markers:
    raise ValueError("at least one marker is required")
  sset = set(shape)
  positions=set()
  for r, c, k in markers:
    if not (type(r) is int and type(c) is int and
            0 <= r < height and 0 <= c < width):
      raise ValueError("marker out of bounds")
    if ((r, c) in sset or (r,c) in positions or type(k) is not int
        or k not in _PALETTE):
      raise ValueError("marker overlaps shape or uses a reserved colour")
    if any((r+dy,c+dx) in sset for dy,dx in _N4):
      raise ValueError("markers must not touch the shape orthogonally")
    # Canonical test markers include a diagonal pair; each is still a
    # separate four-connected singleton.
    if any((r+dy,c+dx) in positions for dy,dx in _N4):
      raise ValueError("markers must be four-connected singletons")
    positions.add((r,c))
  target = _target_colour(shape, markers)
  return {
      "input": _render(height, width, shape, markers, _SHAPE_COLOR),
      "output": _render(height, width, shape, [], target),
  }


def _rect(r0, r1, c0, c1):
  return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(shape=_rect(4, 4, 3, 6), markers=[
          (0, 1, 4), (0, 8, 4), (1, 6, 3), (2, 2, 6), (3, 9, 3), (5, 0, 3),
          (6, 3, 6), (7, 1, 4), (8, 5, 3), (8, 9, 6), (9, 1, 3)]),
      generate(shape=_rect(3, 5, 3, 5), markers=[
          (0, 1, 9), (0, 9, 4), (1, 4, 2), (2, 7, 9), (3, 0, 4), (5, 9, 2),
          (6, 2, 9), (7, 0, 2), (7, 7, 4), (9, 2, 2), (9, 7, 2)]),
      generate(shape=_rect(2, 6, 4, 4), markers=[
          (0, 0, 8), (0, 2, 4), (0, 6, 3), (0, 8, 4), (2, 0, 3), (2, 7, 8),
          (3, 2, 4), (4, 9, 4), (5, 1, 8), (6, 7, 8), (9, 0, 4), (9, 2, 8),
          (9, 5, 3), (9, 8, 4)]),
      generate(shape=_rect(3, 4, 3, 5), markers=[(1, 2, 4), (8, 1, 6)]),
      generate(shape=[(2, 4)] + _rect(3, 3, 3, 5) + _rect(4, 4, 2, 6) +
               _rect(5, 5, 3, 5) + [(6, 4)], markers=[
                   (0, 0, 7), (0, 5, 6), (1, 2, 9), (1, 7, 7), (3, 0, 6),
                   (3, 7, 6), (3, 9, 9), (6, 8, 6), (7, 0, 9), (9, 4, 6),
                   (9, 8, 9)]),
  ]
  test = [
      generate(shape=_rect(2, 2, 4, 5) + _rect(3, 4, 3, 6) +
               _rect(5, 5, 4, 5), markers=[
                   (0, 1, 3), (0, 4, 2), (0, 9, 7), (2, 0, 7), (2, 9, 3),
                   (5, 1, 2), (5, 9, 3), (7, 8, 7), (8, 0, 3), (8, 2, 7),
                   (9, 3, 3), (9, 6, 7), (9, 8, 2)]),
  ]
  return {"train": train, "test": test}
