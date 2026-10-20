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

"""ARC task d35bdbdc: a grey path selects two badges, which get new centres.

Rule: the grid holds several badges. A badge is a ring of one colour around a
centre cell of another colour. It is either a full 3x3 ring or a plus shape
with only the four arms, and it may be clipped by the grid edge. A thin grey (5)
path has exactly two loose ends, and each end sits next to a badge. In the
output every badge is erased and the grey path is kept. The two badges at the
path ends are then restored. Each one's old centre colour names another badge
by its ring colour. That badge's original centre colour becomes the restored
badge's new centre.

Selection at an end: among eligible badges touching the end (a badge is
eligible when its centre colour is some badge's ring colour), keep those whose
centre is nearest. The two ends must then determine exactly one unordered pair
of distinct badges.

Scope: about half of the default random scenes are 10x10, like every ARC
example. The rest use 10..16 cells per side as a synthetic extension. Larger
badge counts raise the minimum sampled side. Explicit sizes from 7 to 30 per
side are accepted. Each scene uses one shape style (full rings or pluses). It
has 3 to 8 badges with distinct ring colours. In random scenes badge boxes never
overlap and never share an edge, although they may touch at a corner, as in the
ARC data. The path never passes between two corner-touching badges. With
allow_clip, exactly one badge is clipped by a grid edge, never at a corner.

Distractor centres are random. Some point at a ring and compete with the
selected badges; others point nowhere. Occasionally a distractor's centre
equals its own ring colour, as in the ARC query. This only happens where it
cannot create spurious badge centres. A restored badge never ends up with a
centre equal to its own ring colour.

Two selection modes are sampled. In 'geometry' scenes a path end may touch
extra badges, but the pair is unique by geometry alone: the extra badges are
farther away, or tied with the badge at the other end (the distinct-pair
situation of the second ARC query). In 'eligibility' scenes (about 35% of
default random scenes with at most 7 badges) one path end touches the selected
badge and an ineligible distractor whose centre colour names no ring. That
distractor is as near as, or nearer than, the selected badge, so only the
eligibility filter decides the pair, as in the third ARC query. The path is a
random winding thin 8-connected path that keeps out of every badge box.

Explicit scenes (badges, path, selected) are checked. Badges must not intrude
into each other's boxes. The path must avoid every badge box, be connected and
have exactly two ends. `selected` must be the unique pair those ends determine.
The rendered input is also scanned for cells that look like badge centres. The
cells found must be exactly the declared centres, so that no spurious badges
appear. An optional `selection` asserts which mode the explicit scene uses.
"""

import random

import common

BADGE_COLORS = [1, 2, 3, 4, 6, 7, 8, 9]
SHAPES = ('ring', 'plus')
SELECTIONS = ('geometry', 'eligibility')
DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
MIN_SIDE, MAX_SIDE = 7, 30


def _cheb(p, q):
  return max(abs(p[0] - q[0]), abs(p[1] - q[1]))


def _mask(r, c, shape, h, w):
  """In-grid non-black cells of a badge centred at (r, c)."""
  cells = []
  for dr in (-1, 0, 1):
    for dc in (-1, 0, 1):
      if shape == 'plus' and dr and dc:
        continue
      rr, cc = r + dr, c + dc
      if 0 <= rr < h and 0 <= cc < w:
        cells.append((rr, cc))
  return cells


def _box(r, c, h, w):
  return [(rr, cc) for rr in range(r - 1, r + 2) for cc in range(c - 1, c + 2)
          if 0 <= rr < h and 0 <= cc < w]


def _counted(cell, road):
  """Grey neighbours of a cell; a diagonal counts only without an orthogonal link."""
  r, c = cell
  out = set()
  for dr, dc in DIRS:
    q = (r + dr, c + dc)
    if q not in road:
      continue
    if dr and dc and ((r + dr, c) in road or (r, c + dc) in road):
      continue
    out.add(q)
  return out


def _touch(cell, mask):
  return any(_cheb(cell, m) == 1 for m in mask)


def _touch_count(cell, masks):
  return sum(1 for m in masks if _touch(cell, m))


def _nearest(cell, centres, masks, eligible):
  """Eligible badges touching cell whose centres are nearest to it."""
  cands = [i for i in range(len(masks)) if eligible[i] and _touch(cell, masks[i])]
  if not cands:
    return set()
  dist = {i: (centres[i][0] - cell[0]) ** 2 + (centres[i][1] - cell[1]) ** 2
          for i in cands}
  best = min(dist.values())
  return {i for i in cands if dist[i] == best}


def _pairs(first, second):
  """Unordered pairs of distinct badges, one from each end's candidates."""
  return {tuple(sorted((i, j))) for i in first for j in second if i != j}


def _spaced(p, centres):
  """Badge boxes may touch diagonally at a corner but never share an edge."""
  for q in centres:
    dr, dc = abs(p[0] - q[0]), abs(p[1] - q[1])
    if max(dr, dc) < 4 and not (dr >= 3 and dc >= 3):
      return False
  return True


def _place(h, w, count, clip):
  """Places badge centres; with clip exactly one sits on a non-corner edge cell."""
  centres = []
  if clip:
    edge = [(r, c) for r in (0, h - 1) for c in range(1, w - 1)]
    edge += [(r, c) for c in (0, w - 1) for r in range(1, h - 1)]
    centres.append(random.choice(edge))
  spots = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
  random.shuffle(spots)
  for p in spots:
    if len(centres) == count:
      break
    if _spaced(p, centres):
      centres.append(p)
  if len(centres) < count:
    return None
  random.shuffle(centres)
  return centres


def _junctions(centres, h, w):
  """The two free cells between every pair of corner-touching badge boxes."""
  out = set()
  for i in range(len(centres)):
    for j in range(i + 1, len(centres)):
      (r1, c1), (r2, c2) = centres[i], centres[j]
      dr, dc = r2 - r1, c2 - c1
      if abs(dr) == 3 and abs(dc) == 3:
        sr = 1 if dr > 0 else -1
        sc = 1 if dc > 0 else -1
        for p in ((r1 + sr, c1 + 2 * sc), (r1 + 2 * sr, c1 + sc)):
          if 0 <= p[0] < h and 0 <= p[1] < w:
            out.add(p)
  return out


def _self_ok(centre, shape, h, w):
  """Whether a badge may use its ring colour as centre without spurious centres."""
  r, c = centre
  if r in (0, h - 1) or c in (0, w - 1):
    return False
  if shape == 'plus':
    return True
  return 2 <= r <= h - 3 and 2 <= c <= w - 3


def _colours(centres, a, b, shape, h, w, dead):
  """Distinct rings; the selected badges point at another badge's ring.

  Badges in dead get a centre colour that names no ring, which makes them
  ineligible. A draw is redrawn when a restored badge would receive its own
  ring colour as its centre, for example when the two selected badges point at
  each other.
  """
  n = len(centres)
  for _ in range(20):
    rings = random.sample(BADGE_COLORS, n)
    spare = [x for x in BADGE_COLORS if x not in rings]
    if dead and not spare:
      return None
    ctrs = []
    for i in range(n):
      if i in (a, b):
        ctrs.append(rings[random.choice([j for j in range(n) if j != i])])
      elif i in dead:
        ctrs.append(random.choice(spare))
      elif _self_ok(centres[i], shape, h, w) and random.random() < 0.15:
        ctrs.append(rings[i])
      else:
        ctrs.append(random.choice([x for x in BADGE_COLORS if x != rings[i]]))
    if all(ctrs[rings.index(ctrs[i])] != rings[i] for i in (a, b)):
      return rings, ctrs
  return None


def _walk(start, a, b, h, w, forbidden, centres, masks, eligible, waypoint,
          min_len, budget, contested, elig):
  """Grows a thin path from start until its two ends select {a, b} uniquely.

  The selection is judged with the eligibility filter. In geometry mode the
  pair must also be unique when every badge counts as eligible. In eligibility
  mode it must not be, so the filter is what decides it. With contested, the
  head must also touch at least two badges.
  """
  everyone = [True] * len(masks)
  target = {tuple(sorted((a, b)))}
  start_el = _nearest(start, centres, masks, eligible)
  start_geo = _nearest(start, centres, masks, everyone)
  seq, pos, road = [start], {start: 0}, {start}

  def expected(x):
    i = pos[x]
    exp = set()
    if i > 0:
      exp.add(seq[i - 1])
    if i + 1 < len(seq):
      exp.add(seq[i + 1])
    return exp

  goal = waypoint if waypoint is not None else centres[b]
  for _ in range(budget):
    cur = seq[-1]
    if waypoint is not None and goal == waypoint and _cheb(cur, goal) <= 1:
      goal = centres[b]
    if len(seq) >= min_len:
      head_el = _nearest(cur, centres, masks, eligible)
      if _pairs(start_el, head_el) == target:
        head_geo = _nearest(cur, centres, masks, everyone)
        by_geometry = _pairs(start_geo, head_geo) == target
        if by_geometry != elig and (
            not contested or _touch_count(cur, masks) >= 2):
          return seq
    options = []
    for dr, dc in DIRS:
      n = (cur[0] + dr, cur[1] + dc)
      if not (0 <= n[0] < h and 0 <= n[1] < w) or n in forbidden or n in road:
        continue
      seq.append(n)
      pos[n] = len(seq) - 1
      road.add(n)
      ok = all(_counted(x, road) == expected(x) for x in road if _cheb(x, n) <= 1)
      seq.pop()
      del pos[n]
      road.discard(n)
      if ok:
        options.append(n)
    if not options:
      return None
    if random.random() < 0.7:
      dist = [(o[0] - goal[0]) ** 2 + (o[1] - goal[1]) ** 2 for o in options]
      best = min(dist)
      nxt = random.choice([o for o, d in zip(options, dist) if d == best])
    else:
      nxt = random.choice(options)
    seq.append(nxt)
    pos[nxt] = len(seq) - 1
    road.add(nxt)
  return None


def _build(h, w, shape, count, clip, elig):
  """Bounded search for badges, colours and a path; None when it fails.

  In eligibility mode an ineligible distractor d is placed with its box one
  cell away from badge a, and the path starts at a free cell where d is at
  least as near as a, so only the eligibility filter selects a there.
  """
  budget = 3 * (h + w) + 30
  everyone = [True] * count
  for _ in range(30):
    centres = _place(h, w, count, clip)
    if centres is None:
      continue
    if elig:
      close = [(i, j) for i in range(count) for j in range(count)
               if i != j and _cheb(centres[i], centres[j]) == 4]
      if not close:
        continue
      d, a = random.choice(close)
      b = random.choice([k for k in range(count) if k not in (a, d)])
      dead = {d} | {k for k in range(count)
                    if k not in (a, b, d) and random.random() < 0.25}
    else:
      a, b = random.sample(range(count), 2)
      dead = set()
    colours = _colours(centres, a, b, shape, h, w, dead)
    if colours is None:
      continue
    rings, ctrs = colours
    eligible = [ctrs[i] in rings for i in range(count)]
    masks = [_mask(r, c, shape, h, w) for r, c in centres]
    forbidden = _junctions(centres, h, w)
    for r, c in centres:
      forbidden.update(_box(r, c, h, w))
    free = [(r, c) for r in range(h) for c in range(w) if (r, c) not in forbidden]
    if not free:
      continue
    if elig:
      starts = [p for p in free
                if _nearest(p, centres, masks, eligible) == {a}
                and _nearest(p, centres, masks, everyone) != {a}]
      contested_starts = []
    else:
      starts = [p for p in free if _nearest(p, centres, masks, everyone) == {a}]
      contested_starts = [p for p in starts if _touch_count(p, masks) >= 2]
    if not starts:
      continue
    for attempt in range(3):
      pool = starts
      if contested_starts and random.random() < 0.4:
        pool = contested_starts
      contested = attempt == 0 and random.random() < 0.3
      waypoint = random.choice(free) if random.random() < 0.6 else None
      min_len = random.randint(4, max(4, (h + w) // 3))
      path = _walk(random.choice(pool), a, b, h, w, forbidden, centres, masks,
                   eligible, waypoint, min_len, budget, contested, elig)
      if path:
        badges = [(centres[i][0], centres[i][1], rings[i], ctrs[i])
                  for i in range(count)]
        return badges, path, (a, b)
  return None


def _sample_count(h, w):
  area = h * w
  if area < 80:
    return random.randint(3, 4)
  hi = 5 if area <= 100 else 6 if area <= 160 else 7 if area <= 225 else 8
  if area <= 100 and random.random() < 0.15:
    hi = 6
  return random.randint(4, hi)


def _min_side(count):
  """Smallest sampled side that comfortably fits the requested badge count."""
  return 10 if count <= 5 else 12 if count == 6 else 13 if count == 7 else 15


def _draw(h, w, shape, badges, path):
  """Paints the input grid and returns it with the badge masks."""
  grid = common.grid(w, h, 0)
  masks = []
  for r, c, ring, ctr in badges:
    m = _mask(r, c, shape, h, w)
    masks.append(m)
    for rr, cc in m:
      grid[rr][cc] = ring
    grid[r][c] = ctr
  for r, c in path:
    grid[r][c] = 5
  return grid, masks


def _detect(grid):
  """Cells that structurally look like badge centres (used only as a check)."""
  h, w = len(grid), len(grid[0])
  found = set()
  for r in range(h):
    for c in range(w):
      arms = [(rr, cc) for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
              if 0 <= rr < h and 0 <= cc < w]
      if len(arms) < 3 or len({grid[rr][cc] for rr, cc in arms}) != 1:
        continue
      ring, ctr = grid[arms[0][0]][arms[0][1]], grid[r][c]
      if ring in (0, 5) or ctr in (0, 5):
        continue
      if any(grid[rr][cc] not in (0, ring, ctr) for rr, cc in _box(r, c, h, w)):
        continue
      found.add((r, c))
  return found


def _check_scene(h, w, shape, badges, path, selected):
  """Rejects scenes that break the task's structural invariants.

  Returns True when geometry alone (every badge treated as eligible) already
  determines the selected pair, and False when the eligibility filter decides.
  """
  n = len(badges)
  if n < 2:
    raise ValueError('need at least two badges')
  if len(selected) != 2 or selected[0] == selected[1]:
    raise ValueError('selected must name two distinct badges')
  if any(not 0 <= i < n for i in selected):
    raise ValueError('selected index out of range')
  centres = [(bd[0], bd[1]) for bd in badges]
  rings = [bd[2] for bd in badges]
  for r, c, ring, ctr in badges:
    if not (0 <= r < h and 0 <= c < w):
      raise ValueError('badge centre outside the grid')
    if ring in (0, 5) or ctr in (0, 5):
      raise ValueError('badges may not use black or grey')
    arms = sum(1 for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
               if 0 <= rr < h and 0 <= cc < w)
    if arms < 3:
      raise ValueError('a badge needs at least three in-grid arms')
  if len(set(rings)) != n:
    raise ValueError('ring colours must be distinct')
  masks = [_mask(r, c, shape, h, w) for r, c in centres]
  boxes = [set(_box(r, c, h, w)) for r, c in centres]
  for i in range(n):
    for j in range(n):
      if i != j and any(m in boxes[j] for m in masks[i]):
        raise ValueError('badges intrude into each other')
  road = {tuple(p) for p in path}
  if len(road) != len(path):
    raise ValueError('duplicate path cells')
  for r, c in road:
    if not (0 <= r < h and 0 <= c < w):
      raise ValueError('path cell outside the grid')
    if any((r, c) in bx for bx in boxes):
      raise ValueError('path cell inside a badge box')
  ends = [p for p in road if len(_counted(p, road)) == 1]
  if len(ends) != 2:
    raise ValueError('the path must have exactly two ends')
  seen, stack = {ends[0]}, [ends[0]]
  while stack:
    r, c = stack.pop()
    for dr, dc in DIRS:
      q = (r + dr, c + dc)
      if q in road and q not in seen:
        seen.add(q)
        stack.append(q)
  if len(seen) != len(road):
    raise ValueError('the path must be one connected piece')
  grid, _ = _draw(h, w, shape, badges, path)
  if _detect(grid) != set(centres):
    raise ValueError('the layout creates spurious or missing badge centres')
  target = {tuple(sorted(selected))}
  eligible = [bd[3] in rings for bd in badges]
  sels = [_nearest(e, centres, masks, eligible) for e in ends]
  if _pairs(sels[0], sels[1]) != target:
    raise ValueError('selected is not the unique pair at the path ends')
  everyone = [True] * n
  geo = [_nearest(e, centres, masks, everyone) for e in ends]
  return _pairs(geo[0], geo[1]) == target


def _render(h, w, shape, badges, path, selected):
  """Draws the input and derives the output from the latent scene."""
  grid, masks = _draw(h, w, shape, badges, path)
  out = [row[:] for row in grid]
  for m in masks:
    for rr, cc in m:
      out[rr][cc] = 0
  for i in selected:
    r, c, ring, ctr = badges[i]
    donors = [bd for bd in badges if bd[2] == ctr]
    if len(donors) != 1:
      raise ValueError('a selected centre must name exactly one ring')
    for rr, cc in masks[i]:
      out[rr][cc] = ring
    out[r][c] = donors[0][3]
  return {'input': grid, 'output': out}


def generate(height=None, width=None, shape=None, badges=None, path=None,
             selected=None, num_badges=None, allow_clip=None, selection=None):
  """Builds an input/output pair.

  Args:
    height: grid height (7..30). Random scenes default to 10, or to a synthetic
      10..16 extension with a larger minimum for 6+ badges. Explicit scenes
      default to 10.
    width: grid width (7..30), with the same defaults as height.
    shape: 'ring' for full 3x3 rings or 'plus' for four-arm badges. It is
      required with explicit badges and random otherwise.
    badges: explicit list of (row, col, ring_colour, centre_colour) tuples.
    path: explicit list of (row, col) grey path cells (only with badges).
    selected: pair of indices into badges for the path-end badges (only with
      badges). It must equal the pair the path ends determine.
    num_badges: exact badge count (3..8) for random scenes.
    allow_clip: random scenes only. True forces exactly one badge clipped by an
      edge and False forbids clipping. When unset, clipping happens 30% of the
      time.
    selection: 'geometry' (the pair is unique even if every badge counted as
      eligible) or 'eligibility' (an ineligible distractor at a path end is as
      near as the selected badge, so the eligibility filter decides). Random
      scenes sample it (eligibility about 35% of the time when at most 7
      badges); 'eligibility' needs at most 7 badges. With explicit badges it is
      an assertion that is checked against the scene.
  """
  for side in (height, width):
    if side is not None and not MIN_SIDE <= side <= MAX_SIDE:
      raise ValueError('grid sides must be between 7 and 30')
  if shape is not None and shape not in SHAPES:
    raise ValueError('shape must be ring or plus')
  if selection is not None and selection not in SELECTIONS:
    raise ValueError('selection must be geometry or eligibility')
  if badges is not None:
    if path is None or selected is None or shape is None:
      raise ValueError('explicit badges need shape, path and selected')
    if num_badges is not None or allow_clip is not None:
      raise ValueError('num_badges and allow_clip only apply to random scenes')
    h = height if height is not None else 10
    w = width if width is not None else 10
    by_geometry = _check_scene(h, w, shape, badges, path, selected)
    if selection is not None and (selection == 'geometry') != by_geometry:
      raise ValueError('the scene does not use the requested selection mode')
    return _render(h, w, shape, badges, path, selected)
  if path is not None or selected is not None:
    raise ValueError('path and selected require explicit badges')
  if num_badges is not None and not 3 <= num_badges <= len(BADGE_COLORS):
    raise ValueError('num_badges must be between 3 and 8')
  if selection == 'eligibility' and num_badges == len(BADGE_COLORS):
    raise ValueError('eligibility selection needs a spare colour: at most 7 badges')
  lo = _min_side(num_badges) if num_badges is not None else 10
  for _ in range(20):
    if height is None and width is None and lo == 10 and random.random() < 0.5:
      h, w = 10, 10
    else:
      hi = max(lo, 16)
      h = height if height is not None else random.randint(lo, hi)
      w = width if width is not None else random.randint(lo, hi)
    sh = shape if shape is not None else ('ring' if random.random() < 0.6 else 'plus')
    count = num_badges if num_badges is not None else _sample_count(h, w)
    if selection == 'eligibility':
      count = min(count, len(BADGE_COLORS) - 1)
    if selection is None:
      elig = count < len(BADGE_COLORS) and random.random() < 0.35
    else:
      elig = selection == 'eligibility'
    clip = bool(allow_clip) if allow_clip is not None else random.random() < 0.3
    scene = _build(h, w, sh, count, clip, elig)
    if scene is not None:
      bds, pth, sel = scene
      by_geometry = _check_scene(h, w, sh, bds, pth, sel)
      if by_geometry == elig:
        continue
      return _render(h, w, sh, bds, pth, sel)
  raise ValueError('could not construct a scene with the requested parameters')


def _cells(spec):
  return [(r, c) for r, cols in spec for c in cols]


def validate():
  """Reconstructs the canonical ARC pairs from explicit latent parameters."""
  train = [
      generate(height=10, width=10, shape='ring',
               badges=[(1, 8, 3, 4), (4, 3, 4, 2), (5, 8, 6, 1), (8, 3, 1, 3)],
               path=_cells([(1, [2, 3, 4, 5, 6]), (2, [1]), (3, [1]), (4, [0]),
                            (5, [1, 6]), (6, [1, 2, 3, 4, 5])]),
               selected=(0, 2), selection='geometry'),
      generate(height=10, width=10, shape='ring',
               badges=[(1, 1, 2, 6), (1, 7, 3, 2), (5, 1, 8, 3), (5, 8, 1, 4),
                       (8, 5, 4, 8)],
               path=_cells([(2, [4]), (3, [3, 5, 6, 7, 8]), (4, [4]), (5, [5]),
                            (6, [4]), (7, [1, 3]), (8, [1, 2])]),
               selected=(2, 3)),
      generate(height=10, width=10, shape='ring',
               badges=[(1, 1, 1, 2), (1, 8, 4, 3), (5, 5, 3, 6), (8, 1, 2, 9),
                       (8, 8, 7, 4)],
               path=_cells([(2, [5]), (3, [1, 4, 6]), (4, [1, 3, 7]), (5, [2, 8]),
                            (6, [8])]),
               selected=(0, 4)),
  ]
  test = [
      generate(height=10, width=10, shape='plus',
               badges=[(1, 7, 2, 3), (2, 2, 4, 2), (6, 4, 1, 9), (6, 8, 3, 3),
                       (7, 1, 7, 1)],
               path=_cells([(3, [7]), (4, [6]), (5, [6]), (6, [6]), (7, [6]),
                            (8, [3, 5]), (9, [1, 2, 4])]),
               selected=(0, 4), selection='geometry'),
      generate(height=10, width=10, shape='ring',
               badges=[(1, 4, 4, 2), (1, 8, 2, 3), (5, 4, 1, 3), (7, 8, 3, 6),
                       (8, 1, 6, 9)],
               path=_cells([(1, [2, 6]), (2, [2, 6]), (3, [3, 6, 7, 8, 9]),
                            (4, [2, 9]), (5, [1, 6, 7, 8]), (6, [2, 6]),
                            (7, [3, 6]), (8, [3, 4, 5, 6])]),
               selected=(0, 1)),
      generate(height=10, width=10, shape='ring',
               badges=[(1, 4, 1, 3), (1, 8, 6, 1), (5, 2, 2, 4), (6, 6, 3, 9),
                       (9, 2, 7, 2)],
               path=_cells([(3, [0, 1, 2, 3, 4, 8]), (4, [0, 4, 8]), (5, [0, 4, 8]),
                            (6, [0, 4, 9]), (7, [1, 2, 4, 9]), (8, [5, 6, 9]),
                            (9, [7, 8])]),
               selected=(1, 4), selection='eligibility'),
  ]
  return {'train': train, 'test': test}
