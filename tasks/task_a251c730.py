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

"""ARC task a251c730: stamp motifs from one framed box onto markers in another.

Rule: the input is a wallpaper of 1-cell-wide stripes. The stripes run
horizontally or vertically and cycle through distinct colours. Two framed
rectangles sit on the wallpaper.
- The motif box holds complete motifs. Each motif has a body colour and one
  anchor cell. The anchor's colour occurs exactly once in that motif.
- The marker box holds lone cells in anchor colours.
- The output is the marker box, cropped with its frame. Each marker is
  replaced by the motif whose unique anchor has the marker's colour. The
  motif is translated so that its anchor lands on the marker.

Anchors are told apart from bodies by multiplicity, not by colour alone. A
body colour occurs at least twice inside its motif. A marker is matched only
by a singly-occurring colour, so the body of one motif type may reuse the
anchor colour of another type.

Scope:
- Motif types: 1-4, drawn from a library of small two-colour shapes, each
  at most 3x3, under random rotation and reflection. All copies of one type
  are identical. Explicit scenes are rejected if one anchor colour is used
  by two different patterns, even when no marker uses that anchor.
- Hard negatives: in about 40% of multi-type scenes, the body colour of one
  or two types equals the anchor colour of another type that a marker uses.
  A solver that matches "the motif containing the marker colour anywhere"
  then fails.
- Distractors: in about 25% of multi-type scenes, one motif type is not used
  by any marker.
- Motif box: holds every type at least once, 2-8 motifs in total. Marker
  box: holds 2-8 markers. Stamped motifs fit inside the marker interior. They
  may touch its frame but never touch another stamp.
- Layout: the boxes are stacked or side by side. At least one wallpaper cell
  separates the boxes from each other and from the grid border.
- Box dimensions are conditioned on the canvas and on the sampled shapes.
  - The along-axis extent of the motif box is at least (tallest motif + 4);
    that of the marker box is at least (tallest used stamp + 2); both are
    at least 5.
  - Along-axis caps are 20 (motif) and 16 (marker), limited by the canvas.
  - Both boxes allow cross-axis extents up to min(24, size - 2). This
    covers the canonical 20-wide and 19-tall marker boxes.
  - A cheap packing-area bound rejects infeasible draws before placement.
- The frame colour of the motif box may coincide with stripe, anchor or body
  colours, as it does in the original pairs.
- Grid size: grids are square. The original task always uses 30x30. Random
  sizes 14-29 are a synthetic extension of the same rule. Auto-chosen sizes
  rise with the requested counts and fall back to 30 when needed.

Not supported: motifs with more than two colours or larger than 3x3,
stripes wider than one cell, stamps clipped by the frame, overlapping
stamps, more than two boxes, and boxes touching the grid border.
"""

import collections
import random

import common


# Shape library: B = body colour, A = unique anchor colour, . = empty.
#
# Spurious-box safety argument. A body component whose bounding box is 3x3
# is ringed by the motif-box interior colour, so it looks like a tiny framed
# box to a box detector.
# - Its non-body cells form exactly one 8-connected group (checked by
#   _spurious_size). The group is either a single lone cell, which loses to
#   the >= 2 real markers, or one multi-cell object of 9 - |B| cells.
# - The real motif box holds strictly more motif cells than any such group
#   (checked in _check_scene), so it is always the largest motif candidate.
SHAPES = [
    ['B.B', 'BBB', '.A.'],
    ['.B.', 'BAB', '.B.'],
    ['.B.', 'BAB', 'BBB'],
    ['BBB', 'BAB'],
    ['BBB', 'BAB', 'BBB'],
    ['BAB'],
    ['B.B', '.A.', 'B.B'],
    ['BBB', '.A.'],
    ['A.', 'BB'],
    ['BB.', 'BAB'],
    ['BB', 'BA'],
    ['.B.', 'BAB'],
    ['BAB', 'B.B', 'BBB'],
    ['B.B', 'BAB'],
]

DIGITS = '0123456789'
MIN_RANDOM_SIZE = 14


def _is_int(x):
  return isinstance(x, int) and not isinstance(x, bool)


def _need_int(name, x, lo, hi):
  if not _is_int(x) or not lo <= x <= hi:
    raise ValueError('%s must be an integer in %d..%d' % (name, lo, hi))


def _rot(p):
  h, w = len(p), len(p[0])
  return [''.join(p[h - 1 - r][c] for r in range(h)) for c in range(w)]


def _orient(shape):
  p = list(shape)
  for _ in range(random.randint(0, 3)):
    p = _rot(p)
  if random.random() < 0.5:
    p = [row[::-1] for row in p]
  return p


def _paint(shape, body, anchor):
  rows = []
  for row in shape:
    s = ''
    for ch in row:
      if ch == 'B':
        s += str(body)
      elif ch == 'A':
        s += str(anchor)
      else:
        s += '.'
    rows.append(s)
  return rows


def _cells(pattern):
  out = []
  for r, row in enumerate(pattern):
    for c, ch in enumerate(row):
      if ch != '.':
        out.append((r, c, int(ch)))
  return out


def _components8(cells):
  """Split a collection of (row, col) cells into 8-connected groups."""
  left = set(cells)
  comps = []
  for start in sorted(left):
    if start not in left:
      continue
    left.discard(start)
    comp = [start]
    stack = [start]
    while stack:
      r, c = stack.pop()
      for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
          n = (r + dr, c + dc)
          if n in left:
            left.discard(n)
            comp.append(n)
            stack.append(n)
    comps.append(comp)
  return comps


def _separated(a, b):
  """True when rectangles (r, c, h, w) are at least one cell apart."""
  r1, c1, h1, w1 = a[:4]
  r2, c2, h2, w2 = b[:4]
  return r1 + h1 < r2 or r2 + h2 < r1 or c1 + w1 < c2 or c2 + w2 < c1


def _place(sizes, h, w, margin):
  """Place (height, width) rectangles in an h x w area with 1-cell gaps.

  Larger rectangles go first. Each one picks uniformly among all legal
  positions left by those already placed. Returns top-left offsets in the
  original order, or None when some rectangle cannot be placed.
  """
  order = sorted(range(len(sizes)), key=lambda i: -sizes[i][0] * sizes[i][1])
  placed = {}
  for i in order:
    ph, pw = sizes[i]
    cands = []
    for r in range(margin, h - margin - ph + 1):
      for c in range(margin, w - margin - pw + 1):
        rect = (r, c, ph, pw)
        if all(_separated(rect, q) for q in placed.values()):
          cands.append(rect)
    if not cands:
      return None
    placed[i] = random.choice(cands)
  return [(placed[i][0], placed[i][1]) for i in range(len(sizes))]


def _place_shrink(pats, types, required, h, w, margin):
  """Place copies of the given types, dropping duplicate copies on failure.

  Every distinct type keeps at least one copy, and the list never shrinks
  below `required`. Returns (types, offsets) or (None, None).
  """
  types = list(types)
  for _ in range(len(types) + 1):
    pos = _place([(len(pats[t]), len(pats[t][0])) for t in types], h, w,
                 margin)
    if pos is not None:
      return types, pos
    if len(types) <= required:
      return None, None
    counts = collections.Counter(types)
    dups = [i for i, t in enumerate(types) if counts[t] > 1]
    if not dups:
      return None, None
    types.pop(random.choice(dups))
  return None, None


def _area(pats, types):
  """Packing area of separated rectangles, each grown by one row/column."""
  return sum((len(pats[t]) + 1) * (len(pats[t][0]) + 1) for t in types)


def _anchor_pos(pattern, colour):
  for r, c, v in _cells(pattern):
    if v == colour:
      return r, c
  return None


def _check_stripes(stripes):
  if not isinstance(stripes, (list, tuple)) or len(stripes) < 2:
    raise ValueError('stripes needs at least two colours')
  for s in stripes:
    _need_int('stripe colour', s, 0, 9)
  if len(set(stripes)) != len(stripes):
    raise ValueError('stripe colours must be distinct')


def _sample_scene(size, num_types, num_markers):
  """Sample latent boxes, motifs and markers, or return None on failure."""
  inner = size - 2
  if size >= 22:
    kmax, hi = 4, 8
  elif size >= 18:
    kmax, hi = 3, 6
  else:
    kmax, hi = 2, 4
  for _ in range(300):
    if num_types is not None:
      k = num_types
    else:
      k = random.choice([x for x in (1, 1, 2, 2, 3, 4) if x <= kmax])
    anchors = random.sample(range(10), k)
    # Types used by markers. Occasionally leave a distractor type unused.
    used_types = list(range(k))
    random.shuffle(used_types)
    if k > 1 and random.random() < 0.25:
      used_types = used_types[:-1]
    if num_markers is not None:
      n_s = num_markers
      used_types = used_types[:n_s]
    else:
      n_s = random.randint(max(2, len(used_types)), max(hi, len(used_types)))
    rest = [c for c in range(10) if c not in anchors]
    bodies = [random.choice(rest) for _ in range(k)]
    # Hard negative: a body reuses the anchor colour of a used type.
    if k > 1 and random.random() < 0.4:
      pairs = [(i, j) for j in used_types for i in range(k) if i != j]
      for i, j in random.sample(pairs, min(len(pairs),
                                           random.choice([1, 1, 2]))):
        bodies[i] = anchors[j]
    used = set(anchors) | set(bodies)
    free = [c for c in range(10) if c not in used]
    b_a = random.choice(free)
    b_b = random.choice(free)
    f_a = random.choice([c for c in range(10) if c != b_a])
    f_b = random.choice([c for c in free if c != b_b])
    shapes = random.sample(SHAPES, k)
    pats = [_paint(_orient(s), bodies[i], anchors[i])
            for i, s in enumerate(shapes)]
    stacked = random.random() < 0.5
    if stacked:
      al = [len(p) for p in pats]
      cr = [len(p[0]) for p in pats]
    else:
      al = [len(p[0]) for p in pats]
      cr = [len(p) for p in pats]
    amin = max(5, max(al) + 4)
    camin = max(5, max(cr) + 4)
    bmin = max(5, max(al[t] for t in used_types) + 2)
    cbmin = max(5, max(cr[t] for t in used_types) + 2)
    if amin + bmin + 1 > inner or max(camin, cbmin) > inner:
      continue
    a = random.randint(amin, min(20, inner - bmin - 1))
    b = random.randint(bmin, min(16, inner - a - 1))
    gap = random.randint(1, inner - a - b)
    start = 1 + random.randint(0, inner - a - b - gap)
    if random.random() < 0.5:
      pa, pb = start, start + a + gap
    else:
      pb, pa = start, start + b + gap
    ca = random.randint(camin, min(24, inner))
    cb = random.randint(cbmin, min(24, inner))
    qa = 1 + random.randint(0, inner - ca)
    qb = 1 + random.randint(0, inner - cb)
    if stacked:
      t1, l1, hh1, ww1 = pa, qa, a, ca
      t2, l2, hh2, ww2 = pb, qb, b, cb
    else:
      t1, l1, hh1, ww1 = qa, pa, ca, a
      t2, l2, hh2, ww2 = qb, pb, cb, b
    types_s = used_types + [random.choice(used_types)
                            for _ in range(n_s - len(used_types))]
    random.shuffle(types_s)
    need_s = n_s if num_markers is not None else max(2, len(used_types))
    need_m = max(2, k)
    n_m = min(8, need_m + random.choice([0, 0, 1, 1, 2, 3, 4, 6]))
    types_m = list(range(k)) + [random.randrange(k) for _ in range(n_m - k)]
    random.shuffle(types_m)
    min_m = list(range(k)) if k >= 2 else [0, 0]
    if num_markers is not None:
      min_s = types_s
    elif len(used_types) >= 2:
      min_s = used_types
    else:
      min_s = used_types * 2
    if (_area(pats, min_m) > (hh1 - 3) * (ww1 - 3) or
        _area(pats, min_s) > (hh2 - 1) * (ww2 - 1)):
      continue
    types_m, pos_m = _place_shrink(pats, types_m, need_m, hh1 - 2, ww1 - 2, 1)
    if pos_m is None:
      continue
    types_s, pos_s = _place_shrink(pats, types_s, need_s, hh2 - 2, ww2 - 2, 0)
    if pos_s is None:
      continue
    motifs = [(t1 + 1 + r, l1 + 1 + c, pats[t])
              for (r, c), t in zip(pos_m, types_m)]
    markers = []
    for (r, c), t in zip(pos_s, types_s):
      ar, ac = _anchor_pos(pats[t], anchors[t])
      markers.append((t2 + 1 + r + ar, l2 + 1 + c + ac, anchors[t]))
    motif_box = (t1, l1, hh1, ww1, f_a, b_a)
    marker_box = (t2, l2, hh2, ww2, f_b, b_b)
    try:
      _check_scene(size, motif_box, motifs, marker_box, markers)
    except ValueError:
      continue
    return {'motif_box': motif_box, 'motifs': motifs,
            'marker_box': marker_box, 'markers': markers}
  return None


def _check_box(box, size, name):
  if (not isinstance(box, (list, tuple)) or len(box) != 6 or
      not all(_is_int(x) for x in box)):
    raise ValueError('%s must be six integers' % name)
  t, l, h, w, f, b = box
  if h < 5 or w < 5:
    raise ValueError('%s must be at least 5x5 including the frame' % name)
  if t < 1 or l < 1 or t + h > size - 1 or l + w > size - 1:
    raise ValueError('%s must leave one wallpaper cell to the border' % name)
  if not 0 <= f <= 9 or not 0 <= b <= 9:
    raise ValueError('%s colours must be 0..9' % name)
  if f == b:
    raise ValueError('%s frame and interior colours must differ' % name)


def _inside(box, r, c, margin):
  t, l, h, w = box[:4]
  return (t + 1 + margin <= r < t + h - 1 - margin and
          l + 1 + margin <= c < l + w - 1 - margin)


def _check_pattern(pat):
  """Validate a motif pattern; return (body, anchor)."""
  if not isinstance(pat, (list, tuple)) or not pat:
    raise ValueError('motif pattern must be a non-empty list of strings')
  if any(not isinstance(row, str) for row in pat):
    raise ValueError('motif pattern rows must be strings')
  w = len(pat[0])
  if w == 0 or any(len(row) != w for row in pat):
    raise ValueError('motif pattern must be rectangular')
  if len(pat) > 3 or w > 3:
    raise ValueError('motif patterns are limited to 3x3')
  for row in pat:
    for ch in row:
      if ch != '.' and ch not in DIGITS:
        raise ValueError('pattern cells must be digits or .')
  cells = _cells(pat)
  if len(cells) < 3:
    raise ValueError('motif needs at least three cells')
  counts = collections.Counter(v for _, _, v in cells)
  if len(counts) != 2:
    raise ValueError('motif must use exactly two colours')
  ones = [v for v, n in counts.items() if n == 1]
  if len(ones) != 1:
    raise ValueError('motif needs exactly one singly-occurring anchor colour')
  anchor = ones[0]
  body = [v for v in counts if v != anchor][0]
  if len(_components8([(r, c) for r, c, _ in cells])) != 1:
    raise ValueError('motif must be 8-connected')
  return body, anchor


def _spurious_size(pat, body):
  """Cells inside the tiny framed box that a 3x3 body ring forms, else 0."""
  if len(pat) != 3 or len(pat[0]) != 3:
    return 0
  bset = set((r, c) for r, c, v in _cells(pat) if v == body)
  for comp in _components8(bset):
    if len(set(r for r, _ in comp)) == 3 and len(set(c for _, c in comp)) == 3:
      nonbody = [(r, c) for r in range(3) for c in range(3)
                 if (r, c) not in bset]
      if len(_components8(nonbody)) != 1:
        raise ValueError('motif body ring would enclose several objects')
      return len(nonbody)
  return 0


def _library(motifs):
  lib = []
  for _, _, pat in motifs:
    key = tuple(pat)
    if key not in lib:
      lib.append(key)
  return lib


def _match(library, colour):
  """Return (cells, anchor) of the single motif type anchored by colour."""
  found = []
  for pat in library:
    cells = _cells(pat)
    anc = [(y, x) for y, x, v in cells if v == colour]
    if len(anc) == 1:
      found.append((cells, anc[0]))
  if len(found) != 1:
    raise ValueError('marker colour %d must match exactly one motif' % colour)
  return found[0]


def _check_scene(size, motif_box, motifs, marker_box, markers):
  """Reject scenes whose input would not visibly determine the output."""
  _check_box(motif_box, size, 'motif_box')
  _check_box(marker_box, size, 'marker_box')
  if not _separated(motif_box, marker_box):
    raise ValueError('boxes must be separated by at least one cell')
  if (not isinstance(motifs, (list, tuple)) or
      not isinstance(markers, (list, tuple))):
    raise ValueError('motifs and markers must be lists')
  if len(motifs) < 2 or len(markers) < 2:
    raise ValueError('need at least two motifs and two markers')
  rects = []
  total = 0
  spur = []
  for m in motifs:
    if not isinstance(m, (list, tuple)) or len(m) != 3:
      raise ValueError('each motif is (row, col, pattern)')
    r, c, pat = m
    if not _is_int(r) or not _is_int(c):
      raise ValueError('motif position must be integers')
    body, _ = _check_pattern(pat)
    ph, pw = len(pat), len(pat[0])
    if not (_inside(motif_box, r, c, 1) and
            _inside(motif_box, r + ph - 1, c + pw - 1, 1)):
      raise ValueError('motif must sit inside the box, one cell off the frame')
    cells = _cells(pat)
    for _, _, v in cells:
      if v == motif_box[5]:
        raise ValueError('motif colour equals the motif-box interior')
    rects.append((r, c, ph, pw))
    total += len(cells)
    spur.append(_spurious_size(pat, body))
  for i in range(len(rects)):
    for j in range(i):
      if not _separated(rects[i], rects[j]):
        raise ValueError('motifs must not touch or overlap')
  for s in spur:
    if s > 1 and total <= s:
      raise ValueError('a motif ring would outweigh the real motif box')
  lib = _library(motifs)
  # Every anchor colour names exactly one pattern, used or not.
  groups = collections.defaultdict(set)
  for pat in lib:
    _, anc = _check_pattern(pat)
    groups[anc].add(pat)
  for anc in groups:
    if len(groups[anc]) > 1:
      raise ValueError('anchor colour %d is used by several motif patterns'
                       % anc)
  stamps = []
  for mk in markers:
    if not isinstance(mk, (list, tuple)) or len(mk) != 3:
      raise ValueError('each marker is (row, col, colour)')
    r, c, v = mk
    if not _is_int(r) or not _is_int(c):
      raise ValueError('marker position must be integers')
    _need_int('marker colour', v, 0, 9)
    if not _inside(marker_box, r, c, 0):
      raise ValueError('marker outside marker box interior')
    cells, (ar, ac) = _match(lib, v)
    for dr, dc, x in cells:
      if not _inside(marker_box, r - ar + dr, c - ac + dc, 0):
        raise ValueError('stamped motif would leave the marker interior')
      if x == marker_box[5]:
        raise ValueError('stamped colour equals the marker-box interior')
    h = max(y for y, _, _ in cells) + 1
    w = max(x for _, x, _ in cells) + 1
    stamps.append((r - ar, c - ac, h, w))
  for i in range(len(stamps)):
    for j in range(i):
      if not _separated(stamps[i], stamps[j]):
        raise ValueError('stamped motifs must not touch or overlap')


def _crop_and_stamp(g, marker_box, motifs, markers):
  """Crop the marker box and stamp each marker's motif from the latents."""
  t, l, h, w = marker_box[:4]
  out = [list(row[l:l + w]) for row in g[t:t + h]]
  lib = _library(motifs)
  for r, c, v in markers:
    cells, (ar, ac) = _match(lib, v)
    for dr, dc, x in cells:
      out[r - t - ar + dr][c - l - ac + dc] = x
  return out


def generate(stripes=None, vertical=None, motif_box=None, motifs=None,
             marker_box=None, markers=None, size=None, num_types=None,
             num_markers=None):
  """Build one input/output pair.

  Args:
    stripes: distinct wallpaper colours (integers 0..9, at least two). A cell
      takes stripes[i % len], where i is its column (vertical) or its row
      (horizontal).
    vertical: True for vertical stripes, False for horizontal ones.
    motif_box: (top, left, outer_height, outer_width, frame, interior).
    motifs: list of (row, col, pattern). row/col is the absolute top-left;
      pattern is a list of digit strings, with '.' for empty cells.
    marker_box: (top, left, outer_height, outer_width, frame, interior).
    markers: list of (row, col, colour), giving absolute marker cells.
    size: side of the square grid. With an explicit scene it defaults to 30.
      In random mode it defaults to 30 with probability 0.4, otherwise to a
      size in 14-29 (a synthetic extension). The lower bound rises to 18 or
      22 for large counts. If an auto-chosen smaller size cannot fit the
      scene, 30 is used.
    num_types: random mode only. Number of motif types, 1-4.
    num_markers: random mode only. Number of markers, 2-8.

  motif_box, motifs, marker_box and markers must be given all together
  (explicit scene) or not at all (random scene). A partial scene raises
  ValueError. stripes and vertical are honoured in both modes. Both modes
  apply the same visibility checks. Counts that cannot fit an explicitly
  requested size raise ValueError.
  """
  scene = [motif_box, motifs, marker_box, markers]
  given = sum(x is not None for x in scene)
  if 0 < given < 4:
    raise ValueError('motif_box, motifs, marker_box, markers go together')
  if size is not None:
    _need_int('size', size, 3, 30)
  if given == 4:
    if num_types is not None or num_markers is not None:
      raise ValueError('num_types/num_markers only apply to random scenes')
    if size is None:
      size = 30
  else:
    if num_types is not None:
      _need_int('num_types', num_types, 1, 4)
    if num_markers is not None:
      _need_int('num_markers', num_markers, 2, 8)
    auto = size is None
    if auto:
      lo = MIN_RANDOM_SIZE
      if (num_types or 0) >= 4 or (num_markers or 0) >= 7:
        lo = 22
      elif (num_types or 0) >= 3 or (num_markers or 0) >= 5:
        lo = 18
      size = 30 if random.random() < 0.4 else random.randint(lo, 29)
    elif size < MIN_RANDOM_SIZE:
      raise ValueError('random scenes need size %d..30' % MIN_RANDOM_SIZE)
    sc = _sample_scene(size, num_types, num_markers)
    if sc is None and auto and size != 30:
      size = 30
      sc = _sample_scene(size, num_types, num_markers)
    if sc is None:
      raise ValueError('requested motif types/markers do not fit in a %dx%d '
                       'grid; use a larger size or smaller counts'
                       % (size, size))
    motif_box, motifs = sc['motif_box'], sc['motifs']
    marker_box, markers = sc['marker_box'], sc['markers']
  if stripes is None:
    stripes = random.sample(range(10), random.randint(3, 5))
  _check_stripes(stripes)
  if vertical is None:
    vertical = random.random() < 0.5
  elif not isinstance(vertical, bool):
    raise ValueError('vertical must be True or False')
  _check_scene(size, motif_box, motifs, marker_box, markers)
  g = common.grid(size, size, 0)
  for r in range(size):
    for c in range(size):
      idx = c if vertical else r
      g[r][c] = stripes[idx % len(stripes)]

  def draw_box(t, l, h, w, f, b):
    for r in range(t, t + h):
      for c in range(l, l + w):
        edge = r in (t, t + h - 1) or c in (l, l + w - 1)
        g[r][c] = f if edge else b

  draw_box(*motif_box)
  draw_box(*marker_box)
  for r, c, pat in motifs:
    for dr, dc, v in _cells(pat):
      g[r + dr][c + dc] = v
  for r, c, v in markers:
    g[r][c] = v
  out = _crop_and_stamp(g, marker_box, motifs, markers)
  return {'input': [list(row) for row in g], 'output': out}


def validate():
  """Rebuild the canonical pairs from explicit latent parameters."""
  cup = ['2.2', '222', '.8.']
  plus = ['.8.', '818', '.8.']
  ring = ['.1.', '161', '111']
  cap = ['555', '575']
  train = [
      generate(stripes=[1, 3, 5, 7, 9], vertical=True,
               motif_box=(5, 2, 14, 16, 6, 1),
               motifs=[(8, 5, cup), (14, 11, cup)],
               marker_box=(20, 5, 9, 20, 3, 1),
               markers=[(24, 16, 8), (24, 20, 8), (25, 9, 8)], size=30),
      generate(stripes=[0, 2, 4, 6, 8], vertical=False,
               motif_box=(3, 3, 19, 13, 1, 2),
               motifs=[(6, 6, plus), (11, 9, plus), (17, 6, plus)],
               marker_box=(3, 17, 19, 8, 3, 4),
               markers=[(10, 22, 1), (18, 20, 1)], size=30),
  ]
  test = [
      generate(stripes=[0, 1, 2, 3], vertical=True,
               motif_box=(1, 2, 12, 18, 4, 3),
               motifs=[(4, 7, ring), (4, 13, cap), (8, 13, ring), (9, 6, cap)],
               marker_box=(15, 1, 9, 14, 2, 8),
               markers=[(19, 7, 6), (20, 11, 7), (21, 3, 6)], size=30),
  ]
  return {'train': train, 'test': test}
