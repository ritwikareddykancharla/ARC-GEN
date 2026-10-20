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

"""ARC-GEN style generator for task e9fc42f2 (jigsaw assembly by markers).

Rule: the input has a red (2) background and 2-4 separated pieces. Each piece
has a blue (1) body and some marker cells coloured 3, 4 or 8. A marker colour
that occurs on exactly two pieces is a join. One marker sits on a non-corner
cell of a side of its piece's bounding box. The other sits on the opposite side
of the partner's box. The partner is translated, never rotated, so that the two
markers become orthogonally adjacent. The joins form a tree over the pieces.
The output is the bounding box of the assembled pieces, with red elsewhere. A
marker colour that occurs only once is a lone marker. It links nothing and
simply stays on its piece.

Scope: every original example is 13x13. Random scenes use 13x13 half the time.
Otherwise they use an independently sampled 10..20 width and height, which is a
synthetic extension of the task. Pieces are random connected shapes that span
their own boxes. They are either blobs or rings with gaps. Each box is at least
2x3 or 3x2, because every piece carries a join marker on a non-corner side
cell. Boxes are at most 8 cells long. Each scene has 2-4 pieces linked by a
random tree of join directions. About 60% of trees are path-shaped, so that each
piece has at most two joins, as in the demonstrations. Other trees may be stars,
which is a synthetic extension with up to three joins on one piece.

When a marker colour is still unused (2-3 pieces), an optional lone marker is
added as a distractor. It is usually placed on a non-corner box side, where it
looks like a join marker. Early sampling attempts keep the assembled output no
larger than the input, as in the demonstrations. Later attempts relax that. If
rejection sampling is exhausted, a randomized simple phase builds 3x3 pieces
joined in a straight chain, which never overlap.
"""

import random

import common

BG = 2
BODY = 1
MARKERS = (3, 4, 8)
SIDES = ('up', 'down', 'left', 'right')
OPP = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}
DELTA = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}


def _parse(rows):
  cells = {}
  for r, row in enumerate(rows):
    for c, ch in enumerate(row):
      if ch != '.':
        cells[(r, c)] = int(ch)
  return cells


def _to_rows(shape, h, w):
  out = [['.'] * w for _ in range(h)]
  for (r, c), v in shape.items():
    out[r][c] = str(v)
  return [''.join(row) for row in out]


def _connected(cells):
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
      nb = (r + dr, c + dc)
      if nb in cells and nb not in seen:
        seen.add(nb)
        stack.append(nb)
  return len(seen) == len(cells)


def _spans(cells, h, w):
  rows = {r for r, _ in cells}
  cols = {c for _, c in cells}
  return 0 in rows and h - 1 in rows and 0 in cols and w - 1 in cols


def _inside(r, c, h, w):
  return 0 <= r < h and 0 <= c < w


def _side_cells(side, h, w):
  """Non-corner cells on one side of an h x w box."""
  if side == 'up':
    return [(0, c) for c in range(1, w - 1)]
  if side == 'down':
    return [(h - 1, c) for c in range(1, w - 1)]
  if side == 'left':
    return [(r, 0) for r in range(1, h - 1)]
  return [(r, w - 1) for r in range(1, h - 1)]


def _make_shape(h, w, markers):
  """Random connected piece spanning its h x w box and containing markers."""
  full = [(r, c) for r in range(h) for c in range(w)]
  if h >= 3 and w >= 3 and random.random() < 0.4:
    start = [(r, c) for r, c in full if r in (0, h - 1) or c in (0, w - 1)]
  else:
    start = full
  cells = set(start)
  keep = max(len(markers) + 1, int(len(start) * random.uniform(0.55, 0.9)))
  order = list(start)
  random.shuffle(order)
  for cell in order:
    if len(cells) <= keep:
      break
    if cell in markers:
      continue
    trial = cells - {cell}
    if _spans(trial, h, w) and _connected(trial):
      cells = trial
  return {cell: markers.get(cell, BODY) for cell in cells}


def _place_inputs(dims, width, height):
  """Places piece boxes with at least one background cell between them."""
  for h, w in dims:
    if h > height or w > width:
      return None
  for _ in range(60):
    boxes = []
    for h, w in dims:
      for _ in range(80):
        r = random.randint(0, height - h)
        c = random.randint(0, width - w)
        if all(r + h < br or br + bh < r or c + w < bc or bc + bw < c
               for br, bc, bh, bw in boxes):
          boxes.append((r, c, h, w))
          break
      else:
        break
    if len(boxes) == len(dims):
      return [(b[0], b[1]) for b in boxes]
  # Shelf packing in a random order, used only if random scattering fails.
  idx = list(range(len(dims)))
  random.shuffle(idx)
  spots = [None] * len(dims)
  r = c = shelf = 0
  for i in idx:
    h, w = dims[i]
    if c + w > width:
      r += shelf + 1
      c = 0
      shelf = 0
    if r + h > height:
      return None
    spots[i] = (r, c)
    c += w + 1
    shelf = max(shelf, h)
  return spots


def _try_scene(width, height, n, simple, strict):
  """One attempt at a latent scene. Returns None if a constraint fails."""
  colours = random.sample(MARKERS, n - 1)
  need = [set() for _ in range(n)]
  links = []
  chain_side = random.choice(SIDES)
  path_bias = random.random() < 0.6
  degree = [0] * n
  for child in range(1, n):
    if simple:
      parent, side = child - 1, chain_side
    else:
      cands = list(range(child))
      if path_bias:
        cands = [p for p in cands if degree[p] < 2] or cands
      parent, side = random.choice(cands), random.choice(SIDES)
    degree[parent] += 1
    degree[child] += 1
    links.append((parent, child, side, colours[child - 1]))
    need[parent].add(side)
    need[child].add(OPP[side])
  dims = []
  for i in range(n):
    if simple:
      dims.append((3, 3))
      continue
    h, w = random.randint(2, 5), random.randint(2, 5)
    if random.random() < 0.25:
      if random.random() < 0.5:
        h = random.randint(5, 8)
      else:
        w = random.randint(5, 8)
    if need[i] & {'left', 'right'}:
      h = max(h, 3)
    if need[i] & {'up', 'down'}:
      w = max(w, 3)
    dims.append((h, w))
  markers = [dict() for _ in range(n)]
  joins = []
  for parent, child, side, colour in links:
    cp = [x for x in _side_cells(side, *dims[parent])
          if x not in markers[parent]]
    cc = [x for x in _side_cells(OPP[side], *dims[child])
          if x not in markers[child]]
    if not cp or not cc:
      return None
    mp, mc = random.choice(cp), random.choice(cc)
    markers[parent][mp] = colour
    markers[child][mc] = colour
    joins.append((parent, child, side, mp, mc))
  shapes = [_make_shape(dims[i][0], dims[i][1], markers[i]) for i in range(n)]
  spare = [m for m in MARKERS if m not in colours]
  if spare and random.random() < 0.6:
    i = random.randrange(n)
    h, w = dims[i]
    body = sorted(x for x, v in shapes[i].items() if v == BODY)
    rim = set()
    for s in SIDES:
      rim.update(_side_cells(s, h, w))
    side_body = [x for x in body if x in rim]
    pool = side_body if side_body and random.random() < 0.75 else body
    if len(body) >= 2:
      shapes[i][random.choice(pool)] = random.choice(spare)
  origins = [None] * n
  origins[0] = (0, 0)
  occupied = set(shapes[0])
  for parent, child, side, mp, mc in joins:
    dr, dc = DELTA[side]
    orow = origins[parent][0] + mp[0] + dr - mc[0]
    ocol = origins[parent][1] + mp[1] + dc - mc[1]
    placed = {(orow + r, ocol + c) for r, c in shapes[child]}
    if placed & occupied:
      return None
    occupied |= placed
    origins[child] = (orow, ocol)
  minr = min(r for r, _ in occupied)
  minc = min(c for _, c in occupied)
  out_h = max(r for r, _ in occupied) - minr + 1
  out_w = max(c for _, c in occupied) - minc + 1
  if out_h > 30 or out_w > 30:
    return None
  if strict and (out_h > height or out_w > width):
    return None
  if (out_h, out_w) == (height, width):
    return None
  if 2 * sum(len(s) for s in shapes) >= width * height:
    return None
  spots = _place_inputs(dims, width, height)
  if spots is None:
    return None
  origins = [(r - minr, c - minc) for r, c in origins]
  return [(_to_rows(shapes[i], *dims[i]), spots[i], origins[i])
          for i in range(n)]


def _random_pieces(width, height, num_pieces):
  for attempt in range(500):
    simple = attempt >= 400
    strict = attempt < 300
    if num_pieces is not None:
      n = num_pieces
    elif simple:
      n = 2
    else:
      n = random.choice((2, 3, 3, 4, 4))
    scene = _try_scene(width, height, n, simple, strict)
    if scene is not None:
      return scene
  raise ValueError('could not build a scene for the requested parameters')


def _check_scene(pieces, width, height):
  """Rejects scenes that break the geometric or marker-join invariants."""
  if not 2 <= len(pieces) <= 4:
    raise ValueError('a scene needs 2..4 pieces')
  shapes, dims, outs = [], [], []
  owner = {}
  placed = set()
  for idx, (rows, (ir, ic), (orow, ocol)) in enumerate(pieces):
    if not rows or any(len(row) != len(rows[0]) for row in rows):
      raise ValueError('piece rows must be a non-empty rectangle')
    h, w = len(rows), len(rows[0])
    shape = _parse(rows)
    if not shape:
      raise ValueError('empty piece')
    if not _connected(set(shape)) or not _spans(shape, h, w):
      raise ValueError('piece must be connected and span its box')
    if any(v == BG or not 0 <= v <= 9 for v in shape.values()):
      raise ValueError('invalid piece colour')
    shapes.append(shape)
    dims.append((h, w))
    outs.append((orow, ocol))
    for (r, c) in shape:
      y, x = ir + r, ic + c
      if not (0 <= y < height and 0 <= x < width):
        raise ValueError('piece outside input grid')
      if (y, x) in owner:
        raise ValueError('pieces overlap in input')
      owner[(y, x)] = idx
      cell = (orow + r, ocol + c)
      if cell in placed or cell[0] < 0 or cell[1] < 0:
        raise ValueError('invalid output placement')
      placed.add(cell)
  for (y, x), idx in owner.items():
    for dy, dx in ((1, 0), (0, 1), (-1, 0), (0, -1)):
      other = owner.get((y + dy, x + dx))
      if other is not None and other != idx:
        raise ValueError('pieces touch in input')
  if 2 * len(owner) >= width * height:
    raise ValueError('background must be the majority colour')
  if (max(r for r, _ in placed) >= 30 or max(c for _, c in placed) >= 30):
    raise ValueError('assembled output exceeds 30 cells')
  found = {}
  for idx, shape in enumerate(shapes):
    for cell, v in shape.items():
      if v != BODY:
        found.setdefault(v, []).append((idx, cell))
  adj = {i: set() for i in range(len(shapes))}
  for colour, lst in found.items():
    if len(lst) > 2:
      raise ValueError('a marker colour occurs more than twice')
    if len(lst) < 2:
      continue
    (a, ma), (b, mb) = lst
    if a == b:
      raise ValueError('a join colour occurs twice on one piece')
    ha, wa = dims[a]
    hb, wb = dims[b]
    valid = [(dr, dc) for dr, dc in DELTA.values()
             if not _inside(ma[0] + dr, ma[1] + dc, ha, wa)
             and not _inside(mb[0] - dr, mb[1] - dc, hb, wb)]
    if len(valid) != 1:
      raise ValueError('join direction is missing or ambiguous')
    dr, dc = valid[0]
    target = (outs[a][0] + ma[0] + dr, outs[a][1] + ma[1] + dc)
    if target != (outs[b][0] + mb[0], outs[b][1] + mb[1]):
      raise ValueError('join markers are not adjacent in the output')
    adj[a].add(b)
    adj[b].add(a)
  seen = {0}
  stack = [0]
  while stack:
    for nb in adj[stack.pop()]:
      if nb not in seen:
        seen.add(nb)
        stack.append(nb)
  if len(seen) != len(shapes):
    raise ValueError('joins do not connect all pieces')


def generate(width=None, height=None, num_pieces=None, pieces=None):
  """Returns an input/output pair for the jigsaw assembly task.

  Args:
    width: input grid width, 9..30. If None, a random scene uses 13 or a
      sampled synthetic 10..20. An explicit scene uses 13.
    height: input grid height, 9..30, with the same default as width.
    num_pieces: number of pieces, 2..4, for random scenes. If None, it is
      sampled. If it is given with pieces, it must equal len(pieces).
    pieces: optional explicit latent scene. This is a list of
      (shape_rows, input_origin, output_origin) tuples. shape_rows are strings
      over '.' (background) and digit colours. input_origin is the (row, col)
      of the piece's box in the input. output_origin is the (row, col) of the
      box in the assembled output. The scene is checked against the marker
      join rule. If None, a fresh random scene is built.
  """
  if num_pieces is not None and not 2 <= num_pieces <= 4:
    raise ValueError('num_pieces must be in 2..4')
  if pieces is not None:
    if num_pieces is not None and num_pieces != len(pieces):
      raise ValueError('num_pieces does not match explicit pieces')
    width = 13 if width is None else width
    height = 13 if height is None else height
  elif width is None and height is None:
    if random.random() < 0.5:
      width, height = 13, 13
    else:
      width, height = random.randint(10, 20), random.randint(10, 20)
  else:
    if width is None:
      width = random.randint(10, 20)
    if height is None:
      height = random.randint(10, 20)
  if not (isinstance(width, int) and isinstance(height, int)):
    raise ValueError('width and height must be integers')
  if not (9 <= width <= 30 and 9 <= height <= 30):
    raise ValueError('width and height must be in 9..30')
  if pieces is None:
    pieces = _random_pieces(width, height, num_pieces)
  _check_scene(pieces, width, height)
  grid = common.grid(width, height, BG)
  cells = {}
  for rows, (ir, ic), (orow, ocol) in pieces:
    shape = _parse(rows)
    for (r, c), v in shape.items():
      grid[ir + r][ic + c] = v
      cells[(orow + r, ocol + c)] = v
  minr = min(r for r, _ in cells)
  minc = min(c for _, c in cells)
  out_h = max(r for r, _ in cells) - minr + 1
  out_w = max(c for _, c in cells) - minc + 1
  output = common.grid(out_w, out_h, BG)
  for (r, c), v in cells.items():
    output[r - minr][c - minc] = v
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the original task pairs from explicit latent scenes."""
  train = [
      generate(pieces=[
          (['..1..', '..1..', '11111', '..1..', '..3..'], (0, 2), (0, 0)),
          (['1311', '1..8', '1111'], (7, 7), (5, 1))]),
      generate(pieces=[
          (['.131.', '11.11', '1...1', '11.11', '.111.'], (1, 1), (3, 5)),
          (['111', '8.1', '131'], (3, 7), (0, 6)),
          (['111111', '.....8', '111111'], (7, 4), (0, 0))]),
      generate(pieces=[
          (['111', '1.4', '111'], (1, 1), (0, 0)),
          (['181', '1.1', '1.1', '1.1', '131'], (1, 8), (3, 3)),
          (['111', '4.1', '181'], (5, 3), (0, 3))]),
  ]
  test = [
      generate(pieces=[
          (['1111', '.1..', '1311'], (1, 1), (0, 3)),
          (['131', '1.1', '8.1', '1.1', '1.1', '1.1', '1.4', '111'], (3, 9),
           (3, 3)),
          (['1.1', '1.8', '111', '.1.'], (5, 4), (4, 0))]),
      generate(pieces=[
          (['.1.11', '.1114', '13111'], (1, 0), (0, 1)),
          (['1181', '.11.', '.11.'], (2, 8), (3, 6)),
          (['11111', '4...1', '11811'], (5, 2), (0, 6)),
          (['.131', '1111', '1..1', '1..1', '1..1'], (7, 8), (3, 0))]),
  ]
  return {'train': train, 'test': test}
