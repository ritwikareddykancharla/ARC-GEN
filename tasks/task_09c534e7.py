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

"""ARC task 09c534e7: fill block interiors with the structure's seed colour.

Rule: the background is 0. Blue (1) structures are made of solid rectangles
(blocks, at least 3x3) joined by 1-cell-wide straight corridors. Each
connected structure holds exactly one odd-coloured seed cell inside the
interior of one of its blocks. In the output, the interior (block minus its
1-cell border) of every block in a structure is painted with that
structure's seed colour. Corridors and block borders stay blue.

Scope: random scenes have a random grid size (14..30 per side), 2-4
structures, each a connected graph of 2-9 blocks (up to four on smaller grids) grown by attaching corridors (length
1-6) to non-corner border cells of existing blocks. Blocks range from 3x3 up
to 8x12. Structures and their parts keep a one-cell clearance from every
unrelated cell, so the latent block interiors are exactly the cells whose
eight neighbours are all filled. The background stays clearly the majority
colour (filled cells are at most 48% of the grid), as in the task, so the
background and the shape colour are unambiguous. Seed colours are distinct
per grid and drawn from 2..9; the shape colour 1 and background 0 are fixed
as in the task.
"""

import random

import common


_MAX_FILL_PERCENT = 48


def _rect_cells(rect):
  r0, c0, r1, c1 = rect
  return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]


def _render(width, height, structures):
  """Draws input and output grids from latent structures."""
  inp = common.grid(width, height, 0)
  out = common.grid(width, height, 0)
  for st in structures:
    for rect in list(st["boxes"]) + list(st["corridors"]):
      for r, c in _rect_cells(rect):
        inp[r][c] = 1
        out[r][c] = 1
  for st in structures:
    color = st["color"]
    for r0, c0, r1, c1 in st["boxes"]:
      for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
          out[r][c] = color
    sr, sc = st["seed"]
    inp[sr][sc] = color
  return inp, out


def _box_size():
  if random.random() < 0.12:
    return random.randint(5, 8), random.randint(6, 12)
  sizes = [3, 3, 3, 4, 4, 4, 5, 5, 6]
  return random.choice(sizes), random.choice(sizes)


def _in_bounds(rect, width, height):
  r0, c0, r1, c1 = rect
  return 0 <= r0 <= r1 < height and 0 <= c0 <= c1 < width


def _clear(owner, width, height, cells, first, parent_cells):
  """Checks new cells are empty and touch nothing except allowed parent."""
  cellset = set(cells)
  for r, c in cells:
    if owner[r][c] != -1:
      return False
  for r, c in cells:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        nr, nc = r + dr, c + dc
        if (dr == 0 and dc == 0) or (nr, nc) in cellset:
          continue
        if not (0 <= nr < height and 0 <= nc < width):
          continue
        if owner[nr][nc] == -1:
          continue
        if first is not None and (r, c) == first and (nr, nc) in parent_cells:
          continue
        return False
  return True


def _try_attach(owner, width, height, parent):
  """Proposes a corridor and a new box attached to parent."""
  r0, c0, r1, c1 = parent
  h, w = _box_size()
  length = random.randint(1, 6)
  d = random.randrange(4)
  if d < 2:
    cr = random.randint(r0 + 1, r1 - 1)
    nr0 = random.randint(cr - h + 2, cr - 1)
    nr1 = nr0 + h - 1
    if d == 0:
      corr = (cr, c1 + 1, cr, c1 + length)
      first = (cr, c1 + 1)
      nc0 = c1 + length + 1
      nc1 = nc0 + w - 1
    else:
      corr = (cr, c0 - length, cr, c0 - 1)
      first = (cr, c0 - 1)
      nc1 = c0 - length - 1
      nc0 = nc1 - w + 1
  else:
    cc = random.randint(c0 + 1, c1 - 1)
    nc0 = random.randint(cc - w + 2, cc - 1)
    nc1 = nc0 + w - 1
    if d == 2:
      corr = (r1 + 1, cc, r1 + length, cc)
      first = (r1 + 1, cc)
      nr0 = r1 + length + 1
      nr1 = nr0 + h - 1
    else:
      corr = (r0 - length, cc, r0 - 1, cc)
      first = (r0 - 1, cc)
      nr1 = r0 - length - 1
      nr0 = nr1 - h + 1
  box = (nr0, nc0, nr1, nc1)
  if not _in_bounds(box, width, height) or not _in_bounds(corr, width, height):
    return None
  cells = _rect_cells(corr) + _rect_cells(box)
  if not _clear(owner, width, height, cells, first, set(_rect_cells(parent))):
    return None
  return box, corr


def _grow(owner, width, height, sid):
  """Grows one tree-shaped structure; marks owner on success."""
  start = None
  for _ in range(60):
    h, w = _box_size()
    if h > height or w > width:
      continue
    r0 = random.randint(0, height - h)
    c0 = random.randint(0, width - w)
    rect = (r0, c0, r0 + h - 1, c0 + w - 1)
    if _clear(owner, width, height, _rect_cells(rect), None, set()):
      start = rect
      break
  if start is None:
    return None
  boxes = [start]
  corridors = []
  placed = list(_rect_cells(start))
  for r, c in placed:
    owner[r][c] = sid
  target = random.randint(2, 9 if width * height >= 600 else 4)
  for _ in range(120):
    if len(boxes) >= target:
      break
    res = _try_attach(owner, width, height, random.choice(boxes))
    if res is None:
      continue
    box, corr = res
    boxes.append(box)
    corridors.append(corr)
    for r, c in _rect_cells(corr) + _rect_cells(box):
      owner[r][c] = sid
      placed.append((r, c))
  if len(boxes) < 2:
    for r, c in placed:
      owner[r][c] = -1
    return None
  return {"boxes": boxes, "corridors": corridors}


def _filled_count(owner):
  return sum(1 for row in owner for v in row if v != -1)


def _close_cycles(owner, width, height, structures):
  """Add clear straight corridors between already-connected blocks.

  Tree growth alone misses cycles. Extra corridors preserve block interiors,
  never join different seeded structures, and obey the same clearance rule.
  """
  added = 0
  for sid, st in enumerate(structures):
    proposals = []
    for a in st['boxes']:
      for b in st['boxes']:
        # Only left-to-right and top-to-bottom, avoiding duplicate proposals.
        if 1 <= b[1] - a[3] - 1 <= 6:
          for row in range(max(a[0], b[0]) + 1, min(a[2], b[2])):
            proposals.append(((row, a[3] + 1, row, b[1] - 1), a, b))
        if 1 <= b[0] - a[2] - 1 <= 6:
          for col in range(max(a[1], b[1]) + 1, min(a[3], b[3])):
            proposals.append(((a[2] + 1, col, b[0] - 1, col), a, b))
    random.shuffle(proposals)
    for corridor, a, b in proposals:
      if random.random() > 0.5:
        continue
      cells = _rect_cells(corridor)
      if _filled_count(owner) + len(cells) > _MAX_FILL_PERCENT * width * height // 100:
        continue
      first, last = cells[0], cells[-1]
      allowed_a, allowed_b = set(_rect_cells(a)), set(_rect_cells(b))
      valid = True
      for r, c in cells:
        if owner[r][c] != -1:
          valid = False
          break
        for dr in (-1, 0, 1):
          for dc in (-1, 0, 1):
            point = nr, nc = r + dr, c + dc
            if not (0 <= nr < height and 0 <= nc < width) or owner[nr][nc] == -1:
              continue
            if (r, c) == first and point in allowed_a:
              continue
            if (r, c) == last and point in allowed_b:
              continue
            valid = False
      if valid:
        st['corridors'].append(corridor)
        for r, c in cells:
          owner[r][c] = sid
        added += 1
  return added


def _random_structures(width, height, num_structures):
  """Samples structures keeping the background a clear majority."""
  for _ in range(80):
    owner = [[-1] * width for _ in range(height)]
    result = []
    count = num_structures if num_structures is not None else random.randint(2, 4 if width * height >= 400 else 3)
    for sid in range(count):
      st = _grow(owner, width, height, sid)
      if st is None:
        break
      result.append(st)
    if len(result) != count:
      continue
    if _filled_count(owner) * 100 > _MAX_FILL_PERCENT * width * height:
      continue
    _close_cycles(owner, width, height, result)
    return result
  return None


def generate(width=None, height=None, structures=None, num_structures=None,
             colors=None):
  """Generates an input/output pair.

  Args:
    width: grid width (columns); sampled in 14..30 if None.
    height: grid height (rows); sampled in 14..30 if None.
    structures: optional explicit latent scene, a list of dicts with keys
      "boxes" (list of (r0, c0, r1, c1) blocks, each >= 3x3), "corridors"
      (list of 1-wide (r0, c0, r1, c1) rectangles), "seed" ((row, col) inside
      a block interior) and "color" (seed colour). If given, width and height
      must be given too, and nothing is sampled.
    num_structures: number of random structures (2..4) when sampling.
    colors: optional list of distinct seed colours for random structures.
  """
  if structures is not None:
    inp, out = _render(width, height, structures)
    return {"input": inp, "output": out}
  if width is None:
    width = random.randint(14, 30)
  if height is None:
    height = random.randint(14, 30)
  if not (14 <= width <= 30 and 14 <= height <= 30):
    raise ValueError('random canvas dimensions must be 14..30')
  if num_structures is not None and num_structures not in range(2, 5):
    raise ValueError('num_structures must be 2..4')
  if colors is not None:
    if len(colors) not in range(2, 5) or len(set(colors)) != len(colors) or any(c not in range(2,10) for c in colors):
      raise ValueError('colors must contain 2..4 distinct seed colours in 2..9')
    if num_structures is not None and num_structures != len(colors):
      raise ValueError('colors length must equal num_structures')
    num_structures = len(colors)
  shapes = _random_structures(width, height, num_structures)
  if shapes is None:
    raise RuntimeError('cannot place requested structures on requested canvas')
  if colors is None:
    colors = random.sample(list(range(2, 10)), len(shapes))
  scene = []
  for st, color in zip(shapes, colors):
    r0, c0, r1, c1 = random.choice(st["boxes"])
    seed = (random.randint(r0 + 1, r1 - 1), random.randint(c0 + 1, c1 - 1))
    scene.append({"boxes": st["boxes"], "corridors": st["corridors"],
                  "seed": seed, "color": color})
  inp, out = _render(width, height, scene)
  return {"input": inp, "output": out}


def _s(color, seed, boxes, corridors):
  return {"color": color, "seed": seed, "boxes": boxes,
          "corridors": corridors}


def validate():
  """Reconstructs the canonical fixtures from explicit latent scenes."""
  train = [
      generate(width=20, height=20, structures=[
          _s(3, (2, 3), [(1, 2, 3, 5), (5, 2, 8, 7), (6, 9, 8, 11)],
             [(4, 4, 4, 4), (7, 8, 7, 8)]),
          _s(4, (2, 16), [(1, 14, 4, 17), (6, 15, 8, 17)],
             [(5, 16, 5, 16)]),
          _s(2, (13, 7), [(12, 5, 15, 8), (12, 11, 14, 13), (14, 0, 17, 2),
                          (17, 6, 19, 8)],
             [(13, 9, 13, 10), (15, 3, 15, 4), (16, 7, 16, 7)]),
      ]),
      generate(width=30, height=30, structures=[
          _s(2, (4, 14), [(1, 22, 5, 25), (2, 12, 6, 16), (3, 5, 5, 7),
                          (7, 5, 9, 7), (11, 10, 15, 18), (11, 21, 14, 24),
                          (11, 27, 13, 29), (12, 5, 14, 7), (19, 14, 22, 17)],
             [(4, 8, 4, 11), (4, 17, 4, 21), (6, 6, 6, 6), (7, 14, 10, 14),
              (12, 19, 12, 20), (12, 25, 12, 26), (13, 8, 13, 9),
              (16, 15, 18, 15)]),
          _s(3, (28, 17), [(17, 8, 19, 10), (22, 7, 27, 11), (18, 2, 20, 4),
                           (23, 2, 25, 4), (25, 14, 29, 19),
                           (26, 23, 29, 25), (20, 23, 22, 25),
                           (20, 19, 22, 21)],
             [(20, 9, 21, 9), (21, 3, 22, 3), (24, 5, 24, 6),
              (26, 12, 26, 13), (27, 20, 27, 22), (23, 24, 25, 24),
              (21, 22, 21, 22)]),
      ]),
      generate(width=18, height=18, structures=[
          _s(4, (2, 4), [(1, 3, 3, 6), (1, 9, 4, 12), (2, 15, 4, 17),
                         (6, 3, 8, 6)],
             [(2, 7, 2, 8), (3, 13, 3, 14), (4, 5, 5, 5)]),
          _s(3, (7, 10), [(6, 9, 8, 11), (6, 13, 8, 15)], [(7, 12, 7, 12)]),
          _s(6, (15, 4), [(13, 2, 16, 5), (12, 8, 17, 11), (14, 13, 16, 15),
                          (10, 13, 12, 15)],
             [(15, 6, 15, 7), (15, 12, 15, 12), (13, 14, 13, 14)]),
      ]),
  ]
  test = [
      generate(width=30, height=30, structures=[
          _s(4, (2, 10), [(2, 2, 5, 5), (1, 8, 6, 12), (2, 15, 5, 20),
                          (1, 23, 6, 28), (7, 16, 9, 19), (8, 24, 11, 27),
                          (8, 9, 11, 11), (8, 4, 10, 7), (12, 4, 14, 6)],
             [(3, 6, 3, 7), (3, 13, 3, 14), (3, 21, 3, 22), (6, 18, 6, 18),
              (7, 26, 7, 26), (7, 10, 7, 10), (9, 8, 9, 8),
              (11, 5, 11, 5)]),
          _s(8, (14, 16), [(13, 15, 17, 19), (14, 21, 16, 24),
                           (19, 9, 25, 20), (15, 9, 17, 11), (20, 5, 23, 7),
                           (20, 1, 22, 3)],
             [(15, 20, 15, 20), (18, 16, 18, 16), (18, 10, 18, 10),
              (22, 8, 22, 8), (21, 4, 21, 4)]),
          _s(6, (21, 27), [(20, 25, 24, 28), (26, 25, 29, 28),
                           (27, 15, 29, 18), (27, 8, 29, 11),
                           (26, 2, 29, 5)],
             [(25, 27, 25, 27), (28, 19, 28, 24), (28, 12, 28, 14),
              (28, 6, 28, 7)]),
      ]),
  ]
  return {"train": train, "test": test}
