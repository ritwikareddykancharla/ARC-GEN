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

"""ARC-GEN style generator for task dbff022c.

Rule: a multicoloured legend, two cells thick, lies against one edge of the
grid. The legend line that touches the edge holds distinct key colours. The
line beside it holds the paired fill colours. Every other object is an
outline. A hole is a 4-connected background component that does not reach
the grid border and is 4-adjacent to exactly one colour. If that colour is a
key, the hole is filled with the key's fill colour. Holes of non-key outlines
stay empty. Open (leaking) outlines have no holes. Pockets bordered by two
colours stay empty.

Scope: random sides are mostly 4..20 and sometimes 21..30. The fixtures span
4..15, so larger sizes are a synthetic extension. Explicit sizes 3..30 are
accepted whenever a scene fits; when both sides are given, an infeasible size
is rejected up front. A random legend has 2..7 pairs and can lie on any of
the four edges. A 2x2 legend is never placed in a corner, because there its
orientation is ambiguous; the reference would read it as vertical. Random
scenes hold 1..8 objects, usually 2 or more. Objects are separated by at
least one background cell, including diagonally. Sprites may interlock
through their empty margins, as in the test fixture. Object kinds:
  - closed rectangles, optionally with interior walls grown from the ring;
  - chipped irregular outlines and diamonds. Any closed sprite may carry a
    pendant tail of 1..2 cells outside its loop;
  - closed outlines in non-key colours, often a colour that appears only in
    the fill line;
  - open outlines (a synthetic extension);
  - two-colour rings (a synthetic extension). Their shared pocket stays
    empty. They are used only when the legend has at least three distinct
    colours, so the legend stays the most colourful object.
Every random scene changes at least one cell. Every alternative reading of
the legend gives a different output: the swapped lines, and for 2x2 legends
the transposed readings as well.
Not supported: nested or touching distinct objects, and legends more than
two cells thick.
"""

import random

import common


_SIDES = ('top', 'bottom', 'left', 'right')
_MAX_SHAPES = 8
_TRUE_READING = {'top': (True, 0), 'bottom': (True, 1),
                 'left': (False, 0), 'right': (False, 1)}
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _rotate(sprite):
  h, w = len(sprite), len(sprite[0])
  return [''.join(sprite[h - 1 - i][j] for i in range(h)) for j in range(w)]


def _random_rotation(sprite):
  for _ in range(random.randint(0, 3)):
    sprite = _rotate(sprite)
  return sprite


def _sprite_rect(h, w):
  rows = [['#' if i in (0, h - 1) or j in (0, w - 1) else 'o'
           for j in range(w)] for i in range(h)]
  inner = [(i, j) for i in range(1, h - 1) for j in range(1, w - 1)]
  if len(inner) >= 4 and random.random() < 0.4:
    # Interior walls grow from the ring, so the outline stays one piece.
    for _ in range(random.randint(1, max(1, len(inner) // 3))):
      left = [(i, j) for i, j in inner if rows[i][j] == 'o']
      if len(left) <= 1:
        break
      grow = [(i, j) for i, j in left
              if any(rows[i + di][j + dj] == '#' for di, dj in _DIRS)]
      i, j = random.choice(grow)
      rows[i][j] = '#'
  return [''.join(r) for r in rows]


def _sprite_chipped(h, w):
  region = [[True] * w for _ in range(h)]
  for ci, cj in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
    if random.random() < 0.5:
      s = random.randint(1, 2)
      for i in range(h):
        for j in range(w):
          if abs(i - ci) + abs(j - cj) < s:
            region[i][j] = False
  rows = []
  for i in range(h):
    row = []
    for j in range(w):
      if not region[i][j]:
        row.append('.')
        continue
      edge = False
      for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
          y, x = i + di, j + dj
          if not (0 <= y < h and 0 <= x < w) or not region[y][x]:
            edge = True
      row.append('#' if edge else 'o')
    rows.append(''.join(row))
  return rows


def _sprite_diamond(r):
  rows = []
  for i in range(2 * r + 1):
    row = ''
    for j in range(2 * r + 1):
      d = abs(i - r) + abs(j - r)
      row += '#' if d == r else ('o' if d < r else '.')
    rows.append(row)
  return rows


def _sprite_open(h, w):
  rows = [list('#' * w)] + [list('#' + '.' * (w - 2) + '#')
                            for _ in range(h - 2)] + [list('#' * w)]
  edges = [(0, j) for j in range(1, w - 1)]
  edges += [(h - 1, j) for j in range(1, w - 1)]
  edges += [(i, 0) for i in range(1, h - 1)]
  edges += [(i, w - 1) for i in range(1, h - 1)]
  i, j = random.choice(edges)
  rows[i][j] = '.'
  return [''.join(r) for r in rows]


def _sprite_pair(h, w):
  """A ring split into two colours ('#' and '%') around one pocket."""
  s = random.randint(1, w - 1)
  rows = []
  for i in range(h):
    row = ''
    for j in range(w):
      if i in (0, h - 1) or j in (0, w - 1):
        row += '#' if j < s else '%'
      else:
        row += 'o'
    rows.append(row)
  return _random_rotation(rows)


def _add_tail(sprite):
  """Attaches a 1..2 cell pendant outside the loop of a closed sprite."""
  sprite = _random_rotation(sprite)
  w = len(sprite[0])
  cols = [j for j, ch in enumerate(sprite[-1]) if ch == '#']
  if not cols:
    return sprite
  j = random.choice(cols)
  tail = '.' * j + '#' + '.' * (w - j - 1)
  return sprite + [tail] * random.randint(1, 2)


def _legend_cells(width, height, side, offset, keys, fills):
  """Returns ((row, col), colour) for every legend cell."""
  cells = []
  for i, (k, f) in enumerate(zip(keys, fills)):
    if side == 'top':
      cells += [((0, offset + i), k), ((1, offset + i), f)]
    elif side == 'bottom':
      cells += [((height - 1, offset + i), k), ((height - 2, offset + i), f)]
    elif side == 'left':
      cells += [((offset + i, 0), k), ((offset + i, 1), f)]
    else:
      cells += [((offset + i, width - 1), k), ((offset + i, width - 2), f)]
  return cells


def _legend_matrix(side, keys, fills):
  """The legend block as it appears in the grid, top-left first."""
  if side == 'top':
    return [list(keys), list(fills)]
  if side == 'bottom':
    return [list(fills), list(keys)]
  if side == 'left':
    return [[k, f] for k, f in zip(keys, fills)]
  return [[f, k] for k, f in zip(keys, fills)]


def _read(matrix, horizontal, key):
  mapping = {}
  if horizontal:
    for c in range(len(matrix[0])):
      mapping[matrix[key][c]] = matrix[1 - key][c]
  else:
    for r in range(len(matrix)):
      mapping[matrix[r][key]] = matrix[r][1 - key]
  return mapping


def _alt_mappings(side, keys, fills):
  """Mappings from every geometrically possible but wrong legend reading."""
  matrix = _legend_matrix(side, keys, fills)
  readings = []
  if len(matrix) == 2:
    readings += [(True, 0), (True, 1)]
  if len(matrix[0]) == 2:
    readings += [(False, 0), (False, 1)]
  return [_read(matrix, hz, key) for hz, key in readings
          if (hz, key) != _TRUE_READING[side]]


def _always_ambiguous(side, keys, fills):
  """True when some wrong reading equals the true mapping on every colour."""
  truth = dict(zip(keys, fills))
  return any(alt == truth for alt in _alt_mappings(side, keys, fills))


def _colour_problem(keys, fills):
  """Returns a description of invalid legend colours, or None."""
  for name, seq in (('keys', keys), ('fills', fills)):
    if seq is None:
      continue
    if not isinstance(seq, (list, tuple)):
      return '%s must be a list of colours' % name
    if not 2 <= len(seq) <= 9:
      return '%s must contain 2..9 colours' % name
    if any(not _is_int(c) or not 1 <= c <= 9 for c in seq):
      return '%s colours must be integers within 1..9' % name
  if keys is not None and len(set(keys)) != len(keys):
    return 'keys must be distinct'
  if keys is not None and fills is not None and len(keys) != len(fills):
    return 'keys and fills must have the same length'
  return None


def _legend_problem(width, height, side, offset, keys, fills):
  """Returns a description of why the legend is invalid, or None."""
  if keys is None or fills is None:
    return 'keys and fills are required'
  problem = _colour_problem(keys, fills)
  if problem is not None:
    return problem
  if side not in _SIDES:
    return 'legend_side must be one of %s' % (_SIDES,)
  if not (_is_int(width) and _is_int(height)):
    return 'grid sides must be integers'
  if not (3 <= width <= 30 and 3 <= height <= 30):
    return 'grid sides must be within 3..30'
  k = len(keys)
  edge = width if side in ('top', 'bottom') else height
  perp = height if side in ('top', 'bottom') else width
  if perp < 3:
    return "grid too thin for the legend's key side to be identifiable"
  if not _is_int(offset) or offset < 0 or offset + k > edge:
    return 'legend does not fit along its edge'
  if k == 2 and (offset == 0 or offset + 2 == edge):
    return 'a 2x2 legend in a corner has an ambiguous orientation'
  return None


def _shape_problem(shapes):
  """Returns a description of malformed explicit shapes, or None."""
  if not isinstance(shapes, (list, tuple)):
    return 'shapes must be a list'
  if not 1 <= len(shapes) <= _MAX_SHAPES:
    return 'shapes must contain 1..%d objects' % _MAX_SHAPES
  for shape in shapes:
    if not isinstance(shape, (list, tuple)) or len(shape) not in (4, 5):
      return 'each shape must be (row, col, colour, sprite[, colour2])'
    r, c, color, sprite = shape[:4]
    if not (_is_int(r) and _is_int(c)):
      return 'shape row and column must be integers'
    if not _is_int(color) or not 1 <= color <= 9:
      return 'shape colour must be an integer within 1..9'
    if len(shape) == 5:
      color2 = shape[4]
      if not _is_int(color2) or not 1 <= color2 <= 9 or color2 == color:
        return 'colour2 must be an integer within 1..9 that differs from colour'
    if not isinstance(sprite, (list, tuple)) or not sprite:
      return 'sprite must be a non-empty list of strings'
    if any(not isinstance(row, str) for row in sprite) or not sprite[0]:
      return 'sprite rows must be non-empty strings'
  return None


def _enclosed(grid):
  """Returns background cells in components that do not touch the border."""
  h, w = len(grid), len(grid[0])
  seen, result = set(), set()
  for sy in range(h):
    for sx in range(w):
      if grid[sy][sx] != 0 or (sy, sx) in seen:
        continue
      comp, stack, border = [], [(sy, sx)], False
      seen.add((sy, sx))
      while stack:
        y, x = stack.pop()
        comp.append((y, x))
        if y in (0, h - 1) or x in (0, w - 1):
          border = True
        for dy, dx in _DIRS:
          ny, nx = y + dy, x + dx
          if (0 <= ny < h and 0 <= nx < w and grid[ny][nx] == 0
              and (ny, nx) not in seen):
            seen.add((ny, nx))
            stack.append((ny, nx))
      if not border:
        result.update(comp)
  return result


def _dilate(blocked, y, x):
  for dy in (-1, 0, 1):
    for dx in (-1, 0, 1):
      blocked.add((y + dy, x + dx))


def _apply(grid, comps, mapping):
  """Fills each designed hole bordered by one key colour."""
  result = [row[:] for row in grid]
  for cells, colours in comps:
    if len(colours) != 1:
      continue
    c = next(iter(colours))
    if c in mapping:
      for y, x in cells:
        result[y][x] = mapping[c]
  return result


def _render(width, height, side, offset, keys, fills, shapes):
  """Draws the scene. Returns ((input, output, comps), None) or (None, why)."""
  grid = common.grid(width, height, 0)
  owner = [[None] * width for _ in range(height)]
  for (y, x), color in _legend_cells(width, height, side, offset, keys,
                                     fills):
    grid[y][x] = color
    owner[y][x] = -1
  holes = {}
  two_colour = False
  for idx, shape in enumerate(shapes):
    r, c, color, sprite = shape[:4]
    color2 = shape[4] if len(shape) == 5 else None
    if color2 is not None:
      two_colour = True
    allowed = '#o%' if color2 is not None else '#o'
    if any(len(row) != len(sprite[0]) for row in sprite):
      return None, 'sprite rows must have equal length'
    for i, row in enumerate(sprite):
      for j, ch in enumerate(row):
        if ch == '.':
          continue
        if ch not in allowed:
          return None, 'unknown sprite character %r' % ch
        y, x = r + i, c + j
        if not (0 <= y < height and 0 <= x < width):
          return None, 'a shape lies outside the grid'
        if owner[y][x] is not None or (y, x) in holes:
          return None, 'shapes overlap each other or the legend'
        if ch == 'o':
          holes[(y, x)] = idx
        else:
          grid[y][x] = color if ch == '#' else color2
          owner[y][x] = idx
  # Distinct objects (and the legend) must not touch, even diagonally.
  for y in range(height):
    for x in range(width):
      if owner[y][x] is None:
        continue
      for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
          ny, nx = y + dy, x + dx
          if (0 <= ny < height and 0 <= nx < width
              and owner[ny][nx] is not None and owner[ny][nx] != owner[y][x]):
            return None, 'distinct objects touch'
  # Every hole cell must border only its own shape's outline or holes.
  for (y, x), idx in holes.items():
    for dy, dx in _DIRS:
      ny, nx = y + dy, x + dx
      if not (0 <= ny < height and 0 <= nx < width):
        return None, 'a hole cell lies on the grid border'
      if (ny, nx) in holes:
        if holes[(ny, nx)] != idx:
          return None, 'holes of different shapes touch'
      elif owner[ny][nx] != idx:
        return None, 'a hole cell is not enclosed by its own outline'
  # The enclosed background must be exactly the designed holes. This rules
  # out incidental pockets, and it confirms that open outlines really leak.
  if _enclosed(grid) != set(holes):
    return None, 'enclosed background differs from the designed holes'
  counts = [0] * 10
  for row in grid:
    for v in row:
      counts[v] += 1
  if any(counts[v] >= counts[0] for v in range(1, 10)):
    return None, 'background 0 must stay the strictly most frequent colour'
  if two_colour and len(set(keys) | set(fills)) < 3:
    return None, ('two-colour objects need a legend with at least three '
                  'distinct colours')
  comps, seen = [], set()
  for cell in holes:
    if cell in seen:
      continue
    stack, cells, colours = [cell], [], set()
    seen.add(cell)
    while stack:
      y, x = stack.pop()
      cells.append((y, x))
      for dy, dx in _DIRS:
        n = (y + dy, x + dx)
        if n in holes:
          if n not in seen:
            seen.add(n)
            stack.append(n)
        else:
          colours.add(grid[n[0]][n[1]])
    comps.append((cells, colours))
  output = _apply(grid, comps, dict(zip(keys, fills)))
  return (grid, output, comps), None


def _random_sprite(kind, max_h, max_w, big):
  hi = 9 if big else 7
  for _ in range(10):
    if kind == 'open':
      sprite = _sprite_open(random.randint(3, hi - 1),
                            random.randint(3, hi - 1))
    elif kind == 'pair':
      sprite = _sprite_pair(random.randint(3, hi - 1), random.randint(4, hi))
    else:
      style = random.choice(['rect', 'rect', 'chip', 'diamond'])
      if style == 'rect':
        sprite = _sprite_rect(random.randint(3, hi), random.randint(3, hi))
      elif style == 'chip':
        sprite = _sprite_chipped(random.randint(4, hi), random.randint(4, hi))
      else:
        radii = [1, 1, 2, 2, 3] + ([4] if big else [])
        sprite = _sprite_diamond(random.choice(radii))
      if not any('o' in row for row in sprite):
        continue
      if random.random() < 0.3:
        sprite = _add_tail(sprite)
    if len(sprite) <= max_h and len(sprite[0]) <= max_w:
      return sprite
  return None


def _sample_side_length():
  if random.random() < 0.15:
    return random.randint(21, 30)
  return random.randint(4, 20)


def _feasible(width, height, sides, k_fixed, offset):
  """True if some legend placement leaves room for a radius-1 diamond."""
  for s in sides:
    edge = width if s in ('top', 'bottom') else height
    for k in ([k_fixed] if k_fixed is not None else [2, 3]):
      if k > edge:
        continue
      offs = [offset] if offset is not None else range(edge - k + 1)
      for o in offs:
        dummy = list(range(1, k + 1))
        if _legend_problem(width, height, s, o, dummy, dummy) is not None:
          continue
        blocked = set()
        for (y, x), _ in _legend_cells(width, height, s, o, dummy, dummy):
          _dilate(blocked, y, x)
        for r in range(height - 2):
          for c in range(width - 2):
            cells = ((r, c + 1), (r + 1, c), (r + 1, c + 1), (r + 1, c + 2),
                     (r + 2, c + 1))
            if all(cell not in blocked for cell in cells):
              return True
  return False


def _random_scene(width, height, side, offset, keys, fills, num_shapes):
  for attempt in range(400):
    w = width if width is not None else _sample_side_length()
    h = height if height is not None else _sample_side_length()
    s = side if side is not None else random.choice(_SIDES)
    edge = w if s in ('top', 'bottom') else h
    if keys is not None:
      k = len(keys)
    elif fills is not None:
      k = len(fills)
    else:
      kmax = min(7, edge)
      if kmax < 2:
        continue
      k = random.randint(2, kmax)
    if offset is not None:
      o = offset
    else:
      lo, hi = (1, edge - 3) if k == 2 else (0, edge - k)
      if hi < lo:
        continue
      o = random.randint(lo, hi)
    ks = list(keys) if keys is not None else random.sample(range(1, 10), k)
    fs = (list(fills) if fills is not None
          else [random.randint(1, 9) for _ in range(k)])
    if _legend_problem(w, h, s, o, ks, fs) is not None:
      continue
    if _always_ambiguous(s, ks, fs):
      continue
    if num_shapes is not None:
      target = num_shapes
    else:
      lo_t = 2 if attempt < 200 else 1
      target = random.randint(lo_t, max(lo_t, min(_MAX_SHAPES,
                                                  1 + (w * h) // 40)))
    others = [c for c in range(1, 10) if c not in ks]
    fill_only = sorted(set(c for c in fs if c not in ks))
    pair_ok = len(set(ks) | set(fs)) >= 3
    # One key outline is always present; a closed non-key outline is also
    # guaranteed when there is room for two objects and a free colour.
    kinds = ['key']
    if target >= 2 and others:
      kinds.append('other')
    while len(kinds) < target:
      options, weights = ['key', 'other', 'open'], [40, 25, 20]
      if pair_ok:
        options.append('pair')
        weights.append(15)
      kind = random.choices(options, weights)[0]
      if kind == 'other' and not others:
        kind = 'key'
      kinds.append(kind)
    random.shuffle(kinds)
    big = min(w, h) >= 16
    blocked = set()
    for (y, x), _ in _legend_cells(w, h, s, o, ks, fs):
      _dilate(blocked, y, x)
    shapes = []
    for kind in kinds:
      sprite = _random_sprite(kind, h, w, big)
      if sprite is None:
        break
      color2 = None
      if kind == 'other':
        pool = fill_only if fill_only and random.random() < 0.55 else others
        color = random.choice(pool)
      elif kind == 'open' and others and random.random() < 0.3:
        color = random.choice(others)
      elif kind == 'pair':
        color = random.choice(ks)
        color2 = random.choice([c for c in range(1, 10) if c != color])
      else:
        color = random.choice(ks)
      cells = [(i, j) for i, row in enumerate(sprite)
               for j, ch in enumerate(row) if ch != '.']
      sh, sw = len(sprite), len(sprite[0])
      placed = False
      for _ in range(40):
        r, c = random.randint(0, h - sh), random.randint(0, w - sw)
        if all((r + i, c + j) not in blocked for i, j in cells):
          for i, j in cells:
            _dilate(blocked, r + i, c + j)
          if color2 is None:
            shapes.append((r, c, color, sprite))
          else:
            shapes.append((r, c, color, sprite, color2))
          placed = True
          break
      if not placed:
        break
    if len(shapes) != target:
      continue
    result, _ = _render(w, h, s, o, ks, fs, shapes)
    if result is None:
      continue
    grid, output, comps = result
    zeros = sum(v == 0 for row in grid for v in row)
    if zeros * 2 <= w * h:
      continue
    if grid == output:
      continue
    if any(_apply(grid, comps, alt) == output
           for alt in _alt_mappings(s, ks, fs)):
      continue
    return grid, output
  raise ValueError('could not build a dbff022c scene with the requested '
                   'parameters')


def generate(width=None, height=None, legend_side=None, legend_offset=None,
             keys=None, fills=None, shapes=None, num_shapes=None):
  """Returns an input/output pair.

  Args:
    width: grid width (number of columns), integer 3..30. When None, sampled
      mostly from 4..20 and sometimes from 21..30.
    height: grid height (number of rows), integer 3..30. Sampled like width
      when None.
    legend_side: the edge the legend touches: 'top', 'bottom', 'left' or
      'right'.
    legend_offset: non-negative integer index along that edge where the
      legend starts.
    keys: distinct key colours (1..9), listed along the edge. These form the
      line that touches the edge.
    fills: fill colours (1..9) paired with the keys. These form the line
      next to the key line.
    shapes: list of 1..8 (row, col, colour, sprite) or (row, col, colour,
      sprite, colour2) tuples. A sprite is a list of equal-length strings:
      '#' is an outline cell of colour, '%' an outline cell of colour2, 'o'
      an enclosed hole cell and '.' untouched background. A hole bordered by
      both colours stays empty. When shapes is given, width, height,
      legend_side, legend_offset, keys and fills are all required, and at
      least one hole must change colour. Explicit scenes are drawn as given;
      the orientation-revealing check is not applied to them.
    num_shapes: number of objects, integer 1..8. When shapes is given, it
      must equal len(shapes).
  If shapes is None, a fresh random scene is sampled. Any other argument
  that is supplied is honoured as a constraint. ValueError is raised for
  invalid or incompatible arguments. This includes a legend that some wrong
  reading cannot tell apart from the true one, a corner 2x2 legend, and a
  grid with no room for even one holed object.
  """
  if legend_side is not None and legend_side not in _SIDES:
    raise ValueError('legend_side must be one of %s' % (_SIDES,))
  problem = _colour_problem(keys, fills)
  if problem is not None:
    raise ValueError(problem)
  if num_shapes is not None and (not _is_int(num_shapes)
                                 or not 1 <= num_shapes <= _MAX_SHAPES):
    raise ValueError('num_shapes must be an integer within 1..%d'
                     % _MAX_SHAPES)
  if legend_offset is not None and (not _is_int(legend_offset)
                                    or legend_offset < 0):
    raise ValueError('legend_offset must be a non-negative integer')
  for v in (width, height):
    if v is not None and (not _is_int(v) or not 3 <= v <= 30):
      raise ValueError('grid sides must be integers within 3..30')
  if shapes is not None:
    params = (width, height, legend_side, legend_offset, keys, fills)
    if any(p is None for p in params):
      raise ValueError('explicit shapes require every legend/grid parameter')
    problem = _shape_problem(shapes)
    if problem is not None:
      raise ValueError(problem)
    if num_shapes is not None and num_shapes != len(shapes):
      raise ValueError('num_shapes disagrees with len(shapes)')
    problem = _legend_problem(width, height, legend_side, legend_offset,
                              keys, fills)
    if problem is not None:
      raise ValueError(problem)
    result, reason = _render(width, height, legend_side, legend_offset,
                             keys, fills, shapes)
    if result is None:
      raise ValueError(reason)
    grid, output, _ = result
    if grid == output:
      raise ValueError('explicit scene has no key-coloured hole to fill')
    return {'input': grid, 'output': output}
  sides = [legend_side] if legend_side is not None else list(_SIDES)
  if keys is not None and fills is not None:
    if all(_always_ambiguous(s, keys, fills) for s in sides):
      raise ValueError('this legend reads the same under a wrong reading; '
                       'no scene can reveal which line holds the keys')
  k_fixed = None
  if keys is not None:
    k_fixed = len(keys)
  elif fills is not None:
    k_fixed = len(fills)
  if k_fixed == 2 and legend_offset == 0:
    raise ValueError('a 2x2 legend in a corner has an ambiguous orientation')
  if legend_side is not None and k_fixed is not None:
    edge = width if legend_side in ('top', 'bottom') else height
    if edge is not None:
      if k_fixed > edge:
        raise ValueError('legend does not fit along its edge')
      if (k_fixed == 2 and legend_offset is not None
          and legend_offset + 2 == edge):
        raise ValueError('a 2x2 legend in a corner has an ambiguous '
                         'orientation')
  if width is not None and height is not None:
    if not _feasible(width, height, sides, k_fixed, legend_offset):
      raise ValueError('grid too small for a legend plus a holed object')
  grid, output = _random_scene(width, height, legend_side, legend_offset,
                               keys, fills, num_shapes)
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the original task pairs from explicit latent parameters."""
  train = [
      generate(12, 12, 'top', 7, [3, 4, 6, 9, 5], [3, 6, 7, 2, 9], [
          (0, 1, 4, ['#####', '#o#o#', '#####']),
          (4, 1, 3, ['####', '#oo#', '#oo#', '#oo#', '.#o#', '..#.']),
          (6, 7, 7, ['####', '#o##', '#oo#', '##o#', '####']),
      ]),
      generate(10, 10, 'left', 0, [2, 4, 6, 8], [6, 5, 8, 1], [
          (0, 4, 8, ['####', '#oo#', '#oo#', '####']),
          (5, 1, 5, ['#####', '#ooo#', '.####']),
          (5, 7, 4, ['###', '#o#', '###', '#o#', '###']),
      ]),
      generate(15, 4, 'top', 1, [2, 6], [7, 1], [
          (0, 4, 4, ['#####', '#ooo#', '#ooo#', '#####']),
          (0, 10, 2, ['####', '#o##', '##o#', '####']),
      ]),
  ]
  test = [
      generate(13, 13, 'bottom', 0, [9, 8, 3, 1, 2], [5, 4, 6, 7, 8], [
          (0, 1, 1, ['#####', '#ooo#', '##oo#', '.####']),
          (0, 8, 3, ['####', '#oo#', '#oo#', '####']),
          (6, 1, 2, ['.#.', '#o#', '.#.']),
          (5, 7, 5, ['.###..', '#ooo#.', '#oooo#', '.#####', '.#....']),
          (10, 9, 2, ['.#.', '#o#', '.#.']),
      ]),
  ]
  return {'train': train, 'test': test}
