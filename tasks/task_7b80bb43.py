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

"""Generator for ARC task 7b80bb43: repairing slipped line segments.

Rule: the grid has one background colour plus horizontal and vertical lines
in a single colour. Some lines have gaps. A 'pure diagonal' chain is a set of
cells joined by diagonal steps whose two shared corner cells are background.
The chain's root is its one cell with exactly one orthogonal foreground
neighbour. In the output:
  * every non-root chain cell is erased (staircases and loose diagonals);
  * from each root, a ray runs straight away from the root's orthogonal
    neighbour. If it reaches a line cell, the background cells it crosses
    are filled with the line colour. If it leaves the grid, the root is
    erased as well;
  * plain gaps without a staircase stay open.

Scope:
  * Random grids are 12..30 per side. An explicit width or height for a
    random scene must be 10..30. Very small sizes may fail to produce a
    scene and raise RuntimeError after bounded retries.
  * Any pair of distinct colours in 0..9 can be background and line colour.
  * A scene has 1..3 row lines and 1..3 column lines, at least 3 apart.
    Line ends can be the grid edge, a perpendicular line, or a free point.
  * Each scene has 1..3 bridged collinear gaps (the fixture mechanism). A
    gap is 2..5 cells long, weighted towards 3 (the fixtures only use 3).
    Its staircase is 1..gap-1 cells, hangs from either end, goes to either
    side and always leans into the gap. A staircase leaning away from the
    gap would touch the line behind its root, so it is not a valid chain.
  * Each scene has 1..2 plain gaps as the contrast case.
  * Each scene has 0..2 loose diagonals of 2..4 cells. They are often
    placed 2..3 cells off a line, as near-miss distractors.
  * Optionally a perpendicular one-cell stub with a 1..2 cell staircase.
    Its ray either leaves the grid (stub erased, as in the test fixture) or
    hits a parallel line (gap filled; this is a synthetic extension).
  * Optionally a staircase on a free line end (synthetic extension). Its ray
    runs along the line and either completes a T-junction with a
    perpendicular line or leaves the grid, which erases the end cell.

Each random scene is checked against its own latent constraints:
  * the pure-diagonal adjacencies are exactly the intended chains;
  * each root has exactly one orthogonal neighbour, and no other chain cell
    touches the foreground orthogonally;
  * every filling ray crosses only background cells that no other ray fills.
    It ends on a line cell that is not erased. Rays other than collinear
    gap bridges never cross plain-gap cells;
  * every erasing ray reaches the edge through untouched background, so the
    ray processing order cannot change the result;
  * foreground covers at most 40% of the grid, so the background is the
    majority colour.

To reproduce a fixture, pass explicit latent objects (lines, diagonals,
bridges, stubs). Explicit scenes need width, height, both colours and at
least one diagonal piece. Diagonals/bridges/stubs without lines are
rejected. Explicit objects are checked for shape, bounds, unique chain roots,
order-independent rays and agreement between the declared edits and the
visible structure. Outputs still come from the supplied latent edits.
Single-cell remnants after plain gaps are permitted near-miss distractors.
"""

import random

import common


_MIN_LEN = 4
_ORTH = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _is_int(value):
  """True for genuine integers; bool is rejected."""
  return isinstance(value, int) and not isinstance(value, bool)


def _cells(orient, idx, a, b):
  """Cells of a segment: 'h' fixes row idx, 'v' fixes column idx; a..b inclusive."""
  if orient == 'h':
    return [(idx, c) for c in range(a, b + 1)]
  return [(r, idx) for r in range(a, b + 1)]


def _axes(orient):
  """Returns (axis, perpendicular) unit vectors as (drow, dcol)."""
  if orient == 'h':
    return (0, 1), (1, 0)
  return (1, 0), (0, 1)


def _segment_of(path):
  """Converts a straight run of cells into an (orient, idx, a, b) segment."""
  if len({cell[0] for cell in path}) == 1:
    cols = [cell[1] for cell in path]
    return ('h', path[0][0], min(cols), max(cols))
  rows = [cell[0] for cell in path]
  return ('v', path[0][1], min(rows), max(rows))


def _walk(start, d, height, width, solid):
  """Walks from start in direction d until a solid cell or the grid edge.

  Returns (list of crossed cells, hit cell or None if the walk left the grid).
  """
  path = []
  y, x = start
  while 0 <= y < height and 0 <= x < width:
    if (y, x) in solid:
      return path, (y, x)
    path.append((y, x))
    y += d[0]
    x += d[1]
  return path, None


def _positions(n, count):
  """Picks up to count line positions in 1..n-2 that are at least 3 apart."""
  out = []
  for _ in range(60):
    if len(out) == count:
      break
    x = random.randint(1, n - 2)
    if all(abs(x - y) >= 3 for y in out):
      out.append(x)
  return sorted(out)


def _extent(n, crossings):
  """Samples a line extent (a, b) of at least _MIN_LEN cells.

  Each end is the grid edge, the position of a perpendicular line, or a free
  point anywhere.
  """
  for _ in range(30):
    roll = random.random()
    if roll < 0.45:
      a = 0
    elif roll < 0.7 and crossings:
      a = random.choice(crossings)
    else:
      a = random.randint(1, max(1, n - _MIN_LEN))
    roll = random.random()
    if roll < 0.45:
      b = n - 1
    elif roll < 0.7 and crossings:
      b = random.choice(crossings)
    else:
      b = random.randint(min(a + _MIN_LEN - 1, n - 2), n - 2)
    if b - a + 1 >= _MIN_LEN:
      return a, b
  return 0, n - 1


def _check(height, width, base, st):
  """Checks the latent scene's own validity and ambiguity constraints."""
  line_cells = base - st['removed']
  extra = set()
  for kind, cells in st['chains']:
    own = cells[1:] if kind in ('bridge', 'end') else cells
    for cell in own:
      if not (0 <= cell[0] < height and 0 <= cell[1] < width):
        return False
      if cell in line_cells or cell in extra or cell in st['removed']:
        return False
      extra.add(cell)
  for kind, cells in st['chains']:
    if kind in ('bridge', 'end') and cells[0] not in line_cells:
      return False
  if any(cell not in line_cells for cell in st['erased']):
    return False
  fg = line_cells | extra
  if 5 * len(fg) > 2 * height * width:
    return False

  def degree(cell):
    y, x = cell
    return sum((y + dy, x + dx) in fg for dy, dx in _ORTH)

  expected = set()
  for _, cells in st['chains']:
    for p, q in zip(cells, cells[1:]):
      expected.add(frozenset((p, q)))
  actual = set()
  for y, x in fg:
    for dx in (-1, 1):
      other = (y + 1, x + dx)
      if other in fg and (y, x + dx) not in fg and (y + 1, x) not in fg:
        actual.add(frozenset(((y, x), other)))
  if actual != expected:
    return False
  for kind, cells in st['chains']:
    if kind == 'loose':
      if any(degree(c) for c in cells):
        return False
    elif degree(cells[0]) != 1 or any(degree(c) for c in cells[1:]):
      return False
  fills = set()
  for path, hit in st['rays']:
    for cell in path:
      if cell in fg or cell in fills:
        return False
      fills.add(cell)
    if hit not in line_cells or hit in st['erased']:
      return False
  for path, hit in st['free_rays']:
    for cell in path:
      if cell in fg or cell in fills or cell in st['removed']:
        return False
      fills.add(cell)
    if hit not in line_cells or hit in st['erased']:
      return False
  for path in st['stub_rays']:
    for cell in path:
      if cell in fg or cell in fills or cell in st['removed']:
        return False
  return True


def _propose(kind, lines, owner, height, width, st):
  """Proposes adding one latent object of the given kind; None if impossible."""
  new = {k: (set(v) if isinstance(v, set) else list(v)) for k, v in st.items()}
  if kind == 'loose':
    n = random.randint(2, 4)
    dr, dc = random.choice((-1, 1)), random.choice((-1, 1))
    if random.random() < 0.5:
      orient, idx, a, b = random.choice(lines)
      _, perp = _axes(orient)
      t = random.randint(a, b)
      anchor = _cells(orient, idx, t, t)[0]
      off = random.choice((-1, 1)) * random.randint(2, 3)
      r, c = anchor[0] + perp[0] * off, anchor[1] + perp[1] * off
    else:
      r, c = random.randrange(height), random.randrange(width)
    cells = [(r + dr * j, c + dc * j) for j in range(n)]
    new['chains'].append(('loose', cells))
    new['diagonals'].append((r, c, dr, dc, n))
    return new
  index = random.randrange(len(lines))
  orient, idx, a, b = lines[index]
  axis, perp = _axes(orient)
  solid = set(owner) - new['removed']
  if kind == 'stub':
    if b - a < 2:
      return None
    t = random.randint(a + 1, b - 1)
    span = _cells(orient, idx, t - 1, t + 1)
    if any(c in new['removed'] or c in new['reserved'] for c in span):
      return None
    anchor = span[1]
    if owner[anchor] != {index}:
      return None
    d = random.choice((-1, 1))
    q = random.choice((-1, 1))
    out_dir = (d * perp[0], d * perp[1])
    stub = (anchor[0] + out_dir[0], anchor[1] + out_dir[1])
    step = (out_dir[0] + q * axis[0], out_dir[1] + q * axis[1])
    k = random.randint(1, 2)
    stairs = [(stub[0] + step[0] * j, stub[1] + step[1] * j)
              for j in range(1, k + 1)]
    path, hit = _walk((stub[0] + out_dir[0], stub[1] + out_dir[1]), out_dir,
                      height, width, solid)
    if hit is not None and not path:
      return None
    new['reserved'].update(span)
    new['chains'].append(('stub', [stub] + stairs))
    new['diagonals'].append((stairs[0][0], stairs[0][1], step[0], step[1], k))
    if hit is None:
      new['stub_rays'].append(path)
      new['stubs'].append(stub)
    else:
      new['free_rays'].append((path, hit))
      new['kept'].append(stub)
      new['bridges'].append(_segment_of(path))
    return new
  if kind == 'end':
    n_axis = width if orient == 'h' else height
    ends = []
    if a > 0:
      ends.append((a, -1))
    if b < n_axis - 1:
      ends.append((b, 1))
    if not ends:
      return None
    t, s = random.choice(ends)
    root = _cells(orient, idx, t, t)[0]
    behind = _cells(orient, idx, t - s, t - s)[0]
    if any(c in new['removed'] or c in new['reserved'] for c in (root, behind)):
      return None
    if owner.get(root) != {index}:
      return None
    direction = (s * axis[0], s * axis[1])
    q = random.choice((-1, 1))
    step = (direction[0] + q * perp[0], direction[1] + q * perp[1])
    k = random.randint(1, 3)
    stairs = [(root[0] + step[0] * j, root[1] + step[1] * j)
              for j in range(1, k + 1)]
    path, hit = _walk((root[0] + direction[0], root[1] + direction[1]),
                      direction, height, width, solid)
    if not path:
      return None
    new['reserved'].update((root, behind))
    new['chains'].append(('end', [root] + stairs))
    new['diagonals'].append((stairs[0][0], stairs[0][1], step[0], step[1], k))
    if hit is None:
      new['stub_rays'].append(path)
      new['stubs'].append(root)
      new['erased'].add(root)
    else:
      new['free_rays'].append((path, hit))
      new['bridges'].append(_segment_of(path))
    return new
  if kind == 'bridge':
    glen = 3 if random.random() < 0.5 else random.randint(2, 5)
    margin = 2
  else:
    glen = random.randint(1, 4)
    margin = 1
  lo, hi = a + margin, b - glen - margin + 1
  if hi < lo:
    return None
  p = random.randint(lo, hi)
  span = _cells(orient, idx, p - margin, p + glen - 1 + margin)
  if any(c in new['removed'] or c in new['reserved'] for c in span):
    return None
  gap = _cells(orient, idx, p, p + glen - 1)
  if any(owner.get(c) != {index} for c in gap):
    return None
  new['removed'].update(gap)
  new['reserved'].update(span)
  if kind == 'gap':
    new['gaps'].append((orient, idx, p, p + glen - 1))
    return new
  before = _cells(orient, idx, p - 1, p - 1)[0]
  after = _cells(orient, idx, p + glen, p + glen)[0]
  if random.random() < 0.5:
    root, hit, path, s = before, after, gap, 1
  else:
    root, hit, path, s = after, before, gap[::-1], -1
  q = random.choice((-1, 1))
  if random.random() < 0.5:
    k = glen - 1
  else:
    k = random.randint(1, glen - 1)
  step = (s * axis[0] + q * perp[0], s * axis[1] + q * perp[1])
  stairs = [(root[0] + step[0] * j, root[1] + step[1] * j)
            for j in range(1, k + 1)]
  new['chains'].append(('bridge', [root] + stairs))
  new['rays'].append((path, hit))
  new['diagonals'].append((stairs[0][0], stairs[0][1], step[0], step[1], k))
  new['bridges'].append((orient, idx, p, p + glen - 1))
  return new


def _sample_scene(width, height, background, color):
  """Builds random latent parameters for a fresh scene."""
  for _ in range(300):
    h = height if height is not None else random.randint(12, 30)
    w = width if width is not None else random.randint(12, 30)
    if background is not None:
      bg = background
    else:
      bg = random.choice([c for c in range(10) if c != color])
    if color is not None:
      fgc = color
    else:
      fgc = random.choice([c for c in range(10) if c != bg])
    rows = _positions(h, random.randint(1, 3))
    cols = _positions(w, random.randint(1, 3))
    lines = []
    for r in rows:
      a, b = _extent(w, cols)
      lines.append(('h', r, a, b))
    for c in cols:
      a, b = _extent(h, rows)
      lines.append(('v', c, a, b))
    owner = {}
    for i, line in enumerate(lines):
      for cell in _cells(*line):
        owner.setdefault(cell, set()).add(i)
    base = set(owner)
    st = {'removed': set(), 'reserved': set(), 'erased': set(), 'chains': [],
          'rays': [], 'free_rays': [], 'stub_rays': [], 'diagonals': [],
          'bridges': [], 'stubs': [], 'kept': [], 'gaps': []}
    if not _check(h, w, base, st):
      continue
    plan = (['bridge'] * random.randint(1, 3) + ['gap'] * random.randint(1, 2)
            + ['loose'] * random.randint(0, 2))
    if random.random() < 0.4:
      plan.append('stub')
    if random.random() < 0.35:
      plan.append('end')
    random.shuffle(plan)
    for kind in plan:
      for _ in range(40):
        cand = _propose(kind, lines, owner, h, w, st)
        if cand is not None and _check(h, w, base, cand):
          st = cand
          break
    if not st['rays'] or not st['gaps']:
      continue
    segments = []
    for orient, idx, a, b in lines:
      start = None
      for t in range(a, b + 2):
        alive = t <= b and _cells(orient, idx, t, t)[0] not in st['removed']
        if alive and start is None:
          start = t
        elif not alive and start is not None:
          segments.append((orient, idx, start, t - 1))
          start = None
    for r, c in st['kept']:
      segments.append(('h', r, c, c))
    return (w, h, bg, fgc, segments, st['diagonals'], st['bridges'],
            st['stubs'])
  raise RuntimeError('could not construct a valid scene')


def _parse_segment(seg, what):
  """Validates an (orient, idx, a, b) segment."""
  seg = tuple(seg)
  if (len(seg) != 4 or seg[0] not in ('h', 'v')
      or not all(_is_int(v) for v in seg[1:]) or seg[2] > seg[3]):
    raise ValueError('bad %s segment %r' % (what, seg))
  return seg


def _parse_diagonal(diag):
  """Validates a (row, col, drow, dcol, length) diagonal piece."""
  diag = tuple(diag)
  if (len(diag) != 5 or not all(_is_int(v) for v in diag)
      or diag[2] not in (-1, 1) or diag[3] not in (-1, 1) or diag[4] < 1):
    raise ValueError('bad diagonal %r' % (diag,))
  return diag


def _parse_cell(cell):
  """Validates a (row, col) cell."""
  cell = tuple(cell)
  if len(cell) != 2 or not all(_is_int(v) for v in cell):
    raise ValueError('bad stub cell %r' % (cell,))
  return cell


def _check_explicit_effects(grid, output, background, color):
  """Check declared edits against visible chain topology, without creating targets."""
  h, w = len(grid), len(grid[0])
  fg = {(r, c) for r in range(h) for c in range(w)
        if grid[r][c] == color}
  neighbours = {}
  for r, c in fg:
    adjacent = {(r + dy, c + dx) for dy in (-1, 1) for dx in (-1, 1)
                if (r + dy, c + dx) in fg and (r + dy, c) not in fg
                and (r, c + dx) not in fg}
    if adjacent:
      neighbours[(r, c)] = adjacent
  unseen = set(neighbours)
  removed, roots = set(), []
  while unseen:
    first = unseen.pop()
    group, pending = {first}, [first]
    while pending:
      p = pending.pop()
      for q in neighbours[p] & unseen:
        unseen.remove(q)
        group.add(q)
        pending.append(q)
    if any(len(neighbours[p]) > 2 for p in group):
      raise ValueError('explicit diagonal chains must not branch')
    candidates = []
    for r, c in group:
      orth = {(r + dy, c + dx) for dy, dx in _ORTH} & fg
      if orth:
        if len(orth) != 1:
          raise ValueError('diagonal chain has an ambiguous attachment')
        candidates.append(((r, c), next(iter(orth))))
    if len(candidates) > 1:
      raise ValueError('diagonal chain has multiple roots')
    if candidates:
      root, support = candidates[0]
      roots.append((root, support))
      removed |= group - {root}
    else:
      removed |= group
  solid = fg - removed
  fills, hits, erased_roots, free_paths = set(), set(), set(), set()
  for root, support in roots:
    direction = (root[0] - support[0], root[1] - support[1])
    start = (root[0] + direction[0], root[1] + direction[1])
    path, hit = _walk(start, direction, h, w, solid)
    if hit is None:
      erased_roots.add(root)
      free_paths.update(path)
    else:
      if fills & set(path):
        raise ValueError('explicit repair rays intersect')
      fills.update(path)
      hits.add(hit)
  if hits & erased_roots:
    raise ValueError('explicit repair depends on a root that is erased')
  if free_paths & fills:
    raise ValueError('an explicit escaping ray crosses another repair')
  expected = (solid - erased_roots) | fills
  actual = {(r, c) for r in range(h) for c in range(w)
            if output[r][c] == color}
  if actual != expected:
    raise ValueError('declared edits do not match visible line-repair effects')


def generate(width=None, height=None, background=None, color=None,
             lines=None, diagonals=None, bridges=None, stubs=None):
  """Returns an input/output pair for task 7b80bb43.

  Args:
    width: grid width (columns), an int. Random scenes use 12..30 by
      default. An explicit value must be 10..30 for random scenes and 1..30
      for explicit scenes.
    height: grid height (rows). Same ranges as width.
    background: background colour (0..9).
    color: line colour (0..9). It must differ from the background.
    lines: line segments present in the input, as (orient, idx, a, b).
      orient 'h' means row idx, columns a..b. orient 'v' means column idx,
      rows a..b.
    diagonals: diagonal pieces as (row, col, drow, dcol, length), with drow
      and dcol in {-1, 1} and length >= 1. These are staircases (without
      their root) and loose pieces. All of them are erased.
    bridges: segments (same format as lines) that are background in the
      input and filled with the line colour in the output.
    stubs: cells (row, col) painted in the input and erased in the output.
      These are roots whose ray leaves the grid, either perpendicular stubs
      or line-end cells.

  If lines is None, a fresh random scene is sampled, and any given width,
  height and colours constrain the sampler. In that case diagonals, bridges
  and stubs must also be None. If lines is given, width, height, background
  and color are all required, and lines and diagonals must be non-empty.
  Declared edits must agree with an unambiguous visible chain/ray structure.
  """
  explicit = lines is not None
  for name, value in (('width', width), ('height', height),
                      ('background', background), ('color', color)):
    if value is not None and not _is_int(value):
      raise ValueError('%s must be an integer' % name)
  for value in (background, color):
    if value is not None and not 0 <= value <= 9:
      raise ValueError('colours must be in 0..9')
  if background is not None and color is not None and background == color:
    raise ValueError('background and line colour must differ')
  if lines is None:
    if diagonals is not None or bridges is not None or stubs is not None:
      raise ValueError('diagonals/bridges/stubs require explicit lines')
    for value in (width, height):
      if value is not None and not 10 <= value <= 30:
        raise ValueError('width/height must be in 10..30')
    (width, height, background, color, lines, diagonals, bridges,
     stubs) = _sample_scene(width, height, background, color)
  else:
    if None in (width, height, background, color):
      raise ValueError('explicit lines need width, height, background, color')
    for value in (width, height):
      if not 1 <= value <= 30:
        raise ValueError('width/height must be in 1..30')
    if not lines:
      raise ValueError('explicit scenes need at least one line')
    if not diagonals:
      raise ValueError('explicit scenes need at least one diagonal piece')
  lines = [_parse_segment(s, 'line') for s in lines]
  diagonals = [_parse_diagonal(d) for d in (diagonals or [])]
  bridges = [_parse_segment(s, 'bridge') for s in (bridges or [])]
  stubs = [_parse_cell(c) for c in (stubs or [])]

  def inside(cell):
    return 0 <= cell[0] < height and 0 <= cell[1] < width

  def paint(target, cell, value):
    if not inside(cell):
      raise ValueError('cell %r lies outside the grid' % (cell,))
    target[cell[0]][cell[1]] = value

  grid = common.grid(width, height, background)
  for orient, idx, a, b in lines:
    for cell in _cells(orient, idx, a, b):
      paint(grid, cell, color)
  erase = []
  for r, c, dr, dc, n in diagonals:
    for j in range(n):
      cell = (r + dr * j, c + dc * j)
      paint(grid, cell, color)
      erase.append(cell)
  for cell in stubs:
    paint(grid, cell, color)
    erase.append(cell)
  output = [row[:] for row in grid]
  for cell in erase:
    paint(output, cell, background)
  for orient, idx, a, b in bridges:
    for cell in _cells(orient, idx, a, b):
      if not inside(cell) or grid[cell[0]][cell[1]] != background:
        raise ValueError('bridge cells must be background gap cells')
      paint(output, cell, color)
  if explicit:
    _check_explicit_effects(grid, output, background, color)
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=30, height=16, background=1, color=6,
               lines=[('v', 4, 0, 0), ('v', 4, 3, 6), ('h', 7, 0, 2),
                      ('h', 7, 6, 14), ('h', 7, 18, 20), ('h', 7, 24, 25),
                      ('v', 14, 7, 9), ('v', 14, 13, 15), ('v', 25, 3, 15),
                      ('h', 3, 25, 29), ('h', 10, 25, 29)],
               diagonals=[(3, 19, 1, 1, 3), (8, 17, 1, -1, 2),
                          (10, 13, 1, -1, 2)],
               bridges=[('h', 7, 15, 17), ('v', 14, 10, 12)]),
      generate(width=24, height=28, background=0, color=3,
               lines=[('v', 4, 0, 1), ('v', 4, 6, 11), ('v', 4, 15, 18),
                      ('v', 4, 22, 27), ('h', 9, 4, 6), ('h', 9, 10, 19),
                      ('h', 9, 23, 23), ('v', 11, 9, 22), ('v', 11, 26, 27),
                      ('v', 18, 0, 4), ('v', 18, 8, 9)],
               diagonals=[(7, 19, -1, 1, 2), (10, 20, 1, 1, 2),
                          (23, 12, 1, 1, 2), (17, 19, 1, -1, 3)],
               bridges=[('v', 18, 5, 7), ('h', 9, 20, 22),
                        ('v', 11, 23, 25)]),
  ]
  test = [
      generate(width=17, height=29, background=8, color=9,
               lines=[('h', 3, 0, 1), ('h', 3, 5, 6), ('v', 6, 3, 14),
                      ('h', 14, 0, 9), ('h', 14, 13, 14), ('v', 14, 0, 19),
                      ('v', 14, 23, 25), ('v', 14, 27, 28)],
               diagonals=[(4, 4, 1, -1, 2), (11, 12, 1, -1, 2),
                          (16, 3, 1, 1, 1), (20, 15, 1, 1, 2)],
               bridges=[('h', 3, 2, 4), ('v', 14, 20, 22)],
               stubs=[(15, 2)]),
  ]
  return {'train': train, 'test': test}
