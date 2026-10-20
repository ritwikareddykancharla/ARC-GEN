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

"""ARC-GEN style generator for task 8698868d.

Rule: the input holds a rectangular block of R x C solid square panels, each
of side S and each a distinct colour, packed edge to edge on a background.
Every panel contains k isolated background-coloured "holes", and the values of
k differ from panel to panel. Elsewhere there are R*C loose square shapes of
side S-2. Each shape has a solid border, and its interior has background holes
forming some number of 4-connected components. For every panel there is
exactly one shape whose number of hole components equals the panel's hole
count. The output is the panel block cropped out of the input. Panel holes
are filled with the panel colour, and each shape is stamped centred, with a
1-cell margin, inside the panel whose count matches. The shape's holes show
the panel colour.

Scope: the panel side S ranges over 5..9, block layouts over R x C with
2..6 panels, and the background, colours, grid size (up to 30x30), block
position and shape positions are all random. Hole counts are distinct values
in 0..6, and solid (0-hole) shapes are supported. Shape hole components are
random 4-connected blobs, which may touch each other diagonally, as in the
task.
"""

import random

import common


_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _comp_count(cells):
  """Number of 4-connected components of a set of (r, c) cells."""
  cells = set(cells)
  seen = set()
  n = 0
  for cell in cells:
    if cell in seen:
      continue
    n += 1
    seen.add(cell)
    stack = [cell]
    while stack:
      r, c = stack.pop()
      for dr, dc in _DIRS4:
        nb = (r + dr, c + dc)
        if nb in cells and nb not in seen:
          seen.add(nb)
          stack.append(nb)
  return n


def _solid_connected(q, holes):
  solid = [(r, c) for r in range(q) for c in range(q) if (r, c) not in holes]
  return _comp_count(solid) == 1


def _box(r0, c0, r1, c1):
  return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]


def _make_shape_holes(q, k):
  """Random interior holes of a q x q shape with exactly k components."""
  if k == 0:
    return []
  interior = _box(1, 1, q - 2, q - 2)
  m = q - 2
  for _ in range(100):
    cells = interior[:]
    random.shuffle(cells)
    chosen = []
    for cell in cells:
      if len(chosen) == k:
        break
      if all((cell[0] + dr, cell[1] + dc) not in chosen for dr, dc in _DIRS4):
        chosen.append(cell)
    if len(chosen) < k:
      continue
    owner = {cell: i for i, cell in enumerate(chosen)}
    holes = set(chosen)
    if not _solid_connected(q, holes):
      continue
    target = random.randint(0, (m * m) // 2)
    grown = 0
    for _ in range(target * 4):
      if grown >= target:
        break
      i = random.randrange(k)
      members = [cell for cell, o in owner.items() if o == i]
      r, c = random.choice(members)
      dr, dc = random.choice(_DIRS4)
      nb = (r + dr, c + dc)
      if not (1 <= nb[0] <= q - 2 and 1 <= nb[1] <= q - 2) or nb in holes:
        continue
      ok = True
      for er, ec in _DIRS4:
        nn = (nb[0] + er, nb[1] + ec)
        if nn in owner and owner[nn] != i:
          ok = False
          break
      if not ok:
        continue
      holes.add(nb)
      if not _solid_connected(q, holes):
        holes.discard(nb)
        continue
      owner[nb] = i
      grown += 1
    if _comp_count(holes) == k and _solid_connected(q, holes):
      return sorted(holes)
  return None


def _make_panel_holes(s, k):
  """k single-cell holes inside an s x s panel, never 4-adjacent."""
  if k == 0:
    return []
  interior = _box(1, 1, s - 2, s - 2)
  for _ in range(100):
    cells = interior[:]
    random.shuffle(cells)
    chosen = []
    for cell in cells:
      if len(chosen) == k:
        break
      if all(abs(cell[0] - o[0]) + abs(cell[1] - o[1]) > 1 for o in chosen):
        chosen.append(cell)
    if len(chosen) == k:
      return sorted(chosen)
  return None


def _random_scene(width, height, bg, size, rows, cols):
  for _ in range(500):
    b = random.randint(0, 9) if bg is None else bg
    s = random.randint(5, 9) if size is None else size
    q = s - 2
    m = s - 4
    shape_cap = {1: 1, 2: 2, 3: 5}.get(m, 6)
    panel_cap = ((s - 1) // 2) ** 2
    cap = min(6, shape_cap, panel_cap)
    max_n = min(6, cap + 1)
    options = []
    for rr in range(1, 7):
      for cc in range(1, 7):
        if rows is not None and rr != rows:
          continue
        if cols is not None and cc != cols:
          continue
        if 2 <= rr * cc <= max_n and rr * s <= 24 and cc * s <= 24:
          options.append((rr, cc))
    if not options:
      continue
    nr, nc = random.choice(options)
    n = nr * nc
    bh, bw = nr * s, nc * s
    h = random.randint(bh, 30) if height is None else height
    w = random.randint(bw, 30) if width is None else width
    if h < bh or w < bw:
      continue
    if (bh + 1) * (bw + 1) + n * (q + 1) ** 2 > 0.75 * h * w:
      continue
    r0 = random.randint(0, h - bh)
    c0 = random.randint(0, w - bw)
    rects = [(r0, c0, bh, bw)]
    positions = []
    for _ in range(n):
      placed = None
      for _ in range(200):
        r = random.randint(0, h - q)
        c = random.randint(0, w - q)
        clash = False
        for (rr, cc, hh, ww) in rects:
          if r < rr + hh + 1 and rr < r + q + 1 and c < cc + ww + 1 and cc < c + q + 1:
            clash = True
            break
        if not clash:
          placed = (r, c)
          break
      if placed is None:
        break
      rects.append((placed[0], placed[1], q, q))
      positions.append(placed)
    if len(positions) < n:
      continue
    counts = random.sample(range(cap + 1), n)
    panel_holes = [_make_panel_holes(s, k) for k in counts]
    if any(p is None for p in panel_holes):
      continue
    shape_holes = [_make_shape_holes(q, k) for k in counts]
    if any(p is None for p in shape_holes):
      continue
    nonbg = [x for x in range(10) if x != b]
    panel_colors = random.sample(nonbg, n)
    shape_colors = None
    for _ in range(100):
      sc = random.sample(nonbg, n)
      if all(sc[i] != panel_colors[i] for i in range(n)):
        shape_colors = sc
        break
    if shape_colors is None:
      continue
    order = list(range(n))
    random.shuffle(order)
    shapes = []
    for j, t in enumerate(order):
      shapes.append((shape_colors[t], positions[j][0], positions[j][1],
                     shape_holes[t], t))
    return dict(width=w, height=h, bg=b, origin=(r0, c0), rows=nr, cols=nc,
                size=s, panel_colors=panel_colors, panel_holes=panel_holes,
                shapes=shapes)
  raise RuntimeError("could not construct a scene")


def generate(width=None, height=None, bg=None, origin=None, rows=None,
             cols=None, size=None, panel_colors=None, panel_holes=None,
             shapes=None):
  """Generate one input/output pair.

  Args:
    width: grid width (columns).
    height: grid height (rows).
    bg: background colour.
    origin: (row, col) of the top-left cell of the panel block.
    rows: number of panel rows in the block.
    cols: number of panel columns in the block.
    size: panel side S. Loose shapes have side S-2.
    panel_colors: row-major list of panel colours.
    panel_holes: row-major list of hole-cell lists, relative to each panel.
    shapes: list of (colour, row, col, hole cells relative to the shape,
      target panel index).
  If shapes is None, a fresh random scene is built. Any of width, height, bg,
  size, rows and cols that are given are used as overrides.
  """
  if shapes is None:
    if origin is not None or panel_colors is not None or panel_holes is not None:
      raise ValueError("explicit panel parameters require explicit shapes")
    p = _random_scene(width, height, bg, size, rows, cols)
    width, height, bg = p["width"], p["height"], p["bg"]
    origin, rows, cols, size = p["origin"], p["rows"], p["cols"], p["size"]
    panel_colors, panel_holes = p["panel_colors"], p["panel_holes"]
    shapes = p["shapes"]
  s = size
  q = s - 2
  n = rows * cols
  # Consistency of the latent matching: hole counts must form a bijection.
  pcounts = [_comp_count(h) for h in panel_holes]
  if len(set(pcounts)) != n or len(shapes) != n:
    raise ValueError("panel hole counts must be distinct")
  if sorted(t for (_, _, _, _, t) in shapes) != list(range(n)):
    raise ValueError("shape targets must be a permutation")
  for (_, _, _, holes, t) in shapes:
    if _comp_count(holes) != pcounts[t]:
      raise ValueError("shape hole count does not match its panel")

  grid = common.grid(width, height, bg)
  r0, c0 = origin
  for i in range(n):
    pr, pc = r0 + (i // cols) * s, c0 + (i % cols) * s
    for r in range(s):
      for c in range(s):
        grid[pr + r][pc + c] = panel_colors[i]
    for (r, c) in panel_holes[i]:
      grid[pr + r][pc + c] = bg
  for (color, sr, sc, holes, _) in shapes:
    hs = set(map(tuple, holes))
    for r in range(q):
      for c in range(q):
        grid[sr + r][sc + c] = bg if (r, c) in hs else color

  output = common.grid(cols * s, rows * s, 0)
  for i in range(n):
    pr, pc = (i // cols) * s, (i % cols) * s
    for r in range(s):
      for c in range(s):
        output[pr + r][pc + c] = panel_colors[i]
  for (color, _, _, holes, t) in shapes:
    hs = set(map(tuple, holes))
    pr, pc = (t // cols) * s + 1, (t % cols) * s + 1
    for r in range(q):
      for c in range(q):
        output[pr + r][pc + c] = panel_colors[t] if (r, c) in hs else color
  return {"input": grid, "output": output}


def validate():
  """Reconstruct the canonical examples from explicit latent parameters."""
  train = [
      generate(width=15, height=20, bg=8, origin=(0, 0), rows=1, cols=2,
               size=6, panel_colors=[1, 4],
               panel_holes=[[(4, 4)], [(1, 1), (4, 4)]],
               shapes=[(2, 9, 2, _box(1, 1, 2, 2), 0),
                       (3, 13, 7, [(1, 2), (2, 1)], 1)]),
      generate(width=30, height=30, bg=2, origin=(0, 0), rows=2, cols=2,
               size=8, panel_colors=[4, 3, 8, 1],
               panel_holes=[[(2, 2), (2, 5), (5, 2)],
                            [(2, 5), (5, 2)],
                            [(2, 5)],
                            [(2, 2), (2, 5), (5, 2), (5, 5)]],
               shapes=[(9, 2, 19, [(1, 1), (1, 2), (1, 4), (2, 1), (2, 2),
                                   (2, 4), (3, 4), (4, 1), (4, 2), (4, 4)], 0),
                       (5, 16, 19, [(1, 1), (1, 2), (1, 4), (2, 1), (2, 2),
                                    (2, 4), (4, 1), (4, 2), (4, 4)], 3),
                       (1, 20, 3, _box(1, 1, 4, 4), 2),
                       (7, 23, 13, [(1, 1), (3, 1), (4, 1)], 1)]),
  ]
  test = [
      generate(width=30, height=30, bg=4, origin=(16, 0), rows=2, cols=3,
               size=7, panel_colors=[9, 2, 7, 3, 8, 1],
               panel_holes=[[(2, 2), (2, 4), (4, 4)],
                            [],
                            [(2, 2), (2, 4), (3, 3), (4, 2), (4, 4)],
                            [(2, 2)],
                            [(2, 2), (2, 4), (4, 2), (4, 4)],
                            [(2, 2), (4, 4)]],
               shapes=[(9, 1, 3, [(1, 1), (1, 3), (2, 2), (3, 1), (3, 3)], 2),
                       (1, 1, 18, _box(1, 1, 3, 3), 3),
                       (6, 8, 1, [], 1),
                       (0, 8, 10, [(1, 1), (2, 2), (3, 3)], 0),
                       (3, 9, 24, [(1, 1), (1, 3), (2, 1), (2, 3), (3, 1),
                                   (3, 3)], 5),
                       (5, 21, 25, [(1, 1), (1, 3), (3, 1), (3, 3)], 4)]),
  ]
  return {"train": train, "test": test}
