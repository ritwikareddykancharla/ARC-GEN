# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ARC task dd6b8c4b: the 3x3 tank collects the 9s it can reach.

Rule: the scene is open ground (7) with walls (6), scattered 9s and one 3x3
tank, which is a ring of 3s around a single 2. Run a 4-connected breadth-first
search from all nine tank cells through every cell that is not a wall. 9s are
passable, so a 9 in a doorway does not block the search. Sort the reachable 9s
by path length and take at most nine of them. Erase each taken 9 to 7. Then
paint that many tank cells 9, in reading order from the tank's top-left corner.
The centre 2 counts as the fifth of those cells.

Scope: random grids are 9x9 to 16x16 by default and need not be square.
Explicit random sizes from 7 to 30 per side are accepted. Explicit scenes accept
any side up to 30 that holds the 3x3 tank. All canonical grids are 11x11, so
other sizes are synthetic extensions. There are three layouts.
  open:   no walls, so every 9 is reachable (like train pair 3).
  framed: a 6-ring at Chebyshev distance 2 around the tank. It has either
          single-cell gaps on one to four sides (like train 1 and both tests)
          or one fully open side, optionally with a corridor of wall arms
          (like train 2). Gaps go only on sides whose outward cell is on the
          grid. Corner arms, rectangle rooms with optional doors, and free
          wall segments create 9s that are unreachable or reachable only by a
          detour. These act as distractors.
  walled: rooms and segments only, with no frame. This is a synthetic
          extension.
The 9s are placed constructively from the BFS distance map of the built walls.
In overflow scenes, exactly nine reachable 9s lie at distance <= D and every
other reachable 9 lies beyond D. The cut-off therefore never depends on
tie-breaking. Many framed overflow scenes are steered so that the path-length
choice differs from a straight-line (Manhattan-to-box) choice, as in train
pair 2. Some walled scenes are steered so that a 9 sits on a chokepoint (frame
gap, room door or one-cell corridor) with a taken 9 behind it, as in test 2.
This contradicts the rival reading that 9s block the search. The colours
7/6/9/3/2 and the capacity of nine are fixed, as in the task. The reference
prose says that test 1 collects five 9s. The canonical output collects six,
because (2,0) is reachable through (9,8) and row 10. This module follows the
canonical fixture.
"""

import random
from collections import deque

import common

BG, WALL, ITEM, RING, CORE = 7, 6, 9, 3, 2
CAPACITY = 9
MAX_SIDE = 30
MIN_SAMPLED_SIDE = 7
ATTEMPTS = 1500
COUNT_ABORT = 300
LAYOUTS = ('open', 'framed', 'walled')
STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _is_int(value):
  return isinstance(value, int) and not isinstance(value, bool)


def _tank_cells(tank):
  cy, cx = tank
  return [(r, c) for r in range(cy - 1, cy + 2) for c in range(cx - 1, cx + 2)]


def _box_manhattan(tank, cell):
  """Returns the Manhattan distance from a cell to the 3x3 tank box.

  Walls are ignored.
  """
  cy, cx = tank
  r, c = cell
  return max(0, abs(r - cy) - 1) + max(0, abs(c - cx) - 1)


def _distances(height, width, tank, walls):
  wall = set(walls)
  dist = {}
  queue = deque()
  for cell in _tank_cells(tank):
    dist[cell] = 0
    queue.append(cell)
  while queue:
    r, c = queue.popleft()
    for dr, dc in STEPS:
      nr, nc = r + dr, c + dc
      if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in dist:
        if (nr, nc) not in wall:
          dist[(nr, nc)] = dist[(r, c)] + 1
          queue.append((nr, nc))
  return dist


def _rival_reach(height, width, tank, walls, nines):
  """Returns the cells reached if 9s can be collected but not walked through."""
  wall = set(walls)
  item = set(nines)
  seen = set(_tank_cells(tank))
  queue = deque(_tank_cells(tank))
  while queue:
    r, c = queue.popleft()
    for dr, dc in STEPS:
      nr, nc = r + dr, c + dc
      cell = (nr, nc)
      if not (0 <= nr < height and 0 <= nc < width):
        continue
      if cell in seen or cell in wall:
        continue
      seen.add(cell)
      if cell not in item:
        queue.append(cell)
  return seen


def _collect(height, width, tank, walls, nines):
  """Returns the taken 9s plus diagnostic facts about the scene."""
  dist = _distances(height, width, tank, walls)
  reached = sorted((dist[p], p) for p in nines if p in dist)
  tie = (len(reached) > CAPACITY and
         reached[CAPACITY - 1][0] == reached[CAPACITY][0])
  taken = [p for _, p in reached[:CAPACITY]]
  left = [p for _, p in reached[CAPACITY:]]
  detour = False
  if left:
    worst_taken = max(_box_manhattan(tank, p) for p in taken)
    best_left = min(_box_manhattan(tank, p) for p in left)
    detour = worst_taken > best_left
  rival = _rival_reach(height, width, tank, walls, nines)
  choke = any(p not in rival for p in taken)
  return {'taken': taken, 'tie': tie, 'reached': len(reached),
          'unreached': len(nines) - len(reached), 'detour': detour,
          'chokepoint': choke}


def _render(height, width, tank, walls, nines):
  grid = common.grid(width, height, BG)
  for r, c in walls:
    grid[r][c] = WALL
  for r, c in nines:
    grid[r][c] = ITEM
  for r, c in _tank_cells(tank):
    grid[r][c] = RING
  grid[tank[0]][tank[1]] = CORE
  return grid


def _frame(tank):
  """Returns the 16 ring cells and, per side, (cells, outward step, corners)."""
  cy, cx = tank
  ring = set()
  for r in range(cy - 2, cy + 3):
    for c in range(cx - 2, cx + 3):
      if max(abs(r - cy), abs(c - cx)) == 2:
        ring.add((r, c))
  sides = [
      ([(cy - 2, cx + d) for d in (-1, 0, 1)], (-1, 0),
       [(cy - 2, cx - 2), (cy - 2, cx + 2)]),
      ([(cy + 2, cx + d) for d in (-1, 0, 1)], (1, 0),
       [(cy + 2, cx - 2), (cy + 2, cx + 2)]),
      ([(cy + d, cx - 2) for d in (-1, 0, 1)], (0, -1),
       [(cy - 2, cx - 2), (cy + 2, cx - 2)]),
      ([(cy + d, cx + 2) for d in (-1, 0, 1)], (0, 1),
       [(cy - 2, cx + 2), (cy + 2, cx + 2)]),
  ]
  return ring, sides


def _room_to_edge(height, width, cell, step):
  r, c = cell
  dr, dc = step
  if dr > 0:
    return height - 1 - r
  if dr < 0:
    return r
  if dc > 0:
    return width - 1 - c
  return c


def _arm(walls, forbidden, start, step, length):
  """Adds a straight wall arm beyond start; it stops at a protected cell."""
  r, c = start
  for k in range(1, length + 1):
    cell = (r + k * step[0], c + k * step[1])
    if cell in forbidden:
      break
    walls.add(cell)


def _build_frame(height, width, tank, walls):
  """Adds a gapped 6-frame and its arms. Returns (ring, forbidden, gaps)."""
  cy, cx = tank
  ring, sides = _frame(tank)
  valid = []
  for s, (cells, (dr, dc), _) in enumerate(sides):
    r, c = cells[1]
    if 0 <= r + dr < height and 0 <= c + dc < width:
      valid.append(s)
  if not valid:
    valid = list(range(4))
  gaps = set()
  open_side = None
  if random.random() < 0.25:
    open_side = random.choice(valid)
    gaps.update(sides[open_side][0])
  else:
    for s in random.sample(valid, random.randint(1, len(valid))):
      gaps.add(sides[s][0][random.choice((0, 1, 1, 2))])
  walls.update(ring - gaps)
  forbidden = set(_tank_cells(tank)) | gaps
  for cells, (dr, dc), _ in sides:
    for r, c in cells:
      if (r, c) in gaps:
        nr, nc = r + dr, c + dc
        if 0 <= nr < height and 0 <= nc < width:
          forbidden.add((nr, nc))
  if open_side is not None:
    _, step, corners = sides[open_side]
    room = min(_room_to_edge(height, width, k, step) for k in corners)
    length = random.randint(0, max(0, room - 1))
    for corner in corners:
      _arm(walls, forbidden, corner, step, length)
  corner_steps = [
      ((cy - 2, cx - 2), ((-1, 0), (0, -1))),
      ((cy - 2, cx + 2), ((-1, 0), (0, 1))),
      ((cy + 2, cx - 2), ((1, 0), (0, -1))),
      ((cy + 2, cx + 2), ((1, 0), (0, 1))),
  ]
  for corner, steps in corner_steps:
    if random.random() < 0.25:
      step = random.choice(steps)
      room = _room_to_edge(height, width, corner, step)
      if room > 0:
        _arm(walls, forbidden, corner, step, random.randint(1, room))
  return ring, forbidden, gaps


def _add_rooms(height, width, walls, forbidden):
  """Adds rectangle outlines with up to two door cells each; returns doors."""
  area = height * width
  span_r = max(2, (3 * height) // 4)
  span_c = max(2, (3 * width) // 4)
  all_doors = []
  for _ in range(random.randint(0, 1 + area // 100)):
    top = random.randint(0, height - 3)
    bottom = random.randint(top + 2, min(height - 1, top + span_r))
    left = random.randint(0, width - 3)
    right = random.randint(left + 2, min(width - 1, left + span_c))
    perim = []
    for r in range(top, bottom + 1):
      for c in range(left, right + 1):
        if r in (top, bottom) or c in (left, right):
          perim.append((r, c))
    sides_only = [(r, c) for r, c in perim
                  if not (r in (top, bottom) and c in (left, right))]
    doors = set()
    if sides_only:
      doors = set(random.sample(sides_only,
                                min(len(sides_only), random.randint(0, 2))))
    for cell in perim:
      if cell not in doors and cell not in forbidden:
        walls.add(cell)
    all_doors.extend(sorted(doors))
  return all_doors


def _add_segments(height, width, walls, forbidden):
  """Adds straight horizontal or vertical wall segments."""
  area = height * width
  for _ in range(random.randint(1, 2 + area // 40)):
    if random.random() < 0.5:
      length = random.randint(2, width)
      r = random.randrange(height)
      c0 = random.randint(0, width - length)
      cells = [(r, c0 + i) for i in range(length)]
    else:
      length = random.randint(2, height)
      c = random.randrange(width)
      r0 = random.randint(0, height - length)
      cells = [(r0 + i, c) for i in range(length)]
    for cell in cells:
      if cell not in forbidden:
        walls.add(cell)


def _side_bounds(fixed, other):
  if fixed is not None:
    return fixed, fixed
  lo = 9
  if other is not None:
    lo = min(MAX_SIDE, max(9, other + 3))
  return lo, max(lo, 16)


def _side_choice(fixed, other):
  lo, hi = _side_bounds(fixed, other)
  return random.randint(lo, hi)


def _choke_pair(height, width, tank, walls, dist, gaps, doors):
  """Finds a reachable chokepoint cell and a reachable cell behind it."""
  tank_set = set(_tank_cells(tank))
  wall = set(walls)

  def blocked(r, c):
    return not (0 <= r < height and 0 <= c < width) or (r, c) in wall

  cands = set(gaps) | set(doors)
  for r, c in dist:
    if (r, c) in tank_set:
      continue
    if ((blocked(r - 1, c) and blocked(r + 1, c)) or
        (blocked(r, c - 1) and blocked(r, c + 1))):
      cands.add((r, c))
  cands = sorted(p for p in cands if p in dist and p not in tank_set)
  random.shuffle(cands)
  for cell in cands[:12]:
    sub = _distances(height, width, tank, wall | {cell})
    behind = sorted((p for p in dist
                     if p not in sub and p != cell and p not in tank_set),
                    key=lambda p: (dist[p], p))
    if behind:
      return cell, random.choice(behind[:max(1, (len(behind) + 1) // 2)])
  return None


def _place_nines(dist, reach, unreach, forced, want_over, count, area):
  """Chooses the 9 cells so that the overflow status is exact and never tied.

  Returns (cells, blocked_by_count). cells is None on failure. The flag is
  True when only the requested num_nines made this particular scene fail.
  """
  budget = min(max(18, area // 10), 40)
  forced_set = set(forced)
  if want_over:
    cands = []
    for d in sorted(set(dist[p] for p in reach)):
      near_n = sum(1 for p in reach if dist[p] <= d)
      forced_near = sum(1 for p in forced if dist[p] <= d)
      if (near_n >= CAPACITY and len(reach) - near_n >= 1 and
          forced_near <= CAPACITY):
        cands.append(d)
    if not cands:
      return None, False
    if forced:
      need = max(dist[p] for p in forced)
      pref = [d for d in cands if d >= need]
      if pref:
        cands = pref
    cut = random.choice(cands)
    near = [p for p in reach if dist[p] <= cut]
    far = [p for p in reach if dist[p] > cut]
    f_near = [p for p in forced if dist[p] <= cut]
    f_far = [p for p in forced if dist[p] > cut]
    lo = max(1, len(f_far))
    hi = len(far)
    base_ok = lo <= hi
    if count is not None:
      lo = max(lo, count - CAPACITY - len(unreach))
      hi = min(hi, count - CAPACITY)
    else:
      hi = min(hi, max(lo, budget - CAPACITY))
    if lo > hi:
      return None, base_ok and count is not None
    n_far = random.randint(lo, hi)
    if count is not None:
      n_un = count - CAPACITY - n_far
    else:
      n_un = random.randint(
          0, min(len(unreach), max(0, budget - CAPACITY - n_far)))
    chosen = f_near + random.sample(
        [p for p in near if p not in forced_set], CAPACITY - len(f_near))
    chosen += f_far + random.sample(
        [p for p in far if p not in forced_set], n_far - len(f_far))
  else:
    lo = max(1, len(forced))
    hi = min(CAPACITY, len(reach))
    base_ok = lo <= hi
    if count is not None:
      lo = max(lo, count - len(unreach))
      hi = min(hi, count)
    if lo > hi:
      return None, base_ok and count is not None
    n_r = random.randint(lo, hi)
    if count is not None:
      n_un = count - n_r
    else:
      n_un = random.randint(0, min(len(unreach), max(0, budget - n_r)))
    chosen = list(forced) + random.sample(
        [p for p in reach if p not in forced_set], n_r - len(forced))
  chosen += random.sample(unreach, n_un)
  return chosen, False


def _sample_scene(height, width, tank, layout, overflow, num_nines,
                  chokepoint):
  count_blocked = 0
  for attempt in range(ATTEMPTS):
    relax = attempt >= ATTEMPTS // 2
    h = _side_choice(height, None if tank is None else tank[0])
    w = _side_choice(width, None if tank is None else tank[1])
    lay = layout
    if lay is None:
      if chokepoint:
        lay = random.choices(('framed', 'walled'), weights=(7, 1))[0]
      else:
        lay = random.choices(LAYOUTS, weights=(2, 7, 1))[0]
    if tank is None:
      margin = 2 if lay == 'framed' else 1
      cy = random.randint(margin, h - 1 - margin)
      cx = random.randint(margin, w - 1 - margin)
    else:
      cy, cx = tank
      if not (1 <= cy <= h - 2 and 1 <= cx <= w - 2):
        continue
      if lay == 'framed' and not (2 <= cy <= h - 3 and 2 <= cx <= w - 3):
        if layout == 'framed':
          continue
        if chokepoint or random.random() < 0.3:
          lay = 'walled'
        else:
          lay = 'open'
    t = (cy, cx)
    tank_set = set(_tank_cells(t))
    walls = set()
    gaps = set()
    doors = []
    if lay == 'framed':
      _, forbidden, gaps = _build_frame(h, w, t, walls)
      doors = _add_rooms(h, w, walls, forbidden)
      _add_segments(h, w, walls, forbidden)
    elif lay == 'walled':
      doors = _add_rooms(h, w, walls, tank_set)
      _add_segments(h, w, walls, tank_set)
    if len(walls) > 0.5 * h * w:
      continue
    dist = _distances(h, w, t, walls)
    reach = sorted(p for p in dist if p not in tank_set)
    if not reach:
      continue
    unreach = [(r, c) for r in range(h) for c in range(w)
               if (r, c) not in walls and (r, c) not in tank_set
               and (r, c) not in dist]
    want_choke = chokepoint
    if (want_choke is None and lay != 'open' and not relax and
        random.random() < 0.3):
      want_choke = True
    forced = []
    if want_choke:
      pair = _choke_pair(h, w, t, walls, dist, gaps, doors)
      if pair is None:
        continue
      forced = list(pair)
    want_over = overflow
    if want_over is None:
      if num_nines is not None and num_nines <= CAPACITY:
        want_over = False
      elif num_nines is not None and not unreach:
        want_over = True
      else:
        want_over = random.random() < (0.5 if relax else 0.35)
    nines, by_count = _place_nines(dist, reach, unreach, forced, want_over,
                                   num_nines, h * w)
    if nines is None:
      if by_count:
        count_blocked += 1
        if count_blocked >= COUNT_ABORT:
          raise ValueError('num_nines cannot be placed under these controls')
      continue
    walls_list = sorted(walls)
    info = _collect(h, w, t, walls_list, nines)
    if info['tie'] or info['reached'] == 0:
      continue
    over = info['reached'] > CAPACITY
    if over != want_over:
      continue
    if want_choke and not info['chokepoint']:
      continue
    if chokepoint is False and info['chokepoint']:
      continue
    if not relax and lay != 'open':
      if over and not info['detour'] and random.random() < 0.6:
        continue
      if not over and info['unreached'] == 0 and random.random() < 0.7:
        continue
    return h, w, t, walls_list, nines
  raise ValueError('could not sample a valid scene for these controls')


def _check_cell(cell, name):
  if len(cell) != 2 or not all(_is_int(v) for v in cell):
    raise ValueError(name + ' cells must be (row, col) integer pairs')


def _as_cell(value, name):
  """Converts a (row, col) pair to a tuple; rejects malformed input."""
  try:
    cell = tuple(value)
  except TypeError:
    raise ValueError(name + ' cells must be (row, col) integer pairs')
  _check_cell(cell, name)
  return cell


def _as_cells(values, name):
  try:
    items = list(values)
  except TypeError:
    raise ValueError(name + ' must be a list of (row, col) pairs')
  return [_as_cell(v, name) for v in items]


def _check_scene(height, width, tank, walls, nines):
  if not (_is_int(height) and _is_int(width)):
    raise ValueError('height and width must be integers')
  if not (1 <= height <= MAX_SIDE and 1 <= width <= MAX_SIDE):
    raise ValueError('grid sides must be 1..30')
  _check_cell(tank, 'tank')
  cy, cx = tank
  if not (1 <= cy <= height - 2 and 1 <= cx <= width - 2):
    raise ValueError('the 3x3 tank must lie inside the grid')
  tank_set = set(_tank_cells(tank))
  for name, cells in (('walls', walls), ('nines', nines)):
    if len(set(cells)) != len(cells):
      raise ValueError(name + ' contains duplicate cells')
    for r, c in cells:
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError(name + ' cell out of bounds')
      if (r, c) in tank_set:
        raise ValueError(name + ' cell overlaps the tank')
  if set(walls) & set(nines):
    raise ValueError('walls and nines overlap')


def generate(height=None, width=None, tank=None, walls=None, nines=None,
             layout=None, overflow=None, num_nines=None, chokepoint=None):
  """Builds one input/output pair.

  Args:
    height: grid height (rows). For random scenes it must be an int in 7..30,
      and it fixes the sampled height. It is required for explicit scenes.
    width: grid width (columns). For random scenes it must be an int in 7..30,
      and it fixes the sampled width. It is required for explicit scenes.
    tank: (row, col) of the tank's central 2 cell. The 3x3 tank must lie
      inside the grid. For random scenes it fixes the tank position. With
      layout='framed' the 5x5 frame must fit as well. With layout=None, a
      position where the frame does not fit gives an open or walled scene.
    walls: list of (row, col) cells coloured 6. Giving it makes the scene
      explicit, and height, width, tank and nines are then required. Walls
      must avoid the tank.
    nines: list of (row, col) cells coloured 9. Allowed only with explicit
      walls. They must avoid the walls and the tank. At least one must be
      reachable, and the ninth and tenth nearest must not tie.
    layout: random scenes only. One of 'open' (no walls), 'framed' (gapped
      6-frame plus arms, rooms and segments) or 'walled' (rooms and segments
      without a frame). None picks one at random, weighted toward 'framed'.
    overflow: random scenes only; None or a bool. True requires more than
      nine reachable 9s. False requires at most nine. None leaves it random.
    num_nines: random scenes only. The exact number (int) of 9s placed. With
      overflow=True it must exceed nine. Counts that prove unplaceable raise
      ValueError after a bounded number of tries.
    chokepoint: random scenes only; None or a bool. True requires a taken 9
      that can only be reached by walking through another 9 (a 9 on a gap,
      door or corridor cell). False forbids that. None steers about a third
      of non-open scenes toward it. True needs walls, so it cannot be combined
      with layout='open'.
  """
  if walls is None:
    if nines is not None:
      raise ValueError('nines requires an explicit walls list (use [] for none)')
    if layout is not None and layout not in LAYOUTS:
      raise ValueError('layout must be open, framed or walled')
    for name, flag in (('overflow', overflow), ('chokepoint', chokepoint)):
      if flag is not None and not isinstance(flag, bool):
        raise ValueError(name + ' must be None, True or False')
    if chokepoint is True and layout == 'open':
      raise ValueError('chokepoint steering needs walls; use framed or walled')
    for side in (height, width):
      if side is not None and (not _is_int(side) or
                               not MIN_SAMPLED_SIDE <= side <= MAX_SIDE):
        raise ValueError('random scenes need integer sides in 7..30')
    if tank is not None:
      tank = _as_cell(tank, 'tank')
      need = 2 if layout == 'framed' else 1
      for coord, side in ((tank[0], height), (tank[1], width)):
        limit = (MAX_SIDE if side is None else side) - 1 - need
        if coord < need or coord > limit:
          raise ValueError('tank position incompatible with grid/frame')
    if num_nines is not None:
      if not _is_int(num_nines) or num_nines < 1:
        raise ValueError('num_nines must be a positive integer')
      if overflow is True and num_nines <= CAPACITY:
        raise ValueError('overflow=True needs num_nines > 9')
      if layout == 'open' and overflow is False and num_nines > CAPACITY:
        raise ValueError('every 9 is reachable in an open scene')
      if chokepoint is True and num_nines < 2:
        raise ValueError('chokepoint=True needs at least two 9s')
      hmax = _side_bounds(height, None if tank is None else tank[0])[1]
      wmax = _side_bounds(width, None if tank is None else tank[1])[1]
      room = hmax * wmax - 9 - (12 if layout == 'framed' else 0)
      if num_nines > room:
        raise ValueError('num_nines cannot fit in the allowed grid sizes')
    height, width, tank, walls, nines = _sample_scene(
        height, width, tank, layout, overflow, num_nines, chokepoint)
  else:
    if (layout is not None or overflow is not None or num_nines is not None
        or chokepoint is not None):
      raise ValueError(
          'layout/overflow/num_nines/chokepoint only apply to random scenes')
    if height is None or width is None or tank is None or nines is None:
      raise ValueError('explicit scenes need height, width, tank and nines')
  walls = _as_cells(walls, 'walls')
  nines = _as_cells(nines, 'nines')
  tank = _as_cell(tank, 'tank')
  _check_scene(height, width, tank, walls, nines)
  info = _collect(height, width, tank, walls, nines)
  if info['tie']:
    raise ValueError('ambiguous cut-off: tied path lengths at the ninth 9')
  if info['reached'] == 0:
    raise ValueError('no reachable 9: the pair would be an identity')
  grid = _render(height, width, tank, walls, nines)
  output = [row[:] for row in grid]
  for r, c in info['taken']:
    output[r][c] = BG
  for r, c in _tank_cells(tank)[:len(info['taken'])]:
    output[r][c] = ITEM
  return {'input': grid, 'output': output}


def _cells(spec):
  return [(r, c) for r in sorted(spec) for c in spec[r]]


def validate():
  """Reconstructs the canonical ARC pairs from explicit latent scenes."""
  r11 = list(range(11))
  train = [
      generate(11, 11, (5, 5),
               _cells({1: [1, 2, 3, 4, 5, 6, 7], 2: [1, 7],
                       3: [1, 2, 3, 4, 5, 6, 7], 4: [3, 7], 5: [3, 7],
                       6: [3, 7], 7: [3, 4, 6, 7, 8, 9], 8: [3, 9],
                       9: [3, 4, 5, 6, 7, 8, 9]}),
               _cells({1: [8, 9], 2: [2, 3, 8, 9], 5: [9], 6: [1],
                       7: [0, 1], 8: [7, 8]})),
      generate(11, 11, (5, 5),
               _cells({3: [3, 4, 5, 6, 7, 8, 9, 10], 4: [3, 7], 5: [3, 7],
                       6: [3, 7], 7: [3, 7], 8: [3, 7], 9: [3, 7]}),
               _cells({0: [6, 7, 8], 1: [6, 7, 10], 2: [10], 3: [0],
                       4: [8], 5: [2], 6: [9], 8: [1, 5], 9: [2, 5]})),
      generate(11, 11, (5, 5), [],
               _cells({1: [9], 2: [2, 10], 9: [8]})),
  ]
  test = [
      generate(11, 11, (5, 5),
               _cells({0: [0, 1, 9, 10], 1: r11, 2: [1, 9],
                       3: [1, 3, 4, 6, 7, 9], 4: [1, 3, 7, 9], 5: [1, 9],
                       6: [1, 3, 7, 9], 7: [1, 3, 4, 6, 7, 9], 8: [1, 9],
                       9: [1, 2, 3, 4, 5, 6, 7, 9, 10], 10: [9, 10]}),
               _cells({0: [2, 8], 2: [0, 2, 8], 3: [10], 5: [10], 7: [10],
                       8: [2, 5, 8]})),
      generate(11, 11, (5, 5),
               _cells({0: [3, 7], 1: [3, 4, 5, 6, 7],
                       3: [0, 1, 3, 4, 6, 7, 8, 9], 4: [3, 7],
                       5: [1, 2, 3, 7, 9, 10], 6: [3, 7],
                       7: [0, 1, 3, 4, 5, 7, 8, 9], 8: [3, 7],
                       9: [1, 2, 3, 5, 6, 7, 9, 10], 10: [3, 7]}),
               _cells({0: [4, 6], 1: [2, 10], 3: [2, 10], 7: [2, 10],
                       10: [0, 1, 2, 4, 6, 8, 9, 10]})),
  ]
  return {'train': train, 'test': test}
