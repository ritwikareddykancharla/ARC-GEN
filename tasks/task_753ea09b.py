"""ARC task 753ea09b generator: fill the pockets of a ladder-like strip.

Rule:
  The grid has a background colour, a wall colour and a stick colour. Two
  8-connected wavy wall lines run from one grid edge to the opposite edge and
  form a strip. Rungs of the stick colour run across the strip and join the
  two walls into one big diagonally connected piece. That piece cuts the
  inside of the strip into pockets. In the output, every background cell
  inside the strip, in every pocket, is painted with the wall colour. This
  includes pockets that touch the grid edge. The two large outside regions,
  the stick cells, loose dots and scattered distractor sticks stay unchanged.

Scope:
  The random scenes have these features:
  * Grid height and width are sampled in 14..30, and about 40% of sampled
    sides are 30, the size used by all the original examples. Sizes other
    than 30x30 are synthetic extensions of the task.
  * Each wall line is a random walk with steps of up to 3 columns per row,
    so the walls can be diagonal and can contain horizontal runs. The strip
    width varies from row to row.
  * Rungs can be horizontal, diagonal or bent with mixed steps.
  * Some stick-coloured spurs are attached to one wall. Some loose dots sit
    inside the strip.
  * Short distractor sticks of either colour are scattered outside the
    strip.
  * Short outward stubs can attach to the wall from outside. They do not
    change the latent fill region; both outside regions remain connected
    and larger than the entire inside area.
  * A random transpose and flips set the strip's orientation.
  The strip always runs between opposite edges. The original fixtures also
  have strips that bend from one edge to an adjacent edge, and their
  irregular hand-drawn outlines do not fit a compact latent description.
  They are replayed through the optional input_grid argument. That path
  uses a small local flood fill and is never used for random generation.
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

import random

import common

# Labels used while constructing a scene.
_OUT_L, _OUT_R, _WALL_L, _INSIDE, _WALL_R = 0, 1, 2, 3, 4
_MIN_SIDE = 14
_MAX_SIDE = 30


def _n8(r, c):
  for dr in (-1, 0, 1):
    for dc in (-1, 0, 1):
      if dr or dc:
        yield r + dr, c + dc


def _runs(v):
  """Turns per-row wall vertices into 8-connected horizontal runs."""
  runs = []
  for r, x in enumerate(v):
    if r == 0:
      runs.append((x, x))
      continue
    p = v[r - 1]
    if x > p + 1:
      runs.append((p + 1, x))
    elif x < p - 1:
      runs.append((x, p - 1))
    else:
      runs.append((x, x))
  return runs


def _path(start, end, h):
  v = [start]
  for r in range(1, h):
    rem = h - r
    step = int(round((end - v[-1]) / rem + random.uniform(-1.3, 1.3)))
    if abs(step) > 1 and random.random() < 0.7:
      step = 1 if step > 0 else -1
    step = max(-3, min(3, step))
    v.append(v[-1] + step)
  return v


def _widths(w0, h):
  out = [w0]
  for _ in range(1, h):
    x = out[-1]
    if random.random() < 0.35:
      x += random.choice([-1, 1])
    out.append(max(3, min(8, x)))
  return out


def _diag(lab, lr, rr, r, h, w, dn):
  """Returns a diagonal rung from one wall to the other, or None."""
  if dn == 1:
    x, target = lr[r][1] + 1, _WALL_R
  else:
    x, target = rr[r][0] - 1, _WALL_L
  y = r
  cells = [(y, x)]
  while True:
    ny, nx = y + 1, x + dn
    if ny >= h or nx < 0 or nx >= w or lab[ny][nx] != _INSIDE:
      break
    y, x = ny, nx
    cells.append((y, x))
  if len(cells) < 2:
    return None
  for yy, xx in _n8(y, x):
    if 0 <= yy < h and 0 <= xx < w and lab[yy][xx] == target:
      return cells
  return None


def _bent(lab, lr, rr, r, h, w, dn):
  """A rung mixing horizontal and diagonal steps across the strip."""
  x = lr[r][1] + 1 if dn == 1 else rr[r][0] - 1
  target = _WALL_R if dn == 1 else _WALL_L
  for _ in range(12):
    y, xx = r, x
    cells, moves = [(y, xx)], set()
    for _ in range(w):
      dy = random.choice((0, 0, 1))
      ny, nx = y + dy, xx + dn
      if not (0 <= ny < h and 0 <= nx < w) or lab[ny][nx] != _INSIDE:
        break
      y, xx = ny, nx
      cells.append((y, xx))
      moves.add(dy)
      if any(0 <= a < h and 0 <= b < w and lab[a][b] == target
             for a, b in _n8(y, xx)):
        if len(moves) == 2:
          return cells
        break
  return None


def _outside_safe(lab, blocked, area_inside, h, w):
  """Check geometry only: neither outside may become a new pocket."""
  for label in (_OUT_L, _OUT_R):
    cells = {(y, x) for y in range(h) for x in range(w)
             if lab[y][x] == label and (y, x) not in blocked}
    if len(cells) <= area_inside:
      return False
    seen = {min(cells)}
    todo = list(seen)
    while todo:
      y, x = todo.pop()
      for q in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
        if q in cells and q not in seen:
          seen.add(q)
          todo.append(q)
    if seen != cells:
      return False
  return True


def _populate(h, w, lr, rr, bg, wall, stick, outward_stubs=None):
  g = common.grid(w, h, bg)
  lab = [[0] * w for _ in range(h)]
  wall_count = 0
  for r in range(h):
    a, b = lr[r]
    c, d = rr[r]
    for x in range(w):
      if x < a:
        lab[r][x] = _OUT_L
      elif x <= b:
        lab[r][x] = _WALL_L
      elif x < c:
        lab[r][x] = _INSIDE
      elif x <= d:
        lab[r][x] = _WALL_R
      else:
        lab[r][x] = _OUT_R
      if lab[r][x] in (_WALL_L, _WALL_R):
        g[r][x] = wall
        wall_count += 1
  budget = wall_count - 3  # The wall colour must stay the majority colour.
  used = 0
  busy = set()
  rungs = 0
  r = random.randint(0, 4)
  while r < h:
    cells = None
    mode = random.random()
    if mode < 0.35:
      cells = _bent(lab, lr, rr, r, h, w, random.choice([1, -1]))
    elif mode < 0.65:
      cells = _diag(lab, lr, rr, r, h, w, random.choice([1, -1]))
    if cells is None:
      cells = [(r, x) for x in range(lr[r][1] + 1, rr[r][0])]
    if used + len(cells) > budget:
      break
    for y, x in cells:
      g[y][x] = stick
    used += len(cells)
    rungs += 1
    last = max(y for y, _ in cells)
    for y in range(r - 1, last + 2):
      busy.add(y)
    r = last + random.randint(3, 7)
  if rungs == 0:
    return None
  # Spurs attached to one wall (join the wall piece, never cross the strip).
  rows = [y for y in range(h) if y not in busy]
  random.shuffle(rows)
  want = random.randint(0, 3)
  for y in rows:
    if want <= 0:
      break
    if y in busy:
      continue
    iw = rr[y][0] - lr[y][1] - 1
    if iw < 3:
      continue
    ln = random.randint(1, iw - 2)
    if used + ln > budget:
      continue
    if random.random() < 0.5:
      cells = [(y, x) for x in range(lr[y][1] + 1, lr[y][1] + 1 + ln)]
      opposite = _WALL_R
    else:
      cells = [(y, x) for x in range(rr[y][0] - ln, rr[y][0])]
      opposite = _WALL_L
    if random.random() < 0.4:
      anchor = cells[0] if opposite == _WALL_R else cells[-1]
      cells = [(anchor[0] + d, anchor[1]) for d in range(random.randint(2, 4))]
    if (used + len(cells) > budget or
        any(not (0 <= a < h and 0 <= b < w) or lab[a][b] != _INSIDE
            or g[a][b] != bg or any(
                0 <= yy < h and 0 <= xx < w and lab[yy][xx] == opposite
                for yy, xx in _n8(a, b)) for a, b in cells)):
      continue
    for a, b in cells:
      g[a][b] = stick
    used += len(cells)
    want -= 1
    for a, b in cells:
      busy.update((a - 1, a, a + 1))
  # Outside attachments must not introduce additional exterior pockets.
  target = random.randint(0, 2) if outward_stubs is None else outward_stubs
  exterior = set()
  area_i = sum(v == _INSIDE for row in lab for v in row)
  placed = 0
  for _ in range(100):
    if placed == target:
      break
    y = random.randint(1, h - 2)
    left_side = random.random() < 0.5
    start = lr[y][0] - 1 if left_side else rr[y][1] + 1
    direction = -1 if left_side else 1
    label = _OUT_L if left_side else _OUT_R
    cells = {(y, start + direction * i) for i in range(random.randint(1, 3))}
    if used + len(cells) > budget:
      continue
    if any(not (0 < x < w - 1) or lab[y][x] != label or g[y][x] != bg
           for y, x in cells):
      continue
    if any(q in exterior for y, x in cells for q in _n8(y, x)):
      continue
    if not _outside_safe(lab, exterior | cells, area_i, h, w):
      continue
    colour = wall if random.random() < 0.2 else stick
    for y, x in cells:
      g[y][x] = colour
    exterior.update(cells)
    used += len(cells)
    placed += 1
  if placed != target:
    return None
  # Loose stick dots inside the strip (they stay as they are).
  for _ in range(random.randint(0, 2)):
    for _ in range(40):
      y, x = random.randint(0, h - 1), random.randint(0, w - 1)
      if lab[y][x] != _INSIDE or g[y][x] != bg:
        continue
      if any(0 <= yy < h and 0 <= xx < w and g[yy][xx] != bg
             for yy, xx in _n8(y, x)):
        continue
      g[y][x] = stick
      break
  # Outside distractor sticks, isolated from everything else.
  dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
  n = random.randint(6, 16)
  placed = 0
  for _ in range(n * 40):
    if placed >= n:
      break
    dy, dx = random.choice(dirs)
    ln = random.choice([1, 1, 2, 2, 3, 3, 4])
    y0, x0 = random.randint(0, h - 1), random.randint(0, w - 1)
    cells = [(y0 + dy * i, x0 + dx * i) for i in range(ln)]
    if any(not (0 <= y < h and 0 <= x < w) for y, x in cells):
      continue
    if any(lab[y][x] not in (_OUT_L, _OUT_R) or g[y][x] != bg
           for y, x in cells):
      continue
    cs = set(cells)
    bad = False
    for y, x in cells:
      for yy, xx in _n8(y, x):
        if (0 <= yy < h and 0 <= xx < w and (yy, xx) not in cs
            and g[yy][xx] != bg):
          bad = True
    if bad:
      continue
    col = random.choice([wall, stick])
    for y, x in cells:
      g[y][x] = col
    placed += 1
  # The answer comes from the latent labels: every inside background cell
  # takes the wall colour.
  out = [row[:] for row in g]
  for y in range(h):
    for x in range(w):
      if lab[y][x] == _INSIDE and g[y][x] == bg:
        out[y][x] = wall
  return g, out


def _scene(h, w, bg, wall, stick, outward_stubs=None):
  """Builds a top-to-bottom strip scene of h rows and w columns."""
  for _ in range(400):
    w0 = random.randint(3, 7)
    if w - 3 - w0 < 2:
      continue
    s = random.randint(2, w - 3 - w0)
    e = random.randint(2, w - 3 - w0)
    if abs(e - s) > h - 1:
      continue
    left = _path(s, e, h)
    widths = _widths(w0, h)
    right = [left[r] + widths[r] for r in range(h)]
    lr, rr = _runs(left), _runs(right)
    ok = True
    for r in range(h):
      iw = rr[r][0] - lr[r][1] - 1
      if lr[r][0] < 1 or rr[r][1] > w - 2 or iw < 2 or iw > 10:
        ok = False
        break
    if not ok:
      continue
    # Both outside regions must be strictly larger than all of the inside.
    area_l = sum(lr[r][0] for r in range(h))
    area_r = sum(w - 1 - rr[r][1] for r in range(h))
    area_i = sum(rr[r][0] - lr[r][1] - 1 for r in range(h))
    if area_i + 4 > min(area_l, area_r):
      continue
    res = _populate(h, w, lr, rr, bg, wall, stick, outward_stubs)
    if res is not None:
      return res
  return None


def _replay(grid):
  """Fixture replay only: flood-fill pockets of a given input grid."""
  h, w = len(grid), len(grid[0])
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  bg = max(counts, key=lambda k: counts[k])
  seen = [[False] * w for _ in range(h)]
  best = []
  for r in range(h):
    for c in range(w):
      if grid[r][c] == bg or seen[r][c]:
        continue
      seen[r][c] = True
      comp, stack = [], [(r, c)]
      while stack:
        y, x = stack.pop()
        comp.append((y, x))
        for yy, xx in _n8(y, x):
          if (0 <= yy < h and 0 <= xx < w and not seen[yy][xx]
              and grid[yy][xx] != bg):
            seen[yy][xx] = True
            stack.append((yy, xx))
      if len(comp) > len(best):
        best = comp
  wallset = set(best)
  vc = {}
  for y, x in best:
    vc[grid[y][x]] = vc.get(grid[y][x], 0) + 1
  fill = max(vc, key=lambda k: vc[k])
  seen = [[False] * w for _ in range(h)]
  regions = []
  for r in range(h):
    for c in range(w):
      if (r, c) in wallset or seen[r][c]:
        continue
      seen[r][c] = True
      reg, stack = [], [(r, c)]
      while stack:
        y, x = stack.pop()
        reg.append((y, x))
        for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
          if (0 <= yy < h and 0 <= xx < w and not seen[yy][xx]
              and (yy, xx) not in wallset):
            seen[yy][xx] = True
            stack.append((yy, xx))
      regions.append(reg)
  regions.sort(key=len, reverse=True)
  out = [row[:] for row in grid]
  for reg in regions[2:]:
    for y, x in reg:
      if out[y][x] == bg:
        out[y][x] = fill
  return out


def _sample_side():
  if random.random() < 0.4:
    return _MAX_SIDE
  return random.randint(_MIN_SIDE, _MAX_SIDE)


def generate(width=None, height=None, bg=None, wall=None, stick=None,
             transpose=None, flip_v=None, flip_h=None, input_grid=None,
             outward_stubs=None):
  """Returns an input/output pair for task 753ea09b.

  Args:
    width: output grid width (14..30); sampled if None.
    height: output grid height (14..30); sampled if None.
    bg: background colour (0..9); sampled if None.
    wall: colour of the wavy strip walls (0..9); it is also the fill colour.
    stick: colour of the rungs, spurs, loose dots and some distractors.
      Colours given explicitly must be distinct. Missing colours are sampled
      distinct from the given ones.
    transpose: if True, the strip runs left-right instead of top-bottom.
    flip_v: flip the scene vertically.
    flip_h: flip the scene horizontally.
    input_grid: optional original fixture input to replay with a local
      flood fill. It is used only by validate() and cannot be combined with
      the scene parameters above.
    outward_stubs: exact 0..3 short exterior wall attachments. None samples
      0..2. Regions remain connected and large; stubs are never repainted.
  """
  if input_grid is not None:
    if any(v is not None for v in (width, height, bg, wall, stick,
                                   transpose, flip_v, flip_h, outward_stubs)):
      raise ValueError('input_grid replay cannot be combined with scene '
                       'parameters')
    grid = [list(row) for row in input_grid]
    return {'input': grid, 'output': _replay(grid)}
  for name, v in (('width', width), ('height', height)):
    if v is not None and (type(v) is not int or not _MIN_SIDE <= v <= _MAX_SIDE):
      raise ValueError(name + ' must be in 14..30')
  given = [c for c in (bg, wall, stick) if c is not None]
  for c in given:
    if type(c) is not int or not 0 <= c <= 9:
      raise ValueError('colours must be in 0..9')
  if len(set(given)) != len(given):
    raise ValueError('bg, wall and stick colours must be distinct')
  for value in (transpose, flip_v, flip_h):
    if value is not None and type(value) is not bool:
      raise ValueError('orientation controls must be bool or None')
  if outward_stubs is not None and (
      type(outward_stubs) is not int or not 0 <= outward_stubs <= 3):
    raise ValueError('outward_stubs must be an integer in 0..3')
  pool = [c for c in range(10) if c not in given]
  random.shuffle(pool)
  if bg is None:
    bg = pool.pop()
  if wall is None:
    wall = pool.pop()
  if stick is None:
    stick = pool.pop()
  if flip_v is None:
    flip_v = random.random() < 0.5
  if flip_h is None:
    flip_h = random.random() < 0.5
  res = None
  tr = transpose
  for _ in range(60):
    tr = transpose if transpose is not None else random.random() < 0.5
    ww = width if width is not None else _sample_side()
    hh = height if height is not None else _sample_side()
    sh, sw = (ww, hh) if tr else (hh, ww)
    res = _scene(sh, sw, bg, wall, stick, outward_stubs)
    if res is not None:
      break
  if res is None:
    raise ValueError('could not build a scene with the given parameters')
  g, o = res

  def tf(m):
    if tr:
      m = [list(r) for r in zip(*m)]
    if flip_v:
      m = m[::-1]
    if flip_h:
      m = [r[::-1] for r in m]
    return [list(r) for r in m]

  return {'input': tf(g), 'output': tf(o)}


_TRAIN_INPUTS = [
    [[6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6], [6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6], [5, 6, 6, 6, 6, 7, 6, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 5, 7, 6, 7, 6, 6, 6, 6, 6, 6, 6, 6, 6], [5, 6, 6, 6, 7, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 5, 6, 7, 6, 7, 6, 6, 6, 6, 6, 6, 6, 6], [6, 5, 6, 7, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6], [6, 5, 7, 6, 6, 6, 6, 6, 6, 7, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6], [6, 5, 5, 5, 6, 6, 6, 6, 7, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6], [6, 6, 6, 6, 5, 6, 6, 7, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6], [6, 6, 6, 6, 6, 5, 7, 6, 6, 6, 6, 6, 6, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6], [6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 7, 6, 6, 6], [6, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 7, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 6, 7, 6, 6], [6, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 7, 6, 6, 6, 5, 5, 5, 5, 5, 6, 6, 6, 6, 5, 6, 6, 7, 6], [6, 7, 6, 6, 6, 6, 6, 6, 5, 6, 6, 7, 6, 6, 6, 6, 6, 7, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 7], [6, 6, 7, 6, 6, 6, 6, 6, 6, 5, 7, 6, 6, 6, 6, 6, 7, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6], [6, 6, 6, 7, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 7, 6, 6, 6, 6, 6, 7, 5, 6, 6, 6, 6, 6, 6, 6], [6, 6, 5, 6, 7, 6, 6, 6, 6, 5, 6, 5, 6, 5, 7, 6, 6, 6, 6, 6, 7, 6, 6, 5, 5, 6, 6, 6, 6, 6], [6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 5, 6, 5, 6, 5, 5, 5, 5, 5, 7, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6], [6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6], [6, 6, 5, 6, 6, 7, 6, 7, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6], [6, 7, 6, 7, 7, 6, 7, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 6, 7, 6, 7, 6, 6, 5, 6, 6, 6, 6], [6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 7, 6, 7, 6, 7, 5, 6, 6, 6, 6, 6], [6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6], [6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 5, 5, 5, 5, 7, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6], [6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 5, 6, 7, 6, 6, 6, 7, 6, 6, 6, 5, 5, 6, 6, 6, 6, 6, 6], [6, 6, 6, 6, 6, 6, 6, 6, 5, 6, 5, 6, 6, 6, 7, 6, 6, 6, 6, 5, 5, 5, 6, 6, 6, 7, 7, 7, 6, 6], [6, 6, 7, 6, 6, 6, 5, 5, 6, 5, 6, 6, 6, 6, 7, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6], [6, 6, 6, 6, 6, 5, 6, 6, 7, 6, 6, 6, 6, 6, 7, 5, 5, 5, 6, 6, 6, 6, 6, 6, 5, 5, 6, 6, 6, 6], [6, 6, 6, 6, 5, 6, 6, 6, 7, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 7, 6, 5, 6, 6, 6, 6, 6], [6, 6, 6, 5, 6, 6, 6, 6, 6, 7, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 7, 6, 6, 6, 6, 6, 6, 6, 6], [6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 7, 5, 5, 6, 6, 6, 6, 6, 6, 6, 7, 6, 6, 6, 6, 6, 6, 6, 6, 6]],
    [[3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3], [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 0, 3, 3], [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 0, 3], [3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 0], [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3], [3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3], [3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 0, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 3, 3], [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3], [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 0, 3, 3, 3], [3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 0, 3, 4], [3, 3, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 4, 3], [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 4, 4, 4, 3, 3, 3, 3, 4, 3], [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 3, 0, 3, 3, 3, 3, 3, 4, 3], [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3, 3, 3, 0, 3, 3, 3, 4, 3, 3], [3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 4, 3, 3], [3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 0, 4, 3, 3, 3], [3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3], [3, 3, 3, 3, 3, 3, 4, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 4, 4, 3, 3, 3, 3], [3, 3, 3, 3, 3, 4, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 4, 3, 3, 3, 3, 3, 3], [3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 4, 3, 3, 3, 3, 3, 3, 3], [3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3], [3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 0, 3, 3, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 0, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 3, 3, 3], [3, 3, 4, 3, 4, 0, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 4, 3, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3], [4, 4, 3, 4, 3, 3, 0, 3, 3, 3, 3, 4, 3, 3, 3, 3, 4, 3, 0, 3, 3, 4, 4, 4, 3, 3, 3, 0, 3, 3], [3, 3, 3, 3, 3, 3, 3, 0, 3, 4, 4, 3, 3, 3, 4, 4, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]],
    [[8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 3, 8, 8, 8, 8], [8, 8, 8, 8, 9, 8, 8, 9, 9, 9, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8], [8, 8, 9, 9, 8, 3, 3, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 3, 8, 8, 8, 3, 8, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 3, 8, 8, 8, 3, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 3, 8, 8, 3, 8], [3, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 9, 9, 8, 8, 8, 8, 9, 9, 9, 8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 3, 8], [8, 8, 8, 8, 8, 8, 9, 8, 3, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 8], [8, 8, 8, 3, 8, 9, 8, 8, 3, 8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 3, 8, 8, 8, 8, 9, 8, 8, 8, 3, 3], [8, 8, 8, 8, 9, 8, 8, 8, 3, 8, 8, 8, 8, 8, 8, 8, 3, 3, 9, 8, 8, 8, 8, 8, 8, 9, 8, 8, 3, 8], [9, 9, 9, 9, 8, 8, 8, 8, 3, 8, 8, 8, 8, 8, 8, 3, 8, 8, 9, 8, 8, 8, 8, 8, 8, 9, 8, 8, 3, 8], [8, 8, 8, 3, 8, 8, 8, 8, 3, 8, 8, 9, 8, 3, 3, 8, 8, 8, 8, 9, 9, 8, 8, 8, 8, 9, 8, 8, 8, 8], [8, 8, 8, 3, 8, 8, 8, 9, 9, 9, 9, 8, 9, 9, 8, 8, 8, 8, 8, 8, 3, 9, 8, 8, 8, 8, 9, 8, 8, 8], [8, 8, 8, 3, 9, 8, 9, 8, 8, 8, 8, 8, 3, 8, 9, 8, 8, 8, 8, 3, 8, 9, 8, 8, 8, 8, 9, 8, 8, 8], [9, 9, 9, 9, 8, 9, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 3, 8, 8, 9, 8, 8, 8, 8, 9, 8, 8, 8], [8, 8, 8, 8, 8, 3, 8, 8, 3, 3, 8, 8, 8, 8, 8, 9, 8, 3, 8, 8, 8, 8, 9, 9, 8, 8, 8, 8, 8, 8], [3, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 3, 8, 8, 9, 9, 9, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 8, 3], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 3, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 3, 9, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 3, 8, 3, 8, 8, 8, 9, 9, 8, 3, 8, 8, 9, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 3, 8, 8, 8, 3, 8, 8, 8, 3, 8, 9, 8, 8, 8, 8, 9, 9, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 9, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 3, 3, 3, 3, 3, 9, 8, 8], [8, 8, 8, 8, 3, 8, 8, 8, 3, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 8, 9, 8, 8], [8, 8, 8, 8, 8, 9, 9, 9, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 9, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 3, 8, 9, 8, 8, 8, 9, 8, 8, 8], [8, 8, 8, 8, 8, 8, 3, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 3, 3, 3, 9, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 9, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 3, 8, 3, 8, 8, 8, 9, 8, 8, 8, 9, 8, 8, 8, 8]],
]

_TEST_INPUTS = [
    [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 3, 3, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 2, 2, 1, 1, 1], [1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 3, 3, 3, 3, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1], [1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 2, 1, 1], [1, 1, 1, 1, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 3, 3, 3, 3, 3, 2, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1], [1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 2, 1, 1, 3, 3, 3, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 3, 3, 1, 1, 2, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 3, 3, 3, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 3, 2, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 3, 1, 1, 2, 1, 1, 1, 1, 1, 3, 3, 1, 1], [1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 3, 3, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]],
]


def validate():
  """Replays the original fixtures through generate(input_grid=...)."""
  train = [generate(input_grid=g) for g in _TRAIN_INPUTS]
  test = [generate(input_grid=g) for g in _TEST_INPUTS]
  return {'train': train, 'test': test}
