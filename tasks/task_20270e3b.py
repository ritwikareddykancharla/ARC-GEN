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

"""Task 20270e3b: slide two marked pieces together.

Rule: the input holds two pieces of colour 4 on a filler background (colour
1). Each piece carries a marker (colour 7). A marker is a straight run of
cells lying just outside one straight run of the piece's own cells. The two
markers point into their pieces from opposite directions along one axis.
Piece B is translated so that its marked edge covers piece A's marker cells.
Piece A's marked edge then sits where B's marker was. The markers vanish and
the number of 4 cells is unchanged. The output is the bounding box of the
joined object, drawn on the filler colour.

Scope: random scenes build two pieces from several latent families. These are
rectangle outlines, barred frames, combs, U shapes, chamfered frames with
diagonal sides, frames with tails, and random polyominoes. Each piece gets a
random symmetry. A marker run of length 1..4 is placed on matching edges. The
whole scene is optionally transposed, so the join can be horizontal instead
of vertical. The pieces are placed anywhere in the grid without 8-adjacency,
so their bounding boxes may interleave. The output is computed from these
latent cells. Original fixtures are reconstructed through explicit piece
specifications.
"""

import random

import common

PIECE = 4
MARK = 7
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _norm(cells):
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  return {(r - r0, c - c0) for r, c in cells}


def _sym(cells, k):
  out = set()
  for r, c in cells:
    if k & 1:
      r, c = c, r
    if k & 2:
      r = -r
    if k & 4:
      c = -c
    out.add((r, c))
  return _norm(out)


def _outline(h, w):
  return {(r, c) for r in range(h) for c in range(w)
          if r in (0, h - 1) or c in (0, w - 1)}


def _blob():
  bh, bw = random.randint(3, 5), random.randint(3, 6)
  n = random.randint(4, min(14, bh * bw - 2))
  cells = {(random.randrange(bh), random.randrange(bw))}
  for _ in range(600):
    if len(cells) >= n:
      break
    r, c = random.choice(sorted(cells))
    dr, dc = random.choice(DIRS)
    if 0 <= r + dr < bh and 0 <= c + dc < bw:
      cells.add((r + dr, c + dc))
  return cells


def _random_shape():
  kind = random.choice(['frame', 'barred', 'comb', 'u', 'chamfer', 'tail',
                        'blob', 'blob'])
  if kind == 'frame':
    cells = _outline(random.randint(3, 7), random.randint(3, 8))
  elif kind == 'barred':
    h, w = random.randint(3, 6), random.randint(5, 8)
    cells = _outline(h, w)
    col = random.randint(2, w - 3)
    cells |= {(r, col) for r in range(h)}
  elif kind == 'comb':
    h, w = random.randint(3, 5), random.choice([3, 5, 7, 9])
    cells = {(0, c) for c in range(w)}
    cells |= {(r, c) for r in range(h) for c in range(0, w, 2)}
  elif kind == 'u':
    h, w = random.randint(3, 5), random.randint(3, 6)
    cells = {(r, 0) for r in range(h)} | {(r, w - 1) for r in range(h)}
    cells |= {(h - 1, c) for c in range(w)}
  elif kind == 'chamfer':
    h, w = random.randint(4, 6), random.randint(4, 6)
    k = random.randint(1, min(h, w) - 2)
    cells = {(r, 0) for r in range(h)} | {(h - 1, c) for c in range(w)}
    cells |= {(0, c) for c in range(w - k)}
    cells |= {(r, w - 1) for r in range(k, h)}
    cells |= {(i, w - 1 - k + i) for i in range(k + 1)}
  elif kind == 'tail':
    h, w = random.randint(3, 4), random.randint(3, 5)
    cells = _outline(h, w)
    t, u = random.randint(1, 3), random.randint(1, 3)
    cells |= {(h - 1, w - 1 + i) for i in range(1, t + 1)}
    cells |= {(h - 1 + j, w - 1 + t) for j in range(1, u + 1)}
  else:
    cells = _blob()
  return _sym(cells, random.randrange(8))


def _windows(cells, d, length):
  """Horizontal runs of piece cells whose cells at offset -d are empty."""
  out = []
  for r, c in sorted(cells):
    run = [(r, c + i) for i in range(length)]
    if all(q in cells and (q[0] - d[0], q[1] - d[1]) not in cells
           for q in run):
      out.append(run)
  return out


def _cands(marks, cells):
  return [d for d in DIRS
          if all((r + d[0], c + d[1]) in cells for r, c in marks)]


def _pairs(ma, pa, mb, pb):
  return [(a, b) for a in _cands(ma, pa) for b in _cands(mb, pb)
          if a == (-b[0], -b[1])]


def _join(pa, ma, pb, mb):
  """Returns (piece A, shifted piece B) or None if invalid/overlapping."""
  pairs = _pairs(ma, pa, mb, pb)
  if not pairs:
    return None
  db = pairs[0][1]
  a0, b0 = min(ma), min(mb)
  sh = (a0[0] - b0[0] - db[0], a0[1] - b0[1] - db[1])
  pb2 = {(r + sh[0], c + sh[1]) for r, c in pb}
  if pb2 & pa:
    return None
  return pa, pb2


def _place(ga, gb, width, height):
  ha, wa = 1 + max(r for r, _ in ga), 1 + max(c for _, c in ga)
  hb, wb = 1 + max(r for r, _ in gb), 1 + max(c for _, c in gb)
  for _ in range(10):
    if random.random() < 0.5:
      hmin, wmin = ha + hb + 1, max(wa, wb)
    else:
      hmin, wmin = max(ha, hb), wa + wb + 1
    hh = height if height is not None else min(30, hmin + random.randint(0, 3))
    ww = width if width is not None else min(30, wmin + random.randint(0, 4))
    if hh < max(ha, hb) or ww < max(wa, wb) or hh > 30 or ww > 30:
      continue
    for _ in range(80):
      ar, ac = random.randint(0, hh - ha), random.randint(0, ww - wa)
      br, bc = random.randint(0, hh - hb), random.randint(0, ww - wb)
      halo = {(r + ar + dr, c + ac + dc) for r, c in ga
              for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
      if any((r + br, c + bc) in halo for r, c in gb):
        continue
      return hh, ww, (ar, ac), (br, bc)
  return None


def _random_scene(marker_length, transpose, width, height):
  for _ in range(1000):
    length = marker_length or random.choice((1, 1, 2, 2, 3, 3, 4))
    pa, pb = _random_shape(), _random_shape()
    wa = _windows(pa, (-1, 0), length)
    wb = _windows(pb, (1, 0), length)
    if not wa or not wb:
      continue
    ma = [(r + 1, c) for r, c in random.choice(wa)]
    mb = [(r - 1, c) for r, c in random.choice(wb)]
    if _pairs(ma, pa, mb, pb) != [((-1, 0), (1, 0))]:
      continue
    joined = _join(pa, ma, pb, mb)
    if joined is None:
      continue
    allc = joined[0] | joined[1]
    if (max(r for r, _ in allc) - min(r for r, _ in allc) >= 30 or
        max(c for _, c in allc) - min(c for _, c in allc) >= 30):
      continue
    tp = transpose if transpose is not None else random.random() < 0.5
    if tp:
      pa = {(c, r) for r, c in pa}
      pb = {(c, r) for r, c in pb}
      ma = [(c, r) for r, c in ma]
      mb = [(c, r) for r, c in mb]
    groups = []
    for p, m in ((pa, ma), (pb, mb)):
      g = p | set(m)
      r0 = min(r for r, _ in g)
      c0 = min(c for _, c in g)
      groups.append(({(r - r0, c - c0) for r, c in p},
                     sorted((r - r0, c - c0) for r, c in m)))
    ga = groups[0][0] | set(groups[0][1])
    gb = groups[1][0] | set(groups[1][1])
    placed = _place(ga, gb, width, height)
    if placed is None:
      continue
    hh, ww, (ar, ac), (br, bc) = placed
    pa = {(r + ar, c + ac) for r, c in groups[0][0]}
    ma = [(r + ar, c + ac) for r, c in groups[0][1]]
    pb = {(r + br, c + bc) for r, c in groups[1][0]}
    mb = [(r + br, c + bc) for r, c in groups[1][1]]
    return hh, ww, pa, ma, pb, mb
  raise RuntimeError('could not build a valid scene')


def _parse(spec):
  top, left, rows = spec
  cells, marks = set(), []
  for r, row in enumerate(rows):
    for c, ch in enumerate(row):
      if ch == '#':
        cells.add((top + r, left + c))
      elif ch == 'm':
        marks.append((top + r, left + c))
  return cells, sorted(marks)


def generate(width=None, height=None, fill=None, piece_a=None, piece_b=None,
             marker_length=None, transpose=None):
  """Returns an input/output pair.

  Args:
    width: grid width. Required with explicit pieces. Otherwise it is an
      optional size request, and scene construction fails if it cannot fit.
    height: grid height, same semantics as width.
    fill: filler colour (default 1; must not be 4 or 7).
    piece_a: optional (top, left, rows) where rows are strings with '#' for
      piece cells, 'm' for marker cells and '.' for cells not in this piece.
    piece_b: second piece in the same format (both pieces must be given to
      use explicit mode).
    marker_length: optional marker run length for random scenes (1..4).
    transpose: optional bool; True makes the join horizontal.
  """
  if fill is None:
    fill = 1
  if fill not in range(10) or fill in (PIECE, MARK):
    raise ValueError('filler colour must be 0..9 and differ from 4 and 7')
  if (piece_a is None) != (piece_b is None):
    raise ValueError('both explicit pieces must be supplied together')
  if marker_length is not None and marker_length not in range(1,5):
    raise ValueError('marker_length must be 1..4')
  if any(v is not None and not 1 <= v <= 30 for v in (width,height)):
    raise ValueError('canvas dimensions must be 1..30')
  if piece_a is None:
    height, width, pa, ma, pb, mb = _random_scene(marker_length, transpose,
                                                   width, height)
  else:
    pa, ma = _parse(piece_a)
    pb, mb = _parse(piece_b)
  joined = _join(pa, ma, pb, mb)
  if joined is None:
    raise ValueError('markers do not define a valid join')
  grid = common.grid(width, height, fill)
  for r, c in pa | pb:
    grid[r][c] = PIECE
  for r, c in ma + mb:
    grid[r][c] = MARK
  allc = joined[0] | joined[1]
  r0 = min(r for r, _ in allc)
  c0 = min(c for _, c in allc)
  oh = max(r for r, _ in allc) - r0 + 1
  ow = max(c for _, c in allc) - c0 + 1
  output = common.grid(ow, oh, fill)
  for r, c in allc:
    output[r - r0][c - c0] = PIECE
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the original task pairs from explicit piece latents."""
  train = [
      generate(width=13, height=7,
               piece_a=(0, 0, ['########', '#..mmm.#', '#......#',
                               '#......#', '#......#', '#......#',
                               '########']),
               piece_b=(0, 9, ['mmm.', '####', '#..#', '#..#', '.##.'])),
      generate(width=13, height=7,
               piece_a=(0, 0, ['#.....', '######', '...#.#', '.#####',
                               '.#....', '.#....', '.m....']),
               piece_b=(0, 10, ['m.#', '###'])),
      generate(width=3, height=9,
               piece_a=(0, 0, ['###', '#.#', '###', 'mmm']),
               piece_b=(5, 0, ['mmm', '###', '#.#', '###'])),
      generate(width=9, height=7,
               piece_a=(0, 0, ['####..', '#..#..', '######', '.....#',
                               '.....m']),
               piece_b=(4, 2, ['.....##', 'm....#.', '######.'])),
  ]
  test = [
      generate(width=10, height=11,
               piece_a=(0, 0, ['##########', '#.#.#.#m#.', '#.#.#.#.#.',
                               '#.#.#.#.#.']),
               piece_b=(6, 1, ['..m', '#.#', '#.#', '#.#', '###'])),
      generate(width=5, height=11,
               piece_a=(0, 0, ['###..', '#..#.', '#...#', '#####',
                               '...mm']),
               piece_b=(6, 0, ['mm...', '#####', '#...#', '.#..#',
                               '..###'])),
  ]
  return {'train': train, 'test': test}
