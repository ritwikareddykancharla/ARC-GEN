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

"""ARC-GEN style generator for task b10624e5.

Rule: one full row and one full column of colour 1 split a background-4 grid
into four quadrants. One quadrant holds a template: a solid square block of
colour 2 with rectangular coloured pieces attached. A piece touches the block
or an earlier piece. Each other quadrant holds at most one lone square of
colour 2. The output redraws the template around every lone square:
  * Scale: P is the template's tight non-background bounding box. It is
    resampled by floor sampling Q[i][j] = P[i*s0//s][j*s0//s], where s0 is the
    template block size and s the target size.
  * Mirror: left-right if the target quadrant is in the other column half,
    and up-down if it is in the other row half.
  * Align: the 2-block of the copy lands exactly on the target. Only
    non-background cells are painted. Cells outside the grid are clipped.

Scope:
  * Sizes. Random quadrant sides are sampled from 9..15 per axis. A side
    requested for a random scene must lie in 7..22. The opposite side is
    then sampled so that the axis stays within 30 cells. Non-square grids are
    common.
  * Layout. The template may sit in any of the four quadrants. Two or three
    target quadrants are used, so one quadrant may be empty.
  * Template modes:
      - aligned: pieces lie on a lattice of f-cell units with f in 1..3, and
        the block is one unit (s0 = f). Targets 1..4 scale exactly. This
        includes enlarging, identity, and fractional or shrinking ratios such
        as 3 -> 2 and 2 -> 1.
      - fine: s0 = 2 and pieces are drawn at single-cell resolution. Only
        target sizes 2 and 4 are used, so information-destroying resampling
        never happens. At least one target has size 4.
  * Construction is constructive, with no blind rejection over a whole
    layout. Target sizes are chosen first. Each axis then gets a budget of
    template extent in units. That budget is split between the inner side
    (toward the dividers) and the outer side. It is capped so that every
    scaled stamp fits completely inside its target quadrant when the target
    sits at its innermost legal position. The innermost position is therefore
    always a valid fallback. Random positions further out produce clipping at
    the outer border. This keeps every layout down to 7-cell quadrants, and
    the 22/7 extremes, reliable in both modes. The requested mode is never
    swapped for an easier one.
  * Random-scene guarantees for every stamp:
      - every template colour stays visible;
      - at least half of the attachment cells stay visible;
      - the visible stamp differs from all three wrong mirror orientations;
      - a one-cell gap is kept from the dividers.
    The template itself is never symmetric under a left-right flip, an
    up-down flip or a 180-degree turn.
  * Colours. Background (4), divider (1) and block (2) are fixed, as in the
    task. Piece colours are distinct and come from {1,3,5,6,7,8,9}.

Explicit scenes (template, template_pos, targets) reconstruct the fixtures.
The raw template_pos and the raw patch bounds are checked before the template
is cropped to its non-background bounding box. Explicit targets must satisfy
the same conditions as random ones:
  * exact scaling (a solid s x s block and no lost colour);
  * lossless resampling (no truncated rows or columns, and every dropped row
    or column of a shrink duplicates a sampled one);
  * the divider gap;
  * colour and attachment visibility;
  * orientation uniqueness.
The three canonical pairs satisfy all of these, so no exception is needed.
"""

import random

import common

BG = 4
DIV = 1
BLOCK = 2
PALETTE = [1, 3, 5, 6, 7, 8, 9]
MIN_SIDE = 9
MAX_SIDE = 15
MAX_GRID = 30
ORIENTS = ((False, False), (True, False), (False, True), (True, True))


def _is_int(v):
  """Strict integer test (rejects bool and float)."""
  return type(v) is int


def _block_info(P):
  """Returns (row, col, size) of the colour-2 block inside template patch P."""
  cells = [(r, c) for r, row in enumerate(P) for c, v in enumerate(row)
           if v == BLOCK]
  br = min(r for r, _ in cells)
  bc = min(c for _, c in cells)
  s0 = max(r for r, _ in cells) - br + 1
  return br, bc, s0


def _stamp_geometry(P, br, bc, s0, s, flip_lr, flip_ud):
  """Scales and mirrors P for target size s; returns (Q, block_row, block_col)."""
  h = len(P) * s // s0
  w = len(P[0]) * s // s0
  Q = [[P[i * s0 // s][j * s0 // s] for j in range(w)] for i in range(h)]
  r2 = br * s // s0
  c2 = bc * s // s0
  if flip_lr:
    Q = [row[::-1] for row in Q]
    c2 = w - (c2 + s)
  if flip_ud:
    Q = Q[::-1]
    r2 = h - (r2 + s)
  return Q, r2, c2


def _exact(P, Q, r2, c2, s):
  """True if the stamp keeps a solid s x s block at (r2, c2) and all colours."""
  if not Q or not Q[0]:
    return False
  if r2 < 0 or c2 < 0 or r2 + s > len(Q) or c2 + s > len(Q[0]):
    return False
  for i in range(s):
    for j in range(s):
      if Q[r2 + i][c2 + j] != BLOCK:
        return False
  if sum(row.count(BLOCK) for row in Q) != s * s:
    return False
  src = set(v for row in P for v in row) - {BG}
  dst = set(v for row in Q for v in row) - {BG}
  return src == dst


def _representatives(n, m, s0, s):
  """For each of n source lines, the last sampled source line at or before it."""
  samples = [i * s0 // s for i in range(m)]
  out = []
  for r in range(n):
    best = 0
    for v in samples:
      if v <= r:
        best = v
    out.append(best)
  return out


def _lossless(P, s0, s):
  """True if floor resampling of P from s0 to s destroys no information."""
  h, w = len(P), len(P[0])
  if (h * s) % s0 or (w * s) % s0:
    return False
  if s >= s0:
    return True
  rrep = _representatives(h, h * s // s0, s0, s)
  crep = _representatives(w, w * s // s0, s0, s)
  for r in range(h):
    for c in range(w):
      if P[r][c] != P[rrep[r]][crep[c]]:
        return False
  return True


def _visible(Q, oy, ox, height, width):
  """Counts (visible, total) attachment cells of stamp Q placed at (oy, ox)."""
  vis = tot = 0
  for i, row in enumerate(Q):
    for j, v in enumerate(row):
      if v in (BG, BLOCK):
        continue
      tot += 1
      if 0 <= oy + i < height and 0 <= ox + j < width:
        vis += 1
  return vis, tot


def _painted(Q, oy, ox, height, width):
  """Returns {(row, col): colour} of the in-grid non-background stamp cells."""
  out = {}
  for i, row in enumerate(Q):
    for j, v in enumerate(row):
      yy, xx = oy + i, ox + j
      if v != BG and 0 <= yy < height and 0 <= xx < width:
        out[(yy, xx)] = v
  return out


def _stamp_ok(P, s, ty, tx, flip_lr, flip_ud, height, width):
  """Checks the visibility and orientation uniqueness of one placed stamp."""
  br, bc, s0 = _block_info(P)
  colours = set(v for row in P for v in row) - {BG, BLOCK}
  Q, r2, c2 = _stamp_geometry(P, br, bc, s0, s, flip_lr, flip_ud)
  vis, tot = _visible(Q, ty - r2, tx - c2, height, width)
  if tot == 0 or 2 * vis < tot:
    return False
  shown = _painted(Q, ty - r2, tx - c2, height, width)
  if not colours <= set(shown.values()):
    return False
  for (a, b) in ORIENTS:
    if (a, b) == (flip_lr, flip_ud):
      continue
    Qx, rx, cx = _stamp_geometry(P, br, bc, s0, s, a, b)
    if _painted(Qx, ty - rx, tx - cx, height, width) == shown:
      return False
  return True


def _side_ok(v, div, qi):
  """True if coordinate v lies in half qi with a one-cell gap to the divider."""
  return v <= div - 2 if qi == 0 else v >= div + 2


def _axis_sizes(a, b):
  """Samples the two side lengths of one axis, honouring fixed values."""
  if a is None and b is None:
    a = random.randint(MIN_SIDE, MAX_SIDE)
  if a is None:
    hi = min(MAX_SIDE, MAX_GRID - 1 - b)
    a = random.randint(min(MIN_SIDE, hi), hi)
  if b is None:
    hi = min(MAX_SIDE, MAX_GRID - 1 - a)
    b = random.randint(min(MIN_SIDE, hi), hi)
  return a, b


def _template_span(qi, div, total, extent):
  """Valid start range of a template patch along one axis (one-cell gap)."""
  if qi == 0:
    return 0, div - 1 - extent
  return div + 2, total - extent


def _target_span(qi, div, total, s, extent, off):
  """Returns (lo, hi, innermost) target starts for a stamp along one axis.

  The stamp's divider side keeps a one-cell gap, and the target square stays
  inside the grid. The outer side of the stamp may be clipped by the border.
  """
  if qi == 0:
    hi = div - 1 - extent + off
    return 0, hi, hi
  lo = div + 2 + off
  return lo, total - s, lo


def _build_template(k, f, box, dmax, nmax):
  """Grows a template from a k x k unit block inside an inclusive unit box.

  box is (row_lo, row_hi, col_lo, col_hi), relative to the block's top-left
  unit. Each piece is a rectangle of a fresh colour that touches the block or
  an earlier piece. Returns the patch scaled by f cells per unit, or None if
  the result is degenerate or mirror/rotation symmetric.
  """
  r_lo, r_hi, c_lo, c_hi = box
  occ = {}
  for r in range(k):
    for c in range(k):
      occ[(r, c)] = BLOCK
  placed = 0
  for colour in random.sample(PALETTE, random.randint(2, nmax)):
    for _ in range(8):
      h = random.randint(1, min(dmax, r_hi - r_lo + 1))
      w = random.randint(1, min(dmax, c_hi - c_lo + 1))
      cands = []
      for y in range(r_lo, r_hi - h + 2):
        for x in range(c_lo, c_hi - w + 2):
          cells = [(y + i, x + j) for i in range(h) for j in range(w)]
          if any(cl in occ for cl in cells):
            continue
          if any((r + dr, c + dc) in occ for (r, c) in cells
                 for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            cands.append(cells)
      if cands:
        for cl in random.choice(cands):
          occ[cl] = colour
        placed += 1
        break
  if placed < 2:
    return None
  rmin = min(r for r, _ in occ)
  rmax = max(r for r, _ in occ)
  cmin = min(c for _, c in occ)
  cmax = max(c for _, c in occ)
  fh = rmax - rmin + 1
  fw = cmax - cmin + 1
  P = [[occ.get((rmin + r // f, cmin + c // f), BG) for c in range(fw * f)]
       for r in range(fh * f)]
  lr = [row[::-1] for row in P]
  if P == lr or P == P[::-1] or P == lr[::-1]:
    return None
  return P


def _sample_sizes(others, lens, sizes, k, s0, mode):
  """Chooses a target size per quadrant that leaves room for >= 1 unit."""
  opts = {}
  for q in others:
    lim = min(lens[0][q[0]], lens[1][q[1]])
    o = [s for s in sizes if s + s // k <= lim]
    if not o:
      return None
    opts[q] = o
  for _ in range(30):
    pick = dict((q, random.choice(opts[q])) for q in others)
    vals = list(pick.values())
    if mode == "fine" and 4 not in vals:
      continue
    if mode == "aligned" and all(v == s0 for v in vals):
      continue
    return pick
  return None


def _random_scene(top, bottom, left, right, tq_req, mode, num_targets):
  """Samples sizes, template, its position and the target squares."""
  for _ in range(400):
    nt, nb = _axis_sizes(top, bottom)
    nl, nr = _axis_sizes(left, right)
    height, width = nt + nb + 1, nl + nr + 1
    if tq_req is not None:
      tq = tq_req
    else:
      tq = (random.randint(0, 1), random.randint(0, 1))
    lens = ({0: nt - 1, 1: nb - 1}, {0: nl - 1, 1: nr - 1})
    lt = (lens[0][tq[0]], lens[1][tq[1]])
    m = mode
    if m is None:
      m = "aligned" if random.random() < 0.65 else "fine"
    if m == "aligned":
      fopts = [f for f in (1, 2, 2, 2, 3) if min(lt) // f >= 2]
      if not fopts:
        continue
      k, f = 1, random.choice(fopts)
      sizes, ecap, dmax, nmax = [1, 2, 3, 4], 3, 2, 4
    else:
      k, f = 2, 1
      sizes, ecap, dmax, nmax = [2, 4], 5, 4, 5
    s0 = k * f
    others = [(a, b) for a in (0, 1) for b in (0, 1) if (a, b) != tq]
    n = num_targets
    if n is None:
      n = 3 if random.random() < 0.8 else 2
    if n == 2:
      others = random.sample(others, 2)
    size_of = _sample_sizes(others, lens, sizes, k, s0, m)
    if size_of is None:
      continue
    caps = []
    for axis in (0, 1):
      cap = min(ecap, lt[axis] // f - k)
      for q in others:
        s = size_of[q]
        cap = min(cap, (lens[axis][q[axis]] - s) // (s // k))
      caps.append(cap)
    if min(caps) < 1:
      continue
    ext = []
    for axis in (0, 1):
      tot = max(random.randint(1, caps[axis]), random.randint(1, caps[axis]))
      e_in = random.randint(0, tot)
      e_out = tot - e_in
      if tq[axis] == 0:
        ext.append((e_out, e_in))
      else:
        ext.append((e_in, e_out))
    box = (-ext[0][0], k - 1 + ext[0][1], -ext[1][0], k - 1 + ext[1][1])
    P = None
    for _ in range(30):
      P = _build_template(k, f, box, dmax, nmax)
      if P is not None:
        break
    if P is None:
      continue
    br, bc, _ = _block_info(P)
    ph, pw = len(P), len(P[0])
    ylo, yhi = _template_span(tq[0], nt, height, ph)
    xlo, xhi = _template_span(tq[1], nl, width, pw)
    if ylo > yhi or xlo > xhi:
      continue
    pos = (random.randint(ylo, yhi), random.randint(xlo, xhi))
    targets = []
    for q in others:
      s = size_of[q]
      flip_lr, flip_ud = q[1] != tq[1], q[0] != tq[0]
      Q, r2, c2 = _stamp_geometry(P, br, bc, s0, s, flip_lr, flip_ud)
      if not (_exact(P, Q, r2, c2, s) and _lossless(P, s0, s)):
        break
      tlo, thi, tin = _target_span(q[0], nt, height, s, len(Q), r2)
      llo, lhi, lin = _target_span(q[1], nl, width, s, len(Q[0]), c2)
      if tlo > thi or llo > lhi:
        break
      found = None
      for _ in range(15):
        ty = random.randint(tlo, thi)
        tx = random.randint(llo, lhi)
        if _stamp_ok(P, s, ty, tx, flip_lr, flip_ud, height, width):
          found = (ty, tx, s)
          break
      if found is None and _stamp_ok(P, s, tin, lin, flip_lr, flip_ud,
                                     height, width):
        found = (tin, lin, s)
      if found is None:
        break
      targets.append(found)
    if len(targets) != len(others):
      continue
    return nt, nb, nl, nr, P, pos, targets
  raise ValueError("could not construct a scene for the requested parameters")


def _crop(template, pos):
  """Crops a template to its non-background bounding box and shifts pos."""
  cells = [(r, c) for r, row in enumerate(template) for c, v in enumerate(row)
           if v != BG]
  if not cells:
    raise ValueError("template has no non-background cells")
  r0 = min(r for r, _ in cells)
  r1 = max(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  c1 = max(c for _, c in cells)
  P = [list(row[c0:c1 + 1]) for row in template[r0:r1 + 1]]
  return P, (pos[0] + r0, pos[1] + c0)


def _check_explicit(top, bottom, left, right, template, template_pos, targets):
  """Rejects explicit scenes that are malformed, ambiguous or out of bounds."""
  height, width = top + bottom + 1, left + right + 1
  vals = set(v for row in template for v in row)
  if not vals - {BG, BLOCK}:
    raise ValueError("template needs a colour other than 4 and 2")
  two = [(r, c) for r, row in enumerate(template) for c, v in enumerate(row)
         if v == BLOCK]
  if not two:
    raise ValueError("template needs a colour-2 block")
  br, bc, s0 = _block_info(template)
  bw = max(c for _, c in two) - bc + 1
  if bw != s0 or len(two) != s0 * s0:
    raise ValueError("template colour-2 cells must form one solid square")
  py, px = template_pos
  ph, pw = len(template), len(template[0])
  if py < 0 or px < 0 or py + ph > height or px + pw > width:
    raise ValueError("template outside grid")
  tq = (1 if py > top else 0, 1 if px > left else 0)
  for y in (py, py + ph - 1):
    if not _side_ok(y, top, tq[0]):
      raise ValueError("template must keep a one-cell gap from the dividers")
  for x in (px, px + pw - 1):
    if not _side_ok(x, left, tq[1]):
      raise ValueError("template must keep a one-cell gap from the dividers")
  if not 1 <= len(targets) <= 3:
    raise ValueError("explicit scenes need 1..3 targets")
  seen = set()
  for (ty, tx, s) in targets:
    if s < 1:
      raise ValueError("target size must be a positive integer")
    if ty < 0 or tx < 0 or ty + s > height or tx + s > width:
      raise ValueError("target outside grid")
    q = (1 if ty > top else 0, 1 if tx > left else 0)
    if q == tq:
      raise ValueError("targets must lie outside the template quadrant")
    if q in seen:
      raise ValueError("at most one target per quadrant")
    seen.add(q)
    for (yy, xx) in ((ty, tx), (ty + s - 1, tx + s - 1)):
      if not (_side_ok(yy, top, q[0]) and _side_ok(xx, left, q[1])):
        raise ValueError("target square must keep a gap from the dividers")
    flip_lr, flip_ud = q[1] != tq[1], q[0] != tq[0]
    Q, r2, c2 = _stamp_geometry(template, br, bc, s0, s, flip_lr, flip_ud)
    if not _exact(template, Q, r2, c2, s):
      raise ValueError("target size %d does not scale the template exactly" % s)
    if not _lossless(template, s0, s):
      raise ValueError("target size %d would destroy template detail" % s)
    for (yy, xx) in _painted(Q, ty - r2, tx - c2, height, width):
      if not (_side_ok(yy, top, q[0]) and _side_ok(xx, left, q[1])):
        raise ValueError("target stamp must keep a gap from the dividers")
    if not _stamp_ok(template, s, ty, tx, flip_lr, flip_ud, height, width):
      raise ValueError("target stamp hides a colour, loses most attachments "
                       "or is orientation-ambiguous")


def _normalise_explicit(template, template_pos, targets):
  """Type-checks explicit scene arguments and returns normalised copies."""
  if not isinstance(template, (list, tuple)) or not template:
    raise ValueError("template must be a non-empty list of rows")
  rows = []
  for row in template:
    if not isinstance(row, (list, tuple)) or not row:
      raise ValueError("template rows must be non-empty lists")
    if any((not _is_int(v)) or v < 0 or v > 9 for v in row):
      raise ValueError("template values must be integer colours 0..9")
    rows.append(list(row))
  if any(len(r) != len(rows[0]) for r in rows):
    raise ValueError("template rows must have equal length")
  if (not isinstance(template_pos, (list, tuple)) or len(template_pos) != 2 or
      not all(_is_int(v) for v in template_pos)):
    raise ValueError("template_pos must be (row, col) integers")
  if not isinstance(targets, (list, tuple)):
    raise ValueError("targets must be a list of (row, col, size)")
  tl = []
  for t in targets:
    if (not isinstance(t, (list, tuple)) or len(t) != 3 or
        not all(_is_int(v) for v in t)):
      raise ValueError("each target must be (row, col, size) integers")
    tl.append(tuple(t))
  return rows, tuple(template_pos), tl


def generate(top=None, bottom=None, left=None, right=None, template=None,
             template_pos=None, targets=None, template_quadrant=None,
             mode=None, num_targets=None):
  """Generates one input/output pair.

  Args:
    top: rows above the divider row. Random scenes: 7..22 if given, otherwise
      sampled from 9..15. Explicit scenes: 5..24, default 13.
    bottom: rows below the divider row (same conventions).
    left: columns left of the divider column (same conventions).
    right: columns right of the divider column (same conventions).
    template: explicit template patch (list of rows, background 4). It holds
      one solid 2-square and at least one other colour, and requires
      template_pos and targets. The raw patch must lie inside the grid. It is
      then cropped to its non-background bounding box.
    template_pos: (row, col) of the raw template patch's top-left corner.
    targets: list of 1..3 (row, col, size) lone 2-squares, at most one per
      non-template quadrant. Each must scale the template exactly and
      losslessly, keep every colour visible and be orientation-unambiguous.
    template_quadrant: (row_half, col_half) in {0, 1} for random scenes.
    mode: "aligned" or "fine" template mode for random scenes.
    num_targets: 2 or 3 target quadrants for random scenes.
  """
  if template is None:
    lo, hi = 7, 22
  else:
    lo, hi = 5, 24
  for v in (top, bottom, left, right):
    if v is not None and (not _is_int(v) or v < lo or v > hi):
      raise ValueError("quadrant sides must be integers in %d..%d" % (lo, hi))
  if top is not None and bottom is not None and top + bottom + 1 > MAX_GRID:
    raise ValueError("grid height exceeds 30")
  if left is not None and right is not None and left + right + 1 > MAX_GRID:
    raise ValueError("grid width exceeds 30")
  if template is None:
    if template_pos is not None or targets is not None:
      raise ValueError("template_pos and targets require an explicit template")
    if mode is not None and mode not in ("aligned", "fine"):
      raise ValueError("mode must be 'aligned' or 'fine'")
    if num_targets is not None and (not _is_int(num_targets) or
                                    num_targets not in (2, 3)):
      raise ValueError("num_targets must be 2 or 3")
    tq_req = None
    if template_quadrant is not None:
      if (not isinstance(template_quadrant, (list, tuple)) or
          len(template_quadrant) != 2 or
          any((not _is_int(v)) or v not in (0, 1) for v in template_quadrant)):
        raise ValueError("template_quadrant must be (0|1, 0|1)")
      tq_req = tuple(template_quadrant)
    top, bottom, left, right, template, template_pos, targets = _random_scene(
        top, bottom, left, right, tq_req, mode, num_targets)
  else:
    if template_pos is None or targets is None:
      raise ValueError("explicit template needs template_pos and targets")
    if template_quadrant is not None or mode is not None or (
        num_targets is not None):
      raise ValueError("random-scene controls conflict with explicit template")
    template, template_pos, targets = _normalise_explicit(
        template, template_pos, targets)
    top = 13 if top is None else top
    bottom = 13 if bottom is None else bottom
    left = 13 if left is None else left
    right = 13 if right is None else right
    if top + bottom + 1 > MAX_GRID or left + right + 1 > MAX_GRID:
      raise ValueError("grid exceeds 30 cells")
    rpy, rpx = template_pos
    if (rpy < 0 or rpx < 0 or rpy + len(template) > top + bottom + 1 or
        rpx + len(template[0]) > left + right + 1):
      raise ValueError("raw template patch must lie inside the grid")
    template, template_pos = _crop(template, template_pos)
    _check_explicit(top, bottom, left, right, template, template_pos, targets)
  height = top + bottom + 1
  width = left + right + 1
  grid = common.grid(width, height, BG)
  for c in range(width):
    grid[top][c] = DIV
  for r in range(height):
    grid[r][left] = DIV
  py, px = template_pos
  for i, row in enumerate(template):
    for j, v in enumerate(row):
      if v != BG:
        grid[py + i][px + j] = v
  for (ty, tx, s) in targets:
    for i in range(s):
      for j in range(s):
        grid[ty + i][tx + j] = BLOCK
  output = [row[:] for row in grid]
  br, bc, s0 = _block_info(template)
  tq = (1 if py > top else 0, 1 if px > left else 0)
  for (ty, tx, s) in targets:
    q = (1 if ty > top else 0, 1 if tx > left else 0)
    Q, r2, c2 = _stamp_geometry(template, br, bc, s0, s, q[1] != tq[1],
                                q[0] != tq[0])
    for (yy, xx), v in _painted(Q, ty - r2, tx - c2, height, width).items():
      output[yy][xx] = v
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical fixtures through explicit parameters."""
  t1 = [[8, 8, 4, 4], [8, 8, 4, 4], [2, 2, 3, 3], [2, 2, 3, 3]]
  t2 = [[4, 4, 3, 4, 4], [4, 8, 3, 4, 4], [9, 2, 2, 1, 1], [9, 2, 2, 1, 1]]
  t3 = [[4, 4, 8, 8, 3, 3], [4, 4, 8, 8, 3, 3], [9, 9, 9, 9, 2, 2],
        [9, 9, 9, 9, 2, 2], [4, 4, 4, 4, 1, 1], [4, 4, 4, 4, 1, 1]]
  train = [
      generate(template=t1, template_pos=(4, 5),
               targets=[(5, 20, 2), (18, 19, 3), (20, 3, 1)]),
      generate(template=t2, template_pos=(3, 4),
               targets=[(5, 20, 2), (19, 4, 4), (20, 19, 2)]),
  ]
  test = [
      generate(template=t3, template_pos=(3, 1),
               targets=[(4, 19, 3), (21, 5, 1), (19, 18, 4)]),
  ]
  return {"train": train, "test": test}
