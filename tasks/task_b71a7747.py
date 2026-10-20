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

"""ARC-GEN style generator for task b71a7747.

Rule: the input is a lattice. A background colour is crossed by 1-wide lines
of a line colour, and the background may carry scattered noise of a fifth
colour. On top of this sits an nr x nc arrangement of solid k x k blocks of a
block colour (k odd). Each block is centred on a line intersection. Block rows
are separated by `gap` rows and block columns by `col_gap` columns. A path of a
path colour is drawn in block space, so every gap interrupts it. The block
colour is the colour of the largest solid square component. The output keeps
exactly the rows and columns that contain the block colour, which glues the
blocks into a (k*nr) x (k*nc) grid in which the path is continuous.

Scope (fixture-like): block size 3/5/7, equal row and column gaps of 1-3,
square or rectangular arrangements of up to 7 blocks per side with at least
four blocks that fit in 30x30 (thin 1 x n and n x 1 included), margins of
1..min(period-1, 5) per side, random distinct role colours, and optional
noise.

Scope (synthetic extensions):
- Block size 9 is sampled by default. Any odd k up to 13 is accepted on
  request. With default positive margins, k >= 9 only fits a 2x2 arrangement,
  yielding an 18x18..26x26 output and a path through exactly 3 blocks.
  Explicit zero margins permit 3 rows/columns of k=9 with gap1; k>=11
  remains limited to 2x2.
- Row and column gaps may differ. When neither gap is given, the column gap
  is drawn different from the row gap in 40% of scenes.
- Noise may land on line cells.
- Two kinds of distractor are planted entirely off the blocks, in the noise
  colour. A near-miss square has side 2..k-1. A solid non-square rectangle
  has area greater than k*k (for example 3x4 or 1x10 when k=3), so the
  'largest square' test differs from a 'largest solid region/rectangle' test.
  A competing k x k square is never planted.
- The path is a strict thin polyline or a relaxed one whose runs may lie side
  by side. It may have up to two branches and an optional closed rectangular
  loop.

The random path grows only inside an allowed set of blocks; one or two blocks
are kept path-free. Growth stops before it would fill a whole output row, a
whole output column or a whole block. Scenes are rejected and resampled
(bounded) unless all of these hold:
- at least one block is path-free;
- the path touches at least three blocks;
- no output line is fully covered by the path;
- no colour other than the block colour forms a solid square component of
  area >= k*k under 4- or 8-connectivity.
The three path conditions above, plus 'no block fully covered by the path',
are also enforced for user strokes in every mode. They are checked before any
rendering, so failures raise ValueError immediately. A fully explicit scene
(all of block_size, gap, rows, cols, margins, colors, strokes and noise given)
must also have rows*cols >= 4. It is rendered once and raises ValueError if
the foreign-square check fails. validate() rebuilds the canonical fixtures
this way.
"""

import collections
import random

import common

_DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
_DIAG = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
_K_CHOICES = [3, 3, 3, 5, 5, 7, 9]
_GAP_CHOICES = [1, 1, 2, 3]
_GAP_VALUES = [1, 2, 3]
_N_CAP = 7
_DISTRACTORS = ('none', 'square', 'rect', 'both')


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _is_seq(v):
  return isinstance(v, (list, tuple))


def _check_int(name, v, lo=None, hi=None):
  """Rejects booleans, floats and out-of-range integers with ValueError."""
  if not _is_int(v):
    raise ValueError(name + ' must be an integer')
  if lo is not None and v < lo:
    raise ValueError(name + ' must be >= ' + str(lo))
  if hi is not None and v > hi:
    raise ValueError(name + ' must be <= ' + str(hi))


def _check_cells(name, cells):
  """Checks a list of integer (row, col) pairs without converting blindly."""
  if not _is_seq(cells):
    raise ValueError(name + ' must be a list of (row, col) pairs')
  out = []
  for q in cells:
    if not _is_seq(q) or len(q) != 2 or not all(_is_int(v) for v in q):
      raise ValueError(name + ' entries must be integer (row, col) pairs')
    out.append((q[0], q[1]))
  return out


def _span(n, k, g):
  """Cells covered by n blocks of side k separated by gaps of width g."""
  return n * k + (n - 1) * g


def _segment(a, b):
  (r0, c0), (r1, c1) = a, b
  if r0 != r1 and c0 != c1:
    raise ValueError('stroke segments must be horizontal or vertical')
  if r0 == r1:
    return [(r0, c) for c in range(min(c0, c1), max(c0, c1) + 1)]
  return [(r, c0) for r in range(min(r0, r1), max(r0, r1) + 1)]


def _strokes_to_cells(strokes):
  cells = set()
  for stroke in strokes:
    if len(stroke) == 1:
      cells.add(stroke[0])
    for a, b in zip(stroke, stroke[1:]):
      cells.update(_segment(a, b))
  return cells


class _PathState(object):
  """Path cells plus row, column and block occupancy counters."""

  def __init__(self, R, C, k, allowed):
    self.R, self.C, self.k = R, C, k
    self.allowed = allowed
    self.cells = set()
    self.order = []
    self.rows = collections.Counter()
    self.cols = collections.Counter()
    self.blocks = collections.Counter()

  def copy(self):
    o = _PathState(self.R, self.C, self.k, self.allowed)
    o.cells = set(self.cells)
    o.order = list(self.order)
    o.rows = collections.Counter(self.rows)
    o.cols = collections.Counter(self.cols)
    o.blocks = collections.Counter(self.blocks)
    return o

  def can_add(self, q):
    r, c = q
    if not (0 <= r < self.R and 0 <= c < self.C) or q in self.cells:
      return False
    b = (r // self.k, c // self.k)
    if b not in self.allowed:
      return False
    if self.rows[r] + 1 >= self.C or self.cols[c] + 1 >= self.R:
      return False
    return self.blocks[b] + 1 < self.k * self.k

  def add(self, q):
    self.cells.add(q)
    self.order.append(q)
    self.rows[q[0]] += 1
    self.cols[q[1]] += 1
    self.blocks[(q[0] // self.k, q[1] // self.k)] += 1


def _grow(st, r, c, d, length, strict=True):
  """Extends a straight run; strict runs never touch older path cells."""
  grown = 0
  for _ in range(length):
    q = (r + d[0], c + d[1])
    if not st.can_add(q):
      break
    if strict:
      bad = False
      for dr, dc in _DIRS:
        p = (q[0] + dr, q[1] + dc)
        if p != (r, c) and p in st.cells:
          bad = True
          break
      if bad:
        break
    r, c = q
    st.add(q)
    grown += 1
  return r, c, grown


def _turn(d):
  return random.choice([(d[1], -d[0]), (-d[1], d[0])])


def _add_loop(st):
  """Adds a closed rectangular loop with one corner on the path, if legal."""
  for _ in range(12):
    r, c = random.choice(st.order)
    h = random.randint(3, max(3, (st.R * 2) // 3))
    w = random.randint(3, max(3, (st.C * 2) // 3))
    r1 = r + random.choice((1, -1)) * (h - 1)
    c1 = c + random.choice((1, -1)) * (w - 1)
    if not (0 <= r1 < st.R and 0 <= c1 < st.C):
      continue
    ra, rb = min(r, r1), max(r, r1)
    ca, cb = min(c, c1), max(c, c1)
    ring = [(ra, x) for x in range(ca, cb + 1)]
    ring += [(rb, x) for x in range(ca, cb + 1)]
    ring += [(y, ca) for y in range(ra + 1, rb)]
    ring += [(y, cb) for y in range(ra + 1, rb)]
    tmp = st.copy()
    ok = True
    for q in ring:
      if q in tmp.cells:
        continue
      if not tmp.can_add(q):
        ok = False
        break
      tmp.add(q)
    if ok:
      return tmp
  return st


def _random_path(R, C, k, nr, nc):
  """Samples a path inside allowed blocks: polyline, branches, loop."""
  blocks = [(a, b) for a in range(nr) for b in range(nc)]
  nfree = 2 if (nr * nc >= 6 and random.random() < 0.3) else 1
  free = set(random.sample(blocks, nfree))
  st = _PathState(R, C, k, set(blocks) - free)
  br, bc = random.choice(sorted(st.allowed))
  r, c = br * k + random.randrange(k), bc * k + random.randrange(k)
  st.add((r, c))
  maxlen = max(2, (max(R, C) * 2) // 3)
  d = random.choice(_DIRS)
  strict = random.random() < 0.75
  for seg in range(random.randint(3, 8)):
    if seg:
      d = _turn(d)
    length = 1 if random.random() < 0.15 else random.randint(2, maxlen)
    r2, c2, g = _grow(st, r, c, d, length, strict)
    if g == 0:
      d = (-d[0], -d[1])
      r2, c2, g = _grow(st, r, c, d, length, strict)
    if g == 0:
      break
    r, c = r2, c2
  for _ in range(random.choice([0, 0, 0, 1, 1, 2])):
    if len(st.order) < 3:
      break
    for _ in range(10):
      rr, cc = random.choice(st.order[1:-1])
      dd = random.choice(_DIRS)
      tmp = st.copy()
      bstrict = random.random() < 0.6
      total = 0
      for seg in range(random.randint(1, 3)):
        if seg:
          dd = _turn(dd)
        rr, cc, g = _grow(tmp, rr, cc, dd, random.randint(2, maxlen), bstrict)
        total += g
        if g == 0:
          break
      if total >= 2:
        st = tmp
        break
  if random.random() < 0.25:
    st = _add_loop(st)
  return st.cells


def _touched_blocks(s, k):
  return {(r // k, c // k) for r, c in s}


def _fills_block(s, k):
  cnt = collections.Counter((r // k, c // k) for r, c in s)
  return any(v >= k * k for v in cnt.values())


def _keeps_block_colour(s, k, nr, nc):
  """Every output line keeps a block cell and some block is path-free."""
  R, C = k * nr, k * nc
  if len(_touched_blocks(s, k)) >= nr * nc:
    return False
  rows = collections.Counter(r for r, _ in s)
  cols = collections.Counter(c for _, c in s)
  if any(v >= C for v in rows.values()) or any(v >= R for v in cols.values()):
    return False
  return True


def _path_ok(s, k, nr, nc, min_len):
  return (len(s) >= min_len and len(_touched_blocks(s, k)) >= 3 and
          _keeps_block_colour(s, k, nr, nc) and not _fills_block(s, k))


def _render(k, gr, gc, nr, nc, margins, colors, path, noise_cells,
            noise_color):
  """Builds the input lattice and the glued output from latent values."""
  top, bottom, left, right = margins
  bc, pc, bgc, lc = colors
  per_r, per_c = k + gr, k + gc
  H = top + _span(nr, k, gr) + bottom
  W = left + _span(nc, k, gc) + right
  g = common.grid(W, H, bgc)
  r0 = (top + k // 2) % per_r
  c0 = (left + k // 2) % per_c
  for r in range(H):
    for c in range(W):
      if r % per_r == r0 or c % per_c == c0:
        g[r][c] = lc
  for r, c in noise_cells:
    g[r][c] = noise_color
  out = common.grid(nc * k, nr * k, bc)
  for r, c in path:
    out[r][c] = pc
  for y in range(nr * k):
    for x in range(nc * k):
      gy = top + (y // k) * per_r + y % k
      gx = left + (x // k) * per_c + x % k
      g[gy][gx] = out[y][x]
  return g, out


def _on_block(r, c, k, gr, gc, nr, nc, margins):
  y, x = r - margins[0], c - margins[2]
  if not (0 <= y < _span(nr, k, gr) and 0 <= x < _span(nc, k, gc)):
    return False
  return y % (k + gr) < k and x % (k + gc) < k


def _windows(mask, h, w):
  """Top-left corners of h x w windows whose cells are all True in mask."""
  H, W = len(mask), len(mask[0])
  if h > H or w > W:
    return []
  P = [[0] * (W + 1) for _ in range(H + 1)]
  for r in range(H):
    for c in range(W):
      P[r + 1][c + 1] = (P[r][c + 1] + P[r + 1][c] - P[r][c] +
                         (1 if mask[r][c] else 0))
  out = []
  for r in range(H - h + 1):
    for c in range(W - w + 1):
      if P[r + h][c + w] - P[r][c + w] - P[r + h][c] + P[r][c] == h * w:
        out.append((r, c))
  return out


def _rect_shapes(k, H, W):
  """Non-square (h, w) shapes with h*w > k*k that fit in H x W."""
  shapes = []
  for h in range(1, 9):
    w = (k * k) // h + 1
    if w == h:
      w += 1
    for a, b in ((h, w), (w, h)):
      if a != b and a <= H and b <= W and (a, b) not in shapes:
        shapes.append((a, b))
  return shapes


def _place_distractors(k, gr, gc, nr, nc, mg, H, W, want_sq, want_rect,
                       forced):
  """Returns off-block distractor cells, or None if a forced one can't fit."""
  off = [[not _on_block(r, c, k, gr, gc, nr, nc, mg) for c in range(W)]
         for r in range(H)]
  chosen = set()
  if want_sq:
    sides = list(range(2, k))
    random.shuffle(sides)
    placed = False
    for side in sides:
      spots = _windows(off, side, side)
      if spots:
        sr, sc = random.choice(spots)
        for y in range(side):
          for x in range(side):
            chosen.add((sr + y, sc + x))
        placed = True
        break
    if not placed and forced:
      return None
  if want_rect:
    mask = [row[:] for row in off]
    for y, x in chosen:
      for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
          if 0 <= y + dy < H and 0 <= x + dx < W:
            mask[y + dy][x + dx] = False
    options = []
    for h, w in _rect_shapes(k, H, W):
      spots = _windows(mask, h, w)
      if spots:
        options.append((h, w, spots))
    if options:
      h, w, spots = random.choice(options)
      sr, sc = random.choice(spots)
      for y in range(h):
        for x in range(w):
          chosen.add((sr + y, sc + x))
    elif forced:
      return None
  return chosen


def _max_foreign_square(g, exclude):
  """Largest solid square component of a colour other than `exclude`."""
  H, W = len(g), len(g[0])
  best = 0
  for nbrs in (_DIRS, _DIRS + _DIAG):
    seen = [[False] * W for _ in range(H)]
    for r in range(H):
      for c in range(W):
        if seen[r][c] or g[r][c] == exclude:
          continue
        col = g[r][c]
        stack = [(r, c)]
        seen[r][c] = True
        n = 0
        ya, yb, xa, xb = r, r, c, c
        while stack:
          y, x = stack.pop()
          n += 1
          ya, yb, xa, xb = min(ya, y), max(yb, y), min(xa, x), max(xb, x)
          for dy, dx in nbrs:
            qy, qx = y + dy, x + dx
            if (0 <= qy < H and 0 <= qx < W and not seen[qy][qx] and
                g[qy][qx] == col):
              seen[qy][qx] = True
              stack.append((qy, qx))
        h, w = yb - ya + 1, xb - xa + 1
        if h == w and n == h * w:
          best = max(best, n)
  return best


def _axis_counts(n, k, g, avail):
  if n is not None:
    return [n] if _span(n, k, g) <= avail else []
  return [m for m in range(1, _N_CAP + 1) if _span(m, k, g) <= avail]


def _pairs(k, gr, gc, rows, cols, margins):
  """Feasible (nr, nc) block counts with at least four blocks."""
  ar = 28 if margins is None else 30 - margins[0] - margins[1]
  ac = 28 if margins is None else 30 - margins[2] - margins[3]
  nrs = _axis_counts(rows, k, gr, ar)
  ncs = _axis_counts(cols, k, gc, ac)
  return [(a, b) for a in nrs for b in ncs if a * b >= 4]


def _sample_layout(block_size, gap, col_gap, rows, cols, margins):
  """Samples (k, row_gap, col_gap, nr, nc, margins), or None."""
  k = block_size if block_size is not None else random.choice(_K_CHOICES)
  gr = gap if gap is not None else random.choice(_GAP_CHOICES)
  if col_gap is not None:
    gc = col_gap
  elif gap is not None:
    gc = gap
  elif random.random() < 0.6:
    gc = gr
  else:
    gc = random.choice([v for v in _GAP_VALUES if v != gr])
  pairs = _pairs(k, gr, gc, rows, cols, margins)
  if not pairs:
    return None
  if rows is not None:
    nr = rows
  else:
    nr = random.choice(sorted({a for a, _ in pairs}))
  ncs = [b for a, b in pairs if a == nr]
  if cols is not None:
    nc = cols
  elif nr in ncs and random.random() < 0.4:
    nc = nr
  else:
    nc = random.choice(ncs)
  ih, iw = _span(nr, k, gr), _span(nc, k, gc)
  if margins is not None:
    mg = margins
  else:
    hr = min(k + gr - 1, 5)
    hc = min(k + gc - 1, 5)
    top = random.randint(1, min(hr, 29 - ih))
    bottom = random.randint(1, min(hr, 30 - ih - top))
    left = random.randint(1, min(hc, 29 - iw))
    right = random.randint(1, min(hc, 30 - iw - left))
    mg = (top, bottom, left, right)
  return k, gr, gc, nr, nc, mg


def generate(block_size=None, gap=None, rows=None, cols=None, margins=None,
             colors=None, strokes=None, noise=None, noise_color=None,
             col_gap=None, distractor=None):
  """Returns a lattice-of-blocks puzzle.

  Args:
    block_size: odd integer side k (>= 3) of each block. Random from 3, 5, 7, 9
      when omitted. Values whose layout cannot fit are rejected (k <= 13).
    gap: integer number (>= 1) of gap rows between block rows. It is also the
      column gap unless col_gap is given. Random from 1..3 when omitted.
    rows: integer number of block rows.
    cols: integer number of block columns. rows*cols must be >= 4.
    margins: (top, bottom, left, right) integer margin widths around the
      blocks (list or tuple).
    colors: (block, path, background, line) colours, distinct integers 0..9.
    strokes: list of polylines forming the path. Each polyline is a non-empty
      list of integer (row, col) vertices in output space with axis-aligned
      segments. Requires block_size, rows and cols. The path must touch >= 3
      blocks, leave a block free, fill no block and no output line.
    noise: list of integer (row, col) input cells, off the blocks, that
      receive noise_color. A non-empty list requires noise_color and the full
      layout (block_size, gap, rows, cols, margins). An empty list means no
      noise and must not be combined with noise_color. If None, noise is
      sampled on background (sometimes also line) cells: always when
      noise_color or a distractor is requested, otherwise with probability
      0.35.
    noise_color: integer colour of the noise, distinct from colors.
    col_gap: integer number (>= 1) of gap columns between block columns.
      Defaults to gap when gap is given. Otherwise it equals the row gap in
      60% of scenes and differs from it in the remaining 40%.
    distractor: None (random), 'none', 'square' (near-miss square of side
      2..k-1), 'rect' (solid non-square rectangle of area > k*k) or 'both'.
      Distractors use the noise colour and lie off the blocks. Only valid with
      noise=None. 'rect' is impossible for k >= 13 and is rejected there.
  """
  if block_size is not None:
    _check_int('block_size', block_size, 3)
    if block_size % 2 == 0:
      raise ValueError('block_size must be odd and >= 3')
  for name, v in (('gap', gap), ('col_gap', col_gap), ('rows', rows),
                  ('cols', cols)):
    if v is not None:
      _check_int(name, v, 1)
  if margins is not None:
    if not _is_seq(margins) or len(margins) != 4:
      raise ValueError('margins must be four non-negative widths')
    for m in margins:
      _check_int('margin', m, 0)
    margins = tuple(margins)
  if noise_color is not None:
    _check_int('noise_color', noise_color, 0, 9)
  if colors is not None:
    if not _is_seq(colors) or len(colors) != 4:
      raise ValueError('colors must be four distinct colours in 0..9')
    for c in colors:
      _check_int('colour', c, 0, 9)
    colors = tuple(colors)
    if len(set(colors)) != 4:
      raise ValueError('colors must be four distinct colours in 0..9')
    if noise_color is not None and noise_color in colors:
      raise ValueError('noise_color must differ from colors')
  if distractor is not None:
    if not isinstance(distractor, str) or distractor not in _DISTRACTORS:
      raise ValueError('distractor must be one of ' + ', '.join(_DISTRACTORS))
    if noise is not None:
      raise ValueError('distractor applies only to sampled noise (noise=None)')
    if (distractor in ('rect', 'both') and block_size is not None and
        block_size >= 13):
      raise ValueError('a rectangle distractor cannot fit when k >= 13')
  if strokes is not None:
    if not _is_seq(strokes):
      raise ValueError('strokes must be a list of polylines')
    checked = []
    for s in strokes:
      s = _check_cells('stroke vertex', s)
      if not s:
        raise ValueError('each stroke needs at least one vertex')
      checked.append(s)
    strokes = checked
    if block_size is None or rows is None or cols is None:
      raise ValueError('strokes are in output space; give block_size, rows '
                       'and cols with them')
  if noise is not None:
    noise = _check_cells('noise', noise)
    if noise and noise_color is None:
      raise ValueError('noise cells need a noise_color')
    if not noise and noise_color is not None:
      raise ValueError('noise_color would be ignored with an empty noise list')
    if noise and any(v is None for v in (block_size, gap, rows, cols,
                                          margins)):
      raise ValueError('explicit noise cells need block_size, gap, rows, '
                       'cols and margins')
  path_given = _strokes_to_cells(strokes) if strokes is not None else None
  explicit = all(v is not None for v in (block_size, gap, rows, cols, margins,
                                         colors, strokes, noise))
  gc_fixed = col_gap if col_gap is not None else gap
  if explicit:
    if rows * cols < 4:
      raise ValueError('a scene needs at least four blocks')
    hh = margins[0] + _span(rows, block_size, gap) + margins[1]
    ww = margins[2] + _span(cols, block_size, gc_fixed) + margins[3]
    if hh > 30 or ww > 30:
      raise ValueError('requested layout exceeds 30x30')
  else:
    ks = [block_size] if block_size is not None else sorted(set(_K_CHOICES))
    grs = [gap] if gap is not None else list(_GAP_VALUES)
    gcs = [gc_fixed] if gc_fixed is not None else list(_GAP_VALUES)
    if not any(_pairs(k, a, b, rows, cols, margins)
               for k in ks for a in grs for b in gcs):
      raise ValueError('requested layout cannot fit >= 4 blocks in 30x30')
  if path_given is not None:
    R0, C0 = block_size * rows, block_size * cols
    if not path_given:
      raise ValueError('strokes must draw a non-empty path')
    if any(not (0 <= r < R0 and 0 <= c < C0) for r, c in path_given):
      raise ValueError('strokes leave the block area')
    if len(_touched_blocks(path_given, block_size)) < 3:
      raise ValueError('strokes must touch at least three blocks')
    if not _keeps_block_colour(path_given, block_size, rows, cols):
      raise ValueError('strokes cover every block or a whole output line')
    if _fills_block(path_given, block_size):
      raise ValueError('strokes fill a whole block, giving a competing '
                       'k x k square of the path colour')
  for _ in range(500):
    if explicit:
      k, gr, gc, nr, nc, mg = block_size, gap, gc_fixed, rows, cols, margins
    else:
      layout = _sample_layout(block_size, gap, col_gap, rows, cols, margins)
      if layout is None:
        continue
      k, gr, gc, nr, nc, mg = layout
    R, C = k * nr, k * nc
    H = mg[0] + _span(nr, k, gr) + mg[1]
    W = mg[2] + _span(nc, k, gc) + mg[3]
    if colors is not None:
      cl = colors
    else:
      cl = tuple(random.sample([c for c in range(10) if c != noise_color], 4))
    if path_given is not None:
      path = path_given
    else:
      path = None
      min_len = max(2 * k + 1, min(R, C))
      for _ in range(40):
        cand = _random_path(R, C, k, nr, nc)
        if _path_ok(cand, k, nr, nc, min_len):
          path = cand
          break
      if path is None:
        continue
    if noise is not None:
      cells = list(noise)
      if any(not (0 <= r < H and 0 <= c < W) or
             _on_block(r, c, k, gr, gc, nr, nc, mg) for r, c in cells):
        raise ValueError('noise cells must lie inside the grid, off blocks')
      ncol = noise_color
    else:
      cells, ncol = [], None
      forced = distractor in ('square', 'rect', 'both')
      if noise_color is not None or forced or random.random() < 0.35:
        if noise_color is not None:
          ncol = noise_color
        else:
          ncol = random.choice([c for c in range(10) if c not in cl])
        base, _ = _render(k, gr, gc, nr, nc, mg, cl, path, [], None)
        on_lines = random.random() < 0.4
        cand = [(r, c) for r in range(H) for c in range(W)
                if base[r][c] == cl[2] or (on_lines and base[r][c] == cl[3])]
        chosen = set()
        if cand:
          cnt = max(1, int(len(cand) * random.uniform(0.04, 0.12)))
          chosen.update(random.sample(cand, min(cnt, len(cand))))
        if distractor is None:
          want_sq = random.random() < 0.3
          want_rect = random.random() < 0.3
        else:
          want_sq = distractor in ('square', 'both')
          want_rect = distractor in ('rect', 'both')
        extra = _place_distractors(k, gr, gc, nr, nc, mg, H, W, want_sq,
                                   want_rect, forced)
        if extra is None:
          continue
        chosen.update(extra)
        cells = sorted(chosen)
    g, out = _render(k, gr, gc, nr, nc, mg, cl, path, cells, ncol)
    if (not _keeps_block_colour(path, k, nr, nc) or
        _max_foreign_square(g, cl[0]) >= k * k):
      if explicit:
        raise ValueError('explicit scene is ambiguous: a colour other than '
                         'the block colour forms a solid square >= k*k')
      continue
    return {'input': g, 'output': out}
  raise ValueError('could not build a valid scene for the requested parameters')


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  noise1 = [(0, 5), (0, 17), (1, 6), (1, 12), (1, 18), (2, 13), (4, 9),
            (5, 0), (5, 10), (5, 16), (6, 1), (6, 17), (8, 13), (9, 4),
            (9, 14), (10, 5), (12, 1), (12, 17), (13, 2), (13, 8), (13, 18),
            (14, 9), (16, 5), (17, 0), (17, 6), (17, 12), (18, 1), (18, 13)]
  train = [
      generate(block_size=3, gap=1, rows=4, cols=4, margins=(2, 2, 2, 2),
               colors=(8, 9, 4, 1),
               strokes=[[(2, 1), (1, 1), (1, 4), (4, 4), (4, 7), (10, 7),
                         (10, 10)]],
               noise=noise1, noise_color=6),
      generate(block_size=3, gap=3, rows=3, cols=3, margins=(5, 5, 5, 5),
               colors=(3, 8, 1, 2),
               strokes=[[(1, 1), (1, 8)], [(1, 4), (7, 4), (7, 7), (8, 7)]],
               noise=[]),
  ]
  test = [
      generate(block_size=5, gap=1, rows=4, cols=4, margins=(3, 2, 3, 2),
               colors=(2, 1, 5, 3),
               strokes=[[(2, 2), (2, 17), (7, 17), (7, 12), (2, 12)],
                        [(2, 2), (6, 2), (6, 3), (7, 3), (7, 7), (17, 7),
                         (17, 13), (16, 13), (16, 16), (13, 16), (13, 13),
                         (7, 13)]],
               noise=[]),
  ]
  return {'train': train, 'test': test}
