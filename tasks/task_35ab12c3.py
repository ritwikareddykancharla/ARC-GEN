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

"""ARC-GEN style generator for task 35ab12c3.

Rule: the input is a sparse scatter of pixels on background 0. All pixels of
one colour with two or more pixels are the corners of one figure. The corners
are joined in the order of the shortest closed tour, so an inner corner makes
the outline concave. A two-corner colour gives a single segment. An edge is
drawn only if it is horizontal, vertical or exactly 45 degrees. Other edges are
skipped, so a colour whose corners admit no legal edge keeps only its pixels.
Outlines are painted in ascending colour order.

A colour with exactly one pixel that 8-touches a corner of a multi-pixel
colour is a companion. It draws a copy of that colour's drawn outline cells,
shifted by its own offset from the touched corner. The copy is drawn
underneath: only background cells are coloured. Companions are processed in
ascending colour order. A companion that touches a figure with no legal edges
changes nothing.

Scope: random grids of 12..30 per side. Each scene has 2..4 figures:
  * lattice octagon-family polygons (rectangles, cut corners, diamonds),
  * polygons with dropped corners, which create skipped illegal edges,
  * concave polygons with one notch corner,
  * legal segments,
  * 'scatter' colours whose corners admit no legal edge (distractors).
Each scene also has 0..2 companions (occasionally one attached to a scatter
distractor) and an optional lone isolated pixel. The intended corner order is
constructed explicitly. A small brute-force check only verifies that this
constructed order is the unique shortest closed tour.
"""

import itertools
import math
import random

import common

_DIRS8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0),
          (1, 1)]


def _legal(a, b):
  dy, dx = b[0] - a[0], b[1] - a[1]
  return dy == 0 or dx == 0 or abs(dy) == abs(dx)


def _sgn(v):
  return (v > 0) - (v < 0)


def _edge_cells(order):
  """Cells of the legal edges of the closed outline through order."""
  n = len(order)
  if n < 2:
    return []
  if n == 2:
    pairs = [(order[0], order[1])]
  else:
    pairs = [(order[i], order[(i + 1) % n]) for i in range(n)]
  cells = []
  for a, b in pairs:
    if not _legal(a, b):
      continue
    dy, dx = b[0] - a[0], b[1] - a[1]
    steps = max(abs(dy), abs(dx))
    sy, sx = _sgn(dy), _sgn(dx)
    for k in range(steps + 1):
      cells.append((a[0] + k * sy, a[1] + k * sx))
  return cells


def _cycle_len(pts, idx):
  total = 0.0
  m = len(idx)
  for i in range(m):
    a = pts[idx[i]]
    b = pts[idx[(i + 1) % m]]
    total += math.hypot(a[0] - b[0], a[1] - b[1])
  return total


def _unique_shortest(order):
  """True iff the constructed cyclic order is the unique shortest tour."""
  n = len(order)
  if n < 3:
    return True
  if len(set(order)) != n:
    return False
  target = _cycle_len(order, list(range(n)))
  ties = 0
  for perm in itertools.permutations(range(1, n)):
    if perm[0] > perm[-1]:
      continue
    length = _cycle_len(order, (0,) + perm)
    if length < target - 1e-9:
      return False
    if abs(length - target) <= 1e-9:
      ties += 1
  return ties == 1


def _normalize(pts):
  r0 = min(p[0] for p in pts)
  c0 = min(p[1] for p in pts)
  return [(p[0] - r0, p[1] - c0) for p in pts]


def _octagon(h, w, cuts):
  tl, tr, br, bl = cuts
  raw = [(0, tl), (0, w - 1 - tr), (tr, w - 1), (h - 1 - br, w - 1),
         (h - 1, w - 1 - br), (h - 1, bl), (h - 1 - bl, 0), (tl, 0)]
  verts = []
  for v in raw:
    if not verts or verts[-1] != v:
      verts.append(v)
  while len(verts) > 1 and verts[0] == verts[-1]:
    verts.pop()
  return verts


def _polygon_template(maxh, maxw):
  for _ in range(40):
    h = random.randint(3, maxh)
    w = random.randint(3, maxw)
    cuts = []
    for _ in range(4):
      if random.random() < 0.4:
        cuts.append(0)
      else:
        cuts.append(random.randint(1, max(1, min(h, w) - 1)))
    tl, tr, br, bl = cuts
    if tl + tr > w - 1 or bl + br > w - 1:
      continue
    if tl + bl > h - 1 or tr + br > h - 1:
      continue
    verts = _octagon(h, w, cuts)
    if len(verts) < 3 or len(set(verts)) != len(verts):
      continue
    mode = random.choice(['plain', 'drop', 'notch'])
    if mode == 'drop' or len(verts) > 7:
      n = len(verts)
      lo = max(1, n - 7)
      hi = max(lo, n - 3)
      if n - lo < 3:
        continue
      k = random.randint(lo, hi)
      gone = set(random.sample(range(n), k))
      verts = [v for i, v in enumerate(verts) if i not in gone]
    elif mode == 'notch' and len(verts) <= 6:
      n = len(verts)
      cands = []
      for i in range(n):
        a, b = verts[i], verts[(i + 1) % n]
        if a[0] == b[0] and a[0] in (0, h - 1) and abs(b[1] - a[1]) >= 3:
          cands.append(i)
        elif a[1] == b[1] and a[1] in (0, w - 1) and abs(b[0] - a[0]) >= 3:
          cands.append(i)
      if cands:
        i = random.choice(cands)
        a, b = verts[i], verts[(i + 1) % n]
        if a[0] == b[0]:
          length = abs(b[1] - a[1])
          t = random.randint(1, length - 1)
          d = random.randint(1, max(1, min(length, h - 2)))
          inward = 1 if a[0] == 0 else -1
          p = (a[0] + inward * d, a[1] + _sgn(b[1] - a[1]) * t)
        else:
          length = abs(b[0] - a[0])
          t = random.randint(1, length - 1)
          d = random.randint(1, max(1, min(length, w - 2)))
          inward = 1 if a[1] == 0 else -1
          p = (a[0] + _sgn(b[0] - a[0]) * t, a[1] + inward * d)
        if p in verts:
          continue
        verts = verts[:i + 1] + [p] + verts[i + 1:]
    if len(verts) < 3 or len(verts) > 7:
      continue
    if not _unique_shortest(verts):
      continue
    return _normalize(verts)
  return None


def _segment_template(maxh, maxw):
  dy, dx = random.choice([(0, 1), (1, 0), (1, 1), (1, -1)])
  limit = 12
  if dy:
    limit = min(limit, maxh - 1)
  if dx:
    limit = min(limit, maxw - 1)
  if limit < 2:
    return None
  length = random.randint(2, limit)
  return _normalize([(0, 0), (length * dy, length * dx)])


def _scatter_template():
  for _ in range(40):
    n = random.randint(2, 3)
    pts = [(random.randint(0, 6), random.randint(0, 6)) for _ in range(n)]
    ok = True
    for a, b in itertools.combinations(pts, 2):
      if _legal(a, b) or max(abs(a[0] - b[0]), abs(a[1] - b[1])) < 2:
        ok = False
        break
    if ok:
      return _normalize(pts)
  return None


def _dilate(cells):
  out = set()
  for r, c in cells:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        out.add((r + dr, c + dc))
  return out


def _random_scene(requested_height, requested_width, requested_shapes, requested_companions):
  for _ in range(200):
    height = requested_height if requested_height is not None else random.randint(12,30)
    width = requested_width if requested_width is not None else random.randint(12,30)
    palette = list(range(1, 10))
    random.shuffle(palette)
    n_shapes = requested_shapes if requested_shapes is not None else random.randint(2,4)
    kinds = [random.choice(['polygon', 'polygon', 'segment'])]
    for _ in range(n_shapes - 1):
      kinds.append(random.choice(['polygon', 'polygon', 'segment', 'scatter']))
    shapes, objects, pixels = [], [], set()
    drawable, scatters = [], []
    for kind in kinds:
      maxh, maxw = min(18, height), min(18, width)
      if kind == 'polygon':
        local = _polygon_template(maxh, maxw)
      elif kind == 'segment':
        local = _segment_template(maxh, maxw)
      else:
        local = _scatter_template()
      if local is None:
        continue
      bh = max(p[0] for p in local) + 1
      bw = max(p[1] for p in local) + 1
      if bh > height or bw > width:
        continue
      for _ in range(40):
        r0 = random.randint(0, height - bh)
        c0 = random.randint(0, width - bw)
        verts = [(r + r0, c + c0) for r, c in local]
        foot = set(verts) | set(_edge_cells(verts))
        if any(foot & o['dil'] for o in objects):
          continue
        colour = palette.pop()
        obj = {'foot': foot, 'dil': _dilate(foot), 'colour': colour}
        objects.append(obj)
        shapes.append((colour, verts))
        pixels |= set(verts)
        if _edge_cells(verts):
          drawable.append((colour, verts, obj))
        else:
          scatters.append((colour, verts, obj))
        break
    if not drawable or len(shapes)!=n_shapes:
      continue
    companions = []
    n_comp = requested_companions if requested_companions is not None else random.choice([0,1,1,2,2,2])
    for _ in range(n_comp):
      pool = drawable
      if scatters and random.random() < 0.15:
        pool = scatters
      colour_t, verts, target = random.choice(pool)
      for _ in range(40):
        anchor = random.choice(verts)
        dy, dx = random.choice(_DIRS8)
        q = (anchor[0] + dy, anchor[1] + dx)
        if not (0 <= q[0] < height and 0 <= q[1] < width):
          continue
        if q in target['foot']:
          continue
        if any(q in o['dil'] for o in objects if o is not target):
          continue
        near = set((q[0] + a, q[1] + b) for a, b in _DIRS8) & pixels
        if near != {anchor}:
          continue
        colour = palette.pop()
        objects.append({'foot': {q}, 'dil': _dilate({q}), 'colour': colour})
        pixels.add(q)
        companions.append((colour, anchor[0], anchor[1], dy, dx))
        break
    if len(companions)!=n_comp:continue
    lones = []
    if random.random() < 0.3:
      for _ in range(40):
        q = (random.randint(0, height - 1), random.randint(0, width - 1))
        if any(q in o['dil'] for o in objects):
          continue
        colour = palette.pop()
        objects.append({'foot': {q}, 'dil': _dilate({q}), 'colour': colour})
        pixels.add(q)
        lones.append((colour, q[0], q[1]))
        break
    grid, out = _render(height, width, shapes, companions, lones)
    if grid != out:
      return height, width, shapes, companions, lones
  raise RuntimeError('failed to build a scene')


def _render(height, width, shapes, companions, lones):
  grid = common.grid(width, height, 0)
  cells_of = {}
  for colour, verts in shapes:
    for r, c in verts:
      grid[r][c] = colour
    cells_of[colour] = _edge_cells(verts)
  for colour, r, c in lones:
    grid[r][c] = colour
  for colour, ar, ac, dy, dx in companions:
    grid[ar + dy][ac + dx] = colour
  out = [row[:] for row in grid]
  for colour in sorted(cells_of):
    for r, c in cells_of[colour]:
      out[r][c] = colour
  for colour, ar, ac, dy, dx in sorted(companions):
    target = grid[ar][ac]
    for r, c in cells_of.get(target, []):
      nr, nc = r + dy, c + dx
      if 0 <= nr < height and 0 <= nc < width and out[nr][nc] == 0:
        out[nr][nc] = colour
  return grid, out


def generate(height=None, width=None, shapes=None, companions=None,
             lones=None, num_shapes=None, num_companions=None):
  """Returns an input/output pair for task 35ab12c3.

  Args:
    height: number of rows.
    width: number of columns.
    shapes: list of (colour, [(row, col), ...]) with the corners listed in
      their closed-tour order (the shortest tour).
    companions: list of (colour, anchor_row, anchor_col, dy, dx). The single
      companion pixel sits at anchor + (dy, dx), touching that corner.
    lones: list of (colour, row, col) isolated single pixels.
    num_shapes: exact random figure count, 2..4.
    num_companions: exact random companion count, 0..2.
  """
  for dimension in (height,width):
    if dimension is not None and (not isinstance(dimension,int) or not 1 <= dimension <= 30):
      raise ValueError("Dimensions must be in 1..30")
  if num_shapes is not None and (not isinstance(num_shapes,int) or not 2 <= num_shapes <= 4):
    raise ValueError("num_shapes must be in 2..4")
  if num_companions is not None and (not isinstance(num_companions,int) or not 0 <= num_companions <= 2):
    raise ValueError("num_companions must be in 0..2")
  if shapes is None:
    if companions is not None or lones is not None:
      raise ValueError("Explicit companions and lones require explicit shapes")
    if any(d is not None and d < 12 for d in (height,width)):
      raise ValueError("Random dimensions must be at least 12")
    height, width, shapes, companions, lones = _random_scene(height,width,num_shapes,num_companions)
  elif num_shapes is not None or num_companions is not None:
    raise ValueError("Count controls apply only to random scenes")
  if height is None or width is None or not shapes:
    raise ValueError("Explicit shapes require dimensions and nonempty shapes")
  companions = companions or []
  lones = lones or []
  used={};colours=[]
  for colour,verts in shapes:
    colours.append(colour)
    if not 2 <= len(verts) <= 8 or len(set(verts))!=len(verts):
      raise ValueError("Shapes require 2..8 distinct ordered corners")
    for r,c in verts:
      if not (0 <= r < height and 0 <= c < width) or (r,c) in used:
        raise ValueError("Corner outside canvas or overlapping marker")
      used[r,c]=colour
  for colour,r,c in lones:
    colours.append(colour)
    if not (0 <= r < height and 0 <= c < width) or (r,c) in used:raise ValueError("Invalid lone pixel")
    used[r,c]=colour
  for colour,ar,ac,dy,dx in companions:
    colours.append(colour);r,c=ar+dy,ac+dx
    if (dy,dx) not in _DIRS8 or (ar,ac) not in used or used[ar,ac] not in {v for v,verts in shapes}:
      raise ValueError("Companion must anchor to a shape corner")
    if not (0 <= r < height and 0 <= c < width) or (r,c) in used:raise ValueError("Invalid companion pixel")
    used[r,c]=colour
  if any(c not in range(1,10) for c in colours) or len(set(colours))!=len(colours):
    raise ValueError("Objects require distinct nonzero colours")
  grid, out = _render(height, width, shapes, companions, lones)
  return {'input': grid, 'output': out}


def validate():
  """Reconstructs the canonical examples from explicit latent parameters."""
  train = [
      generate(height=20, width=20, shapes=[
          (3, [(7, 5), (7, 6), (10, 9), (13, 6), (13, 5), (10, 2)]),
          (4, [(17, 5), (17, 12)]),
          (6, [(2, 7), (8, 13), (6, 3)]),
          (8, [(6, 16), (6, 19), (12, 19), (14, 17), (14, 16)]),
      ], companions=[(7, 6, 3, -1, 0), (1, 6, 16, 0, -1)]),
      generate(height=18, width=18, shapes=[
          (3, [(12, 2), (14, 5), (15, 10)]),
          (6, [(5, 11), (5, 13), (8, 16), (12, 11)]),
          (8, [(3, 8), (6, 5), (8, 7)]),
      ], companions=[(1, 3, 8, -1, -1), (4, 5, 11, -1, -1)]),
      generate(height=15, width=15, shapes=[
          (1, [(2, 2), (2, 13), (12, 13), (12, 2)]),
          (2, [(6, 7), (6, 9)]),
          (7, [(4, 4), (4, 10), (5, 11), (10, 6), (10, 4)]),
      ], companions=[(8, 2, 2, -1, -1), (4, 6, 7, 0, -1)]),
  ]
  test = [
      generate(height=21, width=21, shapes=[
          (1, [(2, 7), (17, 7)]),
          (3, [(0, 14), (3, 17), (8, 17), (8, 15), (6, 13), (6, 10),
               (5, 9)]),
          (6, [(2, 3), (17, 3)]),
          (8, [(13, 10), (15, 16), (17, 13)]),
      ], companions=[(4, 2, 3, 1, -1), (7, 2, 7, 0, -1)]),
  ]
  return {'train': train, 'test': test}
