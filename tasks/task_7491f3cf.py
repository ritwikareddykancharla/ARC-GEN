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

"""ARC-GEN style generator for task 7491f3cf.

Rule: the grid is a one-cell frame in a frame colour. The frame colour also
draws the dividers between four H x W panels laid out in a row. All four
panels share one fill colour and one panel shape.

Panel 1 holds two things in a line colour:
  * a wall: an 8-connected stroke that cuts the panel into exactly two
    4-connected regions;
  * a single dot, which is not 8-adjacent to the wall.

Panels 2 and 3 each hold a one-colour pattern. Panel 4 starts empty and is
filled as follows:
  * the region that contains the dot copies panel 2's pattern;
  * the other region copies panel 3's pattern;
  * wall cells show panel 2's colour where panel 2 is not fill, and panel 3's
    cell otherwise.

Scope:
  * Colours: the frame, fill, line, panel-2 and panel-3 colours are sampled
    as five distinct colours.
  * Panel shape: the four panels share one H x W shape. The canvas is
    (H + 2) x (4W + 5), so W is 3..6 and H is 3..28. Nothing in the rule
    needs square panels; every original example uses 5 x 5.
  * 3 x 3 panels are excluded because of the retained guard that each of
    the two regions has at least two cells. This is not a geometric
    impossibility of the task. Exhaustive enumeration of every 8-connected
    wall of two or more cells in a 3 x 3 panel finds 192 walls that leave
    exactly two 4-connected regions. 16 of those 192 leave a cell that is
    not 8-adjacent to the wall, but each of these 16 has a one-cell
    region. Only 40 walls pass the two-cell guard, and none of them leaves
    room for a dot. Example of a scene the guard rules out: wall (0,2),
    (1,2), (2,1), (2,0) with the dot at (0,0) gives regions of 4 and 1
    cells. Whether one-cell regions should be allowed is a separate
    hypothesis; this constructor keeps the guard.
  * Default shapes: one draw in four keeps the legacy square sizes (4, 5 or
    6, weights 1:3:1). Otherwise W is uniform in 3..6 and H is uniform over
    the heights allowed for that W. The shape is drawn once per call and
    kept for every retry, so acceptance rates never reweight shapes.
  * Wall shapes: a straight row or column, a corner-to-corner diagonal
    (a one-cell-per-step staircase along the long axis of a rectangle), an
    L shape that cuts off a corner, or a random monotone 8-connected path
    crossing the panel. Square panels can be transposed; rectangular panels
    draw the crossing axis instead. Any wall can be mirrored left-right.
  * Dot: it is placed in a randomly chosen region, away from the wall.
  * Patterns: they come from a parametric motif family: X (both diagonals),
    plus, checkerboard, corner blocks, corner L's, row or column stripes,
    ring, diamond, random four-fold symmetric, and fully random. On a
    rectangle the diagonals are staircases and the diamond is the largest
    one centred inside the panel.
  * Legacy square panels use the exact random-draw order of the square-only
    constructor, so explicit legacy calls replay unchanged.

Every scene is checked for the following:
  * the fill colour is strictly the most common colour across panels 1-3;
  * the dot's region shows some panel-2 colour;
  * the other region shows some panel-3 colour;
  * the two patterns differ.
  * routing differs from either unconditional whole-panel overlay.
Half of unconstrained calls also require evidence for both wall-cell overlay
branches. Explicit scenes can request this with wall_evidence=True.
"""

import random

import common

# Legacy square panel_size range (explicit panel_size keeps these semantics).
MIN_SIZE, MAX_SIZE = 4, 6
SIZE_WEIGHTS = {4: 1, 5: 3, 6: 1}
# Independent panel dimensions: H + 2 <= 30 and 4W + 5 <= 30.
MIN_HEIGHT, MAX_HEIGHT = 3, 28
MIN_WIDTH, MAX_WIDTH = 3, 6
# Under the retained two-cells-per-region guard, no 3 x 3 wall leaves room
# for a dot (exhaustive enumeration; see the module docstring).
EXCLUDED_SHAPES = frozenset({(3, 3)})
SHAPES = tuple((h, w) for w in range(MIN_WIDTH, MAX_WIDTH + 1)
               for h in range(MIN_HEIGHT, MAX_HEIGHT + 1)
               if (h, w) not in EXCLUDED_SHAPES)
SQUARE_SHARE = 0.25
MAX_TRIES = 400


def _default_weights():
  heights = {w: sum(1 for h, ww in SHAPES if ww == w)
             for w in range(MIN_WIDTH, MAX_WIDTH + 1)}
  total = sum(SIZE_WEIGHTS.values())
  out = {}
  for h, w in SHAPES:
    p = (1 - SQUARE_SHARE) / (MAX_WIDTH - MIN_WIDTH + 1) / heights[w]
    if h == w and h in SIZE_WEIGHTS:
      p += SQUARE_SHARE * SIZE_WEIGHTS[h] / total
    out[(h, w)] = p
  return out


# Probability of each panel shape under unconstrained sampling. Partially
# constrained calls use this distribution conditioned on the allowed shapes.
DEFAULT_SHAPE_WEIGHTS = _default_weights()


def _parse(rows):
  if not isinstance(rows, (list, tuple)) or not rows:
    raise ValueError('patterns must be non-empty lists of "#"/"." strings')
  w = len(rows[0])
  cells = set()
  for r, row in enumerate(rows):
    if len(row) != w or any(ch not in '#.' for ch in row):
      raise ValueError('patterns must be rectangular lists of "#"/"." strings')
    cells |= {(r, c) for c, ch in enumerate(row) if ch == '#'}
  return cells


def _connected8(cells):
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    y, x = stack.pop()
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        q = (y + dy, x + dx)
        if q in cells and q not in seen:
          seen.add(q)
          stack.append(q)
  return len(seen) == len(cells)


def _regions(h, w, wall):
  seen = set()
  regs = []
  for r in range(h):
    for c in range(w):
      if (r, c) in wall or (r, c) in seen:
        continue
      seen.add((r, c))
      stack = [(r, c)]
      reg = set()
      while stack:
        y, x = stack.pop()
        reg.add((y, x))
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
          q = (y + dy, x + dx)
          if (0 <= q[0] < h and 0 <= q[1] < w and q not in wall
              and q not in seen):
            seen.add(q)
            stack.append(q)
      regs.append(reg)
  return regs


def _wall_regions(h, w, wall):
  """Returns the two regions cut by a valid wall, else None."""
  if len(wall) < 2:
    return None
  if any(not (0 <= r < h and 0 <= c < w) for r, c in wall):
    return None
  if not _connected8(wall):
    return None
  regs = _regions(h, w, wall)
  if len(regs) != 2 or min(len(r) for r in regs) < 2:
    return None
  return regs


def _near(cell, wall):
  r, c = cell
  for dy in (-1, 0, 1):
    for dx in (-1, 0, 1):
      if (r + dy, c + dx) in wall:
        return True
  return False


def _staircase(h, w):
  """Corner-to-corner diagonal: one cell per step along the long axis."""
  if h >= w:
    return {(r, (r * (w - 1)) // max(1, h - 1)) for r in range(h)}
  return {((c * (h - 1)) // max(1, w - 1), c) for c in range(w)}


def _line_cells(kind, a, b):
  """A wall of the given kind crossing an a x b frame from top to bottom."""
  if kind == 'straight':
    k = random.randint(1, a - 2)
    return {(k, c) for c in range(b)}
  if kind == 'diagonal':
    return _staircase(a, b)
  if kind == 'ell':
    r = random.randint(1, a - 2)
    c = random.randint(1, b - 2)
    rows = range(0, r + 1) if random.random() < 0.5 else range(r, a)
    cols = range(0, c + 1) if random.random() < 0.5 else range(c, b)
    return {(i, c) for i in rows} | {(r, j) for j in cols}
  col = random.randint(0, b - 1)
  cells = {(0, col)}
  for row in range(1, a):
    col += random.choice([d for d in (-1, 0, 1) if 0 <= col + d < b])
    cells.add((row, col))
  return cells


def _sample_line(h, w):
  """Returns (kind, cells) of a candidate wall for an h x w panel."""
  kind = random.choices(['straight', 'diagonal', 'ell', 'path'],
                        weights=[2, 1, 3, 4])[0]
  if h == w:
    # Legacy square draw order: build, then transpose.
    cells = _line_cells(kind, h, w)
    if random.random() < 0.5:
      cells = {(c, r) for r, c in cells}
  else:
    # A rectangle cannot be transposed in place; choose the crossing axis.
    if random.random() < 0.5:
      cells = {(c, r) for r, c in _line_cells(kind, w, h)}
    else:
      cells = _line_cells(kind, h, w)
  if random.random() < 0.5:
    cells = {(r, w - 1 - c) for r, c in cells}
  return kind, cells


def _mirror(cells, h, w):
  out = set()
  for r, c in cells:
    out |= {(r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c)}
  return out


def _sample_pattern(h, w):
  """Returns (kind, cells) of a candidate pattern for an h x w panel."""
  kind = random.choice(['x', 'plus', 'checker', 'blocks', 'ells', 'stripes',
                        'ring', 'diamond', 'sym', 'sym', 'random'])
  allc = [(r, c) for r in range(h) for c in range(w)]
  if kind == 'x':
    diag = _staircase(h, w)
    return kind, diag | {(r, w - 1 - c) for r, c in diag}
  if kind == 'plus':
    r0 = random.randint(1, h - 2)
    c0 = random.randint(1, w - 2)
    return kind, {(r0, j) for j in range(w)} | {(i, c0) for i in range(h)}
  if kind == 'checker':
    ph = random.randint(0, 1)
    return kind, {(r, c) for r, c in allc if (r + c) % 2 == ph}
  if kind == 'blocks':
    corners = [(0, 0), (0, w - 2), (h - 2, 0), (h - 2, w - 2)]
    chosen = random.sample(corners, random.randint(1, 4))
    cells = set()
    for r0, c0 in chosen:
      cells |= {(r0 + a, c0 + b) for a in (0, 1) for b in (0, 1)}
    return kind, cells
  if kind == 'ells':
    return kind, _mirror({(0, 0), (0, 1), (1, 0)}, h, w)
  if kind == 'stripes':
    step = random.choice([2, 3])
    ph = random.randint(0, step - 1)
    if random.random() < 0.5:
      return kind, {(r, c) for r, c in allc if c % step == ph}
    return kind, {(r, c) for r, c in allc if r % step == ph}
  if kind == 'ring':
    return kind, {(r, c) for r, c in allc
                  if r in (0, h - 1) or c in (0, w - 1)}
  if kind == 'diamond':
    mr, mc = h // 2, w // 2
    k = random.randint(1, min(mr, mc))
    return kind, {(r, c) for r, c in allc if abs(r - mr) + abs(c - mc) == k}
  if kind == 'sym':
    quad = {(r, c) for r in range((h + 1) // 2) for c in range((w + 1) // 2)
            if random.random() < 0.4}
    return kind, _mirror(quad, h, w)
  return kind, {cell for cell in allc if random.random() < 0.3}


def _colours(given):
  used = [v for v in given if v is not None]
  pool = [v for v in range(10) if v not in used]
  random.shuffle(pool)
  return [v if v is not None else pool.pop() for v in given]


def _shape_ok(h, w):
  return (MIN_HEIGHT <= h <= MAX_HEIGHT and MIN_WIDTH <= w <= MAX_WIDTH
          and (h, w) not in EXCLUDED_SHAPES)


def _resolve_shape(panel_size, panel_height, panel_width, line, dot,
                   pattern2, pattern3):
  """Returns the list of allowed (H, W) panel shapes for these arguments."""
  for name, v in (('panel_size', panel_size), ('panel_height', panel_height),
                  ('panel_width', panel_width)):
    if v is not None and type(v) is not int:
      raise ValueError('%s must be an integer' % name)
  for point in list(line or []) + ([] if dot is None else [dot]):
    if len(point) != 2 or any(type(v) is not int for v in point):
      raise ValueError('line and dot coordinates must be integer pairs')
  heights, widths = set(), set()
  if panel_size is not None:
    heights.add(panel_size)
    widths.add(panel_size)
  if panel_height is not None:
    heights.add(panel_height)
  if panel_width is not None:
    widths.add(panel_width)
  for p in (pattern2, pattern3):
    if p is not None:
      _parse(p)
      heights.add(len(p))
      widths.add(len(p[0]))
  if len(heights) > 1 or len(widths) > 1:
    raise ValueError('panel_size, panel_height, panel_width and pattern '
                     'sizes disagree')
  coords = [v for p in (line or []) for v in p] + list(dot or [])
  if any(v < 0 for v in coords):
    raise ValueError('coordinates must be non-negative')
  pts = list(line or []) + ([] if dot is None else [dot])
  lo_h = max([MIN_HEIGHT] + [r + 1 for r, _ in pts])
  lo_w = max([MIN_WIDTH] + [c + 1 for _, c in pts])
  if panel_size is not None:
    if not MIN_SIZE <= panel_size <= MAX_SIZE or panel_size < max(lo_h, lo_w):
      raise ValueError('panel size out of range or too small for line/dot')
    return [(panel_size, panel_size)]
  if heights and not MIN_HEIGHT <= min(heights) <= MAX_HEIGHT:
    raise ValueError('panel height must be in %d..%d' % (MIN_HEIGHT,
                                                         MAX_HEIGHT))
  if widths and not MIN_WIDTH <= min(widths) <= MAX_WIDTH:
    raise ValueError('panel width must be in %d..%d' % (MIN_WIDTH, MAX_WIDTH))
  options = [(h, w) for h, w in SHAPES
             if (not heights or h in heights) and (not widths or w in widths)
             and h >= lo_h and w >= lo_w]
  if heights and widths:
    shape = (min(heights), min(widths))
    if shape in EXCLUDED_SHAPES:
      raise ValueError('3x3 panels are excluded: under the two-cells-per-region '
                       'guard no wall leaves room for a dot')
    if shape not in options:
      raise ValueError('panel shape too small for line/dot')
  if not options:
    raise ValueError('line/dot coordinates do not fit any allowed panel shape')
  return options


def generate(frame=None, background=None, line_color=None, color2=None,
             color3=None, line=None, dot=None, pattern2=None, pattern3=None,
             panel_size=None, wall_evidence=None, panel_height=None,
             panel_width=None):
  """Returns an input/output pair for task 7491f3cf.

  Args:
    frame: colour of the outer frame and panel dividers.
    background: fill colour shared by all four panels.
    line_color: colour of the wall line and dot in panel 1.
    color2: colour of the panel-2 pattern.
    color3: colour of the panel-3 pattern.
    line: list of (row, col) wall cells in panel 1 (local coordinates); must
      be 8-connected and split the panel into two 4-connected regions.
    dot: (row, col) of the dot in panel 1, not 8-adjacent to the wall.
    pattern2: list of H strings of length W, '#' for panel-2 pattern cells.
    pattern3: list of H strings of length W, '#' for panel-3 pattern cells.
    panel_size: legacy square side N (4..6; 5 in all originals). It fixes
      an N x N panel and may be combined only with agreeing dimensions.
    wall_evidence: True requires wall cells where both patterns overlap and
      cells where only panel 3 contributes. None requires this on half of
      unconstrained calls; False allows either branch to be absent.
    panel_height: panel rows H (3..28).
    panel_width: panel columns W (3..6). 3 x 3 panels are excluded (see
      the two-cells-per-region guard above).

  Raises:
    ValueError: if explicit parameters are invalid or incompatible.
    RuntimeError: if no scene is found within MAX_TRIES tries for the chosen
      panel shape. The shape is never changed to recover.
  """
  given = [frame, background, line_color, color2, color3]
  supplied = [v for v in given if v is not None]
  if any(type(v) is not int or not 0 <= v <= 9 for v in supplied):
    raise ValueError('colours must be integers 0..9')
  if len(set(supplied)) != len(supplied):
    raise ValueError('the five colours must be distinct')
  options = _resolve_shape(panel_size, panel_height, panel_width, line, dot,
                           pattern2, pattern3)
  fixed_line = None if line is None else {tuple(p) for p in line}
  fixed_dot = None if dot is None else tuple(dot)
  fixed_p2 = None if pattern2 is None else _parse(pattern2)
  fixed_p3 = None if pattern3 is None else _parse(pattern3)
  shape_fixed = len(options) == 1 and (
      panel_size is not None or pattern2 is not None or pattern3 is not None
      or (panel_height is not None and panel_width is not None))
  geom_fixed = fixed_line is not None and shape_fixed
  dot_fixed = geom_fixed and fixed_dot is not None
  all_fixed = dot_fixed and fixed_p2 is not None and fixed_p3 is not None
  if wall_evidence is not None and type(wall_evidence) is not bool:
    raise ValueError('wall_evidence must be bool or None')
  require_wall = wall_evidence if wall_evidence is not None else (
      not all_fixed and random.random() < 0.5)
  if fixed_line is not None:
    options = [s for s in options if _wall_regions(s[0], s[1], fixed_line)
               and (fixed_dot is None or not _near(fixed_dot, fixed_line))]
    if not options:
      raise ValueError('line/dot cannot form a valid partition at any allowed '
                       'size')
  if len(options) == 1:
    h, w = options[0]
  else:
    h, w = random.choices(options,
                          weights=[DEFAULT_SHAPE_WEIGHTS[s] for s in options])[0]

  for _ in range(MAX_TRIES):
    f, bg, lc, c2, c3 = _colours(given)
    wall = (set(fixed_line) if fixed_line is not None
            else _sample_line(h, w)[1])
    regs = _wall_regions(h, w, wall)
    if regs is None:
      if geom_fixed:
        raise ValueError('line must be an 8-connected wall cutting the panel '
                         'into exactly two 4-connected regions')
      continue
    if fixed_dot is not None:
      d = fixed_dot
      if d in wall or _near(d, wall):
        if dot_fixed:
          raise ValueError('dot must not touch the wall')
        continue
    else:
      choices = [sorted(c for c in reg if not _near(c, wall)) for reg in regs]
      choices = [o for o in choices if o]
      if not choices:
        if geom_fixed:
          raise ValueError('no room for a dot away from the wall')
        continue
      d = random.choice(random.choice(choices))
    dreg = regs[0] if d in regs[0] else regs[1]
    other = regs[1] if dreg is regs[0] else regs[0]
    p2 = set(fixed_p2) if fixed_p2 is not None else _sample_pattern(h, w)[1]
    p3 = set(fixed_p3) if fixed_p3 is not None else _sample_pattern(h, w)[1]
    lim = h * w - 1
    if not 3 <= len(p2) <= lim:
      if fixed_p2 is not None:
        raise ValueError('pattern2 has too few or too many cells')
      continue
    if not 3 <= len(p3) <= lim:
      if fixed_p3 is not None:
        raise ValueError('pattern3 has too few or too many cells')
      continue
    if p2 == p3:
      if fixed_p2 is not None and fixed_p3 is not None:
        raise ValueError('pattern2 and pattern3 must differ')
      continue
    # Each pattern must visibly contribute to its own region.
    if not (dreg & p2) or not (other & p3):
      if all_fixed:
        raise ValueError('a region would show no pattern colour')
      continue
    if require_wall and (not (wall & p2 & p3) or not (wall & (p3 - p2))):
      if all_fixed:
        raise ValueError('both wall overlay branches must be demonstrated')
      continue
    # The fill colour must be strictly the most common across panels 1-3.
    fill_count = 3 * h * w - (len(wall) + 1) - len(p2) - len(p3)
    if fill_count <= max(len(wall) + 1, len(p2), len(p3)):
      if all_fixed:
        raise ValueError('fill colour would not dominate the panels')
      continue
    result = {}
    for r in range(h):
      for c in range(w):
        if (r, c) in wall:
          v = c2 if (r, c) in p2 else (c3 if (r, c) in p3 else bg)
        elif (r, c) in dreg:
          v = c2 if (r, c) in p2 else bg
        else:
          v = c3 if (r, c) in p3 else bg
        result[(r, c)] = v
    overlay2 = {q: c2 if q in p2 else c3 if q in p3 else bg for q in result}
    overlay3 = {q: c3 if q in p3 else c2 if q in p2 else bg for q in result}
    if result == overlay2 or result == overlay3:
      if all_fixed:
        raise ValueError('wall/dot routing would be indistinguishable from an overlay')
      continue
    width, height = 4 * w + 5, h + 2
    grid = common.grid(width, height, f)
    offs = [1 + k * (w + 1) for k in range(4)]
    for k in range(4):
      for r in range(h):
        for c in range(w):
          grid[1 + r][offs[k] + c] = bg
    for r, c in wall | {d}:
      grid[1 + r][offs[0] + c] = lc
    for r, c in p2:
      grid[1 + r][offs[1] + c] = c2
    for r, c in p3:
      grid[1 + r][offs[2] + c] = c3
    out = [row[:] for row in grid]
    for (r, c), v in result.items():
      out[1 + r][offs[3] + c] = v
    return {'input': grid, 'output': out}
  raise RuntimeError('could not build a valid %dx%d-panel scene with the given '
                     'partial parameters within %d tries' % (h, w, MAX_TRIES))


def validate():
  """Reconstructs the canonical fixtures through explicit latent arguments."""
  xs = ['#...#', '.#.#.', '..#..', '.#.#.', '#...#']
  plus = ['..#..', '..#..', '#####', '..#..', '..#..']
  anti = [(i, 4 - i) for i in range(5)]
  diag = [(i, i) for i in range(5)]
  train = [
      generate(frame=5, background=4, line_color=6, color2=2, color3=3,
               line=anti, dot=(0, 0), pattern2=xs, pattern3=plus),
      generate(frame=1, background=8, line_color=4, color2=2, color3=3,
               line=[(i, 2) for i in range(5)], dot=(2, 0), pattern2=xs,
               pattern3=plus),
      generate(frame=6, background=9, line_color=7, color2=4, color3=1,
               line=diag, dot=(4, 0),
               pattern2=['...##', '...##', '.....', '##...', '##...'],
               pattern3=['.#.#.', '#.#.#', '.#.#.', '#.#.#', '.#.#.']),
      generate(frame=4, background=0, line_color=1, color2=2, color3=3,
               line=[(2, j) for j in range(5)], dot=(0, 2), pattern2=xs,
               pattern3=plus),
  ]
  test = [
      generate(frame=2, background=5, line_color=8, color2=3, color3=7,
               line=[(0, 2), (1, 2), (2, 2), (2, 3), (2, 4)], dot=(0, 4),
               pattern2=['.#.#.', '##.##', '.....', '##.##', '.#.#.'],
               pattern3=['##.##', '#...#', '.....', '#...#', '##.##']),
  ]
  return {'train': train, 'test': test}
