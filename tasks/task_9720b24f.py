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

"""Generator for ARC task 9720b24f: erase objects that sit inside containers.

Rule: objects are 8-connected single-colour components on a 0 background.
An object is erased (set to 0) if all of its cells lie inside the inclusive
bounding box of a strictly larger object of a different colour. Every other
object is kept.

Scope: by default one to three containers are drawn, and up to six can be
requested. Each container is a single-colour outline. It can be a rectangle,
a symmetric octagon or diamond, or an asymmetric octagon with a different
diagonal cut at each corner. Part of one straight side may be thickened
inward, which gives 2-cell-thick parts like the fixture 2-shapes. A container
may be opened by a gap in a straight or diagonal side. A gap never removes
the cells that define the bounding box, and the outline stays 8-connected.

Inner objects are one to three small objects of other colours placed inside
a container. They may use the gap cells, which can lie on the bounding-box
border (as the 5 does in train 4). The first container always gets at least
one inner object, and later containers may be left empty. Every container
keeps at least one blank interior cell, so 0 is always present as the
background.

Up to ten loose distractor objects are sampled, often reusing the inner
colours. Placement is best-effort on tight grids. An explicit num_loose
request (0..12) is exact or raises ValueError if placement fails. A loose object is either far from everything or a "near-miss". A
near-miss has a bounding box that crosses a container's bounding box. It may
have some cells inside any container's box, but never all of them, whatever
its colour. Train 3 has both kinds of near-miss.

Every scene is checked against the rule using its own latent objects.
Components must not merge, and the inner/loose labels must match
containment. If the check fails, a ValueError is raised rather than hidden.

Deliberately untaught clauses: random scenes never put an erased object in a
cut-corner region outside the outline. No object is ever placed inside the
box of an equal-or-smaller different-colour object, nor of a same-colour
object. The fixtures do not exercise these cases either.

Default grids are 7..30 cells per side. Sizes 4..30 are accepted as
synthetic extensions. Explicit latent arguments (container, inner and loose
cell lists) reproduce the original fixtures and are checked the same way.
"""

import random

import common

_PALETTE = list(range(1, 10))
_MAX_SIDE = 30
_MAX_CONTAINERS = 6
_MIN_BOX = 4
_MAX_BOX = 11
# Inward step for the straight sides (segment indices 0, 2, 4, 6).
_INWARD = {0: (1, 0), 2: (0, -1), 4: (-1, 0), 6: (0, 1)}


def _is_int(x):
  return isinstance(x, int) and not isinstance(x, bool)


def _line(r0, c0, r1, c1):
  dr = (r1 > r0) - (r1 < r0)
  dc = (c1 > c0) - (c1 < c0)
  n = max(abs(r1 - r0), abs(c1 - c0))
  return [(r0 + dr * i, c0 + dc * i) for i in range(n + 1)]


def _neighbours(r, c):
  return [(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
          if dr or dc]


def _overlap(a, b):
  return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def _expand(box):
  return (box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1)


def _bbox(cells):
  rows = [r for r, _ in cells]
  cols = [c for _, c in cells]
  return (min(rows), min(cols), max(rows), max(cols))


def _inside(cells, box):
  return all(box[0] <= r <= box[2] and box[1] <= c <= box[3]
             for r, c in cells)


def _connected(cells):
  cells = set(cells)
  if not cells:
    return False
  start = min(cells)
  seen = {start}
  stack = [start]
  while stack:
    p = stack.pop()
    for q in _neighbours(*p):
      if q in cells and q not in seen:
        seen.add(q)
        stack.append(q)
  return len(seen) == len(cells)


def _contained(col, cells, objs):
  """True if cells lie in the bbox of a larger, different-colour object."""
  for ocol, ocells in objs:
    if (ocol != col and len(ocells) > len(cells) and
        _inside(cells, _bbox(ocells))):
      return True
  return False


def _cap(width, height):
  """Number of 4x4 containers that fit with a one-cell separation."""
  return ((width + 1) // 5) * ((height + 1) // 5)


def _min_side(other, n):
  """Smallest free side that fits n containers next to a fixed side."""
  per = (other + 1) // 5
  return 5 * (-(-n // per)) - 1


def _check_side(name, value, low):
  if value is None:
    return
  if not _is_int(value) or not low <= value <= _MAX_SIDE:
    raise ValueError(f"{name} must be an integer in {low}..{_MAX_SIDE}")


def _grow(avail, n, start=None):
  """Grows a random 8-connected shape of up to n cells within avail.

  Each added cell touches an earlier one, so every prefix is connected.
  """
  avail = set(avail)
  if start is None:
    start = random.choice(sorted(avail))
  shape = [start]
  seen = {start}
  while len(shape) < n:
    cand = sorted({q for p in shape for q in _neighbours(*p)
                   if q in avail and q not in seen})
    if not cand:
      break
    q = random.choice(cand)
    shape.append(q)
    seen.add(q)
  return shape


def _corner_sizes(h, w):
  """Samples diagonal corner cuts (top-left, top-right, bottom-right, bottom-left)."""
  u = random.random()
  if u < 0.3:
    return (0, 0, 0, 0)
  if u < 0.6:
    k = random.randint(1, min((h - 1) // 2, (w - 1) // 2))
    return (k, k, k, k)
  top = min(h, w) // 2 + 1
  for _ in range(20):
    tl, tr, br, bl = [random.randint(0, top) for _ in range(4)]
    if (tl + tr <= w - 1 and bl + br <= w - 1 and tl + bl <= h - 1 and
        tr + br <= h - 1):
      return (tl, tr, br, bl)
  return (0, 0, 0, 0)


def _build_container(h, w, ks):
  """Returns (outline, interior, gap) in local coordinates, or None."""
  tl, tr, br, bl = ks
  verts = [(0, tl), (0, w - 1 - tr), (tr, w - 1), (h - 1 - br, w - 1),
           (h - 1, w - 1 - br), (h - 1, bl), (h - 1 - bl, 0), (tl, 0)]
  segs = []
  for i in range(8):
    a, b = verts[i], verts[(i + 1) % 8]
    segs.append(_line(a[0], a[1], b[0], b[1]))
  cells = set()
  for s in segs:
    cells.update(s)
  interior = set()
  for r in range(1, h - 1):
    for c in range(1, w - 1):
      if (r + c > tl and r + (w - 1 - c) > tr and
          (h - 1 - r) + (w - 1 - c) > br and (h - 1 - r) + c > bl):
        interior.add((r, c))
  interior -= cells
  if len(interior) < 3:
    return None
  thick_side = None
  if random.random() < 0.3:
    sides = [i for i in (0, 2, 4, 6) if len(segs[i]) >= 2]
    if sides:
      i = random.choice(sides)
      seg = segs[i]
      run = random.randint(2, len(seg))
      s0 = random.randint(0, len(seg) - run)
      dr, dc = _INWARD[i]
      thick = {(r + dr, c + dc) for r, c in seg[s0:s0 + run]} & interior
      if thick and len(interior - thick) >= 3:
        cells |= thick
        interior -= thick
        thick_side = i
  gap = []
  if random.random() < 0.55:
    cand = [i for i in range(8) if i != thick_side and len(segs[i]) >= 3]
    if cand:
      i = random.choice(cand)
      mid = segs[i][1:-1]  # Endpoints stay, so the bounding box is kept.
      g = random.randint(1, len(mid))
      s0 = random.randint(0, len(mid) - g)
      removed = [p for p in mid[s0:s0 + g] if p in cells]
      trial = cells - set(removed)
      if (removed and _connected(trial) and
          _bbox(trial) == (0, 0, h - 1, w - 1)):
        cells = trial
        gap = removed
  return sorted(cells), sorted(interior), gap


def _container(h, w):
  for _ in range(10):
    res = _build_container(h, w, _corner_sizes(h, w))
    if res is not None:
      return res
  return _build_container(h, w, (0, 0, 0, 0))  # Rectangle: always valid.


def _loose_shape():
  if random.random() < 0.45:
    n = random.randint(2, 4)
    if random.random() < 0.5:
      return [(i, i) for i in range(n)]
    return [(i, n - 1 - i) for i in range(n)]
  shape = _grow([(r, c) for r in range(3) for c in range(3)],
                random.randint(1, 5))
  mr = min(r for r, _ in shape)
  mc = min(c for _, c in shape)
  return [(r - mr, c - mc) for r, c in shape]


def _pick_dims(width, height, n):
  if width is not None and height is not None:
    if _cap(width, height) < n:
      raise ValueError(f"{n} containers do not fit in the requested grid")
    return width, height
  if width is None and height is None:
    for _ in range(100):
      w = random.randint(7, 30)
      h = random.randint(7, 30)
      if _cap(w, h) >= n:
        return w, h
    width = random.randint(7, 30)
  if height is None:
    lo = max(7, _min_side(width, n))
    if lo > _MAX_SIDE:
      raise ValueError(f"{n} containers do not fit with width {width}")
    return width, random.randint(lo, 30)
  lo = max(7, _min_side(height, n))
  if lo > _MAX_SIDE:
    raise ValueError(f"{n} containers do not fit with height {height}")
  return random.randint(lo, 30), height


def _split(total, k):
  """Splits total cells into k spans (sizes 4.._MAX_BOX) with gaps >= 1."""
  sizes = [_MIN_BOX] * k
  gaps = [0] + [1] * (k - 1) + [0]
  for _ in range(total - (5 * k - 1)):
    i = random.randrange(k)
    if random.random() < 0.5 and sizes[i] < _MAX_BOX:
      sizes[i] += 1
    else:
      gaps[random.randrange(k + 1)] += 1
  spans = []
  pos = gaps[0]
  for i in range(k):
    spans.append((pos, sizes[i]))
    pos += sizes[i] + gaps[i + 1]
  return spans


def _lattice_boxes(width, height, n):
  """Fallback: jittered lattice with random slack in sizes and gaps."""
  rows = _split(height, (height + 1) // 5)
  cols = _split(width, (width + 1) // 5)
  slots = [(r, c) for r in rows for c in cols]
  return [(r[0], c[0], r[0] + r[1] - 1, c[0] + c[1] - 1)
          for r, c in random.sample(slots, n)]


def _place_boxes(width, height, n):
  """Random separated container boxes, retried before the lattice fallback."""
  for _ in range(20):
    boxes = []
    for _ in range(n):
      placed = None
      for _ in range(50):
        bh = random.randint(_MIN_BOX, min(_MAX_BOX, height))
        bw = random.randint(_MIN_BOX, min(_MAX_BOX, width))
        r0 = random.randint(0, height - bh)
        c0 = random.randint(0, width - bw)
        box = (r0, c0, r0 + bh - 1, c0 + bw - 1)
        if not any(_overlap(_expand(box), b) for b in boxes):
          placed = box
          break
      if placed is None:
        break
      boxes.append(placed)
    if len(boxes) == n:
      return boxes
  return _lattice_boxes(width, height, n)


def _fill_container(box, col, csize, interior, gap, occ, want):
  """Places up to `want` inner objects, always leaving one interior cell blank."""
  interior = [(box[0] + r, box[1] + c) for r, c in interior]
  gap = [(box[0] + r, box[1] + c) for r, c in gap]
  gap_set = set(gap)
  inners = []
  for _ in range(want):
    free_int = [p for p in interior if p not in occ]
    if len(free_int) < 2:
      break
    free = free_int + [p for p in gap if p not in occ]
    icol = random.choice([x for x in _PALETTE if x != col])
    avail = [p for p in free
             if not any(occ.get(q) == icol for q in _neighbours(*p))]
    if not avail:
      continue
    start = None
    gap_avail = [p for p in avail if p in gap_set]
    if gap_avail and random.random() < 0.5:
      start = random.choice(gap_avail)
    shape = _grow(avail, random.randint(1, min(5, csize - 1)), start)
    while shape and set(free_int) <= set(shape):
      shape.pop()  # Prefixes stay connected; keep one interior cell blank.
    if not shape:
      continue
    inners.append((icol, shape))
    for p in shape:
      occ[p] = icol
  return inners


def _place_loose(shape, lcol, near, width, height, cboxes, loose_boxes,
                 objs, kept, occ, protected):
  """Places a loose object; a near-miss crosses a container bbox."""
  sh = max(r for r, _ in shape) + 1
  sw = max(c for _, c in shape) + 1
  if sh > height or sw > width or (near and not cboxes):
    return None
  for _ in range(40):
    if near:
      b = random.choice(cboxes)
      r0 = random.randint(max(0, b[0] - sh + 1), min(height - sh, b[2]))
      c0 = random.randint(max(0, b[1] - sw + 1), min(width - sw, b[3]))
    else:
      r0 = random.randint(0, height - sh)
      c0 = random.randint(0, width - sw)
    box = (r0, c0, r0 + sh - 1, c0 + sw - 1)
    cells = [(r0 + r, c0 + c) for r, c in shape]
    others = loose_boxes if near else cboxes + loose_boxes
    if any(_overlap(_expand(box), b) for b in others):
      continue
    if any(p in occ or p in protected for p in cells):
      continue
    if any(occ.get(q) == lcol for p in cells for q in _neighbours(*p)):
      continue
    # A loose object never lies wholly inside any container box, whatever
    # its colour, so the untaught same-colour clause is never decisive.
    if any(_inside(cells, cb) for cb in cboxes):
      continue
    if _contained(lcol, cells, objs):
      continue
    if any(ocol != lcol and len(ocells) < len(cells) and _inside(ocells, box)
           for ocol, ocells in kept):
      continue
    return cells, box
  return None


def _random_scene(width, height, n, num_loose=None):
  boxes = _place_boxes(width, height, n)
  colours = random.sample(_PALETTE, n)
  occ = {}
  protected = set()
  containers, inners, loose = [], [], []
  for ci, (box, col) in enumerate(zip(boxes, colours)):
    bh = box[2] - box[0] + 1
    bw = box[3] - box[1] + 1
    outline, interior, gap = _container(bh, bw)
    cells = [(box[0] + r, box[1] + c) for r, c in outline]
    containers.append((col, cells))
    for p in cells:
      occ[p] = col
    protected.update((box[0] + r, box[1] + c) for r, c in interior)
    if ci > 0 and random.random() < 0.2:
      want = 0
    else:
      want = random.randint(1, 3)
    inners.extend(_fill_container(box, col, len(cells), interior, gap, occ,
                                  want))
  inner_cols = sorted({c for c, _ in inners})
  loose_boxes = []
  target = random.randint(0, 10) if num_loose is None else num_loose
  for _ in range(target * 8):
    if len(loose) == target:
      break
    shape = _loose_shape()
    if inner_cols and random.random() < 0.5:
      lcol = random.choice(inner_cols)
    else:
      lcol = random.choice(_PALETTE)
    near = random.random() < 0.45
    placed = _place_loose(shape, lcol, near, width, height, boxes,
                          loose_boxes, containers + inners + loose,
                          containers + loose, occ, protected)
    if placed is None:
      continue
    cells, lbox = placed
    loose.append((lcol, cells))
    loose_boxes.append(lbox)
    for p in cells:
      occ[p] = lcol
  if num_loose is not None and len(loose) != num_loose:
    raise ValueError('could not place the requested number of loose objects')
  return containers, inners, loose


def _normalise(objs, name):
  """Validates and normalises an explicit list of (colour, cells) objects."""
  if not isinstance(objs, (list, tuple)):
    raise ValueError(f"{name} must be a list of (colour, cells) pairs")
  out = []
  for obj in objs:
    if not isinstance(obj, (list, tuple)) or len(obj) != 2:
      raise ValueError(f"each {name} entry must be a (colour, cells) pair")
    col, cells = obj
    if not _is_int(col) or not 1 <= col <= 9:
      raise ValueError("object colours must be integers in 1..9")
    if not isinstance(cells, (list, tuple)):
      raise ValueError(f"{name} cells must be a list of (row, col) pairs")
    pts = []
    for p in cells:
      if (not isinstance(p, (list, tuple)) or len(p) != 2 or
          not _is_int(p[0]) or not _is_int(p[1])):
        raise ValueError("each cell must be a pair of integer coordinates")
      pts.append((p[0], p[1]))
    out.append((col, pts))
  return out


def _verify(width, height, containers, inners, loose):
  """Checks the latent scene is a valid, rule-consistent episode."""
  objs = list(containers) + list(inners) + list(loose)
  owner = {}
  for i, (col, cells) in enumerate(objs):
    if not _is_int(col) or not 1 <= col <= 9:
      raise ValueError("object colours must be integers in 1..9")
    if not cells:
      raise ValueError("objects must be non-empty")
    for r, c in cells:
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError("object cell out of bounds")
      if (r, c) in owner:
        raise ValueError("objects overlap")
      owner[(r, c)] = i
    if not _connected(cells):
      raise ValueError("each object must be one 8-connected component")
  for i, (col, cells) in enumerate(objs):
    for p in cells:
      for q in _neighbours(*p):
        j = owner.get(q)
        if j is not None and j != i and objs[j][0] == col:
          raise ValueError("same-colour objects touch and would merge")
  if len(owner) >= width * height:
    raise ValueError("the grid needs at least one background 0 cell")
  for col, cells in inners:
    if not _contained(col, cells, objs):
      raise ValueError("an inner object is not contained by the rule")
  for col, cells in list(containers) + list(loose):
    if _contained(col, cells, objs):
      raise ValueError("a kept object would be erased by the rule")


def _render(width, height, containers, inners, loose):
  grid = common.grid(width, height, 0)
  for col, cells in list(containers) + list(inners) + list(loose):
    for r, c in cells:
      grid[r][c] = col
  out = [row[:] for row in grid]
  for _, cells in inners:
    for r, c in cells:
      out[r][c] = 0
  return {"input": grid, "output": out}


def generate(width=None, height=None, num_containers=None, containers=None,
             inners=None, loose=None, num_loose=None):
  """Returns an input/output pair for task 9720b24f.

  Args:
    width: grid width (a non-bool integer). In random mode it must be in
      4..30. If omitted it is sampled from 7..30, respecting the space
      needed for the containers. Required when explicit containers are given (1..30).
    height: grid height. The same rules as width apply.
    num_containers: number of containers in random mode (1..6). Defaults to
      a random 1..3, capped by what fits. With explicit containers it must
      equal their count.
    containers: explicit list of (colour, cells) container outlines.
    inners: explicit list of (colour, cells) contained objects, which are
      erased. Only allowed together with containers.
    loose: explicit list of (colour, cells) uncontained objects, which are
      kept. Only allowed together with containers.
    num_loose: exact loose-object count, int 0..12. On the random path,
      bounded placement may reject crowded layouts rather than silently
      lower the count. With explicit scenes it must match len(loose).

  Explicit scenes are checked. Coordinates and colours must be integers.
  Each object must be one 8-connected component, and same-colour objects
  must not touch. A 0 cell must remain. The inner/loose labels must agree
  with the containment rule. Explicit identity scenes (including no
  containers) remain valid; they are never the default random output.
  """
  if num_loose is not None and (not _is_int(num_loose) or not 0 <= num_loose <= 12):
    raise ValueError('num_loose must be an integer in 0..12')
  if num_containers is not None and not _is_int(num_containers):
    raise ValueError("num_containers must be an integer")
  if containers is not None:
    if width is None or height is None:
      raise ValueError("explicit containers require width and height")
    _check_side("width", width, 1)
    _check_side("height", height, 1)
    containers = _normalise(containers, "containers")
    if num_containers is not None and num_containers != len(containers):
      raise ValueError("num_containers does not match containers")
    inners = _normalise(inners if inners is not None else [], "inners")
    loose = _normalise(loose if loose is not None else [], "loose")
    if num_loose is not None and len(loose) != num_loose:
      raise ValueError('num_loose does not match loose')
  else:
    if inners is not None or loose is not None:
      raise ValueError("inners/loose may only be given with containers")
    _check_side("width", width, 4)
    _check_side("height", height, 4)
    if num_containers is not None:
      if not 1 <= num_containers <= _MAX_CONTAINERS:
        raise ValueError(f"num_containers must be in 1..{_MAX_CONTAINERS}")
      n = num_containers
    else:
      n = random.randint(1, 3)
      if width is not None and height is not None:
        n = min(n, _cap(width, height))
    width, height = _pick_dims(width, height, n)
    containers, inners, loose = _random_scene(width, height, n, num_loose)
  _verify(width, height, containers, inners, loose)
  return _render(width, height, containers, inners, loose)


def validate():
  """Reconstructs the canonical fixtures from explicit latent objects."""
  six = [(6, 6), (6, 7), (6, 8), (7, 4), (7, 5), (8, 4), (9, 4), (9, 5),
         (9, 6), (9, 7), (9, 8)]
  train = [
      generate(width=3, height=3,
               containers=[(1, [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2),
                                (1, 2), (0, 2)])],
               inners=[(7, [(1, 1)])], loose=[]),
      generate(width=11, height=11,
               containers=[(2, [(1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
                                (2, 1), (2, 2), (3, 1), (3, 2), (4, 2),
                                (4, 3), (4, 4), (4, 5), (4, 6)]),
                           (6, six)],
               inners=[(5, [(2, 4), (2, 5), (3, 4), (3, 5)]),
                       (8, [(7, 6), (8, 7)])],
               loose=[]),
      generate(width=15, height=15,
               containers=[(3, [(1, 3), (2, 2), (3, 1), (4, 1), (5, 2),
                                (6, 3), (6, 4), (5, 5), (4, 6)]),
                           (7, [(6, 9), (6, 10), (7, 8), (7, 11), (8, 7),
                                (8, 12), (9, 11), (10, 10), (11, 9)])],
               inners=[(6, [(3, 3), (4, 3), (4, 4)]),
                       (8, [(7, 9), (8, 9), (8, 10)])],
               loose=[(6, [(0, 5), (0, 6), (0, 7), (1, 6)]),
                      (8, [(10, 5), (11, 6), (12, 7)])]),
      generate(width=11, height=11,
               containers=[(2, [(1, 3), (1, 4), (2, 1), (2, 2), (3, 1),
                                (3, 2), (4, 2), (4, 3), (4, 4)]),
                           (6, six)],
               inners=[(5, [(3, 4)])],
               loose=[(9, [(7, 10)])]),
  ]
  test = [
      generate(width=12, height=13,
               containers=[(3, [(1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
                                (1, 9), (1, 10), (2, 3), (2, 4), (2, 10),
                                (3, 3), (3, 10), (3, 11), (4, 3), (4, 10),
                                (4, 11), (5, 3), (5, 10), (5, 11), (6, 3),
                                (6, 10)]),
                           (6, [(8, 3), (8, 4), (9, 2), (9, 5), (10, 2),
                                (10, 6), (11, 3), (12, 4)])],
               inners=[(7, [(3, 6), (3, 7), (4, 7), (4, 8)]),
                       (8, [(4, 4), (5, 4), (5, 5)]),
                       (9, [(9, 4), (10, 3), (10, 4)])],
               loose=[(7, [(0, 0)]), (7, [(2, 0)]), (7, [(8, 8)]),
                      (7, [(10, 8)]), (7, [(10, 11)]), (7, [(12, 11)]),
                      (9, [(7, 1)]), (9, [(9, 0)]),
                      (9, [(11, 0), (12, 1)])]),
  ]
  return {"train": train, "test": test}
