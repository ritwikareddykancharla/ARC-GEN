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

"""ARC-GEN style generator for task 184a9768 (rectangular jigsaw).

Rule: the input holds one or more large solid rectangular "frames", each
pierced by enclosed background holes. Small solid rectangular pieces float
outside the frames, and single grey (5) cells are scattered as noise. The
total piece area equals the total hole area. In the output every piece is
translated (never rotated) into the holes so that the holes are tiled
exactly. The pieces vanish from their old places and all grey noise is
erased.

Scope: 1-3 frames, 1-4 holes per frame. A hole is one rectangle, two or
three rectangles stacked along a full shared edge, or two rectangles joined
along part of an edge (L / T / step shapes). Every rectangle of a hole is
one loose piece. Grid sizes are 14..30 per side. Colours are random. The
latent layout is constructed directly. A local exact-cover enumerator
rejects scenes where a different tiling would give a different coloured
output.
"""

import random

import common

PALETTE = [1, 2, 3, 4, 6, 7, 8, 9]


def _rect(r, c, h, w):
  return [(r + i, c + j) for i in range(h) for j in range(w)]


def _render(height, width, frames, pieces, noise):
  inp = common.grid(width, height, 0)
  out = common.grid(width, height, 0)
  for colour, top, left, h, w in frames:
    for r, c in _rect(top, left, h, w):
      inp[r][c] = colour
      out[r][c] = colour
  for colour, h, w, sr, sc, dr, dc in pieces:
    for r, c in _rect(dr, dc, h, w):
      inp[r][c] = 0
  for colour, h, w, sr, sc, dr, dc in pieces:
    for r, c in _rect(sr, sc, h, w):
      inp[r][c] = colour
    for r, c in _rect(dr, dc, h, w):
      out[r][c] = colour
  for r, c in noise:
    inp[r][c] = 5
  return {"input": inp, "output": out}


def _dims():
  a, b = random.randint(1, 3), random.randint(1, 6)
  return (a, b) if random.random() < 0.5 else (b, a)


def _hole_template():
  """Returns a list of (h, w, r, c) rectangles with normalised offsets."""
  kind = random.choices(["single", "stack", "attach", "triple"],
                        weights=[5, 3, 3, 1])[0]
  if kind == "single":
    h, w = _dims()
    return [(h, w, 0, 0)]
  if kind in ("stack", "triple"):
    n = 2 if kind == "stack" else 3
    length = random.randint(1, 6)
    hi = 3 if n == 2 else 2
    vertical = random.random() < 0.5
    rects, off = [], 0
    for _ in range(n):
      t = random.randint(1, hi)
      rects.append((t, length, off, 0) if vertical else (length, t, 0, off))
      off += t
    return rects
  ah, aw = _dims()
  bh, bw = _dims()
  if random.random() < 0.5:
    ro = random.randint(-(bh - 1), ah - 1)
    rects = [(ah, aw, 0, 0), (bh, bw, ro, aw)]
  else:
    co = random.randint(-(bw - 1), aw - 1)
    rects = [(ah, aw, 0, 0), (bh, bw, ah, co)]
  mr = min(r for _, _, r, _ in rects)
  mc = min(c for _, _, _, c in rects)
  return [(h, w, r - mr, c - mc) for h, w, r, c in rects]


def _ambiguous(hole_cells, piece_types, limit=40000):
  """True if the tilings give more than one coloured result or the search is too big."""
  counts = {}
  for t in piece_types:
    counts[t] = counts.get(t, 0) + 1
  results = set()
  nodes = [0]
  placed = []

  def rec(unc):
    nodes[0] += 1
    if nodes[0] > limit:
      return True
    if not unc:
      results.add(frozenset(placed))
      return len(results) > 1
    t = min(unc)
    for typ in list(counts):
      if counts[typ] == 0:
        continue
      colour, h, w = typ
      cells = _rect(t[0], t[1], h, w)
      if all(x in unc for x in cells):
        counts[typ] -= 1
        for x in cells:
          placed.append((x, colour))
        stop = rec(unc - frozenset(cells))
        for _ in cells:
          placed.pop()
        counts[typ] += 1
        if stop:
          return True
    return False

  return rec(frozenset(hole_cells)) or len(results) != 1


def _dilate_into(forb, cells):
  for r, c in cells:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        forb.add((r + dr, c + dc))


def _random_scene(requested_height=None, requested_width=None):
  for _ in range(600):
    height = requested_height if requested_height is not None else random.randint(14, 30)
    width = requested_width if requested_width is not None else random.randint(14, 30)
    nf = random.choice([1, 1, 2, 2, 2, 3]) if height * width > 500 else random.choice([1, 1, 2])
    rects = []
    for _ in range(nf):
      for _ in range(40):
        h = random.randint(5, min(18, height - 2))
        w = random.randint(5, min(18, width - 2))
        top, left = random.randint(0, height - h), random.randint(0, width - w)
        ok = all(top + h + 1 <= t2 or t2 + h2 + 1 <= top or
                 left + w + 1 <= l2 or l2 + w2 + 1 <= left
                 for t2, l2, h2, w2 in rects)
        if ok:
          rects.append((top, left, h, w))
          break
    if not rects:
      continue
    colours = random.sample(PALETTE, len(rects))
    frames = [(colours[i],) + rects[i] for i in range(len(rects))]
    holes_pieces = []  # (colour, h, w, dr, dc)
    near_hole = set()
    hole_cells = set()
    good = True
    for fc, top, left, h, w in frames:
      target = random.randint(1, 4)
      made = 0
      for _ in range(40):
        if made >= target:
          break
        tpl = _hole_template()
        bh = max(r + hh for hh, _, r, _ in tpl)
        bw = max(c + ww for _, ww, _, c in tpl)
        if bh > h - 2 or bw > w - 2 or len(tpl) + len(holes_pieces) > 12:
          continue
        r0 = random.randint(top + 1, top + h - 1 - bh)
        c0 = random.randint(left + 1, left + w - 1 - bw)
        cells = []
        for hh, ww, r, c in tpl:
          cells += _rect(r0 + r, c0 + c, hh, ww)
        if any(x in near_hole for x in cells):
          continue
        _dilate_into(near_hole, cells)
        hole_cells.update(cells)
        choices = [p for p in PALETTE if p != fc]
        for hh, ww, r, c in tpl:
          holes_pieces.append((random.choice(choices), hh, ww, r0 + r, c0 + c))
        made += 1
      if made == 0:
        good = False
        break
    if not good:
      continue
    if _ambiguous(hole_cells, [(p[0], p[1], p[2]) for p in holes_pieces]):
      continue
    forb = set()
    for fc, top, left, h, w in frames:
      _dilate_into(forb, _rect(top, left, h, w))
    order = sorted(range(len(holes_pieces)),
                   key=lambda i: -holes_pieces[i][1] * holes_pieces[i][2])
    srcs = {}
    for i in order:
      colour, h, w, dr, dc = holes_pieces[i]
      cands = [(r, c) for r in range(height - h + 1) for c in range(width - w + 1)
               if all(x not in forb for x in _rect(r, c, h, w))]
      if not cands:
        good = False
        break
      r, c = random.choice(cands)
      srcs[i] = (r, c)
      _dilate_into(forb, _rect(r, c, h, w))
    if not good:
      continue
    noise = []
    for _ in range(random.randint(3, 12)):
      cands = [(r, c) for r in range(height) for c in range(width)
               if (r, c) not in forb]
      if not cands:
        break
      cell = random.choice(cands)
      noise.append(cell)
      _dilate_into(forb, [cell])
    pieces = [(holes_pieces[i][0], holes_pieces[i][1], holes_pieces[i][2],
               srcs[i][0], srcs[i][1], holes_pieces[i][3], holes_pieces[i][4])
              for i in range(len(holes_pieces))]
    random.shuffle(pieces)
    pair = _render(height, width, frames, pieces, noise)
    counts = {}
    for row in pair["input"]:
      for v in row:
        counts[v] = counts.get(v, 0) + 1
    zero = counts.get(0, 0)
    if any(v != 0 and n >= zero for v, n in counts.items()):
      continue
    return pair
  raise RuntimeError("could not construct a valid jigsaw scene")


def generate(height=None, width=None, frames=None, pieces=None, noise=None):
  """Builds one jigsaw pair.

  Args:
    height: grid height (random 14..30 if omitted).
    width: grid width (random 14..30 if omitted).
    frames: list of (colour, top, left, h, w) solid frame rectangles.
    pieces: list of (colour, h, w, src_row, src_col, dst_row, dst_col). Each
      piece is a solid h x w rectangle. Its destination cells are background
      holes in the input. Their union defines every hole.
    noise: list of (row, col) grey (5) noise cells.
  If frames is None, a fresh random scene is built.
  """
  if frames is None:
    if pieces is not None or noise is not None:
      raise ValueError('explicit pieces/noise require explicit frames')
    if any(v is not None and not 14 <= v <= 30 for v in (height, width)):
      raise ValueError('random canvas dimensions must be 14..30')
    return _random_scene(height, width)
  return _render(height, width, frames, pieces, noise or [])


def validate():
  train = [
      generate(20, 22,
               frames=[(1, 1, 2, 7, 8), (4, 9, 7, 6, 11)],
               pieces=[(2, 1, 5, 2, 12, 4, 4), (2, 1, 5, 18, 3, 5, 4),
                       (3, 3, 1, 3, 19, 11, 12), (3, 3, 1, 16, 17, 11, 13),
                       (4, 1, 3, 5, 12, 2, 3), (8, 2, 2, 12, 1, 10, 8)],
               noise=[(0, 19), (2, 0), (5, 16), (9, 1), (9, 21), (10, 4),
                      (13, 19), (15, 4), (18, 12)]),
      generate(21, 23,
               frames=[(2, 2, 3, 9, 11), (1, 12, 9, 7, 10)],
               pieces=[(3, 1, 2, 2, 17, 17, 10), (8, 2, 3, 6, 16, 7, 6),
                       (8, 2, 3, 12, 3, 7, 9), (6, 3, 6, 9, 17, 13, 12),
                       (4, 1, 1, 16, 1, 3, 11), (4, 3, 4, 18, 3, 3, 4)],
               noise=[(0, 0), (0, 15), (3, 21), (4, 0), (16, 21), (20, 17)]),
      generate(20, 20,
               frames=[(1, 2, 1, 12, 9)],
               pieces=[(2, 2, 3, 1, 12, 3, 2), (4, 1, 4, 7, 13, 7, 3),
                       (8, 4, 1, 9, 16, 5, 7), (3, 2, 2, 15, 9, 10, 4),
                       (4, 1, 1, 18, 16, 10, 8)],
               noise=[(0, 4), (1, 16), (4, 13), (4, 18), (9, 18), (10, 12),
                      (15, 14), (15, 19), (17, 4), (18, 6), (18, 18)]),
  ]
  test = [
      generate(25, 26,
               frames=[(4, 1, 2, 6, 13), (8, 3, 17, 16, 8)],
               pieces=[(2, 2, 3, 9, 1, 2, 3), (4, 1, 6, 12, 6, 7, 18),
                       (3, 4, 1, 14, 1, 8, 23), (1, 3, 2, 15, 7, 11, 19),
                       (1, 3, 1, 15, 13, 3, 8), (3, 1, 1, 20, 3, 2, 11),
                       (1, 3, 2, 20, 5, 14, 19), (2, 2, 1, 21, 19, 2, 6),
                       (3, 1, 1, 23, 11, 5, 20), (7, 2, 2, 23, 24, 14, 22)],
               noise=[(0, 19), (8, 9), (10, 14), (16, 11), (19, 9), (22, 17),
                      (22, 23), (23, 4)]),
  ]
  return {"train": train, "test": test}
