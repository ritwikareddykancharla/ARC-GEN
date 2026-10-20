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

"""ARC task 4b6b68e5: fill closed outlines with their majority dot colour.

Rule:
  The background is black. Every connected same-colour piece of two or more
  cells is an outline (a wall). Every other coloured cell is an isolated dot.
  All dots are erased. A closed outline encloses an interior that cannot reach
  the grid border through non-wall cells. Each such interior is painted in the
  colour that occurs most often among the dots originally inside it. Open
  outlines have a gap in their boundary. They are left unfilled, and their
  dots are erased as well.

Scope:
  Random scenes have a width and height of 12..30. The fixtures span 14..26,
  so sizes 27..30 are a synthetic extension. An explicit width or height may
  be 8..30. Each scene has 1..6 outlines, each in its own colour, and at
  least one outline is closed. Each outline is the 8-neighbour boundary of a
  box from which rectangles are cut. There are 0..2 corner notches and an
  optional bite in the middle of one side. This gives L shapes, steps, plus
  shapes and dented shapes, as in the fixtures. An open outline loses a
  4-connected run of 1..5 boundary cells. The run starts on a straight side,
  so the interior is opened under 4-connectivity, and it may wrap round a
  corner. Dots come from a palette of 2..4 colours by default. Inside a
  closed outline the winning colour has 1..4 votes, which is a strict
  plurality, and it differs from the wall colour. A losing dot may share the
  wall colour, as in the test fixture. Open outlines get decoy dots, and
  there are further distractor dots outside every outline. Closed outlines
  without any dots can also occur; they remain unfilled.

  The original fixtures are replayed through the input_grid argument. In that
  path the walls, dots and enclosed regions are parsed from the grid and then
  drawn by the same renderer that the random path uses.
"""

import collections
import random

import common


_MIN_SIDE = 8
_MAX_SIDE = 30


def _components(cells):
  """Return the 4-connected components of a set of (row, col) cells."""
  cells = set(cells)
  seen = set()
  comps = []
  for start in sorted(cells):
    if start in seen:
      continue
    seen.add(start)
    stack = [start]
    comp = []
    while stack:
      r, c = stack.pop()
      comp.append((r, c))
      for nb in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
        if nb in cells and nb not in seen:
          seen.add(nb)
          stack.append(nb)
    comps.append(sorted(comp))
  return comps


def _flood_border(width, height, blocked):
  """Return the non-blocked cells that reach the border (4-connectivity)."""
  reached = set()
  stack = []
  for r in range(height):
    for c in range(width):
      if r in (0, height - 1) or c in (0, width - 1):
        if (r, c) not in blocked and (r, c) not in reached:
          reached.add((r, c))
          stack.append((r, c))
  while stack:
    r, c = stack.pop()
    for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
      if 0 <= nr < height and 0 <= nc < width:
        if (nr, nc) not in blocked and (nr, nc) not in reached:
          reached.add((nr, nc))
          stack.append((nr, nc))
  return reached


def _render(width, height, walls, fills):
  """Draw the walls and the filled interiors on an empty background."""
  out = common.grid(width, height, 0)
  for color, cells in walls:
    for r, c in cells:
      out[r][c] = color
  for color, cells in fills:
    for r, c in cells:
      out[r][c] = color
  return out


def _cut_cells(h, w, cut):
  """Return the box cells removed by one corner notch or side bite."""
  if cut[0] == 'corner':
    _, corner, dh, dw = cut
    rows = range(dh) if corner[0] == 't' else range(h - dh, h)
    cols = range(dw) if corner[1] == 'l' else range(w - dw, w)
  else:
    _, side, off, depth, span = cut
    if side == 't':
      rows, cols = range(depth), range(off, off + span)
    elif side == 'b':
      rows, cols = range(h - depth, h), range(off, off + span)
    elif side == 'l':
      rows, cols = range(off, off + span), range(depth)
    else:
      rows, cols = range(off, off + span), range(w - depth, w)
  return [(r, c) for r in rows for c in cols]


def _region(h, w, cuts):
  """Return an h x w box with the given rectangular cuts removed."""
  cells = set((r, c) for r in range(h) for c in range(w))
  for cut in cuts:
    for cell in _cut_cells(h, w, cut):
      cells.discard(cell)
  return cells


def _split(region):
  """Split a region into its 8-neighbour boundary and its interior."""
  outline, interior = set(), set()
  for r, c in region:
    if all((r + dr, c + dc) in region for dr in (-1, 0, 1)
           for dc in (-1, 0, 1)):
      interior.add((r, c))
    else:
      outline.add((r, c))
  return outline, interior


def _gap(outline, interior, region):
  """Choose a 4-connected run of outline cells to remove, opening the shape.

  The run is seeded on a straight side. One side of the seed is interior and
  the other side lies outside the region. The run then grows along the
  outline and may turn round corners.
  """
  seeds = set()
  for r, c in outline:
    for (a, b), (p, q) in (((1, 0), (0, 1)), ((0, 1), (1, 0))):
      if (r + a, c + b) in outline and (r - a, c - b) in outline:
        s1, s2 = (r + p, c + q), (r - p, c - q)
        if ((s1 in interior and s2 not in region) or
            (s2 in interior and s1 not in region)):
          seeds.add((r, c))
  if not seeds:
    return None
  gap = {random.choice(sorted(seeds))}
  size = random.choice([1, 1, 2, 2, 3, 4, 5])
  for _ in range(size - 1):
    frontier = set()
    for r, c in gap:
      for nb in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
        if nb in outline and nb not in gap:
          frontier.add(nb)
    if not frontier:
      break
    gap.add(random.choice(sorted(frontier)))
  return gap


def _try_shape(width, height, closed, boxes):
  """Try to place one outline shape. Return None if the attempt fails."""
  lo, hi = (5 if closed else 4), 11
  if height < lo or width < lo:
    return None
  h = random.randint(lo, min(hi, height))
  w = random.randint(lo, min(hi, width))
  r0 = random.randint(0, height - h)
  c0 = random.randint(0, width - w)
  for br, bc, bh, bw in boxes:
    if not (r0 > br + bh or r0 + h < br or c0 > bc + bw or c0 + w < bc):
      return None
  cuts = []
  for corner in random.sample(['tl', 'tr', 'bl', 'br'],
                              random.choice([0, 1, 1, 2])):
    if h >= 4 and w >= 4:
      cuts.append(('corner', corner, random.randint(1, h - 3),
                   random.randint(1, w - 3)))
  if random.random() < 0.35:
    side = random.choice('tblr')
    along, across = (w, h) if side in 'tb' else (h, w)
    if along >= 5 and across >= 6:
      off = random.randint(1, along - 3)
      span = random.randint(1, min(3, along - 1 - off))
      depth = random.randint(1, min(2, across - 5))
      cuts.append(('side', side, off, depth, span))
  local = _region(h, w, cuts)
  if not local or len(_components(local)) != 1:
    return None
  outline, interior = _split(local)
  if not interior or len(_components(interior)) != 1:
    return None
  if len(_components(outline)) != 1:
    return None
  if closed and len(interior) < 4:
    return None
  wall = set(outline)
  if not closed:
    gap = _gap(outline, interior, local)
    if gap is None:
      return None
    wall = outline - gap
    if len(wall) < max(4, len(gap) + 2) or len(_components(wall)) != 1:
      return None
  shift = lambda cells: set((r0 + r, c0 + c) for r, c in cells)
  return {'box': (r0, c0, h, w), 'region': shift(local), 'wall': shift(wall),
          'interior': shift(interior), 'closed': closed}


def _ok(g, dots, cell, color):
  """Check that a dot here stays a singleton and touches no other dot."""
  r, c = cell
  height, width = len(g), len(g[0])
  if g[r][c] != 0:
    return False
  for dr in (-1, 0, 1):
    for dc in (-1, 0, 1):
      nr, nc = r + dr, c + dc
      if (dr or dc) and 0 <= nr < height and 0 <= nc < width:
        if (nr, nc) in dots or g[nr][nc] == color:
          return False
  return True


def _place(g, dots, cells, color):
  """Place one dot of the given colour on a random valid cell."""
  options = [cell for cell in cells if _ok(g, dots, cell, color)]
  if not options:
    return False
  r, c = random.choice(options)
  g[r][c] = color
  dots.add((r, c))
  return True


def _check(width, height, num_shapes, num_closed, palette, num_empty_closed):
  """Reject explicit parameters that this generator cannot honour."""
  for name, value in (('width', width), ('height', height)):
    if value is not None and not _MIN_SIDE <= value <= _MAX_SIDE:
      raise ValueError(name + ' must be in 8..30')
  if num_shapes is not None and not 1 <= num_shapes <= 6:
    raise ValueError('num_shapes must be in 1..6')
  if num_closed is not None:
    if not 1 <= num_closed <= 6:
      raise ValueError('num_closed must be in 1..6')
    if num_shapes is not None and num_closed > num_shapes:
      raise ValueError('num_closed cannot exceed num_shapes')
  if num_empty_closed is not None:
    if not isinstance(num_empty_closed, int) or not 0 <= num_empty_closed <= 6:
      raise ValueError('num_empty_closed must be in 0..6')
    if ((num_closed is not None and num_empty_closed > num_closed) or
        (num_shapes is not None and num_empty_closed > num_shapes)):
      raise ValueError('empty closed count exceeds available shapes')
  if palette is not None:
    pal = list(palette)
    if (not pal or len(set(pal)) != len(pal) or
        any(not 1 <= c <= 9 for c in pal)):
      raise ValueError('palette must hold distinct colours in 1..9')


def _sample_scene(width, height, num_shapes, num_closed, palette, num_empty_closed=None):
  """Sample one random scene. Return None if a constraint is violated."""
  W = width if width is not None else random.randint(12, 30)
  H = height if height is not None else random.randint(12, 30)
  cap = max(1, min(6, (W * H) // 70))
  if num_shapes is not None:
    n = num_shapes
  else:
    lo = max(min(2, cap), num_closed or 1, num_empty_closed or 0)
    n = random.randint(lo, max(lo, cap))
  nc = num_closed if num_closed is not None else random.randint(max(1, num_empty_closed or 0), n)
  colours = random.sample(range(1, 10), n)
  flags = [True] * nc + [False] * (n - nc)
  random.shuffle(flags)
  ne = (num_empty_closed if num_empty_closed is not None else
        (random.randint(0, nc - 1) if random.random() < 0.3 else 0))
  empty = set(random.sample([i for i in range(n) if flags[i]], ne))
  if palette is not None:
    pal = list(palette)
  else:
    pal = random.sample(range(1, 10), random.randint(2, 4))
  for i in range(n):
    if flags[i] and i not in empty and all(c == colours[i] for c in pal):
      return None
  shapes, boxes = [], []
  for i in range(n):
    shape = None
    for _ in range(60):
      shape = _try_shape(W, H, flags[i], boxes)
      if shape is not None:
        break
    if shape is None:
      return None
    shape['color'] = colours[i]
    shape['empty'] = i in empty
    shapes.append(shape)
    boxes.append(shape['box'])
  g = common.grid(W, H, 0)
  walls = set()
  for s in shapes:
    for r, c in s['wall']:
      g[r][c] = s['color']
      walls.add((r, c))
  reached = _flood_border(W, H, walls)
  closed_int = set()
  for s in shapes:
    if s['closed']:
      if s['interior'] & reached:
        return None
      closed_int |= s['interior']
    elif not s['interior'] <= reached:
      return None
  unreached = set((r, c) for r in range(H) for c in range(W)
                  if (r, c) not in walls and (r, c) not in reached)
  if unreached != closed_int:
    return None
  dots = set()
  fills = []
  for s in shapes:
    inside = sorted(s['interior'])
    if s['closed']:
      if s['empty']:
        continue
      win = random.choice([c for c in pal if c != s['color']])
      limit = max(1, len(inside) // 5)
      kmax = min(4, limit)
      k = random.randint(min(2, kmax), kmax)
      votes = [win] * k
      if k >= 2:
        others = [c for c in pal if c != win]
        random.shuffle(others)
        for c in others:
          if len(votes) < limit and random.random() < 0.6:
            votes += [c] * random.randint(1, k - 1)
      random.shuffle(votes)
      for col in votes:
        if not _place(g, dots, inside, col):
          return None
      fills.append((win, s['interior']))
    elif random.random() < 0.75:
      for _ in range(random.randint(1, 3)):
        if not _place(g, dots, inside, random.choice(pal)):
          return None
  covered = set()
  for s in shapes:
    covered |= s['region']
  outside = [(r, c) for r in range(H) for c in range(W)
             if (r, c) not in covered]
  for _ in range(random.randint(2, 4 + (W * H) // 60)):
    _place(g, dots, outside, random.choice(pal))
  out = _render(W, H, [(s['color'], s['wall']) for s in shapes], fills)
  return {'input': g, 'output': out}


def _replay(grid):
  """Parse a fixture grid into walls, dots and interiors, then render it."""
  H, W = len(grid), len(grid[0])
  by_colour = collections.defaultdict(set)
  for r in range(H):
    for c in range(W):
      if grid[r][c] != 0:
        by_colour[grid[r][c]].add((r, c))
  walls, wall_cells, dots = [], set(), {}
  for col in sorted(by_colour):
    for comp in _components(by_colour[col]):
      if len(comp) >= 2:
        walls.append((col, comp))
        wall_cells.update(comp)
      else:
        dots[comp[0]] = col
  reached = _flood_border(W, H, wall_cells)
  free = set((r, c) for r in range(H) for c in range(W)
             if (r, c) not in wall_cells and (r, c) not in reached)
  fills = []
  for comp in _components(free):
    votes = collections.Counter(dots[cell] for cell in comp if cell in dots)
    if votes:
      fills.append((votes.most_common(1)[0][0], comp))
  return {'input': [list(row) for row in grid],
          'output': _render(W, H, walls, fills)}


def generate(width=None, height=None, num_shapes=None, num_closed=None,
             palette=None, input_grid=None, num_empty_closed=None):
  """Return one input/output pair for task 4b6b68e5.

  Args:
    width: grid width in 8..30, or None for a random 12..30.
    height: grid height in 8..30, or None for a random 12..30.
    num_shapes: number of outline shapes in 1..6, or None for random.
    num_closed: number of closed outlines, from 1 up to num_shapes, or None
      for random.
    palette: distinct dot colours in 1..9, or None for 2..4 random colours.
    num_empty_closed: exact number of closed outlines without dots, or None
      for occasional empty outlines. Empty interiors remain unfilled.
    input_grid: optional fixture grid to replay. This cannot be combined with
      the other arguments. Its walls, dots and enclosed regions are parsed and
      drawn with the same renderer.

  Raises:
    ValueError: if an explicit argument is out of range or inconsistent.
    RuntimeError: if the requested layout cannot be packed within the
      bounded number of attempts, for example too many shapes on a small grid.
  """
  if input_grid is not None:
    if any(v is not None for v in (width, height, num_shapes, num_closed,
                                   palette, num_empty_closed)):
      raise ValueError('input_grid cannot be combined with scene parameters')
    return _replay(input_grid)
  _check(width, height, num_shapes, num_closed, palette, num_empty_closed)
  for _ in range(500):
    scene = _sample_scene(width, height, num_shapes, num_closed, palette, num_empty_closed)
    if scene is not None:
      return scene
  raise RuntimeError('could not construct a scene with these parameters')


_FIXTURES = [
    ['000000222220000000', '002222200020000000', '002000003020066600',
     '002000000020060300', '002220300020060000', '000020000020066666',
     '000020008020000000', '000020000020000000', '000022222220000003',
     '000000000000000000', '008000000004444000', '000000044444004000',
     '000000040000004080', '300000048030804000', '000000040000004000',
     '000000040000804000', '000300044444004000', '000000000004444000',
     '000000000000000000'],
    ['000000000000000000000', '000002222222000000000',
     '000002000502000000000', '000222080002000000000',
     '000200000222000000000', '000208008200003333000',
     '000200000200003000000', '000222222200003080030',
     '000000000000003000030', '000000000000003000030',
     '000000111110003333330', '000011100810000000000',
     '000010050010000000000', '000010000010000000000',
     '000010505010000000000', '000010000010000000000',
     '000011111010000000000', '000000001110000000000',
     '000000000000000000000', '000000000000000000000',
     '000000000000000000000'],
    ['00000000000000', '00033333333000', '00030020003000',
     '03330000003000', '03000800803000', '03000000003000',
     '03330000003300', '00030600200300', '00030000000300',
     '00330000000300', '00300006000300', '00300603333300',
     '00300003000000', '00333333000000', '00000000000000',
     '00000000000000'],
    ['000000000000000000000000', '000222222200010033333301',
     '000200000222000030000300', '000206008002000030060300',
     '000200100002003330000300', '022200000012003000080300',
     '020010600002003800000300', '020000022222003000800300',
     '020000020000003000010300', '022222220000003000000300',
     '000000000001003333000300', '000100000000000003080300',
     '030000000000000003000300', '000000088888000003333300',
     '000000080008001000000000', '008888880808000030000000',
     '008000000008000000000001', '008040000308000000000000',
     '008000400008000777777700', '008030000408000700000700',
     '008000000008000702010700', '008008888008000700000700',
     '008888008888000701000000', '000000000000000777770000',
     '000003000000000000000000', '000000000010000000003000'],
]


def validate():
  """Rebuild the canonical fixtures by replaying their input grids."""
  pairs = []
  for rows in _FIXTURES:
    grid = [[int(ch) for ch in row] for row in rows]
    pairs.append(generate(input_grid=grid))
  return {'train': pairs[:3], 'test': pairs[3:]}
