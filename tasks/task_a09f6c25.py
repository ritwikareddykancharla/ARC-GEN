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

"""ARC task a09f6c25: recolour glyphs by mirror symmetry and erase noise.

Rule: the input has one background colour and the single foreground colour 2.
The 2-cells form several multi-cell glyphs plus some isolated single cells.
In the output every single cell is erased to background. Every glyph keeps its
exact cells and is repainted according to the symmetry of its cropped mask:
  * up-down mirror symmetric (horizontal axis)            -> 1
  * left-right mirror symmetric (vertical axis)           -> 3
  * symmetric only about a diagonal of its square bbox    -> 6
No glyph is both UD and LR, so the classes never conflict.

Random scenes (default):
  * grid sides 12..30, or 10..30 when fixed by the caller;
  * background from {0, 4, 5, 7, 8, 9};
  * 3..min(9, 3 + area // 110) glyphs, so the count scales with the canvas;
  * 2..3 + area // 100 noise pixels, and never fewer than 2;
  * scenes with two or more glyphs always contain at least two symmetry
    classes; with three or more glyphs, all three classes appear 60% of the
    time.
Controls:
  * num_shapes (1..12) or an explicit kinds list fixes the glyph count;
  * num_noise (0..30) fixes the noise count exactly.

Layout: the canvas, plus one virtual row and column, is cut into an R x C
grid of randomly sized slots. Each slot is at least 4 x 4: a glyph box of at
least 3 x 3 plus a one-cell gap. R and C are chosen from the feasible pairs
with R * C >= n. Each glyph is grown inside its own slot, capped at the slot
size, and placed at a random offset in it. Glyph size therefore scales with
the canvas. Any glyph count that passes the bound
((h + 1) // 4) * ((w + 1) // 4) is always packable, even for nine glyphs in
a 14 x 14 grid, with no retrying of oversized masks. Counts above the bound
raise ValueError immediately.

Glyph growth:
  * Glyphs are grown from a seed on the symmetry axis, closed under the
    mirror orbit. They are therefore 4-connected and exactly symmetric.
  * Growth is biased towards thin arms, which gives stroke-like glyphs with
    holes.
  * UD glyphs are up to 9 rows by 12 columns; LR glyphs are the transpose.
    Diagonal glyphs are square, 3..9 cells, about the main or anti-diagonal.
  * Shortcut negatives: about 22% of UD/LR glyphs are forced to a square
    bbox, and about 18% are 'tall' UD (taller than wide) or 'wide' LR. Axes
    may also fall between two rows or columns.
  * If growth fails 80 times, a hand-checked 3 x 3 template of the right
    class is used.

Noise pixels lie outside every glyph bbox and are 8-isolated from all other
foreground; they may sit right beside a bbox, as in the fixtures. Glyph boxes
are separated by at least one background row or column, so 4- and
8-connected components coincide.

Explicit scenes (shapes=...) are checked, not resampled, for:
  * well-formed entries;
  * in-bounds cells;
  * 4-connected glyphs whose crop is at least 3 x 3 and has exactly the
    declared class;
  * no overlap;
  * 8-isolation between objects;
  * no foreign object cell inside a glyph bbox;
  * a background majority.

Malformed or infeasible controls raise ValueError. Random construction is
bounded and raises ValueError if the requested combination cannot be met.

Not generated: glyphs that are both UD and LR, glyphs with no symmetry,
two-cell or diagonally touching objects, noise inside a glyph bbox, and
foreground colours other than 2.
"""

import random

import common


_FG = 2
_KINDS = ('UD', 'LR', 'D')
_KIND_COLOUR = {'UD': 1, 'LR': 3, 'D': 6}
_BACKGROUNDS = (0, 4, 5, 7, 8, 9)
_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_NEIGH8 = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
           if (dr, dc) != (0, 0)]
# Fallback 3x3 masks, each verified to have exactly the listed class.
_TEMPLATES = {
    'UD': (['#..', '###', '#..'], ['..#', '###', '..#'],
           ['##.', '.##', '##.']),
    'LR': (['###', '.#.', '.#.'], ['.#.', '.#.', '###'],
           ['#.#', '###', '.#.']),
    'D': (['###', '#..', '#..'], ['..#', '..#', '###'],
          ['#..', '##.', '.##'], ['##.', '.##', '..#']),
}


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _check_int(name, v, lo, hi):
  """Raises ValueError unless v is None or a plain int in lo..hi."""
  if v is None:
    return
  if not _is_int(v):
    raise ValueError('%s must be an int, got %r' % (name, v))
  if not lo <= v <= hi:
    raise ValueError('%s must be in %d..%d' % (name, lo, hi))


def _check_background(background):
  if background is None:
    return
  if not _is_int(background) or background not in _BACKGROUNDS:
    raise ValueError('background must be one of %r' % (_BACKGROUNDS,))


def _check_kinds(kinds):
  if isinstance(kinds, str) or not isinstance(kinds, (list, tuple)):
    raise ValueError('kinds must be a list of glyph kinds')
  if not 1 <= len(kinds) <= 12:
    raise ValueError('kinds must list 1..12 glyphs')
  for k in kinds:
    if not isinstance(k, str) or k not in _KIND_COLOUR:
      raise ValueError('unknown glyph kind %r' % (k,))
  return list(kinds)


def _mask_rows(mask):
  """Normalises a mask of strings ('#' = cell, '.' = empty) or 0/1 rows."""
  if isinstance(mask, str) or not isinstance(mask, (list, tuple)) or not mask:
    raise ValueError('mask must be a non-empty list of rows')
  rows = []
  for row in mask:
    if isinstance(row, str):
      if any(ch not in '#.' for ch in row):
        raise ValueError('mask strings may only contain # and .')
      rows.append([1 if ch == '#' else 0 for ch in row])
    elif isinstance(row, (list, tuple)):
      vals = []
      for v in row:
        if not _is_int(v) or v not in (0, 1):
          raise ValueError('mask rows must contain only 0/1 ints')
        vals.append(v)
      rows.append(vals)
    else:
      raise ValueError('mask rows must be strings or lists')
  return rows


def _crop(cells):
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  h = max(r for r, _ in cells) - r0 + 1
  w = max(c for _, c in cells) - c0 + 1
  m = [[0] * w for _ in range(h)]
  for r, c in cells:
    m[r - r0][c - c0] = 1
  return m


def _transpose(m):
  return [list(col) for col in zip(*m)]


def _anti_transpose(m):
  n = len(m)
  return [[m[n - 1 - j][n - 1 - i] for j in range(n)] for i in range(n)]


def _is_ud(m):
  return m == m[::-1]


def _is_lr(m):
  return all(row == row[::-1] for row in m)


def _is_diag(m):
  return len(m) == len(m[0]) and (m == _transpose(m) or
                                  m == _anti_transpose(m))


def _classify(m):
  """Symmetry class of a cropped multi-cell mask (UD checked first)."""
  if _is_ud(m):
    return 'UD'
  if _is_lr(m):
    return 'LR'
  if _is_diag(m):
    return 'D'
  return None


def _connected4(cells):
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr, dc in _DIRS4:
      nxt = (r + dr, c + dc)
      if nxt in cells and nxt not in seen:
        seen.add(nxt)
        stack.append(nxt)
  return len(seen) == len(cells)


def _ud_orbit(h):
  def orbit(r, c):
    return ((r, c), (h - 1 - r, c))
  return orbit


def _main_orbit(r, c):
  return ((r, c), (c, r))


def _anti_orbit(n):
  def orbit(r, c):
    return ((r, c), (n - 1 - c, n - 1 - r))
  return orbit


def _grow(h, w, orbit, seed, target, stroke):
  """Grows a 4-connected cell set closed under a symmetry orbit.

  Args:
    h: height of the growth box.
    w: width of the growth box.
    orbit: function mapping a cell to its symmetry orbit (stays in box).
    seed: starting cell on the symmetry axis.
    target: approximate number of cells to reach.
    stroke: probability of extending a thin arm (frontier cell with exactly
      one neighbour in the shape) instead of any frontier cell.
  """
  shape = set(orbit(seed[0], seed[1]))
  for _ in range(4 * h * w):
    if len(shape) >= target:
      break
    frontier = {}
    for r, c in shape:
      for dr, dc in _DIRS4:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in shape:
          frontier[(nr, nc)] = frontier.get((nr, nc), 0) + 1
    if not frontier:
      break
    cells = sorted(frontier)
    thin = [p for p in cells if frontier[p] == 1]
    if thin and random.random() < stroke:
      pick = random.choice(thin)
    else:
      pick = random.choice(cells)
    shape.update(orbit(pick[0], pick[1]))
  return shape


def _box_dims(mode, gh, gw):
  """Growth-box size for a UD glyph (LR glyphs use the transposed box)."""
  if mode == 'square':
    s = random.randint(3, min(gh, gw, 8))
    return s, s
  if mode == 'tall' and gh >= 4:
    h = random.randint(4, min(gh, 9))
    return h, random.randint(3, min(gw, h - 1))
  heights = [v for v in (3, 3, 3, 4, 5, 5, 5, 6, 7, 8, 9) if v <= gh]
  return random.choice(heights), random.randint(3, gw)


def _make_mask(kind, max_h, max_w):
  """Builds a random glyph mask of exactly the requested symmetry class.

  Args:
    kind: 'UD', 'LR' or 'D'.
    max_h: largest allowed mask height (>= 3).
    max_w: largest allowed mask width (>= 3).
  """
  max_h = min(max_h, 12)
  max_w = min(max_w, 12)
  # LR glyphs are grown as UD glyphs in the transposed box.
  gh, gw = (max_w, max_h) if kind == 'LR' else (max_h, max_w)
  mode = 'free'
  if kind != 'D':
    x = random.random()
    if x < 0.22:
      mode = 'square'
    elif x < 0.40:
      mode = 'tall'
  for attempt in range(80):
    strict = attempt < 50
    stroke = random.uniform(0.3, 0.85)
    if kind == 'D':
      n = random.randint(3, min(9, gh, gw))
      h = w = n
      k = random.randrange(n)
      if random.random() < 0.5:
        orbit, seed = _main_orbit, (k, k)
      else:
        orbit, seed = _anti_orbit(n), (k, n - 1 - k)
      fill = random.uniform(0.3, 0.6)
    else:
      h, w = _box_dims(mode if strict else 'free', gh, gw)
      orbit = _ud_orbit(h)
      seed = ((h - 1) // 2, random.randrange(w))
      fill = random.uniform(0.45 if mode == 'square' else 0.3, 0.6)
    target = max(4, int(round(h * w * fill)))
    m = _crop(_grow(h, w, orbit, seed, target, stroke))
    if len(m) < 3 or len(m[0]) < 3:
      continue
    if strict and mode == 'square' and len(m) != len(m[0]):
      continue
    if strict and mode == 'tall' and len(m) <= len(m[0]):
      continue
    if kind == 'LR':
      m = _transpose(m)
    if len(m) > max_h or len(m[0]) > max_w:
      continue
    ud, lr = _is_ud(m), _is_lr(m)
    if kind == 'UD' and ud and not lr:
      return m
    if kind == 'LR' and lr and not ud:
      return m
    if kind == 'D' and not ud and not lr and _is_diag(m):
      return m
  return _mask_rows(random.choice(_TEMPLATES[kind]))


def _packing_bound(h, w):
  """Number of gapped 3x3 glyph boxes that fit in an h x w grid."""
  return ((h + 1) // 4) * ((w + 1) // 4)


def _noise_bound(h, w):
  """Upper bound on mutually 8-isolated single cells in an h x w grid."""
  return ((h + 1) // 2) * ((w + 1) // 2)


def _partition(total, k):
  """Random composition of total into k parts, each at least 4."""
  extras = total - 4 * k
  cuts = sorted(random.randint(0, extras) for _ in range(k - 1))
  parts = []
  prev = 0
  for cut in cuts + [extras]:
    parts.append(4 + cut - prev)
    prev = cut
  return parts


def _layout(h, w, n):
  """Returns n disjoint slots (top, left, box_h, box_w) with 1-cell gaps."""
  rmax, cmax = (h + 1) // 4, (w + 1) // 4
  pairs = [(r, c) for r in range(1, rmax + 1) for c in range(1, cmax + 1)
           if r * c >= n]
  best = min(r * c for r, c in pairs)
  pairs = [p for p in pairs if p[0] * p[1] <= best + 2]
  r, c = random.choice(pairs)
  slots = []
  y = 0
  for ph in _partition(h + 1, r):
    x = 0
    for pw in _partition(w + 1, c):
      slots.append((y, x, ph - 1, pw - 1))
      x += pw
    y += ph
  random.shuffle(slots)
  return slots[:n]


def _sample_kinds(n):
  if n >= 3 and random.random() < 0.6:
    kinds = list(_KINDS) + [random.choice(_KINDS) for _ in range(n - 3)]
  else:
    kinds = [random.choice(_KINDS) for _ in range(n)]
    if n >= 2 and len(set(kinds)) == 1:
      other = [k for k in _KINDS if k != kinds[0]]
      kinds[random.randrange(n)] = random.choice(other)
  random.shuffle(kinds)
  return kinds


def _place_noise(boxes, occupied, h, w, want):
  """Greedily places up to want 8-isolated pixels outside all glyph boxes."""
  cands = [(r, c) for r in range(h) for c in range(w)
           if not any(t <= r < t + bh and l <= c < l + bw
                      for t, l, bh, bw in boxes)]
  random.shuffle(cands)
  noise = []
  for r, c in cands:
    if len(noise) >= want:
      break
    if (r, c) in occupied or any((r + dr, c + dc) in occupied
                                 for dr, dc in _NEIGH8):
      continue
    occupied.add((r, c))
    noise.append((r, c))
  return noise


def _random_scene(width, height, background, num_shapes, num_noise, kinds):
  """Samples a scene, honouring any fixed size/colour/count controls."""
  _check_int('width', width, 10, 30)
  _check_int('height', height, 10, 30)
  if kinds is not None:
    kinds = _check_kinds(kinds)
    if num_shapes is not None and num_shapes != len(kinds):
      raise ValueError('num_shapes disagrees with kinds')
    num_shapes = len(kinds)
  hh = height if height is not None else 30
  ww = width if width is not None else 30
  if num_shapes is not None and num_shapes > _packing_bound(hh, ww):
    raise ValueError('num_shapes=%d cannot fit in the requested grid'
                     % num_shapes)
  if num_noise is not None and num_noise > _noise_bound(hh, ww):
    raise ValueError('num_noise=%d cannot fit in the requested grid'
                     % num_noise)
  for _ in range(200):
    h = height if height is not None else random.randint(12, 30)
    w = width if width is not None else random.randint(12, 30)
    if num_shapes is not None and num_shapes > _packing_bound(h, w):
      continue
    if num_noise is not None and num_noise > _noise_bound(h, w):
      continue
    bg = background if background is not None else random.choice(
        _BACKGROUNDS)
    area = h * w
    if num_shapes is not None:
      n = num_shapes
    else:
      n = random.randint(3, max(3, min(9, 3 + area // 110,
                                       _packing_bound(h, w))))
    ks = list(kinds) if kinds is not None else _sample_kinds(n)
    boxes, shapes, occupied = [], [], set()
    for kind, (y, x, bh, bw) in zip(ks, _layout(h, w, n)):
      m = _make_mask(kind, bh, bw)
      mh, mw = len(m), len(m[0])
      top = y + random.randint(0, bh - mh)
      left = x + random.randint(0, bw - mw)
      boxes.append((top, left, mh, mw))
      shapes.append((kind, top, left, m))
      for r, row in enumerate(m):
        for c, v in enumerate(row):
          if v:
            occupied.add((top + r, left + c))
    fg = len(occupied)
    if num_noise is not None:
      want = num_noise
    else:
      want = random.randint(2, 3 + area // 100)
    noise = _place_noise(boxes, occupied, h, w, want)
    if len(noise) < want and (num_noise is not None or len(noise) < 2):
      continue
    if 2 * (fg + len(noise)) >= area:
      continue
    return w, h, bg, shapes, noise
  raise ValueError('could not construct a scene with the requested controls')


def _check_scene(width, height, background, shapes, noise):
  """Rejects scenes violating the task invariants; returns glyphs, noise."""
  _check_int('width', width, 1, 30)
  _check_int('height', height, 1, 30)
  _check_background(background)
  if not isinstance(shapes, (list, tuple)) or not shapes:
    raise ValueError('shapes must be a non-empty list')
  if not isinstance(noise, (list, tuple)):
    raise ValueError('noise must be a list of (row, col) pairs')
  objects, glyphs, dots = [], [], []
  for entry in shapes:
    if not isinstance(entry, (list, tuple)) or len(entry) != 4:
      raise ValueError('each glyph must be (kind, top, left, mask)')
    kind, top, left, mask = entry
    if not isinstance(kind, str) or kind not in _KIND_COLOUR:
      raise ValueError('unknown glyph kind %r' % (kind,))
    if not (_is_int(top) and _is_int(left)):
      raise ValueError('glyph position must be ints')
    cells = set()
    for r, row in enumerate(_mask_rows(mask)):
      for c, v in enumerate(row):
        if v:
          cells.add((top + r, left + c))
    if len(cells) < 3:
      raise ValueError('glyphs need at least three cells')
    for r, c in cells:
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError('glyph out of bounds')
    if not _connected4(cells):
      raise ValueError('glyph must be 4-connected')
    m = _crop(cells)
    if len(m) < 3 or len(m[0]) < 3:
      raise ValueError('glyph bounding box must be at least 3x3')
    if _classify(m) != kind or (_is_ud(m) and _is_lr(m)):
      raise ValueError('glyph mask does not have exactly symmetry %s' % kind)
    objects.append(cells)
    glyphs.append((kind, cells))
  for cell in noise:
    if not isinstance(cell, (list, tuple)) or len(cell) != 2:
      raise ValueError('noise entries must be (row, col) pairs')
    r, c = cell
    if not (_is_int(r) and _is_int(c)):
      raise ValueError('noise coordinates must be ints')
    if not (0 <= r < height and 0 <= c < width):
      raise ValueError('noise out of bounds')
    objects.append({(r, c)})
    dots.append((r, c))
  owner = {}
  for i, cells in enumerate(objects):
    for cell in cells:
      if cell in owner:
        raise ValueError('objects overlap')
      owner[cell] = i
  for (r, c), i in owner.items():
    for dr, dc in _NEIGH8:
      j = owner.get((r + dr, c + dc))
      if j is not None and j != i:
        raise ValueError('objects touch (8-connectivity)')
  for i in range(len(glyphs)):
    cells = objects[i]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    for (r, c), j in owner.items():
      if j != i and r0 <= r <= r1 and c0 <= c <= c1:
        raise ValueError('another object lies inside a glyph bounding box')
  if 2 * len(owner) >= width * height:
    raise ValueError('background must remain the majority colour')
  return glyphs, dots


def generate(width=None, height=None, background=None, shapes=None,
             noise=None, num_shapes=None, num_noise=None, kinds=None):
  """Returns an input/output pair for task a09f6c25.

  Args:
    width: grid width (columns). Random scenes accept 10..30 (default random
      12..30); explicit scenes 1..30. Must be an int.
    height: grid height (rows). Same ranges as width.
    background: background colour, one of 0, 4, 5, 7, 8, 9 (int).
    shapes: list of (kind, top, left, mask) glyphs. kind is 'UD' (up-down
      symmetric, becomes 1), 'LR' (left-right symmetric, becomes 3) or 'D'
      (diagonal-only symmetric, becomes 6). mask is a list of strings
      ('#' = foreground, '.' = empty) or 0/1 rows. When given, width, height
      and background are required and the scene is checked, not resampled.
    noise: list of (row, col) isolated foreground cells, erased in the
      output. Only valid together with explicit shapes.
    num_shapes: exact glyph count for random scenes (int, 1..12).
    num_noise: exact noise-pixel count for random scenes (int, 0..30).
    kinds: optional list of glyph kinds for random scenes; it fixes both the
      glyph count and the class of each glyph.
  """
  _check_background(background)
  _check_int('num_shapes', num_shapes, 1, 12)
  _check_int('num_noise', num_noise, 0, 30)
  if shapes is None:
    if noise is not None:
      raise ValueError('explicit noise requires explicit shapes')
    width, height, background, shapes, noise = _random_scene(
        width, height, background, num_shapes, num_noise, kinds)
  else:
    if kinds is not None:
      raise ValueError('kinds only applies to random scenes')
    if width is None or height is None or background is None:
      raise ValueError('explicit shapes need width, height and background')
    if noise is None:
      noise = []
    if not isinstance(shapes, (list, tuple)) or not isinstance(
        noise, (list, tuple)):
      raise ValueError('shapes and noise must be lists')
    if num_shapes is not None and num_shapes != len(shapes):
      raise ValueError('num_shapes disagrees with explicit shapes')
    if num_noise is not None and num_noise != len(noise):
      raise ValueError('num_noise disagrees with explicit noise')
  glyphs, dots = _check_scene(width, height, background, shapes, noise)
  grid = common.grid(width, height, background)
  output = common.grid(width, height, background)
  for kind, cells in glyphs:
    for r, c in cells:
      grid[r][c] = _FG
      output[r][c] = _KIND_COLOUR[kind]
  for r, c in dots:
    grid[r][c] = _FG
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the canonical fixtures from explicit latent scenes."""
  train = [
      generate(width=19, height=19, background=7, shapes=[
          ('D', 0, 0, ['...#.', '..###', '.###.', '###..', '.#...']),
          ('UD', 3, 6, ['.#......', '.##....#', '########', '.##....#',
                        '.#......']),
          ('LR', 9, 1, ['..#..', '.###.', '.###.', '#####', '..#..',
                        '..#..']),
          ('LR', 9, 16, ['.#.', '###', '.#.', '.#.']),
          ('UD', 12, 8, ['..#...', '###...', '#.####', '###...',
                         '..#...']),
      ], noise=[(1, 15), (8, 10), (17, 16)]),
      generate(width=19, height=19, background=8, shapes=[
          ('UD', 2, 5, ['..###..#.', '###.#####', '..###..#.']),
          ('LR', 9, 2, ['.#.', '###', '.#.', '###', '#.#', '###', '#.#']),
          ('UD', 9, 9, ['.##...', '##....', '######', '##....',
                        '.##...']),
      ], noise=[(3, 2), (7, 18), (15, 17), (16, 11)]),
      generate(width=19, height=17, background=4, shapes=[
          ('UD', 1, 3, ['..#...', '.##.#.', '######', '.##.#.',
                        '..#...']),
          ('LR', 3, 13, ['###', '###', '.#.', '.#.']),
          ('LR', 10, 10, ['.#.#.', '#####', '.###.', '..#..']),
          ('UD', 12, 0, ['.##..', '#####', '.##..']),
      ], noise=[(8, 18), (9, 5), (16, 8)]),
  ]
  test = [
      generate(width=27, height=28, background=8, shapes=[
          ('UD', 3, 2, ['.#.#..###.#', '#######.###', '.#.#..###.#']),
          ('LR', 4, 16, ['...#...', '.#####.', '...#...', '..###..',
                         '.##.##.', '.#...#.', '.#...#.', '###.###',
                         '.#...#.']),
          ('D', 10, 3, ['.##.....', '#####...', '##..#...', '.#..###.',
                        '.###..#.', '...#..##', '...#####', '.....##.']),
          ('LR', 17, 18, ['.#.', '###', '#.#', '#.#', '###', '#.#']),
          ('UD', 22, 5, ['#....', '#####', '#....']),
          ('UD', 24, 21, ['...#.', '#####', '...#.']),
      ], noise=[(1, 17), (2, 24), (9, 9), (11, 11), (15, 14), (15, 24),
                (19, 2), (24, 13), (25, 1)]),
      generate(width=27, height=26, background=4, shapes=[
          ('UD', 0, 2, ['......#.', '#.#..###', '######.#', '#.#..###',
                        '......#.']),
          ('UD', 2, 14, ['.###.....', '.#.###..#', '##.#.####', '.#.###..#',
                         '.###.....']),
          ('D', 8, 9, ['###..', '#.#..', '#####', '..#.#', '..###']),
          ('LR', 10, 1, ['.#.#.', '#####', '..#..', '.###.', '#####',
                         '..#..', '..#..', '.###.', '.#.#.', '.#.#.']),
          ('LR', 12, 18, ['#.#.#', '#####', '.#.#.', '.###.', '#####',
                          '.#.#.', '.###.']),
          ('D', 19, 22, ['...##', '.####', '.#.#.', '####.', '##...']),
          ('UD', 21, 8, ['###..####.', '#.####.###', '###..####.']),
      ], noise=[(6, 5), (9, 18), (9, 23), (18, 10), (23, 1)]),
  ]
  return {'train': train, 'test': test}
