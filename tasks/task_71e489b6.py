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

"""ARC task 71e489b6: erase stray 1-specks, ring 0-holes with 7.

Rule:
  The grid is a layout of thick solid regions of colour 0 and colour 1.
  Two kinds of small defects are added to it.
  * Specks are isolated 1-cells inside 0 territory. In the output each speck
    becomes 0.
  * Holes are small, thin 0-groups inside 1 territory: single cells,
    dominoes, diagonal pairs or triples, and L-trominoes. In the output the
    hole cells stay 0. Every other cell that touches a hole, diagonals
    included, is painted 7. The ring is drawn even where it spills into a
    neighbouring 0 region, and it is clipped at the grid border.

Scope:
  The base layout is one of three kinds: horizontal bands, vertical bands, or
  a background with 1-3 overlaid rectangles. Every row run and column run of
  either colour is at least 2 cells long, so the base survives cardinal peeling.
  Grid sides are sampled in 10..28 by default. Explicit sizes 8..30 are
  accepted. Sizes beyond the fixtures (16..19) are synthetic extensions of
  the same rule.
  Holes may touch the grid border. A single-cell hole may also sit on the
  boundary of a 1 region, with at most one cardinal 0-neighbour, so that its
  ring spills into the 0 region. Multi-cell holes have a ring lying wholly in
  1 territory. Ordinary holes leave every remaining 1-cell with at least two
  cardinal 1-neighbours. Optional bridge clusters instead put three holes
  around a central 1-cell. That cell is erased in stage one and painted 7
  in stage two: it was not an original 0-hole. The fourth arm remains 1.
  Bridge clusters lie within a protected 5-by-5 patch of 1 territory.
  Specks either float in 0 territory or form an interior bump with exactly one
  cardinal 1-neighbour. Bumps stay away from holes and the grid border.
  Specks are
  pairwise at Chebyshev distance of at least 2. Holes keep the same spacing
  from each other.
  The fixtures are replayed through explicit latent arguments: the base
  rectangles, the hole cells and the speck cells.
"""

import random

import common


_SHAPES = [
    [(0, 0)], [(0, 0)], [(0, 0)], [(0, 0)],
    [(0, 0), (0, 1)], [(0, 0), (1, 0)],
    [(0, 0), (1, 1)], [(0, 1), (1, 0)],
    [(0, 0), (1, 1), (2, 2)], [(0, 2), (1, 1), (2, 0)],
    [(0, 1), (1, 0), (1, 1)], [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0)], [(0, 0), (0, 1), (1, 1)],
]

_SINGLE = [(0, 0)]

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _base(width, height, background, rects):
  g = [list(row) for row in common.grid(width, height, background)]
  for r0, c0, r1, c1, col in rects:
    for r in range(r0, r1 + 1):
      for c in range(c0, c1 + 1):
        g[r][c] = col
  return g


def _ring(cells, height, width):
  cs = set(cells)
  out = set()
  for r, c in cs:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        rr, cc = r + dr, c + dc
        if 0 <= rr < height and 0 <= cc < width and (rr, cc) not in cs:
          out.add((rr, cc))
  return out


def _render(width, height, background, rects, holes, specks):
  base = _base(width, height, background, rects)
  inp = [row[:] for row in base]
  out = [row[:] for row in base]
  hole_set = set(tuple(h) for h in holes)
  for r, c in hole_set:
    inp[r][c] = 0
    out[r][c] = 0
  for r, c in specks:
    inp[r][c] = 1
  for r, c in _ring(hole_set, height, width):
    out[r][c] = 7
  return {"input": inp, "output": out}


def _thick(g):
  h, w = len(g), len(g[0])
  for r in range(h):
    c = 0
    while c < w:
      e = c
      while e + 1 < w and g[r][e + 1] == g[r][c]:
        e += 1
      if e - c + 1 < 2:
        return False
      c = e + 1
  for c in range(w):
    r = 0
    while r < h:
      e = r
      while e + 1 < h and g[e + 1][c] == g[r][c]:
        e += 1
      if e - r + 1 < 2:
        return False
      r = e + 1
  return True


def _random_layout(height, width, background):
  min_part = max(12, height * width // 8)
  for _ in range(60):
    mode = random.choice(["hbands", "vbands", "rects", "rects", "rects"])
    bg = background if background is not None else random.randint(0, 1)
    rects = []
    if mode in ("hbands", "vbands"):
      n = height if mode == "hbands" else width
      segs, rem = [], n
      while rem > 0:
        t = rem if rem <= 5 else random.randint(2, min(7, rem - 2))
        segs.append(t)
        rem -= t
      if len(segs) < 2:
        continue
      pos, col = 0, bg
      for t in segs:
        if col != bg:
          if mode == "hbands":
            rects.append((pos, 0, pos + t - 1, width - 1, col))
          else:
            rects.append((0, pos, height - 1, pos + t - 1, col))
        pos += t
        col = 1 - col
    else:
      for i in range(random.randint(1, 3)):
        h = random.randint(4, height - 3)
        w = random.randint(4, width - 3)
        p = random.random()
        r0 = 0 if p < 0.25 else (height - h if p < 0.5 else random.randint(0, height - h))
        p = random.random()
        c0 = 0 if p < 0.25 else (width - w if p < 0.5 else random.randint(0, width - w))
        col = 1 - bg if i == 0 else random.randint(0, 1)
        rects.append((r0, c0, r0 + h - 1, c0 + w - 1, col))
    base = _base(width, height, bg, rects)
    if not _thick(base):
      continue
    ones = sum(sum(row) for row in base)
    if ones < min_part or height * width - ones < min_part:
      continue
    return bg, rects, base
  return None


def _two_band_layout(height, width, background):
  """Always-thick two-band layout with random orientation, split and colours."""
  bg = background if background is not None else random.randint(0, 1)
  if random.random() < 0.5:
    k = random.randint(4, height - 4)
    if random.random() < 0.5:
      rect = (0, 0, k - 1, width - 1, 1 - bg)
    else:
      rect = (k, 0, height - 1, width - 1, 1 - bg)
  else:
    k = random.randint(4, width - 4)
    if random.random() < 0.5:
      rect = (0, 0, height - 1, k - 1, 1 - bg)
    else:
      rect = (0, k, height - 1, width - 1, 1 - bg)
  rects = [rect]
  return bg, rects, _base(width, height, bg, rects)


def _inb(r, c, height, width):
  return 0 <= r < height and 0 <= c < width


def _hole_ok(base, height, width, cells, holes, hole_set):
  for r, c in cells:
    if not _inb(r, c, height, width) or base[r][c] != 1:
      return False
  for r, c in cells:
    for r2, c2 in holes:
      if max(abs(r - r2), abs(c - c2)) < 2:
        return False
  if len(cells) > 1:
    if any(base[r][c] != 1 for r, c in _ring(cells, height, width)):
      return False
  else:
    r, c = cells[0]
    zeros = sum(1 for dr, dc in _CARD
                if _inb(r + dr, c + dc, height, width) and base[r + dr][c + dc] == 0)
    if zeros > 1:
      return False
  # Local check: every 1-cell next to the new hole keeps two 1-neighbours.
  trial = hole_set | set(cells)
  for r, c in cells:
    for dr, dc in _CARD:
      rr, cc = r + dr, c + dc
      if not _inb(rr, cc, height, width) or base[rr][cc] != 1 or (rr, cc) in trial:
        continue
      n = 0
      for er, ec in _CARD:
        r3, c3 = rr + er, cc + ec
        if _inb(r3, c3, height, width) and base[r3][c3] == 1 and (r3, c3) not in trial:
          n += 1
      if n < 2:
        return False
  return True


def _place_bridge(base, height, width):
  """Three arms make the centre peelable; the original holes define its ring."""
  centres = [(r, c) for r in range(2, height - 2)
             for c in range(2, width - 2)
             if all(base[y][x] == 1 for y in range(r - 2, r + 3)
                    for x in range(c - 2, c + 3))]
  random.shuffle(centres)
  if not centres:
    return None
  r, c = centres[0]
  omitted = random.choice(_CARD)
  holes = [(r + dr, c + dc) for dr, dc in _CARD if (dr, dc) != omitted]
  # Keep later holes away from the whole patch, including the surviving arm.
  protected = {(y, x) for y in range(r - 2, r + 3)
               for x in range(c - 2, c + 3)}
  return holes, protected


def _place_holes(base, height, width, target, bridge=False):
  ones = [(r, c) for r in range(height) for c in range(width) if base[r][c] == 1]
  random.shuffle(ones)
  holes, hole_set, count = [], set(), 0
  protected = set()
  if bridge:
    placed = _place_bridge(base, height, width)
    if placed is None:
      return [], 0
    holes, protected = placed
    hole_set = set(holes)
    count = 1
  for ar, ac in ones:
    if count >= target:
      break
    for shape in (random.choice(_SHAPES), _SINGLE):
      cells = [(ar + dr, ac + dc) for dr, dc in shape]
      if set(cells) & protected:
        continue
      if _hole_ok(base, height, width, cells, holes, hole_set):
        holes.extend(cells)
        hole_set.update(cells)
        count += 1
        break
  return holes, count


def _place_specks(base, height, width, target, holes=(), attached=None):
  zeros = [(r, c) for r in range(height) for c in range(width) if base[r][c] == 0]
  random.shuffle(zeros)
  specks = []
  bumps, floating = [], []
  for r, c in zeros:
    if any(max(abs(r - y), abs(c - x)) < 2 for y, x in holes):
      continue
    neighbours = sum(base[r + dr][c + dc] == 1 for dr, dc in _CARD
                     if _inb(r + dr, c + dc, height, width))
    if neighbours == 1 and 0 < r < height - 1 and 0 < c < width - 1:
      bumps.append((r, c))
    elif all(base[rr][cc] == 0
             for rr in range(max(0, r - 1), min(height, r + 2))
             for cc in range(max(0, c - 1), min(width, c + 2))):
      floating.append((r, c))
  bump_target = random.randint(0, min(2, target)) if attached is None else attached
  for candidates, quota in ((bumps, bump_target), (floating, target - bump_target)):
    placed = 0
    for r, c in candidates:
      if placed == quota:
        break
      if any(max(abs(r - r2), abs(c - c2)) < 2 for r2, c2 in specks):
        continue
      specks.append((r, c))
      placed += 1
    if attached is not None and placed != quota:
      return []
  return specks


def _random_scene(height, width, background, num_holes, num_specks, bridge_holes,
                  num_attached_specks):
  bridge = random.random() < 0.4 if bridge_holes is None else bridge_holes
  for _ in range(100):
    h = height if height is not None else random.randint(10, 28)
    w = width if width is not None else random.randint(10, 28)
    lay = _random_layout(h, w, background)
    if lay is None:
      continue
    bg, rects, base = lay
    target = num_holes if num_holes is not None else random.randint(2, 6)
    holes, n = _place_holes(base, h, w, target, bridge)
    if n < 2 and num_holes is None or num_holes is not None and n != num_holes:
      continue
    target = num_specks if num_specks is not None else random.randint(1, 5)
    specks = _place_specks(base, h, w, target, holes, num_attached_specks)
    if not specks or num_specks is not None and len(specks) != num_specks:
      continue
    return w, h, bg, rects, holes, specks
  if (num_holes is not None or num_specks is not None or bridge_holes is True
      or num_attached_specks is not None):
    raise ValueError("requested defect counts/bridge did not fit a sampled layout")
  # Randomised constructive fallback: a two-band layout whose bands are at
  # least 4 thick always admits at least one hole and one speck under the
  # exhaustive placement scan above.
  h = height if height is not None else random.randint(10, 28)
  w = width if width is not None else random.randint(10, 28)
  bg, rects, base = _two_band_layout(h, w, background)
  holes, n = _place_holes(base, h, w, random.randint(1, 4))
  specks = _place_specks(base, h, w, random.randint(1, 4), holes, 0)
  if n < 1 or not specks:
    raise RuntimeError("two-band fallback failed to place defects")
  return w, h, bg, rects, holes, specks


def _check_explicit(width, height, background, rects, holes, specks):
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("width and height must be in 1..30")
  if background not in (0, 1):
    raise ValueError("background must be 0 or 1")
  for r0, c0, r1, c1, col in rects:
    if not (0 <= r0 <= r1 < height and 0 <= c0 <= c1 < width) or col not in (0, 1):
      raise ValueError("rectangle out of bounds or bad colour")
  for r, c in list(holes) + list(specks):
    if not _inb(r, c, height, width):
      raise ValueError("hole/speck cell out of bounds")
  base = _base(width, height, background, rects)
  if any(base[r][c] != 1 for r, c in holes):
    raise ValueError("holes must start in base-1 territory")
  if any(base[r][c] != 0 for r, c in specks):
    raise ValueError("specks must start in base-0 territory")


def generate(width=None, height=None, background=None, rects=None,
             holes=None, specks=None, num_holes=None, num_specks=None,
             bridge_holes=None, num_attached_specks=None):
  """Generate one input/output pair.

  Args:
    width: grid width (number of columns). Random mode: 8..30, default
      random 10..28. Required in explicit mode.
    height: grid height (number of rows). Random mode: 8..30, default
      random 10..28. Required in explicit mode.
    background: base colour (0 or 1) that fills the grid before the
      rectangles are painted. Honoured in random mode when given.
    rects: list of (r0, c0, r1, c1, colour) inclusive rectangles painted in
      order onto the background, forming the solid 0/1 regions. If given,
      the scene is fully explicit (width, height, background are required).
    holes: list of (row, col) cells that are 0-holes inside 1 territory
      (explicit mode only).
    specks: list of (row, col) cells that are stray 1-specks in 0 territory
      (explicit mode only).
    num_holes: exact number of latent hole clusters, 1..20, random mode only.
      A three-arm bridge counts as one cluster.
    num_specks: exact number of isolated 1-specks, 1..30, random mode only.
    bridge_holes: True requires one bridge cluster, False excludes it,
      None samples it with probability 0.4. Random mode only.
    num_attached_specks: exact number of interior bumps among num_specks.
      Requires num_specks. None samples 0..2 bumps when space permits.

  If rects is None, a fresh random scene is built from latent parameters.
  """
  for name, value in (("width", width), ("height", height),
                      ("num_holes", num_holes), ("num_specks", num_specks),
                      ("num_attached_specks", num_attached_specks)):
    if value is not None and type(value) is not int:
      raise ValueError(name + " must be an integer")
  if bridge_holes is not None and type(bridge_holes) is not bool:
    raise ValueError("bridge_holes must be True, False or None")
  if num_holes is not None and not 1 <= num_holes <= 20:
    raise ValueError("num_holes must be in 1..20")
  if num_specks is not None and not 1 <= num_specks <= 30:
    raise ValueError("num_specks must be in 1..30")
  if num_attached_specks is not None and (
      num_specks is None or not 0 <= num_attached_specks <= num_specks):
    raise ValueError("num_attached_specks must be in 0..num_specks")
  if rects is None:
    if holes is not None or specks is not None:
      raise ValueError("holes/specks require explicit rects, width, height, background")
    for v in (width, height):
      if v is not None and not 8 <= v <= 30:
        raise ValueError("random-mode width/height must be in 8..30")
    if background not in (None, 0, 1):
      raise ValueError("background must be 0 or 1")
    width, height, background, rects, holes, specks = _random_scene(
        height, width, background, num_holes, num_specks, bridge_holes,
        num_attached_specks)
  else:
    if (num_holes is not None or num_specks is not None or bridge_holes is not None
        or num_attached_specks is not None):
      raise ValueError("defect-count controls require random mode")
    if width is None or height is None or background is None:
      raise ValueError("explicit rects require width, height and background")
    holes = holes or []
    specks = specks or []
    _check_explicit(width, height, background, rects, holes, specks)
  return _render(width, height, background, rects, holes, specks)


def validate():
  """Reconstruct the canonical fixtures through explicit latent arguments."""
  train = [
      generate(width=17, height=19, background=0,
               rects=[(0, 0, 4, 16, 1), (9, 0, 13, 16, 1), (17, 0, 18, 16, 1)],
               holes=[(0, 3), (2, 16), (4, 8), (10, 6), (11, 5), (11, 6), (17, 14)],
               specks=[(7, 13), (14, 8), (15, 3)]),
      generate(width=16, height=16, background=1,
               rects=[(3, 2, 10, 12, 0), (5, 6, 9, 11, 1)],
               holes=[(0, 15), (6, 14), (7, 8), (8, 15), (13, 6), (13, 7)],
               specks=[(5, 2), (8, 4)]),
      generate(width=16, height=16, background=0,
               rects=[(4, 4, 12, 13, 1)],
               holes=[(6, 10), (7, 11), (12, 7)],
               specks=[(3, 6), (4, 15), (14, 1)]),
  ]
  test = [
      generate(width=16, height=16, background=0,
               rects=[(0, 0, 15, 4, 1), (3, 5, 11, 13, 1)],
               holes=[(3, 11), (5, 5), (6, 4), (7, 3), (8, 11), (9, 11), (11, 6)],
               specks=[(4, 15), (6, 15), (9, 14), (14, 12), (15, 15)]),
      generate(width=19, height=18, background=1,
               rects=[(0, 0, 17, 1, 0), (13, 0, 17, 10, 0), (3, 9, 17, 10, 0),
                      (3, 9, 5, 18, 0)],
               holes=[(2, 4), (2, 16), (4, 6), (8, 5), (9, 4), (9, 6), (9, 14),
                      (10, 14), (15, 18), (16, 12), (17, 13)],
               specks=[(1, 1), (4, 13), (6, 0), (13, 3), (15, 8)]),
  ]
  return {"train": train, "test": test}
