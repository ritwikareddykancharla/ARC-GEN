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

"""ARC task e3721c99: recolour grey blobs by their number of enclosed holes.

Rule: the grid holds a divider of colour 1. On one side of the divider is a
legend of small key shapes. Grey (5) blobs fill the rest of the grid. Each
key has its own colour and its own number of holes. Every grey blob takes
the colour of the key with the same hole count. A grey blob whose hole count
matches no key is erased to background (0). The divider is not a key.
Nothing else changes.

Holes are counted the same way for keys and blobs. Crop the object's
bounding box. A hole is a 4-connected group of non-object cells inside the
crop that never touches the crop edge.

Scope of the random sampler:
  * Grid sides. Random grids are 18 to 30 cells per side. Explicit sizes from
    16 to 30 are accepted. The fixtures are all 30x30, so every other size
    is a synthetic extension. When the legend needs a long divider, the
    random length along the divider is drawn only from lengths that fit it.
  * Divider layouts. Two layouts are built, both seen in the fixtures.
    - 'straight': a full row or column of colour 1, five cells in from the
      legend edge (train 1, both tests).
    - 'corner': an L-shaped colour-1 divider that boxes the legend into a
      grid corner (train 2). One arm runs parallel to the keys, five or six
      cells from the legend edge. The other arm crosses the divider line
      one or two cells past the last key. Neither arm spans the whole grid.
    By default about 30% of scenes try the corner layout first. The legend
    may sit on the top, bottom, left or right edge, and the corner may be at
    either end of that edge, giving eight corner orientations.
  * Keys. There are always 2 to 4 keys with distinct hole counts. A legend
    with one key is never built, because it needs no hole comparison. By
    default the counts are drawn from 0 to 6, using only subsets that fit
    along the divider and leave room for the blobs. Each key is a 3-thick
    bar of length max(3, 2h+1) with h single-cell holes. Keys are separated
    by 1-cell gaps. This template matches all four fixtures.
  * Key colours. Key colours are distinct and come from {1,2,3,4,6,7,8,9}.
    A key may be colour 1, but it never touches the divider or the border.
  * Grey blobs. Blobs are irregular and 4-connected, at most 12x12. Each
    starts as a box with h holes, placed either as random 1x1..3x3
    rectangles or on an odd-cell lattice. It is then eroded to 50-100% of
    its cells, so holes may grow irregularly. A 0-hole blob keeps at least
    6 cells, so a blob's size does not give away its hole count.
  * Blob hole counts. Every key hole count appears on at least one blob.
    Distractor blobs (0-2 per scene) carry a count from 0 to 6 that the
    legend lacks, and those blobs are erased. Distractor counts are biased
    toward key count +/- 1 (near misses).
  * Corner ambiguity guard. An L divider is itself a 0-hole colour-1 shape.
    If a corner scene held a 0-hole grey blob but no 0-hole key, then a
    reader who took the L for a key would paint that blob 1 instead of
    erasing it. So corner scenes hold 0-hole blobs only when a 0-hole key
    exists, as in train 2. In about half of default corner scenes a 0-hole
    key is forced, so 0-hole blobs do appear next to the L divider.
  * Validity. A blob's hole count is the same under 4- and 8-connectivity
    of the background. Blob bounding boxes are at least one cell apart.
    They keep one blank cell between themselves and the divider's bounding
    region. Background (0) covers more than half of the grid.
  * Feasibility. Requests are checked before sampling. Blob lists that
    cannot fit the field are rejected with ValueError, using a margin-aware
    area bound. When there are too many blobs, default filler blobs are
    dropped first, but a key's required count is never dropped.
  * Explicit arguments. Explicit blob_holes must contain every explicit key
    hole count. Without key_holes, the keys are drawn from the distinct
    counts in blob_holes, which must therefore number at least two.

Fixture replay: the canonical blobs are irregular hand-drawn shapes, and
writing them out as latent arguments would cost as much as the grids. So
validate() passes each canonical input through the `input_grid` option.
That option decomposes the input into latent objects:
  * a divider is a colour-1 component touching the grid border, so straight
    and L-shaped dividers are both recognised structurally;
  * keys are the other non-grey components;
  * blobs are the grey components.
Replay rejects any grid that is not a well-formed scene. A well-formed scene
has 0 as the plurality colour, at least one divider, at least one key,
pairwise distinct key hole counts and at least one grey blob. The output is
then rendered from the latent objects by the same renderer the random path
uses. input_grid cannot be combined with any other argument.
"""

import itertools
import random

import common

GREY = 5
DIVIDER = 1
KEY_COLOURS = [1, 2, 3, 4, 6, 7, 8, 9]
SIDES = ('top', 'bottom', 'left', 'right')
LAYOUTS = ('straight', 'corner')
CORNER_PROB = 0.3  # share of default scenes that try the L divider first
MAX_HOLES = 6
DEFAULT_KEY_POOL = 7  # default keys use hole counts 0..6
MIN_KEYS = 2
MAX_KEYS = 4
MAX_BLOBS = 10
MAX_BLOB_DIM = 12
MIN_SIDE = 16
MIN_ZERO_CELLS = 6  # smallest 0-hole blob, to blur size vs hole count
FILL_LIMIT = 0.6  # max share of the field taken by margin-padded min boxes
# Extra length along the divider beyond the keys themselves.
_EXTRA = {'straight': 2, 'corner': 5}
# Rows (in the legend frame) lost to the legend, the divider and its margin.
_FIELD_LOSS = {'straight': 7, 'corner': 8}

_N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_N8 = _N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def _is_int(v):
  """True for genuine ints (bools are rejected)."""
  return type(v) is int


def _as_list(name, value):
  """Copies an optional list/tuple argument; other containers are rejected."""
  if value is None:
    return None
  if not isinstance(value, (list, tuple)):
    raise ValueError('%s must be a list or tuple' % name)
  return list(value)


def _groups(cells, conn=4):
  """Splits a cell collection into connected groups, sorted row-major."""
  offs = _N4 if conn == 4 else _N8
  remaining = set(cells)
  out = []
  while remaining:
    start = min(remaining)
    remaining.discard(start)
    stack, comp = [start], [start]
    while stack:
      r, c = stack.pop()
      for dr, dc in offs:
        n = (r + dr, c + dc)
        if n in remaining:
          remaining.discard(n)
          stack.append(n)
          comp.append(n)
    out.append(sorted(comp))
  out.sort()
  return out


def _count_holes(cells, conn=4):
  """Counts background groups inside the bounding box not touching its edge."""
  rows = [r for r, _ in cells]
  cols = [c for _, c in cells]
  r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
  cellset = set(cells)
  empty = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
           if (r, c) not in cellset]
  n = 0
  for comp in _groups(empty, conn):
    if not any(r in (r0, r1) or c in (c0, c1) for r, c in comp):
      n += 1
  return n


def _valid_shape(cells, h):
  """Checks that a blob is 4-connected and has exactly h robust holes."""
  if len(cells) < 3:
    return False
  if len(_groups(cells, 4)) != 1:
    return False
  return _count_holes(cells, 4) == h and _count_holes(cells, 8) == h


def _lattice(bh, bw):
  """Number of isolated single-cell hole sites in a bh x bw box."""
  return ((bh - 1) // 2) * ((bw - 1) // 2)


def _box_ok(bh, bw, h):
  """True when a bh x bw box can start a blob with h holes."""
  if h:
    return _lattice(bh, bw) >= h
  return bh * bw >= MIN_ZERO_CELLS


def _min_area_tables():
  """Smallest bare and margin-padded box areas that can hold h holes."""
  bare, padded = [], []
  for h in range(MAX_HOLES + 1):
    lo = 2 if h == 0 else 3
    best_bare = best_padded = None
    for bh in range(lo, MAX_BLOB_DIM + 1):
      for bw in range(lo, MAX_BLOB_DIM + 1):
        if not _box_ok(bh, bw, h):
          continue
        if best_bare is None or bh * bw < best_bare:
          best_bare = bh * bw
        if best_padded is None or (bh + 1) * (bw + 1) < best_padded:
          best_padded = (bh + 1) * (bw + 1)
    bare.append(best_bare)
    padded.append(best_padded)
  return bare, padded


_MIN_AREA, _MIN_PADDED = _min_area_tables()


def _fits(counts, area):
  """Conservative test that blobs with these hole counts fit a field."""
  return (2 * sum(_MIN_AREA[h] for h in counts) <= area and
          sum(_MIN_PADDED[h] for h in counts) <= FILL_LIMIT * area)


def _random_holes(bh, bw, h, sizes):
  """Places h separated rectangular holes at random, or returns None."""
  holes, blocked = set(), set()
  for _ in range(h):
    placed = False
    for _ in range(60):
      rh = random.choice(sizes)
      rw = random.choice(sizes)
      if rh > bh - 2 or rw > bw - 2:
        continue
      r = random.randint(1, bh - 1 - rh)
      c = random.randint(1, bw - 1 - rw)
      rect = {(r + i, c + j) for i in range(rh) for j in range(rw)}
      if rect & blocked:
        continue
      holes |= rect
      blocked |= {(a + di, b + dj) for a, b in rect
                  for di in (-1, 0, 1) for dj in (-1, 0, 1)}
      placed = True
      break
    if not placed:
      return None
  return holes


def _lattice_holes(bh, bw, h):
  """Places h single-cell holes on the odd-cell lattice of the box."""
  spots = [(2 * i + 1, 2 * j + 1) for i in range((bh - 1) // 2)
           for j in range((bw - 1) // 2)]
  return set(random.sample(spots, h))


def _make_blob(h, max_r, max_c, max_area):
  """Builds an irregular 4-connected blob with h holes, or returns None."""
  lo = 2 if h == 0 else 3
  if max_r < lo or max_c < lo:
    return None
  floor = MIN_ZERO_CELLS if h == 0 else 3
  sizes = (1, 1, 1, 2, 2, 3) if h <= 3 else (1, 1, 1, 2)
  for _ in range(200):
    if random.random() < 0.5:
      bh = random.randint(lo, max(lo, min(max_r, max_area // lo)))
      bw = random.randint(lo, max(lo, min(max_c, max_area // bh)))
    else:
      bw = random.randint(lo, max(lo, min(max_c, max_area // lo)))
      bh = random.randint(lo, max(lo, min(max_r, max_area // bw)))
    if bh > max_r or bw > max_c:
      continue
    if not _box_ok(bh, bw, h):
      continue
    holes = None
    if random.random() < 0.85:
      holes = _random_holes(bh, bw, h, sizes)
    if holes is None:
      holes = _lattice_holes(bh, bw, h)
    cells = {(r, c) for r in range(bh) for c in range(bw)} - holes
    if len(cells) < floor or not _valid_shape(cells, h):
      continue
    target = max(floor, int(len(cells) * random.uniform(0.5, 1.0)))
    for _ in range(2 * bh * bw):
      if len(cells) <= target:
        break
      edge = sorted(p for p in cells
                    if any((p[0] + dr, p[1] + dc) not in cells
                           for dr, dc in _N4))
      cell = random.choice(edge)
      trial = cells - {cell}
      if _valid_shape(trial, h):
        cells = trial
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)
  return None


def _key_len(h):
  """Length along the divider of a key with h holes."""
  return max(3, 2 * h + 1)


def _key_template(h):
  """Key cells in (cross, along) coordinates: a 3-thick bar with h holes."""
  hole = {(1, 2 * j + 1) for j in range(h)}
  return [(i, j) for i in range(3) for j in range(_key_len(h))
          if (i, j) not in hole]


def _legend_length(kh):
  """Length along the divider of the legend keys with 1-cell gaps."""
  return sum(_key_len(h) for h in kh) + len(kh) - 1


def _place(shapes, rows, cols, blocked):
  """Places shapes in a rows x cols frame avoiding blocked cells.

  Bounding boxes keep a 1-cell gap from each other. Each shape is placed at
  a uniformly random free spot; None is returned when no spot remains.
  """
  occ = [list(row) for row in blocked]
  placed = []
  for shape in shapes:
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    if sh > rows or sw > cols:
      return None
    ps = [[0] * (cols + 1) for _ in range(rows + 1)]
    for r in range(rows):
      acc = 0
      for c in range(cols):
        acc += 1 if occ[r][c] else 0
        ps[r + 1][c + 1] = ps[r][c + 1] + acc
    cands = [(r, c) for r in range(rows - sh + 1)
             for c in range(cols - sw + 1)
             if ps[r + sh][c + sw] - ps[r][c + sw] - ps[r + sh][c] +
             ps[r][c] == 0]
    if not cands:
      return None
    r0, c0 = random.choice(cands)
    for r in range(max(0, r0 - 1), min(rows, r0 + sh + 1)):
      for c in range(max(0, c0 - 1), min(cols, c0 + sw + 1)):
        occ[r][c] = True
    placed.append([(r0 + a, c0 + b) for a, b in shape])
  return placed


def _dims_for(side, width, height):
  """(along, cross) for a side, using 30 for unspecified sizes."""
  w = width if width is not None else 30
  h = height if height is not None else 30
  return (w, h) if side in ('top', 'bottom') else (h, w)


def _field_lb(lay, along, cross):
  """Lower bound on blob-field cells for a layout."""
  return along * (cross - _FIELD_LOSS[lay])


def _key_count_choices(pool, kc):
  """Possible numbers of keys for the sampler (always at least two)."""
  if kc is not None:
    return [len(kc)]
  return list(range(MIN_KEYS, min(MAX_KEYS, len(pool)) + 1))


def _pool(bl):
  """Candidate key hole counts when key_holes is not given."""
  if bl is not None:
    return sorted(set(bl))
  return list(range(DEFAULT_KEY_POOL))


def _combo_ok(lay, combo, bl):
  """Corner scenes may only hold 0-hole blobs when a 0-hole key exists."""
  if lay != 'corner' or bl is None:
    return True
  return 0 not in bl or 0 in combo


def _min_legend(kh, kc, bl):
  """Shortest legend the sampler may build for these arguments."""
  if kh is not None:
    return _legend_length(kh)
  pool = sorted(_pool(bl))
  return min(_legend_length(pool[:k]) for k in _key_count_choices(pool, kc))


def _feasible(width, height, sides, layouts, kh, kc, bl):
  """True when some side and layout admit a legend and blobs that fit."""
  for s in sides:
    along, cross = _dims_for(s, width, height)
    for lay in layouts:
      area = _field_lb(lay, along, cross)
      if kh is not None:
        combos = [kh]
      else:
        pool = _pool(bl)
        combos = [c for k in _key_count_choices(pool, kc)
                  for c in itertools.combinations(pool, k)]
      for combo in combos:
        if (_legend_length(combo) + _EXTRA[lay] <= along and
            _combo_ok(lay, combo, bl) and
            _fits(bl if bl is not None else combo, area)):
          return True
  return False


def _check_args(width, height, side, divider, kh, kc, bl):
  """Rejects out-of-domain or mutually inconsistent scene parameters."""
  for name, v in (('width', width), ('height', height)):
    if v is not None and not (_is_int(v) and MIN_SIDE <= v <= 30):
      raise ValueError('%s must be an int in %d..30' % (name, MIN_SIDE))
  if side is not None and (not isinstance(side, str) or side not in SIDES):
    raise ValueError('side must be one of %s' % (SIDES,))
  if divider is not None and (not isinstance(divider, str) or
                              divider not in LAYOUTS):
    raise ValueError('divider must be one of %s' % (LAYOUTS,))
  if bl is not None:
    if not 1 <= len(bl) <= MAX_BLOBS:
      raise ValueError('blob_holes must have 1..%d entries' % MAX_BLOBS)
    if any(not (_is_int(h) and 0 <= h <= MAX_HOLES) for h in bl):
      raise ValueError('blob hole counts must be ints in 0..%d' % MAX_HOLES)
  if kc is not None:
    if not MIN_KEYS <= len(kc) <= MAX_KEYS:
      raise ValueError('key_colours must have %d..%d entries'
                       % (MIN_KEYS, MAX_KEYS))
    if any(not _is_int(c) or c not in KEY_COLOURS for c in kc):
      raise ValueError('key colours must be ints from %s' % KEY_COLOURS)
    if len(set(kc)) != len(kc):
      raise ValueError('key colours must be distinct')
  sides = [side] if side is not None else list(SIDES)
  layouts = [divider] if divider is not None else list(LAYOUTS)
  if kh is not None:
    if not MIN_KEYS <= len(kh) <= MAX_KEYS:
      raise ValueError('key_holes must have %d..%d entries'
                       % (MIN_KEYS, MAX_KEYS))
    if any(not (_is_int(h) and 0 <= h <= MAX_HOLES) for h in kh):
      raise ValueError('key hole counts must be ints in 0..%d' % MAX_HOLES)
    if len(set(kh)) != len(kh):
      raise ValueError('key hole counts must be distinct')
    if kc is not None and len(kc) != len(kh):
      raise ValueError('key_colours must match key_holes in length')
    if bl is not None and not set(kh) <= set(bl):
      raise ValueError('every key hole count must appear in blob_holes')
    if (divider == 'corner' and bl is not None and 0 in bl and
        0 not in kh):
      raise ValueError('with a corner divider, 0-hole blobs need a 0-hole key')
    if all(_legend_length(kh) + _EXTRA[l] > _dims_for(s, width, height)[0]
           for s in sides for l in layouts):
      raise ValueError('legend for key_holes does not fit along the divider')
  else:
    pool = _pool(bl)
    if len(pool) < MIN_KEYS:
      raise ValueError('blob_holes needs at least %d distinct hole counts'
                       % MIN_KEYS)
    if kc is not None and len(kc) > len(pool):
      raise ValueError('more keys requested than distinct blob hole counts')
  if not _feasible(width, height, sides, layouts, kh, kc, bl):
    raise ValueError('requested legend and blobs do not fit the grid')


def _choose_key_holes(lay, along, area, kh, kc, bl):
  """Chooses legend hole counts that fit this side and layout, or None."""
  need = _EXTRA[lay]
  if kh is not None:
    ok = (_legend_length(kh) + need <= along and _combo_ok(lay, kh, bl) and
          _fits(bl if bl is not None else kh, area))
    return list(kh) if ok else None
  if bl is not None and not _fits(bl, area):
    return None
  pool = _pool(bl)
  k = random.choice(_key_count_choices(pool, kc))
  combos = [list(c) for c in itertools.combinations(pool, k)
            if _legend_length(c) + need <= along and
            _combo_ok(lay, c, bl) and
            (bl is not None or _fits(c, area))]
  if lay == 'corner' and bl is None and random.random() < 0.5:
    zero = [c for c in combos if 0 in c]  # train-2 style: solid key + L
    if zero:
      combos = zero
  if not combos:
    return None
  chosen = random.choice(combos)
  if random.random() < 0.5:
    random.shuffle(chosen)
  return chosen


def _default_blob_counts(kh, area, lay):
  """Default blob hole counts: every key count, near-miss distractors, filler."""
  n = random.randint(4, max(4, min(8, area // 65)))
  others = [h for h in range(MAX_HOLES + 1) if h not in kh and
            not (lay == 'corner' and h == 0)]
  nd = random.choice([0, 1, 1, 2]) if others else 0
  extras = []
  if nd:
    weights = [3 if any(abs(h - k) == 1 for k in kh) else 1 for h in others]
    extras = random.choices(others, weights=weights, k=nd)
  while len(kh) + len(extras) < n:
    extras.append(random.choice(kh))
  while extras and not _fits(list(kh) + extras, area):
    extras.pop()  # filler goes first, then distractors; keys stay
  counts = list(kh) + extras
  random.shuffle(counts)
  return counts


def _build(sd, lay, kh, along, cross, kc, bl_arg):
  """Builds one scene in a legend frame, mapped to the grid; None on failure.

  The legend frame has rows = cross index i (0 at the legend edge) and
  columns = along index j. It is mirrored and/or transposed onto the grid,
  which preserves connectivity and hole counts.
  """
  horiz = sd in ('top', 'bottom')
  W, H = (along, cross) if horiz else (cross, along)
  flip_i = sd in ('bottom', 'right')
  flip_j = random.random() < 0.5

  def to_rc(i, j):
    if flip_i:
      i = cross - 1 - i
    if flip_j:
      j = along - 1 - j
    return (i, j) if horiz else (j, i)

  colours = list(kc) if kc is not None else random.sample(KEY_COLOURS,
                                                            len(kh))
  L = _legend_length(kh)
  if lay == 'straight':
    div = 5
    pos = random.randint(1, along - 1 - L)
    div_cells = [(div, j) for j in range(along)]
    blocked = [[i <= div + 1] * along for i in range(cross)]
    field = along * (cross - div - 2)
  else:
    div = random.choice((5, 6))
    pos = 1
    arm = 1 + L + random.randint(1, min(2, along - 4 - L))
    div_cells = ([(div, j) for j in range(arm + 1)] +
                 [(i, arm) for i in range(div)])
    blocked = [[i <= div + 1 and j <= arm + 1 for j in range(along)]
               for i in range(cross)]
    field = cross * along - (div + 2) * (arm + 2)

  divider = sorted(to_rc(i, j) for i, j in div_cells)
  keys = []
  for h, colour in zip(kh, colours):
    cells = sorted(to_rc(1 + i, pos + j) for i, j in _key_template(h))
    keys.append((colour, h, cells))
    pos += _key_len(h) + 1

  bl = list(bl_arg) if bl_arg is not None else _default_blob_counts(
      kh, field, lay)
  if not _fits(bl, field):
    return None
  budget = int(field * 0.38 / len(bl))
  max_r = min(MAX_BLOB_DIM, cross - div - 2)
  max_c = min(MAX_BLOB_DIM, along)
  items = []
  for h in bl:
    shape = _make_blob(h, max_r, max_c,
                       max(budget, (3 * _MIN_AREA[h]) // 2))
    if shape is None:
      return None
    items.append((h, shape))
  items.sort(key=lambda it: -((max(r for r, _ in it[1]) + 1) *
                              (max(c for _, c in it[1]) + 1)))
  placed = None
  for _ in range(3):
    placed = _place([s for _, s in items], cross, along, blocked)
    if placed is not None:
      break
  if placed is None:
    return None
  blobs = [(h, sorted(to_rc(i, j) for i, j in cells))
           for (h, _), cells in zip(items, placed)]
  used = len(divider) + sum(len(c) for _, _, c in keys)
  used += sum(len(c) for _, c in blobs)
  if 2 * used >= H * W:
    return None
  return {'height': H, 'width': W, 'dividers': [(DIVIDER, divider)],
          'keys': keys, 'blobs': blobs}


def _sample_scene(width, height, side, layout_arg, kh_arg, kc, bl_arg):
  """Samples latent objects: divider, legend keys and grey blobs."""
  base = _min_legend(kh_arg, kc, bl_arg)
  for attempt in range(80):
    lo = min(30, 18 + attempt // 5)  # later retries favour roomier grids
    if layout_arg is not None:
      layouts = [layout_arg]
    elif random.random() < CORNER_PROB:
      layouts = ['corner', 'straight']
    else:
      layouts = ['straight', 'corner']
    choice = None
    for lay in layouts:
      sides = [side] if side is not None else list(SIDES)
      random.shuffle(sides)
      for sd in sides:
        horiz = sd in ('top', 'bottom')
        along_arg = width if horiz else height
        cross_arg = height if horiz else width
        if along_arg is None:
          a_lo = max(lo, base + _EXTRA[lay])
          if a_lo > 30:
            continue
          along = random.randint(a_lo, 30)
        else:
          along = along_arg
        cross = cross_arg if cross_arg is not None else random.randint(lo, 30)
        kh = _choose_key_holes(lay, along, _field_lb(lay, along, cross),
                               kh_arg, kc, bl_arg)
        if kh is not None:
          choice = (sd, lay, kh, along, cross)
          break
      if choice is not None:
        break
    if choice is None:
      continue
    scene = _build(choice[0], choice[1], choice[2], choice[3], choice[4],
                   kc, bl_arg)
    if scene is not None:
      return scene
  raise ValueError('could not construct scene for the requested parameters')


def _check_grid(grid):
  """Validates a replay grid: rectangular, 1..30 per side, ints 0..9."""
  if not isinstance(grid, list) or not 1 <= len(grid) <= 30:
    raise ValueError('input_grid must be a list of 1..30 rows')
  width = len(grid[0]) if isinstance(grid[0], list) else 0
  if not 1 <= width <= 30:
    raise ValueError('input_grid rows must have 1..30 cells')
  for row in grid:
    if not isinstance(row, list) or len(row) != width:
      raise ValueError('input_grid must be rectangular')
    if any(not _is_int(v) or not 0 <= v <= 9 for v in row):
      raise ValueError('input_grid cells must be ints 0..9')


def _parse(grid):
  """Decomposes a fixture input into divider, key and blob latents."""
  H, W = len(grid), len(grid[0])
  by_colour = {}
  for r in range(H):
    for c in range(W):
      if grid[r][c] != 0:
        by_colour.setdefault(grid[r][c], []).append((r, c))
  comps = []
  for colour, cells in by_colour.items():
    for comp in _groups(cells, 4):
      comps.append((comp[0], colour, comp))
  comps.sort()
  dividers, keys, blobs = [], [], []
  for _, colour, comp in comps:
    if colour == GREY:
      blobs.append((_count_holes(comp), comp))
    elif any(r in (0, H - 1) or c in (0, W - 1) for r, c in comp):
      dividers.append((colour, comp))
    else:
      keys.append((colour, _count_holes(comp), comp))
  return {'height': H, 'width': W, 'dividers': dividers, 'keys': keys,
          'blobs': blobs}


def _check_scene(grid, scene):
  """Rejects replay grids that are not well-formed legend scenes."""
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  zeros = counts.get(0, 0)
  if any(v != 0 and n >= zeros for v, n in counts.items()):
    raise ValueError('replay background 0 must be the plurality colour')
  if not scene['dividers']:
    raise ValueError('replay grid has no border-touching divider')
  if any(colour != DIVIDER for colour, _ in scene['dividers']):
    raise ValueError('replay divider components must be colour 1')
  if not scene['keys']:
    raise ValueError('replay grid has no legend keys')
  holes = [h for _, h, _ in scene['keys']]
  if len(set(holes)) != len(holes):
    raise ValueError('replay legend has two keys with the same hole count')
  if not scene['blobs']:
    raise ValueError('replay grid has no grey blobs')


def _render(scene):
  """Draws the input grid and builds the answer from the latent objects."""
  H, W = scene['height'], scene['width']
  inp = common.grid(W, H, 0)
  out = common.grid(W, H, 0)
  for colour, cells in scene['dividers']:
    for r, c in cells:
      inp[r][c] = colour
      out[r][c] = colour
  legend = {}
  for colour, h, cells in scene['keys']:
    for r, c in cells:
      inp[r][c] = colour
      out[r][c] = colour
    legend[h] = colour
  for h, cells in scene['blobs']:
    target = legend.get(h, 0)
    for r, c in cells:
      inp[r][c] = GREY
      out[r][c] = target
  return {'input': inp, 'output': out}


def generate(width=None, height=None, side=None, key_holes=None,
             key_colours=None, blob_holes=None, divider=None,
             input_grid=None):
  """Returns an input/output pair for the hole-count legend task.

  Args:
    width: grid width, 16-30. Random 18-30 when None (or longer if the
      legend runs along the width and needs it).
    height: grid height, 16-30. Random 18-30 when None (same caveat).
    side: legend edge, one of 'top', 'bottom', 'left' or 'right'. When None,
      a side is chosen at random among those where the scene fits.
    key_holes: list or tuple of 2-4 distinct hole counts (0-6) for the keys.
      Order is kept along the divider (possibly read from the far end).
    key_colours: list or tuple of 2-4 distinct key colours from
      {1,2,3,4,6,7,8,9}, paired in order with the keys. Its length must
      match key_holes when both are given. Given alone, it sets the number
      of keys, and the counts are sampled among the subsets that fit.
    blob_holes: list or tuple of 1-10 hole counts (0-6) for the grey blobs.
      It must contain every key_holes count. Without key_holes, the keys are
      drawn from its distinct counts, so it needs at least two of them.
    divider: 'straight' (full row/column) or 'corner' (L shape boxing the
      legend into a grid corner). When None, the corner layout is tried
      first in about 30% of scenes. With 'corner', 0-hole blobs require a
      0-hole key; contradicting explicit lists are rejected.
    input_grid: fixture replay only. The grid is checked to be a
      well-formed scene and decomposed into latent divider, key and blob
      objects, and the pair is rendered from those. It cannot be combined
      with any other argument.
  """
  if input_grid is not None:
    if any(v is not None for v in (width, height, side, key_holes,
                                   key_colours, blob_holes, divider)):
      raise ValueError('input_grid replay cannot be combined with parameters')
    _check_grid(input_grid)
    scene = _parse(input_grid)
    _check_scene(input_grid, scene)
    return _render(scene)
  kh = _as_list('key_holes', key_holes)
  kc = _as_list('key_colours', key_colours)
  bl = _as_list('blob_holes', blob_holes)
  _check_args(width, height, side, divider, kh, kc, bl)
  scene = _sample_scene(width, height, side, divider, kh, kc, bl)
  return _render(scene)


_TRAIN1 = [
    '000000000000000000000000000000', '044403330111110222222200000000',
    '044403030101010202020200000000', '044403330111110222222200000000',
    '000000000000000000000000000000', '111111111111111111111111111111',
    '000000000000000000000000000000', '000000000000000000000000000000',
    '000000000055000000000000000000', '000555000555000000000000000000',
    '005505505555000000000000000000', '005505505500000000005555550000',
    '000555500000550000055000550000', '000000000005550000555555500000',
    '000000000555550005500055000000', '000000000555500005555555000000',
    '000005000000000000555000000000', '000555500000000000000000000000',
    '000500500000000000000000000000', '000555500000005500000000555500',
    '000555000000555550000055505500', '000000000000505050000555500500',
    '000000555500555555000550555500', '000005550500505550000550055500',
    '000555550500555000000055555000', '005555055500000000000000000000',
    '005505055500000005550000000000', '005555555500000055555500000000',
    '005505555000000055555500000000', '000555550000000005550000000000',
]

_TRAIN2 = [
    '000000000100000000000000000000', '022203330100000000550000000000',
    '022203030100005555555555000000', '022203330100055555555555000000',
    '000000000100055555555555500000', '000000000100005555555555500000',
    '111111111100005555555555000000', '000000000000000055555000000000',
    '000000000000000000000000005500', '000000000055500000005555555500',
    '000000000005500000005550055500', '000055000000000000055500055550',
    '005555550000000000055500055550', '005555555000000000005500055550',
    '005555555000555500005555555500', '055555555000555000000550000000',
    '005555550000555500000000000000', '000055000005555500000000000000',
    '000000000005555500000000000000', '000000000005555000005555500000',
    '000000000000555000005505500000', '000000000000555000005005500000',
    '000055550000000000005005000000', '000050055000500000005555500000',
    '000550050005555555005555000000', '000550550005050055000000000000',
    '000055550005050055000000000000', '000000500005555550000000000000',
    '000000000000500000000000000000', '000000000000000000000000000000',
]

_TEST1 = [
    '000000000550000000000000100000', '005500000555000000000000108880',
    '055555550555005555500000108080', '050550050000055000500000108880',
    '050050050000050000505550108080', '055550050000055005505050108880',
    '005550550000005555005550100000', '000055500555000000000000106660',
    '550000000555500000000000106060', '550000000555500055555500106660',
    '555000000055005550055550106060', '555005550000055550550050106660',
    '555055055550050055500050106060', '550050005050050005550050106660',
    '000055005550055005055550106060', '000005555555005555000550106660',
    '000000000055500055550500100000', '005500000005500000055500104440',
    '055555000000000000000000104040', '555555500055555550000000104440',
    '055555500555500055550000104040', '000000000500500000555500104440',
    '000000005500500005505500104040', '055000055000500055005000104440',
    '055500555000500550005000104040', '055505505555555500005000104440',
    '055005000555055000005000104040', '000005000050005000055000104440',
    '000005500050005000550000100000', '000000555555555555500000100000',
]

_TEST2 = [
    '000001000000000000000000000000', '044401000555555500000000000000',
    '040401005555555500005555500000', '044401005555500500555505500000',
    '000001005555555500555555550000', '077701000055550000505555555000',
    '070701000000000000555555555000', '077701000000000000555555500000',
    '070701000000555500555555000000', '077701000000500500000550005555',
    '000001000005555550000000055555', '022201000055505550000000055550',
    '020201000055555550000000055550', '022201000000555500000000000500',
    '020201000000000000000000000000', '022201000000000055000055550000',
    '020201000000000555000555055500', '022201000000000055005555055500',
    '000001000000000000050555555500', '011101000555550000050055555000',
    '010101055005050000055005555000', '011101055555555000005555555000',
    '010101055555555000005500555000', '011101055555555000005500550000',
    '010101055555555000005555500000', '011101055550055000000000000000',
    '010101055055555000500000005550', '011101005555550000555000005550',
    '000001000005500005555500005550', '000001000000000000555000000000',
]


def _decode(rows):
  """Turns compact digit strings back into a grid."""
  return [[int(ch) for ch in row] for row in rows]


def validate():
  """Rebuilds the canonical fixtures through generate(input_grid=...)."""
  train = [generate(input_grid=_decode(rows)) for rows in (_TRAIN1, _TRAIN2)]
  test = [generate(input_grid=_decode(rows)) for rows in (_TEST1, _TEST2)]
  return {'train': train, 'test': test}
