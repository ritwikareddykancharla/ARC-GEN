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

"""Generator for ARC task aee291af (odd box out).

Rule: the input is a background of 1 sprinkled with noise cells of 8. Several
square k x k boxes are hidden in the noise. Each box has a solid 8 border and a
(k-2) x (k-2) interior made of 2s and 8s that holds at least one 2. All boxes
but one share the same interior pattern. The output is the single box whose
interior pattern is unique, cropped exactly with its border.

Scope:
  - Box side k is in 4..8, with one size per scene. The fixtures use k=4 and
    k=5, so k=6..8 is a synthetic extension.
  - A sampled scene holds 3..8 boxes (k <= 5) or 3..6 boxes (k >= 6), biased
    toward 3..5. An explicit num_boxes may be 3..16. An explicit odd_index
    raises the sampled lower bound to odd_index + 1.
  - Feasibility is exact: gapped k x k squares in a W x H grid fit at most
    floor((W+1)/(k+1)) * floor((H+1)/(k+1)) times, and that lattice bound is
    always attainable. Requests within the bound are honoured; requests
    beyond it raise ValueError up front (e.g. 3 boxes in 8x8, size 8 with
    num_boxes 16). Explicit decoys count as extra lattice slots.
  - Placement is greedy random (random tries, then an exhaustive shuffled
    scan per square). If that jams, a randomized lattice fallback is used:
    stride k+1 with random nondecreasing slack offsets per row/column, a
    random slot subset, then random +/-2 jitter of each square where it stays
    clear. The fallback is mainly reached by dense explicit requests (boxes
    filling more than about half of the lattice slots, e.g. size=5 with
    num_boxes=16, or size=4, num_boxes=16 in 19x19, which only fits as an
    exact lattice). Default sampling rarely needs it.
  - Sampled boxes and decoys are separated by at least one cell.
  - Sampled grid sides are max(10, k)..30, chosen among (width, height)
    pairs whose lattice capacity fits the request, preferring pairs with
    about 1.6x area slack. Elongated grids occur. Sides other than 16 and 18
    are synthetic extensions.
  - Sampled noise density is 8%..20%. An explicit density may be 0..0.5.
  - The palette 1/8/2 is fixed, as in every demonstration.

The odd pattern is chosen from these variants of the common pattern:
  - a 2/8 swap that keeps the count of 2s;
  - a non-identical rotation or reflection (train 2 and train 3 are
    reflections, so orientation matters);
  - a single-cell toggle;
  - an unrelated random pattern.
Common patterns may contain isolated 2s ringed by 8. Such a pattern creates
smaller detectable windows nested inside every box, exactly as in the
canonical test pair. The odd pattern is never allowed to add a nested window
that the common pattern lacks.

Optional decoys (side 3..k) come in three kinds:
  - a solid 8 square;
  - an 8 ring with a 1-filled interior;
  - a near-miss: a k x k copy of the common box with one non-corner border
    cell set to 1 (only when the common pattern has no nested windows;
    otherwise it becomes a ring).
The near-miss interior equals the common interior, so it can never become an
alternative answer.

The output is built from the latent odd pattern, never read back by a solver.
Acceptance: every scene that is not fully explicit is accepted only when the
strict invariant holds:
  - every square window, at any side 3..30, whose border is all 8 and whose
    interior is 2/8-only with a 2 is either a planted box or nested inside
    one;
  - the windows whose interior is unique are exactly [the odd box].
A fully explicit scene (noise, boxes, both patterns and odd_index) is the
fixture-replay path. It is checked once with the order-sensitive selection,
the first unique window by side 3..8 then row then column, and raises
ValueError if that selection is not the planted odd box.
"""

import collections
import random

import common


_SIZE_CHOICES = [4, 4, 4, 5, 5, 5, 6, 6, 7, 8]


def _is_int(v):
  """True for a genuine int (bools are excluded)."""
  return isinstance(v, int) and not isinstance(v, bool)


def _cap(side, k):
  """Exact count of gapped k-squares that fit along an axis of length side."""
  return (side + 1) // (k + 1)


def _sample_hi(k):
  """Largest box count drawn by default sampling for box side k."""
  return 8 if k <= 5 else 6


def _box(k, pattern):
  """Builds a k x k box: 8 border, interior from pattern strings of '2'/'8'."""
  out = [[8] * k for _ in range(k)]
  for i, row in enumerate(pattern):
    for j, ch in enumerate(row):
      out[i + 1][j + 1] = 2 if ch == '2' else 8
  return out


def _check_pattern(p, m, name):
  """Raises ValueError unless p is m strings of m chars in '28' holding a 2."""
  if p is None:
    return
  if (len(p) != m or
      any(len(row) != m or any(ch not in '28' for ch in row) for row in p)):
    raise ValueError('%s must be %d strings of %d chars in 28' % (name, m, m))
  if not any('2' in row for row in p):
    raise ValueError('%s must contain at least one 2' % name)


def _pattern(m):
  """Constructs an m x m interior pattern with at least two 2s."""
  cells = [(i, j) for i in range(m) for j in range(m)]
  t = random.randint(2, m * m)
  if t == m * m and random.random() < 0.7:
    t = random.randint(2, m * m)
  chosen = set(random.sample(cells, t))
  return [''.join('2' if (i, j) in chosen else '8' for j in range(m))
          for i in range(m)]


def _symmetries(p):
  """All 8 rotations and reflections of a square pattern, as string lists."""
  m = len(p)
  a = [list(row) for row in p]
  out = []
  for _ in range(4):
    a = [[a[m - 1 - j][i] for j in range(m)] for i in range(m)]
    out.append([''.join(row) for row in a])
    out.append([''.join(row[::-1]) for row in a])
  return out


def _odd_pattern(base):
  """Constructs a pattern that differs from base and holds a 2."""
  m = len(base)
  twos = [(i, j) for i in range(m) for j in range(m) if base[i][j] == '2']
  eights = [(i, j) for i in range(m) for j in range(m) if base[i][j] == '8']
  mode = random.choice(['swap', 'swap', 'symmetry', 'toggle', 'random'])
  q = None
  if mode == 'swap' and twos and eights:
    cells = [list(row) for row in base]
    a = random.choice(twos)
    b = random.choice(eights)
    cells[a[0]][a[1]] = '8'
    cells[b[0]][b[1]] = '2'
    q = [''.join(row) for row in cells]
  elif mode == 'symmetry':
    opts = [s for s in _symmetries(base) if s != list(base)]
    if opts:
      q = random.choice(opts)
  elif mode == 'random':
    for _ in range(20):
      cand = _pattern(m)
      if cand != list(base):
        q = cand
        break
  if q is None or q == list(base):
    # Toggle one cell. The result always differs from base and keeps a 2.
    cells = [list(row) for row in base]
    if eights:
      i, j = random.choice(eights)
      cells[i][j] = '2'
    else:
      i, j = random.choice(twos)
      cells[i][j] = '8'
    q = [''.join(row) for row in cells]
  return q


def _clear(r, c, s, rects):
  """True when square (r, c, s) keeps a one-cell gap from every rect."""
  return all(r + s < pr or pr + ps < r or c + s < pc or pc + ps < c
             for pr, pc, ps in rects)


def _place(existing, sizes, w, h, partial=False):
  """Greedily places squares of the given sizes with a one-cell gap.

  Each square first gets random tries, then every position in shuffled order.
  Returns a list aligned with sizes holding (row, col, side) or None. With
  partial=False, any unplaced square makes the call return None.
  """
  rects = list(existing)
  new = []
  for s in sizes:
    spot = None
    if s <= w and s <= h:
      for _ in range(60):
        r = random.randint(0, h - s)
        c = random.randint(0, w - s)
        if _clear(r, c, s, rects):
          spot = (r, c, s)
          break
      if spot is None:
        cells = [(r, c) for r in range(h - s + 1) for c in range(w - s + 1)]
        random.shuffle(cells)
        for r, c in cells:
          if _clear(r, c, s, rects):
            spot = (r, c, s)
            break
    if spot is None:
      if not partial:
        return None
    else:
      rects.append(spot)
    new.append(spot)
  return new


def _offsets(count, k, side):
  """Lattice coordinates with stride k+1 and random nondecreasing slack."""
  slack = side - (count * (k + 1) - 1)
  extra = sorted(random.randint(0, slack) for _ in range(count))
  return [i * (k + 1) + extra[i] for i in range(count)]


def _lattice(w, h, k, n, dsizes, strict_dec):
  """Randomized lattice placement used when greedy placement jams.

  Boxes and decoys (side <= k) each take one slot of a stride-(k+1) lattice
  with random slack offsets, then every square is randomly jittered by up to
  two cells wherever it stays in bounds and gapped.
  """
  cx, cy = _cap(w, k), _cap(h, k)
  total = cx * cy
  nd_slots = len(dsizes) if strict_dec else max(0, min(len(dsizes), total - n))
  if n + nd_slots > total or cx < 1 or cy < 1:
    return None
  xs = _offsets(cx, k, w)
  ys = _offsets(cy, k, h)
  slots = random.sample([(r, c) for r in ys for c in xs], n + nd_slots)
  items = [(r, c, k) for r, c in slots[:n]]
  dec_idx = []
  for idx, s in enumerate(dsizes):
    if idx < nd_slots:
      r, c = slots[n + idx]
      r += random.randint(0, k - s)
      c += random.randint(0, k - s)
      dec_idx.append(len(items))
      items.append((r, c, s))
    else:
      dec_idx.append(None)
  order = list(range(len(items)))
  random.shuffle(order)
  for i in order:
    r, c, s = items[i]
    others = items[:i] + items[i + 1:]
    for _ in range(4):
      nr = r + random.randint(-2, 2)
      nc = c + random.randint(-2, 2)
      if (0 <= nr <= h - s and 0 <= nc <= w - s and
          _clear(nr, nc, s, others)):
        items[i] = (nr, nc, s)
        break
  pos = [(r, c) for r, c, _ in items[:n]]
  dec = [items[j] if j is not None else None for j in dec_idx]
  return pos, dec


def _layout(w, h, k, n, dsizes, strict_dec, fixed=None):
  """Places boxes (unless fixed) and decoys; returns (positions, decoys)."""
  if fixed is not None:
    rects = [(r, c, k) for r, c in fixed]
    dec = _place(rects, dsizes, w, h, partial=not strict_dec)
    if dec is None:
      return None
    return list(fixed), dec
  for _ in range(2):
    placed = _place([], [k] * n, w, h)
    if placed is None:
      continue
    dec = _place(placed, dsizes, w, h, partial=not strict_dec)
    if dec is not None:
      return [(r, c) for r, c, _ in placed], dec
  return _lattice(w, h, k, n, dsizes, strict_dec)


def _dims(k, need, comfy_area, width, height):
  """Chooses (w, h) whose exact lattice capacity holds need squares."""
  lo = max(10, k)
  ws = [width] if width is not None else list(range(lo, 31))
  hs = [height] if height is not None else list(range(lo, 31))
  pairs = [(w, h) for w in ws for h in hs if _cap(w, k) * _cap(h, k) >= need]
  if not pairs:
    return None
  comfy = [p for p in pairs if (p[0] + 1) * (p[1] + 1) >= comfy_area]
  pool = comfy if comfy and random.random() < 0.85 else pairs
  return random.choice(pool)


def _prefix(g, pred):
  """2D prefix counts of cells satisfying pred."""
  h, w = len(g), len(g[0])
  p = [[0] * (w + 1) for _ in range(h + 1)]
  for r in range(h):
    run = 0
    row = g[r]
    for c in range(w):
      if pred(row[c]):
        run += 1
      p[r + 1][c + 1] = p[r][c + 1] + run
  return p


def _rect(p, y0, x0, y1, x1):
  """Count over the half-open rectangle [y0, y1) x [x0, x1)."""
  return p[y1][x1] - p[y0][x1] - p[y1][x0] + p[y0][x0]


def _candidates(g, kmax):
  """Detectable windows (row, col, side) of side 3..kmax, in scan order.

  A window is detectable when its border is all 8 and its interior is
  2/8-only with at least one 2. Scan order is side, then row, then column.
  """
  h, w = len(g), len(g[0])
  twos = _prefix(g, lambda v: v == 2)
  bad = _prefix(g, lambda v: v != 2 and v != 8)
  non8 = _prefix(g, lambda v: v != 8)
  out = []
  for k in range(3, min(kmax, h, w) + 1):
    for y in range(h - k + 1):
      for x in range(w - k + 1):
        y1, x1 = y + k - 1, x + k - 1
        if _rect(twos, y + 1, x + 1, y1, x1) == 0:
          continue
        if _rect(bad, y + 1, x + 1, y1, x1):
          continue
        if (_rect(non8, y, x, y + k, x + k) !=
            _rect(non8, y + 1, x + 1, y1, x1)):
          continue
        out.append((y, x, k))
  return out


def _inner(g, y, x, k):
  """Interior of the window at (y, x) with side k, as a tuple of tuples."""
  return tuple(tuple(g[y + i][x + 1:x + k - 1]) for i in range(1, k - 1))


def _nested(k, pattern):
  """Interiors of the smaller detectable windows lying inside one box."""
  b = _box(k, pattern)
  return set(_inner(b, y, x, s) for y, x, s in _candidates(b, k - 1))


def _nested_ok(k, base, odd):
  """True when every window nested in the odd box also occurs in the others."""
  return _nested(k, odd) <= _nested(k, base)


def _strict_ok(grid, pos, k, target):
  """Every window is planted or nested in a planted box, and the only unique
  interior belongs to the target."""
  cands = _candidates(grid, 30)
  planted = set((r, c, k) for r, c in pos)
  if not planted <= set(cands):
    return False
  for y, x, s in cands:
    if (y, x, s) in planted:
      continue
    if not any(r <= y and c <= x and y + s <= r + k and x + s <= c + k
               for r, c in pos):
      return False
  keys = [_inner(grid, y, x, s) for y, x, s in cands]
  counts = collections.Counter(keys)
  uniq = [c for c, key in zip(cands, keys) if counts[key] == 1]
  return uniq == [target]


def _selected(grid):
  """First window with a unique interior, scanning sides 3..8."""
  cands = _candidates(grid, 8)
  keys = [_inner(grid, y, x, s) for y, x, s in cands]
  counts = collections.Counter(keys)
  uniq = [c for c, key in zip(cands, keys) if counts[key] == 1]
  if not uniq:
    uniq = cands
  return uniq[0] if uniq else None


def _is_seq(v):
  """True for a list or tuple (strings are excluded)."""
  return isinstance(v, (list, tuple))


def generate(width=None, height=None, size=None, boxes=None, pattern=None,
             odd_pattern=None, odd_index=None, noise=None, num_boxes=None,
             density=None, decoys=None):
  """Generates an odd-box-out scene.

  Args:
    width: grid width (int in 1..30, large enough to hold the boxes). When
      None it is sampled in max(10, k)..30 among sides that fit the request.
    height: grid height, with the same rules as width.
    size: box side length k (int in 4..8). When None it is inferred from
      pattern/odd_pattern or sampled. It is required, directly or through a
      pattern, when boxes is given.
    boxes: list of (row, col) top-left corners (lists/tuples of two ints).
      There must be at least 3, inside the grid and non-overlapping.
    pattern: common interior pattern, a list of k-2 strings of '2'/'8'.
    odd_pattern: the unique interior pattern. It must differ from pattern and
      must not contain a nested detectable window that pattern lacks.
    odd_index: index into the box list of the box carrying odd_pattern. When
      the box count is sampled it raises the count to at least odd_index + 1.
    noise: optional list of equal-length strings. '#' marks an 8 noise cell
      and any other character is background. Box cells are painted over the
      noise. When noise, boxes, both patterns and odd_index are all given the
      scene is fully explicit (fixture replay): one attempt, checked with the
      order-sensitive selection, ValueError on failure.
    num_boxes: number of boxes (int in 3..16) when boxes is None. Any value
      within the exact lattice capacity of the grid is honoured.
    density: noise density (number in [0, 0.5]). When None it is sampled in
      0.08..0.2. It cannot be combined with noise.
    decoys: number of decoy squares (int in 0..4): solid 8 blocks, 8 rings with
      1 inside, or near-miss common boxes with a broken border. When None,
      0..3 are sampled and fewer may be placed if space is short. When given,
      all must be placed. They cannot be combined with noise.
  """
  for v, name in ((width, 'width'), (height, 'height'), (size, 'size'),
                  (odd_index, 'odd_index'), (num_boxes, 'num_boxes'),
                  (decoys, 'decoys')):
    if v is not None and not _is_int(v):
      raise ValueError('%s must be an integer' % name)
  if density is not None:
    if isinstance(density, bool) or not isinstance(density, (int, float)):
      raise ValueError('density must be a number')
    if not 0 <= density <= 0.5:
      raise ValueError('density must be in [0, 0.5]')
  for p, name in ((pattern, 'pattern'), (odd_pattern, 'odd_pattern')):
    if p is not None and (not _is_seq(p) or
                          any(not isinstance(r, str) for r in p)):
      raise ValueError('%s must be a list of strings' % name)
  if noise is not None:
    if (not _is_seq(noise) or not noise or
        any(not isinstance(r, str) for r in noise)):
      raise ValueError('noise must be a non-empty list of strings')
    noise = list(noise)
    if not noise[0] or any(len(r) != len(noise[0]) for r in noise):
      raise ValueError('noise rows must be non-empty and equal length')
    if height is not None and height != len(noise):
      raise ValueError('height does not match noise')
    if width is not None and width != len(noise[0]):
      raise ValueError('width does not match noise')
    if density is not None:
      raise ValueError('density cannot be combined with an explicit noise layer')
    if decoys:
      raise ValueError('decoys cannot be combined with an explicit noise layer')
    height, width = len(noise), len(noise[0])
  if boxes is not None:
    if not _is_seq(boxes):
      raise ValueError('boxes must be a list of (row, col) pairs')
    norm = []
    for b in boxes:
      if not _is_seq(b) or len(b) != 2 or not all(_is_int(v) for v in b):
        raise ValueError('each box must be an integer (row, col) pair')
      norm.append((b[0], b[1]))
    boxes = norm
  for v, name in ((width, 'width'), (height, 'height')):
    if v is not None and not 1 <= v <= 30:
      raise ValueError('%s must be in 1..30' % name)
  if decoys is not None and not 0 <= decoys <= 4:
    raise ValueError('decoys must be in 0..4')
  if num_boxes is not None and not 3 <= num_boxes <= 16:
    raise ValueError('num_boxes must be in 3..16')
  k_fixed = size
  for p in (pattern, odd_pattern):
    if p is not None:
      if k_fixed is None:
        k_fixed = len(p) + 2
      elif len(p) + 2 != k_fixed:
        raise ValueError('pattern size does not match box size')
  if k_fixed is not None:
    if not 4 <= k_fixed <= 8:
      raise ValueError('box size must be in 4..8')
    _check_pattern(pattern, k_fixed - 2, 'pattern')
    _check_pattern(odd_pattern, k_fixed - 2, 'odd_pattern')
    for v, name in ((width, 'width'), (height, 'height')):
      if v is not None and v < k_fixed:
        raise ValueError('%s is smaller than the box size' % name)
  if pattern is not None:
    pattern = list(pattern)
  if odd_pattern is not None:
    odd_pattern = list(odd_pattern)
  if pattern is not None and odd_pattern is not None:
    if pattern == odd_pattern:
      raise ValueError('odd_pattern must differ from pattern')
    if not _nested_ok(k_fixed, pattern, odd_pattern):
      raise ValueError('odd_pattern holds a nested box absent from pattern, '
                       'so the odd box would not be the unique one')
  if boxes is not None:
    if num_boxes is not None and num_boxes != len(boxes):
      raise ValueError('num_boxes does not match boxes')
    if k_fixed is None:
      raise ValueError('size (or a pattern) is required with boxes')
    n_fixed = len(boxes)
    for r, c in boxes:
      if r < 0 or c < 0 or r + k_fixed > 30 or c + k_fixed > 30:
        raise ValueError('box out of bounds')
      if height is not None and r + k_fixed > height:
        raise ValueError('box out of bounds')
      if width is not None and c + k_fixed > width:
        raise ValueError('box out of bounds')
    for i in range(len(boxes)):
      for j in range(i + 1, len(boxes)):
        (r1, c1), (r2, c2) = boxes[i], boxes[j]
        if not (r1 + k_fixed <= r2 or r2 + k_fixed <= r1 or
                c1 + k_fixed <= c2 or c2 + k_fixed <= c1):
          raise ValueError('boxes overlap')
  else:
    n_fixed = num_boxes
  if n_fixed is not None and n_fixed < 3:
    raise ValueError('at least 3 boxes are required')
  if odd_index is not None:
    if odd_index < 0 or (n_fixed is not None and odd_index >= n_fixed):
      raise ValueError('odd_index out of range')
    if n_fixed is None and odd_index >= 16:
      raise ValueError('odd_index must be below 16 when the count is sampled')
  n_lo = n_fixed if n_fixed is not None else max(3, (odd_index or 0) + 1)
  dec_req = decoys or 0
  cap_w = width if width is not None else 30
  cap_h = height if height is not None else 30

  def k_ok(kk):
    if kk > cap_w or kk > cap_h:
      return False
    room = _cap(cap_w, kk) * _cap(cap_h, kk) - dec_req
    return room >= n_lo

  if boxes is None:
    if k_fixed is not None:
      if not k_ok(k_fixed):
        raise ValueError('the requested boxes cannot fit these controls')
      choices = [k_fixed]
    else:
      choices = [kk for kk in _SIZE_CHOICES if k_ok(kk)]
      if not choices:
        raise ValueError('no box size fits the requested controls')
  else:
    choices = [k_fixed]
  explicit_scene = (noise is not None and boxes is not None and
                    pattern is not None and odd_pattern is not None and
                    odd_index is not None)

  attempts = 1 if explicit_scene else 500
  for _ in range(attempts):
    k = random.choice(choices)
    m = k - 2
    if n_fixed is not None:
      n = n_fixed
    else:
      room = _cap(cap_w, k) * _cap(cap_h, k) - dec_req
      top = max(n_lo, min(_sample_hi(k), room))
      if random.random() < 0.7:
        top = max(n_lo, min(top, 5))
      n = random.randint(n_lo, top)
    oi = odd_index if odd_index is not None else random.randrange(n)
    if decoys is not None:
      nd = decoys
    else:
      nd = 0 if noise is not None else random.choice([0, 0, 1, 1, 2, 3])
    kinds = [random.choice(['solid', 'ring', 'near']) for _ in range(nd)]
    dsizes = [k if kd == 'near' else random.randint(3, k) for kd in kinds]
    if boxes is not None:
      need_w = max(c for _, c in boxes) + k
      need_h = max(r for r, _ in boxes) + k
      w = width if width is not None else random.randint(max(10, need_w), 30)
      h = height if height is not None else random.randint(max(10, need_h), 30)
    else:
      comfy = 1.6 * (n * (k + 1) ** 2 + sum((s + 1) ** 2 for s in dsizes))
      dims = _dims(k, n + dec_req, comfy, width, height)
      if dims is None:
        continue
      w, h = dims
    lay = _layout(w, h, k, n, dsizes, decoys is not None, boxes)
    if lay is None:
      continue
    pos, dec = lay
    base = pattern if pattern is not None else _pattern(m)
    if odd_pattern is not None:
      odd = odd_pattern
      if odd == base or not _nested_ok(k, base, odd):
        continue
    else:
      odd = None
      for _ in range(20):
        q = _odd_pattern(base)
        if q != base and _nested_ok(k, base, q):
          odd = q
          break
      if odd is None:
        continue
    near_ok = 'near' in kinds and not _nested(k, base)
    grid = common.grid(w, h, 1)
    if len(grid) != h or any(len(row) != w for row in grid):
      raise RuntimeError('common.grid returned an unexpected shape')
    if noise is not None:
      for r, row in enumerate(noise):
        for c, ch in enumerate(row):
          if ch == '#':
            grid[r][c] = 8
    else:
      dens = density if density is not None else random.uniform(0.08, 0.2)
      for r in range(h):
        for c in range(w):
          if random.random() < dens:
            grid[r][c] = 8
    for spot, kd in zip(dec, kinds):
      if spot is None:
        continue
      r, c, s = spot
      if kd == 'near' and near_ok and s == k:
        art = _box(k, base)
        edge = ([(0, j) for j in range(1, k - 1)] +
                [(k - 1, j) for j in range(1, k - 1)] +
                [(i, 0) for i in range(1, k - 1)] +
                [(i, k - 1) for i in range(1, k - 1)])
        i, j = random.choice(edge)
        art[i][j] = 1
      else:
        hollow = kd != 'solid'
        art = [[8 if (i in (0, s - 1) or j in (0, s - 1) or not hollow)
                else 1 for j in range(s)] for i in range(s)]
      for dr in range(s):
        for dc in range(s):
          grid[r + dr][c + dc] = art[dr][dc]
    for i, (r, c) in enumerate(pos):
      box = _box(k, odd if i == oi else base)
      for dr in range(k):
        for dc in range(k):
          grid[r + dr][c + dc] = box[dr][dc]
    target = (pos[oi][0], pos[oi][1], k)
    if explicit_scene:
      ok = _selected(grid) == target
    else:
      ok = _strict_ok(grid, pos, k, target)
    if ok:
      return {'input': grid, 'output': _box(k, odd)}
  if explicit_scene:
    raise ValueError('explicit scene does not single out the odd box')
  raise RuntimeError('could not build a valid scene with these parameters')


def validate():
  """Reconstructs the original fixtures through explicit generate calls."""
  ex1 = ['#...............', '...##...........', '.......#..#.#...',
         '.####.#..##.....', '.#..##..#..##...', '.#..#..#...#..#.',
         '.######.......#.', '.#.#...#..#.####', '............#..#',
         '.....#####..#..#', '.#...#.##..#####', '.....##.#.......',
         '.....#####..####', '...#........#..#', '.....#......#..#',
         '..#..#....#.####']
  ex2 = ['................', '.####.#..#......', '.#..#...####..#.',
         '.#.###..#..#....', '.####...#.##....', '.....#..#####...',
         '..#...........#.', '..####.#........', '..#..#....#..#..',
         '..#.##..####....', '#.####..#..#....', '........##.#..#.',
         '......#.####....', '..#.#...........', '.....#....#..##.',
         '.#.......##.....']
  ex3 = ['.#.#...#..#....##.', '.#####.......#..#.', '##.#.#..######....',
         '.##.###..#.#.##...', '##..##...##.##.#..', '.#####...#..###...',
         '.#.#..#..######.##', '#...............#.', '....##....#.......',
         '#....#####...#....', '##...#.#.#..#.....', '..#..##.##.......#',
         '.....##..#..##..#.', '.#...#####......#.', '.#............#...',
         '....##........#...', '.#..#.............', '.....#............']
  ex4 = ['....#....#...#####', '...#..#..#..##..##', '.#######...###.###',
         '..#..##......###.#', '..#.###.#.#..#####', '.####.##..........',
         '#.#####..#.#......', '.#.#.....#####.##.', '....#.#..#..##....',
         '......#..#.####...', '######...###.#....', '#..##....#####....',
         '#.####............', '###.#...#####...#.', '#####...##..#....#',
         '........##..#...##', '##......#.###.....', '#.#....######.....']
  train = [
      generate(width=16, height=16, size=4,
               boxes=[(3, 1), (7, 12), (9, 5), (12, 12)],
               pattern=['22', '22'], odd_pattern=['28', '82'],
               odd_index=2, noise=ex1),
      generate(width=16, height=16, size=4,
               boxes=[(1, 1), (2, 8), (7, 2), (9, 8)],
               pattern=['22', '28'], odd_pattern=['22', '82'],
               odd_index=3, noise=ex2),
      generate(width=18, height=18, size=5,
               boxes=[(1, 1), (2, 9), (9, 5)],
               pattern=['282', '828', '228'],
               odd_pattern=['282', '828', '822'],
               odd_index=2, noise=ex3),
  ]
  test = [
      generate(width=18, height=18, size=5,
               boxes=[(0, 13), (2, 2), (7, 9), (10, 0), (13, 8)],
               pattern=['228', '288', '882'],
               odd_pattern=['822', '822', '288'],
               odd_index=4, noise=ex4),
  ]
  return {'train': train, 'test': test}
