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

"""ARC-GEN style generator for task 4acc7107.

Rule: the input has four objects on a black background. There are two
colours and two objects of each colour. The "left" colour is the colour of
the object whose bounding box starts furthest left.

The output clears the canvas and builds two columns:
- Left-colour objects are left-aligned at x = 0.
- Other-colour objects are left-aligned at x = (width of the widest
  left-colour object) + 1.
- Each column stacks upward from the bottom row, with one empty row between
  objects.

The stacking order comes from pairing. Take the left-colour objects from
largest to smallest, breaking ties in reading order of the bounding box.
Each one claims the nearest unclaimed other-colour object. Distance is the
minimum Chebyshev distance between cells. The first pair sits at the bottom
and the second pair sits above it.

Scope (random generation):
- Grid sides are 8..30 by default. Any explicit width or height in 8..30 is
  honoured. Sizes other than 10x10 are synthetic extensions.
- Two distinct non-black colours. An explicit `colors` value is
  (left_colour, other_colour), and that pair is enforced.
- Random 4-connected shapes: lines, rectangles and grown polyominoes of
  3..10 cells.
- Same-colour objects are separated, diagonals included. Different colours
  may touch as in the canonical examples, but cannot overlap.

The sampler rejects scenes in which:
- the left colour is ambiguous;
- the two left-colour objects have equal size;
- the largest left-colour object is equally near both candidates;
- the stacks would not fit;
- the output would equal the input.

The canonical fixtures are rebuilt from explicit object specifications
through generate(objects=...).
"""

import random

import common


def _cells(pattern):
  return [(r, c) for r, row in enumerate(pattern)
          for c, ch in enumerate(row) if ch == "#"]


def _normalize(cells):
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  return sorted((r - r0, c - c0) for r, c in cells)


def _random_shape(max_dim):
  """Returns a random 4-connected shape that fits in max_dim+1 squared."""
  roll = random.random()
  if roll < 0.15:
    return [(0, c) for c in range(random.randint(3, max_dim + 1))]
  if roll < 0.25:
    return [(r, 0) for r in range(random.randint(3, max_dim))]
  if roll < 0.4:
    h, w = random.randint(2, 3), random.randint(2, 3)
    return [(r, c) for r in range(h) for c in range(w)]
  maxh, maxw = random.randint(2, max_dim), random.randint(2, max_dim)
  size = random.randint(3, min(10, maxh * maxw))
  cells = {(random.randrange(maxh), random.randrange(maxw))}
  for _ in range(400):
    if len(cells) >= size:
      break
    r, c = random.choice(sorted(cells))
    dr, dc = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
    nr, nc = r + dr, c + dc
    if 0 <= nr < maxh and 0 <= nc < maxw:
      cells.add((nr, nc))
  if len(cells) < 3:
    return None
  return _normalize(cells)


def _box(cells):
  rows = [r for r, _ in cells]
  cols = [c for _, c in cells]
  return min(rows), min(cols), max(rows), max(cols)


def _dist(c1, c2):
  return min(max(abs(a[0] - b[0]), abs(a[1] - b[1])) for a in c1 for b in c2)


def _analyse(objs):
  """Returns (left colour, sorted group A, group B, pairs)."""
  leftmost = min(objs, key=lambda o: (_box(o[1])[1], _box(o[1])[0]))
  leftc = leftmost[0]
  group_a = [o for o in objs if o[0] == leftc]
  group_b = [o for o in objs if o[0] != leftc]
  group_b.sort(key=lambda o: (_box(o[1])[0], _box(o[1])[1]))
  group_a.sort(key=lambda o: (-len(o[1]), _box(o[1])[0], _box(o[1])[1]))
  remaining = list(group_b)
  pairs = []
  for a in group_a:
    if remaining:
      b = min(remaining, key=lambda o: _dist(a[1], o[1]))
      remaining.remove(b)
    else:
      b = None
    pairs.append((a, b))
  for b in remaining:
    pairs.append((None, b))
  return leftc, group_a, group_b, pairs


def _render_output(width, height, group_a, pairs):
  out = common.grid(width, height, 0)
  widths = [_box(o[1])[3] - _box(o[1])[1] + 1 for o in group_a]
  xb = (max(widths) if widths else 0) + 1
  bottoms = {0: height - 1, 1: height - 1}

  def place(obj, colx, key):
    y0, x0, y1, _ = _box(obj[1])
    top = bottoms[key] - (y1 - y0)
    for y, x in obj[1]:
      ny, nx = top + (y - y0), colx + (x - x0)
      if 0 <= ny < height and 0 <= nx < width:
        out[ny][nx] = obj[0]
    bottoms[key] = top - 2

  for a, b in pairs:
    if a is not None:
      place(a, 0, 0)
    if b is not None:
      place(b, xb, 1)
  return out


def _render_input(width, height, objs):
  grid = common.grid(width, height, 0)
  for colour, cells in objs:
    for r, c in cells:
      grid[r][c] = colour
  return grid


def _scene_ok(width, height, objs, left_colour):
  leftc, group_a, group_b, pairs = _analyse(objs)
  if leftc != left_colour:
    return False
  if len(group_a) != 2 or len(group_b) != 2:
    return False
  min_col = min(_box(o[1])[1] for o in objs)
  if any(o[0] != leftc for o in objs if _box(o[1])[1] == min_col):
    return False
  if len(group_a[0][1]) == len(group_a[1][1]):
    return False
  if _dist(group_a[0][1], group_b[0][1]) == _dist(group_a[0][1],
                                                  group_b[1][1]):
    return False
  heights_a = [_box(o[1])[2] - _box(o[1])[0] + 1 for o in group_a]
  heights_b = [_box(o[1])[2] - _box(o[1])[0] + 1 for o in group_b]
  if sum(heights_a) + 1 > height or sum(heights_b) + 1 > height:
    return False
  wa = max(_box(o[1])[3] - _box(o[1])[1] + 1 for o in group_a)
  wb = max(_box(o[1])[3] - _box(o[1])[1] + 1 for o in group_b)
  if wa + 1 + wb > width:
    return False
  inp = _render_input(width, height, objs)
  out = _render_output(width, height, group_a, pairs)
  return inp != out


def _random_scene(width, height, colors):
  for _ in range(3000):
    if height is not None:
      h_grid = height
    else:
      h_grid = 10 if random.random() < 0.3 else random.randint(8, 30)
    if width is not None:
      w_grid = width
    else:
      w_grid = 10 if random.random() < 0.3 else random.randint(8, 30)
    if colors is not None:
      ca, cb = colors
    else:
      ca, cb = random.sample(range(1, 10), 2)
    max_dim = 4 if min(h_grid, w_grid) < 12 else 5
    objs = []
    failed = False
    for colour in (ca, ca, cb, cb):
      shape = _random_shape(max_dim)
      if shape is None:
        failed = True
        break
      sh = max(r for r, _ in shape) + 1
      sw = max(c for _, c in shape) + 1
      if sh > h_grid or sw > w_grid:
        failed = True
        break
      placed = False
      for _ in range(100):
        top = random.randint(0, h_grid - sh)
        left = random.randint(0, w_grid - sw)
        cells = [(top + r, left + c) for r, c in shape]
        if all(_dist(cells, o[1]) >= (2 if o[0] == colour else 1) for o in objs):
          objs.append((colour, cells))
          placed = True
          break
      if not placed:
        failed = True
        break
    if failed:
      continue
    if _scene_ok(w_grid, h_grid, objs, ca):
      return w_grid, h_grid, objs
  raise RuntimeError("could not construct a valid 4acc7107 scene")


def generate(width=None, height=None, colors=None, objects=None):
  """Generates one input/output pair.

  Args:
    width: grid width. For random scenes it must be in 8..30 and is
      honoured exactly. With `objects` it defaults to 10.
    height: grid height. Same conventions as width.
    colors: optional (left_colour, other_colour) for random scenes. These are
      two distinct colours in 1..9. The sampler enforces that left_colour is
      the colour of the leftmost object. This cannot be combined with
      `objects`.
    objects: optional explicit list of (colour, top, left, pattern) tuples.
      Each pattern is a list of strings in which '#' marks a cell. When this
      is given the scene is built exactly as specified.
  """
  if objects is not None:
    if colors is not None:
      raise ValueError("colors cannot be combined with explicit objects")
    width = 10 if width is None else width
    height = 10 if height is None else height
    if not 1 <= width <= 30 or not 1 <= height <= 30:
      raise ValueError("grid sides must be in 1..30")
    if len(objects) != 4:
      raise ValueError("expected four objects")
    objs = []
    used = set()
    for colour, top, left, pattern in objects:
      if colour not in range(1, 10):
        raise ValueError("object colour must be in 1..9")
      cells = [(top + r, left + c) for r, c in _cells(pattern)]
      if not cells:
        raise ValueError("object must be nonempty")
      reached = {cells[0]}
      pending = [cells[0]]
      while pending:
        y, x = pending.pop()
        for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
          p = (y + dy, x + dx)
          if p in cells and p not in reached:
            reached.add(p)
            pending.append(p)
      if len(reached) != len(cells):
        raise ValueError("object must be connected")
      if any(other[0] == colour and _dist(cells, other[1]) < 2 for other in objs):
        raise ValueError("same-colour objects must be separated")
      for r, c in cells:
        if not (0 <= r < height and 0 <= c < width) or (r, c) in used:
          raise ValueError("object out of bounds or overlapping")
        used.add((r, c))
      objs.append((colour, cells))
    palette = set(o[0] for o in objs)
    if len(palette) != 2 or any(sum(o[0] == c for o in objs) != 2 for c in palette):
      raise ValueError("expected two objects of each colour")
  else:
    for side in (width, height):
      if side is not None and not 8 <= side <= 30:
        raise ValueError("random grid sides must be in 8..30")
    if colors is not None:
      if (len(colors) != 2 or colors[0] == colors[1]
          or not all(1 <= c <= 9 for c in colors)):
        raise ValueError("colors must be two distinct colours in 1..9")
      colors = (colors[0], colors[1])
    width, height, objs = _random_scene(width, height, colors)
  _, group_a, _, pairs = _analyse(objs)
  return {
      "input": _render_input(width, height, objs),
      "output": _render_output(width, height, group_a, pairs),
  }


def validate():
  """Reconstructs the canonical fixtures from explicit object specs."""
  train = [
      generate(objects=[
          (8, 1, 0, ["##.", "#..", "###"]),
          (4, 1, 4, ["..#.", "####", "..#."]),
          (4, 5, 5, ["####"]),
          (8, 6, 2, [".##.", "####"]),
      ]),
      generate(objects=[
          (3, 2, 1, ["####", "##..", "##.."]),
          (3, 2, 7, ["###"]),
          (4, 4, 4, ["###", ".##", ".#."]),
          (4, 6, 7, [".#", ".#", "##"]),
      ]),
      generate(objects=[
          (7, 1, 0, [".##.", "####", ".##."]),
          (9, 1, 6, ["###", "###"]),
          (9, 5, 2, ["#####"]),
          (7, 7, 6, ["###", "###"]),
      ]),
      generate(objects=[
          (1, 0, 2, [".#.", "###"]),
          (6, 2, 6, ["#.", "##"]),
          (6, 3, 0, ["##", "##"]),
          (1, 5, 1, [".###", "####"]),
      ]),
  ]
  test = [
      generate(objects=[
          (2, 1, 0, ["####", "...#", "..##"]),
          (3, 1, 6, ["###"]),
          (3, 5, 1, ["..##", "####", "..#."]),
          (2, 6, 6, ["###", "###"]),
      ]),
  ]
  return {"train": train, "test": test}
