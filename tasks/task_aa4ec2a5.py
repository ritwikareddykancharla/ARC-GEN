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

"""ARC-GEN style generator for task aa4ec2a5.

Rule: the background is colour 4. Every shape is a 4-connected blob of
colour 1. The output applies two treatments:
  * Outline. A background cell becomes 2 if it is 4-reachable from the
    grid border and touches a shape cell orthogonally or diagonally.
  * Holes. A pocket is background that is not 4-reachable from the
    border. Every shape that encloses at least one pocket becomes 8, and
    its pocket cells become 6. Shapes without a pocket stay 1.
Pockets never receive the outline.

Scope in random mode:
  * Scenes have 2..6 shapes on grids of 8..30 cells per side. Default
    sides are sampled from max(12, 6 + 3n)..30.
  * Every scene has at least one holed shape and at least one shape with
    no pocket.
  * Each shape is a union of axis-aligned rectangles inside a sampled box
    whose sides are at most 14.
  * A holed shape has one or two hole rectangles with sides of at most 4.
    Two holes may merge into one irregular pocket or stay as two pockets.
    An extra pocket may also be walled in by extension rectangles.
  * The scenes include topological distractors:
      - Open rings. A ring is breached by a straight 1-cell channel to
        its bounding-box edge, so it encloses nothing and stays 1.
      - Shallow exterior notches.
      - Diagonal-only leaks. A ring's outer corner cell is removed, so a
        pocket touches the outside only diagonally. Under 4-connectivity
        it is still enclosed, so it becomes 6.
  * Placement is constructive. The interior is split into shelves of
    slots, separated by full one-cell gap lines. This guarantees that
    shapes never touch (even diagonally), never nest and never reach the
    border.
  * A budget on box areas keeps background the strict majority colour.
  * A requested size and count must pass both of these checks:
      - the same deterministic shelf packing that the generator uses as
        its fallback;
      - the area bound (w-1)*(h-1) >= 20*n.
    Infeasible requests raise ValueError and are not retried.

Not supported: shapes inside another shape's pocket (nesting), shapes
that touch each other or the grid border, colours other than 1 and 4 in
the input, and more than 6 shapes in random mode.

Explicit mode rebuilds a scene from latent rectangles; validate() uses
it. In both modes the output is painted from the latent cells and the
declared holes. The scene is then checked independently with a
4-connected flood fill from the border. It is rejected unless all of
these hold:
  * the declared holes are exactly the enclosed background;
  * each pocket borders only the shape that declares it;
  * at least one holed shape and one non-holed shape are present;
  * colour 4 is the strict majority of the input.
The canonical fixtures satisfy all of these, so no exception is needed.

common.grid(width, height, color) takes the width first. It returns
`height` rows of `width` cells.
"""

import random

import common

BG = 4
SHAPE = 1
OUTLINE = 2
HOLED = 8
HOLE = 6
MIN_RANDOM_SIDE = 8
MAX_SIDE = 30
MIN_SHAPES = 2
MAX_SHAPES = 6
AREA_PER_SHAPE = 20
MAX_BOX = 14
MIN_SIZE = {"holed": 3, "open": 3, "solid": 1}
KIND_POOL = ("holed", "holed", "solid", "solid", "open")
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _is_int(value):
  return isinstance(value, int) and not isinstance(value, bool)


def _rect_cells(rect):
  r, c, h, w = rect
  return {(r + i, c + j) for i in range(h) for j in range(w)}


def _cells_of(rects):
  out = set()
  for rect in rects:
    out |= _rect_cells(rect)
  return out


def _shape_sets(shape):
  """Returns (cells, holes) of a latent shape description."""
  union = _cells_of(shape["rects"])
  holes = _cells_of(shape.get("holes", [])) & union
  notches = _cells_of(shape.get("notches", []))
  holes -= notches
  cells = union - holes - notches
  return cells, holes


def _connected(cells):
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr, dc in N4:
      n = (r + dr, c + dc)
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _components(cells):
  """4-connected components of a set of cells."""
  todo = set(cells)
  comps = []
  while todo:
    start = todo.pop()
    comp = {start}
    stack = [start]
    while stack:
      r, c = stack.pop()
      for dr, dc in N4:
        n = (r + dr, c + dc)
        if n in todo:
          todo.remove(n)
          comp.add(n)
          stack.append(n)
    comps.append(comp)
  return comps


def _outside(width, height, occupied):
  """Background cells 4-reachable from the grid border."""
  seen = set()
  stack = []
  for r in range(height):
    for c in range(width):
      if ((r in (0, height - 1) or c in (0, width - 1)) and
          (r, c) not in occupied):
        seen.add((r, c))
        stack.append((r, c))
  while stack:
    r, c = stack.pop()
    for dr, dc in N4:
      nr, nc = r + dr, c + dc
      if 0 <= nr < height and 0 <= nc < width:
        n = (nr, nc)
        if n not in occupied and n not in seen:
          seen.add(n)
          stack.append(n)
  return seen


def _enclosed(width, height, occupied):
  """Background cells not 4-reachable from the grid border."""
  out = _outside(width, height, occupied)
  return {(r, c) for r in range(height) for c in range(width)
          if (r, c) not in occupied and (r, c) not in out}


def _shift(shape, dr, dc):
  out = {}
  for key in ("rects", "holes", "notches"):
    out[key] = [(r + dr, c + dc, h, w) for r, c, h, w in shape.get(key, [])]
  return out


def _analyse(width, height, shapes):
  """Independent scene verification; returns [(cells, holes)] or None."""
  sets = []
  owner = {}
  for idx, shape in enumerate(shapes):
    cells, holes = _shape_sets(shape)
    if not _connected(cells):
      return None
    for r, c in cells | holes:
      if not (1 <= r < height - 1 and 1 <= c < width - 1):
        return None
    for cell in cells:
      if cell in owner:
        return None
      owner[cell] = idx
    sets.append((cells, holes))
  # Strict background majority in the input.
  if 2 * len(owner) >= width * height:
    return None
  # No two shapes may touch, even diagonally.
  for (r, c), idx in owner.items():
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        o = owner.get((r + dr, c + dc))
        if o is not None and o != idx:
          return None
  all_holes = set()
  for _, holes in sets:
    if holes & set(owner):
      return None
    all_holes |= holes
  enclosed = _enclosed(width, height, set(owner))
  if enclosed != all_holes:
    return None
  # Each pocket must border exactly one shape: the one that declares it.
  owned = [set() for _ in shapes]
  for comp in _components(enclosed):
    adjacent = set()
    for r, c in comp:
      for dr, dc in N4:
        o = owner.get((r + dr, c + dc))
        if o is not None:
          adjacent.add(o)
    if len(adjacent) != 1:
      return None
    owned[adjacent.pop()] |= comp
  for idx, (_, holes) in enumerate(sets):
    if holes != owned[idx]:
      return None
  # Native context: at least one holed and one non-holed shape.
  flags = [bool(holes) for _, holes in sets]
  if not any(flags) or all(flags):
    return None
  return sets


def _local_ok(cells, holes):
  """True when the lone shape encloses exactly its declared holes."""
  minr = min(r for r, _ in cells)
  minc = min(c for _, c in cells)
  maxr = max(r for r, _ in cells)
  maxc = max(c for _, c in cells)
  width, height = maxc - minc + 3, maxr - minr + 3
  moved = {(r - minr + 1, c - minc + 1) for r, c in cells}
  want = {(r - minr + 1, c - minc + 1) for r, c in holes}
  return _enclosed(width, height, moved) == want


def _span(p, size, lo, hi):
  """Random start s with s <= p <= s+size-1 inside [lo, hi]."""
  return random.randint(max(lo, p - size + 1), min(p, hi - size + 1))


def _random_shape(kind, bh, bw):
  """Builds a 'holed', 'solid' or 'open' shape inside a bh x bw box.

  Returns the shape normalised to its own bounding box, or None.
  """
  low = MIN_SIZE[kind]
  h0, w0 = random.randint(low, bh), random.randint(low, bw)
  r0, c0 = random.randint(0, bh - h0), random.randint(0, bw - w0)
  rects = [(r0, c0, h0, w0)]
  holes, notches = [], []
  if kind != "solid":
    in_h, in_w = h0 - 2, w0 - 2
    hh = random.randint(1, min(4, in_h))
    hw = random.randint(1, min(4, in_w))
    if kind == "holed" and random.random() < 0.18:
      # Diagonal-only leak: the hole sits in an interior corner and the
      # matching outer corner cell of the ring is removed.
      top, left = random.random() < 0.5, random.random() < 0.5
      hr = r0 + 1 if top else r0 + h0 - 1 - hh
      hc = c0 + 1 if left else c0 + w0 - 1 - hw
      notches.append((r0 if top else r0 + h0 - 1,
                      c0 if left else c0 + w0 - 1, 1, 1))
    else:
      hr = random.randint(r0 + 1, r0 + h0 - 1 - hh)
      hc = random.randint(c0 + 1, c0 + w0 - 1 - hw)
    holes.append((hr, hc, hh, hw))
    if kind == "holed" and random.random() < 0.45:
      sh = random.randint(1, min(4, in_h))
      sw = random.randint(1, min(4, in_w))
      if random.random() < 0.6:
        # Overlaps the first hole: an irregular merged pocket.
        pr = random.randint(hr, hr + hh - 1)
        pc = random.randint(hc, hc + hw - 1)
        holes.append((_span(pr, sh, r0 + 1, r0 + h0 - 2),
                      _span(pc, sw, c0 + 1, c0 + w0 - 2), sh, sw))
      else:
        holes.append((random.randint(r0 + 1, r0 + h0 - 1 - sh),
                      random.randint(c0 + 1, c0 + w0 - 1 - sw), sh, sw))
  for _ in range(random.choice((0, 0, 1, 1, 2))):
    r, c = random.choice(sorted(_cells_of(rects)))
    eh = random.randint(1, min(bh, 7))
    ew = random.randint(1, min(bw, 7))
    rects.append((_span(r, eh, 0, bh - 1), _span(c, ew, 0, bw - 1), eh, ew))
  union = _cells_of(rects)
  if kind == "holed" and random.random() < 0.2:
    # Extra pocket anywhere in the union; its walls may come from the
    # extension rectangles. The local check decides if it is enclosed.
    r, c = random.choice(sorted(union))
    holes.append((r, c, random.randint(1, 2), random.randint(1, 2)))
  minr = min(r for r, _ in union)
  maxr = max(r for r, _ in union)
  minc = min(c for _, c in union)
  maxc = max(c for _, c in union)
  if kind == "open":
    # Breach the ring with a straight channel to the bounding-box edge.
    hr, hc, hh, hw = holes[0]
    side = random.randint(0, 3)
    if side == 0:
      channel = (minr, random.randint(hc, hc + hw - 1), hr - minr, 1)
    elif side == 1:
      channel = (hr + hh, random.randint(hc, hc + hw - 1),
                 maxr - hr - hh + 1, 1)
    elif side == 2:
      channel = (random.randint(hr, hr + hh - 1), minc, 1, hc - minc)
    else:
      channel = (random.randint(hr, hr + hh - 1), hc + hw, 1,
                 maxc - hc - hw + 1)
    notches.extend([holes[0], channel])
    holes = []
  if random.random() < 0.35:
    d, l = random.randint(1, 2), random.randint(1, 3)
    side = random.randint(0, 3)
    if side == 0:
      notches.append((minr, random.randint(minc, maxc), d, l))
    elif side == 1:
      notches.append((maxr - d + 1, random.randint(minc, maxc), d, l))
    elif side == 2:
      notches.append((random.randint(minr, maxr), minc, l, d))
    else:
      notches.append((random.randint(minr, maxr), maxc - d + 1, l, d))
  shape = {"rects": rects, "holes": holes, "notches": notches}
  cells, hole_cells = _shape_sets(shape)
  if not cells or not _connected(cells):
    return None
  if (kind == "holed") != bool(hole_cells):
    return None
  if not _local_ok(cells, hole_cells):
    return None
  return _shift(shape, -min(r for r, _ in cells), -min(c for _, c in cells))


def _fallback_shape(kind, bh, bw):
  """Deterministic valid shape filling the box (always succeeds)."""
  if kind == "solid":
    return {"rects": [(0, 0, bh, bw)], "holes": [], "notches": []}
  if kind == "holed":
    return {"rects": [(0, 0, bh, bw)], "holes": [(1, 1, bh - 2, bw - 2)],
            "notches": []}
  return {"rects": [(0, 0, bh, bw)], "holes": [],
          "notches": [(1, 1, bh - 2, bw - 2), (0, 1, 1, 1)]}


def _pack(sizes, order, across, depth, randomize):
  """Shelf-packs square minimum footprints separated by one-cell gaps.

  Items run along `across` inside bands that stack along `depth`.
  Returns a list of bands (lists of item indices), or None.
  """
  bands, cur, length = [], [], 0
  for idx in order:
    size = sizes[idx]
    if size > across:
      return None
    if cur and (length + 1 + size > across or
                (randomize and random.random() < 0.3)):
      bands.append(cur)
      cur, length = [], 0
    length = size if not cur else length + 1 + size
    cur.append(idx)
  if cur:
    bands.append(cur)
  if not bands:
    return None
  used = sum(max(sizes[i] for i in band) for band in bands) + len(bands) - 1
  return bands if used <= depth else None


def _feasible(n, width, height):
  """Constructive feasibility of n shapes on a width x height grid."""
  if (width - 1) * (height - 1) < AREA_PER_SHAPE * n:
    return False
  if MIN_SIZE["holed"] ** 2 + (n - 1) > (width * height - 1) // 2:
    return False
  sizes = [MIN_SIZE["holed"]] + [MIN_SIZE["solid"]] * (n - 1)
  order = list(range(n))
  iw, ih = width - 2, height - 2
  return (_pack(sizes, order, iw, ih, False) is not None or
          _pack(sizes, order, ih, iw, False) is not None)


def _spread(total, buckets):
  """Randomly splits a non-negative total into `buckets` parts."""
  cuts = sorted(random.randint(0, total) for _ in range(buckets - 1))
  out, prev = [], 0
  for cut in cuts + [total]:
    out.append(cut - prev)
    prev = cut
  return out


def _layout(kinds, iw, ih):
  """Assigns each shape a slot (r, c, h, w) in interior coordinates."""
  sizes = [MIN_SIZE[k] for k in kinds]
  n = len(kinds)
  plan = None
  for _ in range(12):
    transposed = random.random() < 0.5
    order = list(range(n))
    random.shuffle(order)
    across, depth = (ih, iw) if transposed else (iw, ih)
    bands = _pack(sizes, order, across, depth, True)
    if bands is not None:
      plan = (transposed, bands)
      break
  if plan is None:
    order = sorted(range(n), key=lambda i: -sizes[i])
    for transposed in (False, True):
      across, depth = (ih, iw) if transposed else (iw, ih)
      bands = _pack(sizes, order, across, depth, False)
      if bands is not None:
        plan = (transposed, bands)
        break
  if plan is None:
    return None
  transposed, bands = plan
  across, depth = (ih, iw) if transposed else (iw, ih)
  nb = len(bands)
  band_min = [max(sizes[i] for i in band) for band in bands]
  extra = _spread(depth - sum(band_min) - (nb - 1), 2 * nb + 1)
  slots = [None] * n
  pos = extra[0]
  for b, band in enumerate(bands):
    band_len = band_min[b] + extra[1 + b]
    k = len(band)
    extra2 = _spread(across - sum(sizes[i] for i in band) - (k - 1),
                     2 * k + 1)
    q = extra2[0]
    for j, idx in enumerate(band):
      item_len = sizes[idx] + extra2[1 + j]
      if transposed:
        slots[idx] = (q, pos, item_len, band_len)
      else:
        slots[idx] = (pos, q, band_len, item_len)
      q += item_len + 1 + extra2[1 + k + j]
    pos += band_len + 1 + extra[1 + nb + b]
  return slots


def _pick(lo, values):
  preferred = [v for v in values if v >= lo]
  return random.choice(preferred or values)


def _choose_dims(width, height, num_shapes):
  if num_shapes is not None:
    counts = [num_shapes]
  else:
    counts = list(range(MIN_SHAPES, MAX_SHAPES + 1))
  sides = list(range(MIN_RANDOM_SIDE, MAX_SIDE + 1))

  def ok(n):
    if width is not None and height is not None:
      return _feasible(n, width, height)
    if width is not None:
      return any(_feasible(n, width, v) for v in sides)
    if height is not None:
      return any(_feasible(n, v, height) for v in sides)
    return _feasible(n, MAX_SIDE, MAX_SIDE)

  options = [n for n in counts if ok(n)]
  if not options:
    raise ValueError("requested size cannot hold the requested shapes")
  n = random.choice(options)
  lo = min(MAX_SIDE, max(12, 6 + 3 * n))
  if width is None and height is None:
    w = random.randint(lo, MAX_SIDE)
    h = _pick(lo, [v for v in sides if _feasible(n, w, v)])
  elif height is None:
    w = width
    h = _pick(lo, [v for v in sides if _feasible(n, width, v)])
  elif width is None:
    h = height
    w = _pick(lo, [v for v in sides if _feasible(n, v, height)])
  else:
    w, h = width, height
  return n, w, h


def _random_scene(width, height, num_shapes):
  n, w, h = _choose_dims(width, height, num_shapes)
  kinds = ["holed", "open" if random.random() < 0.35 else "solid"]
  for _ in range(n - 2):
    kinds.append(random.choice(KIND_POOL))
  random.shuffle(kinds)
  keep = kinds.index("holed")
  budget = (w * h - 1) // 2
  slots = None
  for _ in range(n + 1):
    if sum(MIN_SIZE[k] ** 2 for k in kinds) <= budget:
      slots = _layout(kinds, w - 2, h - 2)
      if slots is not None:
        break
    spare = [i for i, k in enumerate(kinds) if k != "solid" and i != keep]
    if not spare:
      break
    kinds[random.choice(spare)] = "solid"
  if slots is None:
    raise RuntimeError("feasible request failed constructive packing")
  reserve = sum(MIN_SIZE[k] ** 2 for k in kinds)
  shapes = [None] * n
  order = list(range(n))
  random.shuffle(order)
  for idx in order:
    kind = kinds[idx]
    low = MIN_SIZE[kind]
    reserve -= low * low
    room = budget - reserve
    sr, sc, sh, sw = slots[idx]
    bh = random.randint(low, min(sh, MAX_BOX))
    if min(sw, MAX_BOX, room // bh) < low:
      bh = low
    bw = random.randint(low, min(sw, MAX_BOX, room // bh))
    budget -= bh * bw
    shape = None
    for _ in range(25):
      shape = _random_shape(kind, bh, bw)
      if shape is not None:
        break
    if shape is None:
      shape = _fallback_shape(kind, bh, bw)
    cells = _shape_sets(shape)[0]
    eh = max(r for r, _ in cells) + 1
    ew = max(c for _, c in cells) + 1
    shapes[idx] = _shift(shape, 1 + sr + random.randint(0, sh - eh),
                         1 + sc + random.randint(0, sw - ew))
  return w, h, shapes


def _normalise_shapes(shapes):
  if not isinstance(shapes, (list, tuple)) or len(shapes) < MIN_SHAPES:
    raise ValueError("shapes must be a list of at least %d shapes"
                     % MIN_SHAPES)
  out = []
  for shape in shapes:
    if (not isinstance(shape, dict) or
        not set(shape) <= {"rects", "holes", "notches"}):
      raise ValueError("each shape must be a dict of rects/holes/notches")
    clean = {}
    for key in ("rects", "holes", "notches"):
      rects = shape.get(key, [])
      if not isinstance(rects, (list, tuple)):
        raise ValueError("%s must be a list of rectangles" % key)
      clean[key] = []
      for rect in rects:
        if (not isinstance(rect, (list, tuple)) or len(rect) != 4 or
            not all(_is_int(v) for v in rect) or
            not (0 <= rect[0] < MAX_SIDE and 0 <= rect[1] < MAX_SIDE) or
            not (1 <= rect[2] <= MAX_SIDE and 1 <= rect[3] <= MAX_SIDE)):
          raise ValueError("bad rectangle %r" % (rect,))
        clean[key].append(tuple(rect))
    if not clean["rects"]:
      raise ValueError("each shape needs at least one rectangle")
    out.append(clean)
  return out


def generate(width=None, height=None, shapes=None, num_shapes=None):
  """Generates one input/output pair.

  Args:
    width: grid width in columns, as an int (bool is rejected). In random
      mode it may be 8..30 and is honoured exactly; it is sampled when
      omitted. It is required (1..30) when shapes is given.
    height: grid height in rows. Handled the same way as width.
    shapes: optional list of at least two latent shapes. Each shape is a
      dict with these keys:
        "rects": filled (row, col, h, w) rectangles whose union is the
          shape.
        "holes": optional rectangles carved out as enclosed pockets.
        "notches": optional rectangles carved out that stay open.
      ValueError is raised in any of these cases:
        * the declared holes differ from the enclosed background;
        * a pocket borders a shape other than the one declaring it;
        * shapes touch each other, nest, or reach the border;
        * there is no holed shape, or no non-holed shape;
        * colour 4 is not the strict majority of the input.
    num_shapes: optional exact shape count, an int in 2..6. In random
      mode the request must also be constructively feasible for the
      sides. With explicit shapes it must equal len(shapes).
  """
  for name, value in (("width", width), ("height", height),
                      ("num_shapes", num_shapes)):
    if value is not None and not _is_int(value):
      raise ValueError("%s must be an int" % name)
  if num_shapes is not None and not MIN_SHAPES <= num_shapes <= MAX_SHAPES:
    raise ValueError("num_shapes must be in %d..%d" % (MIN_SHAPES,
                                                      MAX_SHAPES))
  if shapes is None:
    for name, value in (("width", width), ("height", height)):
      if value is not None and not MIN_RANDOM_SIDE <= value <= MAX_SIDE:
        raise ValueError("%s must be in %d..%d" % (name, MIN_RANDOM_SIDE,
                                                   MAX_SIDE))
    width, height, shapes = _random_scene(width, height, num_shapes)
    sets = _analyse(width, height, shapes)
    if sets is None:
      raise RuntimeError("constructed scene failed verification")
  else:
    if width is None or height is None:
      raise ValueError("width and height are required with explicit shapes")
    if not (1 <= width <= MAX_SIDE and 1 <= height <= MAX_SIDE):
      raise ValueError("grid sides must be in 1..30")
    shapes = _normalise_shapes(shapes)
    if num_shapes is not None and num_shapes != len(shapes):
      raise ValueError("num_shapes disagrees with len(shapes)")
    sets = _analyse(width, height, shapes)
    if sets is None:
      raise ValueError("invalid scene")
  grid = common.grid(width, height, BG)
  output = common.grid(width, height, BG)
  occupied, all_holes = set(), set()
  for cells, holes in sets:
    occupied |= cells
    all_holes |= holes
  for cells, _ in sets:
    for r, c in cells:
      for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
          nr, nc = r + dr, c + dc
          if (0 <= nr < height and 0 <= nc < width and
              (nr, nc) not in occupied and (nr, nc) not in all_holes):
            output[nr][nc] = OUTLINE
  for cells, holes in sets:
    colour = HOLED if holes else SHAPE
    for r, c in cells:
      grid[r][c] = SHAPE
      output[r][c] = colour
    for r, c in holes:
      output[r][c] = HOLE
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical fixtures from explicit latent shapes."""
  train = [
      generate(width=25, height=23, shapes=[
          {"rects": [(2, 3, 4, 4), (3, 6, 5, 4)], "holes": [(4, 7, 2, 2)]},
          {"rects": [(1, 16, 6, 7)], "holes": [(2, 17, 3, 3)]},
          {"rects": [(10, 10, 7, 3), (12, 10, 5, 9)]},
      ]),
      generate(width=23, height=28, shapes=[
          {"rects": [(2, 1, 4, 7), (2, 1, 6, 4)]},
          {"rects": [(1, 10, 6, 1), (3, 10, 4, 5), (1, 14, 6, 7)],
           "holes": [(2, 15, 4, 4)]},
          {"rects": [(10, 4, 7, 6), (11, 4, 6, 14), (11, 12, 11, 6),
                     (10, 13, 1, 5)]},
          {"rects": [(22, 4, 2, 1), (23, 3, 1, 2)]},
      ]),
      generate(width=15, height=20, shapes=[
          {"rects": [(3, 3, 3, 3)]},
          {"rects": [(6, 12, 1, 1)]},
          {"rects": [(12, 4, 4, 5), (13, 4, 3, 7)], "holes": [(13, 5, 1, 2)]},
      ]),
  ]
  test = [
      generate(width=27, height=26, shapes=[
          {"rects": [(2, 8, 7, 9), (5, 6, 1, 2), (6, 4, 5, 9), (11, 4, 1, 7)],
           "holes": [(3, 13, 3, 3)]},
          {"rects": [(10, 19, 2, 4), (12, 18, 4, 8)]},
          {"rects": [(15, 10, 2, 3), (17, 7, 4, 6)]},
          {"rects": [(21, 20, 3, 4)], "holes": [(22, 21, 1, 2)]},
      ]),
  ]
  return {"train": train, "test": test}
