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

"""ARC-GEN style generator for task d8e07eb2.

Rule.  The grid has five parts, from top to bottom:
  - a top band (rows 0..4) holding the query glyphs;
  - a full divider row of colour 6;
  - a catalogue of 3x3 glyph slots.  Slot rows start at y=8+5r and slot
    columns start at x=2+5c;
  - a second divider row of colour 6;
  - a two-row bottom band.

Every query glyph appears exactly once in the catalogue.  Glyphs are compared
by tight crop and colour.  Each matching catalogue slot gets a frame: the
background cells of the 5x5 box around the 3x3 slot become 3.  The frame is
built from the slot, not from the glyph's tight box, so a narrow glyph still
gets a full 5x5 frame.

Success means at least two queries whose matched slots all share one
catalogue row or one catalogue column.  On success, the background of the
bottom band and of the top band becomes 3.  Otherwise only the background of
the bottom band becomes 2.

Scope.  The catalogue is one of three kinds:
  - the task's 4x4 catalogue, used in about 20% of default draws and usually
    altered by distractors;
  - a freshly sampled catalogue with 2..4 slot rows and 2..5 slot columns;
  - a catalogue supplied by the caller, with 1..4 rows and 1..5 columns.

Sampled glyphs are random, 8-connected and monochrome.  About a third of the
unconstrained slots are forced to be narrower or shorter than 3 cells, which
exercises the slot-snapped frame.  Every slot row has a 3-tall glyph and
every slot column has a 3-wide glyph, so the slot lattice can be read from
the catalogue.

Catalogue sizes other than 4x4 are a synthetic extension of the fixed 22x30
fixtures.  The grid stays within 27x30.  These are kept fixed, as in every
fixture:
  - background 8;
  - divider colour 6;
  - slot pitch 5;
  - band heights.

Each scene samples:
  - a mode: row success, column success or failure;
  - a query count;
  - the queried slots.

Success sets fill a whole catalogue line in about 40% of cases, as all the
fixtures do.  Otherwise they are a partial collinear subset, which is a
documented extension consistent with the verified rule.

Failures are either scattered or near-misses, where all but one query lie on
a line.  The queries are placed in the top band either packed from the left
or in scattered slots.

Distractors are recoloured copies of query glyphs placed in non-queried
slots.  A scene-level bias puts them near the decision line, far from it, or
anywhere.  The missing-query failure branch of the reference transform is out
of scope: every query is always present in the catalogue.
"""

import random

import common

BG = 8
DIV = 6
MARK = 3
FAIL = 2
PALETTE = [0, 1, 2, 4, 5, 6, 7, 9]
NR_CHOICES = [2, 3, 3, 4, 4]
NC_CHOICES = [2, 3, 4, 4, 5, 5]
CANON_PROB = 0.2
NARROW_PROB = 0.35
FULL_LINE_PROB = 0.4

CANON = [
    [('2.2', '.2.', '2.2'), ('0..', '000', '0.0'),
     ('..7', '..7', '777'), ('9.9', '99.', '999')],
    [('7..', '777', '7..'), ('111', '.1.', '111'),
     ('.66', '..6', '.66'), ('000', '000', '000')],
    [('4.4', '4.4', '444'), ('22.', '222', '.2.'),
     ('55.', '5..', '55.'), ('1.1', '11.', '1.1')],
    [('9..', '999', '..9'), ('666', '6.6', '6.6'),
     ('.4.', '444', '.4.'), ('222', '2.2', '222')],
]

# Query lists of the canonical pairs.  With the unchanged canonical
# catalogue, a sampled scene never reuses one of these query sets, in any
# order or top-band placement.
FIXTURE_TOPS = [
    ((1, 3), (1, 1), (1, 0), (1, 2)),
    ((0, 1), (1, 1), (3, 1), (2, 1)),
    ((0, 0), (2, 0), (2, 1), (3, 3)),
    ((1, 3), (2, 1), (1, 0), (1, 2)),
    ((1, 1), (2, 3), (0, 3)),
    ((1, 3), (2, 3), (0, 3), (3, 3)),
    ((0, 0), (1, 0), (2, 1), (2, 2)),
]
FIXTURE_SETS = [frozenset(t) for t in FIXTURE_TOPS]

MODES = ('row', 'col', 'fail')
DIGITS = '0123456789'


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _cells(pattern):
  return [(y, x) for y in range(3) for x in range(3) if pattern[y][x] != '.']


def _crop_key(pattern):
  cells = _cells(pattern)
  y0 = min(y for y, _ in cells)
  x0 = min(x for _, x in cells)
  return tuple(sorted((y - y0, x - x0, pattern[y][x]) for y, x in cells))


def _height(pattern):
  ys = [y for y, _ in _cells(pattern)]
  return max(ys) - min(ys) + 1


def _width(pattern):
  xs = [x for _, x in _cells(pattern)]
  return max(xs) - min(xs) + 1


def _connected(pattern):
  cells = set(_cells(pattern))
  start = next(iter(cells))
  seen, stack = {start}, [start]
  while stack:
    y, x = stack.pop()
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        n = (y + dy, x + dx)
        if n in cells and n not in seen:
          seen.add(n)
          stack.append(n)
  return len(seen) == len(cells)


def _structure_ok(cat):
  """Return True if every slot row has a 3-tall glyph and every column a 3-wide one.

  Without these the slot lattice cannot be read from the catalogue.
  """
  nr, nc = len(cat), len(cat[0])
  for r in range(nr):
    if not any(_height(cat[r][c]) == 3 for c in range(nc)):
      return False
  for c in range(nc):
    if not any(_width(cat[r][c]) == 3 for r in range(nr)):
      return False
  return True


def _check_catalogue(cat):
  """Validate a supplied catalogue and return it as lists of string tuples."""
  if not isinstance(cat, (list, tuple)) or not cat:
    raise ValueError('catalogue must be a non-empty list of slot rows')
  if not isinstance(cat[0], (list, tuple)) or not cat[0]:
    raise ValueError('catalogue rows must be non-empty lists')
  nr, nc = len(cat), len(cat[0])
  if not (1 <= nr <= 4 and 1 <= nc <= 5):
    raise ValueError('catalogue must have 1..4 rows and 1..5 columns')
  keys = set()
  out = []
  for row in cat:
    if not isinstance(row, (list, tuple)) or len(row) != nc:
      raise ValueError('ragged catalogue')
    new_row = []
    for pat in row:
      if (not isinstance(pat, (list, tuple)) or len(pat) != 3 or
          any(not isinstance(s, str) or len(s) != 3 for s in pat)):
        raise ValueError('glyph patterns must be 3 strings of length 3')
      pat = tuple(pat)
      for y in range(3):
        for x in range(3):
          if pat[y][x] != '.' and pat[y][x] not in DIGITS:
            raise ValueError('glyph cells must be a digit or \'.\'')
      if not _cells(pat):
        raise ValueError('empty glyph')
      cols = {pat[y][x] for y, x in _cells(pat)}
      if len(cols) != 1 or int(next(iter(cols))) in (BG, MARK):
        raise ValueError('glyph must be monochrome, not colour 3 or 8')
      if not _connected(pat):
        raise ValueError('glyph must be 8-connected')
      k = _crop_key(pat)
      if k in keys:
        raise ValueError('duplicate catalogue glyph')
      keys.add(k)
      new_row.append(pat)
    out.append(new_row)
  if not _structure_ok(out):
    raise ValueError('every slot row/column needs a full-size glyph')
  return out


def _random_glyph(colour, shape=None):
  """Return a random 8-connected monochrome glyph inside a 3x3 slot.

  colour: glyph colour.
  shape: 'full' needs a 3x3 tight box.  'narrow' needs a tight box under 3
    in width or height.  None allows either.
  """
  ch = str(colour)
  steps = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a, b) != (0, 0)]
  hi = 6 if shape == 'narrow' else 9
  for _ in range(80):
    n = random.randint(3, hi)
    cells = {(random.randrange(3), random.randrange(3))}
    for _ in range(200):
      if len(cells) >= n:
        break
      y, x = random.choice(sorted(cells))
      dy, dx = random.choice(steps)
      if 0 <= y + dy < 3 and 0 <= x + dx < 3:
        cells.add((y + dy, x + dx))
    ys = [y for y, _ in cells]
    xs = [x for _, x in cells]
    full = max(ys) - min(ys) == 2 and max(xs) - min(xs) == 2
    if shape == 'full' and not full:
      continue
    if shape == 'narrow' and full:
      continue
    return tuple(''.join(ch if (y, x) in cells else '.' for x in range(3))
                 for y in range(3))
  # Practically unreachable fallbacks, both valid for their shape.
  if shape == 'narrow':
    return (ch + ch + '.', '.' + ch + '.', ch + ch + '.')
  return (ch + '.' + ch, '.' + ch + '.', ch + '.' + ch)


def _random_catalogue(nr, nc):
  need = set()
  for c in range(nc):
    need.add((random.randrange(nr), c))
  for r in range(nr):
    need.add((r, random.randrange(nc)))
  cat = []
  seen = set()
  fallback = [('XXX', 'XXX', 'XXX'), ('X.X', '.X.', 'X.X'),
              ('.X.', 'XXX', '.X.'), ('XXX', 'X.X', 'XXX')]
  for r in range(nr):
    row = []
    for c in range(nc):
      if (r, c) in need:
        shape = 'full'
      elif random.random() < NARROW_PROB:
        shape = 'narrow'
      else:
        shape = None
      glyph = None
      for _ in range(100):
        g = _random_glyph(random.choice(PALETTE), shape)
        if _crop_key(g) not in seen:
          glyph = g
          break
      if glyph is None:
        for col in PALETTE:
          for pat in fallback:
            g = tuple(s.replace('X', str(col)) for s in pat)
            if glyph is None and _crop_key(g) not in seen:
              glyph = g
      seen.add(_crop_key(glyph))
      row.append(glyph)
    cat.append(row)
  return cat


def _classify(top):
  if len(top) > 1 and len(set(r for r, _ in top)) == 1:
    return 'row'
  if len(top) > 1 and len(set(c for _, c in top)) == 1:
    return 'col'
  return 'fail'


def _add_distractors(cat, top, prob):
  """Copy some query glyphs, recoloured, into non-queried slots.

  A scene-level bias orders the candidate slots:
    near: the success line.  For a failure, the slots that would make the
      query set collinear come first, then the queries' rows and columns;
    far: the reverse order;
    none: random.
  A slot that would break the slot lattice is skipped.
  """
  nr, nc = len(cat), len(cat[0])
  used = set(top)
  free = [(r, c) for r in range(nr) for c in range(nc) if (r, c) not in used]
  rows_q = set(r for r, _ in top)
  cols_q = set(c for _, c in top)
  mode = _classify(top)
  bias = random.choice(('near', 'near', 'far', 'none'))

  def in_line(rc):
    if mode == 'row':
      return rc[0] in rows_q
    if mode == 'col':
      return rc[1] in cols_q
    return rc[0] in rows_q or rc[1] in cols_q

  def rank(i, rc):
    if bias == 'none':
      return 0
    if mode == 'fail':
      others = [t for j, t in enumerate(top) if j != i] + [rc]
      if _classify(others) != 'fail':
        near = 0
      else:
        near = 1 if in_line(rc) else 2
    else:
      near = 0 if in_line(rc) else 1
    return near if bias == 'near' else -near

  order = list(range(len(top)))
  random.shuffle(order)
  for i in order:
    if not free:
      break
    if random.random() >= prob:
      continue
    qr, qc = top[i]
    src = cat[qr][qc]
    colour = next(src[y][x] for y, x in _cells(src))
    keys = {_crop_key(cat[r][c]) for r in range(nr) for c in range(nc)}
    options = [str(p) for p in PALETTE if str(p) != colour]
    random.shuffle(options)
    random.shuffle(free)
    free.sort(key=lambda rc: rank(i, rc))
    for new_col in options:
      g = tuple(s.replace(colour, new_col) for s in src)
      if _crop_key(g) in keys:
        continue
      # The lattice check does not depend on colour: one colour is enough.
      for j, (tr, tc) in enumerate(free):
        old = cat[tr][tc]
        cat[tr][tc] = g
        if _structure_ok(cat):
          free.pop(j)
          break
        cat[tr][tc] = old
      break


def _mode_hi(m, nr, nc):
  """Return the largest query count that mode m allows (0 if impossible)."""
  if m == 'row':
    return nc
  if m == 'col':
    return min(nr, nc)
  return nc if (nr >= 2 and nc >= 2) else 0


def _sample_top(nr, nc, mode, k):
  need = 2 if k is None else k
  weighted = ['row', 'col', 'fail', 'fail']
  ok = [m for m in weighted if _mode_hi(m, nr, nc) >= need]
  if mode is None:
    if not ok:
      raise ValueError('no mode can place %d queries in a %dx%d catalogue'
                       % (need, nr, nc))
    mode = random.choice(ok)
  elif _mode_hi(mode, nr, nc) < need:
    raise ValueError('mode %s cannot place %d queries in a %dx%d catalogue'
                     % (mode, need, nr, nc))
  hi = _mode_hi(mode, nr, nc)
  if k is None:
    line = nc if mode == 'row' else nr
    if mode != 'fail' and line <= hi and random.random() < FULL_LINE_PROB:
      k = line
    else:
      k = random.randint(2, hi)
  if mode == 'row':
    r = random.randrange(nr)
    return [(r, c) for c in random.sample(range(nc), k)]
  if mode == 'col':
    c = random.randrange(nc)
    return [(r, c) for r in random.sample(range(nr), k)]
  if k >= 3 and random.random() < 0.5:
    # Near-miss failure: k-1 queries on one line, one query off it.
    orients = ['row']
    if k - 1 <= nr:
      orients.append('col')
    if random.choice(orients) == 'row':
      r = random.randrange(nr)
      top = [(r, c) for c in random.sample(range(nc), k - 1)]
      r2 = random.choice([x for x in range(nr) if x != r])
      top.append((r2, random.randrange(nc)))
    else:
      c = random.randrange(nc)
      top = [(r, c) for r in random.sample(range(nr), k - 1)]
      c2 = random.choice([x for x in range(nc) if x != c])
      top.append((random.randrange(nr), c2))
    random.shuffle(top)
    return top
  r1, r2 = random.sample(range(nr), 2)
  c1, c2 = random.sample(range(nc), 2)
  top = [(r1, c1), (r2, c2)]
  rest = [(r, c) for r in range(nr) for c in range(nc) if (r, c) not in top]
  top += random.sample(rest, k - 2)
  random.shuffle(top)
  return top


def _pick(given, choices, lo, name):
  if given is not None:
    if given < lo:
      raise ValueError('%s=%d too small; need at least %d' % (name, given, lo))
    return given
  opts = [v for v in choices if v >= lo]
  if not opts:
    raise ValueError('requested queries need %s >= %d, above the maximum'
                     % (name, lo))
  return random.choice(opts)


def _is_fixture(cat, top):
  return (cat == [list(r) for r in CANON] and
          frozenset(top) in FIXTURE_SETS)


def _normalise_top(top):
  try:
    entries = list(top)
  except TypeError:
    raise ValueError('top must be a list of (row, col) pairs')
  norm = []
  for t in entries:
    try:
      pair = tuple(t)
    except TypeError:
      raise ValueError('top entries must be (row, col) pairs')
    if len(pair) != 2 or not all(_is_int(v) for v in pair):
      raise ValueError('top entries must be integer (row, col) pairs')
    if pair[0] < 0 or pair[1] < 0:
      raise ValueError('top coordinates must be non-negative')
    norm.append(pair)
  if not norm or len(set(norm)) != len(norm):
    raise ValueError('top must hold distinct slots')
  return norm


def _normalise_slots(top_slots):
  try:
    slots = list(top_slots)
  except TypeError:
    raise ValueError('top_slots must be a list of integers')
  if not slots or not all(_is_int(s) for s in slots):
    raise ValueError('top_slots must be a non-empty list of integers')
  if slots != sorted(set(slots)) or slots[0] < 0:
    raise ValueError('top_slots must be increasing distinct indices >= 0')
  return slots


def _stamp(g, pattern, y0, x0):
  for y, x in _cells(pattern):
    g[y0 + y][x0 + x] = int(pattern[y][x])


def generate(catalogue=None, top=None, rows=None, cols=None, mode=None,
             num_queries=None, top_slots=None, distractor_prob=None):
  """Build one input/output pair.

  catalogue: list of slot rows.  Each entry is a 3x3 pattern given as 3
    strings, with a colour digit or '.' per cell.  The glyph's offset inside
    its slot is part of the pattern.  None samples the task catalogue (about
    20%) or a random one.
  top: list of distinct, non-negative (slot_row, slot_col) catalogue
    positions, queried in order.  None samples them from mode and
    num_queries.  With a sampled catalogue, the size is drawn so that top
    fits.
  rows, cols: integer catalogue slot rows (2..4) and columns (2..5) for a
    sampled catalogue.  They must agree with a supplied catalogue.
  mode: 'row', 'col' or 'fail'.  It is checked against a supplied top.
  num_queries: integer query count (1..5).  It must be at least 2 when top
    is sampled, and it is checked against top and top_slots.
  top_slots: strictly increasing integer top-band slot indices for the
    queries.  Their length fixes the query count.  Defaults to 0..k-1 when
    top is given; otherwise it is sampled.
  distractor_prob: per-query chance (number in [0, 1]) of planting a
    recoloured copy of that query in a non-queried slot.  It applies to
    sampled and canonical catalogues.  Default 0.5.  Rejected with an
    explicit catalogue.
  """
  if mode is not None and mode not in MODES:
    raise ValueError('unknown mode %r' % (mode,))
  for name, v in (('rows', rows), ('cols', cols), ('num_queries', num_queries)):
    if v is not None and not _is_int(v):
      raise ValueError('%s must be an integer' % name)
  user_cat = catalogue is not None
  if distractor_prob is not None:
    if user_cat:
      raise ValueError('distractor_prob only applies to generated catalogues')
    if (isinstance(distractor_prob, bool) or
        not isinstance(distractor_prob, (int, float)) or
        not 0 <= distractor_prob <= 1):
      raise ValueError('distractor_prob must be a number in [0, 1]')
  prob = 0.5 if distractor_prob is None else distractor_prob

  k = num_queries
  if top is not None:
    top = _normalise_top(top)
    if k is not None and k != len(top):
      raise ValueError('num_queries disagrees with top')
    k = len(top)
    if mode is not None and _classify(top) != mode:
      raise ValueError('top does not realise mode %s' % mode)
  if top_slots is not None:
    top_slots = _normalise_slots(top_slots)
    if k is not None and k != len(top_slots):
      raise ValueError('top_slots length disagrees with the query count')
    k = len(top_slots)
  if k is not None:
    if not 1 <= k <= 5:
      raise ValueError('query count must be in 1..5')
    if top is None and k < 2:
      raise ValueError('sampled scenes need at least 2 queries')

  min_nc = k if k is not None else 2
  min_nr = 1
  if top is not None:
    min_nc = max(min_nc, max(c for _, c in top) + 1)
    min_nr = max(r for r, _ in top) + 1
  elif mode == 'col':
    min_nr = max(2, k if k is not None else 2)
  if top_slots is not None:
    min_nc = max(min_nc, top_slots[-1] + 1)

  use_canon = False
  if user_cat:
    base = _check_catalogue(catalogue)
    nr, nc = len(base), len(base[0])
    if (rows is not None and rows != nr) or (cols is not None and cols != nc):
      raise ValueError('rows/cols disagree with the supplied catalogue')
    if nr < min_nr or nc < min_nc:
      raise ValueError('catalogue too small for the requested queries/slots')
  else:
    if rows is not None and not 2 <= rows <= 4:
      raise ValueError('rows must be in 2..4')
    if cols is not None and not 2 <= cols <= 5:
      raise ValueError('cols must be in 2..5')
    canon_ok = (top is None and rows in (None, 4) and cols in (None, 4) and
                min_nr <= 4 and min_nc <= 4)
    use_canon = canon_ok and random.random() < CANON_PROB
    if use_canon:
      nr, nc = 4, 4
    else:
      nr = _pick(rows, NR_CHOICES, min_nr, 'rows')
      nc = _pick(cols, NC_CHOICES, min_nc, 'cols')

  if top is not None and any(r >= nr or c >= nc for r, c in top):
    raise ValueError('top slot outside the %dx%d catalogue' % (nr, nc))

  def fresh():
    if user_cat:
      return [list(r) for r in base]
    if use_canon:
      return [list(r) for r in CANON]
    return _random_catalogue(nr, nc)

  if top is not None:
    cat = fresh()
    if not user_cat:
      _add_distractors(cat, top, prob)
    slots = list(top_slots) if top_slots is not None else list(range(len(top)))
  else:
    result = None
    for _ in range(50):
      cat = fresh()
      cand = _sample_top(nr, nc, mode, k)
      if top_slots is not None:
        slots = list(top_slots)
      elif random.random() < 0.5:
        slots = list(range(len(cand)))
      else:
        slots = sorted(random.sample(range(nc), len(cand)))
      if not user_cat:
        _add_distractors(cat, cand, prob)
      if _is_fixture(cat, cand):
        continue
      result = (cat, cand, slots)
      break
    if result is None:
      raise RuntimeError('could not sample a non-fixture scene')
    cat, top, slots = result

  if len(slots) != len(top) or slots[-1] >= nc:
    raise ValueError('top_slots must fit in the %d top-band slots' % nc)

  width, height = 2 + 5 * nc, 10 + 5 * nr
  d1, d2 = 5, 7 + 5 * nr
  g = common.grid(width, height, BG)
  for x in range(width):
    g[d1][x] = DIV
    g[d2][x] = DIV
  for r in range(nr):
    for c in range(nc):
      _stamp(g, cat[r][c], 8 + 5 * r, 2 + 5 * c)
  for s, (r, c) in zip(slots, top):
    _stamp(g, cat[r][c], 1, 2 + 5 * s)

  out = [row[:] for row in g]
  for r, c in top:
    y0, x0 = 8 + 5 * r, 2 + 5 * c
    for y in range(y0 - 1, y0 + 4):
      for x in range(x0 - 1, x0 + 4):
        if out[y][x] == BG:
          out[y][x] = MARK
  success = _classify(top) != 'fail'
  fill = MARK if success else FAIL
  for y in range(d2 + 1, height):
    for x in range(width):
      if out[y][x] == BG:
        out[y][x] = fill
  if success:
    for y in range(d1):
      for x in range(width):
        if out[y][x] == BG:
          out[y][x] = MARK
  return {'input': g, 'output': out}


def validate():
  """Reconstruct the canonical pairs from explicit latent parameters."""
  train = [
      generate(catalogue=CANON, top=[(1, 3), (1, 1), (1, 0), (1, 2)]),
      generate(catalogue=CANON, top=[(0, 1), (1, 1), (3, 1), (2, 1)]),
      generate(catalogue=CANON, top=[(0, 0), (2, 0), (2, 1), (3, 3)]),
      generate(catalogue=CANON, top=[(1, 3), (2, 1), (1, 0), (1, 2)]),
      generate(catalogue=CANON, top=[(1, 1), (2, 3), (0, 3)]),
  ]
  test = [
      generate(catalogue=CANON, top=[(1, 3), (2, 3), (0, 3), (3, 3)]),
      generate(catalogue=CANON, top=[(0, 0), (1, 0), (2, 1), (2, 2)]),
  ]
  return {'train': train, 'test': test}
