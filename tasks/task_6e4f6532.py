# Copyright 2026 Ritwika Kancharla
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0; you may not use this file
# except in compliance with the License. You may obtain a copy of the License
# at http://www.apache.org/licenses/LICENSE-2.0

"""ARC task 6e4f6532: dock marked ships onto matching 9 targets.

Rule: the grid is a background field with thick single-colour walls. Every
wall touches the grid border. Some walls are border strips and some are
internal dividers. Ships are 4-connected bodies of 8 that contain a core of
9 cells. Single marker cells, coloured like walls, are attached to the body.
Loose 9 blobs are targets.

In the output every ship and every target is erased. Each ship is then
rotated, or reflected if necessary, and stamped so that its core lies exactly
on the target of the same shape. The chosen orientation is the one in which
every marker, looking outward from the body cell it hangs on, sees a wall of
its own colour. Rotations are preferred over reflections when both fit.

Scope of random scenes:
- Size is 13..30 cells per side. Sizes other than the fixture sizes are
  synthetic extensions.
- Walls: two to four border strips, thickness 1 or 2, with randomised corner
  ownership. An optional internal divider reaches the border at an open end.
- Colours: background and wall colours are distinct colours from 0..7. Colours
  8 and 9 are reserved for ship bodies and cores.
- Ships: 1..6 ships, 2..4 by default. Each ship has a distinct core shape
  class: single, domino, diagonal pair, 2x2, L-tromino or I-tromino. Each has
  a randomly grown 8 body and 2..4 markers. A marker may touch multiple body
  cells; its outward ray uses down/up/right/left priority after orientation.
- Any of the 8 dihedral transforms can be the intended one.

Marker colours are derived from the wall each marker faces in the intended
docking. The generator rejects a ship if some other orientation gives a
different placement with an equal score. The one exception is a reflection
tying the intended rotation, because the rotation wins.

Explicit mode takes walls= and ships= together, with width, height and bg.
It reconstructs fixed scenes such as the canonical fixtures.
"""

import collections
import random

import common

TRANSFORMS = (
  lambda y, x: (y, x),
  lambda y, x: (x, -y),
  lambda y, x: (-y, -x),
  lambda y, x: (-x, y),
  lambda y, x: (y, -x),
  lambda y, x: (-x, -y),
  lambda y, x: (-y, x),
  lambda y, x: (x, y),
)
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
CORE_SHAPES = (
  ((0, 0),),
  ((0, 0), (0, 1)),
  ((0, 0), (1, 1)),
  ((0, 0), (0, 1), (1, 0), (1, 1)),
  ((0, 0), (1, 0), (1, 1)),
  ((0, 0), (0, 1), (0, 2)),
)
FRAME = 9
MIN_SIDE, MAX_SIDE = 13, 30


def _normalize(cells):
  cells = list(cells)
  my = min(r for r, _ in cells)
  mx = min(c for _, c in cells)
  return frozenset((r - my, c - mx) for r, c in cells)


def _parse(pattern):
  if (not pattern or not all(isinstance(row, str) for row in pattern)
      or not pattern[0] or any(len(row) != len(pattern[0]) for row in pattern)
      or any(ch not in '.0123456789' for row in pattern for ch in row)):
    raise ValueError('ship pattern must be a rectangle of digits and dots')
  cells = {}
  for r, row in enumerate(pattern):
    for c, ch in enumerate(row):
      if ch != '.':
        cells[(r, c)] = int(ch)
  if not {8, 9} <= set(cells.values()) or not _connected(cells):
    raise ValueError('ship must be 4-connected and contain body 8 and core 9')
  return cells


def _place(cells, t, dock):
  tf = TRANSFORMS[t]
  moved = {tf(r, c): v for (r, c), v in cells.items()}
  core = [p for p, v in moved.items() if v == 9]
  dy = dock[0] - min(r for r, _ in core)
  dx = dock[1] - min(c for _, c in core)
  return {(r + dy, c + dx): v for (r, c), v in moved.items()}


def _buffer(cells):
  out = set()
  for r, c in cells:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        out.add((r + dr, c + dc))
  return out


def _connected(cells):
  cells = set(cells)
  start = min(cells)
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr, dc in DIRS:
      q = (r + dr, c + dc)
      if q in cells and q not in seen:
        seen.add(q)
        stack.append(q)
  return len(seen) == len(cells)


def _ray(wallc, r, c, dr, dc):
  height, width = len(wallc), len(wallc[0])
  r, c = r + dr, c + dc
  while 0 <= r < height and 0 <= c < width and wallc[r][c] is None:
    r, c = r + dr, c + dc
  if 0 <= r < height and 0 <= c < width:
    return wallc[r][c]
  return None


def _score(placed, wallc):
  score = 0
  for (r, c), v in placed.items():
    if v in (8, 9):
      continue
    for dr, dc in DIRS:
      if placed.get((r - dr, c - dc)) in (8, 9):
        if _ray(wallc, r, c, dr, dc) == v:
          score += 1
        break
  return score


def _render(width, height, bg, walls, ships):
  base = common.grid(width, height, bg)
  for colour, r0, c0, r1, c1 in walls:
    for r in range(r0, r1 + 1):
      for c in range(c0, c1 + 1):
        base[r][c] = colour
  grid_in = [row[:] for row in base]
  grid_out = [row[:] for row in base]
  for pattern, (pr, pc), t, dock in ships:
    cells = _parse(pattern)
    for (r, c), v in cells.items():
      grid_in[pr + r][pc + c] = v
    for (r, c), v in _place(cells, t, dock).items():
      if v == 9:
        grid_in[r][c] = 9
      grid_out[r][c] = v
  return {'input': grid_in, 'output': grid_out}


def _wall_layout(width, height, bg, th, divider):
  for _ in range(20):
    n = random.choice((2, 3, 3, 4, 4))
    sides = set(random.sample(('top', 'bottom', 'left', 'right'), n))
    top, bottom = 'top' in sides, 'bottom' in sides
    left, right = 'left' in sides, 'right' in sides
    horiz_first = random.random() < 0.5
    rects = []
    c0 = 0 if horiz_first or not left else th
    c1 = width - 1 if horiz_first or not right else width - 1 - th
    if top:
      rects.append((0, c0, th - 1, c1))
    if bottom:
      rects.append((height - th, c0, height - 1, c1))
    r0 = 0 if not horiz_first or not top else th
    r1 = height - 1 if not horiz_first or not bottom else height - 1 - th
    if left:
      rects.append((r0, 0, r1, th - 1))
    if right:
      rects.append((r0, width - th, r1, width - 1))
    want = divider if divider is not None else random.random() < 0.45
    if want:
      options = []
      if not (top and bottom):
        options.append('v')
      if not (left and right):
        options.append('h')
      added = False
      if options:
        kind = random.choice(options)
        if kind == 'v':
          lx = th if left else 0
          rx = width - 1 - th if right else width - 1
          lo, hi = lx + 6, rx - th - 5
          if lo <= hi:
            cd = random.randint(lo, hi)
            ry0 = th if top else 0
            ry1 = height - 1 - th if bottom else height - 1
            rects.append((ry0, cd, ry1, cd + th - 1))
            added = True
        else:
          ty = th if top else 0
          by = height - 1 - th if bottom else height - 1
          lo, hi = ty + 6, by - th - 5
          if lo <= hi:
            rd = random.randint(lo, hi)
            cx0 = th if left else 0
            cx1 = width - 1 - th if right else width - 1
            rects.append((rd, cx0, rd + th - 1, cx1))
            added = True
      if not added and divider:
        continue
    pool = [c for c in range(8) if c != bg]
    colours = random.sample(pool, len(rects))
    return [(colours[i],) + rects[i] for i in range(len(rects))]
  return None


def _make_ship(core_id):
  for _ in range(40):
    tf = TRANSFORMS[random.randrange(8)]
    core = _normalize(tf(r, c) for r, c in CORE_SHAPES[core_id])
    core = {(r + 3, c + 3) for r, c in core}
    body = set(core)
    eights = set()
    goal = random.randint(4, 11)
    for _ in range(80):
      if len(eights) >= goal:
        break
      frontier = sorted({(r + dr, c + dc) for r, c in body for dr, dc in DIRS
                         if 1 <= r + dr <= FRAME - 2 and
                         1 <= c + dc <= FRAME - 2} - body)
      if not frontier:
        break
      cell = random.choice(frontier)
      body.add(cell)
      eights.add(cell)
    if len(eights) < 3 or not _connected(body):
      continue
    candidates = []
    for r in range(FRAME):
      for c in range(FRAME):
        if (r, c) in body:
          continue
        touching = sum((r + dr, c + dc) in body for dr, dc in DIRS)
        if touching >= 1:
          candidates.append((r, c))
    if len(candidates) < 2:
      continue
    markers = random.sample(candidates,
                            random.randint(2, min(4, len(candidates))))
    cells = {p: 9 for p in core}
    cells.update({p: 8 for p in eights})
    cells.update({p: -1 for p in markers})
    my = min(r for r, _ in cells)
    mx = min(c for _, c in cells)
    cells = {(r - my, c - mx): v for (r, c), v in cells.items()}
    markers = [(r - my, c - mx) for r, c in markers]
    return cells, markers
  return None


def _place_ship(shape, wallc, safe, blocked_in, blocked_out):
  cells, markers = shape
  height, width = len(wallc), len(wallc[0])
  ih = 1 + max(r for r, _ in cells)
  iw = 1 + max(c for _, c in cells)
  if height - 1 - ih < 1 or width - 1 - iw < 1:
    return None
  core = [p for p, v in cells.items() if v == 9]
  for _ in range(300):
    t = random.randrange(8)
    tf = TRANSFORMS[t]
    moved = {p: tf(p[0], p[1]) for p in cells}
    cy = min(moved[p][0] for p in core)
    cx = min(moved[p][1] for p in core)
    rel = {p: (moved[p][0] - cy, moved[p][1] - cx) for p in cells}
    rmin = min(v[0] for v in rel.values())
    rmax = max(v[0] for v in rel.values())
    cmin = min(v[1] for v in rel.values())
    cmax = max(v[1] for v in rel.values())
    if rmax - rmin > height - 1 or cmax - cmin > width - 1:
      continue
    pr = random.randint(1, height - 1 - ih)
    pc = random.randint(1, width - 1 - iw)
    src = [(pr + r, pc + c) for r, c in cells]
    if any(q not in safe or q in blocked_in for q in src):
      continue
    dr0 = random.randint(-rmin, height - 1 - rmax)
    dc0 = random.randint(-cmin, width - 1 - cmax)
    dst = {p: (dr0 + rel[p][0], dc0 + rel[p][1]) for p in cells}
    target = [dst[p] for p in core]
    own = _buffer(src)
    if any(q not in safe or q in blocked_in or q in own for q in target):
      continue
    if any(wallc[r][c] is not None or (r, c) in blocked_out
           for r, c in dst.values()):
      continue
    colours = {}
    moved_body = {dst[p] for p in cells if cells[p] in (8, 9)}
    for p in markers:
      q = dst[p]
      # Anchor priority is evaluated in the final orientation, not before
      # transforming. Those differ for markers with several body neighbours.
      direction = next((dr, dc) for dr, dc in DIRS
                       if (q[0] - dr, q[1] - dc) in moved_body)
      hit = _ray(wallc, q[0], q[1], *direction)
      if hit is None:
        break
      colours[p] = hit
    if len(colours) != len(markers):
      continue
    coloured = {p: colours.get(p, v) for p, v in cells.items()}
    dock = (dr0, dc0)
    intended = {dst[p]: coloured[p] for p in cells}
    shape_key = _normalize(target)
    clash = False
    for t2 in range(8):
      cand = _place(coloured, t2, dock)
      if _normalize(q for q, v in cand.items() if v == 9) != shape_key:
        continue
      if any(not (0 <= r < height and 0 <= c < width) for r, c in cand):
        continue
      if cand == intended:
        continue
      if _score(cand, wallc) >= len(markers) and not (t < 4 <= t2):
        clash = True
        break
    if clash:
      continue
    blocked_in.update(_buffer(src))
    blocked_in.update(_buffer(target))
    blocked_out.update(_buffer(dst.values()))
    rows = []
    for r in range(ih):
      rows.append(''.join(str(coloured[(r, c)]) if (r, c) in coloured else '.'
                          for c in range(iw)))
    return rows, (pr, pc), t, dock
  return None


def _random_scene(width, height, bg, num_ships, thickness, divider):
  h = height if height is not None else random.randint(MIN_SIDE, MAX_SIDE)
  w = width if width is not None else random.randint(MIN_SIDE, MAX_SIDE)
  b = bg if bg is not None else random.randrange(8)
  th = thickness if thickness is not None else random.choice((1, 2, 2, 2))
  walls = _wall_layout(w, h, b, th, divider)
  if walls is None:
    return None
  wallc = [[None] * w for _ in range(h)]
  for colour, r0, c0, r1, c1 in walls:
    for r in range(r0, r1 + 1):
      for c in range(c0, c1 + 1):
        wallc[r][c] = colour
  safe = set()
  for r in range(1, h - 1):
    for c in range(1, w - 1):
      if all(wallc[r + dr][c + dc] is None
             for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
        safe.add((r, c))
  open_area = sum(1 for row in wallc for v in row if v is None)
  if num_ships is None:
    k = random.randint(2, 3 if open_area < 400 else 4)
  else:
    k = num_ships
  core_ids = random.sample(range(len(CORE_SHAPES)), k)
  blocked_in, blocked_out = set(), set()
  specs = []
  for cid in core_ids:
    spec = None
    for _ in range(8):
      shape = _make_ship(cid)
      if shape is None:
        continue
      spec = _place_ship(shape, wallc, safe, blocked_in, blocked_out)
      if spec is not None:
        break
    if spec is None:
      return None
    specs.append(spec)
  pair = _render(w, h, b, walls, specs)
  counts = collections.Counter(v for row in pair['input'] for v in row)
  if any(n >= counts[b] for v, n in counts.items() if v != b):
    return None
  return pair


def _check_random_args(width, height, bg, num_ships, thickness, divider):
  for name, side in (('width', width), ('height', height)):
    if side is not None and not (type(side) is int and
                                 MIN_SIDE <= side <= MAX_SIDE):
      raise ValueError('%s must be an int in %d..%d for random scenes'
                       % (name, MIN_SIDE, MAX_SIDE))
  if bg is not None and (type(bg) is not int or bg not in range(8)):
    raise ValueError('bg must be in 0..7 (8 and 9 are ship colours)')
  if num_ships is not None and (type(num_ships) is not int or
                               num_ships not in range(1, len(CORE_SHAPES) + 1)):
    raise ValueError('num_ships must be in 1..%d' % len(CORE_SHAPES))
  if thickness is not None and (type(thickness) is not int or thickness not in (1, 2)):
    raise ValueError('thickness must be 1 or 2')
  if divider is not None and type(divider) is not bool:
    raise ValueError('divider must be True, False or None')
  if (divider is True and width is not None and height is not None
      and max(width, height) < 12 + 2 * (thickness or 1)):
    raise ValueError('grid too small for the requested internal divider')


def generate(width=None, height=None, bg=None, walls=None, ships=None,
             num_ships=None, thickness=None, divider=None):
  """Returns an input/output pair for task 6e4f6532.

  Args:
    width: grid width (columns). In random mode it is 13..30, chosen at
      random if None. It is required in explicit mode.
    height: grid height (rows). In random mode it is 13..30, chosen at random
      if None. It is required in explicit mode.
    bg: background colour. In random mode it is 0..7, chosen at random if
      None. It is required in explicit mode.
    walls: explicit list of (colour, r0, c0, r1, c1) inclusive rectangles,
      painted in order. Every rectangle must touch the grid border. Must be
      given together with ships.
    ships: explicit list of (pattern, (row, col), transform, (dock_row,
      dock_col)). pattern is a list of strings ('.' = empty, digits =
      colours) giving the ship as seen in the input, with its top-left at
      (row, col). transform indexes TRANSFORMS. The transformed core's
      minimum row/col is placed at the dock, which is also where the 9
      target is drawn in the input. Must be given together with walls.
    num_ships: number of ships in random mode (1..6, default 2..4). Large
      counts on small grids may exhaust the bounded retries.
    thickness: wall thickness in random mode (1 or 2; default random).
    divider: force (True) or forbid (False) an internal divider wall in
      random mode. None means random.
  """
  if walls is not None or ships is not None:
    if walls is None or ships is None:
      raise ValueError('walls and ships must be given together')
    if width is None or height is None or bg is None:
      raise ValueError('explicit scenes need width, height and bg')
    if num_ships is not None or thickness is not None or divider is not None:
      raise ValueError('num_ships/thickness/divider only apply to random '
                       'scenes')
    if (type(width) is not int or type(height) is not int
        or not 1 <= width <= 30 or not 1 <= height <= 30
        or type(bg) is not int or bg not in range(8)):
      raise ValueError('invalid explicit grid dimensions/background')
    wallc = [[None] * width for _ in range(height)]
    for colour, r0, c0, r1, c1 in walls:
      if (any(type(v) is not int for v in (colour, r0, c0, r1, c1))
          or colour not in range(8) or colour == bg):
        raise ValueError('walls require integer geometry and a distinct colour 0..7')
      if not (0 <= r0 <= r1 < height and 0 <= c0 <= c1 < width):
        raise ValueError('wall rectangle out of bounds')
      if not (r0 == 0 or c0 == 0 or r1 == height - 1 or c1 == width - 1):
        raise ValueError('wall rectangle does not touch the border')
      for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
          wallc[r][c] = colour
    input_used, output_used, core_classes = set(), set(), set()
    wall_colours = {colour for colour, _, _, _, _ in walls}
    for pattern, origin, t, dock in ships:
      if (type(t) is not int or t not in range(8)
          or len(origin) != 2 or len(dock) != 2
          or any(type(v) is not int for v in tuple(origin) + tuple(dock))):
        raise ValueError('ship transform/coordinates must be valid integers')
      cells = _parse(pattern)
      if any(c not in (8, 9) and c not in wall_colours for c in cells.values()):
        raise ValueError('marker colours must identify walls')
      placed = _place(cells, t, dock)
      source = {(origin[0] + r, origin[1] + c) for r, c in cells}
      target = {p for p, v in placed.items() if v == 9}
      for group in (source, set(placed)):
        if any(not (0 <= r < height and 0 <= c < width) for r, c in group):
          raise ValueError('ship source or docked cells out of bounds')
        if any(wallc[r][c] is not None for r, c in group):
          raise ValueError('ship overlaps a wall')
      if source & target or (source | target) & input_used or set(placed) & output_used:
        raise ValueError('ships or targets overlap')
      core = [q for q, v in cells.items() if v == 9]
      core_class = min(tuple(sorted(_normalize(tf(*q) for q in core)))
                       for tf in TRANSFORMS)
      if core_class in core_classes:
        raise ValueError('ship core classes must identify distinct targets')
      core_classes.add(core_class)
      target_key = _normalize(target)
      best = None
      for t2 in range(8):
        candidate = _place(cells, t2, dock)
        if _normalize(q for q, v in candidate.items() if v == 9) != target_key:
          continue
        if any(not (0 <= r < height and 0 <= c < width) for r, c in candidate):
          continue
        key = (_score(candidate, wallc), -t2)
        if best is None or key > best[0]:
          best = (key, candidate)
      if best is None or best[1] != placed:
        raise ValueError('chosen orientation does not satisfy marker selection')
      input_used.update(source | target)
      output_used.update(placed)
    return _render(width, height, bg, walls, ships)
  _check_random_args(width, height, bg, num_ships, thickness, divider)
  for _ in range(300):
    pair = _random_scene(width, height, bg, num_ships, thickness, divider)
    if pair is not None:
      return pair
  raise RuntimeError('could not construct a valid scene with these settings')


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
    generate(width=26, height=13, bg=5,
             walls=[(1, 0, 0, 12, 1), (4, 0, 12, 12, 13),
                    (2, 0, 24, 12, 25)],
             ships=[
               (['..4.', '.888', '8898', '...8', '.888', '.2.2'],
                (3, 4), 3, (3, 18)),
               (['1.1..', '8.8..', '88888', '8998.', '...4.'],
                (7, 17), 3, (5, 9)),
             ]),
    generate(width=26, height=26, bg=1,
             walls=[(2, 0, 0, 1, 25), (3, 24, 0, 25, 25),
                    (4, 2, 0, 23, 1), (7, 2, 24, 23, 25)],
             ships=[
               (['....88', '488888', '488988', '.22922'],
                (3, 14), 6, (11, 19)),
               (['77.7..', '88.8..', '88.883', '.898..', '.888..',
                 '.444..'], (10, 9), 1, (19, 6)),
             ]),
  ]
  test = [
    generate(width=28, height=30, bg=7,
             walls=[(4, 0, 0, 1, 27), (1, 2, 0, 29, 1),
                    (2, 2, 14, 29, 15), (3, 2, 26, 29, 27)],
             ships=[
               (['..8.88', '..8988', '488.88', '.3..33'],
                (3, 2), 7, (20, 20)),
               (['.4..', '.98.', '9881', '88..'], (7, 9), 4, (25, 4)),
               (['..1.....', '..88....', '...99884', '...998..',
                 '..8888..', '888..8..', '888..8..', '..8..88.',
                 '..2..22.'], (4, 18), 3, (18, 7)),
             ]),
    generate(width=16, height=30, bg=0,
             walls=[(3, 0, 0, 1, 15), (2, 28, 0, 29, 15),
                    (1, 2, 0, 27, 1), (7, 12, 2, 13, 15)],
             ships=[
               (['.1...', '28...', '.8998', '28998', '..888', '..8..'],
                (4, 4), 3, (17, 4)),
               (['898', '898', '888', '777'], (16, 10), 6, (24, 5)),
               (['......1', '..888.8', '7889888', '.888888'],
                (22, 7), 3, (6, 12)),
             ]),
  ]
  return {'train': train, 'test': test}
