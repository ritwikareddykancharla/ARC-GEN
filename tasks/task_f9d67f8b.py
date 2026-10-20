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

"""ARC-GEN style generator for task f9d67f8b (occluded symmetric mosaic repair).

Rule: the square input is a decorative mosaic. It is mirror symmetric
left-right and up-down about off-centre axes. With side S, column x mirrors
to column S+1-x and row y mirrors to row S+1-y. In the native 30x30 task
these are 31-x and 31-y, so the first two rows and columns have no mirror
inside the grid. Rectangular blobs of colour 9 hide parts of the mosaic. The
output removes every 9 in two steps:
  1. Each hidden cell copies a visible horizontal, vertical or double mirror
     partner.
  2. Each cell that is still hidden copies its diagonal (transpose) partner
     or one of that partner's mirror images. These partners are read on the
     step-1 canvas, so they must be visible or restored in step 1, and they
     must all agree.

Latent scene: an HxH fundamental quadrant Q, with H = S/2 + 1. Q holds
pattern indices 0..H-1 of the full (S+2)x(S+2) pattern. Grid cell (y, x)
shows Q[f(y)][f(x)], where f(i) = i for i < H and f(i) = S+1-i otherwise.
Random quadrants are built from 2x2 tiles (solid, checker, split, random)
over a palette sampled from colours 1..8. A random fraction of transpose
pairs is made equal, so outputs are only partly transpose symmetric, as in
the native grids. The occluders are chosen first. Only the quadrant entries
that the diagonal fallback actually reads are then forced to agree with
their transposes.

There are four latent occluder families for diagonal-fallback scenes:
  * edge: a block on the top or left edge that straddles the centre seam.
    Its height ranges from a 1-row strip to 8 rows. The native test is this
    case (rows 0-7, cols 12-18).
  * shadow: an edge block plus a rectangle that hides, in the raw input, the
    plain transpose (x, y) of some fallback cells. That rectangle is
    restored in step 1 from its vertical mirror. The diagonal step therefore
    reads a cell that was a 9 in the input but is known on the step-1 canvas
    (synthetic). Note: if a plain transpose cannot be restored in step 1,
    then its whole mirror orbit is hidden. Its mirrored transposes are then
    hidden too, so a 'mirrored transpose only' case cannot exist.
  * orbit: a four-fold mirrored blob orbit in the interior whose transposed
    orbit stays visible (synthetic).
  * strip: a 1-wide edge strip touching the (0,1)/(1,0) corner cell. It is
    a deliberate corner probe: exactly one cell needs the fallback and it
    has a single in-grid diagonal partner (synthetic).
Ordinary H/V-recoverable rectangles are added as distractors. Some of these
are three-of-four mirror orbits, so that a few cells can be restored only
from their double (point) mirror.

Scope: the native size is 30x30 and is sampled 60% of the time. Other even
sizes from 16 to 28 keep the same two-cell off-centre crop and are synthetic
extensions. Odd sizes are not supported, because the rule's axes always fall
between cells. Every hidden cell must be recoverable exactly as the archived
rule recovers it. The two candidate axes nearer the centre must be
contradicted by visible cells, so that the off-centre axis is the unique
choice under the rule's tie-break.
"""

import random

import common

OCC = 9
SIZES = (16, 18, 20, 22, 24, 26, 28, 30)
NATIVE = 30
FAMILIES = ('edge', 'shadow', 'orbit', 'strip')
MIN_HIDDEN = 3


def _as_int(value, what):
  """Returns value if it is a plain int; booleans and other types raise."""
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError('%s must be an integer, got %r' % (what, value))
  return value


def _as_list(value, what):
  """Accepts only ordered sequences (list or tuple), else raises ValueError."""
  if not isinstance(value, (list, tuple)):
    raise ValueError('%s must be a list or tuple, got %r' % (what, value))
  return list(value)


def _parse_quadrant(quadrant):
  """Parses rows given as digit strings ('1'..'8') or sequences of ints."""
  quad = []
  for row in _as_list(quadrant, 'quadrant'):
    if isinstance(row, str):
      if not row or any(ch not in '12345678' for ch in row):
        raise ValueError('quadrant string rows must use digits 1..8')
      quad.append([int(ch) for ch in row])
    else:
      quad.append([_as_int(v, 'quadrant colour')
                   for v in _as_list(row, 'quadrant row')])
  half = len(quad)
  if half < 2 or any(len(row) != half for row in quad):
    raise ValueError('quadrant must be square')
  if any(v < 1 or v > 8 for row in quad for v in row):
    raise ValueError('quadrant colours must lie in 1..8')
  return quad


def _parse_palette(palette):
  items = _as_list(palette, 'palette')
  pal = sorted(set(_as_int(c, 'palette colour') for c in items))
  if len(pal) < 2 or any(c < 1 or c > 8 for c in pal):
    raise ValueError('palette needs at least two colours from 1..8')
  return pal


def _fold(i, span):
  half = span // 2
  return i if i < half else span - 1 - i


def _render(quad, size):
  span = size + 2
  return [[quad[_fold(y, span)][_fold(x, span)] for x in range(size)]
          for y in range(size)]


def _occlude(out, hidden):
  inp = [row[:] for row in out]
  for r, c in hidden:
    inp[r][c] = OCC
  return inp


def _mask_cells(rects, size):
  """Union of inclusive rectangles; rejects malformed or out-of-bounds ones."""
  cells = set()
  for rect in _as_list(rects, 'masks'):
    rect = _as_list(rect, 'mask rectangle')
    if len(rect) != 4:
      raise ValueError('mask rectangles are (row0, col0, row1, col1)')
    r0, c0, r1, c1 = [_as_int(v, 'mask coordinate') for v in rect]
    if not (0 <= r0 <= r1 < size and 0 <= c0 <= c1 < size):
      raise ValueError('mask rectangle out of bounds: %r' % (tuple(rect),))
    for r in range(r0, r1 + 1):
      for c in range(c0, c1 + 1):
        cells.add((r, c))
  return cells


def _inside(a, b, size):
  return 0 <= a < size and 0 <= b < size


def _diag_partners(y, x, span):
  return ((x, y), (x, span - 1 - y), (span - 1 - x, y),
          (span - 1 - x, span - 1 - y))


def _hv_split(hidden, size, span):
  """Splits hidden cells into H/V-recoverable ones and the rest."""
  hv, left = set(), []
  for y, x in sorted(hidden):
    partners = ((y, span - 1 - x), (span - 1 - y, x),
                (span - 1 - y, span - 1 - x))
    if any(_inside(a, b, size) and (a, b) not in hidden for a, b in partners):
      hv.add((y, x))
    else:
      left.append((y, x))
  return hv, left


def _known_partners(y, x, hidden, hv, size, span):
  return [(a, b) for a, b in _diag_partners(y, x, span)
          if _inside(a, b, size) and ((a, b) not in hidden or (a, b) in hv)]


def _unusable(hidden, hv, left, size, span):
  """Left-over cells with no usable diagonal partner (independent of colour)."""
  return [(y, x) for y, x in left
          if not _known_partners(y, x, hidden, hv, size, span)]


def _diagonal_safe(out, hidden, hv, left, span):
  """Cells left after H/V repair need agreeing, known diagonal partners."""
  size = len(out)
  for y, x in left:
    known = _known_partners(y, x, hidden, hv, size, span)
    if not known or any(out[a][b] != out[y][x] for a, b in known):
      return False
  return True


def _axis_accepts(grid, a, vertical):
  """True if axis a has no disagreeing pair among non-occluded cells."""
  size = len(grid)
  for j in range(min(a, size - a)):
    p, q = a - 1 - j, a + j
    for k in range(size):
      if vertical:
        u, v = grid[k][p], grid[k][q]
      else:
        u, v = grid[p][k], grid[q][k]
      if u != OCC and v != OCC and u != v:
        return False
  return True


def _scene_problem(out, inp, hidden, span, diagonal):
  """Returns a description of the first violated invariant, or None."""
  size = len(out)
  hv, left = _hv_split(hidden, size, span)
  if diagonal is not None and bool(left) != bool(diagonal):
    return 'diagonal fallback requirement not met'
  if not _diagonal_safe(out, hidden, hv, left, span):
    return 'some hidden cell is not uniquely recoverable'
  half = span // 2
  # Axis half-1 is the exact centre (score 0); axis half-2 ties with the true
  # axis half and wins the tie by its smaller index. Both must be refuted.
  for a in (half - 2, half - 1):
    for vertical in (True, False):
      if _axis_accepts(inp, a, vertical):
        return 'a nearer-centre symmetry axis is consistent'
  return None


def _random_quadrant(half, palette):
  quad = common.grid(half, half, 0)
  for by in range(0, half, 2):
    for bx in range(0, half, 2):
      a, b = random.sample(palette, 2)
      kind = random.randrange(6)
      if kind < 2:
        tile = [[a, a], [a, a]]
      elif kind == 2:
        tile = [[a, b], [b, a]]
      elif kind == 3:
        tile = [[a, a], [b, b]]
      elif kind == 4:
        tile = [[a, b], [a, b]]
      else:
        tile = [[random.choice(palette) for _ in range(2)] for _ in range(2)]
      for dy in range(2):
        for dx in range(2):
          if by + dy < half and bx + dx < half:
            quad[by + dy][bx + dx] = tile[dy][dx]
  return quad


def _symmetrize(quad, left, span, fraction):
  """Equalises a random fraction of transpose pairs, plus every pair read."""
  half = len(quad)
  for y in range(half):
    for x in range(y + 1, half):
      if random.random() < fraction:
        if random.random() < 0.5:
          quad[x][y] = quad[y][x]
        else:
          quad[y][x] = quad[x][y]
  for y, x in left:
    fy, fx = _fold(y, span), _fold(x, span)
    quad[fx][fy] = quad[fy][fx]


def _diagonal_masks(half, family):
  """Occluders whose hidden cells need the diagonal fallback."""
  span = 2 * half
  if family is None:
    roll = random.random()
    if roll < 0.4:
      family = 'edge'
    elif roll < 0.6:
      family = 'shadow'
    elif roll < 0.85:
      family = 'orbit'
    else:
      family = 'strip'
  if family in ('edge', 'shadow'):
    # Edge block straddling the seam (native test: rows 0-7, cols 12-18).
    h = random.randint(1, min(8, half - 4))
    a = random.randint(1, min(4, half - 3))
    b = random.randint(0, min(4, half - 3))
    lo, hi = half - 1 - a, half + b
    top = random.random() < 0.5
    rects = [(0, lo, h - 1, hi)] if top else [(lo, 0, hi, h - 1)]
    if family == 'shadow':
      # Hide, in the raw input, part of the transposed region before the
      # seam (it includes the transpose of fallback cell (0, half-1)). Its
      # vertical/horizontal mirror across the seam stays visible, so step 1
      # restores it and step 2 reads it from the step-1 canvas.
      s0 = random.randint(lo, half - 1)
      t1 = random.randint(0, min(h - 1, 3))
      if top:
        rects.append((s0, 0, half - 1, t1))
      else:
        rects.append((0, s0, t1, half - 1))
    return rects
  if family == 'orbit':
    # Four mirrored interior blobs. Disjoint row/column fold intervals keep
    # the transposed orbit visible.
    n = half - 2
    la, lb = random.randint(1, 3), random.randint(1, 3)
    gap = random.randint(0, n - la - lb)
    start = random.randint(2, 2 + n - la - lb - gap)
    first = (start, start + la - 1)
    second = (start + la + gap, start + la + gap + lb - 1)
    if random.random() < 0.5:
      first, second = second, first
    (r0, r1), (c0, c1) = first, second
    m0, m1 = span - 1 - c1, span - 1 - c0
    n0, n1 = span - 1 - r1, span - 1 - r0
    return [(r0, c0, r1, c1), (r0, m0, r1, m1), (n0, c0, n1, c1),
            (n0, m0, n1, m1)]
  # Corner probe: (0,1) or (1,0) has no mirror in the grid; its only in-grid
  # diagonal partner is the other corner cell.
  w = random.randint(4, min(7, half - 2))
  if random.random() < 0.5:
    return [(0, 1, 0, w)]
  return [(1, 0, w, 0)]


def _triple_orbit(half):
  """Hides three of the four mirror images of an interior rectangle."""
  span = 2 * half
  n = half - 2
  h, w = random.randint(1, min(4, n)), random.randint(1, min(4, n))
  r0, c0 = random.randint(2, half - h), random.randint(2, half - w)
  r1, c1 = r0 + h - 1, c0 + w - 1
  mr0, mr1 = span - 1 - r1, span - 1 - r0
  mc0, mc1 = span - 1 - c1, span - 1 - c0
  orbit = [(r0, c0, r1, c1), (r0, mc0, r1, mc1), (mr0, c0, mr1, c1),
           (mr0, mc0, mr1, mc1)]
  keep = random.randrange(4)
  return [rect for i, rect in enumerate(orbit) if i != keep]


def _plain_masks(size, half, count):
  top = min(9, size // 3)
  rects = []
  for _ in range(count):
    if random.random() < 0.3:
      rects.extend(_triple_orbit(half))
      continue
    h, w = random.randint(2, top), random.randint(2, top)
    r, c = random.randint(0, size - h), random.randint(0, size - w)
    rects.append((r, c, r + h - 1, c + w - 1))
  return rects


def generate(size=None, quadrant=None, masks=None, diagonal=None,
             palette=None, family=None):
  """Returns an occluded symmetric mosaic and its repaired version.

  Args:
    size: optional even int side length in 16..30. The native size is 30;
      other sizes are synthetic extensions. When a quadrant is given, size
      must equal 2 * len(quadrant) - 2. When only masks are given, size
      defaults to the native 30.
    quadrant: optional HxH fundamental quadrant of colours 1..8, given as a
      list/tuple of rows. Rows are digit strings or lists/tuples of ints. It
      holds pattern indices 0..H-1 and is used verbatim (never
      re-symmetrised).
    masks: optional list/tuple of (row0, col0, row1, col1) inclusive integer
      rectangles painted with colour 9. They must lie in bounds, and every
      hidden cell must have some usable partner; otherwise ValueError.
    diagonal: optional bool. True requires some hidden cell to need the
      diagonal fallback; False forbids it. When masks are given, it must
      agree with them. When both quadrant and masks are given, None skips
      the check. When only a quadrant is given and diagonal is None,
      diagonal mode is tried first with probability 0.35 and abandoned if
      that quadrant admits no valid fallback occluder.
    palette: optional colours from 1..8 (at least 2) for a random quadrant.
      It is rejected when a quadrant is supplied.
    family: optional fallback occluder family, one of 'edge', 'shadow',
      'orbit' or 'strip'. It implies diagonal=True and is rejected together
      with explicit masks or with diagonal=False.
  """
  quad = None
  if quadrant is not None:
    quad = _parse_quadrant(quadrant)
    if palette is not None:
      raise ValueError('palette only applies to a sampled quadrant')
  if size is not None:
    size = _as_int(size, 'size')
  if quad is not None:
    expected = 2 * len(quad) - 2
    if size is None:
      size = expected
    elif size != expected:
      raise ValueError('size does not match quadrant')
  elif size is None:
    if masks is not None:
      size = NATIVE
    else:
      size = NATIVE if random.random() < 0.6 else random.choice(SIZES[:-1])
  if size not in SIZES:
    raise ValueError('size must be even and in 16..30')
  span = size + 2
  half = span // 2
  if palette is not None:
    palette = _parse_palette(palette)
  if diagonal is not None and not isinstance(diagonal, bool):
    raise ValueError('diagonal must be a bool or None, got %r' % (diagonal,))
  if family is not None:
    if not isinstance(family, str) or family not in FAMILIES:
      raise ValueError('family must be one of %r' % (FAMILIES,))
    if masks is not None:
      raise ValueError('family cannot be combined with explicit masks')
    if diagonal is False:
      raise ValueError('family requires the diagonal fallback')
    diagonal = True

  fixed_hidden = None
  if masks is not None:
    fixed_hidden = _mask_cells(masks, size)
    if not fixed_hidden:
      raise ValueError('masks hide no cells')

  if quad is not None and fixed_hidden is not None:
    out = _render(quad, size)
    inp = _occlude(out, fixed_hidden)
    problem = _scene_problem(out, inp, fixed_hidden, span, diagonal)
    if problem:
      raise ValueError('explicit scene invalid: ' + problem)
    return {'input': inp, 'output': out}

  if fixed_hidden is not None:
    hv, left = _hv_split(fixed_hidden, size, span)
    bad = _unusable(fixed_hidden, hv, left, size, span)
    if bad:
      raise ValueError('masks hide cell %r with no usable mirror or diagonal '
                       'partner' % (bad[0],))
    if diagonal is None:
      diagonal = bool(left)
    elif diagonal != bool(left):
      raise ValueError('masks are incompatible with the diagonal setting')

  auto = diagonal is None
  if auto:
    diagonal = random.random() < 0.35

  for attempt in range(400):
    mode = diagonal
    if auto and quad is not None and attempt >= 200:
      mode = False
    if fixed_hidden is not None:
      hidden = fixed_hidden
    else:
      if mode:
        rects = _diagonal_masks(half, family) + _plain_masks(
            size, half, random.randint(0, 2))
      else:
        rects = _plain_masks(size, half, random.randint(1, 3))
      hidden = _mask_cells(rects, size)
      if len(hidden) < MIN_HIDDEN or len(hidden) > size * size // 4:
        continue
    hv, left = _hv_split(hidden, size, span)
    if bool(left) != mode:
      continue
    if _unusable(hidden, hv, left, size, span):
      continue
    if quad is None:
      pal = palette
      if pal is None:
        pal = random.sample(range(1, 9), random.randint(4, 8))
      q = _random_quadrant(half, pal)
      _symmetrize(q, left, span, random.uniform(0.15, 0.7))
    else:
      q = quad
    out = _render(q, size)
    inp = _occlude(out, hidden)
    if _scene_problem(out, inp, hidden, span, mode) is None:
      return {'input': inp, 'output': out}
  if quad is not None:
    raise ValueError('the given quadrant admits no sampled valid occluder '
                     '(e.g. it lacks local transpose agreement or cannot '
                     'refute the nearer-centre axes)')
  raise ValueError('Could not build a valid occluded mosaic')


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  quads = [
      ['3382887644663327', '3326886764661372', '8233768888442767',
       '2333678888647236', '5788336231271155', '7588332833721155',
       '8857323327636611', '8875283372766611', '4688332717655557',
       '4488137281555575', '6646276713175755', '6644723633817555',
       '3127116685541755', '3372116658458156', '2763551154853317',
       '7276551145583181'],
      ['3278477411176464', '2387744711716646', '1432744755116411',
       '4123477455114611', '6688327866641658', '6688238746461185',
       '8866143264112216', '8866412346112211', '1155646446338882',
       '1155664674338828', '1711641186468288', '7111461168742888',
       '6664112254664633', '4646612245667433', '6411581166548646',
       '4611856166456874'],
      ['1655888813523673', '6152888831256336', '6316888853137322',
       '3661888835313682', '7733162536732155', '7733615563361255',
       '3377631673282121', '3377366136221212', '1353367322888488',
       '3135633622884888', '5213732253228884', '2531368238228848',
       '3673212168672288', '6336121286762288', '7328552167688322',
       '3622551276863522'],
      ['6122462682833235', '6627646228383355', '1761264681823555',
       '7266626418285555', '7281617233357644', '2718662223556744',
       '8172276135556776', '1827716655557667', '8281323566277745',
       '2818335586757754', '8382355577664577', '3828555577865477',
       '3335766788866657', '2355677688688672', '3555447686887766',
       '5555446768887786'],
      ['4888574175163446', '4488751477614362', '8848415786754618',
       '8644147568776211', '8553488834468684', '5835448843622848',
       '5385684846113586', '3558884462815328', '7786344632238863',
       '5768436223318836', '1677461842326388', '6157621124233688',
       '3446823548873213', '4362685384782332', '4611848287484232',
       '6281486878842423'],
  ]
  masks = [
      [(4, 26, 11, 29), (10, 24, 11, 29), (12, 19, 14, 23)],
      [(3, 8, 7, 11), (4, 1, 5, 5), (5, 6, 5, 7), (6, 3, 9, 8),
       (25, 10, 27, 15)],
      [(3, 17, 9, 19), (4, 23, 5, 24), (10, 0, 11, 2)],
      [(7, 17, 9, 20), (10, 6, 11, 11), (12, 5, 15, 7)],
      [(0, 12, 7, 18), (11, 10, 13, 12), (16, 24, 22, 29)],
  ]
  train = [generate(quadrant=quads[i], masks=masks[i]) for i in range(4)]
  test = [generate(quadrant=quads[4], masks=masks[4])]
  return {'train': train, 'test': test}
