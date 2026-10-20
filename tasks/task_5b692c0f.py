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

"""ARC task 5b692c0f: repair a damaged shape by mirroring its intact half.

Rule: each shape has one main colour, a straight axis line of colour 4
(length 3 or more) and exactly one lone colour-4 dot. The dot lies on the
intact side of the axis. The output keeps the axis and the intact half, and
rewrites the other half as the mirror image of the intact half. The rewrite
covers every row (or column) of the shape's bounding box and reaches as far
from the axis as the wider of the two halves. Cells whose mirror partner is
background are cleared, and the mirrored dot appears on the repaired side.

Scope: 1-4 shapes on a black grid. Random grids are 10-30 cells per side,
or any explicitly requested size from 5 to 30. Each shape has a distinct
main colour from {1,2,3,5,6,7,8,9}. The accent colour is always 4 and the
background is always 0, as in every demonstration. The axis is vertical or
horizontal, and either side can be the intact one. The intact half is a
ragged blob with holes. The damaged half is the mirror of the intact half
with the dot replaced by the main colour, plus 2-5 random cell removals or
additions, so it can be wider or narrower than the intact half. Shape
footprints, including the full mirrored extent, are kept at least one
background cell apart.
"""

import random

import common

BG = 0
ACCENT = 4
MAIN_COLORS = [1, 2, 3, 5, 6, 7, 8, 9]
MAX_SHAPES = 4


def _connected(cells):
  cells = set(cells)
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        n = (r + dr, c + dc)
        if n in cells and n not in seen:
          seen.add(n)
          stack.append(n)
  return len(seen) == len(cells)


def _sample_local(color, max_len, max_half):
  """Builds one shape in local coordinates with the axis at column 0.

  Args:
    color: main colour of the shape.
    max_len: largest allowed extent along the axis.
    max_half: largest allowed distance of any cell from the axis.

  Returns (cells, side, ext, length), where cells maps (row, col) to a colour
  and side is the sign of the intact half. Returns None on failure.
  """
  max_len = min(9, max_len)
  max_half = min(6, max_half)
  if max_len < 3 or max_half < 2:
    return None
  for _ in range(100):
    length = random.randint(3, max_len)
    wg = random.randint(2, min(5, max_half))
    alen = random.randint(max(3, length - 3), length)
    r0 = random.randint(0, length - alen)
    good = {}
    for y in range(length):
      e = random.randint(1, wg)
      for d in range(1, e + 1):
        if d == 1 or random.random() > 0.15:
          good[(y, d)] = color
    cands = [k for k in good if k[1] >= 2]
    if not cands:
      continue
    dot = random.choice(cands)
    axis = set((y, 0) for y in range(r0, r0 + alen))
    bad = set(good)
    wb = max(2, min(max_half, wg + random.randint(-1, 1)))
    ops = random.randint(2, 5)
    done = 0
    for _ in range(60):
      if done >= ops:
        break
      if random.random() < 0.5 and len(bad) > 2:
        cell = random.choice(sorted(bad))
        bad.discard(cell)
        done += 1
      else:
        y = random.randint(0, length - 1)
        d = random.randint(1, wb)
        if (y, d) in bad:
          continue
        near = False
        for dy in (-1, 0, 1):
          for dd in (-1, 0, 1):
            if (y + dy, d + dd) in bad or (y + dy, d + dd) in axis:
              near = True
        if near:
          bad.add((y, d))
          done += 1
    if not bad or bad == set(good):
      continue
    side = random.choice((-1, 1))
    cells = {}
    for (y, _) in axis:
      cells[(y, 0)] = ACCENT
    for (y, d), v in good.items():
      cells[(y, side * d)] = v
    cells[(dot[0], side * dot[1])] = ACCENT
    for (y, d) in bad:
      cells[(y, -side * d)] = color
    if not _connected(cells):
      continue
    main = sum(1 for v in cells.values() if v == color)
    if main <= alen + 1:
      continue
    ext = max(abs(x) for _, x in cells)
    return cells, side, ext, length
  return None


def _to_abs(local, vertical, top, left, ext):
  cells = {}
  for (y, x), v in local.items():
    if vertical:
      cells[(top + y, left + ext + x)] = v
    else:
      cells[(top + ext + x, left + y)] = v
  axis = left + ext if vertical else top + ext
  return cells, axis


def _check_dim(name, value):
  if value is None:
    return
  if not isinstance(value, int) or not 5 <= value <= 30:
    raise ValueError('%s must be an integer in 5..30 for random scenes' % name)


def _random_scene(num_shapes, height, width):
  explicit = num_shapes is not None
  if explicit and (not isinstance(num_shapes, int) or
                   not 1 <= num_shapes <= MAX_SHAPES):
    raise ValueError('num_shapes must be in 1..%d' % MAX_SHAPES)
  _check_dim('height', height)
  _check_dim('width', width)
  n = num_shapes if explicit else random.randint(1, MAX_SHAPES)
  h_cap = height if height is not None else 30
  w_cap = width if width is not None else 30
  for attempt in range(200):
    if not explicit and attempt and attempt % 40 == 0 and n > 1:
      n -= 1
    colors = random.sample(MAIN_COLORS, n)
    items = []
    for color in colors:
      vertical = random.random() < 0.5
      along = h_cap if vertical else w_cap
      across = w_cap if vertical else h_cap
      s = _sample_local(color, along, (across - 1) // 2)
      if s is None:
        break
      local, side, ext, length = s
      if vertical:
        fh, fw = length, 2 * ext + 1
      else:
        fh, fw = 2 * ext + 1, length
      items.append((local, side, ext, vertical, fh, fw))
    if len(items) < n:
      continue
    max_fh = max(it[4] for it in items)
    max_fw = max(it[5] for it in items)
    if height is not None:
      gh = height
    else:
      gh = random.randint(min(30, max(10, max_fh + 2)), 30)
    if width is not None:
      gw = width
    else:
      gw = random.randint(min(30, max(10, max_fw + 2)), 30)
    if max_fh > gh or max_fw > gw:
      continue
    rects = []
    specs = []
    ok = True
    for local, side, ext, vertical, fh, fw in items:
      placed = False
      for _ in range(100):
        top = random.randint(0, gh - fh)
        left = random.randint(0, gw - fw)
        free = True
        for rt, rl, rh, rw in rects:
          if not (top + fh + 1 <= rt or rt + rh + 1 <= top or
                  left + fw + 1 <= rl or rl + rw + 1 <= left):
            free = False
            break
        if free:
          rects.append((top, left, fh, fw))
          cells, axis = _to_abs(local, vertical, top, left, ext)
          specs.append((cells, vertical, axis, side))
          placed = True
          break
      if not placed:
        ok = False
        break
    if not ok:
      continue
    filled = sum(len(s[0]) for s in specs)
    if filled * 100 > 45 * gh * gw:
      continue
    return gh, gw, specs
  raise ValueError('could not fit %d shapes into the requested grid' % n)


def _parse(spec, height, width):
  rows = spec['rows']
  if (not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows)
      or any(ch not in '0123456789' for row in rows for ch in row)):
    raise ValueError('shape rows must be a nonempty rectangle of digits')
  if (type(spec['vertical']) is not bool or spec['side'] not in (-1, 1)
      or any(type(spec[k]) is not int for k in ('top', 'left', 'axis', 'side'))):
    raise ValueError('invalid axis, side or origin')
  cells = {}
  for r, row in enumerate(spec['rows']):
    for c, ch in enumerate(row):
      if ch != '0':
        rr, cc = spec['top'] + r, spec['left'] + c
        if not (0 <= rr < height and 0 <= cc < width):
          raise ValueError('shape cell outside grid')
        cells[(rr, cc)] = int(ch)
  if not cells or not _connected(cells):
    raise ValueError('shape must be nonempty and 8-connected')
  colours = set(cells.values())
  if len(colours) != 2 or ACCENT not in colours:
    raise ValueError('shape needs one main colour and accent colour 4')
  vertical, axis, side = spec['vertical'], spec['axis'], spec['side']
  accent = {p for p, v in cells.items() if v == ACCENT}
  line = {p for p in accent if p[1 if vertical else 0] == axis}
  along = sorted(p[0 if vertical else 1] for p in line)
  dots = accent - line
  if (len(line) < 3 or along != list(range(along[0], along[-1] + 1))
      or len(dots) != 1):
    raise ValueError('accent needs a contiguous axis and exactly one off-axis dot')
  dot = next(iter(dots))
  if (dot[1 if vertical else 0] - axis) * side <= 0:
    raise ValueError('dot must mark the stated intact side')
  if any(abs(dot[0]-y)+abs(dot[1]-x)==1 for y,x in line):
    raise ValueError('dot must be separate from the axis')
  if len(cells)-len(accent) <= len(accent):
    raise ValueError('main colour must be the majority')
  return cells, vertical, axis, side


def _mirror(out, cells, vertical, axis, side):
  h, w = len(out), len(out[0])
  rows = [r for r, _ in cells]
  cols = [c for _, c in cells]
  if vertical:
    ext = max(axis - min(cols), max(cols) - axis)
    for y in range(min(rows), max(rows) + 1):
      for d in range(1, ext + 1):
        t = axis - side * d
        if 0 <= t < w:
          out[y][t] = cells.get((y, axis + side * d), BG)
  else:
    ext = max(axis - min(rows), max(rows) - axis)
    for x in range(min(cols), max(cols) + 1):
      for d in range(1, ext + 1):
        t = axis - side * d
        if 0 <= t < h:
          out[t][x] = cells.get((axis + side * d, x), BG)


def generate(shapes=None, height=None, width=None, num_shapes=None):
  """Returns an input/output pair.

  Args:
    shapes: optional explicit shapes. Each is a dict with keys 'top' and
      'left' (bounding-box origin), 'rows' (digit strings of the input patch,
      '0' meaning empty), 'vertical' (axis orientation), 'axis' (absolute
      axis column or row) and 'side' (+1 or -1, the intact side holding the
      dot). Requires height and width.
    height: grid height. Required with shapes; for random scenes it fixes
      the height (5..30), otherwise it is sampled in 10..30.
    width: grid width. Required with shapes; for random scenes it fixes
      the width (5..30), otherwise it is sampled in 10..30.
    num_shapes: optional shape count (1-4) for random scenes. It is honoured
      exactly; a ValueError is raised if it cannot fit. With explicit shapes
      it must equal len(shapes) if given.
  """
  if shapes is None:
    height, width, specs = _random_scene(num_shapes, height, width)
  else:
    if height is None or width is None:
      raise ValueError('explicit shapes require height and width')
    if any(type(v) is not int or not 1 <= v <= 30 for v in (height, width)):
      raise ValueError('explicit grid sides must be integers in 1..30')
    if not shapes:
      raise ValueError('at least one shape is required')
    if num_shapes is not None and num_shapes != len(shapes):
      raise ValueError('num_shapes disagrees with len(shapes)')
    specs = [_parse(s, height, width) for s in shapes]
    occupied = set()
    for cells, _, _, _ in specs:
      if any((y+dy, x+dx) in occupied for y,x in cells
             for dy in (-1,0,1) for dx in (-1,0,1)):
        raise ValueError('shapes must not touch')
      occupied.update(cells)
  grid = common.grid(width, height, BG)
  for cells, _, _, _ in specs:
    for (r, c), v in cells.items():
      grid[r][c] = v
  output = [row[:] for row in grid]
  for cells, vertical, axis, side in specs:
    _mirror(output, cells, vertical, axis, side)
  return {'input': grid, 'output': output}


def validate():
  """Rebuilds the canonical fixtures through explicit latent shapes."""
  train = [
      generate(height=14, width=14, shapes=[
          {'top': 1, 'left': 2, 'vertical': True, 'axis': 6, 'side': 1,
           'rows': ['030303333', '033300330', '333343300', '033343333',
                    '033343333', '003343430', '003343300', '033343333',
                    '030343333']},
      ]),
      generate(height=17, width=19, shapes=[
          {'top': 1, 'left': 1, 'vertical': False, 'axis': 4, 'side': -1,
           'rows': ['00110100', '11114110', '11111111', '04444444',
                    '11111110', '00011100']},
          {'top': 9, 'left': 5, 'vertical': True, 'axis': 10, 'side': -1,
           'rows': ['0022002000', '0222242220', '0224242222', '2222242220',
                    '0222242222', '2200202220', '0000000220']},
      ]),
  ]
  test = [
      generate(height=24, width=28, shapes=[
          {'top': 2, 'left': 4, 'vertical': False, 'axis': 4, 'side': -1,
           'rows': ['0224200', '2222220', '0444440', '0022200', '0200222']},
          {'top': 2, 'left': 16, 'vertical': True, 'axis': 20, 'side': -1,
           'rows': ['00080000', '08884800', '88484800', '88884800',
                    '08884888', '88884808', '00080000']},
          {'top': 13, 'left': 4, 'vertical': False, 'axis': 16, 'side': 1,
           'rows': ['0003333000', '0333333300', '0333333300', '0444444440',
                    '3333333330', '0033343333', '0033333300', '0003003300']},
          {'top': 14, 'left': 19, 'vertical': True, 'axis': 22, 'side': -1,
           'rows': ['041410', '111411', '011400']},
      ]),
  ]
  return {'train': train, 'test': test}
