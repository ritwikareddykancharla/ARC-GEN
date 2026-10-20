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

"""ARC-GEN style generator for task 1acc24af.

Rule: a blue (1) wall runs from the left edge to the right edge. Its lowest
row is a baseline. Recesses are notches cut upward into the wall from that
baseline. Each recess is a skyline: a run of adjacent columns, each with a
height of 1-3 cells. The wall is made of the baseline row outside the
recesses plus every 8-neighbour of a recess cell that lies at or above the
baseline. Gray (5) polyominoes sit below the wall. A gray piece turns red (2)
if some 90-degree rotation of it (reflections are not allowed) can be placed
so that it covers every cell of one recess. The placement must stay inside
the grid and must not overlap any blue cell. Extra piece cells can spill out
below through the recess opening. All other pieces stay gray. Nothing moves.

Scope: grid sides vary from 12 to 30; original fixtures retain 12x12.
There are 1-4 recesses with sampled skyline shapes, and the baseline row is
sampled. Each recess gets at least one piece that is built to fit it: the
recess shape grown by a few extra cells through the opening, then rotated.
Non-fitting distractors are added too. Some are mirror images of fitting
pieces, so chirality matters; others are random polyominoes that fit no
recess. All pieces are bottom-aligned on row H-2 and separated by empty
columns.
"""

import random

import common

BLUE, GRAY, RED = 1, 5, 2


def _norm(cells):
  r0 = min(r for r, c in cells)
  c0 = min(c for r, c in cells)
  return sorted((r - r0, c - c0) for r, c in cells)


def _rot(cells):
  return _norm([(c, -r) for r, c in cells])


def _mirror(cells):
  return _norm([(r, -c) for r, c in cells])


def _dims(cells):
  return max(r for r, c in cells) + 1, max(c for r, c in cells) + 1


def _holes(baseline, recesses):
  """Returns one cell set per recess. Each recess is (left_col, heights)."""
  out = []
  for left, heights in recesses:
    cells = set()
    for i, h in enumerate(heights):
      for k in range(h):
        cells.add((baseline - k, left + i))
    out.append(cells)
  return out


def _wall(width, height, baseline, holes):
  allh = set()
  for h in holes:
    allh |= h
  wall = set()
  for c in range(width):
    if (baseline, c) not in allh:
      wall.add((baseline, c))
  for r, c in allh:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        rr, cc = r + dr, c + dc
        if (rr <= baseline and 0 <= rr < height and 0 <= cc < width
            and (rr, cc) not in allh):
          wall.add((rr, cc))
  return wall


def _fits_hole(shape, hole, wall, width, height):
  hy, hx = min(hole)
  cur = _norm(shape)
  for _ in range(4):
    for py, px in cur:
      dy, dx = hy - py, hx - px
      placed = {(y + dy, x + dx) for y, x in cur}
      if hole <= placed and all(0 <= y < height and 0 <= x < width
                                and (y, x) not in wall for y, x in placed):
        return True
    cur = _rot(cur)
  return False


def _fits_any(shape, holes, wall, width, height):
  return any(_fits_hole(shape, h, wall, width, height) for h in holes)


def _random_poly(size, maxh, maxw):
  for _ in range(100):
    cells = {(0, 0)}
    while len(cells) < size:
      frontier = {(r + dr, c + dc) for r, c in cells
                  for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))} - cells
      cells.add(random.choice(sorted(frontier)))
    shape = _norm(cells)
    h, w = _dims(shape)
    if h <= maxh and w <= maxw:
      return shape
  return None


def _grow_fitting(hole, wall, width, height, maxh, maxw):
  for _ in range(60):
    lo = max(0, 3 - len(hole))
    hi = min(3, 8 - len(hole))
    if lo > hi:
      return None
    extra = random.randint(lo, hi)
    cells = set(hole)
    ok = True
    for _ in range(extra):
      cand = set()
      for r, c in cells:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
          q = (r + dr, c + dc)
          if (0 <= q[0] < height and 0 <= q[1] < width and q not in wall
              and q not in cells):
            cand.add(q)
      if not cand:
        ok = False
        break
      cells.add(random.choice(sorted(cand)))
    if not ok:
      continue
    shape = _norm(cells)
    for _ in range(random.randint(0, 3)):
      shape = _rot(shape)
    h, w = _dims(shape)
    if h <= maxh and w <= maxw:
      return shape
  return None


def _split(total, parts):
  cuts = sorted(random.randint(0, total) for _ in range(parts - 1))
  bounds = [0] + cuts + [total]
  return [bounds[i + 1] - bounds[i] for i in range(parts)]


def _render(width, height, wall, pieces, holes):
  grid = common.grid(width, height, 0)
  out = common.grid(width, height, 0)
  for r, c in wall:
    grid[r][c] = BLUE
    out[r][c] = BLUE
  for cells in pieces:
    red = _fits_any(_norm(cells), holes, wall, width, height)
    for r, c in cells:
      grid[r][c] = GRAY
      out[r][c] = RED if red else GRAY
  return {"input": grid, "output": out}


def generate(width=None, height=None, baseline=None, recesses=None,
             pieces=None):
  """Generates one input/output pair.

  Args:
    width: grid width (sampled 12..30; explicit fixtures default to 12).
    height: grid height (sampled 12..30; explicit fixtures default to 12).
    baseline: row of the wall's lowest line (explicit mode).
    recesses: list of (left_col, [column heights]) skyline notches (explicit
      mode).
    pieces: list of gray pieces, each a list of absolute (row, col) cells
      (explicit mode).
  If recesses is None, a fresh random scene is built.
  """
  if width is None:
    width = random.randint(12, 30) if recesses is None else 12
  if height is None:
    height = random.randint(12, 30) if recesses is None else 12
  if not (12 <= width <= 30 and 12 <= height <= 30):
    raise ValueError("grid dimensions must be 12..30")
  if recesses is None and (baseline is not None or pieces is not None):
    raise ValueError("explicit baseline or pieces require explicit recesses")
  if recesses is not None:
    holes = _holes(baseline, recesses)
    wall = _wall(width, height, baseline, holes)
    return _render(width, height, wall, pieces, holes)

  for _ in range(300):
    n_rec = random.randint(1, min(4, width // 6))
    shapes = []
    for _ in range(n_rec):
      for _ in range(50):
        w = random.randint(1, 3)
        hs = [random.randint(1, 3) for _ in range(w)]
        if 2 <= sum(hs) <= 5:
          break
      else:
        hs = [2]
      shapes.append(hs)
    max_h = max(max(hs) for hs in shapes)
    lo_b, hi_b = max_h + 2, min(max(6, height // 2), height - 6)
    if lo_b > hi_b:
      continue
    base = random.randint(lo_b, hi_b)
    slack = width - 2 - sum(len(hs) for hs in shapes) - 2 * (n_rec - 1)
    if slack < 0:
      continue
    parts = _split(slack, n_rec + 1)
    recs = []
    col = 1 + parts[0]
    for i, hs in enumerate(shapes):
      recs.append((col, hs))
      col += len(hs) + 2 + parts[i + 1]
    holes = _holes(base, recs)
    wall = _wall(width, height, base, holes)
    maxph = height - 3 - base
    maxpw = 4

    chosen = []
    good = True
    for hole in holes:
      shp = _grow_fitting(hole, wall, width, height, maxph, maxpw)
      if shp is None:
        good = False
        break
      chosen.append(shp)
    if not good:
      continue
    n_d = random.randint(1, 2)
    for _ in range(n_d):
      cand = None
      if random.random() < 0.5:
        m = _mirror(random.choice(chosen))
        for _ in range(random.randint(0, 3)):
          m = _rot(m)
        h, w = _dims(m)
        if (h <= maxph and w <= maxpw
            and not _fits_any(m, holes, wall, width, height)):
          cand = m
      for _ in range(40):
        if cand is not None:
          break
        p = _random_poly(random.randint(3, 6), maxph, maxpw)
        if p is not None and not _fits_any(p, holes, wall, width, height):
          cand = p
      if cand is not None:
        chosen.append(cand)
    if random.random() < 0.3:
      p = _random_poly(random.randint(3, 5), maxph, 3)
      if p is not None:
        chosen.append(p)
    flags = [_fits_any(s, holes, wall, width, height) for s in chosen]
    if all(flags) or not any(flags):
      continue
    widths = [_dims(s)[1] for s in chosen]
    free = width - sum(widths) - (len(chosen) - 1)
    if free < 0:
      continue
    order = list(range(len(chosen)))
    random.shuffle(order)
    gaps = _split(free, len(chosen) + 1)
    placed = []
    col = gaps[0]
    for j, idx in enumerate(order):
      s = chosen[idx]
      h, w = _dims(s)
      top = height - 2 - (h - 1)
      placed.append([(top + r, col + c) for r, c in s])
      col += w + 1 + gaps[j + 1]
    return _render(width, height, wall, placed, holes)
  raise RuntimeError("could not place both fitting and non-fitting pieces")


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(baseline=3, recesses=[(3, [2, 2]), (9, [2])], pieces=[
          [(9, 0), (9, 1), (10, 0), (10, 1)],
          [(8, 3), (9, 3), (9, 4), (10, 4)],
          [(7, 8), (8, 6), (8, 7), (8, 8), (9, 6), (9, 7), (9, 8), (10, 8)],
          [(8, 10), (9, 10), (10, 10)]]),
      generate(baseline=3, recesses=[(4, [2, 2])], pieces=[
          [(9, 1), (9, 2), (9, 3), (10, 1), (10, 2)],
          [(9, 5), (9, 6), (10, 5), (10, 6)],
          [(8, 8), (9, 8), (9, 9), (10, 9)]]),
      generate(baseline=4, recesses=[(3, [2, 1]), (7, [1, 2, 1])], pieces=[
          [(9, 1), (10, 0), (10, 1), (10, 2)],
          [(8, 5), (9, 4), (9, 5), (9, 6), (10, 5)],
          [(8, 8), (9, 8), (10, 8)],
          [(8, 11), (9, 11), (10, 10), (10, 11)]]),
      generate(baseline=6, recesses=[(6, [2, 2])], pieces=[
          [(9, 1), (9, 2), (10, 1), (10, 2)],
          [(8, 4), (9, 4), (10, 4)]]),
  ]
  test = [
      generate(baseline=4, recesses=[(2, [2, 1]), (8, [2])], pieces=[
          [(8, 1), (9, 1), (9, 2), (10, 2)],
          [(7, 5), (8, 4), (8, 5), (9, 4), (10, 4)],
          [(9, 7), (9, 8), (10, 7), (10, 8)],
          [(8, 10), (9, 10), (10, 10)]]),
  ]
  return {"train": train, "test": test}
