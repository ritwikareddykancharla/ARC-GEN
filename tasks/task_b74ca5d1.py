"""ARC task b74ca5d1: corner-legend glyph colour swap and corner stamping.

Rule:
  Some of the four grid corners hold a single non-background cell. Each such
  colour names its corner. Every other non-background colour forms one glyph.
  A glyph fits in a 5x5 box and contains exactly one marker cell whose colour
  is a corner colour. In the output:
    * Swap: the glyph body takes the marker colour, and the marker cell takes
      the old body colour.
    * Stamp: the glyph silhouette is drawn in the marker colour, flush into the
      corner named by that colour. The silhouette is the body plus the marker,
      over their joint bounding box. Stamps aimed at the same corner are
      unioned.
    * Marked corner cells never change.

Scope:
  All original examples are 30x30. The rule does not depend on that size, so
  other sizes are synthetic extensions. Half of default calls use 30x30. The
  other half use synthetic sizes, with each side drawn uniformly from 18..30.
  Explicit sides in 16..30 are accepted for random generation. Small sides
  combined with many corners may be infeasible. Such calls raise
  RuntimeError after a bounded search.
  The generator samples:
    * the background colour;
    * 1-4 marked corners with distinct colours, none equal to the background;
    * usually every marked corner receives at least one glyph, so same-corner
      unions are common. Sometimes (synthetic distractor extension, about 20%
      of scenes with 2+ corners) one marked corner is idle: it is in the
      legend, but no glyph points at it, so it stays unchanged;
    * glyphs with pairwise distinct body colours (default 2-6, scaled to grid
      area);
    * random glyph patterns of 3..5 cells per side, usually 5x5 and often
      symmetric. The marker sits at the centre or anywhere in the box, so it
      sometimes extends the bounding box of the silhouette;
    * glyph placements, found by an exhaustive shuffled search. Glyph boxes
      keep a one-cell gap from each other. They also stay clear of the grid
      border and of the 6x6 stamp area of every marked corner. If no slot
      fits, a glyph shrinks to 4x4 and then to 3x3.
  Every scene enforces the marker-search invariant of the reference. The
  window of a glyph body is every cell that one 5x5 box could share with the
  body. That window must contain the glyph's own marker and no other marker.
  Not supported: two glyphs sharing a body colour, and glyphs larger than
  5x5. Random mode never places a glyph inside a stamp area; replay mode
  allows it. Like the reference, all swaps happen before any stamp, and
  stamps are applied in ascending body-colour order.

Data note:
  The fixtures follow the curated teaching copy. Per the task explanation,
  that copy corrects three output cells, in train pair 3 and test 2 (open
  PR #16). Canonical and approved teaching copies differ at (3,27) and
  (4,27) in train pair 3, and (13,15) in test pair 2 (zero-based cells).
  The union of the two marker-4 silhouettes supports the teaching value 4
  for the two training cells; the query correction changes 4 to 6.
  validate() rebuilds the teaching fixtures from explicit latent glyph
  descriptions and recomputes the outputs from those latents. A mismatch
  against the two affected uncorrected canonical pairs is expected.
"""

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

import collections
import random

import common

CORNERS = ('tl', 'tr', 'bl', 'br')
MIN_SIDE = 16
MAX_SIDE = 30
SYNTH_LO = 18
REPLAY_MIN_SIDE = 10
MAX_BOX = 5
IDLE_PROB = 0.2


def _corner_pos(name, width, height):
  r = 0 if name[0] == 't' else height - 1
  c = 0 if name[1] == 'l' else width - 1
  return r, c


def _parse(pattern, row, col):
  """Returns (body cells, marker cell) in absolute coordinates."""
  body, markers = [], []
  for r, line in enumerate(pattern):
    for c, ch in enumerate(line):
      if ch == '#':
        body.append((row + r, col + c))
      elif ch == '*':
        markers.append((row + r, col + c))
      elif ch != '.':
        raise ValueError('pattern characters must be #, * or .')
  if len(markers) != 1 or not body:
    raise ValueError('pattern needs body cells and exactly one * marker')
  return body, markers[0]


def _random_pattern(h, w):
  """Random glyph pattern of exact size h x w with one marker '*'."""
  for _ in range(200):
    sym = random.choice(['none', 'h', 'v', 'hv', 'hv', 'h', 'v'])
    p = random.uniform(0.25, 0.55)
    cells = set()
    for r in range(h):
      for c in range(w):
        if random.random() < p:
          cells.add((r, c))
    if sym in ('h', 'hv'):
      cells |= {(r, w - 1 - c) for r, c in cells}
    if sym in ('v', 'hv'):
      cells |= {(h - 1 - r, c) for r, c in cells}
    if random.random() < 0.5:
      marker = (h // 2, w // 2)
    else:
      marker = (random.randrange(h), random.randrange(w))
    cells.discard(marker)
    allc = cells | {marker}
    rows = [r for r, _ in allc]
    cols = [c for _, c in allc]
    if min(rows) != 0 or max(rows) != h - 1:
      continue
    if min(cols) != 0 or max(cols) != w - 1:
      continue
    if len(cells) < 3 or len(cells) > h * w - 2:
      continue
    lines = []
    for r in range(h):
      line = ''
      for c in range(w):
        if (r, c) == marker:
          line += '*'
        elif (r, c) in cells:
          line += '#'
        else:
          line += '.'
      lines.append(line)
    return lines
  return None


def _window(body, width, height):
  """Inclusive window of cells that one 5x5 box could share with the body."""
  y0 = min(r for r, _ in body)
  y1 = max(r for r, _ in body)
  x0 = min(c for _, c in body)
  x1 = max(c for _, c in body)
  return (max(0, y1 - 4), min(height, y0 + 5) - 1,
          max(0, x1 - 4), min(width, x0 + 5) - 1)


def _in_window(win, cell):
  return win[0] <= cell[0] <= win[1] and win[2] <= cell[1] <= win[3]


def _boxes_near(a, b, margin):
  return (a[0] <= b[1] + margin and b[0] - margin <= a[1] and
          a[2] <= b[3] + margin and b[2] - margin <= a[3])


def _check_corners(corners, bg):
  if not isinstance(corners, dict) or not corners:
    raise ValueError('corners must be a non-empty dict')
  for name, color in corners.items():
    if name not in CORNERS:
      raise ValueError('unknown corner name %r' % (name,))
    if not isinstance(color, int) or not 0 <= color <= 9:
      raise ValueError('corner colour out of range')
  if len(set(corners.values())) != len(corners):
    raise ValueError('corner colours must be distinct')
  if bg is not None and bg in corners.values():
    raise ValueError('background colour collides with a corner colour')


def _render(width, height, bg, corners, glyphs):
  """Validates a latent scene and builds its input and output grids."""
  for side in (width, height):
    if not isinstance(side, int) or not REPLAY_MIN_SIDE <= side <= MAX_SIDE:
      raise ValueError('grid side must be in %d..%d' %
                       (REPLAY_MIN_SIDE, MAX_SIDE))
  if not isinstance(bg, int) or not 0 <= bg <= 9:
    raise ValueError('bg out of range')
  _check_corners(corners, bg)
  if not glyphs:
    raise ValueError('at least one glyph is required')
  grid = common.grid(width, height, bg)
  all_corners = set(_corner_pos(n, width, height) for n in CORNERS)
  corner_of = {}
  corner_cells = set()
  for name, color in corners.items():
    r, c = _corner_pos(name, width, height)
    grid[r][c] = color
    corner_of[color] = name
    corner_cells.add((r, c))
  parsed = []
  used = set()
  for b, m, row, col, pattern in glyphs:
    if not isinstance(b, int) or not 0 <= b <= 9:
      raise ValueError('body colour out of range')
    if b == bg or b in corner_of or any(b == p[0] for p in parsed):
      raise ValueError('body colours must be distinct, non-background and '
                       'not corner colours')
    if m not in corner_of:
      raise ValueError('marker colour must be a corner colour')
    if (not pattern or len(pattern) > MAX_BOX or
        any(len(line) != len(pattern[0]) for line in pattern) or
        not 0 < len(pattern[0]) <= MAX_BOX):
      raise ValueError('pattern must be a rectangle of at most 5x5')
    body, marker = _parse(pattern, row, col)
    for cell in body + [marker]:
      if not (0 <= cell[0] < height and 0 <= cell[1] < width):
        raise ValueError('glyph out of bounds')
      if cell in all_corners:
        raise ValueError('glyph cell on a grid corner')
      if cell in used:
        raise ValueError('glyphs overlap')
      used.add(cell)
    for r, c in body:
      grid[r][c] = b
    grid[marker[0]][marker[1]] = m
    parsed.append((b, m, body, marker))
  # Marker-search invariant: each body window holds exactly its own marker.
  markers = [p[3] for p in parsed]
  for b, m, body, marker in parsed:
    win = _window(body, width, height)
    if [mk for mk in markers if _in_window(win, mk)] != [marker]:
      raise ValueError('glyph %d window must hold exactly its own marker' % b)
  counts = collections.Counter(v for line in grid for v in line)
  if any(v != bg and k >= counts[bg] for v, k in counts.items()):
    raise ValueError('background must be the most frequent colour')
  out = [list(line) for line in grid]
  # Swap colours inside each glyph.
  for b, m, body, marker in parsed:
    for r, c in body:
      out[r][c] = m
    out[marker[0]][marker[1]] = b
  # Stamp silhouettes flush into the named corners, in body-colour order.
  for b, m, body, marker in sorted(parsed):
    allc = body + [marker]
    y0 = min(r for r, _ in allc)
    y1 = max(r for r, _ in allc)
    x0 = min(c for _, c in allc)
    x1 = max(c for _, c in allc)
    name = corner_of[m]
    oy = 0 if name[0] == 't' else height - (y1 - y0 + 1)
    ox = 0 if name[1] == 'l' else width - (x1 - x0 + 1)
    for r, c in allc:
      p = (oy + r - y0, ox + c - x0)
      if p not in corner_cells:
        out[p[0]][p[1]] = m
  return {'input': grid, 'output': out}


def _place(width, height, blocks, placed, h, w):
  """Finds a legal slot for one new random h x w glyph, or returns None."""
  pattern = _random_pattern(h, w)
  if pattern is None:
    return None
  positions = [(r, c) for r in range(1, height - h)
               for c in range(1, width - w)]
  random.shuffle(positions)
  for row, col in positions:
    box = (row, row + h - 1, col, col + w - 1)
    if any(_boxes_near(box, bl, 0) for bl in blocks):
      continue
    if any(_boxes_near(box, pb, 1) for pb, _, _ in placed):
      continue
    body, marker = _parse(pattern, row, col)
    win = _window(body, width, height)
    if not _in_window(win, marker):
      continue
    if any(_in_window(win, pm) or _in_window(pw, marker)
           for _, pm, pw in placed):
      continue
    return pattern, row, col, box, marker, win
  return None


def _sample_scene(width, height, bg, corners, n, idle):
  """One attempt at a random glyph layout; returns None on failure."""
  names = list(corners.keys())
  random.shuffle(names)
  active = names[idle:]
  avail = [c for c in range(10) if c != bg and c not in corners.values()]
  targets = active + [random.choice(active) for _ in range(n - len(active))]
  random.shuffle(targets)
  body_colors = random.sample(avail, n)
  # Stamp areas of every marked corner (5x5 stamp plus a one-cell margin).
  blocks = []
  for name in names:
    r0 = 0 if name[0] == 't' else height - 6
    c0 = 0 if name[1] == 'l' else width - 6
    blocks.append((r0, r0 + 5, c0, c0 + 5))
  placed = []
  glyphs = []
  for b, target in zip(body_colors, targets):
    h = random.choice([5, 5, 5, 5, 4, 3])
    w = random.choice([5, 5, 5, 5, 4, 3])
    result = None
    for size in [(h, w), (min(h, 4), min(w, 4)), (3, 3)]:
      result = _place(width, height, blocks, placed, size[0], size[1])
      if result is not None:
        break
    if result is None:
      return None
    pattern, row, col, box, marker, win = result
    placed.append((box, marker, win))
    glyphs.append((b, corners[target], row, col, pattern))
  return glyphs


def _sample_size(width, height):
  if width is None and height is None and random.random() < 0.5:
    return 30, 30
  w = width if width is not None else random.randint(SYNTH_LO, MAX_SIDE)
  h = height if height is not None else random.randint(SYNTH_LO, MAX_SIDE)
  return w, h


def _default_count(width, height, used, n_avail):
  lo = min(max(used, 2), n_avail)
  hi = max(lo, min(n_avail, 6, (width * height) // 110))
  return random.randint(lo, hi)


def _k_options(n, idle):
  """Weighted corner counts compatible with glyph count n and idle count."""
  opts = []
  for k in (1, 2, 2, 3, 3, 4):
    if n is not None and n + k > 9:
      continue
    if idle is not None and (idle > k - 1 or
                             (n is not None and k - idle > n)):
      continue
    opts.append(k)
  return opts


def _choose_idle(k, n, idle_corners):
  """Number of legend corners that receive no glyph."""
  lo = 0 if n is None else max(0, k - n)
  if idle_corners is not None:
    if lo <= idle_corners <= k - 1:
      return idle_corners
    return None
  if lo > k - 1:
    return None
  idle = lo
  if idle < k - 1 and random.random() < IDLE_PROB:
    idle += 1
  return idle


def generate(width=None, height=None, bg=None, corners=None, num_glyphs=None,
             idle_corners=None, glyphs=None):
  """Generates one input/output pair.

  Args:
    width: grid width. If None, it is sampled. When both sides are None, the
      grid is 30x30 half the time; otherwise each side is uniform in 18..30.
      Explicit values must lie in 16..30, or in 10..30 in replay mode.
    height: grid height. Sampled in the same way as width.
    bg: background colour 0..9. Sampled if None. It never equals a corner
      colour.
    corners: dict mapping a corner name ('tl', 'tr', 'bl', 'br') to its
      corner colour. Sampled if None (1-4 corners).
    num_glyphs: number of glyphs, 1..9-len(corners). It must be at least the
      number of non-idle corners. If it is smaller than len(corners) and
      idle_corners is None, the surplus corners become idle. Sampled if None.
    idle_corners: number of legend corners that receive no glyph (0..k-1).
      If None, it is 0 most of the time and occasionally 1 (a distractor).
      In replay mode it is optional and checked against the glyphs.
    glyphs: explicit list of (body_colour, marker_colour, top_row, left_col,
      pattern) for replay. pattern is a list of equal-length strings of at
      most 5x5: '#' body, '*' marker, '.' empty. Replay mode also needs
      width, height, bg and corners, and the whole scene is validated.
  """
  if idle_corners is not None and not (isinstance(idle_corners, int) and
                                       0 <= idle_corners <= 3):
    raise ValueError('idle_corners must be an integer in 0..3')
  if glyphs is not None:
    if width is None or height is None or bg is None or corners is None:
      raise ValueError('glyphs replay requires width, height, bg and corners')
    if num_glyphs is not None and num_glyphs != len(glyphs):
      raise ValueError('num_glyphs disagrees with len(glyphs)')
    if idle_corners is not None:
      targeted = set(g[1] for g in glyphs) & set(corners.values())
      if idle_corners != len(corners) - len(targeted):
        raise ValueError('idle_corners disagrees with the replayed glyphs')
    return _render(width, height, bg, corners, glyphs)
  for side in (width, height):
    if side is not None and not (isinstance(side, int) and
                                 MIN_SIDE <= side <= MAX_SIDE):
      raise ValueError('grid side must be in %d..%d' % (MIN_SIDE, MAX_SIDE))
  if bg is not None and not (isinstance(bg, int) and 0 <= bg <= 9):
    raise ValueError('bg out of range')
  if num_glyphs is not None:
    if not isinstance(num_glyphs, int) or not 1 <= num_glyphs <= 8:
      raise ValueError('num_glyphs must be an integer in 1..8')
  if corners is not None:
    _check_corners(corners, bg)
    k = len(corners)
    if num_glyphs is not None and num_glyphs > 9 - k:
      raise ValueError('num_glyphs incompatible with the given corners')
    if idle_corners is not None:
      if idle_corners > k - 1:
        raise ValueError('at least one corner must receive a glyph')
      if num_glyphs is not None and k - idle_corners > num_glyphs:
        raise ValueError('too few glyphs for the non-idle corners')
  elif not _k_options(num_glyphs, idle_corners):
    raise ValueError('num_glyphs and idle_corners are incompatible')
  for _ in range(200):
    w, h = _sample_size(width, height)
    if corners is not None:
      cs = dict(corners)
      b = bg if bg is not None else random.choice(
          [c for c in range(10) if c not in cs.values()])
    else:
      b = bg if bg is not None else random.randrange(10)
      k = random.choice(_k_options(num_glyphs, idle_corners))
      names = random.sample(CORNERS, k)
      cols = random.sample([c for c in range(10) if c != b], k)
      cs = dict(zip(names, cols))
    idle = _choose_idle(len(cs), num_glyphs, idle_corners)
    if idle is None:
      raise ValueError('idle_corners incompatible with the scene')
    n_avail = 9 - len(cs)
    if num_glyphs is not None:
      n = num_glyphs
    else:
      n = _default_count(w, h, len(cs) - idle, n_avail)
    gl = _sample_scene(w, h, b, cs, n, idle)
    if gl is not None:
      return _render(w, h, b, cs, gl)
  raise RuntimeError('could not construct a scene for these parameters')


def validate():
  """Rebuilds the curated (teaching-copy) fixtures from latent parameters."""
  train = [
      generate(width=30, height=30, bg=2, corners={'tl': 9, 'tr': 5, 'br': 1},
               glyphs=[
                   (4, 5, 3, 11, ['....#', '....#', '....#', '...*#',
                                  '#####']),
                   (0, 5, 11, 14, ['..###', '...*#', '..#.#', '.#...',
                                   '#....']),
                   (3, 9, 19, 3, ['#.#..', '###..', '..*..', '..###',
                                  '..#.#']),
                   (6, 9, 20, 20, ['..#..', '##*##', '..#..', '..#..',
                                   '..#..']),
                   (8, 1, 22, 12, ['..#..', '..*..', '.#.#.', '.#.#.',
                                   '#...#']),
               ]),
      generate(width=30, height=30, bg=4, corners={'tl': 6, 'tr': 3},
               glyphs=[
                   (1, 3, 4, 5, ['#...#', '...#.', '...*#', '...#.',
                                 '#...#']),
                   (2, 3, 4, 19, ['..#..', '.....', '##*##', '.....',
                                  '..#..']),
                   (5, 3, 14, 14, ['#....', '#....', '*####', '#....',
                                   '#....']),
                   (9, 6, 21, 20, ['#..#*', '....#', '.....', '.....',
                                   '#...#']),
                   (8, 6, 23, 4, ['#....', '.#...', '#.#..', '.*.#.',
                                  '#.#.#']),
               ]),
      generate(width=30, height=30, bg=8, corners={'tr': 4, 'bl': 7},
               glyphs=[
                   (2, 4, 3, 4, ['#...#', '.#.#.', '..*..', '.#.#.',
                                 '#...#']),
                   (3, 4, 6, 17, ['#####', '#...#', '##*##', '..#..',
                                  '..#..']),
                   (5, 7, 17, 18, ['..#..', '.#.#.', '#.*.#', '..#..',
                                   '..#..']),
                   (6, 7, 18, 4, ['#####', '#....', '##*..', '#....',
                                  '#####']),
               ]),
  ]
  test = [
      generate(width=30, height=30, bg=0, corners={'tl': 7, 'tr': 8},
               glyphs=[
                   (2, 7, 6, 7, ['#####', '#...#', '*...#', '#...#',
                                 '#####']),
                   (5, 8, 7, 21, ['#.#.#', '.#.#.', '#.#.#', '.*.#.',
                                  '#.#.#']),
                   (3, 7, 16, 14, ['..#..', '..#..', '*####', '..#..',
                                   '..#..']),
                   (4, 7, 17, 4, ['#...#', '.#.*.', '..#..', '.#.#.',
                                  '#...#']),
                   (6, 8, 23, 19, ['#####', '.....', '..*..', '.....',
                                   '#####']),
               ]),
      generate(width=30, height=30, bg=5, corners={'tl': 0, 'tr': 2, 'br': 9},
               glyphs=[
                   (4, 2, 3, 17, ['#.#.#', '#.#.#', '#.*.#', '#.#.#',
                                  '#.#.#']),
                   (3, 0, 4, 5, ['#....', '.#...', '..*..', '...#.',
                                 '....#']),
                   (6, 2, 11, 11, ['#####', '.....', '####*', '.....',
                                   '#####']),
                   (8, 9, 17, 19, ['..###', '..#..', '..##.', '.*...',
                                   '#.#..']),
                   (7, 9, 20, 4, ['..#..', '.....', '..#..', '.*.#.',
                                  '#..##']),
               ]),
  ]
  return {'train': train, 'test': test}
