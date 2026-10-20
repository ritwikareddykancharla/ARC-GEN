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

"""ARC-GEN style generator for task 4a21e3da.

Rule: the background is 1. The grid holds one 4-connected shape of colour 7
and one or two single 2-markers on the border. Each marker defines a line
perpendicular to its edge. A marker on the top or bottom edge defines a
column. A marker on the left or right edge defines a row. The line is drawn
in 2 from the marker to the farthest shape cell on it, and shape cells on the
line stay 7. With two lines, the cell where they cross is 2. All other shape
cells are grouped by the side of each line they lie on. Each group moves
rigidly so that its bounding box sits in the matching grid corner. With one
line, the other coordinate of the corner is the marker's own edge. With two
lines, the quadrant whose corner touches neither marker edge is deleted.

Scope: random scenes use grids of 12..26 per side by default. Explicit sizes
from 8..30 are accepted. The fixtures are 18 and 20, so the other sizes are
synthetic extensions. The shape is built constructively inside a 4..12
bounding box. It is made of required anchor cells joined by grid paths, then
grown at random. The anchors guarantee these properties:
  * the shape spans its full bounding box;
  * every side group that should exist is non-empty;
  * in two-line scenes, both lines reach the crossing cell;
  * the crossing cell itself is never a shape cell.
Three marker modes are sampled: vertical only, horizontal only, or both.
The marker edges are also random. Colours (bg 1, shape 7, marker 2) are fixed
by the task.
"""

import collections
import random

import common

BG, SHAPE, MARK = 1, 7, 2
_DIRS = ((0, 1), (1, 0), (0, -1), (-1, 0))


def _bfs_path(src, targets, bh, bw, forbidden):
  """Shortest 4-connected path from src to any target, avoiding forbidden."""
  prev = {src: None}
  dq = collections.deque([src])
  while dq:
    cur = dq.popleft()
    if cur in targets:
      path = []
      while cur is not None:
        path.append(cur)
        cur = prev[cur]
      return path
    dirs = list(_DIRS)
    random.shuffle(dirs)
    for dr, dc in dirs:
      n = (cur[0] + dr, cur[1] + dc)
      if (0 <= n[0] < bh and 0 <= n[1] < bw and n not in prev and
          n != forbidden):
        prev[n] = cur
        dq.append(n)
  raise ValueError("no path inside the box")  # Box minus one cell is connected.


def _build_shape(bh, bw, required, forbidden):
  """Connected shape containing all required cells and avoiding forbidden."""
  cells = {required[0]}
  for r in required[1:]:
    if r not in cells:
      cells.update(_bfs_path(r, cells, bh, bw, forbidden))
  area = bh * bw
  lo = max(bh + bw - 1, (2 * area) // 5)
  hi = max(lo, (3 * area) // 5)
  target = max(len(cells), random.randint(lo, hi))
  while len(cells) < target:
    cand = set()
    for (y, x) in cells:
      for dr, dc in _DIRS:
        n = (y + dr, x + dc)
        if (0 <= n[0] < bh and 0 <= n[1] < bw and n not in cells and
            n != forbidden):
          cand.add(n)
    if not cand:
      break
    cells.add(random.choice(sorted(cand)))
  return cells


def _groups(cells, vm, hm):
  """Split off-line shape cells into (vertical side, horizontal side) groups."""
  vline = vm[1] if vm else None
  hline = hm[1] if hm else None
  groups = {}
  for (y, x) in sorted(cells):
    if x == vline or y == hline:
      continue
    if vline is not None:
      hs = 'left' if x < vline else 'right'
    else:
      hs = hm[0]
    if hline is not None:
      vs = 'top' if y < hline else 'bottom'
    else:
      vs = vm[0]
    groups.setdefault((vs, hs), []).append((y, x))
  return groups


def _marker_cells(height, width, vm, hm):
  out = []
  if vm is not None:
    out.append((0 if vm[0] == 'top' else height - 1, vm[1]))
  if hm is not None:
    out.append((hm[1], 0 if hm[0] == 'left' else width - 1))
  return out


def _check_explicit(height, width, cells, vm, hm):
  """Rejects explicit scenes that the rule cannot interpret unambiguously."""
  if not (1 <= height <= 30 and 1 <= width <= 30):
    raise ValueError("grid size out of range")
  if not cells:
    raise ValueError("shape must be nonempty")
  reached = {min(cells)}
  todo = list(reached)
  while todo:
    y, x = todo.pop()
    for dy, dx in _DIRS:
      p = (y + dy, x + dx)
      if p in cells and p not in reached:
        reached.add(p)
        todo.append(p)
  if reached != cells:
    raise ValueError("shape must be 4-connected")
  for (y, x) in cells:
    if not (0 <= y < height and 0 <= x < width):
      raise ValueError("shape cell out of bounds")
  if vm is not None:
    if vm[0] not in ('top', 'bottom') or not 0 < vm[1] < width - 1:
      raise ValueError("bad vmarker")
    if not any(x == vm[1] for (_, x) in cells):
      raise ValueError("vertical line misses the shape")
  if hm is not None:
    if hm[0] not in ('left', 'right') or not 0 < hm[1] < height - 1:
      raise ValueError("bad hmarker")
    if not any(y == hm[1] for (y, _) in cells):
      raise ValueError("horizontal line misses the shape")
  for m in _marker_cells(height, width, vm, hm):
    if m in cells:
      raise ValueError("marker overlaps shape")
  if vm is not None and hm is not None and (hm[1], vm[1]) in cells:
    raise ValueError("crossing cell must not be a shape cell")
  if vm is not None and hm is not None:
    ys = [y for y, x in cells if x == vm[1]]
    xs = [x for y, x in cells if y == hm[1]]
    if ((vm[0] == 'top' and max(ys) < hm[1]) or
        (vm[0] == 'bottom' and min(ys) > hm[1]) or
        (hm[0] == 'left' and max(xs) < vm[1]) or
        (hm[0] == 'right' and min(xs) > vm[1])):
      raise ValueError("both marker lines must reach the crossing")


def _render(height, width, cells, vm, hm):
  inp = common.grid(width, height, BG)
  out = common.grid(width, height, BG)
  for (y, x) in cells:
    inp[y][x] = SHAPE
  for (y, x) in _marker_cells(height, width, vm, hm):
    inp[y][x] = MARK
    out[y][x] = MARK
  if vm is not None:
    v = vm[1]
    ys = [y for (y, x) in cells if x == v]
    rows = range(0, max(ys) + 1) if vm[0] == 'top' else range(min(ys), height)
    for y in rows:
      out[y][v] = SHAPE if (y, v) in cells else MARK
  if hm is not None:
    h = hm[1]
    xs = [x for (y, x) in cells if y == h]
    cols = range(0, max(xs) + 1) if hm[0] == 'left' else range(min(xs), width)
    for x in cols:
      out[h][x] = SHAPE if (h, x) in cells else MARK
  if vm is not None and hm is not None:
    out[hm[1]][vm[1]] = MARK
  for (vs, hs), group in _groups(cells, vm, hm).items():
    if vm is not None and hm is not None:
      if vs != vm[0] and hs != hm[0]:
        continue  # quadrant touching no marker edge vanishes
    y0 = min(y for y, _ in group)
    y1 = max(y for y, _ in group)
    x0 = min(x for _, x in group)
    x1 = max(x for _, x in group)
    dy = -y0 if vs == 'top' else height - 1 - y1
    dx = -x0 if hs == 'left' else width - 1 - x1
    for (y, x) in group:
      out[y + dy][x + dx] = SHAPE
  return {"input": inp, "output": out}


def _mode_of(vm, hm):
  if vm is not None and hm is not None:
    return 'both'
  return 'v' if vm is not None else 'h'


def generate(height=None, width=None, shape=None, top=None, left=None,
             vmarker=None, hmarker=None, mode=None):
  """Returns an input/output pair.

  Args:
    height: grid height (rows). Random scenes accept 8..30.
    width: grid width (columns). Random scenes accept 8..30.
    shape: list of strings ('#' = shape cell, '.' = empty) giving the 7-shape
      inside its bounding box. If None, a fresh random scene is built.
    top: row of the shape bounding box's top edge. Used only with shape.
    left: column of the shape bounding box's left edge. Used only with shape.
    vmarker: ('top'|'bottom', column) for a marker on a horizontal edge.
      Used only with shape.
    hmarker: ('left'|'right', row) for a marker on a vertical edge.
      Used only with shape.
    mode: 'v', 'h' or 'both', the set of marker lines. It is random if None.
      With an explicit shape, it must agree with the markers given.
  """
  if mode not in (None, 'v', 'h', 'both'):
    raise ValueError("mode must be 'v', 'h' or 'both'")
  if shape is not None:
    if None in (height, width, top, left):
      raise ValueError("explicit shape needs height, width, top and left")
    if vmarker is None and hmarker is None:
      raise ValueError("explicit shape needs at least one marker")
    if mode is not None and mode != _mode_of(vmarker, hmarker):
      raise ValueError("mode disagrees with supplied markers")
    if not shape or not shape[0] or any(len(row) != len(shape[0]) for row in shape):
      raise ValueError("shape must be rectangular")
    if any(ch not in '.#' for row in shape for ch in row):
      raise ValueError("shape uses only . and #")
    cells = set()
    for r, row in enumerate(shape):
      for c, ch in enumerate(row):
        if ch == '#':
          cells.add((top + r, left + c))
    _check_explicit(height, width, cells, vmarker, hmarker)
    return _render(height, width, cells, vmarker, hmarker)
  if (top is not None or left is not None or vmarker is not None or
      hmarker is not None):
    raise ValueError("top/left/vmarker/hmarker require an explicit shape")
  for d in (height, width):
    if d is not None and not 8 <= d <= 30:
      raise ValueError("random scenes need 8..30 per side")
  h = height if height is not None else random.randint(12, 26)
  w = width if width is not None else random.randint(12, 26)
  m = mode if mode is not None else random.choice(
      ['v', 'v', 'h', 'h', 'both', 'both', 'both'])
  bh = random.randint(4, min(12, h - 4))
  bw = random.randint(4, min(12, w - 4))
  t = random.randint(2, h - 2 - bh)
  l = random.randint(2, w - 2 - bw)
  cv = random.randint(1, bw - 2)  # local line column
  ch = random.randint(1, bh - 2)  # local line row
  required = [(0, random.randrange(bw)), (bh - 1, random.randrange(bw)),
              (random.randrange(bh), 0), (random.randrange(bh), bw - 1)]
  forbidden = None
  vm = hm = None
  if m == 'v':
    required.append((random.randrange(bh), cv))
    vm = (random.choice(['top', 'bottom']), l + cv)
  elif m == 'h':
    required.append((ch, random.randrange(bw)))
    hm = (random.choice(['left', 'right']), t + ch)
  else:
    vedge = random.choice(['top', 'bottom'])
    hedge = random.choice(['left', 'right'])
    forbidden = (ch, cv)
    for rr in ((0, ch - 1), (ch + 1, bh - 1)):
      for cc in ((0, cv - 1), (cv + 1, bw - 1)):
        required.append((random.randint(*rr), random.randint(*cc)))
    if vedge == 'top':
      required.append((random.randint(ch + 1, bh - 1), cv))
    else:
      required.append((random.randint(0, ch - 1), cv))
    if hedge == 'right':
      required.append((ch, random.randint(0, cv - 1)))
    else:
      required.append((ch, random.randint(cv + 1, bw - 1)))
    vm = (vedge, l + cv)
    hm = (hedge, t + ch)
  random.shuffle(required)
  blob = _build_shape(bh, bw, required, forbidden)
  cells = {(t + r, l + c) for (r, c) in blob}
  return _render(h, w, cells, vm, hm)


def validate():
  """Reconstructs the canonical ARC pairs from explicit latent parameters."""
  train = [
      generate(height=18, width=18, top=4, left=4,
               vmarker=('top', 8), hmarker=('right', 8),
               shape=["##........",
                      "##........",
                      ".#...#....",
                      ".#.#####..",
                      ".#...##...",
                      "#######...",
                      "##...#####",
                      ".......##."]),
      generate(height=18, width=18, top=4, left=5,
               vmarker=('top', 9),
               shape=["...##...",
                      "..#####.",
                      "..#...##",
                      "####..##",
                      "..#..##.",
                      "..####..",
                      "###.####"]),
      generate(height=18, width=18, top=7, left=5,
               vmarker=('bottom', 9),
               shape=["..##...#",
                      ".###...#",
                      "##...#.#",
                      "########",
                      ".##.##.#"]),
  ]
  test = [
      generate(height=20, width=20, top=6, left=4,
               vmarker=('bottom', 8),
               shape=["....######",
                      "##...#....",
                      ".##..#....",
                      "..####..##",
                      "..##.####.",
                      "..#....#..",
                      "###....###"]),
  ]
  return {"train": train, "test": test}
