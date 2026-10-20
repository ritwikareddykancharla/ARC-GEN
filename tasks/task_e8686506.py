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
"""Task e8686506: slot the loose pieces into the holes of a hollow figure.

Rule: the input holds one large hollow figure, the frame. The frame is
left-right symmetric and has one or two colours. It need not be connected:
pair 1's frame is two mirror halves that do not touch even diagonally. The
frame colours are the colours of the largest 8-connected multicolour object,
and every cell of those colours belongs to the frame. The frame's bounding
box contains background holes. Small monochrome pieces in other colours lie
scattered outside it. Moved by translation only, the pieces tile the holes
exactly, and the resulting colouring is unique. The output is the frame's
bounding box with every hole filled.

Scope:
- Random frames are masks of 3-8 columns by 4-10 rows. The fixtures only
  use 5-wide frames, so other widths are a synthetic extension.
- The mask is left-right symmetric and optionally also top-bottom symmetric.
  Every 8-connected frame fragment has at least 3 cells, and there are at
  most 4 fragments. Frames therefore stay outline-like, and they may be split
  into separate mirror halves as in pair 1.
- The frame has one colour, or two colours split at a row (as in pair 2).
- The holes are split into mirror orbits of 4-connected pieces. Colours are
  assigned to classes: pieces in one mirror orbit share a colour, and pieces
  of identical shape always share a colour. Mirror-image shapes in one orbit,
  such as the test's upward and downward T pieces, share a colour while
  having different shapes. Two equal shapes in different colours could
  always swap places, so such a scene could never have a unique colouring.
  That configuration does not exist in this task.
- In about half of random scenes, same-coloured pieces are forbidden from
  being 4-adjacent in the output, as in the fixtures. The other half applies
  no such filter. That is a synthetic extension.
- An unpinned input dimension is drawn from max(10, frame extent + 5)..20. A
  pinned width or height may be 10-30. When a dimension is pinned, the frame
  extent along it is capped at that dimension minus 5. Sizes other than 13
  and 15 are synthetic extensions.
- Random-scene pieces lie outside the frame bounding box plus a 1-cell ring.
  Explicit scenes need only lie outside the bounding box, away from frame
  cells and away from other pieces (even diagonally). Pair 2's 6-bar touches
  the ring, so the ring cannot be required there.
- Not supported: pieces sharing a frame colour, pieces inside the frame's
  bounding box, rotated or reflected pieces, asymmetric frames.

Random-generation controls: when frame is None, background, width and height
may be pinned. Passing frame_origin or pieces without a frame raises
ValueError. An explicit frame requires every scene argument. It is then
type-checked and validated before rendering with these checks:
- left-right frame symmetry;
- holes exactly partitioned;
- every piece one 4-connected component;
- pieces in bounds, disjoint and separated;
- piece colours distinct from frame and background;
- unique colouring;
- frame colours recoverable;
- strict background majority;
- a bounded naive search in input-scan order.

The constraints keep the scene well posed:
- The hole colouring is unique.
- The frame's colours are recoverable: every largest 8-connected frame part is
  bigger than any piece and carries every frame colour.
- The background is strictly the most frequent input colour.
- Random scenes have 3-10 pieces, with at most 4 copies of any
  (colour, shape).
- A naive first-hole backtracking search over the pieces (no deduplication)
  finishes within a node budget. Random scenes check several piece orders,
  including the row-major order of first cells and random permutations.
  Explicit scenes check the scan order and its reverse.
"""

import random

import common


_N4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_N8 = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _int_pair(v, name):
  if (not isinstance(v, (list, tuple)) or len(v) != 2 or
      not all(_is_int(x) for x in v)):
    raise ValueError("%s must be a pair of ints" % name)
  return (v[0], v[1])


def _norm(cells):
  """Translate cells so the first (row-major) cell sits at (0, 0)."""
  cells = sorted(cells)
  r0, c0 = cells[0]
  return tuple((r - r0, c - c0) for r, c in cells)


def _components(cells, diagonal):
  remaining = set(cells)
  steps = _N8 if diagonal else _N4
  comps = []
  while remaining:
    start = min(remaining)
    remaining.discard(start)
    stack = [start]
    comp = [start]
    while stack:
      r, c = stack.pop()
      for dr, dc in steps:
        n = (r + dr, c + dc)
        if n in remaining:
          remaining.discard(n)
          stack.append(n)
          comp.append(n)
    comps.append(sorted(comp))
  return comps


def _count_tilings(holes, plist, limit=2, budget=5000):
  """Count distinct colourings of holes by translated pieces (capped)."""
  types = {}
  for key in plist:
    types[key] = types.get(key, 0) + 1
  keys = list(types)
  found = set()
  assign = {}
  nodes = [0]

  def rec(remaining):
    if len(found) >= limit or nodes[0] > budget:
      return
    nodes[0] += 1
    if not remaining:
      found.add(tuple(sorted(assign.items())))
      return
    hy, hx = min(remaining)
    for key in keys:
      if types[key] == 0:
        continue
      cells = [(hy + dr, hx + dc) for dr, dc in key[1]]
      if all(c in remaining for c in cells):
        types[key] -= 1
        for c in cells:
          assign[c] = key[0]
        rec(remaining - set(cells))
        for c in cells:
          del assign[c]
        types[key] += 1

  rec(frozenset(holes))
  if nodes[0] > budget:
    return None
  return len(found)


def _naive_cost_ok(holes, rels, budget=3000):
  """Check that an index-based first-hole search (no dedup) stays bounded."""
  n = len(rels)
  used = [False] * n
  nodes = [0]

  def solve(remaining):
    nodes[0] += 1
    if nodes[0] > budget:
      return True
    if not remaining:
      return True
    hy, hx = min(remaining)
    for i in range(n):
      if used[i]:
        continue
      cells = [(hy + dr, hx + dc) for dr, dc in rels[i]]
      if all(c in remaining for c in cells):
        used[i] = True
        if solve(remaining - set(cells)):
          return True
        used[i] = False
    return False

  solve(frozenset(holes))
  return nodes[0] <= budget


def _put(g, r, c, v):
  if not (0 <= r < len(g) and 0 <= c < len(g[0])):
    raise ValueError("cell (%d, %d) is out of bounds" % (r, c))
  g[r][c] = v


def _render(background, width, height, frame, frame_origin, pieces):
  fh, fw = len(frame), len(frame[0])
  inp = common.grid(width, height, background)
  out = common.grid(fw, fh, background)
  r0, c0 = frame_origin
  for r, row in enumerate(frame):
    for c, ch in enumerate(row):
      if ch != ".":
        _put(inp, r0 + r, c0 + c, int(ch))
        _put(out, r, c, int(ch))
  for colour, rel, (ir, ic), (orr, oc) in pieces:
    for dr, dc in rel:
      _put(inp, ir + dr, ic + dc, colour)
      _put(out, orr + dr, oc + dc, colour)
  return {"input": inp, "output": out}


def _majority_ok(grid, bg):
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  return all(v == bg or k < counts.get(bg, 0) for v, k in counts.items())


def _frame_recoverable(frame_cell_colour, fcols, max_piece):
  comps = _components(list(frame_cell_colour), True)
  if not comps:
    return False
  big = max(len(c) for c in comps)
  if big <= max_piece:
    return False
  for comp in comps:
    if len(comp) == big:
      if {frame_cell_colour[cell] for cell in comp} != set(fcols):
        return False
  return True


def _coerce_explicit(background, width, height, frame, frame_origin, pieces):
  """Type-check explicit arguments and return normalized copies."""
  for name, v in (("background", background), ("width", width),
                  ("height", height)):
    if not _is_int(v):
      raise ValueError("%s must be an int" % name)
  if not 0 <= background <= 9:
    raise ValueError("background must be a colour 0-9")
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("width and height must be in 1..30")
  if (not isinstance(frame, (list, tuple)) or not frame or
      not all(isinstance(row, str) for row in frame) or
      not frame[0] or any(len(row) != len(frame[0]) for row in frame)):
    raise ValueError("frame must be a non-empty rectangle of strings")
  frame = list(frame)
  origin = _int_pair(frame_origin, "frame_origin")
  if not isinstance(pieces, (list, tuple)) or not pieces:
    raise ValueError("pieces must be a non-empty list")
  norm_pieces = []
  for p in pieces:
    if not isinstance(p, (list, tuple)) or len(p) != 4:
      raise ValueError("each piece is (colour, rel_cells, in_anchor, "
                       "out_anchor)")
    colour, rel, ia, oa = p
    if not _is_int(colour) or not 0 <= colour <= 9:
      raise ValueError("piece colour must be an int 0-9")
    if not isinstance(rel, (list, tuple)) or not rel:
      raise ValueError("rel_cells must be a non-empty list of offsets")
    rel = tuple(_int_pair(x, "rel offset") for x in rel)
    norm_pieces.append((colour, rel, _int_pair(ia, "input anchor"),
                        _int_pair(oa, "output anchor")))
  return background, width, height, frame, origin, norm_pieces


def _check_explicit(background, width, height, frame, frame_origin, pieces):
  """Reject explicit scenes that would render an inconsistent pair."""
  fh, fw = len(frame), len(frame[0])
  r0, c0 = frame_origin
  if r0 < 0 or c0 < 0 or r0 + fh > height or c0 + fw > width:
    raise ValueError("frame does not fit in the input grid")
  if any(row != row[::-1] for row in frame):
    raise ValueError("frame must be left-right symmetric")
  holes = set()
  fcell_col = {}
  fcols = set()
  for r, row in enumerate(frame):
    for c, ch in enumerate(row):
      if ch == ".":
        holes.add((r, c))
      elif ch in "0123456789":
        fcols.add(int(ch))
        fcell_col[(r0 + r, c0 + c)] = int(ch)
      else:
        raise ValueError("frame cells must be digits or '.'")
  if not holes:
    raise ValueError("frame has no holes")
  if background in fcols:
    raise ValueError("frame colour equals background")
  if (all(ch == "." for ch in frame[0]) or
      all(ch == "." for ch in frame[-1]) or
      all(row[0] == "." for row in frame) or
      all(row[-1] == "." for row in frame)):
    raise ValueError("frame mask must touch all four sides of its box")
  halo = set()
  for r, c in fcell_col:
    for dr, dc in _N8:
      halo.add((r + dr, c + dc))
  covered = set()
  for colour, rel, (ir, ic), (orr, oc) in pieces:
    if colour == background or colour in fcols:
      raise ValueError("piece colour collides with background or frame")
    if len(set(rel)) != len(rel) or min(rel) != (0, 0):
      raise ValueError("rel_cells must be distinct offsets from first cell")
    if len(_components(rel, False)) != 1:
      raise ValueError("each piece must be one 4-connected component")
    for dr, dc in rel:
      oc_cell = (orr + dr, oc + dc)
      if oc_cell not in holes or oc_cell in covered:
        raise ValueError("output piece cells must partition the holes")
      covered.add(oc_cell)
    icells = [(ir + dr, ic + dc) for dr, dc in rel]
    for r, c in icells:
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError("input piece lies outside the grid")
      if r0 <= r < r0 + fh and c0 <= c < c0 + fw:
        raise ValueError("input piece lies inside the frame bounding box")
      if (r, c) in halo:
        raise ValueError("input piece touches the frame or another piece")
    for r, c in icells:
      for dr, dc in _N8:
        halo.add((r + dr, c + dc))
      halo.add((r, c))
  if covered != holes:
    raise ValueError("some holes are left unfilled")
  max_piece = max(len(p[1]) for p in pieces)
  if not _frame_recoverable(fcell_col, fcols, max_piece):
    raise ValueError("largest frame part must exceed every piece and carry "
                     "every frame colour")
  plist = [(p[0], p[1]) for p in pieces]
  if _count_tilings(holes, plist) != 1:
    raise ValueError("hole colouring is not unique (or search too costly)")
  scan = sorted(pieces, key=lambda p: p[2])
  for order in (scan, scan[::-1]):
    if not _naive_cost_ok(holes, [p[1] for p in order], budget=20000):
      raise ValueError("naive tiling search is too costly for this scene")


def _place(wide, tall, piece_cells, width=None, height=None):
  order = sorted(range(len(piece_cells)), key=lambda i: -len(piece_cells[i]))
  for _ in range(30):
    w = width if width is not None else random.randint(max(10, wide + 5), 20)
    h = height if height is not None else random.randint(max(10, tall + 5), 20)
    if wide > w or tall > h:
      return None
    r0 = random.randint(0, h - tall)
    c0 = random.randint(0, w - wide)
    blocked = {(r, c) for r in range(r0 - 1, r0 + tall + 1)
               for c in range(c0 - 1, c0 + wide + 1)}
    anchors = [None] * len(piece_cells)
    ok = True
    for i in order:
      rel = _norm(piece_cells[i])
      mindc = min(dc for _, dc in rel)
      maxdc = max(dc for _, dc in rel)
      maxdr = max(dr for dr, _ in rel)
      spots = [(ar, ac) for ar in range(0, h - maxdr)
               for ac in range(-mindc, w - maxdc)
               if not any((ar + dr, ac + dc) in blocked for dr, dc in rel)]
      if not spots:
        ok = False
        break
      ar, ac = random.choice(spots)
      anchors[i] = (ar, ac)
      for dr, dc in rel:
        for er in (-1, 0, 1):
          for ec in (-1, 0, 1):
            blocked.add((ar + dr + er, ac + dc + ec))
    if ok:
      return w, h, (r0, c0), anchors
  return None


def _colour_classes(piece_cells, orbit_of):
  """Union pieces sharing a mirror orbit or an identical shape."""
  n = len(piece_cells)
  parent = list(range(n))

  def find(i):
    while parent[i] != i:
      parent[i] = parent[parent[i]]
      i = parent[i]
    return i

  first_orbit = {}
  first_shape = {}
  for i in range(n):
    for table, key in ((first_orbit, orbit_of[i]),
                       (first_shape, _norm(piece_cells[i]))):
      if key in table:
        parent[find(i)] = find(table[key])
      else:
        table[key] = i
  return [find(i) for i in range(n)]


def _random_scene(background=None, width=None, height=None):
  wmax = 8 if width is None else min(8, width - 5)
  hmax = 10 if height is None else min(10, height - 5)
  for _ in range(3000):
    wide = random.randint(3, wmax)
    tall = random.randint(4, hmax)
    vsym = random.random() < 0.5
    hw = (wide + 1) // 2
    hh = (tall + 1) // 2 if vsym else tall

    def dom(r, c):
      return (min(r, tall - 1 - r) if vsym else r, min(c, wide - 1 - c))

    dmask = {}
    for r in range(hh):
      for c in range(hw):
        border = r == 0 or c == 0 or (not vsym and r == tall - 1)
        dmask[(r, c)] = random.random() < (0.7 if border else 0.4)
    full = {(r, c): dmask[dom(r, c)]
            for r in range(tall) for c in range(wide)}
    if not any(full[(0, c)] for c in range(wide)):
      continue
    if not any(full[(tall - 1, c)] for c in range(wide)):
      continue
    if not any(full[(r, 0)] for r in range(tall)):
      continue
    holes = sorted(k for k, v in full.items() if not v)
    frame_cells = sorted(k for k, v in full.items() if v)
    if not 4 <= len(holes) <= 28:
      continue
    comps = _components(frame_cells, True)
    if len(comps) > 4 or min(len(c) for c in comps) < 3:
      continue

    dholes = [k for k, v in dmask.items() if not v]
    random.shuffle(dholes)
    label = {}
    nl = 0
    for cell in dholes:
      if cell in label:
        continue
      target = random.choice([1, 2, 2, 3, 3, 4, 4, 5])
      region = [cell]
      label[cell] = nl
      while len(region) < target:
        cand = []
        for r, c in region:
          for dr, dc in _N4:
            n = (r + dr, c + dc)
            if n in dmask and not dmask[n] and n not in label:
              cand.append(n)
        if not cand:
          break
        n = random.choice(cand)
        label[n] = nl
        region.append(n)
      nl += 1

    piece_cells, orbit_of = [], []
    for lab in range(nl):
      pre = [cell for cell in holes if label[dom(*cell)] == lab]
      for comp in _components(pre, False):
        piece_cells.append(comp)
        orbit_of.append(lab)
    if not 3 <= len(piece_cells) <= 10:
      continue
    max_piece = max(len(p) for p in piece_cells)
    if max_piece > 8:
      continue

    bg = random.randint(0, 9) if background is None else background
    palette = [c for c in range(10) if c != bg]
    random.shuffle(palette)
    nfc = random.choice([1, 1, 2])
    fcols = palette[:nfc]
    pcols = palette[nfc:]
    cls = _colour_classes(piece_cells, orbit_of)
    roots = sorted(set(cls))
    random.shuffle(roots)
    if len(roots) > len(pcols):
      continue
    root_col = {root: pcols[k] for k, root in enumerate(roots)}
    colours = [root_col[cls[i]] for i in range(len(piece_cells))]

    plist = [(colours[i], _norm(comp)) for i, comp in enumerate(piece_cells)]
    mult = {}
    for key in plist:
      mult[key] = mult.get(key, 0) + 1
    if max(mult.values()) > 4:
      continue

    if random.random() < 0.5:
      # Fixture-like variant: same-coloured pieces never abut in the output.
      owner = {}
      for i, comp in enumerate(piece_cells):
        for cell in comp:
          owner[cell] = i
      bad = False
      for (r, c), i in owner.items():
        for dr, dc in _N4:
          j = owner.get((r + dr, c + dc))
          if j is not None and j != i and colours[j] == colours[i]:
            bad = True
      if bad:
        continue

    split = random.randint(1, tall - 1)

    def fcol_of(r):
      return fcols[0] if nfc == 1 or r < split else fcols[1]

    fcell_col = {cell: fcol_of(cell[0]) for cell in frame_cells}
    if not _frame_recoverable(fcell_col, fcols, max_piece):
      continue

    if _count_tilings(holes, plist) != 1:
      continue

    placed = _place(wide, tall, piece_cells, width, height)
    if placed is None:
      continue
    w, h, origin, anchors = placed
    n = len(piece_cells)
    scan = sorted(range(n), key=lambda i: anchors[i])
    orders = [
        scan,
        list(reversed(scan)),
        sorted(range(n), key=lambda i: (colours[i], anchors[i])),
        sorted(range(n), key=lambda i: (-len(piece_cells[i]), anchors[i])),
        sorted(range(n), key=lambda i: (len(piece_cells[i]), anchors[i])),
        sorted(range(n), key=lambda i: (anchors[i][1], anchors[i][0])),
    ]
    for _ in range(2):
      perm = list(range(n))
      random.shuffle(perm)
      orders.append(perm)
    if not all(_naive_cost_ok(holes, [plist[i][1] for i in order])
               for order in orders):
      continue
    frame = ["".join(str(fcol_of(r)) if full[(r, c)] else "."
                     for c in range(wide)) for r in range(tall)]
    pieces = [(colours[i], _norm(comp), anchors[i], comp[0])
              for i, comp in enumerate(piece_cells)]
    scene = {"background": bg, "width": w, "height": h,
             "frame": frame, "frame_origin": origin, "pieces": pieces}
    pair = _render(**scene)
    if not _majority_ok(pair["input"], bg):
      continue
    return scene
  raise RuntimeError("could not build a scene for the requested controls")


def generate(background=None, width=None, height=None, frame=None,
             frame_origin=None, pieces=None):
  """Build one input/output pair.

  Args:
    background: background colour of the input grid (int 0-9). It is honoured
      in random mode.
    width: input grid width. In random mode it may be pinned to 10-30; when
      unpinned it is drawn from max(10, frame width + 5)..20.
    height: input grid height. In random mode it may be pinned to 10-30; when
      unpinned it is drawn from max(10, frame height + 5)..20.
    frame: list of strings, one per row of the output-shaped frame. A digit is
      a frame cell of that colour; '.' is a hole. Must be left-right
      symmetric.
    frame_origin: (row, col) of the frame's top-left corner in the input.
    pieces: list of (colour, rel_cells, input_anchor, output_anchor). rel_cells
      are offsets from the piece's first row-major cell and must form one
      4-connected shape. Each anchor is the position of that first cell in
      the input grid or the output grid.

  If frame is None, a fresh random scene is sampled, respecting any pinned
  background, width or height. Passing frame_origin or pieces without a frame
  raises ValueError. With an explicit frame every argument is required. The
  scene is type-checked and checked for consistency and well-posedness before
  rendering.
  """
  if frame is None:
    if frame_origin is not None or pieces is not None:
      raise ValueError("frame_origin and pieces require an explicit frame")
    if background is not None and not (_is_int(background) and
                                       0 <= background <= 9):
      raise ValueError("background must be an int colour 0-9")
    for name, value in (("width", width), ("height", height)):
      if value is not None and not (_is_int(value) and 10 <= value <= 30):
        raise ValueError("%s must be an int in 10..30 for random scenes" % name)
    return _render(**_random_scene(background, width, height))
  if any(v is None for v in (background, width, height, frame_origin, pieces)):
    raise ValueError("an explicit frame needs background, width, height, "
                     "frame_origin and pieces")
  args = _coerce_explicit(background, width, height, frame, frame_origin,
                          pieces)
  _check_explicit(*args)
  pair = _render(*args)
  if not _majority_ok(pair["input"], args[0]):
    raise ValueError("background must be strictly the most frequent colour")
  return pair


def validate():
  dot = ((0, 0),)
  v2 = ((0, 0), (1, 0))
  v4 = ((0, 0), (1, 0), (2, 0), (3, 0))
  train = [
      generate(background=8, width=13, height=13,
               frame=["33.33", "3...3", "3...3", ".3.3.", "33.33"],
               frame_origin=(3, 2),
               pieces=[(4, dot, (1, 5), (0, 2)),
                       (4, dot, (3, 9), (3, 0)),
                       (4, dot, (6, 11), (3, 4)),
                       (1, ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
                        (10, 2), (1, 1)),
                       (6, v2, (10, 8), (3, 2))]),
      generate(background=3, width=13, height=13,
               frame=[".111.", "1...1", "11.11", ".1.1.",
                      ".2.2.", "22.22", "2...2", ".222."],
               frame_origin=(3, 2),
               pieces=[(6, v2, (1, 1), (3, 0)),
                       (6, v2, (11, 1), (3, 4)),
                       (8, ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
                        (1, 8), (1, 1)),
                       (5, dot, (3, 11), (0, 0)),
                       (5, dot, (5, 8), (0, 4)),
                       (5, dot, (11, 10), (7, 0)),
                       (5, dot, (12, 7), (7, 4)),
                       (4, ((0, 0), (1, 0), (2, -1), (2, 0), (2, 1)),
                        (7, 10), (4, 2))]),
  ]
  test = [
      generate(background=4, width=15, height=15,
               frame=[".888.", "8...8", ".8.8.", ".8.8.",
                      ".8.8.", ".8.8.", "8...8", ".888."],
               frame_origin=(2, 4),
               pieces=[(1, dot, (0, 1), (0, 0)),
                       (1, dot, (4, 10), (0, 4)),
                       (1, dot, (8, 12), (7, 0)),
                       (1, dot, (13, 4), (7, 4)),
                       (3, v4, (3, 2), (2, 0)),
                       (3, v4, (10, 1), (2, 4)),
                       (6, ((0, 0), (0, 1), (0, 2), (1, 1)), (2, 12), (1, 1)),
                       (6, ((0, 0), (1, -1), (1, 0), (1, 1)), (12, 11), (5, 2)),
                       (9, v2, (11, 7), (3, 2))]),
  ]
  return {"train": train, "test": test}
