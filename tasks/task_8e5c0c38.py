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

"""ARC-GEN style generator for task 8e5c0c38.

Rule: treat all cells of each non-background colour as one group, even when
the colour is split into several pieces. The group is nearly left-right
symmetric about a vertical axis, but some stray cells break the symmetry. The
axis may lie on a column or halfway between two columns. The best axis is the
vertical axis under which the most cells of that colour have a mirror partner
of the same colour. If several axes tie, the leftmost best axis is chosen. The output erases
every cell that has no partner under that axis. Only vertical axes count. A top-bottom symmetry is never used,
even when it would keep more cells (train 2, colours 8 and 4).

Scope: all original pairs are 22x22. If both sides are left unspecified,
22x22 is used half the time. Otherwise each side is drawn on its own from
14..30, which is a synthetic extension. Explicit sizes 8..30 are accepted.
The background may be any colour 0..9, and it is always strictly the most
frequent colour.

Shapes: a random scene has 2-4 shapes in distinct colours, chosen by grid
area. Callers may request 1-4. Each shape has a random core that is
left-right symmetric, with a box 3-13 wide and 3-10 tall. About a quarter of
the cores are split. A split core is a connected piece plus its mirror with
an empty middle, so the colour has two pieces, as in test 2. A share of the
cores, set by distractor_rate (default 0.25), are also top-bottom symmetric.
Their stray cells mostly come in top-bottom mirror pairs, with an occasional
unpaired single. A horizontal axis then keeps all or nearly all cells, yet
the vertical-only rule must still erase the strays.

Strays in the unique-axis branch: each shape gets 0..min(12, max(4, |core| // 4)) stray cells. The
cap is exact, including paired strays. Strays are grown one at a time. Each
one touches the core or an earlier stray, except that the second cell of a
top-bottom pair is the reflection of the first. Strays can reach up to 2
cells outside the core box, as in test 1 colour 6. A stray is never on the
axis column and never has a mirror partner. Every scene has at least one
stray. These ordinary shapes retain a strictly unique best vertical axis. The boxes of different shapes are separated by at
least one empty row or column. Horizontal and diagonal mirror rules are
deliberately not used.

Tied-axis branch: tie_rate (default 0.2) selects a synthetic family with two
symmetric core cells plus one stray per occupied row. The core reflects about
axis A, while one core cell and the stray reflect about a second axis B>A.
Row positions vary, and all other vertical axes score no higher. Thus the
intended core is selected by the same leftmost tie-break needed by canonical
test 1 colour 3. This branch has 3..10 stray cells (one per row) and may have
more than two connected pieces; it is a separate documented shape vocabulary.
The top-bottom distractor control applies to both branches. Setting tie_rate=0
recovers strictly unique-axis random scenes; tie_rate=1 forces tied shapes.

All four canonical fixtures use explicit core/extras latents, including the
original tied case. The legacy input_rows/axes path remains available for
explicit fixture inspection, but validate() and random generation never call
it. Neither outputs nor intended cores are inferred from rendered random inputs.

"""

import random

import common

_RADIUS = 2
_MAX_CORE_W = 13
_MAX_CORE_H = 10


def _is_int(v):
  """True for a genuine integer (bool is rejected)."""
  return isinstance(v, int) and not isinstance(v, bool)


def _neighbours(c):
  """Yield the eight neighbours of cell c = (y, x)."""
  y, x = c
  for dy in (-1, 0, 1):
    for dx in (-1, 0, 1):
      if dy or dx:
        yield (y + dy, x + dx)


def _connected(cells):
  """True if the cell set is a single 8-connected component."""
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    for n in _neighbours(stack.pop()):
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _make_core(w, h, split=False, vsym=False):
  """Random left-right symmetric shape whose bounding box is w x h.

  Args:
    w: box width (>= 5 when split).
    h: box height.
    split: if True, the middle column(s) stay empty. The shape is then a
      connected left piece plus its mirror image.
    vsym: if True, the shape is also top-bottom symmetric. This is the
      horizontal-axis distractor.
  """
  half = (w + 1) // 2
  limit = half
  if split:
    limit = half - random.randint(1, half - 2)
  rows = range((h + 1) // 2) if vsym else range(h)
  for _ in range(100):
    p = random.uniform(0.4, 0.75)
    cells = set()
    for y in rows:
      for x in range(limit):
        if random.random() < p:
          for yy in ({y, h - 1 - y} if vsym else (y,)):
            cells.add((yy, x))
            cells.add((yy, w - 1 - x))
    if len(cells) < 5 or len(cells) >= w * h:
      continue
    if {y for y, _ in cells} != set(range(h)):
      continue
    if not any(x == 0 for _, x in cells):
      continue
    if split:
      if not _connected({c for c in cells if c[1] < limit}):
        continue
    elif not _connected(cells):
      continue
    return cells
  return None


def _make_strays(core, w, h, k, paired):
  """Grow at most k stray cells next to the core or earlier strays.

  No stray lies on the axis column x = (w - 1) / 2. No stray has a mirror
  partner in the core or among the strays. If paired is True, about 80% of
  additions are top-bottom pairs (y, x) and (h - 1 - y, x). The rest are
  singles, which make the horizontal axis nearly perfect rather than
  perfect. Strays stay within _RADIUS cells of the core box. The total never
  exceeds k.
  """
  s = w - 1
  strays = []
  taken = set()

  def ok(c):
    y, x = c
    if not (-_RADIUS <= y < h + _RADIUS and -_RADIUS <= x < w + _RADIUS):
      return False
    if c in core or c in taken or 2 * x == s:
      return False
    m = (y, s - x)
    return m not in core and m not in taken

  for _ in range(6 * k + 6):
    if len(strays) >= k:
      break
    occupied = core | taken
    cand = sorted({n for c in occupied for n in _neighbours(c) if ok(n)})
    if not cand:
      break
    c = random.choice(cand)
    group = [c]
    if paired and random.random() < 0.8:
      c2 = (h - 1 - c[0], c[1])
      if c2 != c:
        if not ok(c2) or len(strays) + 2 > k:
          continue
        group.append(c2)
    for g in group:
      strays.append(g)
      taken.add(g)
  return strays


def _vertical_scores(cells):
  """Map each doubled vertical axis t (x -> t - x) to the cells it keeps."""
  xs = [x for _, x in cells]
  return {t: sum(1 for (y, x) in cells if (y, t - x) in cells)
          for t in range(2 * min(xs), 2 * max(xs) + 1)}


def _axis_unique(cells, s):
  """True if vertical axis s keeps strictly more cells than any other."""
  scores = _vertical_scores(cells)
  if s not in scores:
    return False
  return all(v < scores[s] for t, v in scores.items() if t != s)


def _axis_leftmost(cells, s):
  """True if s is the leftmost maximizing vertical axis."""
  scores = _vertical_scores(cells)
  return s in scores and all(v < scores[s] if t < s else v <= scores[s]
                            for t, v in scores.items())


def _component_count(cells):
  """Number of eight-connected pieces."""
  todo, n = set(cells), 0
  while todo:
    stack = [todo.pop()]
    n += 1
    while stack:
      for p in _neighbours(stack.pop()):
        if p in todo:
          todo.remove(p)
          stack.append(p)
  return n


def _make_tied_core(w, h, paired):
  """Construct two equal best axes A<B; output is the latent core at A.

  Every row contains a, A-a and B-a. Excluding equally spaced triples
  ensures no axis keeps all three. A is the smallest sum of two distinct
  coordinates in every row, so no earlier axis can match its two-per-row
  score. B matches that same score, independently of row variation.
  """
  a_axis = w - 1
  delta = random.choice([d for d in range(1, 5) if d != a_axis])
  b_axis = a_axis + delta
  allowed = [a for a in range((a_axis + 1) // 2)
             if a_axis - 2 * a != delta]
  starts = [random.choice(allowed) for _ in range(h)]
  starts[0] = 0
  if paired:
    for y in range((h + 1) // 2):
      starts[h - 1 - y] = starts[y]
  core, extras = set(), []
  for y, a in enumerate(starts):
    core.update(((y, a), (y, a_axis - a)))
    extras.append((y, b_axis - a))
  return core, extras


def _near(a, b):
  """True if boxes (y0, x0, y1, x1), end-exclusive, lack a one-cell gap."""
  return (a[0] < b[2] + 1 and b[0] < a[2] + 1 and
          a[1] < b[3] + 1 and b[1] < a[3] + 1)


def _sample_shape(colour, width, height, boxes, force_extra,
                  distractor_rate, tied=False):
  """Sample a core, stray cells and a free position. None on failure."""
  for _ in range(30):
    w = random.randint(3, min(_MAX_CORE_W, width - 2))
    h = random.randint(3, min(_MAX_CORE_H, height - 2))
    vsym = random.random() < distractor_rate
    if tied:
      core, extras = _make_tied_core(w, h, vsym)
    else:
      split = w >= 5 and random.random() < 0.25
      core = _make_core(w, h, split, vsym)
      if core is None:
        continue
      if force_extra or random.random() < 0.85:
        k = random.randint(1, min(12, max(4, len(core) // 4)))
      else:
        k = 0
      extras = _make_strays(core, w, h, k, vsym) if k else []
      if split and _component_count(core | set(extras)) != 2:
        continue
    if force_extra and not extras:
      continue
    cells = core | set(extras)
    if not (_axis_leftmost(cells, w - 1) if tied else
            _axis_unique(cells, w - 1)):
      continue
    ys = [y for y, _ in cells]
    xs = [x for _, x in cells]
    ymin, ymax, xmin, xmax = min(ys), max(ys), min(xs), max(xs)
    if ymax - ymin + 1 > height or xmax - xmin + 1 > width:
      continue
    for _ in range(20):
      top = random.randint(-ymin, height - 1 - ymax)
      left = random.randint(-xmin, width - 1 - xmax)
      box = (top + ymin, left + xmin, top + ymax + 1, left + xmax + 1)
      if any(_near(box, b) for b in boxes):
        continue
      boxes.append(box)
      return {'colour': colour, 'top': top, 'left': left, 'w': w,
              'core': sorted(core), 'extras': extras}
  return None


def _cell_counts(shapes):
  """Number of painted cells per shape."""
  return [len({tuple(p) for p in s['core']} | {tuple(p) for p in s['extras']})
          for s in shapes]


def _counts_ok(width, height, shapes):
  """True if the background strictly outnumbers every shape colour."""
  counts = _cell_counts(shapes)
  return width * height - sum(counts) > max(counts)


def _paint(width, height, background, shapes):
  """Draw latent shapes; the output keeps only the symmetric cores."""
  if not shapes:
    raise ValueError('at least one shape is required')
  grid = common.grid(width, height, background)
  out = common.grid(width, height, background)
  used = set()
  seen_colours = set()
  any_stray = False
  for shape in shapes:
    for key in ('colour', 'top', 'left', 'w', 'core', 'extras'):
      if key not in shape:
        raise ValueError('shape is missing key %r' % key)
    c = shape['colour']
    top, left, w = shape['top'], shape['left'], shape['w']
    if not all(_is_int(v) for v in (c, top, left, w)):
      raise ValueError('colour, top, left and w must be integers')
    if w < 1:
      raise ValueError('w must be positive')
    for name in ('core', 'extras'):
      if (not isinstance(shape[name], (list, tuple)) or
          any(not isinstance(p, (list, tuple)) or len(p) != 2 or
              not all(_is_int(v) for v in p) for p in shape[name])):
        raise ValueError('cells must be integer (y, x) pairs')
      if len({tuple(p) for p in shape[name]}) != len(shape[name]):
        raise ValueError('duplicate cells in ' + name)
    core = {tuple(p) for p in shape['core']}
    extras = {tuple(p) for p in shape['extras']}
    if any(len(p) != 2 or not all(_is_int(v) for v in p)
           for p in core | extras):
      raise ValueError('cells must be integer (y, x) pairs')
    s = w - 1
    if not 0 <= c <= 9 or c == background or c in seen_colours:
      raise ValueError('shape colours must be distinct and not background')
    seen_colours.add(c)
    if not core or any((y, s - x) not in core for (y, x) in core):
      raise ValueError('core must be non-empty and symmetric about w - 1')
    if extras & core or any((y, s - x) in core or (y, s - x) in extras
                            for (y, x) in extras):
      raise ValueError('every stray cell must lack a mirror partner')
    if not _axis_leftmost(core | extras, s):
      raise ValueError('intended axis is not the leftmost best axis')
    if extras:
      any_stray = True
    for (y, x) in core | extras:
      yy, xx = top + y, left + x
      if not (0 <= yy < height and 0 <= xx < width) or (yy, xx) in used:
        raise ValueError('shape cells out of bounds or overlapping')
      used.add((yy, xx))
      grid[yy][xx] = c
      if (y, x) in core:
        out[yy][xx] = c
  if not any_stray:
    raise ValueError('scene needs at least one stray cell')
  if not _counts_ok(width, height, shapes):
    raise ValueError('background must be strictly the most frequent colour')
  return {'input': grid, 'output': out}


def _replay(input_rows, axes, background):
  """Build a pair from an explicit input picture plus per-colour axes.

  Each supplied axis must be the leftmost best vertical axis of its colour.
  The leftmost rule settles the genuine tie in test 1 colour 3. The output
  erases cells whose mirror under that axis is not the same colour.
  """
  if (not isinstance(input_rows, (list, tuple)) or not input_rows or
      any(not isinstance(row, str) or not row or
          any(ch not in '0123456789' for ch in row) for row in input_rows)):
    raise ValueError('input_rows must be non-empty digit strings')
  if not isinstance(axes, dict):
    raise ValueError('axes must be a colour-to-axis dictionary')
  normalized = {}
  for c, axis in axes.items():
    if not (_is_int(c) and 0 <= c <= 9 or
            isinstance(c, str) and len(c) == 1 and c in '0123456789'):
      raise ValueError('axis colour keys must be integers or digit strings')
    c = int(c)
    if c in normalized:
      raise ValueError('duplicate axis colour')
    normalized[c] = axis
  axes = normalized
  grid = [[int(ch) for ch in row] for row in input_rows]
  height, width = len(grid), len(grid[0])
  if any(len(r) != width for r in grid):
    raise ValueError('input_rows must be rectangular')
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError('replay grid must be 1..30 per side')
  out = [row[:] for row in grid]
  groups = {}
  for y in range(height):
    for x in range(width):
      c = grid[y][x]
      if c != background:
        groups.setdefault(c, set()).add((y, x))
  if not groups:
    raise ValueError('replay picture has no shapes')
  bg_count = width * height - sum(len(v) for v in groups.values())
  if bg_count <= max(len(v) for v in groups.values()):
    raise ValueError('background must be strictly the most frequent colour')
  if set(axes) != set(groups):
    raise ValueError('axes must name exactly the shape colours')
  for c, cells in groups.items():
    if not _is_int(axes[c]):
      raise ValueError('axis for colour %d must be an integer' % c)
    scores = _vertical_scores(cells)
    best = max(scores.values())
    first = min(t for t, v in scores.items() if v == best)
    if axes[c] != first:
      raise ValueError('axis for colour %d is not the leftmost best axis' % c)
    for (y, x) in cells:
      mx = axes[c] - x
      if not (0 <= mx < width and grid[y][mx] == c):
        out[y][x] = background
  if out == grid:
    raise ValueError('replay pair would be an identity')
  return {'input': grid, 'output': out}


def generate(width=None, height=None, background=None, num_shapes=None,
             colours=None, shapes=None, distractor_rate=None,
             input_rows=None, axes=None, tie_rate=None):
  """Generate one input/output pair.

  Args:
    width: grid width, an int in 8..30. If both width and height are None,
      the grid is 22x22 half the time and otherwise each side is drawn from
      14..30. A single missing side is 22 or 14..30 with equal odds.
    height: grid height, an int in 8..30.
    background: background colour 0..9. If None, it is random and differs
      from every shape colour.
    num_shapes: number of colours/shapes, 1..4. If None, it is a random 2-4
      chosen by grid area.
    colours: optional list of distinct shape colours. Its length must agree
      with num_shapes when both are given.
    shapes: optional explicit latent shapes, an expert mode. Each is a dict
      with keys 'colour', 'top', 'left', 'w', 'core' and 'extras'. 'core'
      holds local (y, x) cells that are symmetric about x -> w - 1 - x.
      'extras' holds local stray cells. Grid position is
      (top + y, left + x). The rule-level invariants are enforced: the leftmost
      best axis (ties allowed), mirror-free strays, at least one stray, no overlap, and a
      majority background. The cosmetic random-scene limits are not
      enforced: up to 9 colours, no box gap, no stray connectivity or
      radius. This mode excludes num_shapes, colours, distractor_rate and tie_rate.
    distractor_rate: chance (0..1, default 0.25) that a random core is also
      top-bottom symmetric, with mostly top-bottom paired strays.
    tie_rate: chance (0..1, default 0.2) of a tied-axis synthetic shape.
      Each shape retains its selected branch across placement retries.
    input_rows: optional fixture replay, given as a list of digit strings.
      It needs `axes` and `background`, and it excludes every other
      argument.
    axes: dict mapping colour -> doubled axis s (mirror x -> s - x). It is
      used only with input_rows.
  """
  if background is not None and (not _is_int(background) or
                                 not 0 <= background <= 9):
    raise ValueError('background must be an int colour in 0..9')
  if input_rows is not None:
    if axes is None or background is None:
      raise ValueError('input_rows replay needs axes and background')
    if any(v is not None for v in (width, height, num_shapes, colours,
                                   shapes, distractor_rate, tie_rate)):
      raise ValueError('input_rows replay excludes other parameters')
    return _replay(input_rows, axes, background)
  if axes is not None:
    raise ValueError('axes is only used with input_rows')
  for name, v in (('width', width), ('height', height),
                  ('num_shapes', num_shapes)):
    if v is not None and not _is_int(v):
      raise ValueError('%s must be an int' % name)
  if width is None and height is None:
    if random.random() < 0.5:
      width, height = 22, 22
    else:
      width, height = random.randint(14, 30), random.randint(14, 30)
  if width is None:
    width = 22 if random.random() < 0.5 else random.randint(14, 30)
  if height is None:
    height = 22 if random.random() < 0.5 else random.randint(14, 30)
  if not (8 <= width <= 30 and 8 <= height <= 30):
    raise ValueError('width and height must be in 8..30')
  if shapes is not None:
    if (num_shapes is not None or colours is not None or
        distractor_rate is not None or tie_rate is not None):
      raise ValueError('shapes excludes num_shapes, colours, '
                       'distractor_rate and tie_rate')
    if (not isinstance(shapes, (list, tuple)) or not shapes or
        any(not isinstance(s, dict) for s in shapes)):
      raise ValueError('shapes must be a non-empty list of dictionaries')
    if background is None:
      if any(not _is_int(s.get('colour')) for s in shapes):
        raise ValueError('each shape needs an integer colour')
      used = {s['colour'] for s in shapes}
      free = [c for c in range(10) if c not in used]
      if not free:
        raise ValueError('no free background colour')
      background = random.choice(free)
    return _paint(width, height, background, shapes)
  if distractor_rate is None:
    distractor_rate = 0.25
  if (isinstance(distractor_rate, bool) or
      not isinstance(distractor_rate, (int, float)) or
      not 0 <= distractor_rate <= 1):
    raise ValueError('distractor_rate must be a number in 0..1')
  if tie_rate is None:
    tie_rate = 0.2
  if (isinstance(tie_rate, bool) or not isinstance(tie_rate, (int, float)) or
      not 0 <= tie_rate <= 1):
    raise ValueError('tie_rate must be a number in 0..1')
  if colours is not None:
    if not isinstance(colours, (list, tuple)):
      raise ValueError('colours must be a list or tuple')
    colours = list(colours)
    if any(not _is_int(c) or not 0 <= c <= 9 for c in colours):
      raise ValueError('colours must be int values in 0..9')
    if len(set(colours)) != len(colours):
      raise ValueError('colours must be distinct')
    if num_shapes is not None and num_shapes != len(colours):
      raise ValueError('num_shapes disagrees with len(colours)')
    num_shapes = len(colours)
  if num_shapes is None:
    area = width * height
    max_n = 2 if area < 300 else (3 if area < 600 else 4)
    num_shapes = random.choice([n for n in (2, 3, 3, 4) if n <= max_n])
  if not 1 <= num_shapes <= 4:
    raise ValueError('num_shapes must be in 1..4')
  if background is None:
    banned = set(colours or [])
    background = random.choice([c for c in range(10) if c not in banned])
  if colours is None:
    colours = random.sample([c for c in range(10) if c != background],
                            num_shapes)
  if background in colours:
    raise ValueError('background collides with a shape colour')
  tied_modes = [random.random() < tie_rate for _ in colours]
  for _ in range(100):
    boxes = []
    placed = []
    must = random.randrange(num_shapes)
    for i, colour in enumerate(colours):
      shape = _sample_shape(colour, width, height, boxes, i == must,
                            distractor_rate, tied_modes[i])
      if shape is None:
        break
      placed.append(shape)
    else:
      if _counts_ok(width, height, placed):
        return _paint(width, height, background, placed)
  raise RuntimeError('could not place shapes; use a larger grid or fewer '
                     'shapes')


_CANONICAL_SCENES = {'train': [{'width': 22,
            'height': 22,
            'background': 8,
            'shapes': [{'colour': 1,
                        'top': 4,
                        'left': 4,
                        'w': 9,
                        'core': [(0, 1),
                                 (0, 2),
                                 (0, 3),
                                 (0, 5),
                                 (0, 6),
                                 (0, 7),
                                 (1, 0),
                                 (1, 1),
                                 (1, 7),
                                 (1, 8),
                                 (2, 1),
                                 (2, 7),
                                 (3, 1),
                                 (3, 3),
                                 (3, 4),
                                 (3, 5),
                                 (3, 7),
                                 (4, 1),
                                 (4, 2),
                                 (4, 3),
                                 (4, 5),
                                 (4, 6),
                                 (4, 7),
                                 (5, 2),
                                 (5, 6)],
                        'extras': [(-1, 5), (3, 0), (4, 0)]},
                       {'colour': 2,
                        'top': 14,
                        'left': 9,
                        'w': 9,
                        'core': [(0, 2),
                                 (0, 6),
                                 (1, 0),
                                 (1, 1),
                                 (1, 3),
                                 (1, 4),
                                 (1, 5),
                                 (1, 7),
                                 (1, 8),
                                 (2, 2),
                                 (2, 6)],
                        'extras': [(0, 7), (0, 8), (2, 1)]},
                       {'colour': 6,
                        'top': 5,
                        'left': 16,
                        'w': 3,
                        'core': [(0, 0),
                                 (0, 1),
                                 (0, 2),
                                 (1, 0),
                                 (1, 2),
                                 (2, 0),
                                 (2, 1),
                                 (2, 2)],
                        'extras': [(0, -1)]}]},
           {'width': 22,
            'height': 22,
            'background': 0,
            'shapes': [{'colour': 2,
                        'top': 2,
                        'left': 14,
                        'w': 6,
                        'core': [(0, 1),
                                 (0, 2),
                                 (0, 3),
                                 (0, 4),
                                 (1, 0),
                                 (1, 1),
                                 (1, 4),
                                 (1, 5),
                                 (2, 0),
                                 (2, 1),
                                 (2, 4),
                                 (2, 5),
                                 (3, 1),
                                 (3, 2),
                                 (3, 3),
                                 (3, 4),
                                 (4, 2),
                                 (4, 3)],
                        'extras': [(-1, 1), (1, -1)]},
                       {'colour': 4,
                        'top': 12,
                        'left': 9,
                        'w': 7,
                        'core': [(0, 2),
                                 (0, 3),
                                 (0, 4),
                                 (1, 1),
                                 (1, 2),
                                 (1, 3),
                                 (1, 4),
                                 (1, 5),
                                 (2, 0),
                                 (2, 1),
                                 (2, 5),
                                 (2, 6),
                                 (3, 1),
                                 (3, 2),
                                 (3, 3),
                                 (3, 4),
                                 (3, 5),
                                 (4, 3)],
                        'extras': [(2, -1), (4, 4)]},
                       {'colour': 8,
                        'top': 4,
                        'left': 6,
                        'w': 3,
                        'core': [(0, 1), (1, 0), (1, 2), (2, 0), (2, 2), (3, 1)],
                        'extras': [(1, -1), (2, -1)]}]}],
 'test': [{'width': 22,
           'height': 22,
           'background': 1,
           'shapes': [{'colour': 3,
                       'top': 16,
                       'left': 17,
                       'w': 3,
                       'core': [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)],
                       'extras': [(0, 3), (1, 3)]},
                      {'colour': 4,
                       'top': 17,
                       'left': 1,
                       'w': 11,
                       'core': [(0, 5),
                                (1, 4),
                                (1, 5),
                                (1, 6),
                                (2, 0),
                                (2, 1),
                                (2, 2),
                                (2, 3),
                                (2, 4),
                                (2, 5),
                                (2, 6),
                                (2, 7),
                                (2, 8),
                                (2, 9),
                                (2, 10),
                                (3, 4),
                                (3, 5),
                                (3, 6),
                                (4, 5)],
                       'extras': [(1, 7), (3, 7), (4, 4)]},
                      {'colour': 6,
                       'top': 5,
                       'left': 4,
                       'w': 12,
                       'core': [(0, 1),
                                (0, 2),
                                (0, 3),
                                (0, 4),
                                (0, 7),
                                (0, 8),
                                (0, 9),
                                (0, 10),
                                (1, 2),
                                (1, 9),
                                (2, 2),
                                (2, 9),
                                (3, 0),
                                (3, 1),
                                (3, 2),
                                (3, 9),
                                (3, 10),
                                (3, 11),
                                (4, 0),
                                (4, 1),
                                (4, 2),
                                (4, 4),
                                (4, 5),
                                (4, 6),
                                (4, 7),
                                (4, 9),
                                (4, 10),
                                (4, 11),
                                (5, 2),
                                (5, 3),
                                (5, 4),
                                (5, 7),
                                (5, 8),
                                (5, 9),
                                (6, 3),
                                (6, 8),
                                (7, 3),
                                (7, 4),
                                (7, 5),
                                (7, 6),
                                (7, 7),
                                (7, 8),
                                (8, 2),
                                (8, 3),
                                (8, 8),
                                (8, 9)],
                       'extras': [(0, 6),
                                  (0, 11),
                                  (1, 1),
                                  (3, -1),
                                  (3, 6),
                                  (4, -1),
                                  (5, 10),
                                  (8, 10),
                                  (8, 11),
                                  (9, 8),
                                  (9, 9),
                                  (10, 9)]}]},
          {'width': 22,
           'height': 22,
           'background': 4,
           'shapes': [{'colour': 1,
                       'top': 12,
                       'left': 9,
                       'w': 10,
                       'core': [(0, 1),
                                (0, 2),
                                (0, 3),
                                (0, 6),
                                (0, 7),
                                (0, 8),
                                (1, 1),
                                (1, 3),
                                (1, 4),
                                (1, 5),
                                (1, 6),
                                (1, 8),
                                (2, 0),
                                (2, 1),
                                (2, 8),
                                (2, 9),
                                (3, 1),
                                (3, 8),
                                (4, 1),
                                (4, 2),
                                (4, 3),
                                (4, 4),
                                (4, 5),
                                (4, 6),
                                (4, 7),
                                (4, 8),
                                (5, 4),
                                (5, 5)],
                       'extras': [(-1, 7), (2, -1), (4, 0), (5, 6)]},
                      {'colour': 2,
                       'top': 3,
                       'left': 2,
                       'w': 9,
                       'core': [(0, 0),
                                (0, 1),
                                (0, 2),
                                (0, 6),
                                (0, 7),
                                (0, 8),
                                (1, 0),
                                (1, 3),
                                (1, 4),
                                (1, 5),
                                (1, 8),
                                (2, 0),
                                (2, 1),
                                (2, 7),
                                (2, 8),
                                (3, 1),
                                (3, 3),
                                (3, 4),
                                (3, 5),
                                (3, 7),
                                (4, 1),
                                (4, 2),
                                (4, 3),
                                (4, 5),
                                (4, 6),
                                (4, 7)],
                       'extras': [(-1, 0), (-1, 6), (0, 9), (1, 9), (4, 8), (5, 6)]},
                      {'colour': 3,
                       'top': 4,
                       'left': 15,
                       'w': 5,
                       'core': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (1, 3)],
                       'extras': [(0, 5)]}]}]}

def validate():
  """Reconstruct original pairs from explicit symmetric cores and strays."""
  return {split: [generate(**scene) for scene in scenes]
          for split, scenes in _CANONICAL_SCENES.items()}
