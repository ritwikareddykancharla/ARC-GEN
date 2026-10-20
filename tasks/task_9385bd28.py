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

"""ARC task 9385bd28: legend-driven rectangle filling.

Rule: a two-column legend block of (key | value) rows sits on a uniform
background. Each key colour appears in the scene in one of two forms:
  * two L-shaped corner pieces (3 cells of a 2x2) at opposite corners of a
    rectangle;
  * a solid 2x2 block.
Legend rows are applied top to bottom, and each cell can be claimed only once.
  * Value 0 on a non-zero background: every piece of the key colour is erased
    to background first, and no rectangle is claimed.
  * Value equal to the background: the rectangle's free background cells are
    reserved. They stay background, and later rows cannot paint them.
  * Any other value: the rectangle's still-free background cells are filled
    with the value. A solid 2x2 block has no free cells, so the block itself
    is recoloured instead.
Rectangles come from the input piece positions. Keys with no pieces are
ignored. Piece colours that are not keys stay unchanged.

Scope:
  * Random scenes use a 10..24 x 10..24 grid by default. An explicit width or
    height for a random scene may be 10..30. Sizes above 19 are a synthetic
    extension of the fixture range (10..19).
  * The background is random and may be non-zero. Object and key colours are
    drawn from 1..9 minus the background.
  * The legend has 2..5 rows, capped by grid size. It is usually placed near
    the left or right edge; mid-grid placement is a synthetic extension.
  * Every random scene contains at least one load-bearing decision: legend
    order, background reservation, or erasing before claims. By default,
    25% of calls that do not fix background 0 require an erase-first
    counterexample; this decision is retained across placement retries.
    Other scenes usually also differ from a randomly
    chosen "sort rows by rectangle area" order, so area order cannot replace
    legend order as an explanation. Later pairs are biased to intersect
    earlier key rectangles.
  * Row kinds (fill, reserve, erase) and corner orientations are sampled
    independently per row and per pair. A given scene may therefore use only
    one orientation or only fill rows; the mix is distributional.
  * Different objects may touch diagonally (as in the fixtures), never
    orthogonally. Clusters that could be mistaken for the legend (a
    multi-colour 8-connected cluster with a 2-column bounding box) are
    rejected.
  * Erase rows in random scenes never have a rectangle that intersects the
    rectangle of a later claiming row, because no fixture shows whether an
    erase row claims cells.
  * A scene may contain one solid block (always a fill row), one absent key,
    and one distractor pair whose colour is not in the legend. Distractors
    may lie inside key rectangles and stay unchanged, a synthetic extension.
Explicit scenes (legend, legend_pos, objects) are validated, then rendered
exactly. They reconstruct the canonical fixtures. Explicit mode rejects ambiguous background/legend detection. It also renders
unverified cases (pair with no free cell is recoloured; reserve or erase row
on a block) with the same semantics as the verified rule.
"""

import collections
import random

import common


def _is_int(x):
  return type(x) is int


def _pair_pieces(r0, c0, r1, c1, orient):
  """Return the two L pieces of a corner pair spanning rows r0..r1, cols c0..c1."""
  if orient == "main":
    a = [(r0, c0), (r0, c0 + 1), (r0 + 1, c0)]
    b = [(r1 - 1, c1), (r1, c1 - 1), (r1, c1)]
  else:
    a = [(r0, c1 - 1), (r0, c1), (r0 + 1, c1)]
    b = [(r1 - 1, c0), (r1, c0), (r1, c0 + 1)]
  return a, b


def _cells(obj):
  if obj[0] == "pair":
    a, b = _pair_pieces(obj[2], obj[3], obj[4], obj[5], obj[6])
    return a + b
  r, c = obj[2], obj[3]
  return [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]


def _rect(obj):
  if obj[0] == "pair":
    return obj[2], obj[3], obj[4], obj[5]
  return obj[2], obj[3], obj[2] + 1, obj[3] + 1


def _rects_overlap(a, b):
  return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _near(cells_a, cells_b):
  """True if any cell of a overlaps or is 8-adjacent to a cell of b."""
  sb = set(cells_b)
  for r, c in cells_a:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        if (r + dr, c + dc) in sb:
          return True
  return False


def _touch4(cells_a, cells_b):
  """True if any cell of a overlaps or is 4-adjacent to a cell of b."""
  sb = set(cells_b)
  for r, c in cells_a:
    for dr, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
      if (r + dr, c + dc) in sb:
        return True
  return False


def _legend_cells(legend_pos, n):
  lr, lc = legend_pos
  return [(lr + i, lc + j) for i in range(n) for j in range(2)]


def _draw(width, height, bg, legend, legend_pos, objects):
  """Draw the input grid from latent parameters."""
  grid = common.grid(width, height, bg)
  lr, lc = legend_pos
  for i, (k, v) in enumerate(legend):
    grid[lr + i][lc] = k
    grid[lr + i][lc + 1] = v
  for obj in objects:
    for r, c in _cells(obj):
      grid[r][c] = obj[1]
  return grid


def _apply(grid, bg, rows, legend_pos, n_legend, objects, erase_first=True):
  """Apply legend rows (in the given order) to the latent objects.

  Returns (output, pair_recolour). pair_recolour is True if a corner pair had
  no free cell left, which is an unverified case.
  """
  out = [row[:] for row in grid]
  inleg = set(_legend_cells(legend_pos, n_legend))
  by_colour = {obj[1]: obj for obj in objects}
  for k, v in rows:
    if erase_first and k != bg and v == 0 and bg != 0 and k in by_colour:
      for r, c in _cells(by_colour[k]):
        out[r][c] = bg
  painted = set()
  pair_recolour = False
  for k, v in rows:
    if v == 0 and bg != 0:
      if not erase_first and k in by_colour:
        for r, c in _cells(by_colour[k]):
          out[r][c] = bg
      continue
    if k == bg:
      continue
    obj = by_colour.get(k)
    if obj is None:
      continue
    r0, c0, r1, c1 = _rect(obj)
    free = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
            if out[r][c] == bg and (r, c) not in painted
            and (r, c) not in inleg]
    if v == bg:
      painted.update(free)
      continue
    if free:
      for r, c in free:
        out[r][c] = v
      painted.update(free)
    else:
      if obj[0] == "pair":
        pair_recolour = True
      for r, c in _cells(obj):
        out[r][c] = v
        painted.add((r, c))
  return out, pair_recolour


def _is_hard(grid, out, bg, legend, legend_pos, objects):
  """True if row order, reservation or erase-first actually affects output."""
  n = len(legend)
  rev, _ = _apply(grid, bg, legend[::-1], legend_pos, n, objects)
  if rev != out:
    return True
  nores = [(k, v) for k, v in legend if v != bg]
  if len(nores) != n:
    alt, _ = _apply(grid, bg, nores, legend_pos, n, objects)
    if alt != out:
      return True
  inline, _ = _apply(grid, bg, legend, legend_pos, n, objects,
                     erase_first=False)
  return inline != out


def _matches_area_order(grid, out, bg, legend, legend_pos, objects, desc):
  """True if sorting rows by rectangle area reproduces the output."""
  area = {}
  for obj in objects:
    r0, c0, r1, c1 = _rect(obj)
    area[obj[1]] = (r1 - r0 + 1) * (c1 - c0 + 1)
  rows = sorted(legend, key=lambda kv: area.get(kv[0], 0), reverse=desc)
  alt, _ = _apply(grid, bg, rows, legend_pos, len(legend), objects)
  return alt == out


def _erase_overlaps_later(legend, bg, objects):
  """True if an erase row's rectangle meets a later claiming row's rectangle."""
  if bg == 0:
    return False
  rects = {obj[1]: _rect(obj) for obj in objects}
  for i, (k, v) in enumerate(legend):
    if v != 0 or k not in rects:
      continue
    for k2, v2 in legend[i + 1:]:
      if v2 == 0 or k2 not in rects:
        continue
      if _rects_overlap(rects[k], rects[k2]):
        return True
  return False


def _legend_confusable(grid, bg, legend_pos, n):
  """True if a non-legend 8-connected cluster could pass as a legend."""
  height, width = len(grid), len(grid[0])
  leg = set(_legend_cells(legend_pos, n))
  seen = set(leg)
  for r in range(height):
    for c in range(width):
      if grid[r][c] == bg or (r, c) in seen:
        continue
      seen.add((r, c))
      stack = [(r, c)]
      comp = []
      while stack:
        y, x = stack.pop()
        comp.append((y, x))
        for dy in (-1, 0, 1):
          for dx in (-1, 0, 1):
            ny, nx = y + dy, x + dx
            if 0 <= ny < height and 0 <= nx < width \
                and (ny, nx) not in seen and grid[ny][nx] != bg:
              seen.add((ny, nx))
              stack.append((ny, nx))
      colours = set(grid[y][x] for y, x in comp)
      xs = [x for _, x in comp]
      if len(colours) >= 2 and max(xs) - min(xs) == 1:
        return True
  return False


def _bg_dominant(grid, bg):
  counts = collections.Counter(c for row in grid for c in row)
  top = counts[bg]
  return all(n < top for c, n in counts.items() if c != bg)


def _check_detectable(grid, bg, legend_pos, n):
  """Require the background and full legend to be identifiable from input."""
  if not _bg_dominant(grid, bg):
    raise ValueError("background must be the strict plurality colour")
  h, w = len(grid), len(grid[0])
  remaining = {(r, c) for r in range(h) for c in range(w)
               if grid[r][c] != bg}
  candidates = []
  while remaining:
    stack = [remaining.pop()]
    component = set(stack)
    for r, c in stack:
      for p in ((r+1, c), (r-1, c), (r, c+1), (r, c-1)):
        if p in remaining:
          remaining.remove(p)
          component.add(p)
          stack.append(p)
    rows, cols = zip(*component)
    colours = {grid[r][c] for r, c in component}
    if max(cols)-min(cols) == 1 and len(colours) > 1:
      candidates.append((len(colours),
                         (min(rows), min(cols), max(rows), max(cols))))
  candidates.sort(reverse=True)
  lr, lc = legend_pos
  expected = (lr, lc, lr+n-1, lc+1)
  if (not candidates or candidates[0][1] != expected or
      (len(candidates) > 1 and candidates[0][0] == candidates[1][0])):
    raise ValueError("legend is not uniquely identifiable from the input")


def _check_scene(width, height, bg, legend, legend_pos, objects):
  """Reject malformed explicit scenes instead of rendering them silently."""
  if not (_is_int(width) and _is_int(height)):
    raise ValueError("width and height must be integers")
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("width and height must be in 1..30")
  if not _is_int(bg) or not 0 <= bg <= 9:
    raise ValueError("bg must be an integer colour 0..9")
  if len(legend_pos) != 2 or not all(_is_int(x) for x in legend_pos):
    raise ValueError("legend_pos must be (row, col) integers")
  lr, lc = legend_pos
  if not legend or lr < 0 or lc < 0 or lr + len(legend) > height \
      or lc + 2 > width:
    raise ValueError("legend does not fit in the grid")
  keys = set()
  for row in legend:
    if len(row) != 2:
      raise ValueError("legend rows are (key, value)")
    k, v = row
    if not (_is_int(k) and _is_int(v)):
      raise ValueError("legend colours must be integers")
    if not (0 <= k <= 9 and 0 <= v <= 9):
      raise ValueError("legend colours must be 0..9")
    if k == bg:
      raise ValueError("legend keys must differ from the background")
    if k in keys:
      raise ValueError("legend keys must be distinct")
    keys.add(k)
  leg = _legend_cells(legend_pos, len(legend))
  seen = set()
  placed = []
  for obj in objects:
    if not obj or obj[0] not in ("pair", "block"):
      raise ValueError("object kind must be 'pair' or 'block'")
    if obj[0] == "pair":
      if len(obj) != 7 or obj[6] not in ("main", "anti"):
        raise ValueError("pair needs orient 'main' or 'anti'")
      if not all(_is_int(x) for x in obj[1:6]):
        raise ValueError("pair fields must be integers")
      if obj[4] < obj[2] + 1 or obj[5] < obj[3] + 1:
        raise ValueError("pair rectangle is degenerate or inverted")
      a, b = _pair_pieces(obj[2], obj[3], obj[4], obj[5], obj[6])
      if _touch4(a, b):
        raise ValueError("the two corner pieces overlap or touch")
    else:
      if len(obj) != 4:
        raise ValueError("block is ('block', colour, r, c)")
      if not all(_is_int(x) for x in obj[1:4]):
        raise ValueError("block fields must be integers")
    if not 0 <= obj[1] <= 9 or obj[1] == bg:
      raise ValueError("object colour must be 0..9 and differ from bg")
    if obj[1] in seen:
      raise ValueError("each object colour may appear only once")
    seen.add(obj[1])
    cells = _cells(obj)
    for r, c in cells:
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError("object outside the grid")
    if _near(cells, leg):
      raise ValueError("object overlaps or touches the legend")
    for other in placed:
      if _touch4(cells, other):
        raise ValueError("objects overlap or are 4-adjacent")
    placed.append(cells)


def _place(colour, kind, width, height, zone, occupied, targets):
  """Place one object; pairs are biased to intersect a target rectangle."""
  for _ in range(80):
    if kind == "block":
      obj = ("block", colour, random.randint(0, height - 2),
             random.randint(0, width - 2))
    else:
      if random.random() < 0.15:
        h = random.randint(2, height)
      else:
        h = random.randint(2, min(height, 10))
      if random.random() < 0.15:
        w = random.randint(2, width)
      else:
        w = random.randint(2, min(width, 10))
      if targets and random.random() < 0.7:
        tr0, tc0, tr1, tc1 = random.choice(targets)
        rlo, rhi = max(0, tr0 - h + 1), min(height - h, tr1)
        clo, chi = max(0, tc0 - w + 1), min(width - w, tc1)
        if rlo > rhi or clo > chi:
          continue
        r0 = random.randint(rlo, rhi)
        c0 = random.randint(clo, chi)
      else:
        r0 = random.randint(0, height - h)
        c0 = random.randint(0, width - w)
      obj = ("pair", colour, r0, c0, r0 + h - 1, c0 + w - 1,
             random.choice(["main", "anti"]))
      a, b = _pair_pieces(obj[2], obj[3], obj[4], obj[5], obj[6])
      if _near(a, b):
        continue
    r0, c0, r1, c1 = _rect(obj)
    if not (r1 < zone[0] or r0 > zone[2] or c1 < zone[1] or c0 > zone[3]):
      continue
    # Different objects may touch diagonally (as in the fixtures), never
    # orthogonally.
    if _touch4(_cells(obj), occupied):
      continue
    return obj
  return None


def _sample(width, height, bg, require_erase_first):
  if require_erase_first is None:
    require_erase_first = bg != 0 and random.random() < 0.25
  for attempt in range(800):
    b = bg if bg is not None else (
        random.randint(1, 9) if require_erase_first else
        (0 if random.random() < 0.5 else random.randint(1, 9)))
    hgt = height if height is not None else random.randint(10, 24)
    wid = width if width is not None else random.randint(10, 24)
    palette = [c for c in range(1, 10) if c != b]
    nmax = max(2, min(5, (min(wid, hgt) - 4) // 2))
    n = random.randint(2, nmax)
    keys = random.sample(palette, n)
    kinds = ["pair"] * n
    idx = list(range(n))
    random.shuffle(idx)
    if random.random() < 0.3:
      kinds[idx[0]] = "block"
    if random.random() < 0.2:
      kinds[idx[1]] = "absent"
    if require_erase_first:
      kinds[0] = kinds[-1] = "pair"
    legend = []
    for k, kind in zip(keys, kinds):
      if kind == "block":
        v = random.choice([c for c in palette if c != k])
      elif kind == "absent":
        v = random.choice(palette + [b])
      else:
        roll = random.random()
        if b != 0 and roll < 0.15:
          v = 0
        elif roll < 0.35:
          v = b
        else:
          v = random.choice(palette)
      legend.append((k, v))
    if require_erase_first:
      legend[0] = (keys[0], random.choice(palette))
      legend[-1] = (keys[-1], 0)
    fills = [1 for (k, v), kind in zip(legend, kinds)
             if kind != "absent" and v != b and not (v == 0 and b != 0)]
    if not fills:
      continue
    distract = [c for c in palette if c not in keys]
    jobs = [(k, kind, True) for k, kind in zip(keys, kinds)
            if kind != "absent"]
    if distract and random.random() < 0.35:
      jobs.append((random.choice(distract), "pair", False))
    random.shuffle(jobs)
    if random.random() < 0.7:
      lc = random.choice([0, 1, wid - 2, wid - 3])
    else:
      lc = random.randint(0, wid - 2)
    lr = random.randint(0, hgt - n)
    zone = (lr - 1, lc - 1, lr + n, lc + 2)
    occupied = set(_legend_cells((lr, lc), n))
    objects = []
    targets = []
    ok = True
    for colour, kind, is_key in jobs:
      obj = _place(colour, kind, wid, hgt, zone, occupied, targets)
      if obj is None:
        ok = False
        break
      objects.append(obj)
      occupied.update(_cells(obj))
      if is_key and kind == "pair":
        targets.append(_rect(obj))
    if not ok:
      continue
    if _erase_overlaps_later(legend, b, objects):
      continue
    grid = _draw(wid, hgt, b, legend, (lr, lc), objects)
    out, bad = _apply(grid, b, legend, (lr, lc), n, objects)
    if bad or grid == out:
      continue
    if not _bg_dominant(grid, b):
      continue
    if _legend_confusable(grid, b, (lr, lc), n):
      continue
    if not _is_hard(grid, out, b, legend, (lr, lc), objects):
      continue
    if require_erase_first:
      inline, _ = _apply(grid, b, legend, (lr, lc), n, objects,
                         erase_first=False)
      if inline == out:
        continue
    desc = random.random() < 0.5
    if not require_erase_first and attempt < 400 and _matches_area_order(grid, out, b, legend, (lr, lc),
                                             objects, desc):
      continue
    return grid, out
  raise ValueError("could not build a valid scene for the requested size")


def generate(width=None, height=None, bg=None, legend=None, legend_pos=None,
             objects=None, require_erase_first=None):
  """Build one input/output pair.

  Args:
    width: grid width (int). Random 10..24 when None. An explicit value must
      be in 10..30 for random scenes, or 1..30 for explicit scenes.
    height: grid height (int). Random 10..24 when None. Same ranges as width.
    bg: background colour 0..9 (int). Unconstrained proposals choose 0 with
      probability 1/2 except erase-first scenes, which require non-zero bg.
    require_erase_first: optional bool, random mode only. True requires a
      scene where erasing at each row instead of before all rows is wrong.
      False disables this requirement (not erasure itself). None schedules
      this requirement on 25% of calls whose bg is not fixed to zero.
    legend: list of (key, value) rows, applied top to bottom. Keys must be
      distinct and differ from bg.
    legend_pos: (row, col) of the legend's top-left cell.
    objects: list of objects in either of two forms:
      ("pair", colour, r0, c0, r1, c1, orient), where orient is "main"
        (top-left and bottom-right corners) or "anti" (top-right and
        bottom-left corners);
      ("block", colour, r, c) for a solid 2x2 block.
      Explicit mode needs legend, legend_pos and objects together with width,
      height and bg. Supplying only part of that set raises ValueError rather
      than being silently ignored. Booleans and non-integers are rejected.
  """
  if require_erase_first is not None and type(require_erase_first) is not bool:
    raise ValueError("require_erase_first must be a bool or None")
  if require_erase_first and bg == 0:
    raise ValueError("erase-first decision requires a non-zero background")
  explicit = (legend, legend_pos, objects)
  if any(x is not None for x in explicit):
    if require_erase_first is not None:
      raise ValueError("require_erase_first applies only to random scenes")
    if any(x is None for x in explicit + (width, height, bg)):
      raise ValueError("explicit scenes need width, height, bg, legend, "
                       "legend_pos and objects together")
    if not isinstance(legend, (list, tuple)) or not all(
        isinstance(row, (list, tuple)) for row in legend):
      raise ValueError("legend must be a list of (key, value) rows")
    if not isinstance(objects, (list, tuple)) or not all(
        isinstance(obj, (list, tuple)) for obj in objects):
      raise ValueError("objects must be a list of tuples")
    if not isinstance(legend_pos, (list, tuple)):
      raise ValueError("legend_pos must be (row, col)")
    legend = [tuple(row) for row in legend]
    objects = [tuple(obj) for obj in objects]
    legend_pos = tuple(legend_pos)
    _check_scene(width, height, bg, legend, legend_pos, objects)
    grid = _draw(width, height, bg, legend, legend_pos, objects)
    _check_detectable(grid, bg, legend_pos, len(legend))
    out, _ = _apply(grid, bg, legend, legend_pos, len(legend), objects)
  else:
    for name, val in (("width", width), ("height", height)):
      if val is not None and (not _is_int(val) or not 10 <= val <= 30):
        raise ValueError(name + " must be an integer in 10..30 for random "
                         "scenes")
    if bg is not None and (not _is_int(bg) or not 0 <= bg <= 9):
      raise ValueError("bg must be an integer colour 0..9")
    grid, out = _sample(width, height, bg, require_erase_first)
  return {"input": grid, "output": out}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=10, height=10, bg=0, legend=[(1, 0), (2, 3)],
               legend_pos=(8, 0),
               objects=[("pair", 2, 0, 3, 7, 7, "main"),
                        ("pair", 1, 2, 4, 5, 6, "main")]),
      generate(width=10, height=10, bg=0, legend=[(1, 3), (4, 5)],
               legend_pos=(7, 1),
               objects=[("pair", 4, 0, 4, 8, 9, "anti"),
                        ("pair", 1, 2, 5, 7, 7, "main")]),
      generate(width=17, height=12, bg=3,
               legend=[(1, 6), (2, 9), (4, 0), (8, 9)], legend_pos=(8, 2),
               objects=[("pair", 5, 0, 2, 2, 7, "main"),
                        ("pair", 2, 3, 4, 6, 13, "main"),
                        ("pair", 4, 4, 6, 8, 9, "main"),
                        ("pair", 1, 5, 7, 11, 10, "anti")]),
      generate(width=18, height=15, bg=0,
               legend=[(3, 3), (6, 7), (4, 4), (7, 6)], legend_pos=(11, 0),
               objects=[("pair", 3, 1, 5, 5, 8, "main"),
                        ("pair", 4, 6, 12, 8, 17, "main"),
                        ("pair", 6, 8, 6, 12, 10, "main"),
                        ("block", 7, 11, 14)]),
  ]
  test = [
      generate(width=13, height=19, bg=9,
               legend=[(2, 2), (5, 9), (3, 9), (1, 4), (4, 6)],
               legend_pos=(14, 1),
               objects=[("pair", 4, 0, 4, 18, 5, "main"),
                        ("pair", 2, 0, 7, 18, 8, "main"),
                        ("pair", 1, 3, 1, 4, 12, "main"),
                        ("pair", 5, 6, 4, 7, 12, "main"),
                        ("pair", 3, 9, 4, 10, 12, "main")]),
      generate(width=19, height=13, bg=1,
               legend=[(3, 4), (6, 8), (7, 1), (8, 2), (2, 4)],
               legend_pos=(7, 2),
               objects=[("block", 8, 1, 1),
                        ("pair", 7, 1, 6, 11, 8, "main"),
                        ("pair", 6, 4, 6, 7, 13, "main"),
                        ("pair", 3, 5, 8, 8, 10, "main"),
                        ("pair", 2, 6, 13, 10, 16, "anti")]),
  ]
  return {"train": train, "test": test}
