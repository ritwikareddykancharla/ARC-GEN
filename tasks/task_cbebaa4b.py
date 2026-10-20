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

"""ARC-GEN style generator for task cbebaa4b (connector assembly).

Rule: the input holds several solid-coloured pieces. Each piece carries
single red (2) connector cells that touch its body. One solid yellow (4)
block is the anchor, and it stays where it is. Every other piece is
translated, without rotation or recolouring, so that its red connectors land
exactly on open connectors of pieces that are already placed. Two connectors
that meet merge into one red cell. The finished output is one assembly in
which every connector is paired.

Construction: the assembly is grown first, in output coordinates.
  * The anchor rectangle (3-4 x 3-5) opens 2-4 sockets. Sockets may sit
    side by side with the same outward direction, as on the demo-2 anchor.
  * Each non-anchor piece is either a docker or a leaf. A docker closes
    exactly two open sockets at once and opens 0..3 new ones. A leaf
    closes one socket and opens none, like the green pole in query 2.
    Every fixture piece is one of these two kinds. The profile is chosen
    adaptively per piece, so the open count stays positive until the last
    piece and reaches zero exactly at the end.
  * A leaf is a random 1-thick polyline grown from the cell beyond an open
    socket. Its socket can sit at the tip or on the flank of a bar.
  * A docker is a rectilinear route joining the cells beyond two open
    sockets. Route kinds are L, U and Z routes, outward wraps (step out
    from each socket, then join with an L, as in the 4-segment blue pieces
    of both demos) and two-waypoint detours (as in the test-2 grey frame).
  * Optional spurs add hooks, overhangs and T arms.
  * Piece colours (sampled or user supplied) are shuffled before each
    construction attempt, so a colour is not tied to its chain depth.
  * Each piece's bounding box is capped according to the grid area and the
    piece count, so that dense scenes can still be scattered.

Joint grammar, enforced during construction:
  * Every red cell touches exactly one cell of its owner's body.
  * A matched red sits between its two bodies in a straight line.
  * Bodies never touch an unmatched red.
  * Bodies of the same colour never touch. Bodies of different colours may
    touch, as they do in demo 2.
  * Bodies are 1-thick open shapes with no 2x2 block and no enclosed hole.

Scene guards. All of them are derived from the latent assembly. None of
them calls a solver for the answer.
  * Greedy safety (static). Consider a piece shifted to a wrong position
    where two of its reds fall on cells of the final red set. That decoy
    is allowed only in three cases:
      - it lies out of bounds;
      - it renders identically to an identical piece;
      - it is geometrically blocked by the pieces that must already be
        present for both of those cells to be open. These are the openers
        of the two cells and their ancestor chain, including the anchor.
    Under this condition, any assembler that prefers placements matching
    more open sockets places only correct dockers. This keeps a
    most-matches-first backtracking assembler fast.
  * Leaf uniqueness. Once every docker is placed, each assignment of
    leaves to the remaining sockets is enumerated exactly. All complete
    assignments must render the same. This is a cheap prefilter.
  * Exhaustive positional uniqueness. The complete-assembly search uses
    most-constrained-socket branching, a remaining-connector bound, a
    forward check that every open socket still has a valid cover, and
    pruning of identical pieces. It must finish within MAX_NODES nodes and
    find exactly one rendered assembly, the latent one. If the budget is
    exceeded, the scene is REJECTED. Unknown uniqueness is never accepted.
    The search is translation invariant, so it runs on the latent assembly
    before scattering. Scatter positions cannot change its result.
  * Input scatter. Each piece, with its red cells, is placed at Chebyshev
    distance >= 2 from every other piece. Random probing comes first,
    then an exhaustive scan, with the largest pieces placed first. This
    makes nearest-body connector ownership and piece connectivity
    unambiguous.

Scope:
  * Grid sides are 14..30. Default sampling uses near-square 18..30 grids.
    This goes beyond the fixture sizes 22 and 26 and is a synthetic
    extension.
  * There are 2..7 non-anchor pieces, capped by grid area
    (max(2, min(7, h*w // 70))). Colours may repeat, as in the queries.
  * Not supported: rotation, reflection, recolouring, non-yellow anchors,
    single-connector pieces that open further sockets, and pieces that
    close three or more sockets at once.
"""

import itertools
import math
import random

import common

BG = 0
RED = 2
ANCHOR = 4
PALETTE = (1, 3, 5, 6, 7, 8, 9)
NBRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
MIN_SIDE, MAX_SIDE = 14, 30
MAX_BODY = 26
MAX_NODES = 5000
MAX_ATTEMPTS = 300
PIECE_TRIES = 80
SCATTER_TRIES = 6
# (connectors closed, connectors opened, weight) for non-anchor pieces.
# Two-connector pieces are dockers; (1, 0) is a leaf.
PROFILES = ((2, 2, 4.0), (2, 1, 2.5), (2, 0, 2.5), (2, 3, 0.7), (1, 0, 1.0))


def _shift(c, d, k=1):
  return (c[0] + k * d[0], c[1] + k * d[1])


def _nbrs(c):
  return [(c[0] + dy, c[1] + dx) for dy, dx in NBRS]


def _perp(d):
  return [(d[1], d[0]), (-d[1], -d[0])]


def _dist(a, b):
  return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _weighted(options):
  total = sum(o[-1] for o in options)
  r = random.random() * total
  for o in options:
    r -= o[-1]
    if r <= 0:
      return o
  return options[-1]


def _new_state(height, width):
  return {'h': height, 'w': width, 'owner': {}, 'colour': [], 'reds': {},
          'opened': set(), 'pieces': [], 'opener': {}}


def _inb(st, c):
  return 0 <= c[0] < st['h'] and 0 <= c[1] < st['w']


def _cell_ok(st, x, colour, matched):
  """Checks a new body cell: free, touching reds only as a matched partner."""
  if not _inb(st, x) or x in st['owner'] or x in st['reds']:
    return False
  for n in _nbrs(x):
    if n in st['reds']:
      if n not in matched or _shift(n, st['reds'][n]) != x:
        return False
    elif n in st['owner'] and st['colour'][st['owner'][n]] == colour:
      return False
  return True


def _no_block(body):
  for y, x in body:
    if (y + 1, x) in body and (y, x + 1) in body and (y + 1, x + 1) in body:
      return False
  return True


def _no_hole(body):
  """True when the body encloses no background cell (fixture style)."""
  y0 = min(y for y, _ in body) - 1
  y1 = max(y for y, _ in body) + 1
  x0 = min(x for _, x in body) - 1
  x1 = max(x for _, x in body) + 1
  start = (y0, x0)
  seen = {start}
  stack = [start]
  while stack:
    c = stack.pop()
    for n in _nbrs(c):
      if (y0 <= n[0] <= y1 and x0 <= n[1] <= x1 and n not in body and
          n not in seen):
        seen.add(n)
        stack.append(n)
  return len(seen) == (y1 - y0 + 1) * (x1 - x0 + 1) - len(body)


def _body_ok(st, body, colour, matched):
  if not 2 <= len(body) <= MAX_BODY or not _no_block(body):
    return False
  if not _no_hole(body):
    return False
  return all(_cell_ok(st, x, colour, matched) for x in body)


def _socket_cands(st, body, matched):
  """Lists new connector cells (cell, outward dir, weight) for a body."""
  owner, reds = st['owner'], st['reds']
  partners = {_shift(s, reds[s]) for s in st['opened'] if s not in matched}

  def blocked(c):
    return c in owner or c in body or c in reds or c in partners

  halo = sorted({n for b in body for n in _nbrs(b)} - set(body))
  out = []
  for n in halo:
    if not _inb(st, n) or blocked(n):
      continue
    own = [b for b in _nbrs(n) if b in body]
    if len(own) != 1:
      continue
    b = own[0]
    d = (n[0] - b[0], n[1] - b[1])
    if any(blocked(m) for m in _nbrs(n) if m != b):
      continue
    p = _shift(n, d)
    if not _inb(st, p) or blocked(p):
      continue
    if any(blocked(m) for m in _nbrs(p) if m != n):
      continue
    tip = (_shift(b, d, -1) in body and
           not any(_shift(b, e) in body for e in _perp(d)))
    out.append((n, d, 3.0 if tip else 1.0))
  return out


def _pick_sockets(cands, count, allow_pairs=False):
  """Weighted choice of mutually compatible new connectors (or None).

  With allow_pairs, two connectors with the same outward direction may sit
  side by side (their partner cells are then distinct and side by side).
  """
  if count == 0:
    return []
  order = sorted(cands, key=lambda c: -random.random() ** (1.0 / c[2]))
  chosen = []
  for n, d, _ in order:
    p = _shift(n, d)
    good = True
    for n2, d2 in chosen:
      p2 = _shift(n2, d2)
      if allow_pairs and d == d2 and _dist(n, n2) == 1:
        continue
      if (_dist(n, n2) <= 1 or p == p2 or p == n2 or p2 == n or
          _dist(n, p2) == 1 or _dist(p, n2) == 1):
        good = False
        break
    if good:
      chosen.append((n, d))
      if len(chosen) == count:
        return chosen
  return None


def _random_walk(start, d):
  """A 1-thick polyline through start; start is a tip or a bar flank."""
  first = d if random.random() < 0.5 else random.choice(_perp(d))
  cells = {start}
  if first != d and random.random() < 0.35:
    cur = start
    for _ in range(random.randint(1, 3)):
      cur = _shift(cur, first, -1)
      cells.add(cur)
  cur, e = start, first
  for _ in range(random.randint(1, 3)):
    for _ in range(random.randint(1, 5)):
      cur = _shift(cur, e)
      cells.add(cur)
    e = random.choice(_perp(e))
  return cells


def _segment(a, b):
  if a[0] == b[0]:
    lo, hi = sorted((a[1], b[1]))
    return {(a[0], x) for x in range(lo, hi + 1)}
  lo, hi = sorted((a[0], b[0]))
  return {(y, a[1]) for y in range(lo, hi + 1)}


def _lpath(a, b, hfirst):
  corner = (a[0], b[1]) if hfirst else (b[0], a[1])
  return _segment(a, corner) | _segment(corner, b)


def _route(st, c1, d1, c2, d2):
  """A rectilinear body joining partner cells c1 and c2.

  d1 and d2 are the outward directions of the two sockets being closed.
  """
  kind = random.choice((0, 1, 2, 3, 4, 4, 5))
  if kind == 4:
    # Outward wrap: step away from each socket, then join with an L.
    p = _shift(c1, d1, random.randint(0, 4))
    q = _shift(c2, d2, random.randint(0, 4))
    return (_segment(c1, p) | _lpath(p, q, random.random() < 0.5) |
            _segment(q, c2))
  if kind == 5:
    # Detour through two random waypoints near the pair.
    lo_y = max(0, min(c1[0], c2[0]) - 5)
    hi_y = min(st['h'] - 1, max(c1[0], c2[0]) + 5)
    lo_x = max(0, min(c1[1], c2[1]) - 5)
    hi_x = min(st['w'] - 1, max(c1[1], c2[1]) + 5)
    pts = [c1] + [(random.randint(lo_y, hi_y), random.randint(lo_x, hi_x))
                  for _ in range(2)] + [c2]
    cells = set()
    for a, b in zip(pts, pts[1:]):
      cells |= _lpath(a, b, random.random() < 0.5)
    return cells
  if kind == 0:
    pts = [c1, (c1[0], c2[1]), c2]
  elif kind == 1:
    pts = [c1, (c2[0], c1[1]), c2]
  elif kind == 2:
    lo = max(0, min(c1[0], c2[0]) - 7)
    hi = min(st['h'] - 1, max(c1[0], c2[0]) + 7)
    m = random.randint(lo, hi)
    pts = [c1, (m, c1[1]), (m, c2[1]), c2]
  else:
    lo = max(0, min(c1[1], c2[1]) - 7)
    hi = min(st['w'] - 1, max(c1[1], c2[1]) + 7)
    m = random.randint(lo, hi)
    pts = [c1, (c1[0], m), (c2[0], m), c2]
  cells = set()
  for a, b in zip(pts, pts[1:]):
    cells |= _segment(a, b)
  return cells


def _add_spur(st, body, colour, matched):
  """Adds a short straight arm (hook, overhang or T arm) when possible."""
  cells = sorted(body)
  for _ in range(8):
    prev = random.choice(cells)
    e = random.choice(NBRS)
    spur = []
    for _ in range(random.randint(1, 3)):
      x = _shift(prev, e)
      if x in body or not _cell_ok(st, x, colour, matched):
        break
      if any(n in body or n in spur for n in _nbrs(x) if n != prev):
        break
      spur.append(x)
      prev = x
    if spur:
      return body | set(spur)
  return body


def _options(opened, rest):
  """Feasible (closed, opened, weight) profiles for the next piece.

  rest is the number of pieces still to come after this one. The open
  count must reach zero exactly at the end. It never drops to one while
  two or more pieces remain, because then only a leaf could follow and it
  would close the assembly too early.
  """
  opts = []
  for k, m, wt in PROFILES:
    if k > opened:
      continue
    after = opened - k + m
    if rest == 0:
      ok = after == 0
    elif rest == 1:
      ok = after in (1, 2)
    else:
      ok = 2 <= after <= 2 * rest
    if ok:
      opts.append((k, m, wt))
  return opts


def _try_piece(st, colour, k, m, ext):
  opened = sorted(st['opened'])
  reds = st['reds']
  if k == 1:
    s = random.choice(opened)
    body = _random_walk(_shift(s, reds[s]), reds[s])
    matched = {s}
  else:
    s1 = random.choice(opened)
    others = [s for s in opened if s != s1]
    if random.random() < 0.6:
      s2 = min(others, key=lambda s: _dist(s, s1) + 3 * random.random())
    else:
      s2 = random.choice(others)
    body = _route(st, _shift(s1, reds[s1]), reds[s1],
                  _shift(s2, reds[s2]), reds[s2])
    matched = {s1, s2}
  if random.random() < 0.45:
    body = _add_spur(st, body, colour, matched)
  ys = [y for y, _ in body]
  xs = [x for _, x in body]
  if max(ys) - min(ys) + 1 > ext or max(xs) - min(xs) + 1 > ext:
    return None
  if not _body_ok(st, body, colour, matched):
    return None
  new = _pick_sockets(_socket_cands(st, body, matched), m,
                      random.random() < 0.15)
  if new is None:
    return None
  return body, matched, new


def _commit(st, colour, body, matched, new):
  idx = len(st['pieces'])
  for c in body:
    st['owner'][c] = idx
  st['colour'].append(colour)
  st['opened'] -= set(matched)
  for n, d in new:
    st['reds'][n] = d
    st['opened'].add(n)
    st['opener'][n] = idx
  marks = set(matched) | {n for n, _ in new}
  st['pieces'].append((colour, set(body), marks))


def _build_assembly(height, width, colours, ext):
  """Grows a closed assembly; returns ([(colour, body, marks)], opener).

  opener maps every final red cell to the index of the piece that opened
  it (0 is the anchor).
  """
  count = len(colours)
  st = _new_state(height, width)
  ah, aw = random.randint(3, 4), random.randint(3, 5)
  if height < ah + 8 or width < aw + 8:
    return None
  ay = random.randint(4, height - 4 - ah)
  ax = random.randint(4, width - 4 - aw)
  abody = {(ay + y, ax + x) for y in range(ah) for x in range(aw)}
  a_open = random.choice([a for a in (2, 3, 4, 4, 4) if a <= 2 * count])
  socks = _pick_sockets(_socket_cands(st, abody, set()), a_open,
                        random.random() < 0.35)
  if socks is None:
    return None
  _commit(st, ANCHOR, abody, set(), socks)
  for idx, colour in enumerate(colours):
    opts = _options(len(st['opened']), count - 1 - idx)
    if not opts:
      return None
    res = None
    for _ in range(PIECE_TRIES):
      k, m, wt = _weighted(opts)
      res = _try_piece(st, colour, k, m, ext)
      if res is not None:
        break
    if res is None:
      return None
    _commit(st, colour, res[0], res[1], res[2])
  if st['opened']:
    return None
  return st['pieces'], dict(st['opener'])


def _decoy_blocked(mb, mm, need, pieces, opener, closer):
  """True when a shifted piece cannot be valid while all of need exist."""
  for p in need:
    _, pb, pm = pieces[p]
    if not mb.isdisjoint(pb) or not mb.isdisjoint(pm):
      return True
    if not mm.isdisjoint(pb):
      return True
    for c in pm:
      if c in mm and opener[c] in need and closer[c] in need:
        return True
  return False


def _greedy_safe(height, width, pieces, opener):
  """Static check that no wrong placement can match two open sockets.

  Correct dockers are always placed after the openers of both sockets they
  close. So a socket pair can be open together only when its openers and
  their ancestor chain are present. A shifted piece that puts two reds on
  final red cells must be out of bounds, identical in render to an
  identical piece, or blocked by those required pieces.
  """
  final = set(opener)
  closer = {}
  parents = []
  for i, (_, _, marks) in enumerate(pieces):
    ps = set()
    for c in marks:
      if opener[c] != i:
        closer[c] = i
        ps.add(opener[c])
    parents.append(ps)

  def closure(seed):
    seen = set(seed)
    stack = list(seed)
    while stack:
      p = stack.pop()
      for q in parents[p]:
        if q not in seen:
          seen.add(q)
          stack.append(q)
    return seen

  truth = {(c, frozenset(b), frozenset(m)) for c, b, m in pieces[1:]}
  for i in range(1, len(pieces)):
    colour, body, marks = pieces[i]
    if len(marks) < 2:
      continue
    shifts = set()
    for a, b in itertools.permutations(sorted(marks), 2):
      for f in final:
        dy, dx = f[0] - a[0], f[1] - a[1]
        if (b[0] + dy, b[1] + dx) in final:
          shifts.add((dy, dx))
    shifts.discard((0, 0))
    for dy, dx in sorted(shifts):
      mb = frozenset((y + dy, x + dx) for y, x in body)
      mm = frozenset((y + dy, x + dx) for y, x in marks)
      if any(not (0 <= y < height and 0 <= x < width) for y, x in mb | mm):
        continue
      if (colour, mb, mm) in truth:
        continue
      for f1, f2 in itertools.combinations(sorted(mm & final), 2):
        need = closure({0, opener[f1], opener[f2]})
        if i in need or closer[f1] in need or closer[f2] in need:
          continue
        if _decoy_blocked(mb, mm, need, pieces, opener, closer):
          continue
        return False
  return True


def _leaf_unique(height, width, pieces, opener):
  """Every assignment of leaves to their sockets renders the same."""
  leaves = [i for i in range(1, len(pieces)) if len(pieces[i][2]) == 1]
  if len(leaves) < 2:
    return True
  final = set(opener)
  occ = set()
  for i, (_, body, _) in enumerate(pieces):
    if i not in leaves:
      occ |= body
  sockets = sorted(next(iter(pieces[j][2])) for j in leaves)
  want = frozenset((c, pieces[j][0]) for j in leaves for c in pieces[j][1])
  found = set()

  def rec(k, used, taken, cells):
    if len(found) > 1:
      return
    if k == len(leaves):
      found.add(frozenset(cells))
      return
    colour, body, marks = pieces[leaves[k]]
    my, mx = next(iter(marks))
    for s in sockets:
      if s in used:
        continue
      dy, dx = s[0] - my, s[1] - mx
      nb = {(y + dy, x + dx) for y, x in body}
      if any(not (0 <= y < height and 0 <= x < width) for y, x in nb):
        continue
      if nb & occ or nb & final or nb & taken:
        continue
      rec(k + 1, used | {s}, taken | nb, cells + [(c, colour) for c in nb])

  rec(0, frozenset(), frozenset(), [])
  return found == {want}


def _sample_colours(count):
  """Distinct colours, occasionally with one repeated piece colour."""
  colours = random.sample(PALETTE, count)
  if count >= 3 and random.random() < 0.3:
    i, j = random.sample(range(count), 2)
    colours[j] = colours[i]
  return colours


def _dilate(cells):
  return {(y + dy, x + dx) for y, x in cells
          for dy in (-1, 0, 1) for dx in (-1, 0, 1)}


def _to_spec(colour, body, marks, out_dy, out_dx):
  cells = body | marks
  y0 = min(y for y, _ in cells)
  x0 = min(x for _, x in cells)
  y1 = max(y for y, _ in cells)
  x1 = max(x for _, x in cells)
  pattern = []
  for y in range(y0, y1 + 1):
    row = ''
    for x in range(x0, x1 + 1):
      row += '#' if (y, x) in body else ('2' if (y, x) in marks else '.')
    pattern.append(row)
  return (colour, y0, x0, out_dy, out_dx, pattern)


def _scatter(height, width, assembly):
  """Places unassembled pieces in the input; returns piece specs."""
  _, abody, amarks = assembly[0]
  specs = [_to_spec(ANCHOR, abody, amarks, 0, 0)]
  blocked = _dilate(abody | amarks)
  order = list(range(1, len(assembly)))
  random.shuffle(order)
  order.sort(key=lambda i: -len(assembly[i][1] | assembly[i][2]))
  for idx in order:
    colour, body, marks = assembly[idx]
    cells = body | marks
    y0 = min(y for y, _ in cells)
    x0 = min(x for _, x in cells)
    ph = max(y for y, _ in cells) - y0 + 1
    pw = max(x for _, x in cells) - x0 + 1
    if ph > height or pw > width:
      return None
    rel = [(y - y0, x - x0) for y, x in cells]

    def fits(oy, ox):
      if oy == y0 and ox == x0:
        return False
      return all((oy + ry, ox + rx) not in blocked for ry, rx in rel)

    spot = None
    for _ in range(60):
      oy = random.randint(0, height - ph)
      ox = random.randint(0, width - pw)
      if fits(oy, ox):
        spot = (oy, ox)
        break
    if spot is None:
      spots = [(oy, ox) for oy in range(height - ph + 1)
               for ox in range(width - pw + 1) if fits(oy, ox)]
      if not spots:
        return None
      spot = random.choice(spots)
    dy, dx = spot[0] - y0, spot[1] - x0
    moved_body = {(y + dy, x + dx) for y, x in body}
    moved_marks = {(y + dy, x + dx) for y, x in marks}
    blocked |= _dilate(moved_body | moved_marks)
    specs.append(_to_spec(colour, moved_body, moved_marks, -dy, -dx))
  return specs


def _spec_cells(pattern, row, col):
  body, marks = set(), set()
  for r, line in enumerate(pattern):
    for c, ch in enumerate(line):
      if ch == '#':
        body.add((row + r, col + c))
      elif ch == '2':
        marks.add((row + r, col + c))
  return body, marks


def _render_key(bodies, marks, colours, placements):
  cells = set()
  for i, dy, dx in placements:
    cells |= {((y + dy, x + dx), colours[i]) for y, x in bodies[i]}
    cells |= {((y + dy, x + dx), RED) for y, x in marks[i]}
  return frozenset(cells)


def _complete_renders(height, width, bodies, marks, colours, limit=2,
                      max_nodes=MAX_NODES):
  """Bounded search for distinct rendered complete positional assemblies.

  Piece 0 must be the anchor. Each node branches on the open socket with
  the fewest valid covering placements. Every complete assembly covers
  that socket with exactly one piece, so the branches partition the
  solutions and no memo is needed. Identical pieces (same colour and
  shape) are represented by their lowest unplaced index. A node is pruned
  when fewer remaining reds exist than open sockets, or when some open
  socket has no valid cover. Placement validity mirrors the task rule:
  in bounds, body disjoint from occupied/open/closed cells, reds disjoint
  from occupied/closed cells, and at least one red on an open socket.
  Returns (renders, overflowed).
  """
  n = len(bodies)
  boxes = []
  kinds = []
  first = {}
  for i in range(n):
    cells = bodies[i] | marks[i]
    y0 = min(y for y, _ in cells)
    x0 = min(x for _, x in cells)
    boxes.append((y0, x0, max(y for y, _ in cells),
                  max(x for _, x in cells)))
    key = (colours[i], frozenset((y - y0, x - x0) for y, x in bodies[i]),
           frozenset((y - y0, x - x0) for y, x in marks[i]))
    kinds.append(first.setdefault(key, i))
  nreds = [len(m) for m in marks]
  cache = {}

  def moved(i, dy, dx):
    key = (i, dy, dx)
    if key not in cache:
      y0, x0, y1, x1 = boxes[i]
      if y0 + dy < 0 or x0 + dx < 0 or y1 + dy >= height or x1 + dx >= width:
        cache[key] = None
      else:
        cache[key] = (frozenset((y + dy, x + dx) for y, x in bodies[i]),
                      frozenset((y + dy, x + dx) for y, x in marks[i]))
    return cache[key]

  renders = set()
  info = {'nodes': 0, 'overflow': False}

  def rec(placed, remaining, occ, opened, closed, rem_reds):
    info['nodes'] += 1
    if info['nodes'] > max_nodes:
      info['overflow'] = True
      return
    if not opened:
      if not remaining:
        renders.add(_render_key(bodies, marks, colours, placed))
      return
    if not remaining or rem_reds < len(opened):
      return
    reps = {}
    for i in sorted(remaining):
      reps.setdefault(kinds[i], i)
    best = None
    for s in sorted(opened):
      cands = []
      for i in sorted(reps.values()):
        for my, mx in sorted(marks[i]):
          dy, dx = s[0] - my, s[1] - mx
          got = moved(i, dy, dx)
          if got is None:
            continue
          body, mk = got
          if not (body.isdisjoint(occ) and body.isdisjoint(opened) and
                  body.isdisjoint(closed)):
            continue
          if not (mk.isdisjoint(occ) and mk.isdisjoint(closed)):
            continue
          cands.append((i, dy, dx, body, mk))
      if not cands:
        return
      if best is None or len(cands) < len(best):
        best = cands
        if len(best) == 1:
          break
    for i, dy, dx, body, mk in best:
      matched = mk & opened
      rec(placed + ((i, dy, dx),), remaining - {i}, occ | body,
          (opened - matched) | (mk - matched), closed | matched,
          rem_reds - nreds[i])
      if info['overflow'] or len(renders) >= limit:
        return

  rec(((0, 0, 0),), frozenset(range(1, n)), frozenset(bodies[0]),
      frozenset(marks[0]), frozenset(), sum(nreds[1:]))
  return renders, info['overflow']


def _assembly_unique(height, width, assembly):
  """True only when the exhaustive search proves a unique rendered output.

  The search is translation invariant, so it runs on the pieces at their
  latent final positions (shift (0, 0) is the intended placement). An
  overflowing search is treated as failure: unknown uniqueness is never
  accepted.
  """
  bodies = [set(b) for _, b, _ in assembly]
  marks = [set(m) for _, _, m in assembly]
  colours = [c for c, _, _ in assembly]
  renders, overflow = _complete_renders(height, width, bodies, marks, colours)
  if overflow:
    return False
  want = _render_key(bodies, marks, colours,
                     [(i, 0, 0) for i in range(len(assembly))])
  return renders == {want}


def _render(height, width, pieces):
  grid_in = common.grid(width, height, BG)
  grid_out = common.grid(width, height, BG)
  out_marks = []
  for colour, row, col, dy, dx, pattern in pieces:
    body, marks = _spec_cells(pattern, row, col)
    for y, x in body | marks:
      if not (0 <= y < height and 0 <= x < width and
              0 <= y + dy < height and 0 <= x + dx < width):
        raise ValueError('piece cell outside the grid')
    for y, x in body:
      grid_in[y][x] = colour
      grid_out[y + dy][x + dx] = colour
    for y, x in marks:
      grid_in[y][x] = RED
      out_marks.append((y + dy, x + dx))
  for y, x in out_marks:
    grid_out[y][x] = RED
  return {'input': grid_in, 'output': grid_out}


def _max_count(h, w):
  return max(2, min(7, h * w // 70))


def _size_pairs(height, width):
  """Candidate (height, width) pairs consistent with the given sides."""
  if height is not None and width is not None:
    return [(height, width)]
  if height is None and width is None:
    return [(h, w) for h in range(18, MAX_SIDE + 1)
            for w in range(max(18, h - 3), min(MAX_SIDE, h + 3) + 1)]
  if height is None:
    return [(h, width) for h in range(max(MIN_SIDE, width - 3),
                                      min(MAX_SIDE, width + 3) + 1)]
  return [(height, w) for w in range(max(MIN_SIDE, height - 3),
                                     min(MAX_SIDE, height + 3) + 1)]


def _default_count(h, w):
  side = min(h, w)
  if side < 18:
    count = random.randint(2, 3)
  elif side < 22:
    count = random.randint(2, 5)
  else:
    count = 7 if random.random() < 0.15 else random.randint(3, 6)
  return min(count, _max_count(h, w))


def _check_int(name, val, lo, hi):
  if val is None:
    return
  if type(val) is not int or not lo <= val <= hi:
    raise ValueError('%s must be an integer in %d..%d' % (name, lo, hi))


def generate(height=None, width=None, pieces=None, num_pieces=None,
             colors=None):
  """Returns an input/output pair for the connector-assembly task.

  Args:
    height: grid height (rows), integer 14..30. If None, it is random in
      18..30, or within 3 of width when only width is given.
    width: grid width (columns), integer 14..30. If None, it is random and
      within 3 of the height.
    pieces: optional explicit scene for fixture replay. It is a list of
      tuples (colour, row, col, out_dy, out_dx, pattern). Each pattern is a
      list of strings stamped at input (row, col): '#' is body, '2' is a red
      connector and '.' is untouched. (out_dy, out_dx) is the translation of
      that piece in the output; the yellow anchor uses (0, 0). This option
      requires integer height and width (1..30) and cannot be combined with
      num_pieces or colors. The scene is rendered as given and is not
      re-validated.
    num_pieces: number of non-anchor pieces, integer 2..7, and at most
      max(2, min(7, h*w // 70)) for the grid. If None, it is random and
      scaled to the grid size, or len(colors) when colors is given. When a
      side is free, only sizes that can hold the requested count are drawn.
      The count is never reduced silently; if no provably unique scene is
      found within the bounded attempts, RuntimeError is raised.
    colors: optional sequence of non-anchor piece colours (integers drawn
      from 1, 3, 5, 6, 7, 8, 9). Repeats are allowed. Its length must equal
      num_pieces when both are given. The multiset is honoured exactly; the
      order is shuffled per attempt, so it does not fix assembly positions.
  """
  if pieces is not None:
    if height is None or width is None:
      raise ValueError('explicit pieces require height and width')
    if num_pieces is not None or colors is not None:
      raise ValueError('num_pieces/colors cannot be combined with pieces')
    _check_int('height', height, 1, MAX_SIDE)
    _check_int('width', width, 1, MAX_SIDE)
    return _render(height, width, pieces)
  _check_int('height', height, MIN_SIDE, MAX_SIDE)
  _check_int('width', width, MIN_SIDE, MAX_SIDE)
  if colors is not None:
    try:
      colors = list(colors)
    except TypeError:
      raise ValueError('colors must be a sequence of integers')
    if any(type(c) is not int or c not in PALETTE for c in colors):
      raise ValueError('colors must be integers from %s' % (PALETTE,))
    if num_pieces is None:
      num_pieces = len(colors)
    elif len(colors) != num_pieces:
      raise ValueError('len(colors) must equal num_pieces')
  _check_int('num_pieces', num_pieces, 2, 7)
  pairs = _size_pairs(height, width)
  if num_pieces is not None:
    pairs = [p for p in pairs if _max_count(p[0], p[1]) >= num_pieces]
    if not pairs:
      raise ValueError('num_pieces is too large for the requested grid size')
  for _ in range(MAX_ATTEMPTS):
    h, w = random.choice(pairs)
    count = num_pieces if num_pieces is not None else _default_count(h, w)
    if colors is not None:
      colours = list(colors)
      random.shuffle(colours)
    else:
      colours = _sample_colours(count)
    ext = max(6, min(10, int(math.sqrt(h * w / (count + 1.0)))))
    built = _build_assembly(h, w, colours, ext)
    if built is None:
      continue
    assembly, opener = built
    # Input density is scatter independent (pieces are kept apart).
    filled = sum(len(b | m) for _, b, m in assembly)
    if filled * 20 > 9 * h * w:
      continue
    if not _greedy_safe(h, w, assembly, opener):
      continue
    if not _leaf_unique(h, w, assembly, opener):
      continue
    if not _assembly_unique(h, w, assembly):
      continue
    specs = None
    for _ in range(SCATTER_TRIES):
      specs = _scatter(h, w, assembly)
      if specs is not None:
        break
    if specs is None:
      continue
    return _render(h, w, specs)
  raise RuntimeError('could not construct a provably unambiguous assembly')


def validate():
  """Reconstructs the canonical train and test pairs from latent scenes."""
  train = [
      generate(22, 22, pieces=[
          (8, 0, 15, 6, -7, ['2...2', '#####', '.#.#.', '.#.#.', '.2.2.']),
          (1, 3, 2, 9, 8, ['..2###.', '.....#2', '2....#.', '#....#.',
                           '#....#2', '######.']),
          (4, 10, 9, 0, 0, ['2.2.', '###.', '###2', '###.', '.2..']),
          (5, 15, 15, -2, 1, ['2####', '....#', '....#', '2####']),
          (3, 18, 1, -14, 7, ['#####', '#...#', '2...2']),
      ]),
      generate(22, 22, pieces=[
          (6, 3, 16, 1, -9, ['###', '#.#', '#.#', '2.2']),
          (4, 10, 9, 0, 0, ['..22.', '.###.', '2###2', '.###.']),
          (3, 10, 16, -3, -4, ['2..2', '####', '#..#', '2..#', '...#',
                               '.2##']),
          (1, 12, 2, -5, 5, ['2.2..', '#####', '#...#', '#...2', '#....',
                             '##2..']),
          (8, 18, 9, -13, 3, ['####', '#..#', '2..2']),
      ]),
  ]
  test = [
      generate(26, 26, pieces=[
          (8, 1, 10, 8, 7, ['2.2', '#.#', '###']),
          (8, 0, 16, 7, -7, ['......2.', '#######2', '#.....#.', '2.....#.',
                             '.....2#.']),
          (9, 6, 3, -1, 12, ['#####', '#...#', '2...#', '.2###', '..2.2']),
          (4, 10, 8, 0, 0, ['.2.....', '.#####2', '.#####.', '.#####.',
                            '2#####.', '..2....']),
          (1, 9, 18, 9, -13, ['.2..2.', '.#..#.', '.#..#.', '.#..#.',
                              '######', '2....2']),
          (3, 20, 1, -6, 4, ['###2..', '#....2', '#....#', '######',
                             '.2..2.']),
          (7, 20, 12, 3, -7, ['2....2', '######']),
      ]),
      generate(26, 26, pieces=[
          (8, 0, 3, 4, 6, ['2....', '####2', '#..#.', '#..#2', '#..#.',
                           '#..2.', '2....']),
          (6, 3, 18, 14, -7, ['2...2', '#...#', '#...#', '#####']),
          (4, 9, 9, 0, 0, ['...2.', '2###.', '.###.', '.###2', '..2..']),
          (3, 11, 4, -10, 5, ['#', '#', '#', '2']),
          (5, 11, 18, -11, -4, ['######', '#....#', '#....#', '##..##',
                                '.2..2.']),
          (1, 19, 2, -7, 9, ['..2##', '2...#', '#...#', '#...#', '#####',
                             '2...2']),
          (3, 20, 10, -16, 3, ['..2..2.#', '2#######', '.......#',
                               '2#######', '.......#']),
      ]),
  ]
  return {'train': train, 'test': test}
