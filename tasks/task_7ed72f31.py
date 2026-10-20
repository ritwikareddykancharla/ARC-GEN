# Copyright 2026 Ritwika Kancharla
# SPDX-License-Identifier: Apache-2.0
"""Generator for ARC task 7ed72f31: red mirrors reflect the shapes touching them.

Rule: the background is a single colour, and several single-coloured shapes sit on
it. Each shape is one diagonally connected component. Each shape touches exactly
one red (colour 2) mirror, where touching includes diagonal contact.
  * A single red cell is a point mirror. The shape is rotated 180 degrees about
    it: (y, x) -> (2r - y, 2c - x).
  * A straight red line of length >= 2 is a line mirror. The shape is reflected
    across that column (vertical line) or row (horizontal line).
Reflected cells are painted only onto background cells. They are clipped at the
grid border. The original shapes and mirrors stay unchanged.

Scope:
  * Rectangular grids, 12..30 per side when sampled; height and width are
    sampled independently. Explicit sizes of 10..30 are accepted for random
    scenes, and 1..30 for explicit object scenes. Sizes other than the fixture
    sizes (18x18, 28x28), including non-square grids, are synthetic extensions.
  * Any non-red background colour. The background is always the strict
    majority colour of the input, in random and explicit scenes alike.
  * 2..6 mirror/shape pairs by default. By default there is always at least one
    line mirror. With probability 0.15 a scene is line-only, as in the second
    training pair; otherwise it holds at least one point mirror and at least
    one line mirror. An explicit mirror_kinds list overrides this guarantee,
    so point-only scenes can be requested.
  * Shapes are random diagonally connected blobs:
    - Point-mirror shapes sit in one quadrant up to 3x3 (4x4 on large grids)
      away from the red cell, with optional on-axis cells. Every point-mirror
      shape has at least one off-axis cell.
    - Line-mirror shapes sit on one side, up to 4 deep (5 on large grids). They
      may overhang the line's extent by one row or column, as the 1-shape in
      test 2 does. Occasionally the shape grows from an overhang cell, so some
      shapes touch the line end only diagonally (synthetic extension).
  * Border clipping of reflections is a synthetic extension (no fixture
    reflection leaves the grid). It occurs occasionally, and at least half of
    each clipped reflection stays inside the grid.
  * Occlusion (synthetic extension): in about 20% of random scenes, or when
    occlusion=True, a reflection may land on another object's shape or mirror
    cells, which then stay unchanged. Input shapes are still never 8-adjacent
    to other shapes or foreign mirrors. Reflections of different colours never
    share a cell, and at least half of every in-grid reflection stays visible.
    Occlusion is only permitted, not forced, so many such scenes contain none.

Not supported: shapes touching two mirrors, multicoloured shapes, bent or
diagonal red mirrors (distinct mirrors are never 8-adjacent), and colliding
reflections of different colours. Explicit object scenes are checked for the
same semantic invariants the rule relies on (see generate).
"""

import random

import common


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _mirror_cells(mirror):
  kind = mirror[0]
  if kind == 'p':
    return [(mirror[1], mirror[2])]
  if kind == 'v':
    return [(y, mirror[1]) for y in range(mirror[2], mirror[3] + 1)]
  return [(mirror[1], x) for x in range(mirror[2], mirror[3] + 1)]


def _reflect(mirror, y, x):
  kind = mirror[0]
  if kind == 'p':
    return 2 * mirror[1] - y, 2 * mirror[2] - x
  if kind == 'v':
    return y, 2 * mirror[1] - x
  return 2 * mirror[1] - y, x


def _shift(mirror, dy, dx):
  kind = mirror[0]
  if kind == 'p':
    return ('p', mirror[1] + dy, mirror[2] + dx)
  if kind == 'v':
    return ('v', mirror[1] + dx, mirror[2] + dy, mirror[3] + dy)
  return ('h', mirror[1] + dy, mirror[2] + dx, mirror[3] + dx)


def _neighbours8(y, x):
  for a in (-1, 0, 1):
    for b in (-1, 0, 1):
      if a or b:
        yield y + a, x + b


def _connected(cells):
  """Returns True when the cell set is one 8-connected component."""
  cells = set(cells)
  if not cells:
    return False
  start = min(cells)
  seen = {start}
  stack = [start]
  while stack:
    y, x = stack.pop()
    for n in _neighbours8(y, x):
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _grow(cands, seeds, size):
  """Grows a random 8-connected cell set of the given size inside cands."""
  shape = {random.choice(seeds)}
  for _ in range(10 * size):
    if len(shape) >= size:
      break
    frontier = [c for c in sorted(cands) if c not in shape and any(
        abs(c[0] - a) <= 1 and abs(c[1] - b) <= 1 for a, b in shape)]
    if not frontier:
      break
    shape.add(random.choice(frontier))
  return sorted(shape)


def _local_object(kind, big):
  """Builds a mirror at the local origin plus a shape touching it."""
  if kind == 'p':
    reach = 4 if big else 3
    a, b = random.randint(1, reach), random.randint(1, reach)
    axes = random.random() < 0.35
    if not axes and a == 1 and b == 1:
      b = 2
    cands = set()
    for i in range(a + 1):
      for j in range(b + 1):
        if (i, j) != (0, 0) and (axes or (i >= 1 and j >= 1)):
          cands.add((i, j))
    seeds = [s for s in [(0, 1), (1, 0), (1, 1)] if s in cands]
    size = random.randint(2, min(len(cands), 12 if big else 9))
    shape = _grow(cands, seeds, size)
    if not any(i >= 1 and j >= 1 for i, j in shape):
      # Every seed is 8-adjacent to (1, 1), so adding it keeps the shape
      # connected and removes the on-axis (line-like) degeneracy.
      shape = sorted(set(shape) | {(1, 1)})
    sy, sx = random.choice([-1, 1]), random.choice([-1, 1])
    cells = [(sy * i, sx * j) for i, j in shape]
    return ('p', 0, 0), cells
  length = random.randint(2, 9 if big else 7)
  depth = random.randint(1, 5 if big else 4)
  over = 1 if random.random() < 0.3 else 0
  side = random.choice([-1, 1])
  cands = {(y, side * j) for y in range(-over, length + over)
           for j in range(1, depth + 1)}
  seeds = [(y, side) for y in range(length)]
  if over and random.random() < 0.4:
    # Overhang seeds touch the line end diagonally only.
    seeds = [(-1, side), (length, side)]
  size = random.randint(2, min(len(cands), 18 if big else 14))
  cells = _grow(cands, seeds, size)
  if kind == 'v':
    return ('v', 0, 0, length - 1), cells
  return ('h', 0, 0, length - 1), [(x, y) for y, x in cells]


def _pick_kinds(n):
  """Chooses mirror kinds: line-only with probability 0.15, else mixed."""
  if n == 1 or random.random() < 0.15:
    return [random.choice('vh') for _ in range(n)]
  kinds = [random.choice('pvh') for _ in range(n)]
  order = list(range(n))
  random.shuffle(order)
  kinds[order[0]] = random.choice('vh')
  kinds[order[1]] = 'p'
  return kinds


def _halo(cells):
  out = set()
  for y, x in cells:
    for a in (-1, 0, 1):
      for b in (-1, 0, 1):
        out.add((y + a, x + b))
  return out


def _place(kinds, h, w, palette, occlusion):
  """Places one object per kind; returns None on failure.

  Without occlusion, every footprint (inputs and reflections) keeps a one-cell
  gap from every other footprint. With occlusion, only input cells keep the
  gap; reflections may fall on other objects' input cells, and may share cells
  only with reflections of the same colour.
  """
  reserved = set()
  in_halo = set()
  painted = {}
  big = min(h, w) >= 22
  objects = []
  for kind in kinds:
    placed = False
    for _ in range(150):
      mirror, cells = _local_object(kind, big)
      inputs = _mirror_cells(mirror) + cells
      refl = [_reflect(mirror, y, x) for y, x in cells]
      clip = random.random() < 0.15
      box = inputs if clip else inputs + refl
      r0 = min(p[0] for p in box)
      r1 = max(p[0] for p in box)
      c0 = min(p[1] for p in box)
      c1 = max(p[1] for p in box)
      if r1 - r0 >= h or c1 - c0 >= w:
        continue
      if clip and random.random() < 0.5:
        dy = random.choice([-r0, h - 1 - r1])
      else:
        dy = random.randint(-r0, h - 1 - r1)
      if clip and random.random() < 0.5:
        dx = random.choice([-c0, w - 1 - c1])
      else:
        dx = random.randint(-c0, w - 1 - c1)
      ins = [(y + dy, x + dx) for y, x in inputs]
      rin = [(y + dy, x + dx) for y, x in refl
             if 0 <= y + dy < h and 0 <= x + dx < w]
      if not rin or 2 * len(rin) < len(refl):
        continue
      color = random.choice(palette)
      if occlusion:
        if any(p in in_halo for p in ins):
          continue
        if any(painted.get(p, color) != color for p in rin):
          continue
      else:
        if any(p in reserved for p in ins + rin):
          continue
      in_halo |= _halo(ins)
      reserved |= _halo(ins + rin)
      for p in rin:
        painted[p] = color
      objects.append({'mirror': _shift(mirror, dy, dx),
                      'color': color,
                      'cells': [(y + dy, x + dx) for y, x in cells]})
      placed = True
      break
    if not placed:
      return None
  return objects


def _visible_ok(h, w, objects):
  """Each reflection must keep >= 1 and >= half its in-grid cells visible."""
  in_cells = set()
  for o in objects:
    in_cells |= set(_mirror_cells(o['mirror'])) | set(o['cells'])
  for o in objects:
    rin = []
    for y, x in o['cells']:
      ny, nx = _reflect(o['mirror'], y, x)
      if 0 <= ny < h and 0 <= nx < w:
        rin.append((ny, nx))
    vis = [p for p in rin if p not in in_cells]
    if not vis or 2 * len(vis) < len(rin):
      return False
  return True


def _random_scene(width, height, background, num_mirrors, mirror_kinds,
                  occlusion):
  fixed_n = len(mirror_kinds) if mirror_kinds is not None else num_mirrors
  for _ in range(200):
    h = w = None
    for _ in range(50):
      h = height if height is not None else random.randint(12, 30)
      w = width if width is not None else random.randint(12, 30)
      if fixed_n is None or 40 * fixed_n <= h * w:
        break
    else:
      h = height if height is not None else 30
      w = width if width is not None else 30
    if background is not None:
      bg = background
    else:
      bg = random.choice([c for c in range(10) if c != 2])
    palette = [c for c in range(10) if c not in (bg, 2)]
    if mirror_kinds is not None:
      kinds = list(mirror_kinds)
    else:
      if num_mirrors is not None:
        n = num_mirrors
      else:
        n = random.randint(2, max(2, min(6, h * w // 70)))
      kinds = _pick_kinds(n)
    occ = occlusion if occlusion is not None else random.random() < 0.2
    objects = _place(kinds, h, w, palette, occ)
    if objects is None:
      continue
    if not _visible_ok(h, w, objects):
      continue
    nonbg = sum(len(_mirror_cells(o['mirror'])) + len(o['cells'])
                for o in objects)
    if 2 * nonbg >= h * w:
      continue
    return h, w, bg, objects
  raise ValueError('could not place the requested mirrors in the grid')


def _render(width, height, background, objects):
  inp = common.grid(width, height, background)
  for obj in objects:
    for y, x in _mirror_cells(obj['mirror']):
      inp[y][x] = 2
    for y, x in obj['cells']:
      inp[y][x] = obj['color']
  out = [row[:] for row in inp]
  for obj in objects:
    for y, x in obj['cells']:
      ny, nx = _reflect(obj['mirror'], y, x)
      if 0 <= ny < height and 0 <= nx < width and out[ny][nx] == background:
        out[ny][nx] = obj['color']
  return {'input': inp, 'output': out}


def _check_objects(width, height, background, objects):
  """Validates an explicit scene and returns it in normalised form."""
  if not isinstance(objects, (list, tuple)) or not objects:
    raise ValueError('explicit scene needs a non-empty list of objects')
  norm = []
  red = {}
  for k, obj in enumerate(objects):
    if not isinstance(obj, dict) or set(obj) != {'mirror', 'color', 'cells'}:
      raise ValueError('each object needs exactly mirror, color and cells')
    mirror = tuple(obj['mirror'])
    if not mirror or mirror[0] not in ('p', 'v', 'h'):
      raise ValueError('unknown mirror kind')
    if len(mirror) != (3 if mirror[0] == 'p' else 4):
      raise ValueError('malformed mirror tuple')
    if not all(_is_int(v) for v in mirror[1:]):
      raise ValueError('mirror coordinates must be integers')
    if mirror[0] != 'p' and not mirror[2] < mirror[3]:
      raise ValueError('line mirrors need length >= 2 (use p for one cell)')
    color = obj['color']
    if not _is_int(color) or not 0 <= color <= 9:
      raise ValueError('shape colour must be 0..9')
    if color in (2, background):
      raise ValueError('shape colour collides with red or background')
    cells = []
    for c in obj['cells']:
      c = tuple(c)
      if len(c) != 2 or not _is_int(c[0]) or not _is_int(c[1]):
        raise ValueError('cells must be integer (row, col) pairs')
      cells.append(c)
    if not cells or len(set(cells)) != len(cells):
      raise ValueError('shape cells must be non-empty and distinct')
    for y, x in _mirror_cells(mirror) + cells:
      if not (0 <= y < height and 0 <= x < width):
        raise ValueError('object cell outside the grid')
    for c in _mirror_cells(mirror):
      if c in red:
        raise ValueError('mirrors overlap')
      red[c] = k
    norm.append({'mirror': mirror, 'color': color, 'cells': cells})
  for (y, x), k in red.items():
    for n in _neighbours8(y, x):
      if n in red and red[n] != k:
        raise ValueError('distinct mirrors touch (merged or diagonal mirror)')
  owner = {}
  for k, obj in enumerate(norm):
    if not _connected(obj['cells']):
      raise ValueError('shape is not 8-connected')
    for c in obj['cells']:
      if c in red or c in owner:
        raise ValueError('shape overlaps a mirror or another shape')
      owner[c] = k
  for (y, x), k in owner.items():
    for n in _neighbours8(y, x):
      if n in owner and owner[n] != k:
        raise ValueError('distinct shapes would merge into one component')
      if n in red and red[n] != k:
        raise ValueError('shape touches a mirror that is not its own')
  for k, obj in enumerate(norm):
    if not any(red.get(n) == k for y, x in obj['cells']
               for n in _neighbours8(y, x)):
      raise ValueError('shape does not touch its mirror')
  if 2 * (len(red) + len(owner)) >= width * height:
    raise ValueError('background must be the strict majority colour')
  painted = {}
  for obj in norm:
    for y, x in obj['cells']:
      ny, nx = _reflect(obj['mirror'], y, x)
      if not (0 <= ny < height and 0 <= nx < width):
        continue
      if (ny, nx) in red or (ny, nx) in owner:
        continue
      if painted.get((ny, nx), obj['color']) != obj['color']:
        raise ValueError('reflections of different colours collide')
      painted[(ny, nx)] = obj['color']
  if not painted:
    raise ValueError('scene paints nothing (identity pair)')
  return norm


def generate(width=None, height=None, background=None, objects=None,
             num_mirrors=None, mirror_kinds=None, occlusion=None):
  """Returns an input/output pair for task 7ed72f31.

  Args:
    width: grid width. Sampled from 12..30; an explicit value must be an int
      in 10..30 for random scenes, or 1..30 with explicit objects.
    height: grid height. Same ranges as width; sampled independently.
    background: background colour 0..9, never 2. Sampled when None.
    objects: optional explicit scene, given as a list of dicts with keys
      'mirror', 'color' and 'cells'.
      'mirror' is one of ('p', r, c), ('v', col, r0, r1) or ('h', row, c0, c1)
      with r0 < r1 or c0 < c1 for line mirrors.
      'color' is the shape colour.
      'cells' lists the absolute (row, col) cells of the shape.
      The scene is rejected (ValueError) unless every shape is 8-connected,
      disjoint from all red cells, touches its own mirror and no other, and
      is not 8-adjacent to another shape; distinct mirrors are not
      8-adjacent; the background is the strict majority colour; no two
      reflections of different colours land on the same background cell; and
      at least one cell is painted. When objects is given, width, height and
      background are required, and num_mirrors, mirror_kinds and occlusion
      must be None.
    num_mirrors: optional number of mirror/shape pairs (1..8) for random
      scenes. Restricted to 40 canvas cells per object (a conservative sampler cap);
      raises ValueError if they still cannot be placed.
    mirror_kinds: optional list of 'p', 'v' or 'h', one per pair. This fixes
      both the count and the kinds of mirrors in random scenes, and overrides
      the default at-least-one-line-mirror guarantee.
    occlusion: optional bool for random scenes. True allows reflections to
      fall on other objects (which then stay unchanged); False keeps every
      footprint separated. Sampled (True with probability 0.2) when None.
  """
  if background is not None and (not _is_int(background) or
                                 background == 2 or
                                 not 0 <= background <= 9):
    raise ValueError('background must be a colour 0..9 other than red (2)')
  for v in (width, height):
    if v is not None and not _is_int(v):
      raise ValueError('grid sides must be integers')
  if occlusion is not None and not isinstance(occlusion, bool):
    raise ValueError('occlusion must be None, True or False')
  if objects is not None:
    if width is None or height is None or background is None:
      raise ValueError('explicit objects need width, height and background')
    if (num_mirrors is not None or mirror_kinds is not None or
        occlusion is not None):
      raise ValueError('num_mirrors/mirror_kinds/occlusion conflict with '
                       'objects')
    for v in (width, height):
      if not 1 <= v <= 30:
        raise ValueError('grid sides must be 1..30')
    norm = _check_objects(width, height, background, objects)
    return _render(width, height, background, norm)
  for v in (width, height):
    if v is not None and not 10 <= v <= 30:
      raise ValueError('grid sides must be 10..30 for random scenes')
  if mirror_kinds is not None:
    if (not isinstance(mirror_kinds, (list, tuple)) or
        not 1 <= len(mirror_kinds) <= 8 or
        any(k not in ('p', 'v', 'h') for k in mirror_kinds)):
      raise ValueError('mirror_kinds must list 1..8 of p, v, h')
    if num_mirrors is not None and num_mirrors != len(mirror_kinds):
      raise ValueError('num_mirrors disagrees with mirror_kinds')
  if num_mirrors is not None and (not _is_int(num_mirrors) or
                                  not 1 <= num_mirrors <= 8):
    raise ValueError('num_mirrors must be an int 1..8')
  fixed_n = len(mirror_kinds) if mirror_kinds is not None else num_mirrors
  if fixed_n is not None:
    max_area = (height if height is not None else 30) * (
        width if width is not None else 30)
    if 40 * fixed_n > max_area:
      raise ValueError('too many mirrors for the requested grid size')
  height, width, background, objects = _random_scene(
      width, height, background, num_mirrors, mirror_kinds, occlusion)
  return _render(width, height, background, objects)


def _o(mirror, color, cells):
  return {'mirror': mirror, 'color': color, 'cells': cells}


def validate():
  """Reconstructs the canonical train and test pairs from latent objects."""
  train = [
      generate(18, 18, 1, [
          _o(('p', 4, 5), 3, [(2, 4), (3, 3), (3, 4)]),
          _o(('v', 14, 5, 8), 4,
             [(5, 11), (5, 12), (6, 12), (6, 13), (7, 13), (8, 13)]),
          _o(('p', 11, 6), 5, [(11, 7), (12, 6), (12, 7), (13, 8)]),
          _o(('h', 15, 11, 15), 8,
             [(13, 13), (14, 11), (14, 12), (14, 14), (14, 15)]),
      ]),
      generate(18, 18, 8, [
          _o(('v', 4, 3, 6), 4,
             [(3, 5), (3, 6), (3, 7), (4, 5), (4, 7), (5, 5), (5, 6),
              (5, 7), (6, 5)]),
          _o(('v', 13, 3, 4), 1, [(3, 11), (3, 12), (4, 12)]),
          _o(('h', 11, 8, 11), 3,
             [(8, 10), (9, 9), (9, 11), (10, 8), (10, 9), (10, 11)]),
      ]),
  ]
  test = [
      generate(18, 18, 8, [
          _o(('p', 4, 11), 4,
             [(1, 12), (1, 13), (2, 12), (2, 13), (2, 14), (3, 12),
              (3, 13), (3, 14)]),
          _o(('p', 7, 3), 1, [(8, 0), (8, 1), (8, 2), (9, 2), (10, 2)]),
          _o(('h', 13, 7, 12), 3,
             [(14, 7), (14, 8), (14, 9), (14, 10), (14, 11), (14, 12),
              (15, 8), (15, 9), (15, 11), (16, 9), (16, 10), (17, 11)]),
      ]),
      generate(28, 28, 3, [
          _o(('p', 2, 19), 1,
             [(0, 17), (0, 18), (0, 19), (1, 17), (1, 18), (2, 17)]),
          _o(('h', 6, 6, 10), 4,
             [(3, 8), (3, 9), (3, 10), (4, 6), (4, 7), (4, 8), (4, 10),
              (5, 6), (5, 9)]),
          _o(('v', 19, 9, 14), 8,
             [(9, 20), (10, 20), (10, 21), (11, 20), (11, 22), (12, 20),
              (12, 21), (12, 22), (13, 22), (14, 20), (14, 21)]),
          _o(('p', 12, 11), 8,
             [(13, 9), (13, 10), (14, 8), (14, 9), (14, 10), (15, 9)]),
          _o(('v', 4, 17, 20), 1,
             [(17, 6), (18, 5), (19, 5), (20, 5), (20, 6), (21, 6)]),
          _o(('p', 20, 23), 6,
             [(17, 21), (18, 20), (18, 22), (19, 21), (19, 22)]),
          _o(('p', 25, 16), 4, [(23, 18), (24, 17)]),
      ]),
  ]
  return {'train': train, 'test': test}
