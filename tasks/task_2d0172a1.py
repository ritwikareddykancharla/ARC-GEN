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

"""ARC task 2d0172a1: draw the containment tree of loops and blobs.

Rule: the input holds one background colour and one foreground colour. The
foreground forms wobbly closed loops (which enclose background) and solid
blobs (no hole). The output is a schematic of the containment tree:
- every loop becomes an axis-aligned one-cell-thick rectangular frame,
- every blob becomes one dot,
- children of a loop are grouped into row / column bands wherever their input
  bounding boxes overlap vertically / horizontally. A blob occupies a 3x3 cell
  (dot in the middle), a loop occupies its children's layout plus padding and
  frame, neighbouring cells share their one-cell margin, and a dot beside a
  framed sibling is snapped to the unique nearest inner dot whose input extent
  overlaps it.
The drawing is cropped to the top-level frames and top-level dot cells.

Scope of the random generator: one or two top-level loops plus 0-2 outside
blobs; loops hold 1-3 children arranged in rows, columns, diagonals or L
shapes; children are blobs or inner loops, nesting up to four levels deep.
Loops are the 8-neighbour border of a rectangle with random corner and edge
notches (giving staircase walls like the originals). Blobs are 2-4 cell
rectangles with some corners removed. The answer is laid out directly from the
latent tree and the latent bounding boxes; the input is never parsed in the
random path.

Fixture replay: the original hand-drawn loops are impractical to describe with
latent parameters, so generate(input_grid=...) extracts the latent objects
(components, enclosure, parent) from a supplied grid and then uses the same
latent layout renderer. validate() uses only this replay option.
"""

import random

import common

_N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_N8 = tuple((dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)

_LAYOUTS = {
  1: [((0, 0),)],
  2: [((0, 0), (0, 1)), ((0, 0), (1, 0)), ((0, 0), (1, 1)),
      ((0, 1), (1, 0))],
  3: [((0, 0), (0, 1), (0, 2)), ((0, 0), (1, 0), (2, 0)),
      ((0, 0), (0, 1), (1, 0)), ((0, 0), (0, 1), (1, 1)),
      ((0, 0), (1, 0), (1, 1)), ((0, 1), (1, 0), (1, 1)),
      ((0, 0), (1, 1), (2, 2)), ((0, 2), (1, 1), (2, 0))],
}

_LAYOUTS[4] = [((0,0),(0,1),(1,0),(1,1)),
               ((0,0),(0,1),(0,2),(0,3)),
               ((0,0),(1,0),(2,0),(3,0))]

_STYLES = ("blob", "blobs", "nested", "twin", "deep", "pair")


def _connected4(cells):
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    y, x = stack.pop()
    for dy, dx in _N4:
      n = (y + dy, x + dx)
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _bbox(cells):
  ys = [y for y, _ in cells]
  xs = [x for _, x in cells]
  return (min(ys), min(xs), max(ys), max(xs))


def _node(kind, cells, kids=()):
  return {"kind": kind, "cells": set(cells), "kids": list(kids)}


def _shift(node, dy, dx):
  return {"kind": node["kind"],
          "cells": {(y + dy, x + dx) for y, x in node["cells"]},
          "kids": [_shift(k, dy, dx) for k in node["kids"]]}


def _walk(node):
  out = [node]
  for k in node["kids"]:
    out.extend(_walk(k))
  return out


def _make_blob():
  """A solid blob: small rectangle with some corners removed (no holes)."""
  for _ in range(50):
    h, w = random.randint(2, 3), random.randint(2, 4)
    if random.random() < 0.5:
      h, w = w, h
    cells = {(y, x) for y in range(h) for x in range(w)}
    corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    random.shuffle(corners)
    for c in corners:
      if random.random() < 0.4:
        trial = cells - {c}
        if _bbox(trial) == (0, 0, h - 1, w - 1) and _connected4(trial):
          cells = trial
    if len(cells) >= 3:
      return _node("blob", cells)
  raise RuntimeError("Could not construct a valid blob")


def _arrange(nodes, layout, gmax):
  """Place nodes into row/column bands separated by 1..gmax empty lines."""
  norm = []
  for n in nodes:
    y0, x0, _, _ = _bbox(n["cells"])
    norm.append(_shift(n, -y0, -x0))
  sizes = []
  for n in norm:
    b = _bbox(n["cells"])
    sizes.append((b[2] + 1, b[3] + 1))
  nr = 1 + max(r for r, _ in layout)
  nc = 1 + max(c for _, c in layout)
  rh, cw = [0] * nr, [0] * nc
  for (r, c), (h, w) in zip(layout, sizes):
    rh[r] = max(rh[r], h)
    cw[c] = max(cw[c], w)
  rs, cs = [], []
  y = 0
  for r in range(nr):
    rs.append(y)
    y += rh[r] + random.randint(1, gmax)
  x = 0
  for c in range(nc):
    cs.append(x)
    x += cw[c] + random.randint(1, gmax)
  placed = []
  for n, (r, c), (h, w) in zip(norm, layout, sizes):
    oy = rs[r] + random.randint(0, rh[r] - h)
    ox = cs[c] + random.randint(0, cw[c] - w)
    placed.append(_shift(n, oy, ox))
  return placed, rs[-1] + rh[-1], cs[-1] + cw[-1]


def _region_wall(region):
  wall = set()
  for (y, x) in region:
    for dy, dx in _N8:
      if (y + dy, x + dx) not in region:
        wall.add((y, x))
        break
  return wall


def _region_ok(region):
  wall = _region_wall(region)
  inner = region - wall
  if not inner or not _connected4(wall) or not _connected4(inner):
    return None
  for (y, x) in wall:
    if (y + 1, x) in wall and (y, x + 1) in wall and (y + 1, x + 1) in wall:
      return None
  return wall


def _random_notch(h, w):
  if random.random() < 0.55:
    a, b = random.randint(1, 3), random.randint(1, 3)
    corner = random.randrange(4)
    ys = range(a) if corner in (0, 1) else range(h - a, h)
    xs = range(b) if corner in (0, 2) else range(w - b, w)
  else:
    side = random.randrange(4)
    d = random.randint(1, 2)
    if side in (0, 1):
      length = random.randint(2, max(2, w // 2))
      s = random.randint(0, max(0, w - length))
      xs = range(s, s + length)
      ys = range(d) if side == 0 else range(h - d, h)
    else:
      length = random.randint(2, max(2, h // 2))
      s = random.randint(0, max(0, h - length))
      ys = range(s, s + length)
      xs = range(d) if side == 2 else range(w - d, w)
  return {(y, x) for y in ys for x in xs}


def _make_loop(kids):
  """Wrap children in a wobbly closed loop with >=1 empty cell of clearance."""
  kids = list(kids)
  random.shuffle(kids)
  layout = random.choice(_LAYOUTS[len(kids)])
  placed, ch, cw = _arrange(kids, layout, 2)
  mt, mb, ml, mr = [random.choice((2, 2, 3)) for _ in range(4)]
  h, w = mt + ch + mb, ml + cw + mr
  placed = [_shift(k, mt, ml) for k in placed]
  protected = set()
  for k in placed:
    y0, x0, y1, x1 = _bbox(k["cells"])
    for y in range(y0 - 2, y1 + 3):
      for x in range(x0 - 2, x1 + 3):
        protected.add((y, x))
  region = {(y, x) for y in range(h) for x in range(w)}
  wall = _region_wall(region)
  for _ in range(random.randint(2, 8)):
    notch = _random_notch(h, w)
    if notch & protected:
      continue
    trial = region - notch
    tw = _region_ok(trial)
    if tw is not None:
      region, wall = trial, tw
  y0, x0, _, _ = _bbox(wall)
  return _shift(_node("loop", wall, placed), -y0, -x0)


def _inner_loop(nb=None):
  if nb is None:
    nb = random.choice((1, 1, 2))
  return _make_loop([_make_blob() for _ in range(nb)])


def _sample_roots(style, outside):
  if style == "pair":
    mains = []
    for _ in range(2):
      if random.random() < 0.4:
        mains.append(_make_loop([_inner_loop(1)]))
      else:
        mains.append(_make_loop([_make_blob()
                                 for _ in range(random.randint(1, 2))]))
    m = outside if outside is not None else random.choice((0, 1))
    return mains + [_make_blob() for _ in range(m)]
  if style == "blob":
    kids = [_make_blob()]
  elif style == "blobs":
    kids = [_make_blob() for _ in range(random.randint(2, 3))]
  elif style == "nested":
    kids = [_inner_loop()] + [_make_blob()
                              for _ in range(random.choice((0, 1, 1, 2)))]
  elif style == "twin":
    kids = [_inner_loop(1), _inner_loop(1)]
    kids += [_make_blob() for _ in range(random.choice((0, 1)))]
  else:
    kids = [_make_loop([_inner_loop(1)])]
    kids += [_make_blob() for _ in range(random.choice((0, 1)))]
  m = outside if outside is not None else random.choice((0, 0, 1, 1, 2))
  return [_make_loop(kids)] + [_make_blob() for _ in range(m)]


def _touching(a, b):
  for ax in (0, 1):
    if a[ax] == b[ax + 2] + 1 or b[ax] == a[ax + 2] + 1:
      return True
  return False


def _group_ok(group):
  """Forbid projection-adjacent boxes that would make banding ambiguous."""
  boxes = [_bbox(n["cells"]) for n in group]
  for i in range(len(group)):
    for j in range(i + 1, len(group)):
      if _touching(boxes[i], boxes[j]):
        return False
  for i, leaf in enumerate(group):
    if leaf["kids"]:
      continue
    for other in group:
      if not other["kids"]:
        continue
      for d in _walk(other):
        if not d["kids"] and _touching(boxes[i], _bbox(d["cells"])):
          return False
  return all(_group_ok(n["kids"]) for n in group if n["kids"])


def _mv(p, dy, dx):
  if p[0] == "dot":
    return ("dot", p[1] + dy, p[2] + dx, p[3])
  return ("frame", p[1] + dy, p[2] + dx, p[3] + dy, p[4] + dx)


def _render(roots, bg, fg):
  """Lay out the latent containment tree as nested frames and dots."""
  info = {}
  for r in roots:
    for n in _walk(r):
      info[id(n)] = _bbox(n["cells"])

  def clusters(nodes, a):
    order = sorted(range(len(nodes)), key=lambda i: info[id(nodes[i])][a])
    idx, k, cur = [0] * len(nodes), -1, None
    for i in order:
      b = info[id(nodes[i])]
      if cur is None or b[a] > cur:
        k += 1
        cur = b[a + 2]
      else:
        cur = max(cur, b[a + 2])
      idx[i] = k
    return idx, k + 1

  def block(n):
    if not n["kids"]:
      return 3, 3, [("dot", 1, 1, n)]
    h, w, prims, _ = arrange(n["kids"])
    return h + 4, w + 4, [("frame", 1, 1, h + 2, w + 2)] + [
        _mv(p, 2, 2) for p in prims]

  def arrange(nodes):
    ri, nr = clusters(nodes, 0)
    ci, nc = clusters(nodes, 1)
    blocks = [block(n) for n in nodes]
    hs, ws = [1] * nr, [1] * nc
    for i in range(len(nodes)):
      hs[ri[i]] = max(hs[ri[i]], blocks[i][0])
      ws[ci[i]] = max(ws[ci[i]], blocks[i][1])
    rs, cs = [0], [0]
    for r in range(nr - 1):
      rs.append(rs[-1] + hs[r] - 1)
    for c in range(nc - 1):
      cs.append(cs[-1] + ws[c] - 1)
    total = (rs[-1] + hs[-1], cs[-1] + ws[-1])
    places = []
    for i in range(len(nodes)):
      bh, bw, _ = blocks[i]
      dy = (hs[ri[i]] - bh) // 2
      dy -= dy % 2
      dx = (ws[ci[i]] - bw) // 2
      dx -= dx % 2
      places.append((rs[ri[i]] + dy, cs[ci[i]] + dx))
    final = []
    for i, n in enumerate(nodes):
      pos = list(places[i])
      if not n["kids"]:
        ib = info[id(n)]
        for axis in (0, 1):
          band = ri if axis == 0 else ci
          choices = []
          for j, m in enumerate(nodes):
            if j == i or not m["kids"] or band[i] != band[j]:
              continue
            for p in blocks[j][2]:
              if p[0] != "dot":
                continue
              lb = info[id(p[3])]
              lo, hi = ib[axis], ib[axis + 2]
              alo, ahi = lb[axis], lb[axis + 2]
              if max(lo, alo) <= min(hi, ahi):
                choices.append((abs((lo + hi) - (alo + ahi)),
                                places[j][axis] + p[1 + axis]))
          if choices:
            best = min(c[0] for c in choices)
            anchors = {v for d, v in choices if d == best}
            if len(anchors) == 1:
              off = anchors.pop() - 1
              if 0 <= off <= total[axis] - 3:
                pos[axis] = off
      final.append((pos[0], pos[1]))
    prims = []
    for i in range(len(nodes)):
      for p in blocks[i][2]:
        prims.append(_mv(p, final[i][0], final[i][1]))
    return total[0], total[1], prims, [
        (nodes[i], final[i], blocks[i]) for i in range(len(nodes))]

  _, _, prims, places = arrange(roots)
  regions = []
  for n, (oy, ox), (bh, bw, _) in places:
    if n["kids"]:
      regions.append((oy + 1, ox + 1, oy + bh - 2, ox + bw - 2))
    else:
      regions.append((oy, ox, oy + bh - 1, ox + bw - 1))
  y0 = min(r[0] for r in regions)
  x0 = min(r[1] for r in regions)
  y1 = max(r[2] for r in regions)
  x1 = max(r[3] for r in regions)
  out = [[bg] * (x1 - x0 + 1) for _ in range(y1 - y0 + 1)]
  for p in prims:
    if p[0] == "dot":
      out[p[1] - y0][p[2] - x0] = fg
    else:
      a, b, c, d = p[1] - y0, p[2] - x0, p[3] - y0, p[4] - x0
      for x in range(b, d + 1):
        out[a][x] = fg
        out[c][x] = fg
      for y in range(a, c + 1):
        out[y][b] = fg
        out[y][d] = fg
  return out


def _parse(grid):
  """Fixture replay only: recover latent objects from a supplied grid."""
  h, w = len(grid), len(grid[0])
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  bg = max(counts, key=lambda c: counts[c])
  fg = min(c for c in counts if c != bg)
  fgcells = {(y, x) for y in range(h) for x in range(w) if grid[y][x] != bg}
  comps, seen = [], set()
  for y in range(h):
    for x in range(w):
      if (y, x) in fgcells and (y, x) not in seen:
        comp, stack = {(y, x)}, [(y, x)]
        seen.add((y, x))
        while stack:
          cy, cx = stack.pop()
          for dy, dx in _N4:
            n = (cy + dy, cx + dx)
            if n in fgcells and n not in seen:
              seen.add(n)
              comp.add(n)
              stack.append(n)
        comps.append(comp)
  encl = []
  for comp in comps:
    reach = set()
    stack = []
    for y in range(h):
      for x in range(w):
        if (y in (0, h - 1) or x in (0, w - 1)) and (y, x) not in comp:
          reach.add((y, x))
          stack.append((y, x))
    while stack:
      cy, cx = stack.pop()
      for dy, dx in _N4:
        n = (cy + dy, cx + dx)
        if 0 <= n[0] < h and 0 <= n[1] < w and n not in reach and n not in comp:
          reach.add(n)
          stack.append(n)
    encl.append({(y, x) for y in range(h) for x in range(w)
                 if (y, x) not in reach and (y, x) not in comp})
  nodes = [_node("blob", c) for c in comps]
  roots = []
  for i, comp in enumerate(comps):
    cell = next(iter(comp))
    best = None
    for j in range(len(comps)):
      if j != i and cell in encl[j]:
        if best is None or len(encl[j]) < len(encl[best]):
          best = j
    if best is None:
      roots.append(nodes[i])
    else:
      nodes[best]["kids"].append(nodes[i])
      nodes[best]["kind"] = "loop"
  return bg, fg, roots


def _build(roots, bg, fg, width=None, height=None):
  """Place roots on a canvas; returns input grid or None if invalid."""
  roots = list(roots)
  random.shuffle(roots)
  layout = random.choice(_LAYOUTS[len(roots)])
  placed, ch, cw = _arrange(roots, layout, 4)
  if ch > (height if height is not None else 30) or cw > (width if width is not None else 30):
    return None, None
  h = height if height is not None else random.randint(ch, min(30, ch + 10))
  w = width if width is not None else random.randint(cw, min(30, cw + 10))
  top, left = random.randint(0, h - ch), random.randint(0, w - cw)
  placed = [_shift(n, top, left) for n in placed]
  if not _group_ok(placed):
    return None, None
  grid = [list(row) for row in common.grid(w, h, bg)]
  owner = {}
  nodes = [d for n in placed for d in _walk(n)]
  for idx, n in enumerate(nodes):
    for c in n["cells"]:
      if c in owner:
        return None, None
      owner[c] = idx
      grid[c[0]][c[1]] = fg
  for (y, x), idx in owner.items():
    for dy, dx in _N8:
      o = owner.get((y + dy, x + dx))
      if o is not None and o != idx:
        return None, None
  if 2 * len(owner) >= h * w:
    return None, None
  for (y, x) in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
    if grid[y][x] != bg:
      return None, None
  return grid, placed


def generate(bg=None, fg=None, style=None, outside=None, input_grid=None,
             width=None, height=None):
  """Returns a containment-diagram example.

  Args:
    width: requested input width (up to 30); scene must fit.
    height: requested input height (up to 30); scene must fit.
    bg: background colour (0-9); random if None.
    fg: foreground colour (0-9, != bg); random if None.
    style: scene family, one of "blob" (loop with one blob), "blobs" (loop
      with 2-3 blobs), "nested" (loop with an inner loop and 0-2 blobs),
      "twin" (two inner loops), "deep" (three nested loops), "pair" (two
      top-level loops); random if None.
    outside: number of blobs outside every loop (0-2); random if None.
    input_grid: optional fixture replay grid; latent objects are extracted
      from it and rendered with the same layout routine.
  """
  if style is not None and style not in _STYLES:
    raise ValueError("Unknown containment style")
  if outside is not None and (not isinstance(outside, int) or not 0 <= outside <= 2):
    raise ValueError("outside must be in 0..2")
  for dimension in (width, height):
    if dimension is not None and (not isinstance(dimension, int) or not 1 <= dimension <= 30):
      raise ValueError("Dimensions must be integers in 1..30")
  if any(c is not None and c not in range(10) for c in (bg,fg)) or (bg is not None and fg is not None and bg == fg):
    raise ValueError("Foreground and background must be distinct colours in 0..9")
  if input_grid is not None:
    if style is not None or outside is not None:
      raise ValueError("Fixture replay does not accept random style/outside controls")
    if not input_grid or not input_grid[0] or max(len(input_grid),len(input_grid[0])) > 30 or any(len(row) != len(input_grid[0]) for row in input_grid):
      raise ValueError("Input must be rectangular and at most 30x30")
    if (width is not None and width != len(input_grid[0])) or (height is not None and height != len(input_grid)):
      raise ValueError("Replay grid does not match requested dimensions")
    palette = {v for row in input_grid for v in row}
    if len(palette) != 2 or any(v not in range(10) for v in palette):
      raise ValueError("Replay requires exactly two colours in 0..9")
    b, f, roots = _parse(input_grid)
    if (bg is not None and bg != b) or (fg is not None and fg != f):
      raise ValueError("Replay grid does not match requested colours")
    return {"input": [list(r) for r in input_grid],
            "output": _render(roots, b, f)}
  if bg is None:
    bg = random.choice([c for c in range(10) if c != fg])
  if fg is None:
    fg = random.choice([c for c in range(10) if c != bg])
  for attempt in range(300):
    if style in _STYLES:
      s = style
    else:
      s = random.choices(_STYLES, weights=(10, 17, 38, 10, 10, 15))[0]
    roots = _sample_roots(s, outside)
    grid, placed = _build(roots, bg, fg, width, height)
    if grid is None:
      continue
    out = _render(placed, bg, fg)
    if len(out) > 30 or len(out[0]) > 30:
      continue
    return {"input": grid, "output": out}
  raise RuntimeError("Could not construct requested containment scene")


_FIXTURES = {
  "train": [
    [[3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [4, 4, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [4, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3], [4, 3, 3, 4, 4, 3, 3, 3, 3, 4, 4, 3, 3, 3, 3, 4, 3, 3, 4, 4, 3, 3, 3, 3, 3], [4, 3, 3, 4, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 4, 3, 3, 4, 4, 4, 3, 3, 3, 3], [4, 3, 3, 4, 3, 4, 4, 4, 3, 3, 4, 3, 3, 3, 3, 4, 3, 3, 3, 4, 4, 3, 3, 3, 3], [4, 3, 4, 4, 3, 3, 4, 4, 3, 3, 4, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3], [4, 3, 3, 4, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3], [4, 3, 3, 4, 4, 3, 3, 3, 3, 4, 4, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [4, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [4, 4, 3, 3, 3, 4, 4, 4, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [3, 4, 3, 3, 3, 4, 4, 4, 3, 3, 3, 3, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], [3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]],
    [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 4, 4, 4, 4, 4, 4, 1, 1, 1, 1, 1], [1, 1, 1, 4, 4, 4, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1], [1, 1, 4, 4, 1, 1, 1, 4, 1, 1, 4, 1, 1, 1, 1, 1], [1, 1, 4, 1, 1, 4, 4, 4, 1, 1, 4, 1, 1, 1, 1, 1], [1, 1, 4, 1, 1, 4, 4, 4, 1, 1, 4, 1, 1, 1, 1, 1], [1, 1, 4, 1, 1, 1, 4, 1, 1, 1, 4, 1, 1, 1, 1, 1], [1, 1, 4, 1, 1, 1, 1, 1, 1, 4, 4, 1, 1, 1, 1, 1], [1, 1, 4, 4, 1, 1, 1, 4, 4, 4, 1, 1, 1, 1, 1, 1], [1, 1, 1, 4, 4, 4, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]],
    [[4, 4, 4, 4, 9, 9, 9, 9, 9, 9, 4, 4, 4, 4, 4, 4], [4, 4, 4, 9, 9, 4, 4, 4, 4, 9, 4, 4, 4, 4, 4, 4], [4, 9, 9, 9, 4, 4, 4, 4, 4, 9, 9, 4, 4, 4, 4, 4], [4, 9, 4, 4, 4, 4, 4, 4, 4, 4, 9, 4, 4, 4, 4, 4], [4, 9, 4, 4, 4, 9, 9, 4, 4, 4, 9, 4, 4, 4, 4, 4], [4, 9, 4, 4, 9, 9, 9, 4, 4, 4, 9, 4, 4, 4, 4, 4], [4, 9, 4, 4, 9, 9, 4, 4, 4, 4, 9, 4, 4, 4, 4, 4], [4, 9, 4, 4, 4, 4, 4, 4, 4, 4, 9, 4, 4, 4, 4, 4], [4, 9, 4, 4, 4, 4, 9, 4, 4, 4, 9, 4, 4, 4, 4, 4], [4, 9, 4, 4, 9, 9, 9, 4, 4, 9, 9, 4, 4, 4, 4, 4], [4, 9, 4, 4, 4, 9, 9, 4, 4, 9, 4, 4, 4, 4, 4, 4], [4, 9, 9, 4, 4, 4, 4, 4, 4, 9, 4, 4, 4, 4, 4, 4], [4, 4, 9, 4, 4, 4, 4, 4, 4, 9, 4, 4, 4, 4, 4, 4], [4, 9, 9, 4, 4, 4, 4, 4, 4, 9, 4, 4, 4, 4, 4, 4], [4, 9, 4, 4, 4, 4, 4, 4, 9, 9, 4, 4, 4, 4, 4, 4], [4, 9, 9, 9, 9, 4, 4, 9, 9, 4, 4, 4, 4, 4, 4, 4], [4, 4, 4, 4, 9, 9, 9, 9, 4, 4, 4, 4, 4, 4, 4, 4], [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4], [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4], [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]],
    [[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 4, 4, 4, 4, 4, 4, 2, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 4, 4, 4, 4, 4, 4, 4, 2, 2, 2, 2, 2, 4, 2, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 4, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 4, 2, 2, 2, 4, 4, 4, 4, 4, 4, 2, 2, 2, 4, 4, 4, 2, 2, 2, 2, 2], [2, 2, 2, 2, 4, 2, 2, 4, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 2, 4, 4, 2, 2, 2, 2], [2, 2, 2, 2, 4, 2, 2, 4, 2, 2, 4, 4, 2, 4, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 2], [2, 2, 2, 2, 4, 2, 2, 4, 2, 4, 4, 4, 2, 4, 2, 4, 4, 4, 2, 2, 4, 2, 2, 2, 2], [2, 2, 2, 2, 4, 4, 2, 4, 2, 4, 4, 4, 2, 4, 2, 4, 4, 2, 2, 2, 4, 2, 2, 2, 2], [2, 2, 2, 2, 2, 4, 2, 4, 2, 2, 2, 2, 2, 4, 2, 2, 2, 2, 2, 4, 4, 2, 2, 2, 2], [2, 2, 2, 2, 2, 4, 2, 4, 4, 4, 2, 2, 4, 4, 2, 2, 2, 4, 4, 4, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 4, 2, 2, 2, 4, 4, 4, 4, 2, 2, 2, 4, 4, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 4, 4, 2, 2, 2, 2, 2, 2, 2, 2, 4, 4, 2, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]],
  ],
  "test": [
    [[7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 9, 9, 9, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7], [7, 7, 7, 7, 9, 9, 9, 9, 9, 9, 9, 9, 7, 9, 9, 9, 9, 9, 7, 7, 7, 7, 7, 7, 7], [7, 7, 9, 9, 9, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 9, 9, 7, 7, 7, 7, 7, 7], [7, 9, 9, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 9, 9, 9, 7, 7, 7, 7], [7, 9, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 9, 9, 9, 7, 7], [7, 9, 7, 7, 7, 7, 9, 9, 9, 9, 9, 9, 9, 7, 7, 7, 7, 7, 7, 7, 7, 7, 9, 9, 7], [7, 9, 7, 7, 7, 9, 9, 7, 7, 7, 7, 7, 9, 9, 9, 9, 9, 9, 7, 7, 7, 7, 7, 9, 9], [7, 9, 7, 7, 9, 9, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 9, 7, 7, 7, 7, 7, 7, 9], [7, 9, 7, 7, 9, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 9, 9, 7, 9, 9, 7, 7, 9], [7, 9, 7, 7, 9, 7, 7, 9, 9, 7, 7, 7, 9, 9, 9, 9, 7, 7, 9, 7, 9, 9, 7, 7, 9], [7, 9, 7, 7, 9, 7, 7, 9, 9, 9, 7, 7, 9, 9, 9, 9, 7, 7, 9, 7, 7, 7, 7, 7, 9], [7, 9, 7, 7, 9, 7, 7, 7, 9, 9, 7, 7, 9, 9, 9, 7, 7, 9, 9, 7, 7, 7, 7, 7, 9], [7, 9, 7, 7, 9, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 9, 9, 7, 7, 7, 7, 7, 7, 9], [7, 9, 7, 7, 9, 9, 9, 7, 7, 7, 7, 7, 7, 7, 9, 9, 9, 7, 7, 7, 7, 7, 7, 9, 9], [7, 9, 9, 7, 7, 7, 9, 9, 9, 9, 9, 9, 9, 9, 9, 7, 7, 7, 7, 7, 7, 7, 7, 9, 7], [7, 7, 9, 9, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 9, 9, 9, 7], [7, 7, 7, 9, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 9, 9, 9, 9, 9, 7, 7, 7], [7, 7, 7, 9, 9, 7, 7, 7, 7, 7, 7, 7, 9, 9, 9, 9, 9, 9, 7, 7, 7, 7, 7, 7, 7], [7, 7, 7, 7, 9, 9, 9, 9, 9, 9, 9, 9, 9, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7], [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7], [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7], [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7], [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7], [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7], [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7]],
    [[8, 8, 8, 8, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 8, 8, 8, 8, 8, 8, 8], [8, 6, 6, 6, 6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 6, 6, 8, 8, 8, 8, 8], [6, 6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 6, 8, 8, 8, 8], [6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 6, 6, 8, 8, 8, 8, 8, 8, 8, 6, 8, 8, 8, 8], [6, 8, 8, 8, 8, 8, 8, 8, 8, 6, 6, 6, 6, 8, 8, 8, 8, 8, 8, 8, 6, 8, 8, 8, 8], [6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 8, 8, 8, 8], [6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 6, 8, 8, 8], [6, 8, 8, 8, 8, 8, 8, 8, 6, 6, 6, 6, 6, 6, 6, 8, 8, 8, 8, 8, 8, 6, 8, 8, 8], [6, 8, 8, 8, 8, 8, 8, 8, 6, 8, 8, 8, 8, 8, 6, 6, 8, 8, 8, 8, 8, 6, 8, 8, 8], [6, 8, 6, 6, 6, 8, 8, 8, 6, 8, 6, 6, 6, 8, 8, 6, 8, 8, 8, 8, 8, 6, 8, 8, 8], [6, 8, 6, 6, 6, 8, 8, 8, 6, 8, 6, 6, 6, 8, 8, 6, 8, 8, 8, 8, 6, 6, 8, 8, 8], [6, 8, 8, 6, 6, 8, 8, 8, 6, 8, 8, 6, 8, 8, 6, 6, 8, 8, 8, 8, 6, 8, 8, 8, 8], [6, 8, 8, 8, 8, 8, 8, 8, 6, 6, 8, 8, 8, 6, 6, 8, 8, 8, 8, 8, 6, 8, 8, 8, 8], [6, 8, 8, 8, 8, 8, 8, 8, 8, 6, 6, 6, 6, 6, 8, 8, 8, 8, 8, 6, 6, 8, 8, 8, 8], [6, 6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 8, 8, 8, 8, 8], [8, 6, 6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 6, 8, 8, 8, 8, 8], [8, 8, 6, 6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 8, 8, 8, 8, 8, 8], [8, 8, 8, 6, 6, 6, 6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 6, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 8, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 6, 6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 6, 6, 6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8]],
  ],
}


def validate():
  """Replays the original fixtures through generate(input_grid=...)."""
  return {split: [generate(input_grid=g) for g in grids]
          for split, grids in _FIXTURES.items()}
