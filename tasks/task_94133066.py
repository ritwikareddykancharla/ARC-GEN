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

"""ARC task 94133066: orient a marked panel to match loose key dots.

Rule: the input is a background-0 canvas holding one rectangular colour-1
panel. Single-cell markers in three distinct colours sit in three of the four
cells set diagonally inside the panel corners: (1,1), (1,w-2), (h-2,1) and
(h-2,w-2). A free-form shape in a fourth colour lies in the panel interior
(rows 2..h-3, cols 2..w-3). It may have a few stray cells, as in the second
fixture. It may also touch a marker diagonally, as in the third fixture.
Outside the panel, three loose dots in the marker colours sit on three
corners of an axis-aligned rectangle. The output is the panel under the
unique dihedral transform that puts each marker in the same corner as its
matching dot. The shape moves with the panel.

In every fixture the dot rectangle is a translated copy of the output's
marker rectangle, with span (out_h - 3) x (out_w - 3). It sits wholly on one
side of the panel (above, below, left or right), with at least one empty line
between them. Default sampling reproduces both regularities.

Scope:
- Panel sides and transforms are chosen from analytically feasible layouts,
  respecting explicit canvas sizes, positions and dot boxes. The selected
  geometry stays fixed while shape/layout proposals retry. Sides 7..14 are
  preferred; 20% of calls extend that preference to 22. Smaller/larger sides
  within 5..26 are considered when the preferred range cannot satisfy the
  controls. Sizes beyond the fixtures are synthetic extensions.
- Area must not exceed 448, but that alone does not establish feasibility.
  A separated axis requires panel_extent + dot_span + 4 canvas cells.
  Thus a default 20x20 panel cannot fit a separated dot layout on 30x30;
  26x5 panels require a non-swapping transform. Explicit straddling layouts
  are checked separately. Border-connected 1s must form the unique largest
  single-colour 4-connected object, even when a shape encloses 1-pockets.
- Marker and shape colours come from 2..9 and are all distinct.
- Also sampled: the missing corner, the shape (an 8-connected random walk,
  sometimes plus 1-2 stray cells), the transform, the canvas size (up to
  30x30), the panel position, the side the dots lie on, and the dot
  rectangle's offset.
- Default sampling uses the 7 non-identity transforms. "identity" is
  accepted only when requested explicitly.
- Synthetic extensions, accepted only when given explicitly:
  - a dot_box whose span differs from the marker spacing;
  - fully explicit layouts in which the dot rectangle straddles the panel.
  In both cases the dots must still avoid the panel and its 1-cell halo.
- Fixed: background 0, panel colour 1, and a 1-cell empty canvas margin.
"""

import random

import common

TRANSFORMS = ("identity", "rot90", "rot180", "rot270", "flip_h",
              "flip_v", "transpose", "anti_transpose")
_SWAP = ("rot90", "rot270", "transpose", "anti_transpose")
_SIDES = ("above", "below", "left", "right")
_MAX_AREA = 448  # 900 - a - 3 > a on the largest canvas.


def _ri(lo, hi):
  """randint that returns None for an empty range."""
  if lo > hi:
    return None
  return random.randint(lo, hi)


def _pick(fixed, lo, hi):
  """Return fixed if it lies in [lo, hi], else None; sample if fixed is None."""
  if fixed is not None:
    return fixed if lo <= fixed <= hi else None
  return _ri(lo, hi)


def _is_int(v):
  """True for a genuine int (bool excluded)."""
  return isinstance(v, int) and not isinstance(v, bool)


def _apply(panel, name):
  """Apply a named dihedral transform to a list-of-rows grid."""
  h, w = len(panel), len(panel[0])
  hh, ww = (w, h) if name in _SWAP else (h, w)

  def src(r, c):
    if name == "identity":
      return r, c
    if name == "rot90":
      return h - 1 - c, r
    if name == "rot180":
      return h - 1 - r, w - 1 - c
    if name == "rot270":
      return c, w - 1 - r
    if name == "flip_h":
      return r, w - 1 - c
    if name == "flip_v":
      return h - 1 - r, c
    if name == "transpose":
      return c, r
    return h - 1 - c, w - 1 - r  # anti_transpose

  out = []
  for r in range(hh):
    row = []
    for c in range(ww):
      sr, sc = src(r, c)
      row.append(panel[sr][sc])
    out.append(row)
  return out


def _random_shape(ph, pw):
  """Random 8-connected walk in rows 2..ph-3 and cols 2..pw-3.

  Sometimes 1-2 stray cells are added as well.
  """
  r0, r1, c0, c1 = 2, ph - 3, 2, pw - 3
  area = (r1 - r0 + 1) * (c1 - c0 + 1)
  lo = min(5, area)
  n = random.randint(lo, max(lo, min(20, area * 2 // 3)))
  dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)] * 2 + [
      (1, 1), (1, -1), (-1, 1), (-1, -1)]
  r, c = random.randint(r0, r1), random.randint(c0, c1)
  cells = {(r, c)}
  steps = 0
  while len(cells) < n and steps < 600:
    dr, dc = random.choice(dirs)
    nr, nc = r + dr, c + dc
    if r0 <= nr <= r1 and c0 <= nc <= c1:
      r, c = nr, nc
      cells.add((r, c))
    steps += 1
  if area > len(cells) + 2 and random.random() < 0.35:
    free = [(y, x) for y in range(r0, r1 + 1) for x in range(c0, c1 + 1)
            if (y, x) not in cells]
    for cell in random.sample(free, min(random.randint(1, 2), len(free))):
      cells.add(cell)
  return sorted(cells)


def _cap(size, pos):
  """Largest panel side compatible with an explicit canvas size/position."""
  cap = 28
  if size is not None:
    cap = min(cap, size - 2)
    if pos is not None:
      cap = min(cap, size - 1 - pos)
  elif pos is not None:
    cap = min(cap, 29 - pos)
  return cap


def _layout_ok(hgt, wid, pt, pl, ph, pw, box, flags):
  """Check canvas, panel and dot-rectangle placement."""
  if not (1 <= hgt <= 30 and 1 <= wid <= 30):
    return False
  t, l, b, r = box
  if b - t < 2 or r - l < 2:
    return False
  if t < 1 or l < 1 or b > hgt - 2 or r > wid - 2:
    return False
  if pt < 1 or pl < 1 or pt + ph > hgt - 1 or pl + pw > wid - 1:
    return False
  for top, left in flags:
    y = t if top else b
    x = l if left else r
    # Keep dots off the panel and not 8-adjacent to it.
    if pt - 1 <= y <= pt + ph and pl - 1 <= x <= pl + pw:
      return False
  # Background must remain the majority colour.
  return hgt * wid - ph * pw - 3 > ph * pw


def _sep_axis(size, extent, span, box_first, fixed_pos, fixed_a):
  """Axis on which the panel and dot span are separated by an empty line.

  size: canvas length or None. extent: panel length. span: dot span.
  box_first: the dots lie before the panel on this axis.
  Returns (size, panel_pos, dot_start), or None when infeasible.
  """
  if size is None:
    lo = extent + span + 4
    if box_first:
      if fixed_pos is not None:
        lo = max(lo, fixed_pos + extent + 1)
      if fixed_a is not None:
        lo = max(lo, fixed_a + span + extent + 3)
    else:
      if fixed_pos is not None:
        lo = max(lo, fixed_pos + extent + span + 3)
      if fixed_a is not None:
        lo = max(lo, fixed_a + span + 2)
    size = _ri(lo, 30)
  if size is None:
    return None
  if box_first:
    lo = max(span + 3, fixed_a + span + 2 if fixed_a is not None else 1)
    pos = _pick(fixed_pos, lo, size - 1 - extent)
    if pos is None:
      return None
    a = _pick(fixed_a, 1, pos - span - 2)
  else:
    hi = min(size - extent - span - 3,
             fixed_a - extent - 1 if fixed_a is not None else size)
    pos = _pick(fixed_pos, 1, hi)
    if pos is None:
      return None
    a = _pick(fixed_a, pos + extent + 1, size - 2 - span)
  if a is None:
    return None
  return size, pos, a


def _cross_axis(size, extent, span, fixed_pos, fixed_a):
  """Axis on which the panel and dot span are placed independently."""
  if size is None:
    lo = max(extent + 2, span + 3)
    if fixed_pos is not None:
      lo = max(lo, fixed_pos + extent + 1)
    if fixed_a is not None:
      lo = max(lo, fixed_a + span + 2)
    size = _ri(lo, 30)
  if size is None:
    return None
  pos = _pick(fixed_pos, 1, size - 1 - extent)
  a = _pick(fixed_a, 1, size - 2 - span)
  if pos is None or a is None:
    return None
  return size, pos, a


def _axis_possible(size, extent, span, before, fixed_pos, fixed_a):
  """Whether this axis admits coordinates satisfying all fixed controls."""
  if extent+2 > size or span+3 > size:
    return False
  if fixed_a is not None and not 1 <= fixed_a <= size-2-span:
    return False
  if before is None:
    lo, hi = 1, size-1-extent
  elif before:
    lo = max(span+3, fixed_a+span+2 if fixed_a is not None else 1)
    hi = size-1-extent
  else:
    lo = 1
    hi = min(size-extent-span-3,
             fixed_a-extent-1 if fixed_a is not None else size)
  return lo <= hi and (fixed_pos is None or lo <= fixed_pos <= hi)


def _possible_layout(ph, pw, tr, flags, hgt, wid, pt, pl, box):
  """Exact separated-layout feasibility on the largest available canvas."""
  H, W = hgt or 30, wid or 30
  if H*W-ph*pw-3 <= ph*pw:
    return False
  if None not in (hgt, wid, pt, pl) and box is not None:
    return _layout_ok(H, W, pt, pl, ph, pw, box, flags)
  oh, ow = (pw, ph) if tr in _SWAP else (ph, pw)
  sr, sc, t, l = oh-3, ow-3, None, None
  if box is not None:
    t, l, b, r = box
    sr, sc = b-t, r-l
  for side in _SIDES:
    rows_before = side == "above" if side in ("above", "below") else None
    cols_before = side == "left" if side in ("left", "right") else None
    if (_axis_possible(H, ph, sr, rows_before, pt, t) and
        _axis_possible(W, pw, sc, cols_before, pl, l)):
      return True
  return False


def _border_is_largest(panel):
  """The border-connected colour-1 object must be the unique largest object."""
  h, w = len(panel), len(panel[0])
  todo = {(r,c) for r in range(h) for c in range(w)}
  border_size, others = 0, []
  while todo:
    seed = todo.pop()
    group, stack = {seed}, [seed]
    colour = panel[seed[0]][seed[1]]
    for r,c in stack:
      for p in ((r+1,c), (r-1,c), (r,c+1), (r,c-1)):
        if p in todo and panel[p[0]][p[1]] == colour:
          todo.remove(p)
          group.add(p)
          stack.append(p)
    if (0,0) in group:
      border_size = len(group)
    else:
      others.append(len(group))
  return all(border_size > n for n in others)


def _sample_layout(ph, pw, span_r, span_c, flags, hgt, wid, pt, pl, box,
                   tries=40):
  """Sample unspecified layout values, honouring every specified one.

  Returns (height, width, panel_top, panel_left, box) or None.
  """
  if None not in (hgt, wid, pt, pl) and box is not None:
    if _layout_ok(hgt, wid, pt, pl, ph, pw, box, flags):
      return hgt, wid, pt, pl, box
    return None
  fixed_t = fixed_l = None
  if box is not None:
    t, l, b, r = box
    span_r, span_c, fixed_t, fixed_l = b - t, r - l, t, l
  for attempt in range(tries + 4):
    side = random.choice(_SIDES) if attempt < tries else _SIDES[attempt-tries]
    H = hgt if attempt < tries else (hgt or 30)
    W = wid if attempt < tries else (wid or 30)
    if side in ("above", "below"):
      rows = _sep_axis(H, ph, span_r, side == "above", pt, fixed_t)
      cols = _cross_axis(W, pw, span_c, pl, fixed_l)
    else:
      rows = _cross_axis(H, ph, span_r, pt, fixed_t)
      cols = _sep_axis(W, pw, span_c, side == "left", pl, fixed_l)
    if rows is None or cols is None:
      continue
    h, ptop, t = rows
    w, pleft, l = cols
    bx = (t, l, t + span_r, l + span_c)
    if _layout_ok(h, w, ptop, pleft, ph, pw, bx, flags):
      return h, w, ptop, pleft, bx
  return None


def generate(height=None, width=None, panel_top=None, panel_left=None,
             panel_height=None, panel_width=None, corners=None,
             shape_color=None, shape_cells=None, transform=None,
             dot_box=None):
  """Build one input/output pair.

  Any argument left as None is sampled. Given arguments are honoured, and
  incompatible or malformed values raise ValueError.

  Args:
    height, width: canvas size in rows and columns, 7..30.
    panel_top, panel_left: top-left cell of the colour-1 panel, 1..28.
    panel_height, panel_width: panel size, 5..26, with product <= 448.
      Preferred sides are 7..14 (sometimes up to 22); the full 5..26 range
      is considered if that preference cannot fit. The separated axis needs
      panel extent + dot span + 4 cells; area alone is not sufficient.
    corners: tuple (tl, tr, bl, br) of marker colours, with 0 marking the
      unused corner. Exactly three must be nonzero, distinct, and in 2..9.
      Markers sit at panel cells (1,1), (1,w-2), (h-2,1), (h-2,w-2).
    shape_color: colour of the interior shape. In 2..9 and not a marker.
    shape_cells: non-empty list of integer (row, col) panel coordinates of
      the shape, all within rows 2..h-3 and cols 2..w-3. Need not be
      connected.
    transform: one of TRANSFORMS. The output is the transformed panel.
    dot_box: (top, left, bottom, right) of the rectangle whose corners hold
      the loose key dots, each side span at least 2. When sampled, its span
      equals the output marker spacing (out_h-3, out_w-3) and it lies wholly
      on one side of the panel.
  """
  for name, v, lo, hi in (("height", height, 7, 30),
                          ("width", width, 7, 30),
                          ("panel_top", panel_top, 1, 28),
                          ("panel_left", panel_left, 1, 28),
                          ("panel_height", panel_height, 5, 26),
                          ("panel_width", panel_width, 5, 26)):
    if v is not None and not (_is_int(v) and lo <= v <= hi):
      raise ValueError("%s must be an integer in %d..%d" % (name, lo, hi))
  if dot_box is not None:
    try:
      dot_box = tuple(dot_box)
    except TypeError:
      raise ValueError("dot_box must be (top, left, bottom, right)")
    if len(dot_box) != 4 or not all(
        _is_int(v) and 0 <= v <= 29 for v in dot_box):
      raise ValueError("dot_box must be four integers in 0..29")
    if dot_box[2] - dot_box[0] < 2 or dot_box[3] - dot_box[1] < 2:
      raise ValueError("dot_box spans must be at least 2")
  if (panel_height is not None and panel_width is not None
      and panel_height * panel_width > _MAX_AREA):
    raise ValueError("panel area above 448 cannot leave background majority")

  need_h = need_w = 0
  if shape_cells is not None:
    cells = set()
    try:
      for cell in shape_cells:
        r, c = cell
        if not (_is_int(r) and _is_int(c)):
          raise ValueError("shape cell coordinates must be integers")
        cells.add((r, c))
    except TypeError:
      raise ValueError("shape_cells must be a list of (row, col) pairs")
    shape_cells = sorted(cells)
    if not shape_cells:
      raise ValueError("shape_cells must be non-empty")
    if any(r < 2 or c < 2 for r, c in shape_cells):
      raise ValueError("shape cells must be inside the panel interior")
    need_h = max(r for r, _ in shape_cells) + 3
    need_w = max(c for _, c in shape_cells) + 3

  cap_h = _cap(height, panel_top)
  cap_w = _cap(width, panel_left)
  for fixed, need, cap, nm in ((panel_height, need_h, cap_h, "height"),
                               (panel_width, need_w, cap_w, "width")):
    if fixed is not None and fixed < need:
      raise ValueError("shape cells do not fit the panel interior")
    if (fixed if fixed is not None else max(5, need)) > min(26, cap):
      raise ValueError("panel %s does not fit the canvas" % nm)

  if corners is None:
    cols = random.sample(range(2, 10), 3)
    missing = random.randint(0, 3)
    corners = tuple(0 if i == missing else cols.pop() for i in range(4))
  try:
    corners = tuple(corners)
  except TypeError:
    raise ValueError("corners must be a sequence of four ints")
  if len(corners) != 4 or not all(
      _is_int(c) and (c == 0 or 2 <= c <= 9) for c in corners):
    raise ValueError("corners must be four ints, each 0 or in 2..9")
  markers = [c for c in corners if c]
  if len(markers) != 3 or len(set(markers)) != 3:
    raise ValueError("corners needs exactly three distinct marker colours")
  if shape_color is None:
    shape_color = random.choice([c for c in range(2, 10) if c not in markers])
  if not (_is_int(shape_color) and 2 <= shape_color <= 9
          and shape_color not in markers):
    raise ValueError("shape colour collides with background, panel or marker")
  if transform is not None and (not isinstance(transform, str)
                                or transform not in TRANSFORMS):
    raise ValueError("unknown transform")

  # Select only geometries with a feasible layout; never reject a valid
  # small canvas merely because preferred 7..14 panels cannot fit.
  hs = [panel_height] if panel_height is not None else range(max(5,need_h), min(26,cap_h)+1)
  ws = [panel_width] if panel_width is not None else range(max(5,need_w), min(26,cap_w)+1)
  transforms = [transform] if transform is not None else TRANSFORMS[1:]
  options = {}
  preferred_max = 22 if random.random() < 0.2 else 14
  for tr in transforms:
    corner_grid = _apply([list(corners[:2]), list(corners[2:])], tr)
    flags = [(r == 0, c == 0) for r in range(2) for c in range(2)
             if corner_grid[r][c]]
    feasible = [(ph,pw) for ph in hs for pw in ws
                if ph*pw <= _MAX_AREA and
                _possible_layout(ph,pw,tr,flags,height,width,panel_top,panel_left,dot_box)]
    preferred = [(ph,pw) for ph,pw in feasible
                 if (panel_height is not None or 7 <= ph <= preferred_max) and
                 (panel_width is not None or 7 <= pw <= preferred_max)]
    if feasible:
      options[tr] = preferred or feasible
  if not options:
    raise ValueError("no feasible panel/dot layout with these dimensions and controls")
  tr = random.choice(list(options))
  ph, pw = random.choice(options[tr])
  for _ in range(80):
    cells = shape_cells if shape_cells is not None else _random_shape(ph, pw)

    panel = [[1] * pw for _ in range(ph)]
    for r, c in cells:
      panel[r][c] = shape_color
    spots = [(1, 1), (1, pw - 2), (ph - 2, 1), (ph - 2, pw - 2)]
    for (r, c), col in zip(spots, corners):
      if col:
        panel[r][c] = col
    # Colour 1 must remain the panel's dominant colour.
    if (sum(row.count(1) for row in panel) <= len(cells) or
        not _border_is_largest(panel)):
      if shape_cells is not None:
        raise ValueError("panel border must remain the unique largest object")
      continue
    output = _apply(panel, tr)
    oh, ow = len(output), len(output[0])

    # The output corner of each marker decides the corner of its dot.
    flags = []
    for col in markers:
      for r in range(oh):
        for c in range(ow):
          if output[r][c] == col:
            flags.append((col, 2 * r < oh, 2 * c < ow))

    layout = _sample_layout(ph, pw, oh - 3, ow - 3,
                            [(a, b) for _, a, b in flags], height, width,
                            panel_top, panel_left, dot_box)
    if layout is None:
      continue
    hgt, wid, ptop, pleft, box = layout

    grid = common.grid(wid, hgt, 0)
    for r in range(ph):
      for c in range(pw):
        grid[ptop + r][pleft + c] = panel[r][c]
    t, l, b, rr = box
    for col, top, left in flags:
      grid[t if top else b][l if left else rr] = col
    return {"input": grid, "output": output}
  raise ValueError("no valid layout compatible with the given parameters")


def validate():
  """Rebuild the canonical fixtures from explicit latent parameters."""
  train = [
      generate(height=22, width=21, panel_top=1, panel_left=10,
               panel_height=9, panel_width=9, corners=(4, 8, 5, 0),
               shape_color=2,
               shape_cells=[(2, 4), (3, 4), (4, 2), (4, 3), (4, 4), (5, 4),
                            (6, 4), (6, 5), (6, 6)],
               transform="transpose", dot_box=(13, 5, 19, 11)),
      generate(height=23, width=19, panel_top=1, panel_left=2,
               panel_height=9, panel_width=10, corners=(2, 4, 0, 3),
               shape_color=8,
               shape_cells=[(2, 5), (3, 3), (3, 4), (3, 5), (3, 7), (4, 3),
                            (5, 3), (5, 4), (5, 5), (5, 6), (6, 2), (6, 6)],
               transform="anti_transpose", dot_box=(14, 8, 21, 14)),
      generate(height=22, width=25, panel_top=9, panel_left=2,
               panel_height=12, panel_width=10, corners=(2, 3, 0, 4),
               shape_color=5,
               shape_cells=[(2, 3), (2, 6), (3, 2), (3, 3), (3, 6), (3, 7),
                            (4, 4), (4, 5), (4, 7), (5, 7), (6, 7), (7, 7),
                            (8, 7), (9, 7)],
               transform="flip_v", dot_box=(1, 15, 10, 22)),
  ]
  test = [
      generate(height=19, width=30, panel_top=2, panel_left=18,
               panel_height=13, panel_width=10, corners=(4, 2, 0, 8),
               shape_color=3,
               shape_cells=[(2, 3), (3, 2), (3, 3), (4, 4), (4, 5), (4, 6),
                            (4, 7), (5, 4), (5, 5), (6, 5), (7, 5), (8, 5),
                            (9, 6), (9, 7), (10, 6)],
               transform="anti_transpose", dot_box=(5, 2, 12, 12)),
  ]
  return {"train": train, "test": test}
