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

"""ARC-GEN style generator for task 9b5080bb.

Rule: a frame-coloured grid holds two rectangular coloured panels. The second
panel is painted over the first, and some frame colour is left over. Inside
each panel sit one or more nearly rectangular shapes of one shared shape
colour. Each shape has defects on its border:
  * notch: a non-corner border cell of the rectangle that shows the panel
    colour instead of the shape colour;
  * bump: one shape-coloured cell sticking out one step beyond a non-corner
    border position.
In the output, every defect becomes a 2-cell bar that straddles the rectangle
border. A notch is painted together with the cell just outside it. A bump is
painted together with the border cell just inside it. The bar colour is the
colour of the OTHER panel.

Scope: random grids are 14..30 per side by default. Explicit random-mode sizes
may be 8..30, provided the longer side is at least 14 (sizes other than the
fixture sizes are synthetic extensions). The frame colour, the two panel
colours and the shape colour are four distinct colours. The caller may fix
the frame colour, the shape colour, the two panel colours and the layout.
Panels are either placed freely, where they may overlap and the later one is
painted on top, or split along the longer axis, where they touch or are
separated by a 1-2 cell frame gap. Each panel holds 1-3 shapes. Rectangles
are 3..11 on each side (both orientations), clamped to the panel box. Each
shape has 1-4 non-touching notch or bump defects on non-corner border
positions. Every scene contains at least one notch and at least one bump, on
at least two different sides. Shapes keep a panel-coloured ring: 1 cell wide,
or 2 cells on sides that carry a bump. Different shapes may come as close as
one empty cell between their cells and bars, as in the fixtures. Explicit
latent arguments reproduce the original fixtures exactly and are checked for
rule consistency. Explicit mode is broader than the random distribution:
it may contain adjacent defects, larger rectangles, only one defect type,
or no visible frame, provided the scene remains independently recoverable.
Random bar cells remain inside their own panel. A notch bar can lie on the
panel boundary and be adjacent to a foreign colour; it does not cross into it.
A split gap of one or two rows/columns is available only when the longer
side leaves room beyond the minimum14-cell split span.
"""

import random
from collections import Counter

import common


_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _build_base(width, height, frame, panels):
  g = [list(row) for row in common.grid(width, height, frame)]
  for colour, top, left, h, w in panels:
    for y in range(top, top + h):
      for x in range(left, left + w):
        g[y][x] = colour
  return g


def _shape_cells(shape):
  top, left, h, w, notches, bumps = shape
  cells = set((y, x) for y in range(top, top + h)
              for x in range(left, left + w))
  cells -= set(tuple(c) for c in notches)
  cells |= set(tuple(c) for c in bumps)
  return cells


def _bars(shape):
  """Cells repainted for one shape, derived from its latent defects."""
  top, left, h, w, notches, bumps = shape
  bottom, right = top + h - 1, left + w - 1
  cells = []
  for y, x in notches:
    if x == left:
      cells += [(y, x), (y, x - 1)]
    elif x == right:
      cells += [(y, x), (y, x + 1)]
    elif y == top:
      cells += [(y, x), (y - 1, x)]
    else:
      cells += [(y, x), (y + 1, x)]
  for y, x in bumps:
    if y < top:
      cells += [(y, x), (top, x)]
    elif y > bottom:
      cells += [(y, x), (bottom, x)]
    elif x < left:
      cells += [(y, x), (y, left)]
    else:
      cells += [(y, x), (y, right)]
  return cells


def _occupied(shape):
  return set(_shape_cells(shape)) | set(_bars(shape))


def _halo(cells):
  out = set()
  for y, x in cells:
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        out.add((y + dy, x + dx))
  return out


def _render(width, height, frame, panels, shape_color, shapes):
  base = _build_base(width, height, frame, panels)
  inp = [row[:] for row in base]
  for shape in shapes:
    for y, x in _shape_cells(shape):
      inp[y][x] = shape_color
  out = [row[:] for row in inp]
  colours = [p[0] for p in panels]
  for shape in shapes:
    panel_colour = base[shape[0]][shape[1]]
    fill = [c for c in colours if c != panel_colour][0]
    for y, x in _bars(shape):
      out[y][x] = fill
  return inp, out


def _recoverable(shape):
  """The true rectangle must be the span of rows/cols holding > half max."""
  top, left, h, w = shape[0], shape[1], shape[2], shape[3]
  cells = _shape_cells(shape)
  rows = Counter(y for y, _ in cells)
  cols = Counter(x for _, x in cells)
  mr, mc = max(rows.values()), max(cols.values())
  rr = [y for y, n in rows.items() if 2 * n > mr]
  cc = [x for x, n in cols.items() if 2 * n > mc]
  return (min(rr) == top and max(rr) == top + h - 1 and
          min(cc) == left and max(cc) == left + w - 1)


def _classify(shape):
  """Returns (kind, side) per defect; raises if a defect is misplaced."""
  top, left, h, w, notches, bumps = shape
  bottom, right = top + h - 1, left + w - 1
  out = []
  for y, x in notches:
    if top < y < bottom and x in (left, right):
      out.append(("notch", "L" if x == left else "R"))
    elif left < x < right and y in (top, bottom):
      out.append(("notch", "T" if y == top else "B"))
    else:
      raise ValueError("a notch must be a non-corner border cell")
  for y, x in bumps:
    if top < y < bottom and x in (left - 1, right + 1):
      out.append(("bump", "L" if x < left else "R"))
    elif left < x < right and y in (top - 1, bottom + 1):
      out.append(("bump", "T" if y < top else "B"))
    else:
      raise ValueError("a bump must sit just outside a non-corner border cell")
  return out


def _components(g):
  height, width = len(g), len(g[0])
  seen = set()
  comps = []
  for y in range(height):
    for x in range(width):
      if (y, x) in seen:
        continue
      colour = g[y][x]
      seen.add((y, x))
      stack, cells = [(y, x)], []
      while stack:
        cy, cx = stack.pop()
        cells.append((cy, cx))
        for dy, dx in _DIRS:
          ny, nx = cy + dy, cx + dx
          if (0 <= ny < height and 0 <= nx < width and
              (ny, nx) not in seen and g[ny][nx] == colour):
            seen.add((ny, nx))
            stack.append((ny, nx))
      comps.append((colour, cells))
  return comps


def _scene_ok(g, shapes, shape_color):
  """Only the shapes may be components enclosed by one single colour."""
  height, width = len(g), len(g[0])
  singles = set()
  for colour, cells in _components(g):
    cs = set(cells)
    nb = set()
    for y, x in cells:
      for dy, dx in _DIRS:
        ny, nx = y + dy, x + dx
        if 0 <= ny < height and 0 <= nx < width and (ny, nx) not in cs:
          nb.add(g[ny][nx])
    if len(nb) <= 1:
      if colour != shape_color or not nb:
        return False
      singles.add(frozenset(cells))
  return singles == set(frozenset(_shape_cells(s)) for s in shapes)


def _prefix(base, colour):
  height, width = len(base), len(base[0])
  pre = [[0] * (width + 1) for _ in range(height + 1)]
  for y in range(height):
    run = 0
    for x in range(width):
      run += 1 if base[y][x] == colour else 0
      pre[y + 1][x + 1] = pre[y][x + 1] + run
  return pre


def _full(pre, y0, x0, y1, x1):
  area = (y1 - y0 + 1) * (x1 - x0 + 1)
  s = pre[y1 + 1][x1 + 1] - pre[y0][x1 + 1] - pre[y1 + 1][x0] + pre[y0][x0]
  return s == area


def _sample_defects(h, w):
  """Relative defects (side, is_bump, cell) on non-corner positions."""
  want = random.randint(1, 3 if max(h, w) < 6 else 4)
  defects, cells = [], []
  for _ in range(40):
    if len(defects) == want:
      break
    side = random.choice("TBLR")
    length = w if side in "TB" else h
    i = random.randint(1, length - 2)
    if side == "T":
      border, outside = (0, i), (-1, i)
    elif side == "B":
      border, outside = (h - 1, i), (h, i)
    elif side == "L":
      border, outside = (i, 0), (i, -1)
    else:
      border, outside = (i, w - 1), (i, w)
    is_bump = random.random() < 0.5
    cell = outside if is_bump else border
    if any(max(abs(cell[0] - c[0]), abs(cell[1] - c[1])) <= 1
           for c in cells):
      continue
    cells.append(cell)
    defects.append((side, is_bump, cell))
  return defects


def _place_shape(pre, blocked, box):
  """Places one random defective rectangle inside the given panel box."""
  _, btop, bleft, bh, bw = box
  hmax, wmax = min(11, bh - 2), min(11, bw - 2)
  if hmax < 3 or wmax < 3:
    return None
  h = random.randint(3, hmax)
  w = random.randint(3, wmax)
  defects = _sample_defects(h, w)
  if not defects:
    return None
  rel = (0, 0, h, w, [c for _, b, c in defects if not b],
         [c for _, b, c in defects if b])
  if not _recoverable(rel):
    return None
  m = {s: 1 for s in "TBLR"}
  for side, is_bump, _ in defects:
    if is_bump:
      m[side] = 2
  occ_rel = _occupied(rel)
  cands = []
  for top in range(btop + m["T"], btop + bh - h - m["B"] + 1):
    for left in range(bleft + m["L"], bleft + bw - w - m["R"] + 1):
      if _full(pre, top - m["T"], left - m["L"],
               top + h - 1 + m["B"], left + w - 1 + m["R"]):
        cands.append((top, left))
  random.shuffle(cands)
  for top, left in cands:
    if any((top + y, left + x) in blocked for y, x in occ_rel):
      continue
    notches = [(top + y, left + x) for y, x in rel[4]]
    bumps = [(top + y, left + x) for y, x in rel[5]]
    return (top, left, h, w, notches, bumps)
  return None


def _sample_panels(wd, ht, pa, pb, layout):
  """Two panel boxes: free (possibly overlapping) or split along an axis."""
  if layout == "split":
    split = True
  elif layout == "free":
    split = False
  else:
    split = min(wd, ht) < 12 or random.random() < 0.5
  if split:
    if ht > wd:
      axis = 0
    elif wd > ht:
      axis = 1
    else:
      axis = random.randint(0, 1)
    length, cross = (ht, wd) if axis == 0 else (wd, ht)
    gap = random.randint(0, min(2, length - 14))
    cut = random.randint(7, length - 7 - gap)
    spans = [(random.randint(0, cut - 7), cut - 1),
             (cut + gap, random.randint(cut + gap + 6, length - 1))]
    random.shuffle(spans)
    panels = []
    for colour, (s0, s1) in zip((pa, pb), spans):
      ln = random.randint(min(7, cross), cross)
      st = random.randint(0, cross - ln)
      if axis == 0:
        panels.append((colour, s0, st, s1 - s0 + 1, ln))
      else:
        panels.append((colour, st, s0, ln, s1 - s0 + 1))
    return panels
  panels = []
  for colour in (pa, pb):
    h = random.randint(7, ht)
    w = random.randint(7, wd)
    panels.append((colour, random.randint(0, ht - h),
                   random.randint(0, wd - w), h, w))
  return panels


def _random_scene(width, height, frame, shape_color, panel_colors, layout):
  for _ in range(1000):
    wd = width if width is not None else random.randint(14, 30)
    ht = height if height is not None else random.randint(14, 30)
    if max(wd, ht) < 14:
      continue
    if layout == "free" and min(wd, ht) < 12:
      continue
    fixed = [c for c in (frame, shape_color) if c is not None]
    if panel_colors is not None:
      fixed += list(panel_colors)
    pool = [c for c in range(10) if c not in fixed]
    random.shuffle(pool)
    fr = frame if frame is not None else pool.pop()
    sc = shape_color if shape_color is not None else pool.pop()
    if panel_colors is not None:
      pa, pb = panel_colors
    else:
      pa, pb = pool.pop(), pool.pop()
    panels = _sample_panels(wd, ht, pa, pb, layout)
    base = _build_base(wd, ht, fr, panels)
    if not any(fr in row for row in base):
      continue
    shapes, blocked, ok = [], set(), True
    for box in panels:
      pre = _prefix(base, box[0])
      want, placed = random.randint(1, 3), 0
      for _ in range(30):
        if placed == want:
          break
        shape = _place_shape(pre, blocked, box)
        if shape is None:
          continue
        blocked |= _halo(_occupied(shape))
        shapes.append(shape)
        placed += 1
      if placed == 0:
        ok = False
        break
    if not ok:
      continue
    kinds = [d for s in shapes for d in _classify(s)]
    if not any(k == "notch" for k, _ in kinds):
      continue
    if not any(k == "bump" for k, _ in kinds):
      continue
    if len(set(side for _, side in kinds)) < 2:
      continue
    inp, _ = _render(wd, ht, fr, panels, sc, shapes)
    if not _scene_ok(inp, shapes, sc):
      continue
    return wd, ht, fr, panels, sc, shapes
  raise RuntimeError("could not build a valid scene for the requested size")


def _check_colour(c, name):
  if c is not None and (not _is_int(c) or not 0 <= c <= 9):
    raise ValueError(name + " must be an integer colour in 0..9")


def _int_field(v, name):
  if not _is_int(v):
    raise ValueError(name + " must be an integer")
  return v


def _normalise_panels(panels):
  if not isinstance(panels, (list, tuple)) or len(panels) != 2:
    raise ValueError("panels must be a list of exactly two boxes")
  out = []
  for p in panels:
    if not isinstance(p, (list, tuple)) or len(p) != 5:
      raise ValueError("each panel must be (colour, top, left, height, width)")
    out.append(tuple(_int_field(v, "panel field") for v in p))
  return out


def _normalise_cells(cells, name):
  if not isinstance(cells, (list, tuple)):
    raise ValueError(name + " list must be a list of (row, col) cells")
  out = []
  for c in cells:
    if not isinstance(c, (list, tuple)) or len(c) != 2:
      raise ValueError(name + " cells must be (row, col) pairs")
    out.append((_int_field(c[0], name), _int_field(c[1], name)))
  return out


def _normalise_shapes(shapes):
  if not isinstance(shapes, (list, tuple)) or not shapes:
    raise ValueError("shapes must be a non-empty list")
  out = []
  for s in shapes:
    if not isinstance(s, (list, tuple)) or len(s) != 6:
      raise ValueError("each shape must be (top, left, h, w, notches, bumps)")
    head = tuple(_int_field(v, "shape field") for v in s[:4])
    out.append(head + (_normalise_cells(s[4], "notch"),
                       _normalise_cells(s[5], "bump")))
  return out


def _check_explicit(width, height, frame, panels, shape_color, shapes):
  """Rejects explicit scenes that are inconsistent with the task rule."""
  if not (_is_int(width) and _is_int(height)):
    raise ValueError("grid sides must be integers")
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("grid sides must be in 1..30")
  if panels[0][0] == panels[1][0]:
    raise ValueError("exactly two panels with distinct colours are required")
  for p in panels:
    _check_colour(p[0], "panel colour")
  colours = [frame, shape_color, panels[0][0], panels[1][0]]
  if len(set(colours)) != 4:
    raise ValueError("frame, panel and shape colours must be distinct")
  for _, top, left, h, w in panels:
    if (h < 1 or w < 1 or top < 0 or left < 0 or top + h > height or
        left + w > width):
      raise ValueError("panel out of bounds")
  base = _build_base(width, height, frame, panels)
  used, occs = set(), []
  for shape in shapes:
    top, left, h, w = shape[0], shape[1], shape[2], shape[3]
    if h < 3 or w < 3:
      raise ValueError("shape rectangles must be at least 3x3")
    if not (0 <= top and 0 <= left and top + h <= height and
            left + w <= width):
      raise ValueError("shape rectangle out of bounds")
    if not _classify(shape):
      raise ValueError("every shape needs at least one defect")
    if not _recoverable(shape):
      raise ValueError("shape rectangle is not recoverable from its cells")
    occ = _occupied(shape)
    for y, x in occ:
      if not (0 <= y < height and 0 <= x < width):
        raise ValueError("shape or bar cell out of bounds")
    colour = base[top][left]
    if colour not in (panels[0][0], panels[1][0]):
      raise ValueError("shape must lie inside a panel")
    cells = _shape_cells(shape)
    ring = set()
    for y, x in cells:
      for dy, dx in _DIRS:
        ny, nx = y + dy, x + dx
        if 0 <= ny < height and 0 <= nx < width and (ny, nx) not in cells:
          ring.add((ny, nx))
    if any(base[y][x] != colour for y, x in occ | ring):
      raise ValueError("shape, bars and ring must all lie in one panel")
    used.add(colour)
    occs.append(occ)
  if used != set((panels[0][0], panels[1][0])):
    raise ValueError("both panels must hold at least one shape")
  for i in range(len(occs)):
    halo = _halo(occs[i])
    for j in range(i + 1, len(occs)):
      if halo & occs[j]:
        raise ValueError("shapes (with their bars) must not touch")
  inp, _ = _render(width, height, frame, panels, shape_color, shapes)
  if not _scene_ok(inp, shapes, shape_color):
    raise ValueError("scene has extra single-colour-enclosed components")


def generate(width=None, height=None, frame=None, panels=None,
             shape_color=None, shapes=None, panel_colors=None, layout=None):
  """Returns an input/output pair for task 9b5080bb.

  Args:
    width: grid width. Random mode samples 14..30 when None. An explicit
      random-mode value must be an int in 8..30, and max(width, height) >= 14
      if both are given. Explicit mode accepts 1..30 subject to scene checks.
    height: grid height, same convention as width.
    frame: leftover frame colour. Honoured in random mode when given.
    panels: list of (colour, top, left, height, width) boxes, painted in
      order. There must be exactly two, with distinct colours. Must be given
      together with shapes (explicit mode).
    shape_color: colour of all near-rectangular shapes. Honoured in random
      mode when given.
    shapes: list of (top, left, height, width, notches, bumps). notches and
      bumps are lists of absolute (row, col) cells. Explicit mode requires
      width, height, frame, panels, shape_color and shapes all given, and
      rejects scenes that are inconsistent with the rule.
    panel_colors: random mode only. A pair of two distinct panel colours,
      painted in the given order; must differ from frame and shape_color.
    layout: random mode only. "free" (possibly overlapping panels; needs
      both sides >= 12), "split" (panels split along the longer axis, with
      an optional 1-2 cell frame gap), or None for a random choice.
  """
  _check_colour(frame, "frame")
  _check_colour(shape_color, "shape_color")
  if frame is not None and frame == shape_color:
    raise ValueError("frame and shape_color must differ")
  if panels is not None or shapes is not None:
    if (panels is None or shapes is None or width is None or
        height is None or frame is None or shape_color is None):
      raise ValueError("explicit mode needs width, height, frame, panels, "
                       "shape_color and shapes together")
    if panel_colors is not None or layout is not None:
      raise ValueError("panel_colors and layout are random-mode controls")
    panels = _normalise_panels(panels)
    shapes = _normalise_shapes(shapes)
    _check_explicit(width, height, frame, panels, shape_color, shapes)
  else:
    for v in (width, height):
      if v is not None and (not _is_int(v) or not 8 <= v <= 30):
        raise ValueError("random-mode grid sides must be integers in 8..30")
    if width is not None and height is not None and max(width, height) < 14:
      raise ValueError("random mode needs a side of at least 14")
    if layout not in (None, "free", "split"):
      raise ValueError("layout must be None, 'free' or 'split'")
    if layout == "free":
      for v in (width, height):
        if v is not None and v < 12:
          raise ValueError("free layout needs both sides >= 12")
    if panel_colors is not None:
      if (not isinstance(panel_colors, (list, tuple)) or
          len(panel_colors) != 2):
        raise ValueError("panel_colors must be a pair of colours")
      for c in panel_colors:
        if c is None:
          raise ValueError("panel colour must be an integer in 0..9")
        _check_colour(c, "panel colour")
      panel_colors = (panel_colors[0], panel_colors[1])
      if panel_colors[0] == panel_colors[1]:
        raise ValueError("panel colours must differ")
      if frame in panel_colors or shape_color in panel_colors:
        raise ValueError("panel colours must differ from frame and shape")
    width, height, frame, panels, shape_color, shapes = _random_scene(
        width, height, frame, shape_color, panel_colors, layout)
  inp, out = _render(width, height, frame, panels, shape_color, shapes)
  return {"input": inp, "output": out}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=23, height=23, frame=1,
               panels=[(8, 1, 1, 15, 14), (4, 10, 4, 12, 18)],
               shape_color=2,
               shapes=[(2, 4, 5, 9, [(4, 4), (4, 12)], [(7, 7)]),
                       (13, 8, 6, 8, [(13, 12)], [(15, 7), (19, 11)]),
                       (11, 18, 5, 3, [(14, 18)], [])]),
      generate(width=23, height=23, frame=8,
               panels=[(4, 1, 1, 13, 14), (2, 9, 9, 14, 14)],
               shape_color=1,
               shapes=[(3, 3, 3, 5, [(3, 6)], [(6, 5)]),
                       (13, 14, 6, 6, [(16, 14)], [(12, 16), (19, 18)])]),
      generate(width=20, height=20, frame=8,
               panels=[(3, 0, 0, 9, 10), (2, 9, 1, 10, 19)],
               shape_color=1,
               shapes=[(1, 2, 5, 6, [(3, 2), (5, 6)], []),
                       (11, 3, 6, 9, [(11, 8)], [(14, 12), (17, 6)])]),
  ]
  test = [
      generate(width=27, height=27, frame=4,
               panels=[(3, 9, 4, 17, 23), (1, 0, 1, 12, 22)],
               shape_color=8,
               shapes=[(3, 5, 5, 11, [(7, 7)], [(2, 9), (8, 12)]),
                       (1, 18, 4, 3, [], [(5, 19)]),
                       (16, 8, 7, 9, [(19, 8), (22, 11)], [(15, 11)]),
                       (14, 19, 9, 6, [(16, 19)], [(19, 25)])]),
  ]
  return {"train": train, "test": test}
