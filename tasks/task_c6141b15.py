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

"""ARC-GEN style generator for ARC task c6141b15.

Rule: the background is colour 7 and the input has two foreground colours.
  - One colour forms a single straight segment (horizontal, vertical or
    diagonal). It is one 8-connected component.
  - The other colour forms two or more identical small shapes.
In the output both objects are erased. Every pair of shape centres that
shares a row, column or diagonal is joined by an inclusive line in the
segment colour. A copy of the small shape, anchored at its bounding-box
centre, is stamped in the shape colour on each of the two endpoints of the
old segment.

Scope (attested by the fixtures):
  - 11x11 and 16x16 grids, background 7.
  - Dot, plus, X and I-beam templates.
  - 2 or 3 centres, all pairwise aligned.
  - Segments that are horizontal, vertical or diagonal.

Synthetic extensions (consistent with the rule, but not attested):
  - Default grid sides sampled independently from 10..30, non-square.
  - Explicit sizes 1..30, including degenerate one-row scenes.
  - Extra templates: horizontal I-beam, ring, diamond, and random
    8-connected, non-collinear, bbox-centred templates.
  - 'square' (4 centres) and 'apex' layouts.
  - 'bent' layouts with an unaligned distractor pair that is not drawn.
  - 'grown' clusters of 2..5 centres.

Layouts:
  - pair, right, square, apex: enumerated exactly, at every spacing whose
    geometry is valid for the actual template, including tight spacings.
    Feasibility prechecks use the same enumeration, so halo crossings
    (e.g. the hypotenuse of a 7x7 X right triangle) are detected up front.
  - bent, grown: sampled with conservative bounding-box spacing.

Constraints:
  - Input objects never overlap or 8-touch.
  - Output stamps never overlap or 8-touch the drawn lines or each other.
  - Every stamp lies fully inside the grid.
  - A connecting line never enters or 8-touches the body of a third shape
    unless that shape's centre lies on the line. As a result, 'join all
    aligned pairs' and 'join unobstructed pairs' give the same picture.
"""

import collections
import functools
import random

import common

BACKGROUND = 7

SHAPES = {
  'dot': [(0, 0)],
  'plus': [(-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)],
  'x': [(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)],
  'ibeam': [(-2, -1), (-2, 0), (-2, 1), (-1, 0), (0, 0), (1, 0),
            (2, -1), (2, 0), (2, 1)],
  'hbeam': [(-1, -2), (0, -2), (1, -2), (0, -1), (0, 0), (0, 1),
            (-1, 2), (0, 2), (1, 2)],
  'ring': [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0),
           (1, 1)],
  'diamond': [(-1, 0), (0, -1), (0, 1), (1, 0)],
}

UNIT_DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1),
                   (0, -1), (-1, 0), (-1, -1), (-1, 1))

LAYOUT_COUNTS = {
  'pair': (2,),
  'right': (3,),
  'apex': (3,),
  'bent': (3,),
  'square': (4,),
  'grown': (2, 3, 4, 5),
}

LAYOUT_CHOICES = ('pair', 'right', 'apex', 'bent', 'square', 'grown', 'grown')

STRUCTURED = ('pair', 'right', 'square', 'apex')

NEAR = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1))

_Info = collections.namedtuple('_Info', 'cells er ec halo conflict')


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _as_point(p, name):
  try:
    pt = tuple(p)
  except TypeError:
    raise ValueError('%s must be a (row, col) pair of integers' % name)
  if len(pt) != 2 or not all(_is_int(v) for v in pt):
    raise ValueError('%s must be a (row, col) pair of integers' % name)
  return pt


def _sign(v):
  return (v > 0) - (v < 0)


@functools.lru_cache(maxsize=512)
def _template_info(key):
  """Extents, 8-halo offsets and stamp-conflict offsets of a template."""
  cells = key
  er = max(abs(r) for r, _ in cells)
  ec = max(abs(c) for _, c in cells)
  halo = frozenset((r + dr, c + dc) for r, c in cells for dr, dc in NEAR)
  conflict = frozenset((a[0] - b[0] + dr, a[1] - b[1] + dc)
                       for a in cells for b in cells for dr, dc in NEAR)
  return _Info(cells, er, ec, halo, conflict)


def _info(template):
  return _template_info(tuple(sorted(set(template))))


def _segment(start, direction, length):
  return [(start[0] + direction[0] * k, start[1] + direction[1] * k)
          for k in range(length)]


def _aligned(a, b):
  dy, dx = b[0] - a[0], b[1] - a[1]
  return dy == 0 or dx == 0 or abs(dy) == abs(dx)


def _pair_line(a, b):
  (ay, ax), (by, bx) = a, b
  dy, dx = by - ay, bx - ax
  n = max(abs(dy), abs(dx))
  sy, sx = _sign(dy), _sign(dx)
  return [(ay + sy * k, ax + sx * k) for k in range(n + 1)]


def _aligned_pairs(centres):
  return [(i, j) for i in range(len(centres))
          for j in range(i + 1, len(centres))
          if _aligned(centres[i], centres[j])]


def _connect(centres):
  """Cells of every line joining two aligned centres."""
  cells = []
  for i, j in _aligned_pairs(centres):
    cells.extend(_pair_line(centres[i], centres[j]))
  return cells


def _stamp(centre, template):
  return [(centre[0] + dy, centre[1] + dx) for dy, dx in template]


def _separated(groups):
  """True if the cell groups are pairwise disjoint and not 8-adjacent."""
  owner = {}
  for idx, cells in enumerate(groups):
    for cell in cells:
      if cell in owner and owner[cell] != idx:
        return False
      owner[cell] = idx
  for (r, c), idx in owner.items():
    for dr, dc in NEAR:
      other = owner.get((r + dr, c + dc))
      if other is not None and other != idx:
        return False
  return True


def _inside(cells, height, width):
  return all(0 <= r < height and 0 <= c < width for r, c in cells)


def _connected8(cells):
  cells = set(cells)
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr, dc in NEAR:
      n = (r + dr, c + dc)
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _collinear(cells):
  if len(cells) < 3:
    return True
  (r0, c0), (r1, c1) = cells[0], cells[1]
  return all((r1 - r0) * (c - c0) - (c1 - c0) * (r - r0) == 0
             for r, c in cells[2:])


def _apart(p, q, er, ec):
  return abs(p[0] - q[0]) >= 2 * er + 2 or abs(p[1] - q[1]) >= 2 * ec + 2


def _pick(lo, hi):
  """Uniform or small-biased integer in [lo, hi]; None if empty."""
  if hi < lo:
    return None
  if random.random() < 0.5:
    return random.randint(lo, hi)
  return random.randint(lo, random.randint(lo, hi))


def _check_template(template):
  """Normalise an explicit offset list, rejecting unusable templates."""
  try:
    items = list(template)
  except TypeError:
    raise ValueError('shape must be a name or a list of (dr, dc) offsets')
  cells = sorted(set(_as_point(p, 'shape offset') for p in items))
  if not cells:
    raise ValueError('shape template must be non-empty')
  rs = [r for r, _ in cells]
  cs = [c for _, c in cells]
  if min(rs) != -max(rs) or min(cs) != -max(cs):
    raise ValueError('shape template must be centred on its bounding box')
  if not _connected8(cells):
    raise ValueError('shape template must be 8-connected')
  if len(cells) > 1 and _collinear(cells):
    raise ValueError('a multi-cell shape template must not be a straight '
                     'segment (it would mimic the line object)')
  return cells


def _random_template():
  """A random 8-connected, non-collinear template with odd bounding box."""
  hr, hc = random.choice([(1, 1), (1, 1), (1, 2), (2, 1), (2, 2)])
  box = [(r, c) for r in range(-hr, hr + 1) for c in range(-hc, hc + 1)]
  for _ in range(500):
    p = random.uniform(0.35, 0.75)
    cells = sorted(cell for cell in box if random.random() < p)
    if len(cells) < 3:
      continue
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    if min(rs) != -hr or max(rs) != hr or min(cs) != -hc or max(cs) != hc:
      continue
    if not _connected8(cells) or _collinear(cells):
      continue
    return cells
  return SHAPES['ring']


def _geom_ok(info, centres):
  """Grid-independent shape constraints: separation and line halos."""
  n = len(centres)
  if n < 2:
    return False
  for i in range(n):
    for j in range(i + 1, n):
      diff = (centres[j][0] - centres[i][0], centres[j][1] - centres[i][1])
      if diff in info.conflict:
        return False
  pairs = _aligned_pairs(centres)
  if not pairs:
    return False
  for i, j in pairs:
    line = _pair_line(centres[i], centres[j])
    on_line = set(line)
    for k, (kr, kc) in enumerate(centres):
      if k in (i, j) or (kr, kc) in on_line:
        continue
      for r, c in line:
        if (r - kr, c - kc) in info.halo:
          return False
  return True


def _centres_ok(height, width, info, centres):
  """All shape bodies inside the grid, plus the geometric constraints."""
  for r, c in centres:
    if not (info.er <= r <= height - 1 - info.er and
            info.ec <= c <= width - 1 - info.ec):
      return False
  return _geom_ok(info, centres)


@functools.lru_cache(maxsize=2048)
def _structured_candidates(key, layout):
  """Every geometrically valid normalised centre set for a layout."""
  info = _template_info(key)
  found = []
  for d in range(1, 30):
    if layout == 'pair':
      sets = ([(0, 0), (0, d)], [(0, 0), (d, 0)], [(0, 0), (d, d)],
              [(0, d), (d, 0)])
    elif layout == 'right':
      corners = [(0, 0), (0, d), (d, 0), (d, d)]
      sets = [[p for p in corners if p != m] for m in corners]
    elif layout == 'square':
      sets = ([(0, 0), (0, d), (d, 0), (d, d)],)
    else:
      if 2 * d > 29:
        break
      sets = ([(0, 0), (0, 2 * d), (d, d)], [(d, 0), (d, 2 * d), (0, d)],
              [(0, 0), (2 * d, 0), (d, d)], [(0, d), (2 * d, d), (d, 0)])
    for rel in sets:
      if _geom_ok(info, rel):
        found.append((d, tuple(rel), max(r for r, _ in rel),
                      max(c for _, c in rel)))
  return tuple(found)


def _fitting(info, layout, height, width):
  room_r = height - 1 - 2 * info.er
  room_c = width - 1 - 2 * info.ec
  if room_r < 0 or room_c < 0:
    return []
  return [f for f in _structured_candidates(info.cells, layout)
          if f[2] <= room_r and f[3] <= room_c]


def _frame_ok(fh, fw, ar, ac, layout):
  """Conservative spacing feasibility for the 'bent' and 'grown' layouts."""
  room_r = fh - 1 - 2 * ar
  room_c = fw - 1 - 2 * ac
  if room_r < 0 or room_c < 0:
    return False
  mh, mv = 2 * ac + 2, 2 * ar + 2
  md = min(mh, mv)
  if layout == 'grown':
    return mh <= room_c or mv <= room_r or md <= min(room_r, room_c)
  if layout == 'bent':
    return (mh <= room_c and mv <= room_r and
            not (mh == room_c and mv == room_r and mh == mv))
  return False


def _layout_feasible(height, width, info, layout):
  if layout in STRUCTURED:
    return bool(_fitting(info, layout, height, width))
  return (_frame_ok(height, width, info.er, info.ec, layout) or
          _frame_ok(width, height, info.ec, info.er, layout))


def _random_centres(height, width, info, layout, count):
  """Sample centres for a layout, or None."""
  if layout in STRUCTURED:
    fits = _fitting(info, layout, height, width)
    if not fits:
      return None
    ds = sorted(set(f[0] for f in fits))
    d = ds[_pick(0, len(ds) - 1)]
    _, rel, span_r, span_c = random.choice([f for f in fits if f[0] == d])
    oy = random.randint(info.er, height - 1 - info.er - span_r)
    ox = random.randint(info.ec, width - 1 - info.ec - span_c)
    return [(r + oy, c + ox) for r, c in rel]
  frames = []
  for transpose in (False, True):
    if transpose:
      frame = (True, width, height, info.ec, info.er)
    else:
      frame = (False, height, width, info.er, info.ec)
    if _frame_ok(frame[1], frame[2], frame[3], frame[4], layout):
      frames.append(frame)
  if not frames:
    return None
  transpose, fh, fw, ar, ac = random.choice(frames)
  room_r = fh - 1 - 2 * ar
  room_c = fw - 1 - 2 * ac
  mh, mv = 2 * ac + 2, 2 * ar + 2
  md = min(mh, mv)
  if layout == 'bent':
    rel = None
    for _ in range(20):
      a = _pick(mh, room_c)
      b = _pick(mv, room_r)
      if a is None or b is None:
        return None
      if a != b:
        rel = [(0, 0), (0, a), (b, a)]
        break
    if rel is None:
      return None
  else:
    rel = [(0, 0)]
    for _ in range(200):
      if len(rel) >= count:
        break
      p = random.choice(rel)
      dv = random.choice(UNIT_DIRECTIONS)
      if dv[0] == 0:
        d = _pick(mh, room_c)
      elif dv[1] == 0:
        d = _pick(mv, room_r)
      else:
        d = _pick(md, min(room_r, room_c))
      if d is None:
        continue
      q = (p[0] + dv[0] * d, p[1] + dv[1] * d)
      if not all(_apart(q, s, ar, ac) for s in rel):
        continue
      rows = [r for r, _ in rel] + [q[0]]
      cols = [c for _, c in rel] + [q[1]]
      if max(rows) - min(rows) > room_r or max(cols) - min(cols) > room_c:
        continue
      rel.append(q)
    if len(rel) < count:
      return None
  sr, sc = random.choice((1, -1)), random.choice((1, -1))
  rel = [(r * sr, c * sc) for r, c in rel]
  if transpose:
    rel = [(c, r) for r, c in rel]
  er, ec = info.er, info.ec
  lo_r = -min(r for r, _ in rel) + er
  hi_r = height - 1 - max(r for r, _ in rel) - er
  lo_c = -min(c for _, c in rel) + ec
  hi_c = width - 1 - max(c for _, c in rel) - ec
  if lo_r > hi_r or lo_c > hi_c:
    return None
  oy, ox = random.randint(lo_r, hi_r), random.randint(lo_c, hi_c)
  return [(r + oy, c + ox) for r, c in rel]


def _valid(height, width, info, start, direction, length, centres):
  """Segment-dependent constraints; centres are assumed to pass checks."""
  if length < 3:
    return False
  seg = _segment(start, direction, length)
  if not _inside(seg, height, width):
    return False
  stamps = [_stamp(seg[0], info.cells), _stamp(seg[-1], info.cells)]
  for cells in stamps:
    if not _inside(cells, height, width):
      return False
  shapes = [_stamp(c, info.cells) for c in centres]
  if not _separated([seg] + shapes):
    return False
  if not _separated([_connect(centres)] + stamps):
    return False
  return True


def _start_range(lo, hi, step, length):
  """Start positions p with p and p + step*(length-1) inside [lo, hi]."""
  span = step * (length - 1)
  return max(lo, lo - span), min(hi, hi - span)


def _max_length(height, width, er, ec, direction, start):
  """Longest segment along direction whose endpoint stamps fit the grid."""
  limits = []
  for axis, size, margin in ((0, height, er), (1, width, ec)):
    d = direction[axis]
    if d == 0:
      continue
    if start is None:
      limits.append(size - 2 * margin)
    else:
      p = start[axis]
      room = (size - 1 - margin - p) if d > 0 else (p - margin)
      limits.append(room + 1)
  return min(limits)


def _line_feasible(height, width, info, start, direction, length):
  """Necessary feasibility of the segment controls in a grid."""
  er, ec = (info.er, info.ec) if info is not None else (0, 0)
  dirs = [direction] if direction is not None else list(UNIT_DIRECTIONS)
  lengths = [length] if length is not None else range(3, 31)
  for d in dirs:
    for n in lengths:
      off = (d[0] * (n - 1), d[1] * (n - 1))
      if info is not None and off in info.conflict:
        continue
      if start is not None:
        ends = [start, (start[0] + off[0], start[1] + off[1])]
        if all(er <= r <= height - 1 - er and ec <= c <= width - 1 - ec
               for r, c in ends):
          return True
      elif (abs(off[0]) <= height - 1 - 2 * er and
            abs(off[1]) <= width - 1 - 2 * ec):
        return True
  return False


def _choose_dim(fixed, coords, margin):
  if fixed is not None:
    return fixed
  lo = max([10] + [v + margin + 1 for v in coords])
  if lo > 30:
    return None
  return random.randint(lo, 30)


def _render(height, width, info, lc, sc, start, direction, length, centres):
  grid = common.grid(width, height, BACKGROUND)
  out = common.grid(width, height, BACKGROUND)
  seg = _segment(start, direction, length)
  for r, c in seg:
    grid[r][c] = lc
  for centre in centres:
    for r, c in _stamp(centre, info.cells):
      grid[r][c] = sc
  for r, c in _connect(centres):
    out[r][c] = lc
  for end in (seg[0], seg[-1]):
    for r, c in _stamp(end, info.cells):
      out[r][c] = sc
  return {'input': grid, 'output': out}


def generate(height=None, width=None, line_color=None, shape_color=None,
             shape=None, line_start=None, line_dir=None, line_length=None,
             centres=None, layout=None, num_shapes=None):
  """Generate one input/output pair.

  Args:
    height: number of grid rows, an integer 1..30. If omitted, it is sampled
      from 10..30 and raised if needed to fit explicit points.
    width: number of grid columns, an integer 1..30. It is sampled the same
      way.
    line_color: colour 0..9 of the straight segment. It must not be 7 and
      must differ from shape_color.
    shape_color: colour 0..9 of the small repeated shapes. It must not be 7.
    shape: a name from SHAPES, 'random' for a sampled template, or an
      explicit list of integer (dr, dc) offsets. Offsets must be centred on
      their bounding box, 8-connected, and not a straight multi-cell run.
    line_start: integer (row, col) of one endpoint of the segment.
    line_dir: (dr, dc) unit step of the segment, e.g. (1, -1).
    line_length: number of cells in the segment, an integer >= 3.
    centres: list of integer (row, col) shape centres. It needs at least two
      distinct centres with an aligned pair, and it is mutually exclusive
      with layout.
    layout: one of LAYOUT_COUNTS (a string): the random centre configuration.
    num_shapes: number of shape centres, 2..5. It must be compatible with
      layout or centres.

  Raises:
    ValueError: for malformed, inconsistent or detectably infeasible
      controls. Detection also applies when height or width is omitted;
      a 30x30 grid is then used as the most permissive bound. Explicit
      controls are honoured exactly or rejected, never altered.
    RuntimeError: the controls passed the prechecks, but the bounded
      sampler found no valid scene. This is possible only for the
      heuristic 'bent'/'grown' layouts, or for shape='random'.
  """
  for name, v in (('height', height), ('width', width)):
    if v is not None and (not _is_int(v) or not 1 <= v <= 30):
      raise ValueError('%s must be an integer in 1..30' % name)
  for name, v in (('line_color', line_color), ('shape_color', shape_color)):
    if v is not None and (not _is_int(v) or not 0 <= v <= 9 or
                          v == BACKGROUND):
      raise ValueError('%s must be an integer colour 0..9 other than 7' % name)
  if line_color is not None and line_color == shape_color:
    raise ValueError('line_color and shape_color must differ')
  if line_dir is not None:
    line_dir = _as_point(line_dir, 'line_dir')
    if line_dir not in UNIT_DIRECTIONS:
      raise ValueError('line_dir must be a unit row/column/diagonal step')
  if line_length is not None and (not _is_int(line_length) or
                                  line_length < 3):
    raise ValueError('line_length must be an integer of at least 3 (shorter '
                     'segments put the two endpoint stamps in contact)')
  if line_start is not None:
    line_start = _as_point(line_start, 'line_start')
    if line_start[0] < 0 or line_start[1] < 0:
      raise ValueError('line_start must be non-negative')
  if layout is not None and (not isinstance(layout, str) or
                             layout not in LAYOUT_COUNTS):
    raise ValueError('unknown layout: %r' % (layout,))
  if num_shapes is not None and not _is_int(num_shapes):
    raise ValueError('num_shapes must be an integer')
  if centres is not None:
    try:
      centres = [_as_point(c, 'centre') for c in centres]
    except TypeError:
      raise ValueError('centres must be a list of (row, col) pairs')
    if layout is not None:
      raise ValueError('centres and layout are mutually exclusive')
    if num_shapes is not None and num_shapes != len(centres):
      raise ValueError('num_shapes does not match len(centres)')
    if len(centres) < 2 or len(set(centres)) != len(centres):
      raise ValueError('centres must hold at least two distinct points')
    if any(r < 0 or c < 0 for r, c in centres):
      raise ValueError('centres must be non-negative')
    if not _aligned_pairs(centres):
      raise ValueError('centres must contain at least one aligned pair')
  if num_shapes is not None:
    if layout is not None and num_shapes not in LAYOUT_COUNTS[layout]:
      raise ValueError('num_shapes incompatible with layout')
    if centres is None and not 2 <= num_shapes <= 5:
      raise ValueError('num_shapes must be in 2..5')
  fixed_info = None
  if shape is not None and not (isinstance(shape, str) and shape == 'random'):
    if isinstance(shape, str):
      if shape not in SHAPES:
        raise ValueError('unknown shape name: %s' % shape)
      fixed_info = _info(SHAPES[shape])
    else:
      fixed_info = _info(_check_template(shape))

  # Prechecks in the largest admissible grid (exact when sizes are given).
  max_h = height if height is not None else 30
  max_w = width if width is not None else 30
  line_fixed = (line_start is not None and line_dir is not None and
                line_length is not None)
  pinned = list(centres or [])
  if line_start is not None:
    pinned.append(line_start)
  if line_fixed:
    end = (line_start[0] + line_dir[0] * (line_length - 1),
           line_start[1] + line_dir[1] * (line_length - 1))
    if end[0] < 0 or end[1] < 0:
      raise ValueError('the requested segment leaves the grid')
    pinned.append(end)
  for r, c in pinned:
    if r > max_h - 1 or c > max_w - 1:
      raise ValueError('explicit point lies outside any admissible grid')
  if fixed_info is not None:
    m_r, m_c = fixed_info.er, fixed_info.ec
  elif shape is not None:
    m_r = m_c = 1  # every random template has extent >= 1 on both axes
  else:
    m_r = m_c = 0
  for r, c in pinned:
    if r < m_r or c < m_c or r > max_h - 1 - m_r or c > max_w - 1 - m_c:
      raise ValueError('explicit point is too close to the grid edge for '
                       'the shape template')
  if not _line_feasible(max_h, max_w, fixed_info, line_start, line_dir,
                        line_length):
    raise ValueError('segment controls cannot fit in this grid')
  if layout is not None:
    lays = [layout]
  else:
    lays = [l for l in LAYOUT_COUNTS
            if num_shapes is None or num_shapes in LAYOUT_COUNTS[l]]

  def feasible(info):
    if not _line_feasible(max_h, max_w, info, line_start, line_dir,
                          line_length):
      return False
    if centres is not None:
      if not _centres_ok(max_h, max_w, info, centres):
        return False
      if line_fixed:
        return _valid(max_h, max_w, info, line_start, line_dir, line_length,
                      centres)
      return True
    return any(_layout_feasible(max_h, max_w, info, l) for l in lays)

  named = []
  if fixed_info is not None:
    if not feasible(fixed_info):
      raise ValueError('requested controls are infeasible for this shape '
                       'template (spacing, line halo or edge constraints)')
  elif shape is None:
    named = [SHAPES[k] for k in sorted(SHAPES) if feasible(_info(SHAPES[k]))]
    if not named:
      raise ValueError('no named shape template satisfies the controls')

  for _ in range(300):
    if fixed_info is not None:
      info = fixed_info
    elif shape is None and random.random() < 0.65:
      info = _info(random.choice(named))
    else:
      info = _info(_random_template())
    er, ec = info.er, info.ec
    h = _choose_dim(height, [r for r, _ in pinned], er)
    w = _choose_dim(width, [c for _, c in pinned], ec)
    if h is None or w is None:
      continue
    if any(r < er or c < ec or r > h - 1 - er or c > w - 1 - ec
           for r, c in pinned):
      continue
    if line_color is not None:
      lc = line_color
    else:
      lc = random.choice([c for c in range(10)
                          if c not in (BACKGROUND, shape_color)])
    if shape_color is not None:
      sc = shape_color
    else:
      sc = random.choice([c for c in range(10) if c not in (BACKGROUND, lc)])
    if centres is not None:
      cs = centres
    else:
      if layout is not None:
        options = [layout]
      else:
        options = [l for l in LAYOUT_CHOICES
                   if num_shapes is None or num_shapes in LAYOUT_COUNTS[l]]
      options = [l for l in options if _layout_feasible(h, w, info, l)]
      if not options:
        continue
      lay = random.choice(options)
      if num_shapes is not None:
        count = num_shapes
      else:
        count = random.choice(LAYOUT_COUNTS[lay])
      cs = _random_centres(h, w, info, lay, count)
      if cs is None:
        continue
    if not _centres_ok(h, w, info, cs):
      continue
    dirs = UNIT_DIRECTIONS if line_start is not None else UNIT_DIRECTIONS[:4]
    for _ in range(1 if line_fixed else 60):
      direction = line_dir if line_dir is not None else random.choice(dirs)
      if line_length is not None:
        length = line_length
      else:
        lmax = _max_length(h, w, er, ec, direction, line_start)
        lens = [n for n in range(3, lmax + 1)
                if (direction[0] * (n - 1), direction[1] * (n - 1))
                not in info.conflict]
        if not lens:
          continue
        length = lens[_pick(0, len(lens) - 1)]
      if line_start is not None:
        start = line_start
      else:
        r0, r1 = _start_range(er, h - 1 - er, direction[0], length)
        c0, c1 = _start_range(ec, w - 1 - ec, direction[1], length)
        if r0 > r1 or c0 > c1:
          continue
        start = (random.randint(r0, r1), random.randint(c0, c1))
      if _valid(h, w, info, start, direction, length, cs):
        return _render(h, w, info, lc, sc, start, direction, length, cs)
  raise RuntimeError('could not construct a valid scene for these parameters')


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(height=16, width=16, line_color=2, shape_color=1,
               shape='plus', line_start=(2, 7), line_dir=(1, -1),
               line_length=6, centres=[(6, 13), (12, 7), (12, 13)]),
      generate(height=11, width=11, line_color=9, shape_color=5,
               shape='dot', line_start=(2, 2), line_dir=(1, 0),
               line_length=6, centres=[(5, 5), (5, 9)]),
      generate(height=16, width=16, line_color=4, shape_color=8,
               shape='x', line_start=(3, 11), line_dir=(1, 0),
               line_length=10, centres=[(2, 2), (6, 6), (10, 2)]),
  ]
  test = [
      generate(height=16, width=16, line_color=1, shape_color=2,
               shape='ibeam', line_start=(12, 2), line_dir=(0, 1),
               line_length=6, centres=[(3, 6), (3, 12), (9, 12)]),
  ]
  return {'train': train, 'test': test}
