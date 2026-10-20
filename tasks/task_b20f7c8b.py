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

"""ARC-GEN style generator for task b20f7c8b.

Rule:
  A 6-column legend strip sits on the left or right edge. Its background is
  8, and it holds several 3x3 glyphs, each in its own colour. The rest of the
  grid is a background-0 canvas of 5x5 boxes. Every box swaps kind:
  * A pattern box (a 2-frame around a 3x3 pattern of 1s) whose pattern equals
    a legend glyph up to rotation or reflection becomes a solid 5x5 box in
    that glyph's colour.
  * A solid box of a legend colour becomes a 2-frame. That colour's glyph is
    drawn inside in 1s, exactly as it appears in the legend (unrotated).
  The legend does not change.

Scope (random mode):
  * Sampled: the legend side, the glyph count, the glyph shapes, colours,
    legend order, vertical spacing and in-strip offsets.
  * Glyph pool: every 3x3 mask with a full 3x3 bounding box, 4..7 cells and
    8-connected, as all fixture glyphs are. 4-disconnected glyphs such as
    110/101/110 are included. Glyphs are pairwise distinct up to
    rotation/reflection.
  * Sampled box geometry: the box-grid shape, gaps of at least 1 cell, and
    margins. Boxes never touch each other, the grid edge or the legend.
  * Sampled assignment: the colour-to-box assignment, the pattern/solid mix
    (at least one pattern box) and the pattern orientations.
  * Enforced in every random scene:
    - At least one pattern box is drawn in a non-identity orientation.
    - If there are 2 or more glyphs, that box's glyph shares its cell count
      with another glyph, so cell counting cannot identify it.
    - If a solid box exists, at least one solid box's glyph is not fully
      rotation/reflection symmetric, so the "draw unrotated" choice matters.
  The native size is 18x22, with a 2x2 box layout and as many glyphs as
  boxes.
  Synthetic extensions of the same rule:
  * heights 12..30 and canvas widths 12..24 (total width 18..30);
  * box layouts from 1x1 up to 8 boxes;
  * unused distractor glyphs, up to two more than the box count. Defaults
    use at least two glyphs, including for a single-box layout. An explicit
    num_glyphs=1 request is a broader single-choice control.
  Fixed, as in every demonstration: legend width 6, legend colour 8, frame
  colour 2, pattern colour 1, background 0. In random mode a solid input box
  never has colour 2, because it would look like an empty pattern box.
  Explicit mode still accepts one, and it accepts any full-bbox glyph.
  Colour counts are budgeted so that 0 is strictly most common and 8 is
  strictly second, which is how the legend and background are identified.
"""

import collections
import random

import common


NATIVE_H, NATIVE_W = 18, 22
LEGEND_W = 6
BOX = 5
BG, LEGEND_C, FRAME_C, PAT_C = 0, 8, 2, 1
PALETTE = [1, 2, 3, 4, 5, 6, 7, 9]
MIN_H, MAX_H = 12, 30
MIN_CW, MAX_CW = 12, 24
MIN_CELLS, MAX_CELLS = 4, 7


def _parse(shape):
  if not isinstance(shape, (list, tuple)) or len(shape) != 3:
    raise ValueError("shape must contain three rows")
  result = []
  for row in shape:
    if not isinstance(row, (str, list, tuple)) or len(row) != 3:
      raise ValueError("shape rows must contain three binary cells")
    if any(not ((type(ch) is int and ch in (0, 1)) or
                (type(ch) is str and ch in ("0", "1"))) for ch in row):
      raise ValueError("shape cells must be binary integers or characters")
    result.append(tuple(int(ch) for ch in row))
  return tuple(result)


def _unparse(m):
  return ["".join(str(v) for v in row) for row in m]


def _rot(m):
  return tuple(tuple(m[2 - c][r] for c in range(3)) for r in range(3))


def _flip(m):
  return tuple(tuple(reversed(row)) for row in m)


def _syms(m):
  res, cur = [], m
  for _ in range(4):
    res.append(cur)
    res.append(_flip(cur))
    cur = _rot(cur)
  return res


def _canon(m):
  return min(_syms(m))


def _full_bbox(m):
  return bool(any(m[0]) and any(m[2]) and any(row[0] for row in m)
              and any(row[2] for row in m))


def _is_mask(m):
  return (len(m) == 3 and all(len(row) == 3 for row in m)
          and all(v in (0, 1) for row in m for v in row))


def _connected8(m):
  cells = set((r, c) for r in range(3) for c in range(3) if m[r][c])
  if not cells:
    return False
  start = min(cells)
  seen, stack = {start}, [start]
  while stack:
    r, c = stack.pop()
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        q = (r + dr, c + dc)
        if q in cells and q not in seen:
          seen.add(q)
          stack.append(q)
  return len(seen) == len(cells)


def _build_classes():
  """All 8-connected full-bbox 3x3 glyphs (4..7 cells), grouped by D4 class."""
  groups = {}
  for bits in range(512):
    m = tuple(tuple((bits >> (3 * r + c)) & 1 for c in range(3))
              for r in range(3))
    k = sum(sum(row) for row in m)
    if k < MIN_CELLS or k > MAX_CELLS:
      continue
    if not _full_bbox(m) or not _connected8(m):
      continue
    groups.setdefault(_canon(m), set()).add(m)
  return [sorted(groups[key]) for key in sorted(groups)]


_CLASSES = _build_classes()
_CLASS_SIZE = [sum(sum(row) for row in members[0]) for members in _CLASSES]


def _check_int(name, v):
  """Rejects bools, floats and other non-integers (None is allowed)."""
  if v is not None and (isinstance(v, bool) or not isinstance(v, int)):
    raise ValueError("%s must be an integer" % name)


def _distribute(total, slots):
  parts = [0] * slots
  for _ in range(total):
    parts[random.randrange(slots)] += 1
  return parts


def _counts_ok(grid):
  """Background 0 strictly most common, legend 8 strictly second."""
  counts = collections.Counter(v for row in grid for v in row)
  c0, c8 = counts.get(BG, 0), counts.get(LEGEND_C, 0)
  return c0 > c8 and all(
      c8 > n for v, n in counts.items() if v not in (BG, LEGEND_C))


def _feasible_p(height, n, p):
  """Necessary and (with the sampler) sufficient budget for 8 > 2.

  count(8) - count(2) = 6h - 25p - (cells of non-pattern glyphs)
  - (cells of glyph 2). Every glyph has at least MIN_CELLS cells. If the
  palette is exhausted (n == 8), glyph 2 is always present, which costs at
  least MIN_CELLS more.
  """
  need = MIN_CELLS * (n - p)
  if n >= len(PALETTE):
    need += MIN_CELLS
  return 6 * height - 25 * p - 1 >= need


def _render(side, glyphs, boxes, height, width):
  """Draws the input and output grids from latent parameters."""
  for name, entries in (("glyphs", glyphs), ("boxes", boxes)):
    if (not isinstance(entries, (list, tuple)) or not entries or
        any(not isinstance(entry, (list, tuple)) or len(entry) != 4
            for entry in entries)):
      raise ValueError("%s must contain four-field entries" % name)
  if side not in ("left", "right"):
    raise ValueError("legend_side must be 'left' or 'right'")
  _check_int("height", height)
  _check_int("width", width)
  if not (3 <= height <= 30 and LEGEND_W + BOX <= width <= 30):
    raise ValueError("grid size out of range")
  lx = width - LEGEND_W if side == "right" else 0
  cx0 = 0 if side == "right" else LEGEND_W
  cx1 = cx0 + width - LEGEND_W
  grid = common.grid(width, height, BG)
  for r in range(height):
    for c in range(lx, lx + LEGEND_W):
      grid[r][c] = LEGEND_C
  shapes = {}
  for colour, top, off, shape in glyphs:
    for name, v in (("glyph colour", colour), ("glyph top", top),
                    ("glyph offset", off)):
      _check_int(name, v)
    if colour in (BG, LEGEND_C) or colour in shapes or not 0 <= colour <= 9:
      raise ValueError("glyph colours must be distinct and not 0 or 8")
    m = _parse(shape)
    if not _is_mask(m) or not _full_bbox(m):
      raise ValueError("glyph must be a 0/1 3x3 mask with full bbox")
    if off < 0 or off + 3 > LEGEND_W or top < 0 or top + 3 > height:
      raise ValueError("glyph outside legend")
    for r in range(3):
      for c in range(3):
        if m[r][c]:
          if grid[top + r][lx + off + c] != LEGEND_C:
            raise ValueError("glyphs overlap")
          grid[top + r][lx + off + c] = colour
    shapes[colour] = m
  if len(set(_canon(m) for m in shapes.values())) != len(shapes):
    raise ValueError("glyphs must be distinct up to rotation/reflection")
  for c in range(lx, lx + LEGEND_W):
    if all(grid[r][c] != LEGEND_C for r in range(height)):
      raise ValueError("legend strip extent would be ambiguous (column)")
  for r in range(height):
    if all(grid[r][c] != LEGEND_C for c in range(lx, lx + LEGEND_W)):
      raise ValueError("legend strip extent would be ambiguous (row)")
  out = [row[:] for row in grid]
  placed = []
  n_pattern = 0
  for top, left, colour, pattern in boxes:
    for name, v in (("box top", top), ("box left", left),
                    ("box colour", colour)):
      _check_int(name, v)
    if colour not in shapes:
      raise ValueError("box colour must be a legend colour")
    if top < 0 or top + BOX > height or left < cx0 or left + BOX > cx1:
      raise ValueError("box outside canvas")
    for t2, l2 in placed:
      if (top - 1 < t2 + BOX and t2 < top + BOX + 1 and
          left - 1 < l2 + BOX and l2 < left + BOX + 1):
        raise ValueError("boxes overlap or touch")
    placed.append((top, left))
    m = shapes[colour]
    if pattern is None:
      for r in range(BOX):
        for c in range(BOX):
          grid[top + r][left + c] = colour
          out[top + r][left + c] = FRAME_C
      for r in range(3):
        for c in range(3):
          if m[r][c]:
            out[top + 1 + r][left + 1 + c] = PAT_C
    else:
      p = _parse(pattern)
      if not _is_mask(p) or p not in _syms(m):
        raise ValueError("pattern does not match its glyph")
      n_pattern += 1
      for r in range(BOX):
        for c in range(BOX):
          grid[top + r][left + c] = FRAME_C
          out[top + r][left + c] = colour
      for r in range(3):
        for c in range(3):
          if p[r][c]:
            grid[top + 1 + r][left + 1 + c] = PAT_C
  if n_pattern == 0:
    raise ValueError("at least one pattern box is required")
  return grid, out


def _sample_scene(side, height, cw, rows, cols, n, p, minimal, strict):
  """Samples glyphs and boxes for a fixed layout, or returns None.

  Roles are fixed first: pattern colours, solid colours and distractors.
  Colour 2 is used only if the budget allows it, and as a box colour it is
  always a pattern colour. A designated pattern target is not fully
  D4-symmetric, is drawn in a non-identity orientation and (if strict)
  shares its cell count with another glyph. One solid glyph, if any, is not
  fully D4-symmetric. Shapes are drawn under a cell budget that keeps colour
  8 strictly above colour 2.
  """
  b = rows * cols
  budget = 6 * height - 25 * p - 1
  base = MIN_CELLS * (n - p)
  palette = list(PALETTE)
  if base + MIN_CELLS > budget:
    palette.remove(FRAME_C)
  if len(palette) < n or base > budget:
    return None
  colours = random.sample(palette, n)
  used = colours[:b]
  pat = set(random.sample(range(b), p))
  if FRAME_C in used:
    i2 = used.index(FRAME_C)
    if i2 not in pat:
      pat.remove(random.choice(sorted(pat)))
      pat.add(i2)
  pattern_colours = [used[i] for i in sorted(pat)]
  solid_colours = [used[i] for i in range(b) if i not in pat]
  costs = {}
  for c in colours:
    costs[c] = (0 if c in pattern_colours else 1) + (1 if c == FRAME_C else 0)
  free_targets = [c for c in pattern_colours if c != FRAME_C]
  target = random.choice(free_targets or pattern_colours)
  asym_solid = random.choice(solid_colours) if solid_colours else None
  costly = [c for c in colours if costs[c] and c != target]
  free = [c for c in colours if not costs[c] and c != target]
  random.shuffle(costly)
  random.shuffle(free)
  order = costly + free + [target]
  taken = set()
  shapes = {}
  sizes = []
  for i, c in enumerate(order):
    m = costs[c]
    cap = MAX_CELLS
    if m:
      reserve = sum(MIN_CELLS * costs[d] for d in order[i + 1:])
      cap = min(MAX_CELLS, (budget - reserve) // m)
    cands = [k for k in range(len(_CLASSES))
             if k not in taken and _CLASS_SIZE[k] <= cap]
    if c == target or c == asym_solid:
      cands = [k for k in cands if len(_CLASSES[k]) > 1]
    if c == target and strict and sizes:
      cands = [k for k in cands if _CLASS_SIZE[k] in sizes]
    if not cands:
      return None
    if minimal:
      smallest = min(_CLASS_SIZE[k] for k in cands)
      cands = [k for k in cands if _CLASS_SIZE[k] == smallest]
    k = random.choice(cands)
    taken.add(k)
    budget -= m * _CLASS_SIZE[k]
    sizes.append(_CLASS_SIZE[k])
    shapes[c] = random.choice(_CLASSES[k])
  legend_order = colours[:]
  random.shuffle(legend_order)
  gaps = _distribute(height - 3 * n, n + 1)
  offsets = [1, 2, 3] if side == "right" else [0, 1, 2]
  glyphs, r = [], gaps[0]
  for i, c in enumerate(legend_order):
    glyphs.append((c, r, random.choice(offsets), _unparse(shapes[c])))
    r += 3 + gaps[i + 1]
  x0 = 0 if side == "right" else LEGEND_W
  vg = _distribute(height - BOX * rows - (rows + 1), rows + 1)
  hg = _distribute(cw - BOX * cols - (cols + 1), cols + 1)
  tops, t = [], 1 + vg[0]
  for i in range(rows):
    tops.append(t)
    t += BOX + 1 + vg[i + 1]
  lefts, left = [], x0 + 1 + hg[0]
  for i in range(cols):
    lefts.append(left)
    left += BOX + 1 + hg[i + 1]
  slots = [(tt, ll) for tt in tops for ll in lefts]
  boxes = []
  for i, (tt, ll) in enumerate(slots):
    colour = used[i]
    if i in pat:
      shape = shapes[colour]
      opts = _syms(shape)
      if colour == target:
        opts = [s for s in opts if s != shape]
      boxes.append((tt, ll, colour, _unparse(random.choice(opts))))
    else:
      boxes.append((tt, ll, colour, None))
  return glyphs, boxes


def _random_scene(legend_side, height, width, num_glyphs, box_rows,
                  box_cols, num_patterns):
  for name, v in (("height", height), ("width", width),
                  ("num_glyphs", num_glyphs), ("box_rows", box_rows),
                  ("box_cols", box_cols), ("num_patterns", num_patterns)):
    _check_int(name, v)
  side = legend_side
  if side is None:
    side = random.choice(["left", "right"])
  if side not in ("left", "right"):
    raise ValueError("legend_side must be 'left' or 'right'")
  if height is None:
    if random.random() < 0.4:
      height = NATIVE_H
    else:
      height = random.randint(MIN_H, MAX_H)
  if width is None:
    if random.random() < 0.4:
      width = NATIVE_W
    else:
      width = random.randint(LEGEND_W + MIN_CW, LEGEND_W + MAX_CW)
  if not MIN_H <= height <= MAX_H:
    raise ValueError("random height must be in [12, 30]")
  cw = width - LEGEND_W
  if not MIN_CW <= cw <= MAX_CW:
    raise ValueError("random width must be in [18, 30]")
  n_cap = min(len(PALETTE), (height - 1) // 3)
  if num_glyphs is not None and not 1 <= num_glyphs <= n_cap:
    raise ValueError("num_glyphs must be in [1, %d]" % n_cap)
  if num_patterns is not None and num_patterns < 1:
    raise ValueError("num_patterns must be >= 1")
  glyph_cap = n_cap if num_glyphs is None else num_glyphs
  r_max, c_max = (height - 1) // 6, (cw - 1) // 6
  rows_opts = [box_rows] if box_rows is not None else range(1, r_max + 1)
  cols_opts = [box_cols] if box_cols is not None else range(1, c_max + 1)
  cands = []
  for r in rows_opts:
    for c in cols_opts:
      if not (1 <= r <= r_max and 1 <= c <= c_max):
        continue
      b = r * c
      if b > glyph_cap or height * cw - 25 * b <= 6 * height:
        continue
      if num_patterns is not None:
        n_min = max(2, b) if num_glyphs is None else num_glyphs
        if num_patterns > b or not _feasible_p(height, n_min, num_patterns):
          continue
      cands.append((r, c))
  if not cands:
    raise ValueError("requested box layout / glyph count / pattern count "
                     "does not fit the colour-count budget")
  big = [rc for rc in cands if rc[0] * rc[1] >= 2]
  if big:
    cands = big
  if (2, 2) in cands and random.random() < 0.4:
    rows, cols = 2, 2
  else:
    rows, cols = random.choice(cands)
  b = rows * cols
  n = num_glyphs
  if n is None:
    n_min = max(2, b)
    if random.random() < 0.5:
      n = n_min
    else:
      n = random.randint(n_min, min(n_cap, b + 2))
    if num_patterns is not None and not _feasible_p(height, n, num_patterns):
      n = n_min
  p_opts = [q for q in range(1, b + 1) if _feasible_p(height, n, q)]
  if not p_opts:
    raise ValueError("requested parameters admit no unambiguous scene")
  p_hi = max(p_opts)
  for attempt in range(60):
    minimal = attempt >= 40
    p = num_patterns if num_patterns is not None else random.randint(1, p_hi)
    scene = _sample_scene(side, height, cw, rows, cols, n, p, minimal, True)
    if scene is None:
      continue
    grid, out = _render(side, scene[0], scene[1], height, width)
    if _counts_ok(grid):
      return grid, out
  p = num_patterns if num_patterns is not None else 1
  # Retry with compact placement, but retain the same-count distractor:
  # a failed placement must not silently turn into an easier puzzle.
  for _ in range(40):
    scene = _sample_scene(side, height, cw, rows, cols, n, p, True, True)
    if scene is None:
      continue
    grid, out = _render(side, scene[0], scene[1], height, width)
    if _counts_ok(grid):
      return grid, out
  raise ValueError("requested parameters admit no unambiguous scene")


def generate(legend_side=None, glyphs=None, boxes=None, height=None,
             width=None, num_glyphs=None, box_rows=None, box_cols=None,
             num_patterns=None):
  """Returns {"input", "output"} for one b20f7c8b scene.

  Args:
    legend_side: "left" or "right", the side of the 6-wide legend strip.
      If omitted, it is random in random mode and "right" in explicit mode.
    glyphs: list of (colour, top_row, col_offset_in_legend, shape). shape is
      three '0'/'1' strings with a full 3x3 bounding box. Give this together
      with boxes for an explicit scene.
    boxes: list of (top, left, colour, pattern) in absolute coordinates.
      pattern is None for a solid box of that colour. Otherwise it is three
      '0'/'1' strings for the 1-pattern inside a 2-frame, and it must be a
      rotation/reflection of the colour's glyph.
    height: integer grid height. Random mode allows 12..30; explicit mode
      defaults to 18.
    width: integer total grid width including the legend. Random mode
      allows 18..30; explicit mode defaults to 22.
    num_glyphs: random mode only. Number of legend glyphs, at least the box
      count and at most min(8, (height - 1) // 3). Defaults use at least two;
      an explicitly requested one-glyph scene is a broader control.
    box_rows: random mode only. Rows in the box grid, 1..(height - 1) // 6.
    box_cols: random mode only. Columns in the box grid,
      1..(width - 7) // 6.
    num_patterns: random mode only. Number of pattern boxes, >= 1. It is
      rejected with ValueError if it cannot keep colour 8 second-most common.
  Bools, floats and other non-integers are rejected with ValueError.
  Explicit scenes allow full-bounding-box glyphs outside the random
  connected 4..7-cell vocabulary, and solid colour-2 boxes. They do not
  require non-identity orientations, same-count distractors, edge margins
  or an asymmetric solid target. The legend-readability, unique D4
  matching and colour-frequency checks still apply.
  """
  if (glyphs is None) != (boxes is None):
    raise ValueError("glyphs and boxes must be given together")
  if glyphs is not None:
    if any(v is not None for v in (num_glyphs, box_rows, box_cols,
                                   num_patterns)):
      raise ValueError("random controls cannot be combined with explicit "
                       "glyphs/boxes")
    side = legend_side if legend_side is not None else "right"
    h = NATIVE_H if height is None else height
    w = NATIVE_W if width is None else width
    grid, out = _render(side, glyphs, boxes, h, w)
    if not _counts_ok(grid):
      raise ValueError("background/legend colours would be ambiguous")
    return {"input": grid, "output": out}
  grid, out = _random_scene(legend_side, height, width, num_glyphs,
                            box_rows, box_cols, num_patterns)
  return {"input": grid, "output": out}


def validate():
  """Reconstructs the canonical fixtures through explicit parameters."""
  train = [
      generate("right",
               [(2, 1, 1, ["100", "011", "100"]),
                (3, 5, 2, ["111", "010", "100"]),
                (4, 10, 1, ["111", "010", "101"]),
                (7, 15, 1, ["110", "110", "001"])],
               [(2, 1, 2, ["010", "010", "101"]),
                (2, 8, 3, None),
                (9, 1, 7, ["100", "011", "011"]),
                (9, 8, 4, ["101", "110", "101"])]),
      generate("left",
               [(6, 2, 1, ["101", "101", "010"]),
                (5, 5, 2, ["001", "110", "101"]),
                (4, 9, 1, ["100", "111", "100"]),
                (3, 14, 2, ["011", "101", "011"])],
               [(1, 8, 3, ["110", "101", "110"]),
                (1, 15, 5, ["110", "010", "101"]),
                (8, 8, 4, ["111", "010", "010"]),
                (8, 15, 6, ["010", "101", "101"])]),
      generate("left",
               [(1, 1, 1, ["110", "101", "011"]),
                (3, 6, 1, ["110", "010", "011"]),
                (6, 11, 1, ["111", "010", "101"]),
                (4, 15, 2, ["010", "111", "010"])],
               [(1, 8, 3, ["100", "111", "001"]),
                (1, 15, 1, None),
                (8, 8, 6, None),
                (8, 15, 4, ["010", "111", "010"])]),
  ]
  test = [
      generate("right",
               [(3, 1, 2, ["101", "111", "101"]),
                (4, 6, 1, ["110", "101", "110"]),
                (6, 9, 3, ["010", "111", "010"]),
                (5, 13, 1, ["101", "011", "101"])],
               [(1, 1, 3, ["111", "010", "111"]),
                (1, 8, 6, None),
                (8, 1, 4, ["111", "101", "010"]),
                (8, 8, 5, ["101", "110", "101"])]),
  ]
  return {"train": train, "test": test}
