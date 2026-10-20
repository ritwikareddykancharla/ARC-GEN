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

"""ARC-GEN style generator for task a395ee82.

Rule:
  The input holds one multi-cell shape of colour A and a constellation of
  single dots on a lattice with spacing 2. Exactly one dot has colour A. This
  is the centre dot. Every other dot has colour B. The constellation is a map
  of where copies of the shape go.
  - The centre dot stands for the shape itself. The shape stays in place but
    is recoloured to B.
  - A B dot at cell offset (2*uy, 2*ux) from the centre dot produces a copy of
    the shape in colour A, shifted by (uy*h, ux*w). Here h x w is the shape's
    bounding box.
  All dots are erased. Copies are clipped at the grid border.

Scope:
  The four canonical pairs are 22x22. None of them clips a copy. The reference
  prose says pair 3 clips at the left edge, but its copies at (5,0) and (8,0)
  lie fully inside the grid. The canonical pairs are rebuilt exactly from
  explicit latent arguments in validate().

  Random grids are 12..30 per side and may be rectangular. Sizes other than
  22 are a synthetic extension that the rule permits.

  Random shapes have a 2..4 by 2..4 bounding box. The mask is a random
  4-connected mask that touches every row and column of its box and is not
  a full rectangle.

  Random constellations have 1..5 B dots by default. Up to 24 can be
  requested with num_dots. They are grown 8-connected on the unit lattice
  within +-2 units of the centre, so the gcd of the dot offsets is exactly 2.

Clipping (synthetic extension, labelled as such):
  The clipping mode is resolved ONCE per generate() call, before any retry.
  Shape placement is then enumerated subject to that mode.
  - "clip": at least one copy is clipped, and every clipped copy keeps at
    least half of its cells.
  - "noclip": every copy lies fully inside the grid.
  - "any": clipping is permitted (half-cells rule still holds) but not
    required.
  With default arguments and random placement, "clip" is drawn with
  probability 0.15 and "noclip" otherwise. A forced mode is never silently
  downgraded. If it cannot be met, ValueError is raised.

Invariants:
  - No dot lies inside the shape's bounding box or in the ring of cells
    around it.
  - The background is strictly the most frequent input colour.
  - The three colours are distinct.
  - Copy boxes never overlap each other or the original box.
"""

import math
import random

import common


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _mask_from_rows(rows):
  if not isinstance(rows, (list, tuple)) or not rows:
    raise ValueError("shape must be a non-empty list of strings")
  if any(not isinstance(r, str) for r in rows):
    raise ValueError("shape must be a non-empty list of strings")
  if not rows[0] or any(len(r) != len(rows[0]) for r in rows):
    raise ValueError("shape rows must be non-empty and rectangular")
  for r in rows:
    for ch in r:
      if ch not in "X.":
        raise ValueError("shape rows may only contain 'X' and '.'")
  return [[1 if ch == "X" else 0 for ch in row] for row in rows]


def _connected(cells):
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
      p = (r + dr, c + dc)
      if p in cells and p not in seen:
        seen.add(p)
        stack.append(p)
  return len(seen) == len(cells)


def _check_mask(mask):
  h, w = len(mask), len(mask[0])
  if h > 30 or w > 30:
    raise ValueError("shape is larger than 30 cells per side")
  cells = [(r, c) for r in range(h) for c in range(w) if mask[r][c]]
  if len(cells) < 2:
    raise ValueError("shape needs at least two cells")
  if len({r for r, _ in cells}) != h or len({c for _, c in cells}) != w:
    raise ValueError("shape must touch every row and column of its box")
  if not _connected(cells):
    raise ValueError("shape must be 4-connected")


def _random_mask(h, w):
  """Random 4-connected mask covering every row and column, not full."""
  for _ in range(100):
    cells = {(random.randrange(h), random.randrange(w))}

    def frontier():
      out = set()
      for (r, c) in cells:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
          rr, cc = r + dr, c + dc
          if 0 <= rr < h and 0 <= cc < w and (rr, cc) not in cells:
            out.add((rr, cc))
      return sorted(out)

    while (len({r for r, _ in cells}) < h or
           len({c for _, c in cells}) < w):
      cells.add(random.choice(frontier()))
    for _ in range(random.randint(0, (h * w) // 3)):
      f = frontier()
      if not f:
        break
      cells.add(random.choice(f))
    if 3 <= len(cells) < h * w:
      return [[1 if (r, c) in cells else 0 for c in range(w)]
              for r in range(h)]
  # Practically unreachable. If reached, return a randomly oriented L shape.
  rows = [[1] * w] + [[1] + [0] * (w - 1) for _ in range(h - 1)]
  if random.random() < 0.5:
    rows = rows[::-1]
  if random.random() < 0.5:
    rows = [r[::-1] for r in rows]
  return rows


def _random_offsets(k):
  """Return k unit offsets (centre excluded) of an 8-connected cluster."""
  pts = {(0, 0)}
  while len(pts) < k + 1:
    cand = set()
    for (y, x) in pts:
      for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
          p = (y + dy, x + dx)
          if p not in pts and -2 <= p[0] <= 2 and -2 <= p[1] <= 2:
            cand.add(p)
    pts.add(random.choice(sorted(cand)))
  return sorted(p for p in pts if p != (0, 0))


def _parse_offsets(offsets):
  if not isinstance(offsets, (list, tuple)) or not offsets:
    raise ValueError("offsets must be a non-empty list of (uy, ux) pairs")
  offs = []
  for o in offsets:
    if (not isinstance(o, (list, tuple)) or len(o) != 2 or
        not all(_is_int(v) for v in o)):
      raise ValueError("offsets must be pairs of integers")
    offs.append((o[0], o[1]))
  if len(set(offs)) != len(offs) or (0, 0) in offs:
    raise ValueError("offsets must be distinct and non-zero")
  g = 0
  for uy, ux in offs:
    g = math.gcd(g, math.gcd(abs(uy), abs(ux)))
  if g != 1:
    raise ValueError("offsets must have gcd 1 so the dot spacing is 2")
  return offs


def _check_pair(p, name):
  if (not isinstance(p, (list, tuple)) or len(p) != 2 or
      not all(_is_int(v) for v in p)):
    raise ValueError(name + " must be a (row, col) pair of integers")
  return (p[0], p[1])


def _resolve_colours(bg, a, b):
  given = [c for c in (bg, a, b) if c is not None]
  for c in given:
    if not _is_int(c) or not 0 <= c <= 9:
      raise ValueError("colours must be integers 0..9")
  if len(set(given)) != len(given):
    raise ValueError("bg, shape_color and dot_color must be distinct")
  pool = [c for c in range(10) if c not in given]
  random.shuffle(pool)
  bg = bg if bg is not None else pool.pop()
  a = a if a is not None else pool.pop()
  b = b if b is not None else pool.pop()
  return bg, a, b


def _resolve_mode(allow_clip, force_clip, pos_fixed):
  """Resolve the clipping mode once per generate() call."""
  if force_clip is True:
    return "clip"
  if allow_clip is False:
    return "noclip"
  if allow_clip is True:
    return "any"
  # allow_clip is None.
  if force_clip is False:
    return "any" if pos_fixed else "noclip"
  if pos_fixed:
    return "any"
  return "clip" if random.random() < 0.15 else "noclip"


def _stamp(g, mask, oy, ox, colour):
  height, width = len(g), len(g[0])
  for dy, row in enumerate(mask):
    for dx, v in enumerate(row):
      if v:
        y, x = oy + dy, ox + dx
        if 0 <= y < height and 0 <= x < width:
          g[y][x] = colour


def _visible_count(mask, oy, ox, height, width):
  n = 0
  for dy, row in enumerate(mask):
    for dx, v in enumerate(row):
      if v and 0 <= oy + dy < height and 0 <= ox + dx < width:
        n += 1
  return n


def _placement_ok(H, W, mask, total, offs, r0, c0, mode):
  """Check copy placement for a shape at (r0, c0) under the given mode."""
  h, w = len(mask), len(mask[0])
  if not (0 <= r0 <= H - h and 0 <= c0 <= W - w):
    return False
  clipped = 0
  for (uy, ux) in offs:
    oy, ox = r0 + uy * h, c0 + ux * w
    if 0 <= oy and oy + h <= H and 0 <= ox and ox + w <= W:
      continue
    if mode == "noclip":
      return False
    if 2 * _visible_count(mask, oy, ox, H, W) < total:
      return False
    clipped += 1
  return mode != "clip" or clipped > 0


def _shape_positions(H, W, mask, total, offs, mode, fixed_pos):
  h, w = len(mask), len(mask[0])
  if fixed_pos is not None:
    cand = [fixed_pos]
  else:
    cand = [(r, c) for r in range(H - h + 1) for c in range(W - w + 1)]
  return [p for p in cand
          if _placement_ok(H, W, mask, total, offs, p[0], p[1], mode)]


def _centre_positions(H, W, units, r0, c0, h, w, fixed_centre):
  miny = min(u[0] for u in units)
  maxy = max(u[0] for u in units)
  minx = min(u[1] for u in units)
  maxx = max(u[1] for u in units)
  if fixed_centre is not None:
    cand = [fixed_centre]
  else:
    cand = [(y, x) for y in range(-2 * miny, H - 2 * maxy)
            for x in range(-2 * minx, W - 2 * maxx)]
  out = []
  for (cy, cx) in cand:
    good = True
    for (uy, ux) in units:
      y, x = cy + 2 * uy, cx + 2 * ux
      if not (0 <= y < H and 0 <= x < W):
        good = False
        break
      # Dots stay out of the shape's box and the ring around it.
      if r0 - 1 <= y <= r0 + h and c0 - 1 <= x <= c0 + w:
        good = False
        break
    if good:
      out.append((cy, cx))
  return out


def _build(height, width, bg, a, b, mask, pos, centre, offsets):
  h, w = len(mask), len(mask[0])
  r0, c0 = pos
  cy, cx = centre
  grid = common.grid(width, height, bg)
  _stamp(grid, mask, r0, c0, a)
  grid[cy][cx] = a
  for (uy, ux) in offsets:
    grid[cy + 2 * uy][cx + 2 * ux] = b
  output = common.grid(width, height, bg)
  _stamp(output, mask, r0, c0, b)
  for (uy, ux) in offsets:
    _stamp(output, mask, r0 + uy * h, c0 + ux * w, a)
  for g in (grid, output):
    if len(g) != height or any(len(row) != width for row in g):
      raise RuntimeError("grid dimensions do not match height/width")
  return {"input": grid, "output": output}


def generate(height=None, width=None, bg=None, shape_color=None,
             dot_color=None, shape=None, shape_pos=None, centre=None,
             offsets=None, num_dots=None, allow_clip=None, force_clip=None):
  """Generate one input/output pair.

  Every argument is optional. Unspecified latents are sampled. Specified ones
  are honoured exactly, or a ValueError is raised.

  Args:
    height: grid rows (1..30). Random default is 12..30, raised if needed to
      fit fixed latents.
    width: grid columns (1..30). Random default is 12..30, raised likewise.
    bg: background colour.
    shape_color: colour A of the shape and of the centre dot.
    dot_color: colour B of the other constellation dots.
    shape: list of strings, using 'X' for shape cells and '.' for holes. It
      must have at least two cells, be 4-connected, and touch every row and
      column of its box. Full rectangles are a labelled extension.
    shape_pos: (row, col) of the top-left of the shape's box. The whole box
      must lie inside the grid. Negative or out-of-range values are rejected
      immediately.
    centre: (row, col) of the centre dot. It must lie inside the grid.
    offsets: unit offsets (uy, ux) of the B dots. A dot lies at
      centre + 2*(uy, ux). The gcd of all components must be 1.
    num_dots: number of B dots (1..24). Random default is 1..5. If offsets
      is also given, the two must agree.
    allow_clip: False means every copy lies fully inside the grid. True means
      clipping is permitted, with each clipped copy keeping at least half of
      its cells.
    force_clip: True means at least one copy must be clipped. It is
      incompatible with allow_clip=False and is never silently downgraded.
      False means clipping is not forced. In that case clipping is permitted
      if allow_clip is True or shape_pos is explicit, and forbidden
      otherwise.
    With both clip flags None, an explicit shape_pos permits clipping. With
    random placement, a single 15% draw per call chooses forced clipping and
    otherwise forbids it.
  """
  for v in (height, width):
    if v is not None and (not _is_int(v) or not 1 <= v <= 30):
      raise ValueError("grid sides must be integers 1..30")
  for name, v in (("allow_clip", allow_clip), ("force_clip", force_clip)):
    if v is not None and not isinstance(v, bool):
      raise ValueError(name + " must be None, True or False")
  if allow_clip is False and force_clip is True:
    raise ValueError("force_clip=True is incompatible with allow_clip=False")
  if num_dots is not None and (not _is_int(num_dots) or
                               not 1 <= num_dots <= 24):
    raise ValueError("num_dots must be an integer 1..24")
  cbg, ca, cb = _resolve_colours(bg, shape_color, dot_color)

  fixed_mask = None
  if shape is not None:
    fixed_mask = _mask_from_rows(shape)
    _check_mask(fixed_mask)
  fixed_offs = None
  if offsets is not None:
    fixed_offs = _parse_offsets(offsets)
    if num_dots is not None and num_dots != len(fixed_offs):
      raise ValueError("num_dots does not match len(offsets)")
  fixed_pos = (_check_pair(shape_pos, "shape_pos")
               if shape_pos is not None else None)
  fixed_centre = (_check_pair(centre, "centre")
                  if centre is not None else None)

  max_h = height if height is not None else 30
  max_w = width if width is not None else 30
  need_h, need_w = 1, 1
  if fixed_mask is not None:
    mh, mw = len(fixed_mask), len(fixed_mask[0])
    if mh > max_h or mw > max_w:
      raise ValueError("shape does not fit in the grid")
    need_h, need_w = max(need_h, mh), max(need_w, mw)
  if fixed_pos is not None:
    pr, pc = fixed_pos
    ph = len(fixed_mask) if fixed_mask is not None else 2
    pw = len(fixed_mask[0]) if fixed_mask is not None else 2
    if pr < 0 or pc < 0 or pr + ph > max_h or pc + pw > max_w:
      raise ValueError("shape_pos puts the shape box outside the grid")
    need_h, need_w = max(need_h, pr + ph), max(need_w, pc + pw)
  if fixed_offs is not None:
    units = fixed_offs + [(0, 0)]
    sy = 2 * (max(u[0] for u in units) - min(u[0] for u in units)) + 1
    sx = 2 * (max(u[1] for u in units) - min(u[1] for u in units)) + 1
    if sy > max_h or sx > max_w:
      raise ValueError("constellation does not fit in the grid")
    need_h, need_w = max(need_h, sy), max(need_w, sx)
  if fixed_centre is not None:
    cy0, cx0 = fixed_centre
    if not (0 <= cy0 < max_h and 0 <= cx0 < max_w):
      raise ValueError("centre lies outside the grid")
    need_h, need_w = max(need_h, cy0 + 1), max(need_w, cx0 + 1)
    if fixed_offs is not None:
      for (uy, ux) in fixed_offs:
        y, x = cy0 + 2 * uy, cx0 + 2 * ux
        if not (0 <= y < max_h and 0 <= x < max_w):
          raise ValueError("a dot lies outside the grid")
        need_h, need_w = max(need_h, y + 1), max(need_w, x + 1)

  # The clipping mode is drawn once, before any retry.
  mode = _resolve_mode(allow_clip, force_clip, fixed_pos is not None)

  deterministic = (height is not None and width is not None and
                   fixed_mask is not None and fixed_offs is not None and
                   fixed_pos is not None and fixed_centre is not None)
  attempts = 1 if deterministic else 400
  reason = "no attempt made"

  for _ in range(attempts):
    H = (height if height is not None
         else random.randint(max(12, need_h), 30))
    W = (width if width is not None
         else random.randint(max(12, need_w), 30))
    if fixed_mask is not None:
      mask = fixed_mask
    else:
      if H < 2 or W < 2:
        reason = "grid too small for a random shape"
        continue
      mask = _random_mask(random.randint(2, min(4, H)),
                          random.randint(2, min(4, W)))
    h, w = len(mask), len(mask[0])
    if h > H or w > W:
      reason = "shape does not fit in the grid"
      continue
    total = sum(sum(r) for r in mask)
    if fixed_offs is not None:
      offs = fixed_offs
    else:
      k = num_dots if num_dots is not None else random.randint(1, 5)
      offs = _random_offsets(k)
    units = offs + [(0, 0)]

    # The background must be strictly the most frequent input colour.
    n_a = total + 1
    n_b = len(offs)
    if H * W - n_a - n_b <= max(n_a, n_b):
      reason = "background would not be the most frequent colour"
      continue

    positions = _shape_positions(H, W, mask, total, offs, mode, fixed_pos)
    if not positions:
      reason = "no shape placement satisfies clipping mode '%s'" % mode
      continue
    random.shuffle(positions)
    chosen = None
    for (r0, c0) in positions[:12]:
      centres = _centre_positions(H, W, units, r0, c0, h, w, fixed_centre)
      if centres:
        chosen = ((r0, c0), random.choice(centres))
        break
    if chosen is None:
      reason = "no centre keeps the dots inside and clear of the shape box"
      continue
    return _build(H, W, cbg, ca, cb, mask, chosen[0], chosen[1], offs)
  raise ValueError("could not place scene with given parameters: " + reason)


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(height=22, width=22, bg=4, shape_color=2, dot_color=8,
               shape=[".X.", "XXX", "X.X"], shape_pos=(3, 12),
               centre=(8, 4),
               offsets=[(-1, 0), (0, -1), (0, 1), (1, 0), (2, 0)]),
      generate(height=22, width=22, bg=3, shape_color=1, dot_color=2,
               shape=["XXX", ".XX", "XX.", "XXX"], shape_pos=(6, 5),
               centre=(13, 15),
               offsets=[(-1, -1), (-1, 0), (-1, 1), (1, 0)]),
      generate(height=22, width=22, bg=7, shape_color=4, dot_color=6,
               shape=["XX.", "XXX", ".XX"], shape_pos=(5, 3),
               centre=(10, 13),
               offsets=[(-1, 0), (0, -1), (0, 1), (1, -1), (1, 1)]),
  ]
  test = [
      generate(height=22, width=22, bg=8, shape_color=6, dot_color=4,
               shape=[".XX", "XXX", ".X.", "XXX"], shape_pos=(5, 8),
               centre=(14, 6),
               offsets=[(-1, 1), (0, -2), (0, -1), (0, 1), (1, -2)]),
  ]
  return {"train": train, "test": test}
