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

"""ARC-GEN style generator for task 6165ea8f.

Rule: the last column holds a legend of n single pixels, listed top-down
from row 0. Each legend colour also appears exactly once elsewhere as a
connected polyomino. The output is a (3(n+1)-1) x (3(n+1)-1) comparison
table of 2x2 blocks with 1-cell background gaps. Row-block 0 and
column-block 0 hold the legend colours in legend order. The corner block and
the diagonal blocks stay background. Block (i, j) is 2 when shapes i and j
are congruent under rotation and/or reflection, and 5 otherwise.

Scope: random scenes use 3..7 legend colours drawn from {1,3,4,6,7,8,9}.
Colours 0, 2 and 5 are reserved for the background and the table marks.
Shapes are random 4-connected polyominoes of 5..20 cells (or a requested
size up to 25). They are grouped
into 2..n-1 congruence classes, so every table contains both 2 and 5 marks.
Members of a class are random rotations/reflections of one base shape.
Distractors are included in two ways. Classes often share a cell count, and
some class bases are near-miss mutations of another base (one cell moved).
Shape bounding boxes are separated by at least one background cell. They
never touch the legend column or the column beside it. Input sizes are
sampled from roughly 10..30 per side. Sizes outside the 20..25 fixture range
are synthetic extensions.
"""

import random

import common

LEGEND_COLORS = [1, 3, 4, 6, 7, 8, 9]
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _rot(rows):
  h = len(rows)
  w = len(rows[0])
  return tuple("".join(rows[h - 1 - r][c] for r in range(h)) for c in range(w))


def _flip(rows):
  return tuple(r[::-1] for r in rows)


def _variants(rows):
  out = []
  cur = tuple(rows)
  for _ in range(4):
    out.append(cur)
    out.append(_flip(cur))
    cur = _rot(cur)
  return out


def _canon(rows):
  return min((len(v), len(v[0]), v) for v in _variants(rows))


def _cells_to_rows(cells):
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  h = max(r for r, _ in cells) - r0 + 1
  w = max(c for _, c in cells) - c0 + 1
  rows = []
  for r in range(h):
    rows.append("".join("#" if (r + r0, c + c0) in cells else "."
                        for c in range(w)))
  return tuple(rows)


def _rows_to_cells(rows):
  return {(r, c) for r, line in enumerate(rows)
          for c, ch in enumerate(line) if ch == "#"}


def _connected(cells):
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr, dc in DIRS:
      nb = (r + dr, c + dc)
      if nb in cells and nb not in seen:
        seen.add(nb)
        stack.append(nb)
  return len(seen) == len(cells)


def _polyomino(size, maxh, maxw):
  """Random 4-connected polyomino of `size` cells inside a maxh x maxw box."""
  for _ in range(200):
    start = (random.randrange(maxh), random.randrange(maxw))
    cells = {start}
    while len(cells) < size:
      frontier = []
      for (r, c) in cells:
        for dr, dc in DIRS:
          nr, nc = r + dr, c + dc
          if 0 <= nr < maxh and 0 <= nc < maxw and (nr, nc) not in cells:
            frontier.append((nr, nc))
      if not frontier:
        break
      cells.add(random.choice(frontier))
    if len(cells) != size:
      continue
    rows = _cells_to_rows(cells)
    if len(rows) >= 2 and len(rows[0]) >= 2:
      return rows
  return None


def _mutate(rows):
  """Near-miss distractor: move one cell, keeping the shape connected."""
  cells = _rows_to_cells(rows)
  for _ in range(40):
    rem = random.choice(sorted(cells))
    rest = cells - {rem}
    if not _connected(rest):
      continue
    frontier = sorted({(r + dr, c + dc) for (r, c) in rest
                       for dr, dc in DIRS} - cells)
    if not frontier:
      continue
    new = rest | {random.choice(frontier)}
    out = _cells_to_rows(new)
    if len(out) < 2 or len(out[0]) < 2 or len(out) > 8 or len(out[0]) > 8:
      continue
    return out
  return None


def _place(height, width, masks):
  """Places masks with >=1 cell gaps; shape columns limited to 0..width-3."""
  order = sorted(range(len(masks)),
                 key=lambda i: -len(masks[i]) * len(masks[i][0]))
  boxes = []
  pos = [None] * len(masks)
  for i in order:
    h = len(masks[i])
    w = len(masks[i][0])
    if height - h < 0 or width - 2 - w < 0:
      return None
    ok = False
    for _ in range(300):
      r = random.randint(0, height - h)
      c = random.randint(0, width - 2 - w)
      clash = False
      for (r2, c2, h2, w2) in boxes:
        if (r < r2 + h2 + 1 and r2 < r + h + 1 and
            c < c2 + w2 + 1 and c2 < c + w + 1):
          clash = True
          break
      if not clash:
        boxes.append((r, c, h, w))
        pos[i] = (r, c)
        ok = True
        break
    if not ok:
      return None
  return pos


def _random_scene(n, width, height, legend, num_classes, shape_cells=None):
  lo_h = max(10, n + 4)
  lo_w = 10 + n // 2
  for _ in range(60):
    if num_classes is not None:
      k = num_classes
    else:
      k = random.randint(2, n - 1)
    classes = list(range(k)) + [random.randrange(k) for _ in range(n - k)]
    random.shuffle(classes)
    common_size = (shape_cells if shape_cells is not None else
                   random.randint(5, 18) if random.random() < 0.5 else None)
    bases = []
    seen = set()
    for _ in range(k):
      base = None
      for _ in range(60):
        if bases and random.random() < 0.35:
          cand = _mutate(random.choice(bases))
        else:
          size = common_size if common_size else random.randint(5, 20)
          maxh = random.randint(2, 7)
          maxw = random.randint(3, 8)
          if size > maxh * maxw - 2:
            continue
          cand = _polyomino(size, maxh, maxw)
        if cand is None:
          continue
        key = _canon(cand)
        if key in seen:
          continue
        seen.add(key)
        base = cand
        break
      if base is None:
        break
      bases.append(base)
    if len(bases) != k:
      continue
    masks = [random.choice(_variants(bases[cl])) for cl in classes]
    if legend is not None:
      colors = list(legend)
    else:
      colors = random.sample(LEGEND_COLORS, n)
    for attempt in range(25):
      if height is not None:
        h = height
      elif attempt < 20:
        h = random.randint(lo_h, 30)
      else:
        h = 30
      if width is not None:
        w = width
      elif attempt < 20:
        w = random.randint(lo_w, 30)
      else:
        w = 30
      pos = _place(h, w, masks)
      if pos is not None:
        shapes = [(colors[i], pos[i][0], pos[i][1], list(masks[i]))
                  for i in range(n)]
        return w, h, colors, shapes
  raise ValueError("could not construct a scene with the given parameters")


def generate(width=None, height=None, legend=None, shapes=None, n=None,
             num_classes=None, shape_cells=None):
  """Builds one input/output pair.

  Args:
    width: grid width (the legend sits in the last column). Random scenes
      sample 10..30 when it is omitted.
    height: grid height; must be at least the legend length.
    legend: ordered list of legend colours (top to bottom). In random mode it
      fixes the colours and their order, and n defaults to len(legend).
    shapes: list of (color, row, col, mask_rows). mask_rows are strings of
      '#' (filled) and '.' (empty), placed with the top-left at (row, col).
      Explicit mode; width and height are then required.
    n: number of legend colours for random generation (3..7).
    num_classes: number of congruence classes for random generation
      (2..n-1).
    shape_cells: exact cell count of every random shape, in 5..25.
      All classes then have the same area, so area cannot decide similarity.
  """
  if width is not None and (type(width) is not int or not 5 <= width <= 30):
    raise ValueError("width must be in 5..30")
  if height is not None and (type(height) is not int or not 1 <= height <= 30):
    raise ValueError("height must be in 1..30")
  if shapes is None:
    if legend is not None:
      legend = list(legend)
      if (len(set(legend)) != len(legend) or
          any(c not in LEGEND_COLORS for c in legend)):
        raise ValueError("legend colours must be distinct, from 1,3,4,6,7,8,9")
      if n is not None and n != len(legend):
        raise ValueError("n conflicts with len(legend)")
      n = len(legend)
    if n is None:
      n = random.randint(3, 7)
    if type(n) is not int or not 3 <= n <= 7:
      raise ValueError("n must be in 3..7")
    if num_classes is not None and (type(num_classes) is not int or
                                    not 2 <= num_classes <= n - 1):
      raise ValueError("num_classes must be in 2..n-1")
    if shape_cells is not None and (type(shape_cells) is not int or
                                    not 5 <= shape_cells <= 25):
      raise ValueError("shape_cells must be an integer in 5..25")
    if height is not None and height < n:
      raise ValueError("height must be at least n")
    width, height, legend, shapes = _random_scene(n, width, height, legend,
                                                  num_classes, shape_cells)
  else:
    if width is None or height is None:
      raise ValueError("explicit shapes require width and height")
    if num_classes is not None or shape_cells is not None:
      raise ValueError("class/count controls only apply to random generation")
    if legend is None:
      legend = [s[0] for s in shapes]
    if sorted(legend) != sorted(s[0] for s in shapes):
      raise ValueError("legend must list each shape colour exactly once")
    if n is not None and n != len(legend):
      raise ValueError("n conflicts with the explicit legend")
    if height < len(legend):
      raise ValueError("height must be at least the legend length")
  if (not 2 <= len(legend) <= 7 or len(set(legend)) != len(legend)
      or any(type(c) is not int or c not in LEGEND_COLORS for c in legend)):
    raise ValueError("legend must have 2..7 distinct allowed colours")
  grid = common.grid(width, height, 0)
  canon = {}
  occupied = set()
  for color, r0, c0, rows in shapes:
    if (not rows or not rows[0] or any(len(row)!=len(rows[0]) for row in rows)
        or any(ch not in '#.' for row in rows for ch in row)
        or type(r0) is not int or type(c0) is not int):
      raise ValueError("shape needs a rectangular mask and integer origin")
    cells = _rows_to_cells(rows)
    if not _connected(cells) or _cells_to_rows(cells) != tuple(rows):
      raise ValueError("shape mask must be connected and tightly cropped")
    absolute = {(r0+y,c0+x) for y,x in cells}
    if any(not (0<=y<height and 0<=x<width-2) for y,x in absolute):
      raise ValueError("shape must fit outside the legend and its gap")
    if any((y+dy,x+dx) in occupied for y,x in absolute
           for dy in (-1,0,1) for dx in (-1,0,1)):
      raise ValueError("shapes must be separated")
    occupied.update(absolute)
    for dr, line in enumerate(rows):
      for dc, ch in enumerate(line):
        if ch == "#":
          grid[r0 + dr][c0 + dc] = color
    canon[color] = _canon(tuple(rows))
  for i, color in enumerate(legend):
    grid[i][width - 1] = color
  m = len(legend)
  size = 3 * (m + 1) - 1
  out = common.grid(size, size, 0)
  for i, color in enumerate(legend):
    p = 3 * (i + 1)
    for a in range(2):
      for b in range(2):
        out[a][p + b] = color
        out[p + a][b] = color
  for i, ca in enumerate(legend):
    for j, cb in enumerate(legend):
      if i == j:
        continue
      v = 2 if canon[ca] == canon[cb] else 5
      for a in range(2):
        for b in range(2):
          out[3 * (i + 1) + a][3 * (j + 1) + b] = v
  return {"input": grid, "output": out}


def validate():
  """Reconstructs the canonical fixtures from explicit latent scenes."""
  train = [
      generate(width=20, height=20, legend=[1, 3, 4, 7, 8], shapes=[
          (3, 0, 2, ["..#", "###", "#.."]),
          (8, 2, 12, ["#..", "###", "..#"]),
          (1, 8, 12, ["#..", "###", "#.."]),
          (7, 10, 5, ["#..", "###", "..#"]),
          (4, 16, 4, [".#.", ".#.", "###"]),
      ]),
      generate(width=20, height=20, legend=[6, 4, 1, 3], shapes=[
          (6, 2, 3, [".#.#", ".#.#", ".#.#", "####", ".#.."]),
          (4, 6, 14, ["#.#", "#.#", "#.#", "###", ".#."]),
          (1, 14, 1, ["...#.", "#####", "...#.", "####."]),
          (3, 14, 11, ["#.", "##", ".#", "##", "#."]),
      ]),
      generate(width=20, height=20, legend=[8, 1, 3, 4], shapes=[
          (1, 3, 4, ["##..", ".#..", ".#..", ".#..", "####"]),
          (4, 4, 13, ["##..", ".#..", ".#..", ".###", "##.."]),
          (3, 11, 5, ["#...#", "#####", "....#", "....#"]),
          (8, 15, 2, ["#...#", "#####", ".#...", ".#..."]),
      ]),
  ]
  test = [
      generate(width=21, height=25, legend=[1, 3, 4, 7, 8, 9, 6], shapes=[
          (1, 1, 1, ["#.....#", "#######", "#.....#"]),
          (6, 4, 9, ["..#.", "####", "#.#.", "#.#.", "#.##"]),
          (3, 4, 16, ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"]),
          (4, 6, 3, ["#..#", "#..#", "####", "...#", "####"]),
          (9, 15, 2, ["#.....#", "#######", "#.....#"]),
          (8, 18, 12, ["#####", "#.#..", "#.#..", "#.###"]),
          (7, 20, 3, ["####.", "...#.", "#####", "#..#."]),
      ]),
      generate(width=23, height=22, legend=[1, 3, 4, 6, 8, 7], shapes=[
          (6, 2, 8, ["#...#", "#####", "#...."]),
          (7, 6, 2, ["##.", ".#.", ".#.", ".##"]),
          (1, 8, 9, ["#..#", "####"]),
          (8, 8, 16, ["###", ".#.", ".#.", ".#.", "##."]),
          (4, 15, 4, ["#...#", "#####", "....#"]),
          (3, 16, 14, ["...#", "####", "#..."]),
      ]),
  ]
  return {"train": train, "test": test}
