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

"""ARC-GEN style generator for task 88e364bc.

Rule: each legend is a solid frame of colour C in a grid corner. Inside it
are one or more arrows. Each arrow is two tail cells ending in a 2. The tail
colour is 1, or another colour when C is 1. A legend therefore fixes one of
eight directions. Closed outlines are drawn in the legend colours, and yellow
markers (4) sit inside them.

To solve, lift all markers. Each marker then slides in the direction of the
legend whose colour matches the outline that encloses it. It keeps moving
while the next cell is background. A diagonal step is refused if either
orthogonal side cell is not background. Every slide is computed with all
markers lifted, and the markers are then redrawn at their end cells.

Scope of random scenes:
- Grid size. Sides are sampled from a feasibility minimum up to 28. The
  minimum is 10 + 2 * legends, so 12 for one legend and 18 for four.
  Explicit integer sides 12..30 are accepted when they meet that minimum;
  otherwise ValueError is raised. Sizes other than 20x20 are synthetic
  extensions.
- Colours. There are 1..3 shape colours from {1,3,5,6,7,8,9}.
- Legends. Each legend is a corner box of 5..7 per side (exactly 5 in tight
  grids). It holds 1..3 randomly placed, non-touching arrows, all in the same
  direction. An optional distractor legend has no outlines. Its colour may be
  any unused palette colour, including 1, which then gets a non-1 tail.
- Outlines. Each colour has 1..2 outlines on grids with fewer than 500 cells,
  or 1..3 on larger grids, subject to placement space. An interior is either a union of
  up to three overlapping rectangles or a staircase chain of 3..5 small
  offset rectangles. The staircase gives stepped walls like the hand-drawn
  fixture walls. The wall is the 8-neighbour ring of the interior.
- Touching mode (optional). Outlines of different colours may touch.
  Outlines of the same colour may touch or share wall cells, as in test 2.
- Pillars (optional). A 1x1..2x2 block of wall may sit inside an interior,
  and it may partition that interior.
- Wall marker (optional). One marker may replace a wall cell, as in test 1.
  The wall behind it is thickened so that, once lifted, the cell joins only
  its own interior. It replaces an outer ring cell, never an interior pillar.
  Diagonal wall markers require concave geometry that permits the first step.
- Diagonal legends are biased towards markers that stop on the corner-squeeze
  guard.
- Marker constraints. Every marker moves at least one cell. No marker starts
  on another marker's path, and no two markers end on the same cell.

Fixture replay: the original outlines are hand drawn, so they are passed as
an explicit latent 'layout', which is the wall picture with the markers
lifted. Markers are passed as (row, col, dr, dc) tuples, where (dr, dc) is
the direction of the legend for the enclosing outline's colour. Replay checks
the layout and markers structurally. It trusts the caller that each (dr, dc)
matches the legend. The output is always produced by the local slide routine.
"""

import random

import common


DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
PALETTE = [1, 3, 5, 6, 7, 8, 9]
TAIL_COLOURS = [3, 5, 6, 7, 8, 9]
CORNERS = ("tl", "tr", "bl", "br")
ORTHO = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _min_side(n_legends):
  """Smallest grid side accepted for n corner legends plus outlines."""
  return 10 + 2 * n_legends


def _legend(colour, direction, arrows, bh, bw, tail):
  """Solid bh x bw box of `colour` holding up to `arrows` arrows.

  Arrow cells stay off the frame border, and different arrows are never
  8-adjacent. So every 2 has exactly one non-frame neighbour (its own tail)
  and seven frame neighbours, which makes the direction readout unambiguous.
  """
  dr, dc = direction
  box = [[colour] * bw for _ in range(bh)]
  placed = []
  used = set()
  for _ in range(60):
    if len(placed) >= arrows:
      break
    hr = random.randint(1, bh - 2)
    hc = random.randint(1, bw - 2)
    cells = [(hr - 2 * dr, hc - 2 * dc), (hr - dr, hc - dc), (hr, hc)]
    if any(not (1 <= r <= bh - 2 and 1 <= c <= bw - 2) for r, c in cells):
      continue
    halo = {(r + i, c + j) for r, c in cells
            for i in (-1, 0, 1) for j in (-1, 0, 1)}
    if halo & used:
      continue
    used |= set(cells)
    placed.append(cells)
  if not placed:
    cy, cx = bh // 2, bw // 2
    placed.append([(cy - dr, cx - dc), (cy, cx), (cy + dr, cx + dc)])
  for cells in placed:
    for r, c in cells[:2]:
      box[r][c] = tail
    r, c = cells[2]
    box[r][c] = 2
  return box


def _dilate(cells, h, w):
  out = set()
  for r, c in cells:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
          out.add((rr, cc))
  return out


def _ring(cells):
  ring = set()
  for r, c in cells:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        n = (r + dr, c + dc)
        if n not in cells:
          ring.add(n)
  return ring


def _normalise(rects):
  cells = set()
  for r, c, hh, ww in rects:
    for i in range(hh):
      for j in range(ww):
        cells.add((r + i, c + j))
  mr = min(r for r, _ in cells)
  mc = min(c for _, c in cells)
  return {(r - mr, c - mc) for r, c in cells}


def _blob(maxh, maxw):
  """Union of 1..3 rectangles, each overlapping an earlier one (4-connected)."""
  rects = [(0, 0, random.randint(2, maxh), random.randint(2, maxw))]
  for _ in range(random.randint(0, 2)):
    br, bc, bh, bw = random.choice(rects)
    nh, nw = random.randint(2, maxh), random.randint(2, maxw)
    r = random.randint(br - nh + 1, br + bh - 1)
    c = random.randint(bc - nw + 1, bc + bw - 1)
    rects.append((r, c, nh, nw))
  return _normalise(rects)


def _stair_blob(maxh, maxw):
  """Staircase interior: a chain of small rectangles stepping down.

  Each rectangle is 2..3 per side. It moves down by at least one row and
  consistently left or right by at least one column, while still overlapping
  the previous rectangle. Row starts strictly increase and row ends never
  decrease, so each row's coverage is one interval. The interior is therefore
  4-connected and hole-free.
  """
  step = random.choice((1, -1))
  rects = [(0, 0, random.randint(2, 3), random.randint(2, 3))]
  for _ in range(random.randint(2, 4)):
    pr, pc, ph, pw = rects[-1]
    nh, nw = random.randint(2, 3), random.randint(2, 3)
    r = random.randint(pr + 1, pr + ph - 1)
    if step > 0:
      c = random.randint(pc + 1, pc + pw - 1)
    else:
      c = random.randint(pc - nw + 1, pc - 1)
    trial = rects + [(r, c, nh, nw)]
    top = min(x[0] for x in trial)
    bot = max(x[0] + x[2] for x in trial)
    lef = min(x[1] for x in trial)
    rig = max(x[1] + x[3] for x in trial)
    if bot - top > maxh + 2 or rig - lef > maxw + 2:
      break
    rects = trial
  return _normalise(rects)


def _slide(lifted, r, c, dr, dc):
  """Slide over background; return end, path and whether the corner guard hit."""
  h, w = len(lifted), len(lifted[0])
  path = []
  guard = False
  while 0 <= r + dr < h and 0 <= c + dc < w and lifted[r + dr][c + dc] == 0:
    if dr and dc and (lifted[r + dr][c] != 0 or lifted[r][c + dc] != 0):
      guard = True
      break
    r += dr
    c += dc
    path.append((r, c))
  return r, c, path, guard


def _render(lifted, markers):
  inp = [row[:] for row in lifted]
  out = [row[:] for row in lifted]
  targets = []
  for r, c, dr, dc in markers:
    inp[r][c] = 4
    tr, tc, _, _ = _slide(lifted, r, c, dr, dc)
    targets.append((tr, tc))
  for tr, tc in targets:
    out[tr][tc] = 4
  return {"input": inp, "output": out}


def _wall_candidates(cells, walls, forbidden, h, w, direction, candidates=None):
  """Wall cells that can hold a marker sliding into the open interior.

  The cell must be 4-adjacent to the interior, and its first step must enter
  the interior. Its outward 8-neighbours are thickened into wall ('extra'),
  so that once lifted it joins only this outline's interior.
  """
  dr, dc = direction
  out = []
  # Retain all walls as obstacles but restrict which ones may be lifted.
  for qr, qc in sorted(walls if candidates is None else candidates):
    if (qr + dr, qc + dc) not in cells:
      continue
    if not any((qr - vr, qc - vc) in cells for vr, vc in ORTHO):
      continue
    extra = []
    ok = True
    for i in (-1, 0, 1):
      for j in (-1, 0, 1):
        n = (qr + i, qc + j)
        if n == (qr, qc) or n in cells or n in walls:
          continue
        if not (0 <= n[0] < h and 0 <= n[1] < w):
          continue
        if n in forbidden:
          ok = False
        extra.append(n)
    if ok:
      out.append(((qr, qc), extra))
  random.shuffle(out)
  return out


def _place_shape(col, shapes, legend_block, h, w, maxh, maxw, touch_mode):
  """Place one outline of colour `col`; return a shape record or None.

  In touch mode an outline may touch outlines of other colours (the walls
  stay disjoint). It may also share wall cells with same-colour outlines, as
  long as interiors stay out of each other's footprint. Otherwise a background
  gap of at least one cell is kept.
  """
  for _ in range(30):
    if random.random() < 0.35:
      blob = _stair_blob(maxh, maxw)
    else:
      blob = _blob(maxh, maxw)
    bh = max(r for r, _ in blob) + 1
    bw = max(c for _, c in blob) + 1
    if bh > h - 2 or bw > w - 2:
      continue
    valid, touching = [], []
    for _ in range(20):
      orow = random.randint(1, h - 1 - bh)
      ocol = random.randint(1, w - 1 - bw)
      cells = {(r + orow, c + ocol) for r, c in blob}
      ring = _ring(cells)
      foot = cells | ring
      if foot & legend_block:
        continue
      ok, touches = True, False
      for other in shapes:
        if touch_mode:
          if other["col"] == col:
            clash = cells & other["foot"] or other["cells"] & foot
          else:
            clash = foot & other["foot"]
          if clash:
            ok = False
            break
          if foot & other["halo"]:
            touches = True
        elif foot & other["halo"]:
          ok = False
          break
      if not ok:
        continue
      valid.append((cells, ring, foot))
      if touches:
        touching.append((cells, ring, foot))
    if valid:
      pool = touching if touching and random.random() < 0.75 else valid
      cells, ring, foot = random.choice(pool)
      return {"col": col, "cells": cells, "ring": ring, "foot": foot,
              "halo": _dilate(foot, h, w), "pillar": set()}
  return None


def _check_args(width, height, colours, directions, distractor):
  for name, v in (("width", width), ("height", height)):
    if v is not None and (not _is_int(v) or not 12 <= v <= 30):
      raise ValueError(name + " must be an integer in 12..30")
  if colours is not None:
    if any(not _is_int(c) or c not in PALETTE for c in colours):
      raise ValueError("colours must be integers from " + str(PALETTE))
    if not 1 <= len(colours) <= 3 or len(set(colours)) != len(colours):
      raise ValueError("colours must be 1..3 distinct values")
  if directions is not None:
    if any(d not in DIRS for d in directions):
      raise ValueError("directions must be unit 8-neighbour steps")
    if colours is not None and len(directions) != len(colours):
      raise ValueError("directions must align with colours")
    if not 1 <= len(directions) <= 3:
      raise ValueError("directions must have 1..3 entries")
  given = [v for v in (width, height) if v is not None]
  if given:
    if colours is not None:
      n = len(colours)
    elif directions is not None:
      n = len(directions)
    else:
      n = 1
    need = _min_side(n + (1 if distractor else 0))
    if min(given) < need:
      raise ValueError("grid side must be >= %d for %d legends" %
                       (need, n + (1 if distractor else 0)))


def _check_replay(layout, markers):
  """Validate an explicit replay scene; return (lifted grid, marker list)."""
  if not isinstance(layout, (list, tuple)) or not 1 <= len(layout) <= 30:
    raise ValueError("layout must be a list of 1..30 rows")
  width = None
  lifted = []
  for row in layout:
    if not isinstance(row, str) or not 1 <= len(row) <= 30:
      raise ValueError("layout rows must be strings of 1..30 digits")
    if width is None:
      width = len(row)
    if len(row) != width:
      raise ValueError("layout must be rectangular")
    if any(ch not in "012356789" for ch in row):
      raise ValueError("layout digits must exclude the lifted marker colour 4")
    lifted.append([int(ch) for ch in row])
  h, w = len(lifted), width
  if not isinstance(markers, (list, tuple)) or not markers:
    raise ValueError("at least one marker is required")
  marks, starts, ends = [], set(), set()
  paths = []
  for m in markers:
    if (not isinstance(m, (list, tuple)) or len(m) != 4 or
        not all(_is_int(v) for v in m)):
      raise ValueError("markers must be (row, col, dr, dc) integer tuples")
    r, c, dr, dc = m
    if not (0 <= r < h and 0 <= c < w):
      raise ValueError("marker out of bounds")
    if lifted[r][c] != 0:
      raise ValueError("marker must sit on a background cell of the layout")
    if (dr, dc) not in DIRS:
      raise ValueError("marker direction must be a unit 8-neighbour step")
    if (r, c) in starts:
      raise ValueError("duplicate marker")
    tr, tc, path, _ = _slide(lifted, r, c, dr, dc)
    if not path:
      raise ValueError("every marker must move at least one cell")
    if (tr, tc) in ends:
      raise ValueError("two markers end on the same cell")
    starts.add((r, c))
    ends.add((tr, tc))
    marks.append((r, c, dr, dc))
    paths.append(path)
  if any(starts.intersection(path) for path in paths):
    raise ValueError("a marker may not start on another marker's path")
  return lifted, marks


def _attempt(width, height, colours, directions, distractor, wall_marker,
             touching, pillars):
  """One construction attempt; returns a pair or None."""
  given = [v for v in (width, height) if v is not None]
  side_cap = min(given) if given else 30
  if colours is not None:
    shape_cols = list(colours)
  else:
    if directions is not None:
      n = len(directions)
    else:
      reserve = 1 if distractor else 0
      n = random.randint(1, max(1, min(3, (side_cap - 10) // 2 - reserve)))
    shape_cols = random.sample(PALETTE, n)
  n = len(shape_cols)
  if distractor is None:
    use_distractor = (_min_side(n + 1) <= side_cap and
                      random.random() < 0.25)
  else:
    use_distractor = distractor
  req = _min_side(n + (1 if use_distractor else 0))
  h = height if height is not None else random.randint(req, 28)
  w = width if width is not None else random.randint(req, 28)
  dirs = list(directions) if directions is not None else random.sample(DIRS, n)
  legend_cols = list(shape_cols)
  if use_distractor:
    legend_cols.append(random.choice(
        [c for c in PALETTE if c not in legend_cols]))
    dirs.append(random.choice([d for d in DIRS if d not in dirs]))
  dir_of = dict(zip(legend_cols, dirs))
  tail_of = {}
  for col in legend_cols:
    if col == 1:
      others = [c for c in shape_cols if c != 1]
      if others and random.random() < 0.6:
        tail_of[col] = random.choice(others)
      else:
        tail_of[col] = random.choice(TAIL_COLOURS)
    else:
      tail_of[col] = 1

  lifted = common.grid(w, h, 0)
  big_ok = min(h, w) >= _min_side(len(legend_cols)) + 3
  legend_cells, legend_block = set(), set()
  corners = random.sample(CORNERS, len(legend_cols))
  for col, corner in zip(legend_cols, corners):
    bh = random.choice((5, 5, 6, 7)) if big_ok else 5
    bw = random.choice((5, 5, 6, 7)) if big_ok else 5
    box = _legend(col, dir_of[col], random.randint(1, 3), bh, bw, tail_of[col])
    r0 = 0 if corner[0] == "t" else h - bh
    c0 = 0 if corner[1] == "l" else w - bw
    cells = {(r0 + i, c0 + j) for i in range(bh) for j in range(bw)}
    if cells & legend_block:
      return None
    for i in range(bh):
      for j in range(bw):
        lifted[r0 + i][c0 + j] = box[i][j]
    legend_cells |= cells
    legend_block |= _dilate(cells, h, w)

  touch_mode = touching if touching is not None else random.random() < 0.5
  maxh = max(3, min(8, h // 3))
  maxw = max(3, min(8, w // 3))
  per_colour = 2 if h * w < 500 else 3
  shapes = []
  for col in shape_cols:
    for s in range(random.randint(1, per_colour)):
      shape = _place_shape(col, shapes, legend_block, h, w, maxh, maxw,
                           touch_mode)
      if shape is None:
        if s == 0:
          return None
        break
      shapes.append(shape)
  if touching:
    if not any(shapes[i]["foot"] & shapes[j]["halo"]
               for i in range(len(shapes)) for j in range(i + 1, len(shapes))):
      return None
  for shape in shapes:
    for r, c in shape["ring"]:
      lifted[r][c] = shape["col"]

  pillar_mode = pillars if pillars is not None else random.random() < 0.35
  if pillar_mode:
    placed_any = False
    for shape in shapes:
      if len(shape["cells"]) < 12 or random.random() < 0.3:
        continue
      ph, pw = random.choice(((1, 1), (1, 2), (2, 1), (2, 2)))
      anchors = [(r, c) for r, c in sorted(shape["cells"])
                 if all((r + i, c + j) in shape["cells"]
                        for i in range(ph) for j in range(pw))]
      if not anchors:
        continue
      r, c = random.choice(anchors)
      block = {(r + i, c + j) for i in range(ph) for j in range(pw)}
      if len(shape["cells"]) - len(block) < 8:
        continue
      shape["cells"] = shape["cells"] - block
      shape["pillar"] = shape["pillar"] | block
      for pr, pc in block:
        lifted[pr][pc] = shape["col"]
      placed_any = True
    if pillars and not placed_any:
      return None

  marks, paths = [], []

  def try_add(r, c, d):
    _, _, path, _ = _slide(lifted, r, c, d[0], d[1])
    if not path:
      return False
    for (mr, mc, _, _), p in zip(marks, paths):
      if (r, c) in p or (mr, mc) in path or (r, c) == (mr, mc):
        return False
      if p[-1] == path[-1]:
        return False
    marks.append((r, c, d[0], d[1]))
    paths.append(path)
    return True

  want_wall = wall_marker if wall_marker is not None else random.random() < 0.3
  wall_shape = None
  if want_wall:
    order = list(range(len(shapes)))
    random.shuffle(order)
    for si in order:
      shape = shapes[si]
      col = shape["col"]
      others = set(legend_cells)
      for sj, other in enumerate(shapes):
        if sj != si:
          others |= other["foot"]
      forbidden = _dilate(others, h, w)
      walls = shape["ring"] | shape["pillar"]
      for (qr, qc), extra in _wall_candidates(shape["cells"], walls, forbidden,
                                              h, w, dir_of[col],
                                              candidates=shape["ring"]):
        if (qr, qc) in others:
          continue
        lifted[qr][qc] = 0
        for er, ec in extra:
          lifted[er][ec] = col
        if try_add(qr, qc, dir_of[col]):
          wall_shape = si
          break
        lifted[qr][qc] = col
        for er, ec in extra:
          lifted[er][ec] = 0
      if wall_shape is not None:
        break
    if wall_shape is None and wall_marker:
      return None

  for si, shape in enumerate(shapes):
    if si != wall_shape and len(shapes) > 1 and random.random() < 0.15:
      continue
    d = dir_of[shape["col"]]
    lo = 0 if si == wall_shape else 1
    k = random.randint(lo, 3 if len(shape["cells"]) >= 20 else 2)
    cand = sorted(shape["cells"])
    random.shuffle(cand)
    if d[0] and d[1] and random.random() < 0.6:
      first, rest = [], []
      for r, c in cand:
        _, _, path, guard = _slide(lifted, r, c, d[0], d[1])
        (first if path and guard else rest).append((r, c))
      cand = first + rest
    got = 0
    for r, c in cand:
      if got >= k:
        break
      if try_add(r, c, d):
        got += 1
  if len(marks) < 2:
    return None
  zeros = sum(row.count(0) for row in lifted)
  if zeros * 2 <= h * w:
    return None
  return _render(lifted, marks)


def generate(width=None, height=None, colours=None, directions=None,
             distractor=None, wall_marker=None, touching=None, pillars=None,
             layout=None, markers=None):
  """Build one input/output pair.

  Args:
    width: integer grid width. If None it is random from the feasibility
      minimum to 28. An explicit value must be in 12..30 and at least the
      minimum, which is 10 + 2 * number_of_legends.
    height: integer grid height, with the same rules as width.
    colours: list of 1..3 distinct shape/legend colours from {1,3,5,6,7,8,9}.
    directions: list of (dr, dc) integer legend directions aligned with
      colours. If it is given without colours, its length sets the colour
      count.
    distractor: None or bool. True/False forces or forbids an extra legend
      with no outlines. If None it is used with probability 0.25 when the
      size allows.
    wall_marker: None or bool. True/False forces or forbids one marker that
      replaces a wall cell. If None it is attempted with probability 0.3.
    touching: None or bool. True requires at least one pair of touching
      outlines (walls of different colours in contact, or touching/shared
      same-colour walls). False keeps a background gap between outlines. If None it is
      random.
    pillars: None or bool. True requires at least one wall pillar inside an
      interior, and False forbids pillars. If None they appear with
      probability 0.35.
    layout: optional list of digit strings giving the wall picture with the
      markers lifted (explicit latent scene, used for fixture replay). It
      cannot be combined with the random-scene controls above.
    markers: used with layout. A list of (row, col, dr, dc) markers, where
      (dr, dc) is the legend direction of the enclosing outline's colour.
  """
  if layout is not None:
    if any(v is not None for v in (width, height, colours, directions,
                                   distractor, wall_marker, touching, pillars)):
      raise ValueError("layout replay cannot be combined with scene controls")
    lifted, marks = _check_replay(layout, markers)
    return _render(lifted, marks)
  if markers is not None:
    raise ValueError("markers are only meaningful together with layout")
  for name, v in (("distractor", distractor), ("wall_marker", wall_marker),
                  ("touching", touching), ("pillars", pillars)):
    if v is not None and not isinstance(v, bool):
      raise ValueError(name + " must be None, True or False")
  if colours is not None:
    if not isinstance(colours, (list, tuple)):
      raise ValueError("colours must be a list")
    colours = list(colours)
  if directions is not None:
    if not isinstance(directions, (list, tuple)):
      raise ValueError("directions must be a list")
    for d in directions:
      if (not isinstance(d, (list, tuple)) or len(d) != 2 or
          not all(_is_int(x) for x in d)):
        raise ValueError("each direction must be an integer (dr, dc) pair")
    directions = [tuple(d) for d in directions]
  _check_args(width, height, colours, directions, distractor)
  for _ in range(500):
    scene = _attempt(width, height, colours, directions, distractor,
                     wall_marker, touching, pillars)
    if scene is not None:
      return scene
  raise RuntimeError("could not build a valid scene for these parameters")


_P1 = [
    "77777000000000055555", "71127000000000052115", "77777000000000055555",
    "71127000000000052115", "77777000777770055555", "00000007700070000000",
    "00000077000070000000", "07777770007770055550", "07000000077005550050",
    "07000000075555000050", "07700000075000000550", "00777700075000000500",
    "00000777775000000500", "00000005555000000500", "05555555000000000550",
    "05000050000000000050", "05000050000000000050", "05500055000000000550",
    "00505555555555555500", "00555000000055000000"]

_P2 = [
    "00000000000005555555", "00000000000005551555", "00000000000005155155",
    "00000000000005515525", "00000000000005552555", "00000055550005555555",
    "00000550055000000000", "00555500005550000000", "00500000000055550000",
    "00500000000000050000", "00500000000000050000", "00500055000000050000",
    "00500055000000050000", "05500055000000050000", "05000055000000050000",
    "05000055500000550000", "05505550500005500000", "00555000500055000000",
    "00000000555550000000", "00000000000000000000"]

_P3 = [
    "00000000000000055555", "00000000000000051515", "00000000000000051515",
    "00000000000000052525", "00005555500000055555", "00005000555000000000",
    "00005000005550000000", "00005000000050000000", "00555000000055000000",
    "00500000000005500000", "00500555500005500000", "00555500555555555000",
    "00500000000000005000", "00550000000000005000", "00055000000005505000",
    "00005005500055555000", "00005005550050000000", "00005005055050000000",
    "00005005005550000000", "00000550000000000000"]

_T1 = [
    "55555550000000000000", "55515550055500000000", "51551550050555000000",
    "55155250050005005500", "55525550050005555550", "55555550050000000050",
    "00000000050000000050", "00000000055000000050", "00000111115000000050",
    "00000100015550055550", "00000100011155550000", "00000110000100000000",
    "00000011000111111000", "00000000100001001100", "00000000110001000110",
    "11111000011111000010", "12121000010000000010", "15151000010000000010",
    "15151000011011111110", "11111000001110000000"]

_T2 = [
    "66666000000000000000", "62626003333333006666", "61616003000003006006",
    "61616033000003666606", "66666030000033600006", "00000030000030600006",
    "00333330000033666006", "00300000000003306006", "00330000000003306006",
    "00033333333333006606", "00003333333000000666", "00003000003000000000",
    "00003000003000000000", "00033000003000000000", "00330000003003333333",
    "00300000033003332333", "00300000030003233133", "00330000030003313313",
    "00033300330003331333", "00000333300003333333"]


def validate():
  """Rebuild the canonical pairs from explicit latent layouts and markers."""
  train = [
      generate(layout=_P1, markers=[(6, 9, 0, 1), (10, 4, 0, 1),
                                    (12, 15, 0, -1), (15, 4, 0, -1),
                                    (16, 13, 0, -1)]),
      generate(layout=_P2, markers=[(9, 3, 1, 1), (15, 11, 1, 1)]),
      generate(layout=_P3, markers=[(6, 5, 1, 0), (13, 6, 1, 0),
                                    (13, 10, 1, 0)]),
  ]
  test = [
      generate(layout=_T1, markers=[(3, 11, 1, 1), (6, 11, 1, 1),
                                    (12, 9, -1, 0), (17, 16, -1, 0),
                                    (18, 11, -1, 0)]),
      generate(layout=_T2, markers=[(5, 16, -1, 0), (8, 18, -1, 0),
                                    (7, 9, -1, -1), (8, 11, -1, -1),
                                    (13, 6, -1, -1), (17, 5, -1, -1)]),
  ]
  return {"train": train, "test": test}
