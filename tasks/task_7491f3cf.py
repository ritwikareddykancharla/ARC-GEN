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
draws the dividers between four square NxN panels laid out in a row. All four
panels share one fill colour.

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
  * Wall shapes: a straight row or column, a main diagonal, an L shape that
    cuts off a corner, or a random monotone 8-connected path. Any of these
    can be reflected or transposed.
  * Dot: it is placed in a randomly chosen region, away from the wall.
  * Patterns: they come from a parametric motif family: X, plus,
    checkerboard, corner blocks, corner L's, stripes, ring, diamond, random
    four-fold symmetric, and fully random.
  * Panel size: 5 is the size of every original example and the most likely
    choice. Panel sizes 4 and 6 are synthetic extensions, giving grids of
    6x21 and 8x29. Panels are always square.

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

MIN_SIZE, MAX_SIZE = 4, 6
SIZE_WEIGHTS = {4: 1, 5: 3, 6: 1}


def _parse(rows):
  n = len(rows)
  cells = set()
  for r, row in enumerate(rows):
    if len(row) != n or any(ch not in '#.' for ch in row):
      raise ValueError('patterns must be square lists of "#"/"." strings')
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


def _regions(n, wall):
  seen = set()
  regs = []
  for r in range(n):
    for c in range(n):
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
          if (0 <= q[0] < n and 0 <= q[1] < n and q not in wall
              and q not in seen):
            seen.add(q)
            stack.append(q)
      regs.append(reg)
  return regs


def _wall_regions(n, wall):
  """Returns the two regions cut by a valid wall, else None."""
  if len(wall) < 2:
    return None
  if any(not (0 <= r < n and 0 <= c < n) for r, c in wall):
    return None
  if not _connected8(wall):
    return None
  regs = _regions(n, wall)
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


def _sample_line(n):
  kind = random.choices(['straight', 'diagonal', 'ell', 'path'],
                        weights=[2, 1, 3, 4])[0]
  if kind == 'straight':
    k = random.randint(1, n - 2)
    cells = {(k, c) for c in range(n)}
  elif kind == 'diagonal':
    cells = {(i, i) for i in range(n)}
  elif kind == 'ell':
    r = random.randint(1, n - 2)
    c = random.randint(1, n - 2)
    rows = range(0, r + 1) if random.random() < 0.5 else range(r, n)
    cols = range(0, c + 1) if random.random() < 0.5 else range(c, n)
    cells = {(i, c) for i in rows} | {(r, j) for j in cols}
  else:
    col = random.randint(0, n - 1)
    cells = {(0, col)}
    for row in range(1, n):
      col += random.choice([d for d in (-1, 0, 1) if 0 <= col + d < n])
      cells.add((row, col))
  if random.random() < 0.5:
    cells = {(c, r) for r, c in cells}
  if random.random() < 0.5:
    cells = {(r, n - 1 - c) for r, c in cells}
  return cells


def _mirror(cells, n):
  out = set()
  for r, c in cells:
    out |= {(r, c), (r, n - 1 - c), (n - 1 - r, c), (n - 1 - r, n - 1 - c)}
  return out


def _sample_pattern(n):
  m = n // 2
  kind = random.choice(['x', 'plus', 'checker', 'blocks', 'ells', 'stripes',
                        'ring', 'diamond', 'sym', 'sym', 'random'])
  allc = [(r, c) for r in range(n) for c in range(n)]
  if kind == 'x':
    return {(i, i) for i in range(n)} | {(i, n - 1 - i) for i in range(n)}
  if kind == 'plus':
    r0 = random.randint(1, n - 2)
    c0 = random.randint(1, n - 2)
    return {(r0, j) for j in range(n)} | {(i, c0) for i in range(n)}
  if kind == 'checker':
    ph = random.randint(0, 1)
    return {(r, c) for r, c in allc if (r + c) % 2 == ph}
  if kind == 'blocks':
    corners = [(0, 0), (0, n - 2), (n - 2, 0), (n - 2, n - 2)]
    chosen = random.sample(corners, random.randint(1, 4))
    cells = set()
    for r0, c0 in chosen:
      cells |= {(r0 + a, c0 + b) for a in (0, 1) for b in (0, 1)}
    return cells
  if kind == 'ells':
    return _mirror({(0, 0), (0, 1), (1, 0)}, n)
  if kind == 'stripes':
    step = random.choice([2, 3])
    ph = random.randint(0, step - 1)
    cells = {(r, c) for r, c in allc if r % step == ph}
    if random.random() < 0.5:
      cells = {(c, r) for r, c in cells}
    return cells
  if kind == 'ring':
    return {(r, c) for r, c in allc if r in (0, n - 1) or c in (0, n - 1)}
  if kind == 'diamond':
    k = random.randint(1, m)
    return {(r, c) for r, c in allc if abs(r - m) + abs(c - m) == k}
  if kind == 'sym':
    quad = {(r, c) for r in range((n + 1) // 2) for c in range((n + 1) // 2)
            if random.random() < 0.4}
    return _mirror(quad, n)
  return {cell for cell in allc if random.random() < 0.3}


def _colours(given):
  used = [v for v in given if v is not None]
  pool = [v for v in range(10) if v not in used]
  random.shuffle(pool)
  return [v if v is not None else pool.pop() for v in given]


def _resolve_size(panel_size, line, dot, pattern2, pattern3):
  if panel_size is not None and type(panel_size) is not int:
    raise ValueError('panel_size must be an integer')
  for point in list(line or []) + ([] if dot is None else [dot]):
    if len(point) != 2 or any(type(v) is not int for v in point):
      raise ValueError('line and dot coordinates must be integer pairs')
  sizes = set()
  if panel_size is not None:
    sizes.add(panel_size)
  for p in (pattern2, pattern3):
    if p is not None:
      sizes.add(len(p))
  if len(sizes) > 1:
    raise ValueError('panel_size and pattern sizes disagree')
  coords = [v for p in (line or []) for v in p] + list(dot or [])
  if any(v < 0 for v in coords):
    raise ValueError('coordinates must be non-negative')
  lo = max([MIN_SIZE] + [v + 1 for v in coords])
  if sizes:
    n = sizes.pop()
    if not MIN_SIZE <= n <= MAX_SIZE or n < lo:
      raise ValueError('panel size out of range or too small for line/dot')
    return n, [n]
  options = [s for s in range(MIN_SIZE, MAX_SIZE + 1) if s >= lo]
  if not options:
    raise ValueError('line/dot coordinates exceed the largest panel size')
  return None, options


def generate(frame=None, background=None, line_color=None, color2=None,
             color3=None, line=None, dot=None, pattern2=None, pattern3=None,
             panel_size=None, wall_evidence=None):
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
    pattern2: list of N strings with '#' for pattern cells of panel 2.
    pattern3: list of N strings with '#' for pattern cells of panel 3.
    panel_size: side length N of each square panel (4..6; 5 in all originals).
    wall_evidence: True requires wall cells where both patterns overlap and
      cells where only panel 3 contributes. None requires this on half of
      unconstrained calls; False allows either branch to be absent.
  """
  given = [frame, background, line_color, color2, color3]
  supplied = [v for v in given if v is not None]
  if any(type(v) is not int or not 0 <= v <= 9 for v in supplied):
    raise ValueError('colours must be integers 0..9')
  if len(set(supplied)) != len(supplied):
    raise ValueError('the five colours must be distinct')
  n_fixed, size_options = _resolve_size(panel_size, line, dot, pattern2,
                                        pattern3)
  fixed_line = None if line is None else {tuple(p) for p in line}
  fixed_dot = None if dot is None else tuple(dot)
  fixed_p2 = None if pattern2 is None else _parse(pattern2)
  fixed_p3 = None if pattern3 is None else _parse(pattern3)
  geom_fixed = fixed_line is not None and n_fixed is not None
  dot_fixed = geom_fixed and fixed_dot is not None
  all_fixed = dot_fixed and fixed_p2 is not None and fixed_p3 is not None
  if wall_evidence is not None and type(wall_evidence) is not bool:
    raise ValueError('wall_evidence must be bool or None')
  require_wall = wall_evidence if wall_evidence is not None else (
      not all_fixed and random.random() < 0.5)
  if fixed_line is not None:
    size_options = [n for n in size_options if _wall_regions(n, fixed_line)
                    and (fixed_dot is None or not _near(fixed_dot, fixed_line))]
    if not size_options:
      raise ValueError('line/dot cannot form a valid partition at any allowed size')

  for _ in range(400):
    n = n_fixed if n_fixed is not None else random.choices(
        size_options, weights=[SIZE_WEIGHTS[s] for s in size_options])[0]
    f, bg, lc, c2, c3 = _colours(given)
    wall = set(fixed_line) if fixed_line is not None else _sample_line(n)
    regs = _wall_regions(n, wall)
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
      options = [sorted(c for c in reg if not _near(c, wall)) for reg in regs]
      options = [o for o in options if o]
      if not options:
        if geom_fixed:
          raise ValueError('no room for a dot away from the wall')
        continue
      d = random.choice(random.choice(options))
    dreg = regs[0] if d in regs[0] else regs[1]
    other = regs[1] if dreg is regs[0] else regs[0]
    p2 = set(fixed_p2) if fixed_p2 is not None else _sample_pattern(n)
    p3 = set(fixed_p3) if fixed_p3 is not None else _sample_pattern(n)
    lim = n * n - 1
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
    fill_count = 3 * n * n - (len(wall) + 1) - len(p2) - len(p3)
    if fill_count <= max(len(wall) + 1, len(p2), len(p3)):
      if all_fixed:
        raise ValueError('fill colour would not dominate the panels')
      continue
    result = {}
    for r in range(n):
      for c in range(n):
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
    width, height = 4 * n + 5, n + 2
    grid = common.grid(width, height, f)
    offs = [1 + k * (n + 1) for k in range(4)]
    for k in range(4):
      for r in range(n):
        for c in range(n):
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
  raise RuntimeError('could not build a valid scene with the given '
                     'partial parameters')


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
