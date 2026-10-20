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

"""ARC task de809cff: clean overlapping noisy rectangles and mark their holes.

Rule:
  The input is a black grid with a few large solid rectangles drawn in exactly
  two colours. Rectangles of different colours may overlap, and the rectangle
  painted later covers the overlap. The rectangles are noisy in three ways.
  Holes are 0 cells inside a rectangle. Foreign pixels are cells inside a
  rectangle that carry the other colour. Strays are isolated coloured pixels
  on the black background.
  In the output, strays vanish and the rectangles are redrawn cleanly in the
  same stacking order. The overlap goes to the colour that dominates it in the
  input. Every hole becomes an 8 surrounded by a 3x3 frame in the other
  colour. All frames are stamped in row-major order before any 8 is placed, so
  neighbouring holes form merged frames. Frames may spill onto black cells and
  are clipped at the grid border.

Scope:
  The generator samples the grid size (14..30 per side) and 2 to 4 rectangles
  that form a connected overlap graph. It properly two-colours them using two
  distinct colours other than 0 and 8, and samples a random stacking order.
  Hole groups can be singles, horizontal or vertical dominoes, or diagonal
  pairs. It also samples sparse foreign pixels and isolated strays.
  Each scene must satisfy these invariants:
    - Rectangles of the same colour never overlap or touch.
    - Every rectangle stays recognisable from its 2x2 solid core. The core is
      4-connected and has the full rectangle as its bounding box.
    - For every overlapping pair, the input fraction of own-colour overlap
      cells strictly increases with stacking order, so the dominance rule is
      unambiguous.
  Original fixtures are rebuilt from explicit latent lists: rectangles in
  paint order, holes, foreign pixels and strays.
"""

import random

import common

_PALETTE = [1, 2, 3, 4, 5, 6, 7, 9]


def _cheb(a, b):
  return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _paint(width, height, rects):
  grid = common.grid(width, height, 0)
  for color, top, left, bottom, right in rects:
    for y in range(top, bottom + 1):
      for x in range(left, right + 1):
        grid[y][x] = color
  return grid


def _noisy(clean, holes, foreign, strays):
  grid = [row[:] for row in clean]
  for y, x in holes:
    grid[y][x] = 0
  for y, x, c in foreign:
    grid[y][x] = c
  for y, x, c in strays:
    grid[y][x] = c
  return grid


def _inside(rect, y, x):
  return rect[1] <= y <= rect[3] and rect[2] <= x <= rect[4]


def _recognisable(grid, rects, width, height):
  """Checks that each rectangle is recoverable from its solid 2x2 core."""
  for color in set(r[0] for r in rects):
    core = set()
    for y in range(height - 1):
      for x in range(width - 1):
        if (grid[y][x] == color and grid[y][x + 1] == color and
            grid[y + 1][x] == color and grid[y + 1][x + 1] == color):
          core.update([(y, x), (y, x + 1), (y + 1, x), (y + 1, x + 1)])
    mine = [r for r in rects if r[0] == color]
    for y, x in core:
      if not any(_inside(r, y, x) for r in mine):
        return False
    for r in mine:
      sub = set(p for p in core if _inside(r, p[0], p[1]))
      if len(sub) < 9:
        return False
      ys = [p[0] for p in sub]
      xs = [p[1] for p in sub]
      if (min(ys), min(xs), max(ys), max(xs)) != (r[1], r[2], r[3], r[4]):
        return False
      start = next(iter(sub))
      seen = {start}
      stack = [start]
      while stack:
        cy, cx = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
          q = (cy + dy, cx + dx)
          if q in sub and q not in seen:
            seen.add(q)
            stack.append(q)
      if len(seen) != len(sub):
        return False
  return True


def _dominance_ok(grid, rects):
  """The own-colour overlap share must increase strictly with paint order."""
  shares = []
  for i, (c, t, l, b, r) in enumerate(rects):
    tot = own = 0
    for j, (_, t2, l2, b2, r2) in enumerate(rects):
      if j == i:
        continue
      ya, yb, xa, xb = max(t, t2), min(b, b2), max(l, l2), min(r, r2)
      if ya > yb or xa > xb:
        continue
      for y in range(ya, yb + 1):
        for x in range(xa, xb + 1):
          tot += 1
          own += 1 if grid[y][x] == c else 0
    if tot == 0:
      return False
    shares.append(own / tot)
  for i in range(len(rects)):
    for j in range(i + 1, len(rects)):
      a, b = rects[i], rects[j]
      if a[1] <= b[3] and b[1] <= a[3] and a[2] <= b[4] and b[2] <= a[4]:
        if not shares[i] + 0.05 < shares[j]:
          return False
  return True


def _try_scene(width, height):
  h, w = height, width
  n = random.choice([2, 2, 3, 3, 3, 4]) if min(w, h) >= 18 else random.choice(
      [2, 2, 3])
  boxes = []
  for _ in range(n):
    rh = random.randint(6, max(6, (h * 7) // 10))
    rw = random.randint(6, max(6, (w * 7) // 10))
    if rh > h or rw > w:
      return None
    if not boxes:
      top = random.randint(0, h - rh)
      left = random.randint(0, w - rw)
    else:
      p = random.choice(boxes)
      lo, hi = max(0, p[0] - rh + 3), min(h - rh, p[2] - 2)
      lo2, hi2 = max(0, p[1] - rw + 3), min(w - rw, p[3] - 2)
      if lo > hi or lo2 > hi2:
        return None
      top = random.randint(lo, hi)
      left = random.randint(lo2, hi2)
    boxes.append((top, left, top + rh - 1, left + rw - 1))

  def near(a, b):
    return (a[0] <= b[2] + 1 and b[0] <= a[2] + 1 and
            a[1] <= b[3] + 1 and b[1] <= a[3] + 1)

  side = [None] * n
  side[0] = 0
  stack = [0]
  while stack:
    i = stack.pop()
    for j in range(n):
      if j != i and near(boxes[i], boxes[j]) and side[j] is None:
        side[j] = 1 - side[i]
        stack.append(j)
  if any(s is None for s in side):
    return None
  for i in range(n):
    for j in range(i + 1, n):
      if near(boxes[i], boxes[j]) and side[i] == side[j]:
        return None
  c1, c2 = random.sample(_PALETTE, 2)
  colors = (c1, c2)
  other = {c1: c2, c2: c1}
  order = list(range(n))
  random.shuffle(order)
  rects = [(colors[side[i]],) + boxes[i] for i in order]
  clean = _paint(w, h, rects)

  union = [(y, x) for y in range(h) for x in range(w) if clean[y][x]]
  area = len(union)
  target = random.randint(max(2, area // 70), max(3, area // 28))
  shapes = ([[(0, 0)]] * 7 + [[(0, 0), (0, 1)], [(0, 0), (1, 0)],
                              [(0, 0), (1, 1)], [(0, 1), (1, 0)]])
  holes = []
  groups = 0
  for _ in range(target * 30):
    if groups >= target:
      break
    y, x = random.choice(union)
    col = clean[y][x]
    cells = [(y + dy, x + dx) for dy, dx in random.choice(shapes)]
    if any(not (0 <= cy < h and 0 <= cx < w) or clean[cy][cx] != col
           for cy, cx in cells):
      continue
    ok = True
    for hc in holes:
      need = 2 if clean[hc[0]][hc[1]] == col else 3
      if any(_cheb(hc, cc) < need for cc in cells):
        ok = False
        break
    if ok:
      holes.extend(cells)
      groups += 1
  if groups < 2:
    return None

  foreign = []
  k = random.choice([0, 0, 1, 1, 2, 2, 3, 4])
  for _ in range(80):
    if len(foreign) >= k:
      break
    y, x = random.choice(union)
    if any(_cheb((y, x), hc) < 2 for hc in holes):
      continue
    if any(_cheb((y, x), f[:2]) < 2 for f in foreign):
      continue
    foreign.append((y, x, other[clean[y][x]]))

  free = []
  for y in range(h):
    for x in range(w):
      if all(clean[yy][xx] == 0
             for yy in range(max(0, y - 1), min(h, y + 2))
             for xx in range(max(0, x - 1), min(w, x + 2))):
        free.append((y, x))
  random.shuffle(free)
  k = random.randint(1, 7)
  strays = []
  for y, x in free:
    if len(strays) >= k:
      break
    if any(_cheb((y, x), s[:2]) < 2 for s in strays):
      continue
    strays.append((y, x, random.choice(colors)))

  grid = _noisy(clean, holes, foreign, strays)
  if not _recognisable(grid, rects, w, h):
    return None
  if not _dominance_ok(grid, rects):
    return None
  return rects, holes, foreign, strays


def _sample_scene(width=None, height=None):
  for _ in range(500):
    w = width if width is not None else random.randint(14, 30)
    h = height if height is not None else random.randint(14, 30)
    scene = _try_scene(w, h)
    if scene is not None:
      return (w, h) + scene
  raise RuntimeError("could not sample identifiable overlapping rectangles")


def generate(width=None, height=None, rects=None, holes=None, foreign=None,
             strays=None):
  """Returns an input/output pair for task de809cff.

  Args:
    width: grid width (14..30 when sampling; required with rects).
    height: grid height (14..30 when sampling; required with rects).
    rects: list of (color, top, left, bottom, right), inclusive, in paint order
      (later rectangles cover earlier ones where they overlap).
    holes: list of (row, col) cells inside the rectangle union set to 0.
    foreign: list of (row, col, color) pixels inside rectangles in the other
      colour.
    strays: list of (row, col, color) isolated pixels on the black background.
  """
  if any(v is not None and not 14 <= v <= 30 for v in (width, height)):
    raise ValueError("canvas dimensions must be 14..30")
  if rects is None:
    if any(v is not None for v in (holes, foreign, strays)):
      raise ValueError("explicit noise parameters require explicit rectangles")
    width, height, rects, holes, foreign, strays = _sample_scene(width, height)
  holes = list(holes or [])
  foreign = list(foreign or [])
  strays = list(strays or [])
  clean = _paint(width, height, rects)
  grid = _noisy(clean, holes, foreign, strays)
  palette = sorted(set(c for row in grid for c in row if c))
  output = [row[:] for row in clean]
  marks = sorted(set((y, x) for y, x in holes if clean[y][x]))
  for y, x in marks:
    own = clean[y][x]
    others = [c for c in palette if c != own]
    frame = others[0] if others else own
    for yy in range(max(0, y - 1), min(height, y + 2)):
      for xx in range(max(0, x - 1), min(width, x + 2)):
        output[yy][xx] = frame
  for y, x in marks:
    output[y][x] = 8
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the original fixtures from explicit latent parameters."""
  train = [
      generate(
          width=20, height=20,
          rects=[(3, 0, 1, 9, 12), (4, 7, 6, 17, 19), (3, 14, 0, 19, 9)],
          holes=[(0, 3), (1, 7), (1, 8), (2, 6), (3, 7), (3, 12), (6, 3),
                 (9, 16), (10, 10), (12, 13), (13, 12), (14, 2), (15, 17),
                 (16, 12), (16, 13), (17, 0), (17, 4)],
          foreign=[],
          strays=[(2, 15, 3), (4, 14, 4), (4, 18, 3), (11, 1, 3), (11, 3, 4),
                  (13, 4, 4), (19, 14, 4)]),
      generate(
          width=20, height=20,
          rects=[(1, 0, 0, 10, 10), (2, 8, 6, 19, 19)],
          holes=[(2, 5), (3, 4), (7, 5), (9, 4), (10, 14), (14, 8), (14, 14),
                 (14, 17), (16, 16), (18, 11), (18, 14), (19, 7)],
          foreign=[(7, 7, 2), (7, 9, 2)],
          strays=[(1, 14, 2), (2, 11, 1), (2, 18, 2), (4, 12, 1), (4, 15, 2),
                  (5, 18, 1), (7, 15, 2), (11, 1, 1), (12, 4, 1), (15, 1, 1),
                  (16, 5, 2), (18, 2, 1)]),
  ]
  test = [
      generate(
          width=30, height=30,
          rects=[(6, 1, 8, 10, 29), (1, 5, 1, 19, 20), (6, 19, 4, 29, 25)],
          holes=[(2, 10), (2, 18), (4, 25), (5, 26), (6, 4), (6, 13), (7, 28),
                 (10, 6), (10, 16), (11, 16), (13, 1), (13, 9), (15, 20),
                 (17, 3), (18, 16), (21, 14), (22, 22), (23, 6), (24, 17),
                 (24, 22), (26, 4), (26, 11), (28, 21), (28, 22)],
          foreign=[(4, 10, 1), (7, 21, 1), (9, 20, 6), (19, 8, 1)],
          strays=[(0, 4, 6), (3, 6, 6), (4, 2, 1), (11, 27, 6), (12, 22, 1),
                  (15, 26, 1), (17, 29, 6), (18, 22, 6), (22, 1, 6),
                  (22, 27, 6), (23, 3, 6), (23, 29, 6), (26, 0, 1),
                  (26, 26, 6), (28, 28, 6)]),
  ]
  return {"train": train, "test": test}
