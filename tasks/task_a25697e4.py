"""ARC task a25697e4: seat two-colour chains in the notches of sockets.

Rule:
  The input holds two kinds of objects on a background. The background is the
  most frequent colour.
  * A chain is two 4-connected pieces of different colours that touch edge to
    edge.
  * A socket is a group of same-coloured parts linked at Chebyshev distance
    <= 2. Its hole is the set of background cells inside the group's bounding
    box.
  Each chain is lifted off the canvas and moved as one rigid body: one of the
  8 dihedral transforms plus a translation. The move must make one piece cover
  a hole exactly. The rest of the chain must land in bounds, on background or
  on cells that chains have vacated.
  If the seating transform is a reflection, the chain's two colours swap
  (train pair 1). A proper rotation keeps them.
  A transform can fit a piece to a hole in shape and still be illegal, because
  the other piece would leave the grid or overlap a socket. Test pair 2 has
  such a hard negative. Its staircase 7-piece is transpose-symmetric, so a
  reflection also fills the 2-socket's hole. That reflection would push the
  3-piece off the top border and into the socket, so it is rejected.

Scope:
  Random scenes:
  * Height and width default to 12..30 each. A caller may fix either side to
    10..30. The fixtures are 18x25, 30x30 and 30x25; other sizes are
    synthetic.
  * The background colour is random. Chain and socket colours avoid it. The
    background stays the strict majority, with non-background below 45%.
  * There are 1..3 chain/socket pairs. Two pairs need area >= 200. Three
    pairs need area >= 360 and both sides >= 12. Infeasible requests raise
    ValueError at once.
  * Piece sizes shrink on small grids: 3..4 cells when a side is <= 12, 3..6
    on cramped grids, 3..9 otherwise.
  * The seating transform is any of the 8 dihedral transforms. Pure
    translation, rotations and colour-swapping reflections all occur, and
    either piece can be the filling piece.
  * A socket must equal its bounding box minus the hole, because any other
    background cell inside the box would join the hole. Sockets are therefore
    rectangles padded around the filling footprint, which is cut out. Padding
    is 0..2 cells per side, or 0..1 on cramped grids (a side <= 12 or area
    below 150 cells per pair) so that dense multi-pair layouts keep room for
    the loose chains.
  * If the socket is outermost on some side of the seated footprint, it is
    pushed against that grid border when that side admits a valid placement.
    The probability is 0.7, or 0.9 for hard pairs.
  * Hard negatives: with hard_negative=True, one pair gets a filling piece
    with a mirror, diagonal or half-turn symmetry. Default calls do this with
    probability 0.6 per attempt in the first half of the retry budget. The
    symmetric copy of the seating fills the hole too. The pair is accepted
    only if some shape fit onto its hole is blocked by the border or a socket
    cell, as in test 2. hard_negative=False only stops forcing it; hard
    negatives can still occur.
  * All latent objects are at Chebyshev distance >= 3 from each other in the
    input. Seated footprints do not touch each other.
  Placement planning:
  * Phase 1 seats the sockets one pair at a time, the forced hard pair first.
    For each sampled chain/socket shape every grid offset is enumerated and
    filtered geometrically, then candidate offsets are tried in random order.
  * Fit legality depends only on bounds and socket cells, because chain cells
    are either background or vacated. Adding a socket can only block fits.
    So each new pair is checked once against all earlier pairs: every legal
    fit of the new chain into any hole, and of any earlier chain into the new
    hole, must give that chain's intended outcome. Earlier checks stay valid.
  * Phase 2 drops the loose chains into the free space, at distance >= 3
    from every socket rectangle and every other chain, by enumerating all
    offsets.
  The output is painted from the latent seating transform and offset. The
  fit enumeration is used only as a constraint check. A final whole-grid
  check re-confirms uniqueness.
  Explicit mode rebuilds the canonical fixtures from latent sprites. Seats are
  found by enumerating fits of each latent chain into the latent holes; the
  grid is never parsed into objects. Explicit scenes must be inside the task's
  native scope:
  * every chain has a legal seating with a unique outcome;
  * every socket receives exactly one chain;
  * bg is the strict majority colour.
  Zero-fit or unfilled scenes are out of scope and raise ValueError.
"""

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

import collections
import random

import common

_DIRS = ((0, 1), (1, 0), (0, -1), (-1, 0))
_NBR8 = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
              if dr or dc)
_MIN_RANDOM_SIDE = 10
_SNAP_PROB = 0.7
_HARD_SNAP_PROB = 0.9
_HARD_PROB = 0.6
_PADS = (0, 0, 1, 1, 2)
_HARD_PADS = (0, 1, 1, 2, 2)
_CRAMPED_PADS = (0, 0, 1)
_CRAMPED_HARD_PADS = (0, 1, 1)
_SCENE_TRIES = 60
_CHAIN_TRIES = 30
_OFFSET_CHECKS = 24
_CHAIN_PASSES = 6
_WORK_BUDGET = 1500
_SPRITE_CHARS = set(".0123456789")


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _sprite(top, left, rows):
  """Parse a sprite into an {(row, col): colour} dict ('.' = empty)."""
  cells = {}
  for r, row in enumerate(rows):
    for c, ch in enumerate(row):
      if ch != ".":
        cells[(top + r, left + c)] = int(ch)
  return cells


def _parse_spec(spec, what):
  """Validate a (top, left, rows) sprite spec and parse it."""
  if not isinstance(spec, (list, tuple)) or len(spec) != 3:
    raise ValueError("each %s must be a (top, left, rows) triple" % what)
  top, left, rows = spec
  if not _is_int(top) or not _is_int(left):
    raise ValueError("%s top/left must be plain ints" % what)
  if not isinstance(rows, (list, tuple)) or not rows:
    raise ValueError("%s rows must be a non-empty list of strings" % what)
  for row in rows:
    if not isinstance(row, str) or not set(row) <= _SPRITE_CHARS:
      raise ValueError("%s rows may only contain '.' and digits" % what)
  return _sprite(top, left, rows)


def _bbox(cells):
  rs = [p[0] for p in cells]
  cs = [p[1] for p in cells]
  return min(rs), min(cs), max(rs), max(cs)


def _dihedral(cells, fl, k):
  """Apply rot90^k(fliplr^fl(.)) to a coloured cell dict, like numpy."""
  r0, c0, r1, c1 = _bbox(cells)
  h, w = r1 - r0 + 1, c1 - c0 + 1
  cur = {(r - r0, c - c0): v for (r, c), v in cells.items()}
  if fl:
    cur = {(r, w - 1 - c): v for (r, c), v in cur.items()}
  for _ in range(k):
    cur = {(w - 1 - c, r): v for (r, c), v in cur.items()}
    h, w = w, h
  return cur


def _colour_order(chain):
  order = []
  for key in sorted(chain):
    if chain[key] not in order:
      order.append(chain[key])
  return order


def _swap(v, a, b):
  return b if v == a else a


def _dil(cells, d):
  out = set()
  for r, c in cells:
    for i in range(-d, d + 1):
      for j in range(-d, d + 1):
        out.add((r + i, c + j))
  return out


def _border(cells):
  return {(r + dr, c + dc) for r, c in cells for dr, dc in _DIRS} - cells


def _components(cells):
  cells = set(cells)
  comps = []
  while cells:
    start = cells.pop()
    comp = {start}
    stack = [start]
    while stack:
      r, c = stack.pop()
      for dr, dc in _DIRS:
        n = (r + dr, c + dc)
        if n in cells:
          cells.remove(n)
          comp.add(n)
          stack.append(n)
    comps.append(comp)
  return comps


def _cheb(a, b):
  return min(max(abs(p - r), abs(q - s)) for p, q in a for r, s in b)


def _linked(cells):
  """True if all 4-components are chained by Chebyshev distance <= 2."""
  comps = _components(cells)
  seen = {0}
  frontier = [0]
  while frontier:
    i = frontier.pop()
    for j in range(len(comps)):
      if j in seen:
        continue
      if _cheb(comps[i], comps[j]) <= 2:
        seen.add(j)
        frontier.append(j)
  return len(seen) == len(comps)


def _holes(grid, bg, sockets):
  holes = []
  for s in sockets:
    r0, c0, r1, c1 = _bbox(s)
    holes.append(frozenset((r, c) for r in range(r0, r1 + 1)
                           for c in range(c0, c1 + 1) if grid[r][c] == bg))
  return holes


def _fits(grid, bg, chain, holes, chain_cells):
  """Every shape fit of a chain piece onto a hole, legal or blocked.

  Returns tuples (fl, k, piece_colour, hole_index, legal, placement).
  """
  h, w = len(grid), len(grid[0])
  fits = []
  cols = _colour_order(chain)
  for fl in (0, 1):
    for k in range(4):
      t = _dihedral(chain, fl, k)
      for pc in cols:
        pm = [p for p, v in t.items() if v == pc]
        py = min(p[0] for p in pm)
        px = min(p[1] for p in pm)
        for hi, hole in enumerate(holes):
          if not hole or len(hole) != len(pm):
            continue
          hy = min(p[0] for p in hole)
          hx = min(p[1] for p in hole)
          dy, dx = hy - py, hx - px
          if {(y + dy, x + dx) for y, x in pm} != hole:
            continue
          place = []
          ok = True
          for (y, x), v in t.items():
            yy, xx = y + dy, x + dx
            if not (0 <= yy < h and 0 <= xx < w) or (
                grid[yy][xx] != bg and (yy, xx) not in chain_cells):
              ok = False
              break
            place.append((yy, xx, v))
          fits.append((fl, k, pc, hi, ok, place))
  return fits


def _candidates(grid, bg, chain, holes, chain_cells):
  return [f for f in _fits(grid, bg, chain, holes, chain_cells) if f[4]]


def _outcome(fl, place, a, b):
  return frozenset((y, x, _swap(v, a, b) if fl else v) for y, x, v in place)


def _seat(grid, bg, sockets, chains, need_hard):
  """Explicit path: seat latent chains into latent socket holes."""
  chain_cells = set()
  for ch in chains:
    chain_cells |= set(ch)
  holes = _holes(grid, bg, sockets)
  out = [row[:] for row in grid]
  for r, c in chain_cells:
    out[r][c] = bg
  painted = set()
  used = set()
  blocked = 0
  for ch in chains:
    fits = _fits(grid, bg, ch, holes, chain_cells)
    blocked += sum(1 for f in fits if not f[4])
    cands = [f for f in fits if f[4]]
    if not cands:
      raise ValueError("an explicit chain has no legal seating; zero-fit "
                       "scenes are out of scope")
    a, b = _colour_order(ch)
    outcomes = {_outcome(f[0], f[5], a, b) for f in cands}
    if len(outcomes) > 1:
      raise ValueError("an explicit chain has several distinct seatings")
    fl, _, _, hi, _, place = cands[0]
    cells = {(yy, xx) for yy, xx, _ in place}
    if cells & painted or hi in used:
      raise ValueError("explicit chains would share a socket or overlap")
    painted |= cells
    used.add(hi)
    for yy, xx, v in place:
      out[yy][xx] = _swap(v, a, b) if fl else v
  if len(used) != len(sockets):
    raise ValueError("every explicit socket must receive exactly one chain")
  if need_hard and not blocked:
    raise ValueError("hard_negative=True but no shape fit is blocked")
  return out


def _check_explicit(height, width, bg, sk, ch):
  """Raise ValueError unless explicit sprites form a well-posed scene."""
  if not sk or not ch:
    raise ValueError("explicit mode needs at least one socket and one chain")
  sprites = sk + ch
  owner = {}
  for idx, obj in enumerate(sprites):
    if not obj:
      raise ValueError("empty sprite")
    for (r, c), v in obj.items():
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError("sprite cell (%d, %d) is out of bounds" % (r, c))
      if v == bg:
        raise ValueError("sprite cells must not use the background colour")
      if (r, c) in owner:
        raise ValueError("sprites overlap at (%d, %d)" % (r, c))
      owner[(r, c)] = idx
  for (r, c), idx in owner.items():
    for dr, dc in _NBR8:
      o = owner.get((r + dr, c + dc))
      if o is not None and o != idx:
        raise ValueError("distinct sprites must not touch (8-neighbourhood)")
  for si, obj in enumerate(sk):
    if len(set(obj.values())) != 1:
      raise ValueError("a socket must be single-coloured")
    if not _linked(set(obj)):
      raise ValueError("socket parts must be linked within Chebyshev 2")
    r0, c0, r1, c1 = _bbox(obj)
    for (r, c), idx in owner.items():
      if idx != si and r0 <= r <= r1 and c0 <= c <= c1:
        raise ValueError("another sprite lies inside a socket's bounding box")
  for i in range(len(sk)):
    for j in range(i + 1, len(sk)):
      ci = next(iter(sk[i].values()))
      cj = next(iter(sk[j].values()))
      if ci == cj and _cheb(set(sk[i]), set(sk[j])) <= 2:
        raise ValueError("same-coloured sockets must be at least 3 apart")
  for obj in ch:
    cols = sorted(set(obj.values()))
    if len(cols) != 2:
      raise ValueError("a chain must have exactly two colours")
    pieces = [{p for p, v in obj.items() if v == col} for col in cols]
    for piece in pieces:
      if len(_components(piece)) != 1:
        raise ValueError("each chain piece must be 4-connected")
    if not any((r + dr, c + dc) in pieces[1]
               for r, c in pieces[0] for dr, dc in _DIRS):
      raise ValueError("the two chain pieces must touch edge to edge")


def _check_majority(grid, bg):
  counts = collections.Counter(v for row in grid for v in row)
  if any(n >= counts[bg] for col, n in counts.items() if col != bg):
    raise ValueError("bg must be the strict majority colour of the input")


def _grow(size, start, forbid):
  cells = [start]
  seen = {start}
  last = None
  for _ in range(400):
    if len(cells) >= size:
      break
    if last is not None and random.random() < 0.5:
      base, d = cells[-1], last
    else:
      base, d = random.choice(cells), random.choice(_DIRS)
    n = (base[0] + d[0], base[1] + d[1])
    if n in seen or n in forbid:
      last = None
      continue
    cells.append(n)
    seen.add(n)
    last = d
  return seen


def _random_chain(lim, maxsz):
  for _ in range(50):
    na, nb = random.randint(3, maxsz), random.randint(3, maxsz)
    a = _grow(na, (0, 0), set())
    b = _grow(nb, random.choice(sorted(_border(a))), a)
    if len(a) != na or len(b) != nb:
      continue
    r0, c0, r1, c1 = _bbox(a | b)
    if r1 - r0 > lim or c1 - c0 > lim:
      continue
    return a, b
  return None


def _invol(kind, p, s):
  """Involutive symmetries: mirrors, (anti)transpose and half turn."""
  r, c = p
  if kind == 0:
    return (r, s[1] - c)
  if kind == 1:
    return (s[0] - r, c)
  if kind == 2:
    return (c, r)
  if kind == 3:
    return (-c, -r)
  return (s[0] - r, s[1] - c)


def _symmetric_chain(lim, maxsz):
  """A chain whose first piece is invariant under a non-trivial symmetry."""
  for _ in range(80):
    kind = random.randrange(5)
    s = (random.randint(0, 1), random.randint(0, 1))
    half = _grow(random.randint(2, max(2, (maxsz + 1) // 2)), (0, 0), set())
    u = half | {_invol(kind, p, s) for p in half}
    if not 3 <= len(u) <= maxsz or len(_components(u)) != 1:
      continue
    nb = random.randint(3, maxsz)
    b = _grow(nb, random.choice(sorted(_border(u))), u)
    if len(b) != nb:
      continue
    r0, c0, r1, c1 = _bbox(u | b)
    if r1 - r0 > lim or c1 - c0 > lim:
      continue
    return u, b
  return None


def _make_socket(fcells, pcells, pads):
  r0, c0, r1, c1 = _bbox(fcells)
  for _ in range(40):
    e = [random.choice(pads) for _ in range(4)]
    rr0, cc0, rr1, cc1 = r0 - e[0], c0 - e[1], r1 + e[2], c1 + e[3]
    if rr1 - rr0 > 9 or cc1 - cc0 > 9:
      continue
    rect = {(r, c) for r in range(rr0, rr1 + 1) for c in range(cc0, cc1 + 1)}
    if rect & pcells:
      continue
    sock = rect - fcells
    if len(sock) < 3 or _bbox(sock) != (rr0, cc0, rr1, cc1):
      continue
    if not _linked(sock):
      continue
    return rect, sock
  return None


def _shift(cells, dy, dx):
  return {(r + dy, c + dx) for r, c in cells}


def _legal_fits(chain, hole, obst, hh, ww):
  """Shape fits of a chain piece onto one hole, as (fl, legal, placement).

  Legality depends only on the grid bounds and socket cells (obst), because
  every chain cell is either background or vacated.
  """
  fits = []
  n = len(hole)
  hy = min(p[0] for p in hole)
  hx = min(p[1] for p in hole)
  cols = _colour_order(chain)
  for fl in (0, 1):
    for k in range(4):
      t = _dihedral(chain, fl, k)
      for pc in cols:
        pm = [p for p, v in t.items() if v == pc]
        if len(pm) != n:
          continue
        dy = hy - min(p[0] for p in pm)
        dx = hx - min(p[1] for p in pm)
        if {(y + dy, x + dx) for y, x in pm} != hole:
          continue
        place = [(y + dy, x + dx, v) for (y, x), v in t.items()]
        ok = all(0 <= y < hh and 0 <= x < ww and (y, x) not in obst
                 for y, x, _ in place)
        fits.append((fl, ok, place))
  return fits


def _has_block(chain, hole, obst, hh, ww):
  """True if some shape fit of the chain onto hole is blocked."""
  return any(not ok for _, ok, _ in _legal_fits(chain, hole, obst, hh, ww))


def _pair_clean(chains, cols, holes, wants, obst, hh, ww):
  """Check the newest pair against every pair.

  Each legal fit of the newest chain into any hole, and of any chain into
  the newest hole, must reproduce that chain's intended outcome. Adding
  sockets only blocks fits, so earlier pairs stay clean.
  """
  new = len(chains) - 1
  found = False
  for j in range(len(chains)):
    a, b = cols[j]
    for h in range(len(holes)):
      if j != new and h != new:
        continue
      for fl, ok, place in _legal_fits(chains[j], holes[h], obst, hh, ww):
        if not ok:
          continue
        if h != j or _outcome(fl, place, a, b) != wants[j]:
          return False
        if j == new:
          found = True
  return found


def _unambiguous(grid, bg, sockets, chains, seats, wants):
  """Every legal fit of every chain must give exactly the intended outcome."""
  chain_cells = set()
  for ch in chains:
    chain_cells |= set(ch)
  holes = _holes(grid, bg, sockets)
  for i, ch in enumerate(chains):
    _, _, ca, cb = seats[i]
    cands = _candidates(grid, bg, ch, holes, chain_cells)
    if not cands:
      return False
    for fl, _, _, hi, _, place in cands:
      if hi != i or _outcome(fl, place, ca, cb) != wants[i]:
        return False
  return True


def _has_blocked(grid, bg, sockets, chains):
  chain_cells = set()
  for ch in chains:
    chain_cells |= set(ch)
  holes = _holes(grid, bg, sockets)
  for ch in chains:
    for fit in _fits(grid, bg, ch, holes, chain_cells):
      if not fit[4]:
        return True
  return False


def _feasible(h, w, n):
  if n == 1:
    return min(h, w) >= _MIN_RANDOM_SIDE
  if n == 2:
    return min(h, w) >= _MIN_RANDOM_SIDE and h * w >= 200
  return min(h, w) >= 12 and h * w >= 360


def _dim_options(height, width, n):
  hs = [height] if height is not None else list(range(12, 31))
  ws = [width] if width is not None else list(range(12, 31))
  m = n if n is not None else 1
  return [(h, w) for h in hs for w in ws if _feasible(h, w, m)]


def _piece_limits(hh, ww, n):
  """(max bbox span, max piece size) for chain pieces on this grid."""
  if min(hh, ww) <= 12:
    return 3, 4
  if min(hh, ww) < 16 or hh * ww < 200 * n:
    return 5, 6
  return 8, 9


def _snapped(off, snap, fbox, hh, ww):
  oy, ox = off
  fr0, fc0, fr1, fc1 = fbox
  if snap == "top":
    return oy == -fr0
  if snap == "bottom":
    return oy == hh - 1 - fr1
  if snap == "left":
    return ox == -fc0
  return ox == ww - 1 - fc1


def _plan_seats(hh, ww, n, others, want_hard, work):
  """Phase 1: seat sockets and their seated chains, one pair at a time.

  Returns (chains, colour pairs, rects, socket dicts, wanted outcomes) with
  chains in origin coordinates, or None.
  """
  lim, maxsz = _piece_limits(hh, ww, n)
  cramped = min(hh, ww) <= 12 or hh * ww < 150 * n
  pads = _CRAMPED_PADS if cramped else _PADS
  hpads = _CRAMPED_HARD_PADS if cramped else _HARD_PADS
  cap = (45 * hh * ww - 1) // 100
  used = 0
  chains, cols, holes, wants, rects, sockets = [], [], [], [], [], []
  obst, rect_forbid, rects_all = set(), set(), set()
  out_raw, out_dil = set(), set()
  for i in range(n):
    is_hard = want_hard and i == 0
    seated = False
    for _ in range(_CHAIN_TRIES):
      work[0] += 1
      if work[0] >= _WORK_BUDGET:
        return None
      if is_hard:
        ab = _symmetric_chain(lim, maxsz)
      else:
        ab = _random_chain(lim, maxsz)
      if ab is None:
        continue
      pa, pb = ab
      ca, cb = random.sample(others, 2)
      cs = random.choice([c for c in others if c not in (ca, cb)])
      chain = {p: ca for p in pa}
      chain.update({p: cb for p in pb})
      fl, k = random.randint(0, 1), random.randint(0, 3)
      t = _dihedral(chain, fl, k)
      fcol = ca if is_hard else random.choice((ca, cb))
      fcells = {p for p, v in t.items() if v == fcol}
      pcells = set(t) - fcells
      sk = _make_socket(fcells, pcells, hpads if is_hard else pads)
      if sk is None:
        continue
      rect, sock = sk
      if used + len(sock) + len(chain) > cap:
        continue
      fbox = _bbox(rect | pcells)
      fr0, fc0, fr1, fc1 = fbox
      ir0, ic0, ir1, ic1 = _bbox(chain)
      if (fr1 - fr0 + 1 > hh or fc1 - fc0 + 1 > ww or
          ir1 - ir0 + 1 > hh or ic1 - ic0 + 1 > ww):
        continue
      rlist = sorted(rect)
      plist = sorted(pcells)
      flist = sorted(fcells)
      offsets = []
      for oy in range(-fr0, hh - fr1):
        for ox in range(-fc0, ww - fc1):
          if any((r + oy, c + ox) in rect_forbid or (r + oy, c + ox) in out_raw
                 for r, c in rlist):
            continue
          if any((r + oy, c + ox) in rects_all or (r + oy, c + ox) in out_dil
                 for r, c in plist):
            continue
          if any((r + oy, c + ox) in out_dil for r, c in flist):
            continue
          offsets.append((oy, ox))
      if not offsets:
        continue
      rr0, rc0, rr1, rc1 = _bbox(rect)
      sides = []
      if rr0 == fr0:
        sides.append("top")
      if rr1 == fr1:
        sides.append("bottom")
      if rc0 == fc0:
        sides.append("left")
      if rc1 == fc1:
        sides.append("right")
      prob = _HARD_SNAP_PROB if is_hard else _SNAP_PROB
      if sides and random.random() < prob:
        snap = random.choice(sides)
        snapped = [o for o in offsets if _snapped(o, snap, fbox, hh, ww)]
        if snapped:
          offsets = snapped
      random.shuffle(offsets)
      for oy, ox in offsets[:_OFFSET_CHECKS]:
        ss = _shift(sock, oy, ox)
        fp = frozenset(_shift(fcells, oy, ox))
        new_obst = obst | ss
        if is_hard and not _has_block(chain, fp, new_obst, hh, ww):
          continue
        want = frozenset((r + oy, c + ox, _swap(v, ca, cb) if fl else v)
                         for (r, c), v in t.items())
        if not _pair_clean(chains + [chain], cols + [(ca, cb)],
                           holes + [fp], wants + [want], new_obst, hh, ww):
          continue
        rr = _shift(rect, oy, ox)
        pp = _shift(pcells, oy, ox)
        obst = new_obst
        rect_forbid |= _dil(rr, 2)
        rects_all |= rr
        out_raw |= set(fp) | pp
        out_dil |= _dil(set(fp) | pp, 1)
        used += len(sock) + len(chain)
        chains.append(chain)
        cols.append((ca, cb))
        holes.append(fp)
        wants.append(want)
        rects.append(rr)
        sockets.append({p: cs for p in ss})
        seated = True
        break
      if seated:
        break
    if not seated:
      return None
  return chains, cols, rects, sockets, wants


def _place_chains(hh, ww, chains, rects, work):
  """Phase 2: put loose chains >= 3 away from rects and other chains."""
  base = set()
  for rr in rects:
    base |= _dil(rr, 2)
  order = sorted(range(len(chains)), key=lambda i: -len(chains[i]))
  for _ in range(_CHAIN_PASSES):
    work[0] += 1
    forbid = set(base)
    placed = [None] * len(chains)
    ok = True
    for i in order:
      ch = chains[i]
      cells = sorted(ch)
      r0, c0, r1, c1 = _bbox(cells)
      opts = [(iy, ix) for iy in range(-r0, hh - r1)
              for ix in range(-c0, ww - c1)
              if not any((r + iy, c + ix) in forbid for r, c in cells)]
      if not opts:
        ok = False
        break
      iy, ix = random.choice(opts)
      cc = {(r + iy, c + ix): v for (r, c), v in ch.items()}
      placed[i] = cc
      forbid |= _dil(set(cc), 2)
    if ok:
      return placed
    random.shuffle(order)
  return None


def _random_scene(height, width, bg, num_pairs, hard):
  dims = _dim_options(height, width, num_pairs)
  work = [0]
  for attempt in range(_SCENE_TRIES):
    if work[0] >= _WORK_BUDGET:
      break
    hh, ww = random.choice(dims)
    bgc = bg if bg is not None else random.randint(0, 9)
    others = [c for c in range(10) if c != bgc]
    if num_pairs is not None:
      n = num_pairs
    else:
      n = random.choice([m for m in (1, 1, 2, 2, 2, 3)
                         if _feasible(hh, ww, m)])
    if hard is None:
      want_hard = (attempt < _SCENE_TRIES // 2 and
                   random.random() < _HARD_PROB)
    else:
      want_hard = hard
    plan = _plan_seats(hh, ww, n, others, want_hard, work)
    if plan is None:
      continue
    chains, cols, rects, sockets, wants = plan
    placed = _place_chains(hh, ww, chains, rects, work)
    if placed is None:
      continue
    grid = common.grid(ww, hh, bgc)
    for obj in sockets + placed:
      for (r, c), v in obj.items():
        grid[r][c] = v
    nonbg = sum(1 for row in grid for v in row if v != bgc)
    if nonbg * 100 >= 45 * hh * ww:
      continue
    # Output written directly from the latent seating transforms.
    out = [row[:] for row in grid]
    for cc in placed:
      for r, c in cc:
        out[r][c] = bgc
    for want in wants:
      for r, c, v in want:
        out[r][c] = v
    seats = [(None, None, a, b) for a, b in cols]
    if not _unambiguous(grid, bgc, sockets, placed, seats, wants):
      continue
    if want_hard and not _has_blocked(grid, bgc, sockets, placed):
      continue
    return {"input": grid, "output": out}
  raise RuntimeError("could not construct a valid a25697e4 scene with the "
                     "requested parameters within the retry budget")


def generate(height=None, width=None, bg=None, num_pairs=None,
             hard_negative=None, sockets=None, chains=None):
  """Generate one input/output pair.

  Args:
    height: grid height. Random mode accepts 10..30 and defaults to 12..30.
      Explicit mode requires it and accepts 1..30.
    width: grid width. Random mode accepts 10..30 and defaults to 12..30.
      Explicit mode requires it and accepts 1..30.
    bg: background colour 0..9. Random by default; explicit mode requires it.
    num_pairs: number of chain/socket pairs. Random mode: 1..3, default
      random among the counts feasible for the grid. Two pairs need area
      >= 200; three pairs need area >= 360 and sides >= 12. Requests with no
      feasible size raise ValueError at once. Explicit mode: if given, it must
      equal both len(chains) and len(sockets).
    hard_negative: None, True or False. True forces a hard negative: some
      chain piece also fits a hole in shape under another transform, but that
      placement is blocked by the border or a socket cell. This is the test 2
      situation. None forces it with probability 0.6 per attempt. False does
      not force it, though it may still occur. In explicit mode, True checks
      that such a blocked fit exists.
    sockets: list of (top, left, rows) single-colour socket sprites. top and
      left are plain ints; rows are strings of '.' and digits.
    chains: list of (top, left, rows) two-colour chain sprites.

  All numeric controls must be plain ints; bool and float raise ValueError.
  Give both sockets and chains for explicit mode, or neither for a fresh
  random scene. Explicit scenes must satisfy all of the following, or
  ValueError is raised:
  * sprites are in bounds and do not overlap or touch, even diagonally;
  * sprites do not use bg, and bg is the strict majority colour;
  * sockets are single-coloured and Chebyshev-2 linked, with no other sprite
    inside their bounding box;
  * same-coloured sockets are at least 3 apart;
  * each chain has two 4-connected, edge-adjacent pieces;
  * each chain has exactly one distinct legal seating outcome;
  * every socket is filled by exactly one chain.
  Random construction plans placements by offset enumeration with a bounded
  work budget. A RuntimeError is possible only on very cramped requests, for
  example a forced hard negative on 10x10.
  """
  for name, val in (("height", height), ("width", width), ("bg", bg),
                    ("num_pairs", num_pairs)):
    if val is not None and not _is_int(val):
      raise ValueError("%s must be an int" % name)
  for name, val in (("height", height), ("width", width)):
    if val is not None and not 1 <= val <= 30:
      raise ValueError("%s must be in 1..30" % name)
  if bg is not None and not 0 <= bg <= 9:
    raise ValueError("bg must be in 0..9")
  if hard_negative is not None and not isinstance(hard_negative, bool):
    raise ValueError("hard_negative must be None, True or False")
  if (sockets is None) != (chains is None):
    raise ValueError("sockets and chains must be given together")
  if sockets is None:
    if num_pairs is not None and not 1 <= num_pairs <= 3:
      raise ValueError("num_pairs must be in 1..3")
    for name, val in (("height", height), ("width", width)):
      if val is not None and val < _MIN_RANDOM_SIDE:
        raise ValueError("random mode needs %s >= %d" %
                         (name, _MIN_RANDOM_SIDE))
    if not _dim_options(height, width, num_pairs):
      raise ValueError("infeasible request: two pairs need area >= 200, "
                       "three pairs need area >= 360 and sides >= 12")
    return _random_scene(height, width, bg, num_pairs, hard_negative)
  if height is None or width is None or bg is None:
    raise ValueError("explicit mode needs height, width and bg")
  if not isinstance(sockets, (list, tuple)) or not isinstance(
      chains, (list, tuple)):
    raise ValueError("sockets and chains must be lists of sprite triples")
  sk = [_parse_spec(s, "socket") for s in sockets]
  ch = [_parse_spec(c, "chain") for c in chains]
  if num_pairs is not None and (num_pairs != len(ch) or
                                num_pairs != len(sk)):
    raise ValueError("num_pairs must equal the explicit chain and socket "
                     "counts")
  _check_explicit(height, width, bg, sk, ch)
  grid = common.grid(width, height, bg)
  for obj in sk + ch:
    for (r, c), v in obj.items():
      grid[r][c] = v
  _check_majority(grid, bg)
  out = _seat(grid, bg, sk, ch, hard_negative is True)
  return {"input": grid, "output": out}


def validate():
  """Rebuild the canonical fixtures from explicit latent sprites."""
  chain34 = (1, 18, [".3.", ".3.", "33.", "33.", "4..", "4..", "4..",
                     "4..", "444", "..4"])
  train = [
      generate(height=18, width=25, bg=1,
               sockets=[(6, 0, ["2222", "22..", "....", "2222"])],
               chains=[chain34]),
      generate(height=18, width=25, bg=1,
               sockets=[(6, 0, ["2222", "....", "22..", "2222"])],
               chains=[chain34]),
      generate(height=18, width=25, bg=1,
               sockets=[(15, 11, ["6...6", "6.666", "6.666"])],
               chains=[(11, 3, [".5....", "55....", ".555..", "...777",
                                "...7..", "...7.."])]),
  ]
  test = [
      generate(height=30, width=30, bg=4,
               sockets=[(0, 2, ["222.2", "222.2", "222.2", "222.2",
                                "22..2"]),
                        (6, 25, ["22222", "...22", ".....", "22222",
                                 "22222", "22222", "22222"])],
               chains=[(10, 11, [".......1", ".......1", ".......1",
                                 "33333111", "....3111"]),
                       (24, 12, ["1.33333", "11333..", "1......"])]),
      # Test 2 carries the hard negative: the transpose-symmetric 7-piece
      # also fits by reflection, but that seat is blocked.
      generate(height=30, width=25, bg=8, hard_negative=True,
               sockets=[(0, 16, ["22.222", "22..22", "22...2"]),
                        (11, 21, ["3333", "3333", "....", ".333", "3333"])],
               chains=[(2, 6, ["...466", "44446.", "....66"]),
                       (18, 4, [".....777", "...3377.", "...3.7..",
                                "3333...."])]),
  ]
  return {"train": train, "test": test}
