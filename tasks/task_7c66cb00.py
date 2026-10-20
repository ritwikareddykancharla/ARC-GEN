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

"""ARC task 7c66cb00: drop shape colour parts into matching bands.

Rule: the lower part of the grid holds full-width horizontal bands. Each band
has an interior fill colour F and a different end colour E in its first and
last columns. Band fills are unique. The free background area above the bands
holds small shapes. In the output every shape is erased to background. Each
colour part of a shape reappears inside the band whose fill equals that
colour. The part keeps its columns and silhouette and is painted in the band's
end colour. It is moved down so that the bottom of that colour's own bounding
box, taken over the whole shape, touches the band's bottom row. Band cells the
part does not cover keep the fill colour, so holes stay visible.

Shape kinds:
  * single-colour: solid, blob, notched block, hollow ring;
  * two-colour: ring with a coloured inside (optionally divided), capsule;
  * synthetic extensions: three-colour nested ring, and 'stagger'. A stagger
    is a ring whose inner colour forms two separate blocks with different
    bottom rows. The whole colour part is aligned by its joint bounding box,
    so the two blocks keep their relative heights. This separates per-colour
    alignment from per-component alignment.

Scope:
  * Width 12..30 (default 14..30) and height 14..30 (default 18..30). The
    fixtures are all 24x30; other sizes are synthetic extensions.
  * 2..4 bands, each 3..7 rows tall, separated by one background row,
    followed by 0..2 trailing background rows. At least 7 free rows sit above
    the first band.
  * 1..5 shapes (default 2..4) placed in columns 1..W-2, with at least one
    background row or column between bounding boxes. Shapes may share
    columns only when they share no colour, so stamps never overlap.
  * Every shape colour is a band fill, and every band receives at least one
    part. Parts always fit their band's height, so no clipping occurs.
"""

import collections
import random

import common


_KIND_COLOURS = {
    'solid': 1, 'blob': 1, 'notch': 1, 'hollow': 1,
    'ring': 2, 'capsule': 2, 'stagger': 2, 'nest': 3,
}
_ALL_KINDS = ['solid', 'blob', 'notch', 'hollow', 'ring', 'ring',
              'capsule', 'stagger', 'nest']
_MULTI_KINDS = ['ring', 'ring', 'capsule', 'stagger', 'nest']


def _pattern(cells):
  """Convert {(r, c): colour} into a normalised list of strings."""
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  r1 = max(r for r, _ in cells)
  c1 = max(c for _, c in cells)
  rows = []
  for r in range(r0, r1 + 1):
    line = ''
    for c in range(c0, c1 + 1):
      line += str(cells[(r, c)]) if (r, c) in cells else '.'
    rows.append(line)
  return rows


def _solid(a, small):
  h = random.randint(1, 2 if small else 3)
  w = random.randint(2 if h == 1 else 1, 2 if small else 4)
  return _pattern({(r, c): a for r in range(h) for c in range(w)})


def _blob(a, small):
  h = random.randint(2, 3 if small else 4)
  w = random.randint(2, 3 if small else 6)
  cells = {}
  pl, pr = None, None
  for r in range(h):
    if pl is None:
      l = random.randint(0, w - 1)
      rr = random.randint(l, w - 1)
    else:
      l = random.randint(0, pr)
      rr = random.randint(max(l, pl), w - 1)
    for c in range(l, rr + 1):
      cells[(r, c)] = a
    pl, pr = l, rr
  return _pattern(cells)


def _notch(a, small):
  h = random.randint(2, 3 if small else 4)
  w = random.randint(3, 4 if small else 7)
  depth = random.randint(1, h - 1)
  l = random.randint(1, w - 2)
  rr = random.randint(l, w - 2)
  cells = {}
  for r in range(h):
    for c in range(w):
      if r >= h - depth and l <= c <= rr:
        continue
      cells[(r, c)] = a
  if random.random() < 0.5:
    cells = {(h - 1 - r, c): v for (r, c), v in cells.items()}
  return _pattern(cells)


def _ring(a, b, small):
  h = random.randint(3, 3 if small else 5)
  w = random.randint(3, 4 if small else 7)
  iw = w - 2
  dividers = set()
  if b is not None and iw >= 3 and random.random() < 0.4:
    dividers.add(random.randint(2, w - 3))
  cells = {}
  for r in range(h):
    for c in range(w):
      edge = r in (0, h - 1) or c in (0, w - 1) or c in dividers
      if edge:
        cells[(r, c)] = a
      elif b is not None:
        cells[(r, c)] = b
  return _pattern(cells)


def _capsule(a, b, small):
  n = random.randint(1, 1 if small else 5)
  w = n + 4
  cells = {}
  for c in range(1, w - 1):
    cells[(0, c)] = a
    cells[(2, c)] = a
  for c in range(w):
    cells[(1, c)] = b if 2 <= c <= n + 1 else a
  return _pattern(cells)


def _stagger(a, b, small):
  """Ring of a; inner colour b forms two blocks with different bottom rows."""
  h = random.randint(4, 4 if small else 6)
  w = random.randint(5, 5 if small else 8)
  ih, iw = h - 2, w - 2
  s = random.randint(1, iw - 2)
  uh = random.randint(1, ih - 1)
  lh = random.randint(1, ih)
  cells = {}
  for r in range(h):
    for c in range(w):
      if r in (0, h - 1) or c in (0, w - 1):
        cells[(r, c)] = a
  for r in range(1, 1 + uh):
    for c in range(1, s + 1):
      cells[(r, c)] = b
  for r in range(h - 1 - lh, h - 1):
    for c in range(s + 2, w - 1):
      cells[(r, c)] = b
  if random.random() < 0.5:
    cells = {(r, w - 1 - c): v for (r, c), v in cells.items()}
  return _pattern(cells)


def _nest(a, b, c):
  h, w = random.randint(5, 6), random.randint(5, 8)
  cells = {}
  for r in range(h):
    for x in range(w):
      d = min(r, x, h - 1 - r, w - 1 - x)
      cells[(r, x)] = a if d == 0 else (b if d == 1 else c)
  return _pattern(cells)


def _make(kind, cols, small):
  if kind == 'solid':
    return _solid(cols[0], small)
  if kind == 'blob':
    return _blob(cols[0], small)
  if kind == 'notch':
    return _notch(cols[0], small)
  if kind == 'hollow':
    return _ring(cols[0], None, small)
  if kind == 'ring':
    return _ring(cols[0], cols[1], small)
  if kind == 'capsule':
    return _capsule(cols[0], cols[1], small)
  if kind == 'stagger':
    return _stagger(cols[0], cols[1], small)
  return _nest(cols[0], cols[1], cols[2])


def _parts(pat):
  """Return {colour: height of that colour's bounding box}."""
  rows = {}
  for r, line in enumerate(pat):
    for ch in line:
      if ch != '.':
        rows.setdefault(int(ch), []).append(r)
  return {c: max(v) - min(v) + 1 for c, v in rows.items()}


def _connected(pat):
  """True if the non-empty cells of pat form one 4-connected component."""
  cells = {(r, c) for r, line in enumerate(pat)
           for c, ch in enumerate(line) if ch != '.'}
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  queue = collections.deque([start])
  while queue:
    r, c = queue.popleft()
    for nb in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
      if nb in cells and nb not in seen:
        seen.add(nb)
        queue.append(nb)
  return len(seen) == len(cells)


def _place(pats, W, top):
  """Place patterns in rows 0..top-2, columns 1..W-2, with gaps."""
  shapes = []
  boxes = []
  for p in pats:
    h, w = len(p), len(p[0])
    cols = set(_parts(p))
    spot = None
    for _ in range(200):
      r = random.randint(0, top - 1 - h)
      c = random.randint(1, W - 1 - w)
      box = (r, c, r + h - 1, c + w - 1)
      ok = True
      for ob, ocols in boxes:
        apart_rows = box[2] + 1 < ob[0] or ob[2] + 1 < box[0]
        apart_cols = box[3] + 1 < ob[1] or ob[3] + 1 < box[1]
        if not (apart_rows or apart_cols):
          ok = False
          break
        share_cols = not (box[3] < ob[1] or ob[3] < box[1])
        if share_cols and cols & ocols:
          ok = False
          break
      if ok:
        spot = (r, c, box)
        break
    if spot is None:
      return None
    shapes.append((spot[0], spot[1], p))
    boxes.append((spot[2], cols))
  return shapes


def _dominated(grid, bg):
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  return all(n < counts.get(bg, 0) for c, n in counts.items() if c != bg)


def _sample(width, height, background, num_bands, num_shapes):
  for attempt in range(400):
    small = attempt >= 200  # compact shapes once plain sampling struggles
    W = width if width is not None else random.randint(14, 30)
    H = height if height is not None else random.randint(18, 30)
    bg = background if background is not None else random.randint(0, 9)
    kmax = min(4, (H - 6) // 4)
    if num_bands is not None:
      k = num_bands
    else:
      opts = [v for v in (2, 2, 3, 3, 3, 4) if v <= kmax and
              (num_shapes is None or v <= 3 * num_shapes)]
      if not opts:
        continue
      k = random.choice(opts)
    spare = H - 7 - (k - 1) - 3 * k
    if spare < 0:
      continue
    mandatory_nest = num_shapes is not None and k > 2 * num_shapes
    if mandatory_nest and spare < 2:
      continue
    reserved_nest = 2 if mandatory_nest else 0
    trailing = random.randint(0, min(2, spare - reserved_nest))
    spare -= trailing
    extra = random.randint(reserved_nest, min(spare, 4 * k))
    hs = [3] * k
    if mandatory_nest:
      hs[random.randrange(k)] += 2
      extra -= 2
    for _ in range(extra):
      idx = random.choice([i for i in range(k) if hs[i] < 7])
      hs[idx] += 1
    top = H - sum(hs) - (k - 1) - trailing
    others = [c for c in range(10) if c != bg]
    fills = random.sample(others, k)
    bands = []
    y = top
    for f, h in zip(fills, hs):
      e = random.choice([c for c in others if c != f])
      bands.append((y, h, f, e))
      y += h + 1
    hmap = {f: h for f, h in zip(fills, hs)}
    if num_shapes is not None:
      n = num_shapes
    else:
      n = random.randint(max(2, (k + 1) // 2), 4)
    pats = []
    covered = set()
    failed = False
    for i in range(n):
      left = n - i
      unc = [f for f in fills if f not in covered]
      if len(unc) > 2 * left:
        allowed = ['nest']
      elif len(unc) > left:
        allowed = _MULTI_KINDS
      else:
        allowed = _ALL_KINDS
      pat = None
      for _ in range(40):
        kind = random.choice(allowed)
        ncol = _KIND_COLOURS[kind]
        if ncol > k:
          continue
        pool = unc[:]
        random.shuffle(pool)
        rest = [f for f in fills if f in covered]
        random.shuffle(rest)
        cols = (pool + rest)[:ncol]
        random.shuffle(cols)
        cand = _make(kind, cols, small)
        if len(cand) > top - 1 or len(cand[0]) > W - 3:
          continue
        if any(hmap[c] < ph for c, ph in _parts(cand).items()):
          continue
        pat = cand
        break
      if pat is None:
        failed = True
        break
      pats.append(pat)
      covered.update(_parts(pat).keys())
    if failed or covered != set(fills):
      continue
    random.shuffle(pats)
    shapes = _place(pats, W, top)
    if shapes is None:
      continue
    grid = _build_input(W, H, bg, bands, shapes)
    if not _dominated(grid, bg):
      continue
    return W, H, bg, bands, shapes
  raise ValueError('could not sample a scene for the requested parameters')


def _build_input(W, H, bg, bands, shapes):
  grid = common.grid(W, H, bg)
  for top, h, f, e in bands:
    for y in range(top, top + h):
      grid[y] = [e] + [f] * (W - 2) + [e]
  for r, c, pat in shapes:
    for dy, line in enumerate(pat):
      for dx, ch in enumerate(line):
        if ch != '.':
          grid[r + dy][c + dx] = int(ch)
  return grid


def _check_scene(W, H, bg, bands, shapes):
  """Reject explicit scenes that break the task's input invariants."""
  if not (3 <= W <= 30 and 1 <= H <= 30 and 0 <= bg <= 9):
    raise ValueError('bad grid size or background')
  if not isinstance(bands, (list, tuple)) or not 2 <= len(bands) <= 4:
    raise ValueError('two to four bands are required')
  if any(not isinstance(b, (list, tuple)) or len(b) != 4 or any(type(v) is not int for v in b) for b in bands):
    raise ValueError('bands require four integer parameters')
  if not isinstance(shapes, (list, tuple)) or any(not isinstance(s, (list, tuple)) or len(s) != 3 or any(type(v) is not int for v in s[:2]) for s in shapes):
    raise ValueError('shapes require integer row/col and a pattern')
  fills = [b[2] for b in bands]
  if len(set(fills)) != len(fills):
    raise ValueError('band fills must be unique')
  prev_bottom = None
  for top, h, f, e in sorted(bands):
    if not (0 <= f <= 9 and 0 <= e <= 9):
      raise ValueError('band colours must be 0..9')
    if top < 0 or h < 1 or top + h > H:
      raise ValueError('band out of bounds')
    if f == e or f == bg or e == bg:
      raise ValueError('band fill, end and background must differ')
    if prev_bottom is not None and top <= prev_bottom + 1:
      raise ValueError('bands need at least one background row between')
    prev_bottom = top + h - 1
  first_top = min(b[0] for b in bands)
  hmap = {f: h for _, h, f, _ in bands}
  boxes = []
  covered, stamped = set(), set()
  for r, c, pat in shapes:
    if not isinstance(pat, (list, tuple)) or any(not isinstance(line, str) for line in pat):
      raise ValueError('pattern rows must be strings')
    if not pat or any(len(l) != len(pat[0]) for l in pat):
      raise ValueError('pattern must be a non-empty rectangle')
    if any(ch != '.' and ch not in "0123456789" for l in pat for ch in l):
      raise ValueError('pattern characters must be digits or "."')
    h, w = len(pat), len(pat[0])
    if r < 0 or r + h > first_top - 1:
      raise ValueError('shape must sit above the first band with a gap')
    if c < 1 or c + w > W - 1 or w > W - 3:
      raise ValueError('shape must stay inside columns 1..W-2')
    if not _connected(pat):
      raise ValueError('shape must be one connected object')
    for col, ph in _parts(pat).items():
      if col not in hmap:
        raise ValueError('shape colour has no matching band')
      if ph > hmap[col]:
        raise ValueError('colour part taller than its band')
    for col in _parts(pat):
      covered.add(col)
      band_top, bh, _, _ = next(b for b in bands if b[2] == col)
      cells = [(dy, dx) for dy, line in enumerate(pat) for dx, ch in enumerate(line) if ch == str(col)]
      bottom = max(dy for dy, _ in cells)
      target = {(band_top+bh-1+dy-bottom, c+dx) for dy, dx in cells}
      if stamped & target:
        raise ValueError('different shapes would overlap in their target band')
      stamped.update(target)
    box = (r, c, r + h - 1, c + w - 1)
    for ob in boxes:
      apart_rows = box[2] + 1 < ob[0] or ob[2] + 1 < box[0]
      apart_cols = box[3] + 1 < ob[1] or ob[3] + 1 < box[1]
      if not (apart_rows or apart_cols):
        raise ValueError('shape bounding boxes must be separated')
    boxes.append(box)
  if covered != set(fills):
    raise ValueError('every band must receive a shape part')
  if not _dominated(_build_input(W, H, bg, bands, shapes), bg):
    raise ValueError('background must be the most frequent colour')


def generate(width=None, height=None, background=None, bands=None,
             shapes=None, num_bands=None, num_shapes=None):
  """Build one input/output pair.

  Args:
    width: grid width (12..30; sampled 14..30 if None).
    height: grid height (14..30; sampled 18..30 if None).
    background: background colour (sampled if None).
    bands: explicit list of (top_row, band_height, fill, end) tuples.
    shapes: explicit list of (row, col, pattern). A pattern is a list of
      equal-length strings with '.' for empty cells and digits for colours.
    num_bands: number of bands (2..4) for random scenes.
    num_shapes: number of shapes (1..5) for random scenes.

  To reconstruct an explicit scene, give bands and shapes together, with
  width, height and background. Explicit scenes are validated and rejected
  with ValueError if they break the task invariants. Otherwise a fresh random
  scene is sampled that honours width, height, background, num_bands and
  num_shapes.
  """
  for name, value in (("width", width), ("height", height), ("background", background), ("num_bands", num_bands), ("num_shapes", num_shapes)):
    if value is not None and type(value) is not int:
      raise ValueError(name + " must be an integer")
  if bands is not None or shapes is not None:
    if bands is None or shapes is None:
      raise ValueError('bands and shapes must be given together')
    if width is None or height is None or background is None:
      raise ValueError('explicit scenes need width, height and background')
    if num_bands is not None and num_bands != len(bands):
      raise ValueError('num_bands disagrees with bands')
    if num_shapes is not None and num_shapes != len(shapes):
      raise ValueError('num_shapes disagrees with shapes')
    _check_scene(width, height, background, bands, shapes)
    W, H, bg = width, height, background
  else:
    if width is not None and not 12 <= width <= 30:
      raise ValueError('width must be in 12..30')
    if height is not None and not 14 <= height <= 30:
      raise ValueError('height must be in 14..30')
    if background is not None and not 0 <= background <= 9:
      raise ValueError('background must be in 0..9')
    if num_bands is not None:
      if not 2 <= num_bands <= 4:
        raise ValueError('num_bands must be in 2..4')
      if height is not None and height < 4 * num_bands + 6:
        raise ValueError('height too small for num_bands')
    if num_shapes is not None:
      if not 1 <= num_shapes <= 5:
        raise ValueError('num_shapes must be in 1..5')
      if num_bands is not None and num_bands > 3 * num_shapes:
        raise ValueError('too few shapes to reach every band')
      if num_bands is not None and num_bands > 2*num_shapes and height is not None and height < 4*num_bands+8:
        raise ValueError('height too small for a required three-colour nest')
    W, H, bg, bands, shapes = _sample(width, height, background, num_bands,
                                      num_shapes)
  grid = _build_input(W, H, bg, bands, shapes)
  out = [row[:] for row in grid]
  band_of = {f: (top, top + h - 1, e) for top, h, f, e in bands}
  for r, c, pat in shapes:
    for dy, line in enumerate(pat):
      for dx, ch in enumerate(line):
        if ch != '.':
          out[r + dy][c + dx] = bg
  for r, c, pat in shapes:
    parts = {}
    for dy, line in enumerate(pat):
      for dx, ch in enumerate(line):
        if ch != '.':
          parts.setdefault(int(ch), []).append((r + dy, c + dx))
    for col, cells in parts.items():
      t, b, e = band_of[col]
      shift = b - max(y for y, _ in cells)
      for y, x in cells:
        ny = y + shift
        if t <= ny <= b:
          out[ny][x] = e
  return {'input': grid, 'output': out}


def validate():
  """Reconstruct the canonical examples from explicit latent parameters."""
  train = [
      generate(24, 30, 1,
               bands=[(10, 7, 3, 4), (18, 6, 2, 5), (25, 4, 8, 3)],
               shapes=[(1, 2, ['222', '282', '222']),
                       (2, 7, ['333333', '322223', '333333']),
                       (4, 17, ['88', '88'])]),
      generate(24, 30, 8,
               bands=[(13, 8, 2, 4), (22, 6, 4, 6)],
               shapes=[(1, 1, ['2222', '2442', '2442', '2222']),
                       (2, 8, ['2222222', '2442442', '2442442',
                               '2442442', '2222222'])]),
      generate(24, 30, 4,
               bands=[(16, 8, 3, 1), (25, 5, 8, 6)],
               shapes=[(6, 6, ['.33.', '3333', '.33.']),
                       (11, 3, ['33', '33']),
                       (10, 13, ['8888888', '8888888', '88...88'])]),
  ]
  test = [
      generate(24, 30, 8,
               bands=[(14, 5, 1, 3), (20, 4, 2, 1), (25, 4, 3, 4)],
               shapes=[(2, 2, ['11111', '12221', '11111']),
                       (4, 9, ['33', '33']),
                       (7, 12, ['.2222222.', '223333322', '.2222222.'])]),
  ]
  return {'train': train, 'test': test}
