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

"""ARC task 7acdf6d3: pour the loose filler cells into the cup that fits them.

Rule: the background is 7. One colour forms upward-opening cups. A cup is
either a V (a diagonal chain) or a U (two vertical walls on a horizontal
floor). The other colour is a set of loose filler cells, given as scattered
single cells or short straight bars. Exactly one cup's interior holds as many
background cells as there are filler cells. The interior is counted row by
row, as the background cells strictly between the cup's leftmost and
rightmost cells in that row. In the output the filler cells are erased and
that cup's interior is painted with the filler colour.

Scope: by default the grid size is sampled from 10 to 30 per side, which is a
synthetic extension of the 13 to 16 sizes in the fixtures. Grids need not be
square. The scene holds 2 to 4 cups by default, or 1 to 6 if num_cups is
given. V depths are 1 to 4, giving capacities 1, 4, 9 and 16. U cups have
inner width 1 to 4 and wall height 1 to 4. Depths and sizes above 3 are a
synthetic extension. Only the target cup has the matching capacity, so the
other cups act as distractors. The cup and filler roles of colours 2 and 9
are assigned at random. The filler is a single bar, fully scattered single
cells, or a mix of bars of length 1 to 3. No two filler pieces touch, even
diagonally. Every filler piece lies outside each cup's padded bounding box,
and cups are separated by at least one background cell. Cups always open
upward, because the row-wise interior metric only gives the intended
capacity for upright cups.

Explicit mode takes cups and fill and rejects scenes that would make the
rule ambiguous or degenerate. It rejects touching or nested cups, filler
inside a cup interior, filler shapes that have their own interior, and scenes
that do not have exactly one matching cup.
"""

import random

import common


BACKGROUND = 7
PALETTE = (2, 9)
MAX_SIZE = 4

_SHAPES = ([("V", k, 0) for k in range(1, MAX_SIZE + 1)] +
           [("U", w, h) for w in range(1, MAX_SIZE + 1)
            for h in range(1, MAX_SIZE + 1)])


def _cup_cells(kind, r, c, a, b):
  """Return (cells, interior) for a cup whose bounding box starts at (r, c).

  For kind "V", a is the depth and b must be zero. For kind "U", a is the
  inner width and b is the wall height.
  """
  cells, interior = [], []
  if kind == "V":
    k = a
    for i in range(k + 1):
      cells.append((r + i, c + i))
      if c + 2 * k - i != c + i:
        cells.append((r + i, c + 2 * k - i))
      for x in range(c + i + 1, c + 2 * k - i):
        interior.append((r + i, x))
  elif kind == "U":
    w, h = a, b
    for i in range(h):
      cells.append((r + i, c))
      cells.append((r + i, c + w + 1))
      for x in range(c + 1, c + w + 1):
        interior.append((r + i, x))
    for x in range(c, c + w + 2):
      cells.append((r + h, x))
  else:
    raise ValueError("unknown cup kind %r" % (kind,))
  return cells, interior


def _bbox(kind, a, b):
  """Return (rows, cols) of a cup's bounding box."""
  if kind == "V":
    return a + 1, 2 * a + 1
  return b + 1, a + 2


def _capacity(kind, a, b):
  return a * a if kind == "V" else a * b


def _random_shape(max_rows, max_cols, exclude_cap=None):
  """Pick a cup shape that fits the bounds, optionally avoiding a capacity."""
  options = []
  for s in _SHAPES:
    rows, cols = _bbox(*s)
    if rows > max_rows or cols > max_cols:
      continue
    if exclude_cap is not None and _capacity(*s) == exclude_cap:
      continue
    options.append(s)
  if not options:
    return None
  kinds = sorted(set(s[0] for s in options))
  kind = random.choice(kinds)
  return random.choice([s for s in options if s[0] == kind])


def _partition(n):
  """Split n filler cells into straight pieces."""
  roll = random.random()
  if n <= 6 and roll < 0.25:
    return [n]
  if roll < 0.5:
    return [1] * n
  parts, rem = [], n
  while rem > 0:
    p = random.randint(1, min(3, rem))
    parts.append(p)
    rem -= p
  random.shuffle(parts)
  return parts


def _sample_scene(width, height, ncups):
  """Try once to build a random scene. Return None if placement fails."""
  target_shape = _random_shape(height, width)
  if target_shape is None:
    return None
  cap = _capacity(*target_shape)
  shapes = [target_shape]
  for _ in range(ncups - 1):
    s = _random_shape(height, width, exclude_cap=cap)
    if s is None:
      return None
    shapes.append(s)
  order = list(range(len(shapes)))
  random.shuffle(order)
  blocked = set()
  cups = [None] * len(shapes)
  for idx in order:
    kind, a, b = shapes[idx]
    rows, cols = _bbox(kind, a, b)
    placed = False
    for _ in range(100):
      r = random.randint(0, height - rows)
      c = random.randint(0, width - cols)
      if any((y, x) in blocked for y in range(r, r + rows)
             for x in range(c, c + cols)):
        continue
      for y in range(r - 1, r + rows + 1):
        for x in range(c - 1, c + cols + 1):
          blocked.add((y, x))
      cups[idx] = (kind, r, c, a, b)
      placed = True
      break
    if not placed:
      return None
  fill = []
  for part in _partition(cap):
    placed = False
    for _ in range(200):
      vertical = part > 1 and random.random() < 0.5
      if vertical:
        if part > height:
          continue
        r = random.randint(0, height - part)
        c = random.randint(0, width - 1)
        cells = [(r + i, c) for i in range(part)]
      else:
        if part > width:
          continue
        r = random.randint(0, height - 1)
        c = random.randint(0, width - part)
        cells = [(r, c + i) for i in range(part)]
      if any(p in blocked for p in cells):
        continue
      for y, x in cells:
        for dy in (-1, 0, 1):
          for dx in (-1, 0, 1):
            blocked.add((y + dy, x + dx))
      fill.extend(cells)
      placed = True
      break
    if not placed:
      return None
  return cups, fill


def _other(color):
  if color == PALETTE[0]:
    return PALETTE[1]
  if color == PALETTE[1]:
    return PALETTE[0]
  return random.choice(PALETTE)


def _resolve_colors(cup_color, fill_color):
  if cup_color is None and fill_color is None:
    cup_color, fill_color = random.choice([(2, 9), (9, 2)])
  elif cup_color is None:
    cup_color = _other(fill_color)
  elif fill_color is None:
    fill_color = _other(cup_color)
  for col in (cup_color, fill_color):
    if type(col) is not int or not 0 <= col <= 9 or col == BACKGROUND:
      raise ValueError("colours must be 0..9 and differ from background 7")
  if cup_color == fill_color:
    raise ValueError("cup_color and fill_color must differ")
  return cup_color, fill_color


def _check_cup_tuple(cup):
  """Validate one explicit cup tuple and return it."""
  if not isinstance(cup, (tuple, list)) or len(cup) != 5:
    raise ValueError("each cup must be a (kind, row, col, a, b) tuple")
  kind, r, c, a, b = cup
  if kind not in ("V", "U"):
    raise ValueError("cup kind must be 'V' or 'U'")
  for v in (r, c, a, b):
    if type(v) is not int:
      raise ValueError("cup parameters must be integers")
  if not 1 <= a <= 28 or (kind == "U" and not 1 <= b <= 29) or (kind == "V" and b != 0):
    raise ValueError("cup sizes exceed grid limits or V unused b is not zero")
  return kind, r, c, a, b


def _components8(cells):
  """Group a set of cells into 8-connected components."""
  remaining = set(cells)
  comps = []
  while remaining:
    start = remaining.pop()
    stack, comp = [start], [start]
    while stack:
      y, x = stack.pop()
      for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
          q = (y + dy, x + dx)
          if q in remaining:
            remaining.remove(q)
            stack.append(q)
            comp.append(q)
    comps.append(comp)
  return comps


def generate(width=None, height=None, cup_color=None, fill_color=None,
             cups=None, fill=None, num_cups=None):
  """Return one input/output pair.

  Args:
    width: grid width, 6..30. Sampled from 10..30 when None (random mode).
    height: grid height, 6..30. Sampled from 10..30 when None (random mode).
    cup_color: colour of the cups. If only one of the two colours is given,
      the other is taken from {2, 9}.
    fill_color: colour of the loose filler cells.
    cups: explicit list of (kind, row, col, a, b) tuples. kind "V" uses a as
      the depth. kind "U" uses a as the inner width and b as the wall height.
      This must be given together with fill, width and height.
    fill: explicit list of (row, col) filler cells. This must be given
      together with cups.
    num_cups: number of cups, 1..6. In random mode it defaults to 2..4. In
      explicit mode, if given, it must equal len(cups). Small grids with many
      cups may be infeasible, and then a ValueError is raised.
  """
  cup_color, fill_color = _resolve_colors(cup_color, fill_color)
  for name, v in (("width", width), ("height", height)):
    if v is not None and (type(v) is not int or not 6 <= v <= 30):
      raise ValueError("%s must be in 6..30" % name)
  if num_cups is not None and (type(num_cups) is not int or not 1 <= num_cups <= 6):
    raise ValueError("num_cups must be in 1..6")
  explicit = cups is not None or fill is not None
  if explicit:
    if cups is None or fill is None or width is None or height is None:
      raise ValueError("explicit mode needs cups, fill, width and height")
    if num_cups is not None and num_cups != len(cups):
      raise ValueError("num_cups does not match len(cups)")
    cups = [_check_cup_tuple(cup) for cup in cups]
    if any(not isinstance(p, (tuple, list)) or len(p) != 2 or
           any(type(v) is not int for v in p) for p in fill):
      raise ValueError("filler coordinates must be integer pairs")
    fill = [tuple(p) for p in fill]
  else:
    scene = None
    for _ in range(500):
      w = width if width is not None else random.randint(10, 30)
      h = height if height is not None else random.randint(10, 30)
      n_c = num_cups if num_cups is not None else random.randint(2, 4)
      scene = _sample_scene(w, h, n_c)
      if scene is not None:
        width, height = w, h
        break
    if scene is None:
      raise ValueError("could not place a scene with the requested settings")
    cups, fill = scene

  grid = common.grid(width, height, BACKGROUND)
  owner = {}
  all_interior = {}
  shapes = []
  for idx, (kind, r, c, a, b) in enumerate(cups):
    cells, interior = _cup_cells(kind, r, c, a, b)
    for y, x in cells:
      if not (0 <= y < height and 0 <= x < width):
        raise ValueError("cup out of bounds")
      if (y, x) in owner:
        raise ValueError("overlapping cups")
      owner[(y, x)] = idx
      grid[y][x] = cup_color
    for p in interior:
      all_interior[p] = idx
    shapes.append((cells, interior))

  # Cups must be separate 8-connected components and must not nest.
  for (y, x), idx in owner.items():
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        other = owner.get((y + dy, x + dx))
        if other is not None and other != idx:
          raise ValueError("cups touch; they would merge into one component")
    if (y, x) in all_interior and all_interior[(y, x)] != idx:
      raise ValueError("a cup lies inside another cup's interior")

  fill_set = set()
  for y, x in fill:
    if not (0 <= y < height and 0 <= x < width):
      raise ValueError("filler out of bounds")
    if grid[y][x] != BACKGROUND:
      raise ValueError("filler overlaps a cup or another filler cell")
    if (y, x) in all_interior:
      raise ValueError("filler lies inside a cup interior")
    grid[y][x] = fill_color
    fill_set.add((y, x))
  n = len(fill_set)
  if n == 0:
    raise ValueError("there must be at least one filler cell")

  # Filler shapes must not themselves act as cups (role ambiguity).
  for comp in _components8(fill_set):
    rows = {}
    for y, x in comp:
      rows.setdefault(y, []).append(x)
    for y, xs in rows.items():
      for x in range(min(xs) + 1, max(xs)):
        if grid[y][x] == BACKGROUND:
          raise ValueError("filler cells enclose background; roles ambiguous")

  matches = [interior for _, interior in shapes
             if interior and len(interior) == n]
  if len(matches) != 1:
    raise ValueError("exactly one cup must hold as many cells as the filler")

  counts = {col: sum(v == col for line in grid for v in line)
            for col in (BACKGROUND, cup_color, fill_color)}
  if counts[BACKGROUND] <= max(counts[cup_color], counts[fill_color]):
    raise ValueError("background must be the unique majority colour")

  output = [row[:] for row in grid]
  for y, x in fill_set:
    output[y][x] = BACKGROUND
  for y, x in matches[0]:
    output[y][x] = fill_color
  return {"input": grid, "output": output}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=16, height=16, cup_color=2, fill_color=9,
               cups=[("V", 5, 4, 1, 0), ("V", 6, 10, 2, 0)],
               fill=[(13, 7)]),
      generate(width=13, height=13, cup_color=2, fill_color=9,
               cups=[("V", 7, 6, 2, 0), ("V", 10, 1, 1, 0)],
               fill=[(1, 2), (1, 9), (4, 2), (4, 4)]),
  ]
  test = [
      generate(width=15, height=15, cup_color=9, fill_color=2,
               cups=[("U", 8, 8, 2, 2), ("U", 11, 2, 1, 1)],
               fill=[(11, 14), (12, 14), (13, 14), (14, 14)]),
  ]
  return {"train": train, "test": test}
