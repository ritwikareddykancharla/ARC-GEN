# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Task 8b9c3697: slide fitting red pieces into comb slots.

Rule: the grid has a background colour, comb objects of one non-red ink
colour, and several red (2) rectangles.

A comb is a straight bar with one overhang cell at each end. Two legs run
perpendicular to the bar, and a depth-1 inner stub sits between the legs. The
empty space in front of the stub is a slot that opens away from the bar.

Every red rectangle is erased to background. A red rectangle is put back only
if all of these hold:
  * it slides in a cardinal direction until its front face meets a comb, and
    it moves at least one step. Other red is ignored during the slide;
  * that face is fully covered by cells of a single comb;
  * the two cells just past the ends of the front strip are not comb, so the
    piece is exactly as wide as what it hits;
  * the landed piece lies inside that comb's bounding box.
In practice the piece lies in a slot lane, is exactly stub-wide, and is
shallow enough to fit between the legs. A fitting piece slides until its front
face touches the stub. Every cell it swept becomes 0, from its original cells
to just behind its landing cells. Every other red piece vanishes.

Scope of random scenes. The following are sampled:
  * grid size;
  * background colour and comb ink;
  * number of combs (2-3);
  * comb orientation (4 directions);
  * gap widths (1-2), stub width (1-3) and leg length (3-4).
Fitting pieces are stub-wide. Their depth runs from 1 up to the full slot depth
(legs - 1). They start outside the comb, sometimes just past the leg tips. In
about 20% of placement proposals they start already between its legs.
Acceptance changes that proportion; it is not a quota on completed scenes.

Distractors are random rectangles plus deliberate near misses:
  * pieces in a slot lane that are too wide, too narrow, or offset by one;
  * width-1 pieces in a leg's lane, which come to rest against the leg tip;
  * pieces in the bar's line beyond an overhang cell, which come to rest
    against the overhang outside the box. The test fixture has such a case.

Random scenes never contain two cases that the fixtures do not show:
  * a stub-wide, in-lane piece that is too deep to fit between the legs;
  * a red piece lying in another piece's sliding path.
Explicit latents may still describe the first case, and the box rule then
makes the piece vanish.

Explicit scenes need at least one comb. Comb bounding boxes must be disjoint
with a one-cell margin. Background must strictly outnumber both ink and red in
the input, so that it is recoverable as the dominant colour.

Explicit scenes can also contain a single comb, no pieces, or only rejected
pieces. With no pieces the output equals the input. A distractor may lie in a
fitting piece's path: all original red is erased first, then the fitting piece
paints its trail and landing. Paths of two fitting pieces may not overlap.

Synthetic extensions:
  * grid sides of 14-30 extend the fixture sizes (19x22, 23x27);
  * leg length 4 and full-depth slot fills are not shown by the fixtures.
"""

import random

import common

_ORIENTS = ('down', 'up', 'right', 'left')
_MOVE = {'down': (-1, 0), 'up': (1, 0), 'right': (0, -1), 'left': (0, 1)}
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SIZES = ((1, 1), (1, 1), (1, 1), (2, 2), (2, 2), (1, 2), (2, 1), (2, 3),
          (3, 2))
_PALETTE = (1, 3, 4, 5, 6, 7, 8, 9)
_RED = 2
_TRAIL = 0
_MIN_SIDE = 14
_MAX_SIDE = 30


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _is_seq(v):
  return isinstance(v, (list, tuple))


def _check_colour(value, name):
  if value is None:
    return
  if not _is_int(value) or not 1 <= value <= 9 or value == _RED:
    raise ValueError('%s must be an int in 1..9 other than 2' % name)


def _dims(comb):
  g1, s, g2, legs = comb[3], comb[4], comb[5], comb[6]
  return g1 + s + g2 + 4, legs + 1


def _to_grid(comb, i, j):
  # Local frame: i = depth away from the bar (bar at i=0), j = along the bar.
  top, left, orient = comb[0], comb[1], comb[2]
  _, depth = _dims(comb)
  if orient == 'down':
    return top + i, left + j
  if orient == 'up':
    return top + depth - 1 - i, left + j
  if orient == 'right':
    return top + j, left + i
  return top + j, left + depth - 1 - i


def _stub_cells(comb):
  g1, s = comb[3], comb[4]
  return [_to_grid(comb, 1, j) for j in range(2 + g1, 2 + g1 + s)]


def _comb_cells(comb):
  length, _ = _dims(comb)
  legs = comb[6]
  local = [(0, j) for j in range(length)]
  for i in range(1, legs + 1):
    local.append((i, 1))
    local.append((i, length - 2))
  return [_to_grid(comb, i, j) for i, j in local] + _stub_cells(comb)


def _comb_box(comb):
  length, depth = _dims(comb)
  top, left = comb[0], comb[1]
  if comb[2] in ('down', 'up'):
    return (top, left, top + depth - 1, left + length - 1)
  return (top, left, top + length - 1, left + depth - 1)


def _local_rect(comb, i0, i1, j0, j1):
  pts = [_to_grid(comb, i, j) for i in (i0, i1) for j in (j0, j1)]
  ys = [p[0] for p in pts]
  xs = [p[1] for p in pts]
  return (min(ys), min(xs), max(ys) - min(ys) + 1, max(xs) - min(xs) + 1)


def _rect_cells(piece):
  top, left, h, w = piece
  return [(top + r, left + c) for r in range(h) for c in range(w)]


def _rect_box(piece):
  top, left, h, w = piece
  return (top, left, top + h - 1, left + w - 1)


def _overlap(a, b, margin):
  return not (a[2] + margin < b[0] or b[2] + margin < a[0] or
              a[3] + margin < b[1] or b[3] + margin < a[1])


def _in_box(cell, box, margin):
  y, x = cell
  return (box[0] - margin <= y <= box[2] + margin and
          box[1] - margin <= x <= box[3] + margin)


def _inside(piece, height, width):
  top, left, h, w = piece
  return (h >= 1 and w >= 1 and top >= 0 and left >= 0 and
          top + h <= height and left + w <= width)


def _halo(cells):
  out = set()
  for y, x in cells:
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        out.add((y + dy, x + dx))
  return out


def _background_dominant(width, height, ink_cells, red_cells):
  """True if background strictly outnumbers ink and red in the input."""
  bg_cells = width * height - ink_cells - red_cells
  return bg_cells > ink_cells and bg_cells > red_cells


def _slide(comb, piece):
  """Distance, swept trail and landing cells of a piece fitting a comb slot."""
  top, left, orient = comb[0], comb[1], comb[2]
  _, depth = _dims(comb)
  ptop, pleft, ph, pw = piece
  if orient == 'down':
    k = ptop - (top + 2)
  elif orient == 'up':
    k = (top + depth - 3) - (ptop + ph - 1)
  elif orient == 'right':
    k = pleft - (left + 2)
  else:
    k = (left + depth - 3) - (pleft + pw - 1)
  dy, dx = _MOVE[orient]
  cells = _rect_cells(piece)
  trail = set()
  for t in range(k + 1):
    for y, x in cells:
      trail.add((y + dy * t, x + dx * t))
  final = [(y + dy * k, x + dx * k) for y, x in cells]
  return k, trail, final


def _probe(piece, owner, boxes, height, width):
  """Lists (dir, k, comb, front, inside_box) for every flush, exact contact."""
  cells = _rect_cells(piece)
  y0, x0, y1, x1 = _rect_box(piece)
  found = []
  for dy, dx in _DIRS:
    k = 0
    escaped = False
    while True:
      nxt = [(y + dy * (k + 1), x + dx * (k + 1)) for y, x in cells]
      if any(not (0 <= y < height and 0 <= x < width) for y, x in nxt):
        escaped = True
        break
      if any(c in owner for c in nxt):
        break
      k += 1
    if escaped or k == 0:
      continue
    if dy:
      fy = (y0 if dy < 0 else y1) + dy * (k + 1)
      front = [(fy, x) for x in range(x0, x1 + 1)]
      ends = [(fy, x0 - 1), (fy, x1 + 1)]
    else:
      fx = (x0 if dx < 0 else x1) + dx * (k + 1)
      front = [(y, fx) for y in range(y0, y1 + 1)]
      ends = [(y0 - 1, fx), (y1 + 1, fx)]
    if not all(c in owner for c in front):
      continue
    ids = set(owner[c] for c in front)
    if len(ids) != 1:
      continue
    if any(c in owner for c in ends):
      continue
    cid = ids.pop()
    inbox = all(_in_box((y + dy * k, x + dx * k), boxes[cid], 0)
                for y, x in cells)
    found.append(((dy, dx), k, cid, frozenset(front), inbox))
  return found


def _fits(piece, owner, boxes, height, width):
  """Constraint check: every (direction, distance, comb) in which piece fits."""
  return [(d, k, cid) for d, k, cid, _, ib in
          _probe(piece, owner, boxes, height, width) if ib]


def _too_deep(piece, owner, boxes, stubs, height, width):
  """True if piece is stub-wide in a slot lane but too deep to fit."""
  return any(not ib and front == stubs[cid] for _, _, cid, front, ib in
             _probe(piece, owner, boxes, height, width))


def _place_match(idx, combs, boxes, owner, stubs, taken, height, width):
  comb = combs[idx]
  g1, s, legs = comb[3], comb[4], comb[6]
  _, depth = _dims(comb)
  j0 = 2 + g1
  for _ in range(30):
    # Slot depth is legs - 1 (rows 2..legs in the local frame).
    dp = random.randint(1, legs - 1)
    if random.random() < 0.2:
      a = random.randint(3, legs)  # already between the legs
    else:
      a = random.randint(depth, depth + 14)  # at or beyond the leg tips
    piece = _local_rect(comb, a, a + dp - 1, j0, j0 + s - 1)
    if not _inside(piece, height, width):
      continue
    cells_list = _rect_cells(piece)
    if any(c in owner for c in _halo(cells_list)):
      continue
    pbox = _rect_box(piece)
    if any(_overlap(pbox, b, 1) for o, b in enumerate(boxes) if o != idx):
      continue
    k, trail, _ = _slide(comb, piece)
    bad = False
    for o, b in enumerate(boxes):
      if o != idx and any(_in_box(c, b, 1) for c in trail):
        bad = True
        break
    if bad:
      continue
    cells = set(cells_list) | trail
    if _halo(cells) & taken:
      continue
    if _fits(piece, owner, boxes, height, width) != [
        (_MOVE[comb[2]], k, idx)]:
      continue
    if _too_deep(piece, owner, boxes, stubs, height, width):
      continue
    return piece, cells
  return None


def _near_miss(comb):
  g1, s = comb[3], comb[4]
  length, depth = _dims(comb)
  j0 = 2 + g1
  kind = random.choice(('wide', 'narrow', 'shift', 'tip', 'overhang'))
  if kind == 'overhang':
    ext = random.randint(1, 2)
    gap = random.randint(1, 10)
    if random.random() < 0.5:
      jb = -1 - gap
      return _local_rect(comb, 0, 0, jb - ext + 1, jb)
    jb = length + gap
    return _local_rect(comb, 0, 0, jb, jb + ext - 1)
  a = random.randint(depth + 1, depth + 14)
  dp = random.randint(1, 2)
  if kind == 'tip':
    jt = random.choice((1, length - 2))
    return _local_rect(comb, a, a + dp - 1, jt, jt)
  if kind == 'wide':
    ww = s + 1
    js = j0 - random.randint(0, 1)
  elif kind == 'narrow':
    if s < 2:
      return None
    ww = random.randint(1, s - 1)
    js = j0 + random.randint(0, s - ww)
  else:
    ww = s
    js = j0 + random.choice((-1, 1))
  return _local_rect(comb, a, a + dp - 1, js, js + ww - 1)


def _place_distractor(combs, boxes, owner, stubs, taken, height, width):
  for _ in range(40):
    if random.random() < 0.5:
      piece = _near_miss(combs[random.randrange(len(combs))])
      if piece is None:
        continue
    else:
      ph, pw = random.choice(_SIZES)
      if ph > height or pw > width:
        continue
      piece = (random.randint(0, height - ph), random.randint(0, width - pw),
               ph, pw)
    if not _inside(piece, height, width):
      continue
    pbox = _rect_box(piece)
    if any(_overlap(pbox, b, 1) for b in boxes):
      continue
    cells = set(_rect_cells(piece))
    if _halo(cells) & taken:
      continue
    if _fits(piece, owner, boxes, height, width):
      continue
    if _too_deep(piece, owner, boxes, stubs, height, width):
      continue
    return piece, cells
  return None


def _random_scene(width, height, background, ink):
  for side in (width, height):
    if side is not None and (not _is_int(side) or
                             not _MIN_SIDE <= side <= _MAX_SIDE):
      raise ValueError('random scenes need sides in %d..%d'
                       % (_MIN_SIDE, _MAX_SIDE))
  if background is not None and ink is not None and ink == background:
    raise ValueError('ink must differ from background')
  for _ in range(500):
    h = height if height is not None else random.randint(_MIN_SIDE, _MAX_SIDE)
    w = width if width is not None else random.randint(_MIN_SIDE, _MAX_SIDE)
    bg = background if background is not None else random.choice(
        [c for c in _PALETTE if c != ink])
    col = ink if ink is not None else random.choice(
        [c for c in _PALETTE if c != bg])
    want = random.choice((2, 2, 3))
    combs, boxes = [], []
    for _ in range(80):
      if len(combs) == want:
        break
      orient = random.choice(_ORIENTS)
      g1 = random.choice((1, 1, 1, 2))
      g2 = random.choice((1, 1, 1, 2))
      s = random.choice((1, 2, 3))
      legs = random.choice((3, 3, 3, 4))
      length, depth = g1 + s + g2 + 4, legs + 1
      if orient in ('down', 'up'):
        bh, bw = depth, length
      else:
        bh, bw = length, depth
      if bh > h or bw > w:
        continue
      top = random.randint(0, h - bh)
      left = random.randint(0, w - bw)
      box = (top, left, top + bh - 1, left + bw - 1)
      if any(_overlap(box, b, 1) for b in boxes):
        continue
      combs.append((top, left, orient, g1, s, g2, legs))
      boxes.append(box)
    if len(combs) < 2:
      continue
    owner = {}
    for idx, comb in enumerate(combs):
      for c in _comb_cells(comb):
        owner[c] = idx
    stubs = [frozenset(_stub_cells(c)) for c in combs]
    pieces, targets, taken = [], [], set()
    order = list(range(len(combs)))
    random.shuffle(order)
    for n, idx in enumerate(order):
      if n and random.random() < 0.25:
        continue
      got = _place_match(idx, combs, boxes, owner, stubs, taken, h, w)
      if got is None:
        continue
      pieces.append(got[0])
      targets.append(idx)
      taken |= got[1]
    if not pieces:
      continue
    want_d = random.randint(3, 9)
    nd = 0
    for _ in range(want_d):
      got = _place_distractor(combs, boxes, owner, stubs, taken, h, w)
      if got is None:
        continue
      pieces.append(got[0])
      targets.append(None)
      taken |= got[1]
      nd += 1
    if nd < 2:
      continue
    red_cells = sum(p[2] * p[3] for p in pieces)
    if not _background_dominant(w, h, len(owner), red_cells):
      continue
    pairs = list(zip(pieces, targets))
    random.shuffle(pairs)
    return (w, h, bg, col, combs, [p for p, _ in pairs],
            [t for _, t in pairs])
  raise RuntimeError('could not construct a valid scene')


def _check_scene(width, height, combs, pieces, targets):
  """Rejects latents that are malformed, touching, or contradict targets."""
  if not _is_seq(combs) or not _is_seq(pieces) or not _is_seq(targets):
    raise ValueError('combs, pieces and targets must be lists or tuples')
  if not combs:
    raise ValueError('at least one comb is required')
  owner, boxes = {}, []
  for idx, comb in enumerate(combs):
    if not _is_seq(comb) or len(comb) != 7:
      raise ValueError('comb %d must be a sequence of 7 fields' % idx)
    top, left, orient, g1, s, g2, legs = comb
    if not isinstance(orient, str) or orient not in _ORIENTS:
      raise ValueError('unknown comb orientation %r' % (orient,))
    if not all(_is_int(v) for v in (top, left, g1, s, g2, legs)):
      raise ValueError('comb %d fields must be ints' % idx)
    if min(g1, s, g2) < 1 or legs < 2:
      raise ValueError('comb %d needs gaps/stub >= 1 and legs >= 2' % idx)
    box = _comb_box(comb)
    if box[0] < 0 or box[1] < 0 or box[2] >= height or box[3] >= width:
      raise ValueError('comb %d leaves the grid' % idx)
    if any(_overlap(box, b, 1) for b in boxes):
      raise ValueError('comb bounding boxes must be disjoint with a margin')
    for c in _comb_cells(comb):
      owner[c] = idx
    boxes.append(box)
  red = set()
  for n, piece in enumerate(pieces):
    if (not _is_seq(piece) or len(piece) != 4 or
        not all(_is_int(v) for v in piece)):
      raise ValueError('piece %d must be four ints' % n)
    piece = tuple(piece)
    if not _inside(piece, height, width):
      raise ValueError('piece %d leaves the grid' % n)
    cells = _rect_cells(piece)
    halo = _halo(cells)
    if any(c in owner for c in halo):
      raise ValueError('piece %d overlaps or touches a comb' % n)
    if halo & red:
      raise ValueError('piece %d overlaps or touches another piece' % n)
    red |= set(cells)
  if not _background_dominant(width, height, len(owner), len(red)):
    raise ValueError('background must strictly outnumber ink and red cells')
  used = set()
  for n, (piece, target) in enumerate(zip(pieces, targets)):
    piece = tuple(piece)
    found = _fits(piece, owner, boxes, height, width)
    if target is None:
      if found:
        raise ValueError('piece %d fits a slot but has no target' % n)
      continue
    if not _is_int(target) or not 0 <= target < len(combs):
      raise ValueError('piece %d has an invalid target' % n)
    k, trail, _ = _slide(combs[target], piece)
    if found != [(_MOVE[combs[target][2]], k, target)]:
      raise ValueError('piece %d does not fit comb %d uniquely'
                       % (n, target))
    if trail & used:
      raise ValueError('paths of fitting pieces overlap')
    used |= trail


def generate(width=None, height=None, background=None, ink=None, combs=None,
             pieces=None, targets=None):
  """Returns an input/output pair for task 8b9c3697.

  Args:
    width: grid width. Sampled from 14..30 if None. Required with combs
      (1..30).
    height: grid height. Sampled from 14..30 if None. Required with combs
      (1..30).
    background: background colour, an int in 1..9 other than 2. Sampled if
      None. Required with combs.
    ink: comb colour, an int in 1..9 other than 2 and the background. Sampled
      if None. Required with combs.
    combs: list of (top, left, orient, gap1, stub_width, gap2, leg_length).
      (top, left) is the corner of the comb's bounding box. orient is the
      direction the legs point: 'down', 'up', 'right' or 'left'. At least one
      comb is needed, and bounding boxes must be disjoint with a one-cell
      margin. If None, a random scene with 2-3 combs is built from
      width/height/background/ink.
    pieces: list of red rectangles (top, left, height, width). Required with
      combs, and must be None otherwise. Background must strictly outnumber
      both red and ink cells.
    targets: per piece, the index of the comb whose slot it fits, or None if
      it should vanish. Defaults to all None with explicit combs, and must be
      None in random mode. Explicit targets are checked against the geometry.
  """
  _check_colour(background, 'background')
  _check_colour(ink, 'ink')
  if combs is None:
    if pieces is not None or targets is not None:
      raise ValueError('pieces/targets require explicit combs')
    (width, height, background, ink, combs, pieces,
     targets) = _random_scene(width, height, background, ink)
  else:
    if (width is None or height is None or background is None or
        ink is None or pieces is None):
      raise ValueError('explicit combs need width, height, background, ink '
                       'and pieces')
    if not (_is_int(width) and _is_int(height) and
            1 <= width <= _MAX_SIDE and 1 <= height <= _MAX_SIDE):
      raise ValueError('grid sides must be ints in 1..30')
    if ink == background:
      raise ValueError('background and ink must differ')
    if not _is_seq(pieces):
      raise ValueError('pieces must be a list or tuple')
    if targets is None:
      targets = [None] * len(pieces)
    if not _is_seq(targets) or len(targets) != len(pieces):
      raise ValueError('targets must be a sequence matching pieces')
  _check_scene(width, height, combs, pieces, targets)
  pieces = [tuple(p) for p in pieces]
  grid = common.grid(width, height, background)
  output = common.grid(width, height, background)
  for comb in combs:
    for y, x in _comb_cells(comb):
      grid[y][x] = ink
      output[y][x] = ink
  for piece in pieces:
    for y, x in _rect_cells(piece):
      grid[y][x] = _RED
  for piece, target in zip(pieces, targets):
    if target is None:
      continue
    _, trail, final = _slide(combs[target], piece)
    for y, x in trail:
      output[y][x] = _TRAIL
    for y, x in final:
      output[y][x] = _RED
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=22, height=19, background=4, ink=1,
               combs=[(3, 5, 'right', 1, 1, 1, 3),
                      (11, 11, 'down', 1, 2, 1, 3)],
               pieces=[(1, 2, 1, 1), (1, 13, 1, 1), (6, 15, 1, 1),
                       (14, 2, 1, 1), (17, 11, 2, 2)],
               targets=[None, None, 0, None, None]),
      generate(width=22, height=19, background=3, ink=4,
               combs=[(3, 3, 'down', 1, 1, 1, 3),
                      (9, 12, 'up', 1, 2, 1, 3)],
               pieces=[(1, 15, 2, 2), (9, 6, 1, 1), (11, 0, 1, 1),
                       (16, 4, 1, 1), (17, 8, 2, 2), (17, 18, 1, 1)],
               targets=[1, 0, None, None, None, None]),
      generate(width=22, height=19, background=4, ink=8,
               combs=[(2, 6, 'down', 2, 1, 2, 3),
                      (10, 1, 'down', 1, 3, 1, 3)],
               pieces=[(1, 19, 1, 1), (2, 1, 1, 1), (6, 2, 2, 2),
                       (7, 18, 1, 1), (8, 10, 1, 1), (14, 16, 2, 2),
                       (16, 4, 2, 3)],
               targets=[None, None, None, None, 0, None, 1]),
  ]
  test = [
      generate(width=27, height=23, background=3, ink=4,
               combs=[(3, 14, 'down', 1, 1, 1, 3),
                      (6, 7, 'left', 1, 3, 1, 3),
                      (17, 19, 'up', 1, 2, 1, 3)],
               pieces=[(0, 14, 1, 1), (0, 23, 3, 2), (1, 3, 1, 2),
                       (2, 11, 1, 1), (9, 2, 3, 2), (9, 22, 2, 2),
                       (11, 14, 1, 1), (11, 17, 1, 1), (14, 14, 1, 1),
                       (20, 6, 2, 2), (20, 15, 1, 1)],
               targets=[None, None, None, None, 1, 2, None, 0, None, None,
                        None]),
  ]
  return {'train': train, 'test': test}
