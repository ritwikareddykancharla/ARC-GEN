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

"""ARC-GEN style generator for task 8b7bacbf (ring threading).

Rule: closed rings sit on a background. Each ring is an outline that
4-encloses a pocket of background; the grid edge may close one side of it.
A marker cell has a colour that occurs exactly once. A one-cell-wide,
8-connected line of a path colour leaves the marker. The line can be
interrupted in two ways:
  * By a ring. The line reaches one corner or side of the ring and resumes
    from another, with only ring wall in between.
  * By another marker's line. The line resumes on the far side of the
    crossing cell.
Every ring that the marker's connected line touches (8-adjacency) gets its
pocket filled with the marker colour. Nothing else changes. Lines that do
not connect to a marker leave their rings empty, even when they share a
marker's path colour. Colours that occur two or three times are not
markers.

Scope of the random generator:
  * Grid sides are 10..30 by default. 8..30 is accepted when requested
    explicitly. Crossings need sides of at least 12, both when requested
    and when chosen at random, and use a sparser ring budget
    (w*h/60 instead of w*h/40). Sizes above the fixtures' 30x22 range are
    a synthetic extension. The background is 0 most of the time,
    otherwise a random colour.
  * Pockets come in three kinds: small rectangles framed by rounded-corner
    rings as in the originals, long thin rectangles (1x5..1x8, 2x5..2x8), and
    random bent polyomino pockets of 3..10 cells. About a fifth of rings are
    deliberately clipped by one grid edge, so the edge closes the pocket (as
    in train 3).
  * Rings use one to four colours and never touch one another.
  * There are one to three markers. Each has its own path colour and one or
    more target rings. A path is threaded through ring corners or contacts
    and may have a tail after its last ring. Line stretches are shortest
    8-connected paths, optionally detouring through a random waypoint, so
    lines are not always straight-line approaches.
  * Optionally a marker sits in a small blob of its path colour (train 3).
  * Optionally one marker's line crosses an earlier marker's line once. The
    crossed stretch can be orthogonal or diagonal, and the crossing
    direction is any non-parallel direction (test 1 has a diagonal case). The
    crossing cell takes the crossing line's colour.
  * Distractors:
      - Untouched rings.
      - An optional marker-less line threading its own rings, which stay
        empty. Its colour is either fresh, or equal to a marker's path
        colour, which reproduces the disconnected same-colour segments of
        train 1 and test 1.
      - An optional decoy colour placed 2..3 times, often at line ends (like
        the 0 cells in test 1).
  * Not supported:
      - Rings sharing walls.
      - Path cells replacing ring wall cells.
      - Wide or irregular path bodies (like the 9 structure of test 2).
      - Slanted parallelogram pockets.
      - Crossings that involve the marker-less line.
      - More than one crossing.

Fixture replay: generate(input_grid=..., fills=[(row, col, colour), ...])
reproduces the original examples. Re-extracting every hand-drawn path and
ring from the originals is impractical, so the replay takes the input grid
together with explicit latent fill seeds. Each seed must name a background
cell inside a single-colour pocket, which is then flood-filled with the
given marker colour. A replay-only reachability graph verifies every fill
against visible marker paths and checks that none were omitted. It never
supplies targets for the normal random generator. Replay cannot be combined
with the random-generation controls.
"""

import random
from collections import Counter, deque

import common

_D4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_D8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
_MIN_SIDE = 8
_MAX_SIDE = 30
_DEFAULT_MIN_SIDE = 10
_CROSSING_MIN_SIDE = 12
_CLIP_PROB = 0.2
_WAYPOINT_PROB = 0.35
_MAX_DISTRACTOR_RINGS = 40


def _inside(cell, height, width):
  return 0 <= cell[0] < height and 0 <= cell[1] < width


def _nbrs8(cell, height, width):
  for dr, dc in _D8:
    q = (cell[0] + dr, cell[1] + dc)
    if _inside(q, height, width):
      yield q


def _dilate(cells, k, height, width):
  """All in-grid cells within Chebyshev distance k of the given cells."""
  out = set()
  for r, c in cells:
    for dr in range(-k, k + 1):
      for dc in range(-k, k + 1):
        q = (r + dr, c + dc)
        if _inside(q, height, width):
          out.add(q)
  return out


def _budget(width, height, cross):
  """Maximum number of rings attempted for a grid of this size."""
  return max(2, width * height // (60 if cross else 40))


def _is_int(value):
  return isinstance(value, int) and not isinstance(value, bool)


def _extra_enclosure(pocket, wall):
  """True if the wall also encloses outside cells (a second hole)."""
  foot = pocket | wall
  r0 = min(r for r, _ in foot) - 1
  r1 = max(r for r, _ in foot) + 1
  c0 = min(c for _, c in foot) - 1
  c1 = max(c for _, c in foot) + 1
  start = (r0, c0)
  seen = {start}
  stack = [start]
  while stack:
    p = stack.pop()
    for dr, dc in _D4:
      q = (p[0] + dr, p[1] + dc)
      if (r0 <= q[0] <= r1 and c0 <= q[1] <= c1 and q not in foot and
          q not in seen):
        seen.add(q)
        stack.append(q)
  for r in range(r0, r1 + 1):
    for c in range(c0, c1 + 1):
      if (r, c) not in foot and (r, c) not in seen:
        return True
  return False


def _ring_shape():
  """Returns (pocket, wall, rect) in local coordinates."""
  roll = random.random()
  pocket = None
  rect = None
  if roll >= 0.7:
    for _ in range(20):
      size = random.randint(3, 10)
      cand = {(0, 0)}
      while len(cand) < size:
        r, c = random.choice(sorted(cand))
        dr, dc = random.choice(_D4)
        cand.add((r + dr, c + dc))
      wall = set()
      for r, c in cand:
        for dr, dc in _D4:
          q = (r + dr, c + dc)
          if q not in cand:
            wall.add(q)
      if not _extra_enclosure(cand, wall):
        pocket = cand
        break
  if pocket is None:
    if roll < 0.55 or roll >= 0.7:
      a = random.choice([1, 2, 2, 2, 3])
      b = random.choice([2, 2, 2, 3, 4, 5])
    else:
      a = random.choice([1, 2])
      b = random.randint(5, 8)
    if random.random() < 0.5:
      a, b = b, a
    pocket = {(r, c) for r in range(a) for c in range(b)}
    rect = (a, b)
  wall = set()
  for r, c in pocket:
    for dr, dc in _D4:
      q = (r + dr, c + dc)
      if q not in pocket:
        wall.add(q)
  foot = pocket | wall
  r0 = min(r for r, _ in foot)
  c0 = min(c for _, c in foot)
  pocket = {(r - r0, c - c0) for r, c in pocket}
  wall = {(r - r0, c - c0) for r, c in wall}
  return pocket, wall, rect


def _traps(cells, height, width):
  """True if an outside cell is 4-enclosed by the ring (plus grid edge)."""
  for p in _dilate(cells, 1, height, width) - cells:
    closed = True
    for dr, dc in _D4:
      q = (p[0] + dr, p[1] + dc)
      if _inside(q, height, width) and q not in cells:
        closed = False
        break
    if closed:
      return True
  return False


def _place(shapes, height, width, clip_prob):
  """Places rings with at least a two-cell gap between footprints.

  With probability clip_prob a ring is shifted so that its outermost wall
  row or column on one chosen side falls outside the grid; the grid edge
  then closes the pocket. Pockets always stay inside the grid.
  """
  near = set()
  rings = []
  for pocket, wall, rect in shapes:
    foot = pocket | wall
    fh = max(r for r, _ in foot) + 1
    fw = max(c for _, c in foot) + 1
    clip = random.random() < clip_prob
    placed = None
    for _ in range(80):
      r0 = random.randint(0, height - fh) if height >= fh else None
      c0 = random.randint(0, width - fw) if width >= fw else None
      if clip:
        side = random.randrange(4)
        if side == 0:
          r0 = -1
        elif side == 1:
          r0 = height - fh + 1
        elif side == 2:
          c0 = -1
        else:
          c0 = width - fw + 1
      if r0 is None or c0 is None:
        continue
      pk = {(r + r0, c + c0) for r, c in pocket}
      if any(not _inside(p, height, width) for p in pk):
        continue
      cells = set()
      for r, c in foot:
        q = (r + r0, c + c0)
        if _inside(q, height, width):
          cells.add(q)
      if cells & near or _traps(cells, height, width):
        continue
      placed = (r0, c0, pk, cells)
      break
    if placed is None:
      return None
    r0, c0, pk, cells = placed
    near |= _dilate(cells, 2, height, width)
    corners = None
    if rect is not None:
      a, b = rect
      corners = [q for q in ((r0, c0), (r0, c0 + b + 1), (r0 + a + 1, c0),
                             (r0 + a + 1, c0 + b + 1))
                 if _inside(q, height, width)]
    near1 = _dilate(cells, 1, height, width)
    rings.append({
        'pocket': pk,
        'wall': cells - pk,
        'foot': cells,
        'near1': near1,
        'contacts': near1 - cells,
        'corners': corners,
        'centre': (sum(r for r, _ in cells) / len(cells),
                   sum(c for _, c in cells) / len(cells)),
    })
  return rings


def _bfs_path(start, goals, forbid, height, width):
  """Shortest 8-connected path from start to a goal, avoiding forbid."""
  prev = {start: None}
  queue = deque([start])
  while queue:
    p = queue.popleft()
    dirs = list(_D8)
    random.shuffle(dirs)
    for dr, dc in dirs:
      q = (p[0] + dr, p[1] + dc)
      if not _inside(q, height, width) or q in prev or q in forbid:
        continue
      prev[q] = p
      if q in goals:
        path = [q]
        while prev[path[-1]] is not None:
          path.append(prev[path[-1]])
        return path[::-1]
      queue.append(q)
  return None


def _leg(start, goals, forbid, height, width):
  """A one-wide path from start to a goal, sometimes via a waypoint.

  The second half of a detour may not touch the first half (except at the
  waypoint), so the line stays one cell wide.
  """
  if random.random() < _WAYPOINT_PROB:
    for _ in range(6):
      w = (random.randrange(height), random.randrange(width))
      if w in forbid or w in goals or w == start:
        continue
      if max(abs(w[0] - start[0]), abs(w[1] - start[1])) < 3:
        continue
      first = _bfs_path(start, {w}, forbid, height, width)
      if first is None:
        continue
      for i in range(1, len(first)):
        if first[i] in goals:
          return first[:i + 1]
      second = _bfs_path(
          w, goals, forbid | _dilate(set(first[:-1]), 1, height, width),
          height, width)
      if second is None:
        continue
      return first + second[1:]
  return _bfs_path(start, goals, forbid, height, width)


def _tail(start, forbid, height, width):
  """A short free line (2..7 steps) leaving start; excludes start itself."""
  prev = {start: None}
  dist = {start: 0}
  queue = deque([start])
  while queue:
    p = queue.popleft()
    if dist[p] >= 7:
      continue
    dirs = list(_D8)
    random.shuffle(dirs)
    for dr, dc in dirs:
      q = (p[0] + dr, p[1] + dc)
      if not _inside(q, height, width) or q in prev or q in forbid:
        continue
      prev[q] = p
      dist[q] = dist[p] + 1
      queue.append(q)
  ends = sorted(q for q, d in dist.items() if d >= 2)
  if not ends:
    return []
  path = [random.choice(ends)]
  while prev[path[-1]] is not None:
    path.append(prev[path[-1]])
  path.reverse()
  return path[1:]


def _choose_exit(ring, entry, forbid):
  """Picks where the line resumes after threading through a ring."""
  if ring['corners']:
    free = [q for q in ring['corners'] if q != entry and q not in forbid]
    if free:
      if entry in ring['corners']:
        side = [q for q in free if q[0] == entry[0] or q[1] == entry[1]]
        other = [q for q in free if q not in side]
        if side and (random.random() < 0.75 or not other):
          pool = side
        else:
          pool = other
      else:
        pool = free
      return random.choice(pool)
  free = sorted(q for q in ring['contacts'] if q not in forbid)
  if not free:
    return None
  free.sort(key=lambda q: -max(abs(q[0] - entry[0]), abs(q[1] - entry[1])))
  return random.choice(free[:3])


def _route(start, targets, blocked, tail, height, width, done=None):
  """Routes a line from start through the target rings, in order.

  Args:
    start: first cell of the routed stretch.
    targets: rings to visit, in order.
    blocked: cells the line may not occupy.
    tail: whether to add a free tail after the last ring.
    height: grid height.
    width: grid width.
    done: cells already used by this line that the stretch must not touch.

  Returns:
    The ordered list of cells, including start, or None.
  """
  cells = [start]
  done = set(done) if done else set()
  cur = start
  for i, ring in enumerate(targets):
    last = i == len(targets) - 1
    forbid = blocked | _dilate(done, 1, height, width)
    contacts = ring['contacts'] - forbid
    goals = set()
    if ring['corners']:
      goals = {q for q in ring['corners'] if q in contacts}
    if not goals:
      goals = contacts
    if not goals:
      return None
    seg = _leg(cur, goals, forbid, height, width)
    if seg is None:
      return None
    cells.extend(seg[1:])
    seg_set = set(seg)
    if last and not tail:
      break
    exit_forbid = blocked | _dilate(done | seg_set, 1, height, width)
    nxt = _choose_exit(ring, seg[-1], exit_forbid)
    done |= seg_set
    if nxt is None:
      if last:
        break
      return None
    cells.append(nxt)
    cur = nxt
    if last:
      forbid = blocked | _dilate(done, 1, height, width)
      cells.extend(_tail(cur, forbid, height, width))
  return cells


def _order(indices, rings, start):
  """Greedy nearest-centre visiting order for a line's rings."""
  remaining = list(indices)
  order = []
  cur = start
  while remaining:
    best = min(remaining, key=lambda j: (
        abs(rings[j]['centre'][0] - cur[0]) +
        abs(rings[j]['centre'][1] - cur[1]), j))
    order.append(best)
    remaining.remove(best)
    cur = rings[best]['centre']
  return order


def _pick_cell(height, width, avoid):
  cells = [(r, c) for r in range(height) for c in range(width)
           if (r, c) not in avoid]
  if not cells:
    return None
  border = [p for p in cells
            if p[0] in (0, height - 1) or p[1] in (0, width - 1)]
  if border and random.random() < 0.5:
    return random.choice(border)
  return random.choice(cells)


def _site_ok(site, allowed, body, marker, ring_near, others_near, height,
             width):
  """Checks a 5-cell crossing strip against the crossed line."""
  for k, y in enumerate(site):
    if (not _inside(y, height, width) or y in ring_near or
        y in others_near):
      return False
    if y in body and k != 2:
      return False
    if marker is not None and max(abs(y[0] - marker[0]),
                                  abs(y[1] - marker[1])) <= 2:
      return False
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        q = (y[0] + dr, y[1] + dc)
        if q in body and q not in allowed:
          return False
  return True


def _crossing_site(line, ring_near, others_near, height, width):
  """Finds a straight 3-cell stretch of a marker line that a line can cut.

  The stretch may be orthogonal or diagonal. The cutting strip runs in any
  direction that is not parallel to it. Returns five cells
  [pre, mid1, x, mid2, post] along the strip, where x is the line cell that
  the crossing line overwrites, or None.
  """
  route = line['route']
  body = line['cells']
  idx = list(range(2, len(route) - 1))
  random.shuffle(idx)
  for i in idx:
    x = route[i]
    a = route[i - 1]
    b = route[i + 1]
    if x not in body or a not in body or b not in body:
      continue
    d = (b[0] - x[0], b[1] - x[1])
    if max(abs(d[0]), abs(d[1])) != 1 or (x[0] - d[0], x[1] - d[1]) != a:
      continue
    # Non-perpendicular crossings can sit 8-adjacent to the nearby bend.
    # Permit that local contact without admitting contacts with remote parts
    # of the path; only the central cell may actually overwrite the path.
    local = set(route[max(0, i - 2):i + 3]) & body
    dirs = [e for e in _D8 if e != d and e != (-d[0], -d[1])]
    random.shuffle(dirs)
    for e in dirs:
      site = [(x[0] + k * e[0], x[1] + k * e[1]) for k in (-2, -1, 0, 1, 2)]
      if _site_ok(site, local, body, line['marker'], ring_near,
                  others_near, height, width):
        return site
  return None


def _single_colour_holes(grid, bg):
  """Background 4-components whose in-grid orthogonal border is one colour."""
  height, width = len(grid), len(grid[0])
  seen = set()
  result = []
  for r in range(height):
    for c in range(width):
      if grid[r][c] != bg or (r, c) in seen:
        continue
      comp = [(r, c)]
      seen.add((r, c))
      colours = set()
      i = 0
      while i < len(comp):
        p = comp[i]
        i += 1
        for dr, dc in _D4:
          q = (p[0] + dr, p[1] + dc)
          if not _inside(q, height, width):
            continue
          v = grid[q[0]][q[1]]
          if v == bg:
            if q not in seen:
              seen.add(q)
              comp.append(q)
          else:
            colours.add(v)
      if len(colours) == 1:
        result.append((frozenset(comp), next(iter(colours))))
  return result


def _attempt(width, height, background, ks_fixed, num_markers,
             num_distractor_rings, distractor_line, distractor_same_colour,
             crossing, marker_blob, decoy, needed):
  """One construction attempt; returns None when a constraint fails."""
  want_cross = bool(crossing)
  lo = _CROSSING_MIN_SIDE if want_cross else _DEFAULT_MIN_SIDE
  h = w = None
  for _ in range(30):
    h = height if height is not None else random.randint(lo, _MAX_SIDE)
    w = width if width is not None else random.randint(lo, _MAX_SIDE)
    if _budget(w, h, want_cross) >= needed:
      break
  else:
    h = height if height is not None else _MAX_SIDE
    w = width if width is not None else _MAX_SIDE
  height, width = h, w
  if ks_fixed is not None:
    ks = list(ks_fixed)
  else:
    if num_markers is not None:
      nm = num_markers
    elif crossing:
      nm = 3 if random.random() < 0.2 else 2
    else:
      roll = random.random()
      nm = 1 if roll < 0.5 else (2 if roll < 0.88 else 3)
    ks = [random.randint(1, 4 if nm == 1 else 3) for _ in range(nm)]
  nm = len(ks)
  floor = 1 if (distractor_line or distractor_same_colour) else 0
  if num_distractor_rings is not None:
    nd = num_distractor_rings
  else:
    nd = random.randint(1, 3)
  # Decide the crossing before the size budget, so random crossings also
  # respect the 12-cell side floor and the sparser crossing budget.
  if crossing is None:
    cross = (nm >= 2 and min(height, width) >= _CROSSING_MIN_SIDE and
             random.random() < 0.5)
  else:
    cross = bool(crossing) and nm >= 2
  budget = _budget(width, height, cross)
  while sum(ks) + nd > budget:
    if num_distractor_rings is None and nd > max(1, floor):
      nd -= 1
    elif ks_fixed is None and max(ks) > 1:
      ks[ks.index(max(ks))] -= 1
    elif num_distractor_rings is None and nd > floor:
      nd -= 1
    else:
      break
  if crossing is None and cross and sum(ks) + nd > budget:
    cross = False
  if distractor_line is None:
    dline = nd > 0 and (bool(distractor_same_colour) or
                        random.random() < 0.6)
  else:
    dline = bool(distractor_line)
  if dline and nd < 1:
    return None
  if distractor_same_colour is None:
    same = dline and random.random() < 0.5
  else:
    same = dline and bool(distractor_same_colour)
  if decoy is None:
    use_decoy = random.random() < 0.3
  else:
    use_decoy = bool(decoy)
  n_line_rings = random.randint(1, min(2, nd)) if dline else 0

  if background is not None:
    bg = background
  else:
    bg = 0 if random.random() < 0.6 else random.randint(1, 9)
  palette = [c for c in range(10) if c != bg]
  random.shuffle(palette)
  marker_cols = palette[:nm]
  path_cols = palette[nm:2 * nm]
  pos = 2 * nm
  line_col = None
  if dline:
    if same:
      line_col = random.choice(path_cols)
    else:
      line_col = palette[pos]
      pos += 1
  decoy_col = None
  if use_decoy:
    decoy_col = palette[pos]
    pos += 1
  spare = len(palette) - pos
  ring_cols = palette[pos:pos + random.randint(1, min(4, spare))]

  total = sum(ks) + nd
  rings = _place([_ring_shape() for _ in range(total)], height, width,
                 _CLIP_PROB)
  if rings is None:
    return None
  for ring in rings:
    ring['colour'] = random.choice(ring_cols)
  idx = list(range(total))
  random.shuffle(idx)
  groups = []
  pos = 0
  for k in ks:
    groups.append(idx[pos:pos + k])
    pos += k
  line_group = idx[pos:pos + n_line_rings]

  all_foot = set()
  for ring in rings:
    all_foot |= ring['foot']
  near1 = _dilate(all_foot, 1, height, width)
  near2 = _dilate(all_foot, 2, height, width)

  cross_li = random.randint(1, nm - 1) if cross else -1
  cross_target = random.randint(0, cross_li - 1) if cross else -1
  placed = set()
  lines = []
  plans = [(g, path_cols[i], marker_cols[i]) for i, g in enumerate(groups)]
  if dline:
    plans.append((line_group, line_col, None))
  for li, (group, colour, mcol) in enumerate(plans):
    blocked = all_foot | _dilate(placed, 1, height, width)
    for j, ring in enumerate(rings):
      if j not in group:
        blocked |= ring['near1']
    avoid = near2 | _dilate(placed, 2, height, width)
    tail = random.random() < 0.6
    if li == cross_li:
      target = lines[cross_target]
      others = set()
      for k, other in enumerate(lines):
        if k != cross_target:
          others |= other['cells']
          if other['marker'] is not None:
            others.add(other['marker'])
      site = _crossing_site(target, near1,
                            _dilate(others, 1, height, width), height, width)
      if site is None:
        return None
      pre, mid1, mid, mid2, post = site
      start = _pick_cell(height, width,
                         avoid | _dilate(set(site), 2, height, width))
      if start is None:
        return None
      # The approach may only touch mid1 through pre, keeping the line
      # one cell wide on both sides of the crossing.
      forbid = (blocked | _dilate({mid2, post}, 1, height, width) |
                (_dilate({mid1}, 1, height, width) - {pre}) | {mid})
      forbid.discard(pre)
      seg = _leg(start, {pre}, forbid, height, width)
      if seg is None:
        return None
      order = _order(group, rings, post)
      rest = _route(post, [rings[j] for j in order], blocked, tail, height,
                    width, done=set(seg) | {mid1, mid, mid2})
      if rest is None:
        return None
      route = seg + [mid1, mid, mid2] + rest
      target['cells'].discard(mid)
    else:
      start = _pick_cell(height, width, avoid)
      if start is None:
        return None
      order = _order(group, rings, start)
      route = _route(start, [rings[j] for j in order], blocked, tail, height,
                     width)
      if route is None:
        return None
    if mcol is None:
      body = set(route)
    else:
      body = set(route[1:])
      if marker_blob is None:
        use_blob = random.random() < 0.25
      else:
        use_blob = bool(marker_blob)
      if use_blob:
        cand = [q for q in _nbrs8(start, height, width)
                if q not in body and q not in blocked]
        if cand:
          body |= set(random.sample(cand, random.randint(1, len(cand))))
        elif marker_blob:
          return None
    lines.append({
        'route': route,
        'cells': body,
        'colour': colour,
        'marker': start if mcol is not None else None,
        'marker_colour': mcol,
        'targets': list(group),
    })
    placed |= set(route) | body

  # Decoy colour: 2..3 isolated cells, often at line ends; never a marker.
  decoys = []
  if use_decoy:
    bad = _dilate(all_foot, 1, height, width)
    for line in lines:
      bad |= line['cells']
      if line['marker'] is not None:
        bad |= _dilate({line['marker']}, 1, height, width)
    ends = [line['route'][-1] for line in lines]
    for _ in range(random.randint(2, 3)):
      cand = []
      if random.random() < 0.7:
        cand = [q for q in _nbrs8(random.choice(ends), height, width)
                if q not in bad]
      if not cand:
        cand = [(r, c) for r in range(height) for c in range(width)
                if (r, c) not in bad]
      if not cand:
        return None
      q = random.choice(sorted(cand))
      decoys.append(q)
      bad |= _dilate({q}, 1, height, width)

  grid = common.grid(width, height, bg)
  for ring in rings:
    for r, c in ring['wall']:
      grid[r][c] = ring['colour']
  for line in lines:
    for r, c in line['cells']:
      grid[r][c] = line['colour']
    if line['marker'] is not None:
      grid[line['marker'][0]][line['marker'][1]] = line['marker_colour']
  for r, c in decoys:
    grid[r][c] = decoy_col

  # Constraint checks: each line touches exactly its own rings.
  ring_at = {}
  for j, ring in enumerate(rings):
    for cell in ring['foot']:
      ring_at[cell] = j
  for line in lines:
    touched = set()
    for cell in line['cells']:
      for q in _nbrs8(cell, height, width):
        if q in ring_at:
          touched.add(ring_at[q])
    if touched != set(line['targets']):
      return None
    if line['marker'] is not None:
      nb = {grid[q[0]][q[1]] for q in _nbrs8(line['marker'], height, width)}
      if not nb <= {bg, line['colour']} or line['colour'] not in nb:
        return None
  # Constraint checks: the only single-colour enclosures are the pockets,
  # apart from line-colour enclosures that no other marker path can reach.
  pockets = {frozenset(ring['pocket']) for ring in rings}
  line_colours = {line['colour'] for line in lines}
  found = 0
  for comp, colour in _single_colour_holes(grid, bg):
    if comp in pockets:
      found += 1
      continue
    if colour not in line_colours:
      return None
    zone = set(comp)
    for p in comp:
      for q in _nbrs8(p, height, width):
        if grid[q[0]][q[1]] == colour:
          zone.add(q)
    zone = _dilate(zone, 1, height, width)
    for line in lines:
      if (line['marker'] is not None and line['colour'] != colour and
          line['cells'] & zone):
        return None
  if found != len(rings):
    return None
  # Constraint checks: colour counts (markers are the only singletons).
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  marker_set = set(marker_cols)
  for v, n in counts.items():
    if v == bg:
      continue
    if (n == 1) != (v in marker_set) or n >= counts[bg]:
      return None

  output = [row[:] for row in grid]
  for line in lines:
    if line['marker'] is None:
      continue
    for j in line['targets']:
      for r, c in rings[j]['pocket']:
        output[r][c] = line['marker_colour']
  return {'input': grid, 'output': output}


def _replay_targets(grid, bg):
  """Check which pocket declarations have a visible marker-path witness.

  This graph check is confined to explicit replay. Normal random targets
  continue to be constructed from latent ring and route assignments.
  """
  h, w = len(grid), len(grid[0])
  counts = Counter(v for row in grid for v in row)
  holes = _single_colour_holes(grid, bg)
  hole_index = {p: i for i, (cells, _) in enumerate(holes) for p in cells}
  walls = []
  wall_index = {}
  for i, (cells, colour) in enumerate(holes):
    wall = {q for p in cells for q in _nbrs8(p, h, w)
            if grid[q[0]][q[1]] == colour}
    walls.append(wall)
    for p in wall:
      wall_index.setdefault(p, set()).add(i)
  markers = []
  for r in range(h):
    for c in range(w):
      colour = grid[r][c]
      if colour == bg or counts[colour] != 1:
        continue
      nearby = Counter(grid[y][x] for y, x in _nbrs8((r, c), h, w)
                       if grid[y][x] not in (bg, colour))
      if not nearby:
        continue
      ranked = nearby.most_common()
      if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        raise ValueError('marker has an ambiguous path colour')
      markers.append(((r, c), colour, ranked[0][0]))
  path_colours = {pc for _, _, pc in markers}
  targets = {}
  for marker, colour, pc in markers:
    pending = [p for p in _nbrs8(marker, h, w) if grid[p[0]][p[1]] == pc]
    visited = set(pending)
    activated = set()
    while pending:
      p = pending.pop()
      next_cells = set()
      hit_holes = set()
      for q in _nbrs8(p, h, w):
        value = grid[q[0]][q[1]]
        if value == pc:
          next_cells.add(q)
        else:
          if value in path_colours:
            next_cells.update(e for e in _nbrs8(q, h, w)
                              if grid[e[0]][e[1]] == pc)
          if q in hole_index:
            hit_holes.add(hole_index[q])
          hit_holes.update(wall_index.get(q, ()))
      for i in hit_holes - activated:
        if holes[i][1] in (pc, colour):
          continue
        activated.add(i)
        if i in targets and targets[i] != colour:
          raise ValueError('two markers imply different fills for one pocket')
        targets[i] = colour
        next_cells.update(q for cell in walls[i] for q in _nbrs8(cell, h, w)
                          if grid[q[0]][q[1]] == pc)
      pending.extend(next_cells - visited)
      visited |= next_cells
  return holes, hole_index, targets


def _replay(input_grid, fills):
  """Fixture replay: flood-fill each named pocket with its marker colour."""
  if not isinstance(input_grid, (list, tuple)) or any(
      not isinstance(row, (list, tuple)) for row in input_grid):
    raise ValueError('input_grid must contain rows')
  grid = [list(row) for row in input_grid]
  height = len(grid)
  if not height or not grid[0] or any(len(row) != len(grid[0])
                                      for row in grid):
    raise ValueError('input_grid must be a non-empty rectangle')
  width = len(grid[0])
  if height > 30 or width > 30 or any(
      not _is_int(v) or not 0 <= v <= 9 for row in grid for v in row):
    raise ValueError('replay needs 1..30 sides and integer colours0..9')
  if not isinstance(fills, (list, tuple)) or any(
      not isinstance(f, (list, tuple)) or len(f) != 3
      or not all(_is_int(v) for v in f) for f in fills):
    raise ValueError('fills must contain integer(row,col,colour) triples')
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  bg = max(sorted(counts), key=lambda v: counts[v])
  holes, hole_index, targets = _replay_targets(grid, bg)
  declared = {}
  for r, c, colour in fills:
    i = hole_index.get((r, c))
    if i is None or targets.get(i) != colour:
      raise ValueError('fill is not justified by a visible marker path')
    if i in declared:
      raise ValueError('a pocket may be declared only once')
    declared[i] = colour
  if declared != targets:
    raise ValueError('fills omit a marker-reachable pocket')
  output = [row[:] for row in grid]
  for r, c, colour in fills:
    if not _inside((r, c), height, width):
      raise ValueError('fill seed outside the grid')
    if not _is_int(colour) or not 0 <= colour <= 9:
      raise ValueError('fill colour must be an integer 0..9')
    if grid[r][c] != bg:
      raise ValueError('fill seed must be a background cell')
    comp = [(r, c)]
    seen = {(r, c)}
    border = set()
    i = 0
    while i < len(comp):
      p = comp[i]
      i += 1
      for dr, dc in _D4:
        q = (p[0] + dr, p[1] + dc)
        if not _inside(q, height, width):
          continue
        v = grid[q[0]][q[1]]
        if v == bg:
          if q not in seen:
            seen.add(q)
            comp.append(q)
        else:
          border.add(v)
    if len(border) != 1:
      raise ValueError('fill seed is not inside a single-colour pocket')
    for p in comp:
      output[p[0]][p[1]] = colour
  return {'input': grid, 'output': output}


def generate(width=None, height=None, background=None, num_markers=None,
             rings_per_marker=None, num_distractor_rings=None,
             distractor_line=None, distractor_same_colour=None,
             crossing=None, marker_blob=None, decoy=None, input_grid=None,
             fills=None):
  """Generates an input/output pair for the ring-threading task.

  Args:
    width: grid width, integer 8..30. Random 10..30 (12..30 with crossing)
      if None.
    height: grid height, integer 8..30. Random like width if None.
    background: background colour, integer 0..9. Usually 0, otherwise
      random.
    num_markers: integer 1..3 marker cells, each with its own path colour.
    rings_per_marker: list or tuple of positive ints, giving the number of
      threaded rings per marker. Its length must agree with num_markers if
      both are given.
    num_distractor_rings: integer number (0..40) of rings that no marker
      path touches.
    distractor_line: bool; whether a marker-less line threads some
      distractor rings. Requires at least one distractor ring.
    distractor_same_colour: bool; whether the marker-less line reuses a
      marker's path colour, so it is a disconnected same-colour segment.
      True implies distractor_line, and is incompatible with
      distractor_line=False.
    crossing: bool; whether one marker's line crosses an earlier marker's
      line. Requires at least two markers, sides of at least 12 and a ring
      count within the sparser w*h/60 crossing budget. When None, a random
      crossing is only built on grids whose sides are both at least 12.
    marker_blob: bool; whether markers sit in a small blob of their path
      colour.
    decoy: bool; whether a non-marker colour appears 2..3 times.
    input_grid: fixture replay only, an explicit input grid.
    fills: fixture replay only, list of (row, col, colour) pocket seeds.

  Returns:
    {'input': grid, 'output': grid}.
  """
  if input_grid is not None or fills is not None:
    if input_grid is None or fills is None:
      raise ValueError('fixture replay needs both input_grid and fills')
    others = (width, height, background, num_markers, rings_per_marker,
              num_distractor_rings, distractor_line, distractor_same_colour,
              crossing, marker_blob, decoy)
    if any(v is not None for v in others):
      raise ValueError('random-generation controls cannot be combined with '
                       'fixture replay')
    return _replay(input_grid, fills)
  for name, value, lo, hi in (
      ('width', width, _MIN_SIDE, _MAX_SIDE),
      ('height', height, _MIN_SIDE, _MAX_SIDE),
      ('background', background, 0, 9),
      ('num_markers', num_markers, 1, 3),
      ('num_distractor_rings', num_distractor_rings, 0,
       _MAX_DISTRACTOR_RINGS)):
    if value is not None and (not _is_int(value) or not lo <= value <= hi):
      raise ValueError('%s must be an integer in %d..%d' % (name, lo, hi))
  for name, value in (('distractor_line', distractor_line),
                      ('distractor_same_colour', distractor_same_colour),
                      ('crossing', crossing), ('marker_blob', marker_blob),
                      ('decoy', decoy)):
    if value is not None and not isinstance(value, bool):
      raise ValueError('%s must be a bool or None' % name)
  ks_fixed = None
  if rings_per_marker is not None:
    if (not isinstance(rings_per_marker, (list, tuple)) or
        not all(_is_int(k) for k in rings_per_marker)):
      raise ValueError('rings_per_marker must be a list of integers')
    ks_fixed = list(rings_per_marker)
    if not 1 <= len(ks_fixed) <= 3 or min(ks_fixed) < 1:
      raise ValueError('rings_per_marker needs 1..3 positive counts')
    if num_markers is not None and num_markers != len(ks_fixed):
      raise ValueError('num_markers disagrees with rings_per_marker')
  if (distractor_line or distractor_same_colour) and num_distractor_rings == 0:
    raise ValueError('a distractor line needs at least one distractor ring')
  if distractor_same_colour and distractor_line is False:
    raise ValueError('distractor_same_colour requires a distractor line')
  n_fixed = len(ks_fixed) if ks_fixed is not None else num_markers
  if crossing and n_fixed == 1:
    raise ValueError('crossing needs at least two markers')
  if crossing and any(v is not None and v < _CROSSING_MIN_SIDE
                      for v in (width, height)):
    raise ValueError('crossing needs sides of at least %d' %
                     _CROSSING_MIN_SIDE)
  if ks_fixed is not None:
    marker_rings = sum(ks_fixed)
  elif num_markers is not None:
    marker_rings = num_markers
  else:
    marker_rings = 2 if crossing else 1
  if num_distractor_rings is not None:
    dist_rings = num_distractor_rings
  else:
    dist_rings = 1 if (distractor_line or distractor_same_colour) else 0
  needed = marker_rings + dist_rings
  max_w = width if width is not None else _MAX_SIDE
  max_h = height if height is not None else _MAX_SIDE
  if needed > _budget(max_w, max_h, bool(crossing)):
    raise ValueError('too many rings for the requested grid size')
  for _ in range(500):
    result = _attempt(width, height, background, ks_fixed, num_markers,
                      num_distractor_rings, distractor_line,
                      distractor_same_colour, crossing, marker_blob, decoy,
                      needed)
    if result is not None:
      return result
  raise RuntimeError('could not construct a ring-threading scene')


_TRAIN_1 = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 0, 0],
    [0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 5, 0],
    [2, 0, 0, 2, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 5, 0],
    [2, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1, 5, 5, 1, 0],
    [0, 2, 2, 1, 0, 0, 0, 0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 2, 1, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 1, 0, 0, 0, 0, 2, 0, 2, 2, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 2, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 2, 0, 0, 2, 2, 0, 1, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 0, 0, 0, 1, 0],
    [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 3, 0, 0, 3, 0, 0, 0, 2, 2, 1, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 3, 0, 0, 3, 0, 0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 1, 0, 0, 1, 3, 3, 1, 1, 1, 2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 7],
]

_TRAIN_2 = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0],
    [0, 0, 0, 2, 2, 0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0, 2, 0],
    [0, 0, 2, 0, 0, 2, 2, 0, 0, 2, 0, 0, 2, 2, 0, 2, 0, 0, 2, 0],
    [0, 0, 2, 0, 0, 2, 1, 2, 2, 0, 0, 2, 0, 0, 2, 0, 2, 2, 1, 0],
    [0, 0, 0, 2, 2, 1, 1, 1, 0, 0, 0, 2, 0, 0, 2, 0, 0, 1, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 2, 2, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 2, 2, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 2],
    [4, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 2],
]

_TRAIN_3 = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2],
    [0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 2, 0, 0],
    [0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0, 2, 0, 0, 0, 2, 0, 0],
    [0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0, 2, 0, 0, 0, 3, 2, 2],
    [0, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 0, 0, 0, 3, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 3, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 3, 0],
    [1, 1, 0, 0, 0, 0, 0, 2, 2, 1, 1, 1, 0, 0, 0, 0, 2, 2, 3, 0],
    [0, 1, 0, 0, 0, 0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0, 2, 0],
    [1, 1, 0, 0, 0, 0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0, 2, 0],
    [0, 0, 0, 0, 0, 0, 1, 2, 2, 0, 0, 0, 0, 0, 0, 3, 2, 2, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 3, 3, 2, 2, 3, 0, 0, 0, 0],
    [0, 0, 2, 2, 1, 0, 0, 0, 0, 0, 3, 0, 2, 0, 0, 2, 0, 0, 0, 0],
    [0, 2, 0, 0, 2, 0, 0, 0, 3, 3, 3, 0, 2, 0, 0, 2, 0, 0, 0, 0],
    [0, 2, 0, 0, 2, 0, 0, 0, 3, 4, 3, 0, 0, 2, 2, 0, 0, 0, 0, 0],
]

_TRAIN_4 = [
    [0, 0, 2, 2, 0, 0, 0, 0],
    [0, 2, 0, 0, 2, 0, 0, 0],
    [0, 2, 0, 0, 2, 0, 0, 0],
    [0, 0, 2, 2, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 0, 0, 1, 4],
]

_TEST_1 = [
    [6, 1, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 8],
    [1, 1, 1, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3],
    [5, 5, 5, 1, 9, 9, 1, 1, 1, 1, 1, 1, 1, 9, 9, 9, 9, 9, 9, 9, 5, 5, 5, 5, 5, 5, 3, 3, 5, 5],
    [5, 5, 5, 9, 5, 5, 9, 5, 5, 5, 5, 5, 9, 5, 5, 5, 5, 5, 5, 5, 9, 5, 5, 5, 5, 5, 3, 5, 5, 5],
    [5, 5, 5, 9, 5, 5, 9, 5, 5, 5, 5, 5, 9, 5, 5, 5, 5, 5, 5, 5, 9, 5, 5, 5, 5, 3, 3, 5, 5, 5],
    [5, 5, 5, 5, 9, 9, 5, 5, 5, 5, 5, 5, 5, 9, 9, 9, 9, 9, 9, 9, 1, 1, 1, 1, 5, 3, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 3, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 1, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 5, 5, 1, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 9, 3, 5, 5, 1, 5, 5],
    [5, 5, 5, 5, 9, 9, 9, 9, 9, 9, 9, 5, 5, 5, 5, 5, 9, 3, 3, 5, 5, 9, 5, 5, 9, 5, 5, 1, 5, 5],
    [5, 5, 5, 9, 5, 5, 5, 5, 5, 5, 5, 9, 5, 5, 5, 9, 9, 9, 3, 3, 3, 9, 5, 5, 9, 5, 5, 1, 5, 5],
    [5, 5, 5, 9, 5, 5, 5, 5, 5, 5, 5, 9, 5, 5, 5, 9, 5, 9, 5, 5, 3, 3, 9, 9, 5, 5, 5, 1, 1, 5],
    [5, 5, 3, 3, 9, 9, 9, 9, 9, 9, 9, 5, 5, 5, 5, 9, 5, 9, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 5],
    [5, 0, 3, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 9, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 9, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 1, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 9, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 9, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 5, 5],
    [5, 5, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 9, 5, 5, 5, 5, 5, 5, 5, 5, 1, 1, 5, 5],
    [5, 5, 3, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 9, 5, 5, 5, 5, 5, 5, 5, 5, 1, 5, 5, 5],
    [5, 5, 3, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 3, 9, 5, 5, 5, 5, 5, 5, 5, 5, 1, 1, 5, 5, 5],
    [5, 5, 3, 3, 5, 5, 5, 5, 5, 5, 3, 3, 3, 3, 5, 5, 5, 5, 5, 5, 9, 9, 9, 1, 1, 1, 5, 5, 5, 5],
    [5, 5, 5, 3, 9, 9, 3, 3, 3, 3, 3, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 5, 9, 1, 1, 5, 5, 5, 5, 5],
    [5, 5, 5, 9, 5, 5, 9, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 5, 5, 9, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 9, 5, 5, 9, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 5, 5, 9, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 9, 9, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 5, 5, 9, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 5, 5, 9, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 9, 9, 9, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
]

_TEST_2 = [
    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 8, 8, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 8, 0, 0, 8],
    [0, 0, 0, 0, 2, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 8, 8, 0, 0, 8, 0, 0, 8],
    [0, 0, 0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 8, 0, 0, 8, 8, 0],
    [0, 0, 0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 2, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 8, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 0, 0, 1, 1, 6, 6, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 6, 0, 0, 0, 6, 0, 0, 0, 8, 8, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 0, 0, 0, 0, 6, 0, 0, 0, 6, 0, 0, 8, 0, 0, 8, 0, 0, 0, 5, 5, 5, 1, 0],
    [0, 0, 1, 0, 0, 0, 0, 6, 0, 0, 0, 6, 0, 0, 8, 0, 0, 8, 0, 0, 5, 0, 0, 0, 5, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 6, 6, 6, 0, 0, 9, 9, 8, 8, 9, 0, 0, 5, 0, 0, 0, 5, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 9, 9, 0, 0, 5, 5, 5, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 8, 8, 9, 9, 0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 8, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 8, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 8, 8, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 8, 8, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 8, 9, 0, 0, 8, 0, 0, 8, 0],
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 8, 0, 0, 8, 0, 0, 8, 0],
    [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 8, 0, 0, 9, 8, 8, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 9, 9, 9, 9, 0, 0, 0, 0, 9, 8, 8, 9, 9, 9, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 9, 9, 9, 0, 0, 0, 9, 9, 9, 9, 9, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [4, 1, 0, 0, 9, 3, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]


def validate():
  """Reconstructs the canonical pairs by replaying inputs with fill seeds."""
  train = [
      generate(input_grid=_TRAIN_1,
               fills=[(1, 20, 7), (5, 17, 7), (11, 7, 7), (12, 13, 7)]),
      generate(input_grid=_TRAIN_2,
               fills=[(3, 3, 4), (2, 7, 4), (2, 16, 4)]),
      generate(input_grid=_TRAIN_3,
               fills=[(1, 18, 4), (8, 16, 4), (13, 13, 4)]),
      generate(input_grid=_TRAIN_4, fills=[(1, 2, 4)]),
  ]
  test = [
      generate(input_grid=_TEST_1,
               fills=[(3, 4, 6), (3, 13, 6), (22, 20, 6),
                      (10, 22, 8), (12, 16, 8), (23, 4, 8)]),
      generate(input_grid=_TEST_2,
               fills=[(3, 4, 4), (3, 18, 4), (7, 8, 4), (9, 21, 4),
                      (8, 15, 3), (13, 8, 3), (16, 22, 3), (17, 16, 3)]),
  ]
  return {'train': train, 'test': test}
