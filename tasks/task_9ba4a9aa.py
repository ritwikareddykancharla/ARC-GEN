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

"""ARC-GEN style generator for task 9ba4a9aa.

Rule: the canvas holds several 3x3 boxes joined by dotted lines, with dots two
cells apart. Every box is a ring (8 outer cells of one colour around a centre
of another colour) except one checkerboard box, which is the start. Exactly
one dot touches the checkerboard, and its colour c is the path colour. Follow
the dots of colour c in orthogonal steps of two. Branches change colour at
junctions and are ignored. The c path ends beside exactly one ring box. The
output is that box, copied as a 3x3 grid.

Scene model: dots and box centres lie on one lattice with spacing 2 and a
random parity. A random tree of dotted walks grows from the start box. The
trunk leaves the start box, and later branches leave existing (non-final)
dots at junctions. Every walk ends in a ring box. One leaf box is chosen as
the target. The root-to-target chain is coloured c. Every chain that leaves
it initially uses colours other than c, including a continuation beyond a
junction. A labelled synthetic extension may recolour a non-main tail to c
behind a wrong-colour barrier, producing a disconnected same-colour decoy. Sub-branches may keep their
parent's colour or change it. The target may also get an extra non-c walk
from another side, leading to a further distractor box (as in train pair 3).
The path colour usually differs from the checker colours (as in all
fixtures). Occasionally it may equal one of them; this is a harmless
synthetic extension.

These constraints are enforced in random mode by construction:
  * Box centres are at Chebyshev distance >= 4, so boxes never touch.
  * Dots never touch a box except the last dot of the walk that ends there
    (plus the trunk's first dot at the start box and the optional extra
    walk's first dot at the target).
  * Dots are lattice-adjacent only to their tree parent and children.
  * Branches never leave a walk's final dot, so no distractor box can touch
    the c path.
  * After a forced turn a walk keeps going straight for at least two dots
    unless blocked again, which limits diagonal-looking staircases.

All fixtures are 22x22. Random scenes default to 16..30 per side and accept
explicit sizes 14..30. Sizes other than 22 are synthetic extensions; the rule
does not depend on grid size. On grids with a side below 18, the minimum
number of ring boxes drops from 3 to 2 and the minimum trunk length from 4 to
3, so that small lattices remain feasible. With 2 ring boxes the scene still
contains a colour-changing branch off the c path.

Fixture replay uses explicit latent arguments: box list, dot segment list and
target index, given together with height, width and background. Partial
explicit scenes are rejected. Explicit scenes are type-checked (integers
only, booleans rejected) and checked for colour ranges, box spacing, dots
inside boxes, conflicting dots, a single dot-lattice parity, and stray solid
3x3 windows that are not declared boxes. The supplied target must also agree
with the latent path structure. Random scenes also receive post-construction label and solid-window checks;
a construction failure is surfaced, not silently filtered. Explicit replay
retains broader valid path structures than the random tree distribution.
"""

import random

import common

ORTH = ((2, 0), (-2, 0), (0, 2), (0, -2))
DIAG = ((2, 2), (2, -2), (-2, 2), (-2, -2))
MIN_SIDE, MAX_SIDE = 14, 30


def _is_int(x):
  return isinstance(x, int) and not isinstance(x, bool)


def _add(p, d):
  return (p[0] + d[0], p[1] + d[1])


def _perp(d):
  return [(d[1], d[0]), (-d[1], -d[0])]


def _pattern(kind, a, b):
  """3x3 pattern: ring (outer a, centre b) or checker (corners/centre a)."""
  if kind == "ring":
    return [[a, a, a], [a, b, a], [a, a, a]]
  return [[a if (i + j) % 2 == 0 else b for j in range(3)] for i in range(3)]


def _dot_cells(segments):
  """Maps every dot cell to its colour; rejects conflicting overlaps."""
  cells = {}
  for colour, r0, c0, r1, c1 in segments:
    if r0 == r1:
      pts = [(r0, c) for c in range(min(c0, c1), max(c0, c1) + 1, 2)]
    else:
      pts = [(r, c0) for r in range(min(r0, r1), max(r0, r1) + 1, 2)]
    for p in pts:
      if cells.get(p, colour) != colour:
        raise ValueError("two segments give one cell different colours")
      cells[p] = colour
  return cells


def _render(height, width, background, boxes, dots):
  g = common.grid(width, height, background)
  for (r, c), colour in dots.items():
    g[r][c] = colour
  for kind, top, left, a, b in boxes:
    pat = _pattern(kind, a, b)
    for i in range(3):
      for j in range(3):
        g[top + i][left + j] = pat[i][j]
  return g


def _box_cells(top, left):
  return {(top + i, left + j) for i in range(3) for j in range(3)}


def _edge_cells(top, left):
  """The 12 cells that share an edge with a 3x3 box."""
  out = []
  for i in range(3):
    out += [(top - 1, left + i), (top + 3, left + i),
            (top + i, left - 1), (top + i, left + 3)]
  return out


def _check_label(boxes, dots, target):
  """Checks that an explicit scene's target matches its latent path."""
  covered = set()
  for _, top, left, _, _ in boxes:
    covered |= _box_cells(top, left)
  if any(p in covered for p in dots):
    raise ValueError("a dot lies inside a box")
  start = [bx for bx in boxes if bx[0] == "checker"][0]
  touching = [p for p in _edge_cells(start[1], start[2]) if p in dots]
  if len(touching) != 1:
    raise ValueError("exactly one dot must touch the checker box")
  c = dots[touching[0]]
  seen, stack = {touching[0]}, [touching[0]]
  while stack:
    p = stack.pop()
    for d in ORTH:
      q = _add(p, d)
      if q not in seen and dots.get(q) == c:
        seen.add(q)
        stack.append(q)
  reached = [i for i, bx in enumerate(boxes) if bx[0] == "ring" and
             any(p in seen for p in _edge_cells(bx[1], bx[2]))]
  if reached != [target]:
    raise ValueError("target is not the unique ring reached by the path")


def _check_windows(grid, background, boxes):
  """Rejects solid (background-free) 3x3 windows that are not boxes."""
  tops = {(bx[1], bx[2]) for bx in boxes}
  h, w = len(grid), len(grid[0])
  for y in range(h - 2):
    for x in range(w - 2):
      if (y, x) in tops:
        continue
      if all(grid[y + i][x + j] != background
             for i in range(3) for j in range(3)):
        raise ValueError("solid 3x3 window outside the declared boxes")


def _check_explicit(height, width, background, boxes, segments, target):
  """Rejects malformed, partial or inconsistent explicit scenes."""
  if None in (height, width, background, segments, target):
    raise ValueError("explicit boxes need height, width, background, "
                     "segments and target")
  for name, v in (("height", height), ("width", width),
                  ("background", background), ("target", target)):
    if not _is_int(v):
      raise ValueError("%s must be an integer" % name)
  if not (1 <= height <= 30 and 1 <= width <= 30):
    raise ValueError("grid sides must be 1..30")
  if not 0 <= background <= 9:
    raise ValueError("background must be 0..9")
  if not isinstance(boxes, (list, tuple)):
    raise ValueError("boxes must be a list")
  if not isinstance(segments, (list, tuple)):
    raise ValueError("segments must be a list")
  for box in boxes:
    if not isinstance(box, (list, tuple)) or len(box) != 5:
      raise ValueError("boxes are (kind, top, left, a, b)")
    kind, top, left, a, b = box
    if kind not in ("ring", "checker"):
      raise ValueError("box kind must be 'ring' or 'checker'")
    if not all(_is_int(v) for v in (top, left, a, b)):
      raise ValueError("box coordinates and colours must be integers")
    if not (0 <= top <= height - 3 and 0 <= left <= width - 3):
      raise ValueError("box out of bounds")
    if not (0 <= a <= 9 and 0 <= b <= 9):
      raise ValueError("box colours must be 0..9")
    if a == b or background in (a, b):
      raise ValueError("box colours must differ from each other and bg")
  if sum(1 for bx in boxes if bx[0] == "checker") != 1:
    raise ValueError("exactly one checker box is required")
  for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
      if max(abs(boxes[i][1] - boxes[j][1]),
             abs(boxes[i][2] - boxes[j][2])) < 4:
        raise ValueError("boxes overlap or touch")
  for seg in segments:
    if not isinstance(seg, (list, tuple)) or len(seg) != 5:
      raise ValueError("segments are (colour, r0, c0, r1, c1)")
    if not all(_is_int(v) for v in seg):
      raise ValueError("segment values must be integers")
    colour, r0, c0, r1, c1 = seg
    if not 0 <= colour <= 9 or colour == background:
      raise ValueError("dot colour must be 0..9 and differ from background")
    if r0 != r1 and c0 != c1:
      raise ValueError("segments must lie on one row or column")
    if (r1 - r0) % 2 or (c1 - c0) % 2:
      raise ValueError("segment endpoints must be an even distance apart")
    for r, c in ((r0, c0), (r1, c1)):
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError("segment out of bounds")
  if not 0 <= target < len(boxes) or boxes[target][0] != "ring":
    raise ValueError("target must index a ring box")
  dots = _dot_cells(segments)
  if len({(r % 2, c % 2) for r, c in dots}) > 1:
    raise ValueError("all dots must lie on one lattice of spacing 2")
  _check_label(boxes, dots, target)
  _check_windows(_render(height, width, background, boxes, dots),
                 background, boxes)
  return dots


def _try_scene(height, width, background, disconnected_decoy=None):
  """One attempt at a random scene; returns None if the layout gets stuck."""
  pr, pc = random.randint(0, 1), random.randint(0, 1)
  boxes, boxset = [], set()
  parent, order, first, last, attach = {}, [], set(), set(), {}
  small = min(height, width) < 18
  need = 2 if small else 3
  trunk_lo = 3 if small else 4
  trunk_hi = max(6, (height + width) // 4)
  branch_hi = max(5, (height + width) // 5)

  def inside(p):
    return (1 <= p[0] <= height - 2 and 1 <= p[1] <= width - 2 and
            p[0] % 2 == pr and p[1] % 2 == pc)

  def ok_dot(p, prev, pset):
    if not inside(p) or p in parent or p in pset or p in boxset:
      return False
    for d in ORTH:
      n = _add(p, d)
      if n == prev:
        continue
      if n in parent or n in pset or n in boxset:
        return False
    for d in DIAG:
      if _add(p, d) in boxset:
        return False
    return True

  def ok_box(b, lastdot, pset):
    if not inside(b) or b in parent or b in pset or b in boxset:
      return False
    for d in ORTH + DIAG:
      n = _add(b, d)
      if n == lastdot:
        continue
      if n in parent or n in pset:
        return False
    for o in boxes:
      if max(abs(o[0] - b[0]), abs(o[1] - b[1])) < 4:
        return False
    return True

  def walk(origin, d0, lo, hi):
    pend, pset, cur, d = [], set(), origin, d0
    length = random.randint(lo, hi)
    seg, k = random.randint(1, 4), 0
    while len(pend) < length:
      p = _add(cur, d)
      if not ok_dot(p, cur, pset):
        if not pend:
          return None
        opts = _perp(d)
        random.shuffle(opts)
        for nd in opts:
          q = _add(cur, nd)
          if ok_dot(q, cur, pset):
            d, p = nd, q
            break
        else:
          return None
        seg, k = random.randint(2, 5), 0
      pend.append(p)
      pset.add(p)
      cur = p
      k += 1
      if k >= seg:
        d = random.choice(_perp(d))
        seg, k = random.randint(2, 5), 0
    side = _perp(d)
    random.shuffle(side)
    for nd in [d] + side:
      b = _add(cur, nd)
      if ok_box(b, cur, pset):
        return pend, b
    return None

  def commit(pend, b, par0):
    for i, p in enumerate(pend):
      parent[p] = par0 if i == 0 else pend[i - 1]
      order.append(p)
    first.add(pend[0])
    last.add(pend[-1])
    attach[len(boxes)] = pend[-1]
    boxes.append(b)
    boxset.add(b)

  pts = [(r, c) for r in range(1, height - 1) for c in range(1, width - 1)
         if inside((r, c))]
  start = random.choice(pts)
  boxes.append(start)
  boxset.add(start)
  for _ in range(30):
    res = walk(start, random.choice(ORTH), trunk_lo, trunk_hi)
    if res:
      commit(res[0], res[1], "S")
      break
  else:
    return None
  goal = random.randint(need, max(need, min(7, 3 + (height * width) // 200)))
  for _ in range(100):
    if len(boxes) - 1 >= goal:
      break
    cands = [p for p in order if p not in last]
    if not cands:
      break
    q = random.choice(cands)
    res = walk(q, random.choice(ORTH), 2, branch_hi)
    if res:
      commit(res[0], res[1], q)
  if len(boxes) - 1 < need:
    return None

  def chain(idx):
    out, p = [], attach[idx]
    while p != "S":
      out.append(p)
      p = parent[p]
    return out

  tcands = [i for i in range(1, len(boxes)) if len(chain(i)) >= 3]
  if not tcands:
    return None
  t = random.choice(tcands)
  main = set(chain(t))
  if random.random() < 0.4:
    dirs = list(ORTH)
    random.shuffle(dirs)
    for d in dirs:
      res = walk(boxes[t], d, 2, branch_hi)
      if res:
        commit(res[0], res[1], "T")
        break

  bg = background if background is not None else random.randint(0, 9)
  pal = [x for x in range(10) if x != bg]
  a, b = random.sample(pal, 2)
  if random.random() < 0.8:
    cpool = [x for x in pal if x not in (a, b)]
  else:
    cpool = pal
  c = random.choice(cpool)
  others = [x for x in pal if x != c]
  colour = {}
  for p in order:
    par = parent[p]
    if p in main:
      colour[p] = c
    elif par == "T" or par in main:
      colour[p] = random.choice(others)
    elif p in first:
      colour[p] = colour[par] if random.random() < 0.35 else random.choice(
          others)
    else:
      colour[p] = colour[par]

  # A wrong-colour barrier separates the added path-colour tail from main.
  # Geometry is still the constructed tree; no main-chain dot is recoloured.
  if disconnected_decoy is True or (disconnected_decoy is None and random.random() < 0.5):
    candidates = []
    for idx, endpoint in attach.items():
      if idx == t:
        continue
      tail, q = [], endpoint
      while q in parent and q not in main:
        tail.append(q)
        q = parent[q]
      tail.reverse()
      if len(tail) >= 2 and colour[tail[0]] != c:
        candidates.append(tail)
    if not candidates:
      if disconnected_decoy is True:
        return None
    else:
      tail = random.choice(candidates)
      for q in tail[1:]:
        colour[q] = c

  box_list = [("checker", start[0] - 1, start[1] - 1, a, b)]
  pairs = [(r, z) for r in pal for z in pal if r != z]
  chosen = random.sample(pairs, len(boxes) - 1)
  for ctr, (r, z) in zip(boxes[1:], chosen):
    box_list.append(("ring", ctr[0] - 1, ctr[1] - 1, r, z))
  segments = [(colour[p], p[0], p[1], p[0], p[1]) for p in order]
  return height, width, bg, box_list, segments, t


def generate(height=None, width=None, background=None, boxes=None,
             segments=None, target=None, disconnected_decoy=None):
  """Builds one input/output pair.

  Args:
    height: grid height (int). Random mode: 14..30, default random 16..30
      (22 in all fixtures; other sizes are synthetic extensions).
    width: grid width (int), same ranges as height.
    background: background colour 0..9 (random if None in random mode,
      required in explicit mode). Booleans are rejected.
    boxes: list of (kind, top, left, a, b); kind is "ring" (outer a, centre b)
      or "checker" (corners and centre a, edges b). If None, a random scene
      is built, and segments/target must also be None.
    segments: list of (colour, r0, c0, r1, c1) dotted segments with step 2
      along a single row or column, all on one lattice parity. Required with
      boxes.
    disconnected_decoy: random mode only; True requires a disconnected
      path-colour tail ending at a distractor ring, False disables it, and
      None attempts one in half the scenes. This is a synthetic extension.
    target: index into boxes of the ring box reached by the start-coloured
      path. Required with boxes, and checked against the latent path.
  """
  if disconnected_decoy is not None and type(disconnected_decoy) is not bool:
    raise ValueError("disconnected_decoy must be a boolean or None")
  if boxes is not None and disconnected_decoy is not None:
    raise ValueError("disconnected_decoy is a random-mode control")
  if boxes is None:
    if segments is not None or target is not None:
      raise ValueError("segments/target are only valid with explicit boxes")
    if background is not None:
      if not _is_int(background) or not 0 <= background <= 9:
        raise ValueError("background must be an integer 0..9")
    for side in (height, width):
      if side is not None:
        if not _is_int(side) or not MIN_SIDE <= side <= MAX_SIDE:
          raise ValueError("random scenes need integer sides %d..%d" %
                           (MIN_SIDE, MAX_SIDE))
    h = height if height is not None else random.randint(16, MAX_SIDE)
    w = width if width is not None else random.randint(16, MAX_SIDE)
    scene = None
    for _ in range(600):
      scene = _try_scene(h, w, background, disconnected_decoy)
      if scene is not None:
        break
    if scene is None:
      raise RuntimeError("could not build a scene of size %dx%d" % (h, w))
    height, width, background, boxes, segments, target = scene
    dots = _dot_cells(segments)
  else:
    dots = _check_explicit(height, width, background, boxes, segments,
                           target)
  grid = _render(height, width, background, boxes, dots)
  if boxes is not None:
    _check_label(boxes, dots, target)
    _check_windows(grid, background, boxes)
  kind, _, _, a, b = boxes[target]
  return {"input": grid, "output": _pattern(kind, a, b)}


def validate():
  """Reconstructs the canonical pairs from explicit latent parameters."""
  train = [
      generate(22, 22, 8,
               [("ring", 1, 0, 1, 3), ("checker", 1, 16, 2, 9),
                ("ring", 15, 2, 9, 4), ("ring", 15, 6, 5, 2),
                ("ring", 17, 14, 6, 7)],
               [(2, 2, 3, 2, 5), (3, 2, 7, 2, 15), (3, 4, 7, 10, 7),
                (3, 10, 9, 10, 15), (3, 12, 15, 16, 15), (4, 10, 3, 10, 5),
                (4, 12, 3, 14, 3), (5, 12, 7, 14, 7)], 4),
      generate(22, 22, 2,
               [("checker", 1, 1, 8, 1), ("ring", 5, 17, 1, 3),
                ("ring", 7, 1, 9, 5), ("ring", 17, 3, 3, 1),
                ("ring", 19, 17, 7, 9)],
               [(4, 2, 4, 2, 10), (4, 4, 10, 14, 10), (4, 14, 4, 14, 8),
                (4, 16, 4, 16, 4), (3, 6, 12, 6, 16), (9, 8, 4, 8, 8),
                (8, 14, 12, 14, 18), (8, 16, 18, 18, 18)], 3),
      generate(22, 22, 1,
               [("ring", 1, 18, 4, 6), ("ring", 7, 12, 7, 2),
                ("ring", 13, 14, 6, 8), ("checker", 17, 2, 3, 6),
                ("ring", 17, 18, 2, 8)],
               [(8, 2, 3, 2, 17), (8, 4, 3, 16, 3), (3, 4, 7, 8, 7),
                (3, 8, 9, 8, 11), (4, 10, 7, 14, 7), (4, 14, 9, 14, 13),
                (3, 4, 19, 16, 19)], 0),
  ]
  test = [
      generate(22, 22, 4,
               [("ring", 1, 1, 2, 8), ("ring", 7, 1, 1, 6),
                ("ring", 9, 15, 6, 1), ("ring", 13, 1, 3, 1),
                ("ring", 17, 1, 6, 8), ("checker", 17, 15, 8, 9)],
               [(1, 2, 4, 2, 12), (1, 4, 12, 4, 20), (1, 6, 20, 14, 20),
                (1, 14, 16, 14, 18), (1, 16, 16, 16, 16), (6, 6, 16, 8, 16),
                (3, 6, 12, 8, 12), (3, 8, 4, 8, 10), (2, 10, 12, 16, 12),
                (2, 18, 4, 18, 12), (9, 10, 8, 12, 8), (9, 14, 4, 14, 8)],
               0),
  ]
  return {"train": train, "test": test}
