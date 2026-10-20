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

"""Generator for ARC task 88bcf3b4 (snake re-routed around a target).

Rule: each scene has three parts.
  - Line: a straight bar of one colour.
  - Snake: a diagonally connected object of another colour. Its anchor cell
    sits beside one end of the line, perpendicular to the line.
  - Target: the non-line, non-snake object closest to the anchor, measured by
    Chebyshev distance.
In the output the line and the target stay put. The snake is erased and
redrawn as a path of the same colour and the same cell count. The path starts
at the anchor and advances one layer per cell past the line end, along the
line direction. Its sideways coordinate has three phases:
  - Approach: move at most one cell per step toward the cell just outside the
    target's first layer, on the snake's side.
  - Hug: inside the target layers, sit exactly one cell outside the target's
    outermost cell on that side.
  - Leave: after the target, drift back one cell per layer.
Path cells that fall outside the grid are dropped.

Scope:
  - Scenes: 1 to 3 independent scenes per grid; num_scenes requests a count.
    A sampled count is retained through retries. Automatic counts use minimum
    supplied sides of 7/12/18 for one/two/three scenes; explicit counts can
    request other feasible aspect ratios.
  - Orientation: each scene has a random line direction (4 choices) and a
    random snake side (2 choices).
  - Snake: a random 8-connected snake of 3..14 cells. It crawls backwards
    along the line and stays within the line's span, as in every fixture.
  - Line: length 2..9, and at least about half the snake length (fixtures
    use 4..7).
  - Target: a random 4-connected blob of up to 4 layers along the line and 4
    cells across. Its snake-side outline changes by at most one cell per layer.
  - Target offset: the hug column lies on the snake's side of the anchor or
    level with it on the first target layer. Its offset delta from the anchor
    is 0..5. Later shrinking target layers can take the hug across the line
    axis; targets may also touch the line end orthogonally. These geometries
    are synthetic extensions.
  - Gap: when delta > 0 the target starts exactly delta layers past the line
    end, so the approach is fully diagonal. This includes gap 1, where the
    target touches the anchor, as in pair 4 and test 1. Only delta = 0 scenes
    get a gap of 2..4, as in pair 1. The fixtures never decide between moving
    early or late when there is slack, so slack with a sideways move is never
    generated.
  - Snake length: always reaches at least one hug layer; the leave tail is
    0..5 cells (fixtures show 0..3; longer tails are a synthetic extension).
  - Clipping: paths may be clipped, but only at the far grid edge along the
    line direction.
  - Placement: about 80% of lines start at the grid border, as in every
    fixture. Floating lines are a minority synthetic extension.
  - Distractors: optional blobs, strictly farther from every anchor than that
    anchor's own target. Target identity is also required to agree under
    Manhattan and Euclidean distance, measured from the anchor, line end or
    whole snake, so generated examples do not depend on an unspecified metric.
  - Colours: background and object colours are random; the three colours of
    a scene are distinct, colours may repeat across scenes.
  - Grid size: 7..30 per side. Squares are favoured. Non-square grids, sizes
    beyond 27, distractors and floating lines are synthetic extensions.
  - Validity check: every random input is checked against an independent
    structural reading. That reading must find exactly the intended line ends
    with attached snakes, and a unique nearest target per anchor.
Explicit scene arguments reconstruct the original fixtures (structurally
checked for bounds, palette, connectivity and overlap, but rendered as supplied).
"""

import random

import common

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_STEPS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1))
_SIZES = {1: (7, 18), 2: (12, 26), 3: (18, 30)}


def _is_int(value):
  return isinstance(value, int) and not isinstance(value, bool)


def _cheb(point, cells):
  return min(max(abs(point[0] - r), abs(point[1] - c)) for r, c in cells)


def _nearest_is_robust(scene, others):
  """Reject synthetic target choices that depend on an unspecified metric."""
  origins = [(_anchor(scene),), (scene['end'],), scene['snake_cells']]
  target = scene['target_cells']
  for points in origins:
    for metric in ('chebyshev', 'manhattan', 'euclidean_squared'):
      def distance(cells):
        values = []
        for y, x in points:
          for r, c in cells:
            dy, dx = abs(y-r), abs(x-c)
            values.append(max(dy, dx) if metric == 'chebyshev' else
                          dy+dx if metric == 'manhattan' else dy*dy+dx*dx)
        return min(values)
      threshold = distance(target)
      if any(distance(cells) <= threshold for cells in others):
        return False
  return True


def _dilate(cells):
  return {(r + dr, c + dc) for r, c in cells
          for dr in (-1, 0, 1) for dc in (-1, 0, 1)}


def _line_cells(scene):
  er, ec = scene['end']
  dr, dc = scene['direction']
  return [(er - i * dr, ec - i * dc) for i in range(scene['length'])]


def _anchor(scene):
  return (scene['end'][0] + scene['side'][0],
          scene['end'][1] + scene['side'][1])


def _path(anchor, size, d, n, target_cells):
  """Cells of the redrawn snake path (unclipped), in grid coordinates."""
  def along(cell):
    return cell[0] * d[0] + cell[1] * d[1]

  def across(cell):
    return cell[0] * n[0] + cell[1] * n[1]

  side = {}
  for cell in target_cells:
    a = along(cell)
    side[a] = max(side.get(a, -10 ** 9), across(cell) + 1)
  amin, amax = min(side), max(side)
  a, q = along(anchor), across(anchor)
  points = [(a, q)]
  for _ in range(1, size):
    a += 1
    if a < amin:
      goal = side[amin]
      q += (goal > q) - (goal < q)
    elif a <= amax:
      q = side.get(a, q)
    else:
      q -= 1
    points.append((a, q))
  return [(a * d[0] + q * n[0], a * d[1] + q * n[1]) for a, q in points]


def _render(width, height, background, scenes, extras):
  grid = common.grid(width, height, background)
  for s in scenes:
    for r, c in _line_cells(s):
      grid[r][c] = s['line_colour']
    for r, c in s['snake_cells']:
      grid[r][c] = s['snake_colour']
    for r, c in s['target_cells']:
      grid[r][c] = s['target_colour']
  for colour, cells in extras:
    for r, c in cells:
      grid[r][c] = colour
  output = [row[:] for row in grid]
  for s in scenes:
    for r, c in s['snake_cells']:
      output[r][c] = background
    path = _path(_anchor(s), len(s['snake_cells']), s['direction'],
                 s['side'], s['target_cells'])
    for r, c in path:
      if 0 <= r < height and 0 <= c < width:
        output[r][c] = s['snake_colour']
  return {'input': grid, 'output': output}


def _components(grid, background):
  """Single-colour 8-connected components of non-background cells."""
  height, width = len(grid), len(grid[0])
  owner, comps = {}, []
  for r in range(height):
    for c in range(width):
      colour = grid[r][c]
      if colour == background or (r, c) in owner:
        continue
      index = len(comps)
      owner[(r, c)] = index
      stack, cells = [(r, c)], []
      while stack:
        y, x = stack.pop()
        cells.append((y, x))
        for dy in (-1, 0, 1):
          for dx in (-1, 0, 1):
            ny, nx = y + dy, x + dx
            if (0 <= ny < height and 0 <= nx < width and
                (ny, nx) not in owner and grid[ny][nx] == colour):
              owner[(ny, nx)] = index
              stack.append((ny, nx))
      comps.append((colour, frozenset(cells)))
  return comps, owner


def _reading_is_unique(grid, background, scenes):
  """True if the input admits exactly the intended line/snake/target reading.

  Every straight object (>= 2 cells) is inspected. A differently coloured
  object touching one of its ends perpendicularly counts as an attachment.
  The attachments must be exactly the intended line ends and snakes. Each
  anchor must then have a unique nearest remaining object, and that object
  must be its own target.
  """
  comps, owner = _components(grid, background)
  found = set()
  for i, (colour, cells) in enumerate(comps):
    if len(cells) < 2:
      continue
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    if len(cols) == 1:
      c0 = min(cols)
      ends = [((min(rows), c0), (-1, 0)), ((max(rows), c0), (1, 0))]
    elif len(rows) == 1:
      r0 = min(rows)
      ends = [((r0, min(cols)), (0, -1)), ((r0, max(cols)), (0, 1))]
    else:
      continue
    for (er, ec), (dr, dc) in ends:
      for nr, nc in ((dc, dr), (-dc, -dr)):
        cell = (er + nr, ec + nc)
        j = owner.get(cell)
        if j is not None and j != i and comps[j][0] != colour:
          found.add((i, j, cell))
  expected = set()
  for s in scenes:
    anchor = _anchor(s)
    li, si = owner.get(s['end']), owner.get(anchor)
    if li is None or si is None:
      return False
    if comps[li][1] != frozenset(_line_cells(s)):
      return False
    if comps[si][1] != frozenset(s['snake_cells']):
      return False
    expected.add((li, si, anchor))
  if found != expected:
    return False
  used = {i for i, _, _ in found} | {j for _, j, _ in found}
  for s in scenes:
    anchor = _anchor(s)
    dists = sorted((_cheb(anchor, comps[i][1]), i)
                   for i in range(len(comps)) if i not in used)
    if not dists:
      return False
    if len(dists) > 1 and dists[0][0] == dists[1][0]:
      return False
    if comps[dists[0][1]][1] != frozenset(s['target_cells']):
      return False
    if not _nearest_is_robust(
        s, [comps[i][1] for _, i in dists[1:]]):
      return False
  return True


def _blob(ha, hq, size):
  """Random 4-connected blob inside an ha x hq box, normalised to origin."""
  cells = {(random.randrange(ha), random.randrange(hq))}
  while len(cells) < size:
    frontier = sorted({(a + da, q + dq) for a, q in cells
                       for da, dq in ((1, 0), (-1, 0), (0, 1), (0, -1))
                       if 0 <= a + da < ha and 0 <= q + dq < hq} - cells)
    cells.add(random.choice(frontier))
  ma = min(a for a, _ in cells)
  mq = min(q for _, q in cells)
  return sorted((a - ma, q - mq) for a, q in cells)


def _snake_local(k, length):
  """Snake in local frame: anchor (0, 1), cells with 1-length <= a <= 0, q >= 1.

  The snake stays within the line's span, as in every fixture. It never sits
  perpendicular to the far end of the line.
  """
  low = 1 - length
  forbidden = (low, 1)
  for _ in range(100):
    cells = [(0, 1)]
    used = {(0, 1)}
    back = random.uniform(0.45, 0.85)
    drift = random.choice((-1, 0, 1, 1))
    while len(cells) < k:
      a, q = cells[-1]
      options, weights = [], []
      for da, dq in _STEPS:
        cell = (a + da, q + dq)
        if (cell[1] < 1 or cell[0] < low or cell in used or
            cell == forbidden):
          continue
        weight = back if da else 1.0 - back
        if dq == drift:
          weight *= 2.0
        options.append(cell)
        weights.append(weight)
      if not options:
        break
      cell = random.choices(options, weights)[0]
      cells.append(cell)
      used.add(cell)
    if len(cells) < k:
      continue
    if len({c[0] for c in cells}) < 2 or len({c[1] for c in cells}) < 2:
      continue
    return cells
  return None


def _scene_local():
  """Local frame: line on q = 0 ending at a = 0, path advances along +a."""
  ha, hq = random.randint(1, 4), random.randint(1, 4)
  shape = _blob(ha, hq, random.randint(1, min(10, ha * hq)))
  extent = max(a for a, _ in shape) + 1
  sides = [max(q for a, q in shape if a == layer) + 1
           for layer in range(extent)]
  if any(abs(sides[i + 1] - sides[i]) > 1 for i in range(extent - 1)):
    return None
  side_first = random.randint(1, 6)
  delta = side_first - 1
  # A sideways approach is always fully diagonal (gap == delta), as in every
  # fixture with delta > 0. Only straight approaches (delta == 0) get slack.
  gap = delta if delta > 0 else random.randint(2, 4)
  q_off = side_first - sides[0]
  target = [(gap + a, q_off + q) for a, q in shape]
  # Path has k cells: anchor, gap - 1 approach layers, hug layers, then a
  # leave tail of k - gap - extent cells (0..5 when not truncated by hugging).
  k = max(3, min(16, gap + random.randint(1, extent + 5)))
  lo = max(2, (k + 1) // 2)
  length = random.randint(lo, max(lo, 9))
  snake = _snake_local(k, length)
  if snake is None:
    return None
  return length, snake, target


def _place_scene(width, height, background, to_border):
  local = _scene_local()
  if local is None:
    return None
  length, snake, target = local
  d = random.choice(_DIRS)
  n = random.choice(((d[1], d[0]), (-d[1], -d[0])))

  def put(cell):
    return (cell[0] * d[0] + cell[1] * n[0], cell[0] * d[1] + cell[1] * n[1])

  line = [(-i, 0) for i in range(length)]
  cells = [put(c) for c in line + snake + target]
  rows = [r for r, _ in cells]
  cols = [c for _, c in cells]
  if max(rows) - min(rows) >= height or max(cols) - min(cols) >= width:
    return None
  oy = random.randint(-min(rows), height - 1 - max(rows))
  ox = random.randint(-min(cols), width - 1 - max(cols))
  if to_border:
    far = put((1 - length, 0))
    if d[0] == 1:
      oy = -far[0]
    elif d[0] == -1:
      oy = height - 1 - far[0]
    elif d[1] == 1:
      ox = -far[1]
    else:
      ox = width - 1 - far[1]
    if (min(rows) + oy < 0 or max(rows) + oy >= height or
        min(cols) + ox < 0 or max(cols) + ox >= width):
      return None

  def shift(cell):
    p = put(cell)
    return (p[0] + oy, p[1] + ox)

  colours = random.sample([c for c in range(10) if c != background], 3)
  scene = {
      'line_colour': colours[0], 'end': (oy, ox), 'direction': d,
      'length': length, 'side': n, 'snake_colour': colours[1],
      'snake_cells': [shift(c) for c in snake],
      'target_colour': colours[2],
      'target_cells': [shift(c) for c in target],
  }
  footprint = {(r + oy, c + ox) for r, c in cells}
  for r, c in _path(_anchor(scene), len(snake), d, n, scene['target_cells']):
    # Clipping is only allowed along the line direction (as in the fixtures);
    # the sideways coordinate of every path cell must stay inside the grid.
    cross, limit = (c, width) if d[0] else (r, height)
    if not 0 <= cross < limit:
      return None
    if 0 <= r < height and 0 <= c < width:
      footprint.add((r, c))
  return scene, footprint


def _sample(width, height, background, num_scenes):
  if num_scenes is not None:
    count = num_scenes
  else:
    supplied = [v for v in (width, height) if v is not None]
    options = [n for n in (1, 1, 1, 2, 2, 3)
               if not supplied or min(supplied) >= _SIZES[n][0]]
    count = random.choice(options)
  for attempt in range(500):
    lo, hi = _SIZES[count]
    h = height if height is not None else random.randint(lo, hi)
    if width is not None:
      w = width
    elif random.random() < 0.6:
      w = h
    else:
      w = random.randint(lo, hi)
    if background is not None:
      bg = background
    else:
      bg = 0 if random.random() < 0.5 else random.randint(1, 9)
    scenes, blocked = [], set()
    for _ in range(count):
      for _ in range(60):
        placed = _place_scene(w, h, bg, random.random() < 0.8)
        if placed is None:
          continue
        scene, footprint = placed
        if footprint & blocked:
          continue
        scenes.append(scene)
        blocked |= _dilate(footprint)
        break
    if len(scenes) < count:
      continue
    extras = []
    for _ in range(random.choice((0, 0, 1, 1, 2))):
      for _ in range(40):
        ha, hq = random.randint(1, 3), random.randint(1, 3)
        if ha > h or hq > w:
          continue
        shape = _blob(ha, hq, random.randint(1, min(5, ha * hq)))
        r0, c0 = random.randint(0, h - ha), random.randint(0, w - hq)
        cells = [(r0 + a, c0 + q) for a, q in shape]
        if any(c in blocked for c in cells):
          continue
        if not all(_nearest_is_robust(s, [cells]) for s in scenes):
          continue
        colour = random.choice([c for c in range(10) if c != bg])
        extras.append((colour, cells))
        blocked |= _dilate(cells)
        break
    grid = _render(w, h, bg, scenes, extras)['input']
    counts = [0] * 10
    for row in grid:
      for v in row:
        counts[v] += 1
    if any(counts[c] >= counts[bg] for c in range(10) if c != bg):
      continue
    if not _reading_is_unique(grid, bg, scenes):
      continue
    return w, h, bg, scenes, extras
  raise RuntimeError('could not sample a valid scene for the requested '
                     'size / scene count')


def _check_size_and_background(width, height, background):
  for name, value in (('width', width), ('height', height)):
    if value is not None and (not _is_int(value) or not 7 <= value <= 30):
      raise ValueError(name + ' must be an int in 7..30')
  if background is not None and (not _is_int(background) or
                                 not 0 <= background <= 9):
    raise ValueError('background must be an int in 0..9')


def _check_explicit(width, height, background, scenes, extras):
  """Structural checks for explicit (fixture replay) scenes."""
  if width is None or height is None or background is None:
    raise ValueError('explicit scenes need width, height and background')
  _check_size_and_background(width, height, background)
  if not isinstance(scenes, (list, tuple)) or not scenes:
    raise ValueError('explicit scenes must be a non-empty list')
  if not isinstance(extras, (list, tuple)):
    raise ValueError('extras must be a list of colour/cells pairs')

  def inside(cell):
    return (isinstance(cell, (list, tuple)) and len(cell) == 2 and
            _is_int(cell[0]) and _is_int(cell[1]) and
            0 <= cell[0] < height and 0 <= cell[1] < width)

  occupied = set()
  def check_cells(cells):
    if not isinstance(cells, (list, tuple)) or not cells or not all(inside(c) for c in cells):
      raise ValueError('objects need nonempty in-bounds cell pairs')
    points = {tuple(c) for c in cells}
    if len(points) != len(cells) or points & occupied:
      raise ValueError('object cells must be distinct and must not overlap')
    todo = set(points)
    stack = [todo.pop()]
    while stack:
      r, c = stack.pop()
      for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
          q = (r+dr, c+dc)
          if q in todo:
            todo.remove(q)
            stack.append(q)
    if todo:
      raise ValueError('objects must be 8-connected')
    occupied.update(points)

  required = {'line_colour', 'snake_colour', 'target_colour', 'end',
              'direction', 'side', 'length', 'snake_cells', 'target_cells'}
  for s in scenes:
    if not isinstance(s, dict) or not required.issubset(s):
      raise ValueError('scene is missing required fields')
    if not inside(s['end']):
      raise ValueError('line end must be an in-bounds cell pair')
    colours = (s['line_colour'], s['snake_colour'], s['target_colour'])
    if (any(not _is_int(c) or not 0 <= c <= 9 or c == background
            for c in colours) or len(set(colours)) != 3):
      raise ValueError('scene colours must be distinct ints in 0..9 and '
                       'differ from the background')
    if any(not isinstance(s[k], (list, tuple)) or len(s[k]) != 2
           or not all(_is_int(v) for v in s[k]) for k in ('direction', 'side')):
      raise ValueError('direction and side must be integer pairs')
    d, n = tuple(s['direction']), tuple(s['side'])
    if d not in _DIRS or n not in ((d[1], d[0]), (-d[1], -d[0])):
      raise ValueError('direction must be a unit step and side perpendicular')
    if not _is_int(s['length']) or s['length'] < 2:
      raise ValueError('line length must be an int >= 2')
    for cells in (_line_cells(s), s['snake_cells'], s['target_cells']):
      check_cells(cells)
    if _anchor(s) not in {tuple(c) for c in s['snake_cells']}:
      raise ValueError('the anchor (end + side) must be a snake cell')
  for item in extras:
    if not isinstance(item, (list, tuple)) or len(item) != 2:
      raise ValueError('extras must contain colour/cells pairs')
    colour, cells = item
    if not _is_int(colour) or not 0 <= colour <= 9 or colour == background:
      raise ValueError('extra colours must be non-background ints in 0..9')
    check_cells(cells)


def generate(width=None, height=None, background=None, num_scenes=None,
             scenes=None, extras=None):
  """Returns an input/output pair.

  Args:
    width: grid width, int 7..30 (sampled if None).
    height: grid height, int 7..30 (sampled if None).
    background: background colour, int 0..9 (sampled if None).
    num_scenes: number of line/snake/target scenes, int 1..3 (sampled if
      None). Small explicit sizes combined with 2 or 3 scenes may be
      infeasible. In that case RuntimeError is raised after a bounded number
      of attempts.
    scenes: optional explicit list of scene dicts with these keys:
      - line_colour.
      - end: (row, col) of the line end touching the snake.
      - direction: unit step pointing out of that end.
      - length.
      - side: unit step from the end to the snake anchor.
      - snake_colour.
      - snake_cells: including the anchor.
      - target_colour.
      - target_cells.
      When given, width, height and background are required. The scenes are
      checked for bounds, palette and geometry and then rendered as supplied
      (fixture replay; the nearest-target reading is not re-verified). If
      None, a fresh random layout is sampled.
    extras: optional list of (colour, cells) distractor objects. Only
      accepted together with explicit scenes.
  """
  if num_scenes is not None and (not _is_int(num_scenes) or
                                 num_scenes not in (1, 2, 3)):
    raise ValueError('num_scenes must be the int 1, 2 or 3')
  if scenes is None:
    if extras is not None:
      raise ValueError('extras can only be supplied with explicit scenes')
    _check_size_and_background(width, height, background)
    width, height, background, scenes, extras = _sample(
        width, height, background, num_scenes)
  else:
    extras = [] if extras is None else extras
    _check_explicit(width, height, background, scenes, extras)
    if num_scenes is not None and num_scenes != len(scenes):
      raise ValueError('num_scenes disagrees with the explicit scenes')
  return _render(width, height, background, scenes, extras)


def _s(line_colour, end, direction, length, side, snake_colour, snake_cells,
       target_colour, target_cells):
  return {'line_colour': line_colour, 'end': end, 'direction': direction,
          'length': length, 'side': side, 'snake_colour': snake_colour,
          'snake_cells': snake_cells, 'target_colour': target_colour,
          'target_cells': target_cells}


def validate():
  """Reconstructs the original task pairs from explicit latent scenes."""
  train = [
      generate(width=7, height=7, background=0, scenes=[
          _s(8, (3, 5), (-1, 0), 4, (0, -1), 4,
             [(3, 3), (3, 4), (4, 3), (5, 2), (5, 3), (6, 1)],
             2, [(1, 5)])]),
      generate(width=12, height=12, background=7, scenes=[
          _s(2, (5, 7), (-1, 0), 7, (0, -1), 3,
             [(5, 6), (6, 5), (7, 5), (8, 3), (8, 4)],
             4, [(0, 4), (1, 4), (2, 4)])]),
      generate(width=17, height=17, background=1, scenes=[
          _s(2, (6, 6), (1, 0), 7, (0, 1), 7,
             [(2, 12), (2, 13), (3, 12), (4, 11), (4, 12), (5, 8), (5, 9),
              (5, 10), (6, 7)],
             9, [(9, 9), (10, 9), (11, 9)])]),
      generate(width=10, height=10, background=0, scenes=[
          _s(5, (4, 4), (-1, 0), 6, (0, -1), 8,
             [(4, 3), (5, 3), (6, 2), (7, 2), (8, 1), (8, 2)],
             3, [(1, 3), (2, 2), (3, 3)])]),
      generate(width=9, height=9, background=0, scenes=[
          _s(6, (5, 5), (-1, 0), 4, (0, -1), 9,
             [(5, 4), (6, 3), (7, 0), (7, 1), (7, 2), (8, 0)],
             3, [(2, 3), (3, 3)])]),
  ]
  test = [
      generate(width=22, height=22, background=5, scenes=[
          _s(3, (8, 6), (0, 1), 7, (-1, 0), 8,
             [(1, 1), (2, 2), (3, 2), (4, 2), (5, 3), (6, 4), (7, 5),
              (7, 6)],
             9, [(4, 10), (4, 11), (5, 10), (5, 11), (5, 12), (6, 10),
                 (6, 11), (6, 12), (6, 13)]),
          _s(1, (18, 8), (-1, 0), 4, (0, -1), 4,
             [(18, 6), (18, 7), (19, 3), (19, 4), (19, 5), (20, 2)],
             6, [(17, 7)])]),
      generate(width=27, height=27, background=8, scenes=[
          _s(3, (5, 13), (1, 0), 6, (0, -1), 1,
             [(2, 7), (2, 8), (2, 9), (3, 9), (4, 9), (4, 10), (4, 11),
              (5, 12)],
             9, [(7, 13), (8, 13), (9, 13)]),
          _s(2, (14, 21), (0, -1), 6, (1, 0), 5,
             [(15, 21), (16, 22), (17, 22), (18, 22), (18, 23), (19, 23),
              (19, 24)],
             6, [(16, 16), (16, 17), (17, 17), (17, 18)]),
          _s(1, (22, 6), (-1, 0), 5, (0, -1), 4,
             [(22, 4), (22, 5), (23, 2), (23, 3), (23, 4), (24, 2)],
             5, [(19, 4), (19, 5), (19, 6), (20, 4), (20, 5), (20, 6)])]),
  ]
  return {'train': train, 'test': test}
