# Copyright 2026 Ritwika Kancharla
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0; you may not use this file
# except in compliance with the License. You may obtain a copy of the License
# at http://www.apache.org/licenses/LICENSE-2.0

"""ARC task 800d221b: recolour corridor branches with their patch's majority.

Rule: the input has a background, one line colour and several two-colour
textured patches. The patches lie in grid corners or against grid edges, and
each is framed by the line colour. One-cell-wide corridors run from the frames
to a solid 3x3 hub of line colour. Removing the hub splits the line network
into 4-connected branches, one per patch (the frame plus its corridors). In
the output:
  * every branch cell takes the strict-majority colour of its patch;
  * the 8 ring cells of the hub keep the line colour;
  * the hub centre takes the colour that now covers the most branch cells,
    counted in cells, not in branches or patch pixels.

Scope: random grids are 12..30 cells per side by default. Explicit random
sizes of 10..30 are accepted; sides of 10..11 give cramped layouts. Each scene
has 2..6 patches in distinct corner or edge slots. The allowed patch count
grows with the shorter side: 3 below 14, 4 below 18, 5 below 24, 6 from 24 up.
Most patches are 2..H/3 by 2..W/3. About one in five is elongated, up to half
the grid along one axis. Every patch has a strict majority and uses the same
two patch colours.

Each patch gets one to three corridors. Corridors are turn-penalised shortest
paths around obstacles, so they have long straight runs. Corridors of
different patches never touch 4-adjacently. They may touch diagonally at a
hub corner, where one attaches on the top/bottom side and another on the
left/right side, as in the test fixture. This forces 4-connected branch
segmentation.

All four colours are random and distinct. Both patch colours always win at
least one branch, and the hub centre never ties. In most scenes the generator
also asks for a centre winner that defeats a shortcut. The shortcut is either
the most frequent patch-pixel colour, or any one defined heuristic: pixel
majority, the colour owning the most branches, or the majority of the largest
patch. This request is dropped after half of the bounded attempts. Sizes above
the fixture sizes, and six-patch scenes, are synthetic extensions.

The original fixtures are rebuilt from explicit latent arguments: patch
positions and textures, plus corridor polylines. Explicit scenes are checked
for geometric and colour-frequency validity before they are returned.
"""

import heapq
import random
from collections import Counter

import common

_SLOTS = ('TL', 'TR', 'BL', 'BR', 'T', 'B', 'L', 'R')
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
_THRESHOLD = {2: 10, 3: 10, 4: 14, 5: 18, 6: 24}
_ATTEMPTS = 400


def _is_int(value):
  return isinstance(value, int) and not isinstance(value, bool)


def _max_patches(height, width):
  """Largest patch count supported by a grid of the given size."""
  m = min(height, width)
  if m < 14:
    return 3
  if m < 18:
    return 4
  if m < 24:
    return 5
  return 6


def _polyline(points):
  """Rasterises axis-aligned waypoints into a list of cells."""
  if not isinstance(points, (list, tuple)) or any(
      not isinstance(p, (list, tuple)) or len(p) != 2 or
      not all(_is_int(v) for v in p) for p in points):
    raise ValueError('waypoints must be pairs of integer coordinates')
  points = [tuple(p) for p in points]
  if not points:
    raise ValueError('a corridor needs at least one point')
  r, c = points[0]
  cells = [(r, c)]
  for nr, nc in points[1:]:
    if nr != r and nc != c:
      raise ValueError('polyline segments must be axis aligned')
    dr = (nr > r) - (nr < r)
    dc = (nc > c) - (nc < c)
    while (r, c) != (nr, nc):
      r += dr
      c += dc
      cells.append((r, c))
  return cells


def _frame(top, left, h, w, height, width):
  """Returns the ring of cells around a patch, clipped to the grid."""
  cells = []
  for r in range(top - 1, top + h + 1):
    for c in range(left - 1, left + w + 1):
      if not (0 <= r < height and 0 <= c < width):
        continue
      if top <= r < top + h and left <= c < left + w:
        continue
      cells.append((r, c))
  return cells


def _box(top, left, h, w, height, width):
  """Bounding box (r0, c0, r1, c1) of a patch together with its frame."""
  return (max(0, top - 1), max(0, left - 1), min(height - 1, top + h),
          min(width - 1, left + w))


def _gap(a, b):
  return max(b[0] - a[2], a[0] - b[2], b[1] - a[3], a[1] - b[3])


def _dist(r, c, box):
  dr = max(box[0] - r, 0, r - box[2])
  dc = max(box[1] - c, 0, c - box[3])
  return max(dr, dc)


def _render(width, height, background, line, hub, patches, paths):
  """Draws a scene from latent parameters and derives its answer.

  Raises ValueError on geometric conflicts. These are out-of-bounds parts,
  overlapping patches, corridors through patch interiors or other branches,
  and majority ties inside a patch.
  """
  grid = [list(row) for row in common.grid(width, height, background)]
  if len(hub) != 2 or not all(_is_int(v) for v in hub):
    raise ValueError('hub must be a pair of integers')
  hr, hc = hub[0], hub[1]
  if not (0 <= hr <= height - 3 and 0 <= hc <= width - 3):
    raise ValueError('hub lies outside the grid')
  hub_cells = set((hr + i, hc + j) for i in range(3) for j in range(3))
  interior = {}
  shapes, majors, sizes = [], [], []
  pix = Counter()
  if not isinstance(patches, (list, tuple)) or any(
      not isinstance(p, (list, tuple)) or len(p) != 3 for p in patches):
    raise ValueError('patches must contain (top, left, rows) entries')
  if not patches:
    raise ValueError('a scene needs patches')
  for i, (top, left, rows) in enumerate(patches):
    if not (_is_int(top) and _is_int(left)):
      raise ValueError('patch positions must be integers')
    if not isinstance(rows, (list, tuple)):
      raise ValueError('patch texture must be a sequence of rows')
    parsed = []
    for row in rows:
      if isinstance(row, str):
        if not row or any(v not in '0123456789' for v in row):
          raise ValueError('string texture rows must contain digits only')
        parsed.append([int(v) for v in row])
      elif isinstance(row, (list, tuple)) and all(_is_int(v) for v in row):
        parsed.append(list(row))
      else:
        raise ValueError('texture cells must be integers, not coerced values')
    rows = parsed
    if not rows or not rows[0] or any(len(row) != len(rows[0])
                                      for row in rows):
      raise ValueError('patch textures must be non-empty rectangles')
    h, w = len(rows), len(rows[0])
    if top < 0 or left < 0 or top + h > height or left + w > width:
      raise ValueError('patch lies outside the grid')
    counts = Counter()
    for dr, row in enumerate(rows):
      for dc, v in enumerate(row):
        if not 0 <= v <= 9 or v in (background, line):
          raise ValueError('patch colours must be 0..9, not bg or line')
        cell = (top + dr, left + dc)
        if cell in interior or cell in hub_cells:
          raise ValueError('patches overlap each other or the hub')
        interior[cell] = i
        grid[cell[0]][cell[1]] = v
        counts[v] += 1
    ranked = counts.most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
      raise ValueError('every patch needs a strict majority colour')
    majors.append(ranked[0][0])
    sizes.append(h * w)
    pix.update(counts)
    shapes.append((top, left, h, w))
  group = {}

  def claim(cell, i, in_frame):
    r, c = cell
    if not (0 <= r < height and 0 <= c < width):
      raise ValueError('corridor leaves the grid')
    if cell in interior:
      raise ValueError('line cell inside a patch')
    if cell in hub_cells:
      if in_frame:
        raise ValueError('frame overlaps the hub')
      return
    if group.get(cell, i) != i:
      raise ValueError('branches of different patches overlap')
    group[cell] = i
    grid[r][c] = line

  for i, (top, left, h, w) in enumerate(shapes):
    for cell in _frame(top, left, h, w, height, width):
      claim(cell, i, True)
  if not isinstance(paths, (list, tuple)) or any(
      not isinstance(p, (list, tuple)) or len(p) != 2 for p in paths):
    raise ValueError('paths must contain (patch_index, waypoints) entries')
  for i, points in paths:
    if not (_is_int(i) and 0 <= i < len(patches)):
      raise ValueError('corridor refers to a missing patch')
    for cell in _polyline(points):
      claim(cell, i, False)
  for r, c in hub_cells:
    grid[r][c] = line
  if not group:
    raise ValueError('a scene needs at least one branch')
  output = [row[:] for row in grid]
  tally = Counter()
  for (r, c), i in group.items():
    output[r][c] = majors[i]
    tally[majors[i]] += 1
  best = max(tally.values())
  output[hr + 1][hc + 1] = min(k for k, v in tally.items() if v == best)
  info = {'tally': tally, 'majors': majors, 'sizes': sizes, 'pix': pix,
          'group': group, 'interior': interior, 'hub_cells': hub_cells}
  return {'input': grid, 'output': output}, info


def _block(blocked, cells):
  """Blocks the 8-neighbourhood of a corridor, except at its hub end.

  The final (hub attachment) cell blocks only its 4-neighbourhood. A corridor
  of another patch may then attach on the perpendicular side of the same hub
  corner and touch it diagonally. Every other diagonal contact is still
  prevented by the 8-neighbourhood of the preceding corridor cell.
  """
  for r, c in cells[:-1]:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        blocked.add((r + dr, c + dc))
  r, c = cells[-1]
  blocked.add((r, c))
  for dr, dc in _DIRS:
    blocked.add((r + dr, c + dc))


def _corner_partner(cell, hub):
  """Attachment cell diagonally adjacent to `cell` across a hub corner."""
  hr, hc = hub
  pairs = (((hr - 1, hc), (hr, hc - 1)),
           ((hr - 1, hc + 2), (hr, hc + 3)),
           ((hr + 3, hc), (hr + 2, hc - 1)),
           ((hr + 3, hc + 2), (hr + 2, hc + 3)))
  for a, b in pairs:
    if cell == a:
      return b
    if cell == b:
      return a
  return None


def _dijkstra(starts, goal, free, turn_cost):
  """Cheapest path from any start to the goal set, penalising turns."""
  best, prev, heap = {}, {}, []
  tick = 0
  for cell in starts:
    cost = random.random() * 0.5
    best[(cell, -1)] = cost
    prev[(cell, -1)] = None
    heap.append((cost, tick, cell, -1))
    tick += 1
  heapq.heapify(heap)
  while heap:
    cost, _, cell, d = heapq.heappop(heap)
    if cost > best[(cell, d)]:
      continue
    if cell in goal:
      out = []
      key = (cell, d)
      while key is not None:
        out.append(key[0])
        key = prev[key]
      return out[::-1]
    for k, (dr, dc) in enumerate(_DIRS):
      nb = (cell[0] + dr, cell[1] + dc)
      if nb not in goal and nb not in free:
        continue
      step = 1.0 + random.random() * 0.1
      if 0 <= d != k:
        step += turn_cost
      key = (nb, k)
      if cost + step < best.get(key, 1e18):
        best[key] = cost + step
        prev[key] = (cell, d)
        heapq.heappush(heap, (cost + step, tick, nb, k))
        tick += 1
  return None


def _route(height, width, boxes, index, hub, blocked, turn_cost, prefer):
  """Corridor from patch `index`'s frame to a hub attachment cell."""
  hr, hc = hub

  def in_zone(r, c):
    return hr - 1 <= r <= hr + 3 and hc - 1 <= c <= hc + 3

  def clear(r, c, own):
    if not (0 <= r < height and 0 <= c < width) or (r, c) in blocked:
      return False
    for j, box in enumerate(boxes):
      d = _dist(r, c, box)
      if d < 2 and not (own and j == index and d == 1):
        return False
    return True

  r0, c0, r1, c1 = boxes[index]
  exits = [(r0 - 1, c) for c in range(c0, c1 + 1)]
  exits += [(r1 + 1, c) for c in range(c0, c1 + 1)]
  exits += [(r, c0 - 1) for r in range(r0, r1 + 1)]
  exits += [(r, c1 + 1) for r in range(r0, r1 + 1)]
  exits = [p for p in exits if not in_zone(*p) and clear(p[0], p[1], True)]
  targets = []
  for j in range(3):
    targets += [(hr - 1, hc + j), (hr + 3, hc + j), (hr + j, hc - 1),
                (hr + j, hc + 3)]
  targets = [p for p in targets if clear(p[0], p[1], False)]
  if not exits or not targets:
    return None
  free = set()
  for r in range(height):
    for c in range(width):
      if not in_zone(r, c) and clear(r, c, False):
        free.add((r, c))
  preferred = [p for p in targets if p in prefer]
  if preferred and random.random() < 0.6:
    chosen = set(preferred)
  else:
    chosen = set(random.sample(targets, random.randint(1, len(targets))))
  cells = _dijkstra(exits, chosen, free, turn_cost)
  if cells is None and len(chosen) < len(targets):
    cells = _dijkstra(exits, set(targets), free, turn_cost)
  return cells


def _sample_scene(width, height, background, line, num_patches):
  """Samples latent scene parameters, or returns None on a failed attempt."""
  lo = 12 if num_patches is None else max(12, _THRESHOLD[num_patches])
  height = height if height is not None else random.randint(lo, 30)
  width = width if width is not None else random.randint(lo, 30)
  if background is None:
    background = random.choice([c for c in range(10) if c != line])
  if line is None:
    line = random.choice([c for c in range(10) if c != background])
  pool = [c for c in range(10) if c not in (background, line)]
  ca, cb = random.sample(pool, 2)
  hr = random.randint(2, height - 5)
  hc = random.randint(2, width - 5)
  hub_box = (hr, hc, hr + 2, hc + 2)
  if num_patches is not None:
    count = num_patches
  else:
    count = random.randint(2, _max_patches(height, width))
  slots = random.sample(_SLOTS, count)
  majors = [ca, cb] + [random.choice((ca, cb)) for _ in range(count - 2)]
  random.shuffle(majors)
  patches, boxes, areas = [], [], []
  for slot, major in zip(slots, majors):
    placed = None
    for _ in range(12):
      if random.random() < 0.2:
        if random.random() < 0.5:
          hmax, wmax = height // 2, width // 5
        else:
          hmax, wmax = height // 5, width // 2
      else:
        hmax = random.choice((height // 4, height // 3))
        wmax = random.choice((width // 4, width // 3))
      h = random.randint(2, max(2, hmax))
      w = random.randint(2, max(2, wmax))
      if slot in ('TL', 'TR', 'T'):
        top = 0
      elif slot in ('BL', 'BR', 'B'):
        top = height - h
      else:
        top = random.randint(1, height - h - 1)
      if slot in ('TL', 'BL', 'L'):
        left = 0
      elif slot in ('TR', 'BR', 'R'):
        left = width - w
      else:
        left = random.randint(1, width - w - 1)
      box = _box(top, left, h, w, height, width)
      if _gap(box, hub_box) < 2:
        continue
      if any(_gap(box, other) < 2 for other in boxes):
        continue
      placed = (top, left, h, w, box)
      break
    if placed is None:
      return None
    top, left, h, w, box = placed
    minor = cb if major == ca else ca
    n = h * w
    rows = [[major] * w for _ in range(h)]
    for idx in random.sample(range(n), random.randint(1, (n - 1) // 2)):
      rows[idx // w][idx % w] = minor
    patches.append((top, left, rows))
    boxes.append(box)
    areas.append(n)
  turn_cost = random.uniform(0.2, 0.8)
  blocked = set()
  paths = []
  attach = []

  def run(i):
    prefer = set()
    for cell, owner in attach:
      if owner != i:
        mate = _corner_partner(cell, (hr, hc))
        if mate is not None:
          prefer.add(mate)
    cells = _route(height, width, boxes, i, (hr, hc), blocked, turn_cost,
                   prefer)
    if cells is not None:
      paths.append((i, cells))
      _block(blocked, cells)
      attach.append((cells[-1], i))
    return cells

  order = list(range(count))
  random.shuffle(order)
  for i in order:
    if run(i) is None:
      return None
  for i in order:
    extra = 0
    if random.random() < 0.35:
      extra = 1
      if areas[i] >= 6 and random.random() < 0.3:
        extra = 2
    for _ in range(extra):
      if run(i) is None:
        break
  return width, height, background, line, (hr, hc), patches, paths


def _solid_blocks(grid, colour):
  total = 0
  for r in range(len(grid) - 2):
    for c in range(len(grid[0]) - 2):
      if all(grid[r + i][c + j] == colour for i in range(3) for j in range(3)):
        total += 1
  return total


def _branches_ok(group, interior, hub_cells):
  """Each 4-connected branch belongs to one patch and touches only it.

  Every branch must also be 4-adjacent to the hub.
  """
  seen = set()
  owners = []
  for start in group:
    if start in seen:
      continue
    seen.add(start)
    stack = [start]
    ids, touched = set(), set()
    at_hub = False
    while stack:
      r, c = stack.pop()
      ids.add(group[(r, c)])
      for dr, dc in _DIRS:
        nb = (r + dr, c + dc)
        if nb in group:
          if nb not in seen:
            seen.add(nb)
            stack.append(nb)
        elif nb in interior:
          touched.add(interior[nb])
        elif nb in hub_cells:
          at_hub = True
    if len(ids) != 1 or touched != ids or not at_hub:
      return False
    owners.append(next(iter(ids)))
  return len(owners) == len(set(owners))


def _colours_ok(grid, background, line):
  """Background is the most frequent colour; line beats every patch colour."""
  counts = Counter(v for row in grid for v in row)
  n_line = counts[line]
  for colour, n in counts.items():
    if colour not in (background, line) and n >= n_line:
      return False
  return counts[background] > n_line


def _unique_top(counter):
  ranked = counter.most_common()
  if not ranked or (len(ranked) > 1 and ranked[0][1] == ranked[1][1]):
    return None
  return ranked[0][0]


def _defeats_shortcut(info, mode):
  """True if the cell-count winner differs from a defined simpler heuristic."""
  winner = _unique_top(info['tally'])
  pixel = _unique_top(info['pix'])
  if mode == 'pixel':
    return pixel is not None and pixel != winner
  majors, sizes = info['majors'], info['sizes']
  largest = [i for i, s in enumerate(sizes) if s == max(sizes)]
  shortcuts = (pixel, _unique_top(Counter(majors)),
               majors[largest[0]] if len(largest) == 1 else None)
  defined = [s for s in shortcuts if s is not None]
  return bool(defined) and any(s != winner for s in defined)


def _acceptable(pair, info, background, line, mode):
  grid = pair['input']
  if len(set(info['majors'])) < 2:
    return False
  values = sorted(info['tally'].values(), reverse=True)
  if len(values) < 2 or values[0] == values[1]:
    return False
  if not _colours_ok(grid, background, line):
    return False
  if _solid_blocks(grid, line) != 1:
    return False
  if not _branches_ok(info['group'], info['interior'], info['hub_cells']):
    return False
  if mode is not None and not _defeats_shortcut(info, mode):
    return False
  return True


def generate(width=None, height=None, background=None, line=None, hub=None,
             patches=None, paths=None, num_patches=None):
  """Returns an input/output pair for task 800d221b.

  Args:
    width: grid width (int). Random scenes default to 12..30 and accept
      10..30. Explicit scenes accept 1..30.
    height: grid height, with the same ranges as width.
    background: background colour 0..9 (random if None).
    line: line / corridor colour 0..9, distinct from background (random if
      None).
    hub: (row, col) of the top-left cell of the solid 3x3 hub.
    patches: list of (top, left, rows). Each rows entry is a list of digit
      strings or integer lists giving the patch texture. A line-colour frame
      is drawn around each patch and clipped to the grid.
    paths: list of (patch_index, waypoints). Each waypoints entry is a list of
      axis-aligned (row, col) points. The corridor belongs to that patch's
      branch, and any cells it draws inside the hub are absorbed by the hub.
    num_patches: number of patches for a random scene, 2..6. Counts of
      4, 5 and 6 need both sides to be at least 14, 18 and 24. Random if
      None.

  If hub, patches and paths are all given, the scene is rendered exactly.
  width, height, background and line are then required. The scene is
  rejected (ValueError) unless all of the following hold:
    * it is geometrically valid;
    * it has exactly one solid 3x3 line block;
    * every branch maps to exactly one patch and touches the hub;
    * the background outnumbers the line colour, which outnumbers every
      patch colour;
    * the hub centre does not tie.
  Giving only some of hub, patches and paths is rejected. Otherwise a fresh
  random scene is constructed, honouring any of width, height, background,
  line and num_patches that are given. If that is infeasible within the
  bounded attempts, a ValueError is raised.
  """
  explicit = [hub is not None, patches is not None, paths is not None]
  if any(explicit) and not all(explicit):
    raise ValueError('hub, patches and paths must be given together')
  for value in (background, line):
    if value is not None and not (_is_int(value) and 0 <= value <= 9):
      raise ValueError('colours must be integers in 0..9')
  if background is not None and background == line:
    raise ValueError('background and line colours must differ')
  for value in (width, height, num_patches):
    if value is not None and not _is_int(value):
      raise ValueError('sizes and counts must be integers')
  if all(explicit):
    if None in (width, height, background, line):
      raise ValueError('explicit scenes need width, height, background, line')
    if not (1 <= width <= 30 and 1 <= height <= 30):
      raise ValueError('grid sides must lie in 1..30')
    if num_patches is not None and num_patches != len(patches):
      raise ValueError('num_patches disagrees with the explicit patches')
    pair, info = _render(width, height, background, line, hub, patches,
                         paths)
    values = sorted(info['tally'].values(), reverse=True)
    if len(values) > 1 and values[0] == values[1]:
      raise ValueError('hub centre colour would be a tie')
    if _solid_blocks(pair['input'], line) != 1:
      raise ValueError('the hub must be the only solid 3x3 line block')
    if not _branches_ok(info['group'], info['interior'], info['hub_cells']):
      raise ValueError('each branch must belong to one patch and the hub')
    if not _colours_ok(pair['input'], background, line):
      raise ValueError('background > line > each patch colour is required')
    return pair
  for value in (width, height):
    if value is not None and not 10 <= value <= 30:
      raise ValueError('random scenes need 10..30 cells per side')
  if num_patches is not None:
    if not 2 <= num_patches <= 6:
      raise ValueError('num_patches must lie in 2..6')
    for value in (width, height):
      if value is not None and value < _THRESHOLD[num_patches]:
        raise ValueError('grid too small for the requested patch count')
  roll = random.random()
  if roll < 0.3:
    mode = 'pixel'
  elif roll < 0.75:
    mode = 'any'
  else:
    mode = None
  for attempt in range(_ATTEMPTS):
    scene = _sample_scene(width, height, background, line, num_patches)
    if scene is None:
      continue
    pair, info = _render(*scene)
    require = mode if attempt < _ATTEMPTS // 2 else None
    if _acceptable(pair, info, scene[2], scene[3], require):
      return pair
  raise ValueError('could not build a scene with the requested parameters')


def validate():
  """Rebuilds the original task pairs from explicit latent parameters."""
  train = [
      generate(width=16, height=16, background=9, line=8, hub=(6, 5),
               patches=[(0, 0, ['3434', '4343', '3334', '3433']),
                        (0, 12, ['4444', '4434', '3344']),
                        (14, 6, ['44', '43']),
                        (14, 14, ['34', '44'])],
               paths=[(0, [(2, 4), (2, 6), (5, 6)]),
                      (0, [(4, 1), (7, 1), (7, 4)]),
                      (1, [(3, 12), (6, 12), (6, 8)]),
                      (2, [(9, 6), (12, 6)]),
                      (3, [(8, 8), (8, 14), (12, 14)])]),
      generate(width=10, height=10, background=0, line=5, hub=(3, 3),
               patches=[(0, 8, ['22', '21']),
                        (8, 0, ['211', '121']),
                        (8, 8, ['22', '12'])],
               paths=[(0, [(2, 4), (1, 4), (1, 7)]),
                      (1, [(4, 2), (4, 1), (7, 1)]),
                      (2, [(4, 6), (4, 8), (7, 8)])]),
      generate(width=20, height=20, background=8, line=7, hub=(8, 8),
               patches=[(0, 0, ['66666', '66566', '56666', '66666',
                                '66666']),
                        (0, 11, ['565', '655']),
                        (6, 18, ['56', '55', '56', '65']),
                        (14, 0, ['656666', '666666', '666666', '666665',
                                 '656656', '666666']),
                        (18, 10, ['65565', '65565'])],
               paths=[(0, [(2, 5), (2, 7), (4, 7), (4, 8), (7, 8)]),
                      (0, [(5, 3), (8, 3), (8, 7)]),
                      (1, [(2, 11), (5, 11), (5, 10), (7, 10)]),
                      (2, [(7, 17), (7, 13), (8, 13), (8, 11)]),
                      (3, [(10, 7), (10, 3), (13, 3)]),
                      (3, [(11, 8), (14, 8), (14, 6)]),
                      (4, [(11, 10), (16, 10)])]),
  ]
  big = ['2' * 15, '2' * 15, '2' * 6 + '3' + '2' * 6 + '32',
         '2' * 4 + '3' + '2' * 7 + '332', '2' * 13 + '32',
         '2' * 9 + '3' + '222' + '32', '2' * 15, '2' * 15, '2' * 15]
  test = [
      generate(width=30, height=30, background=6, line=4, hub=(11, 12),
               patches=[(0, 0, ['333333333', '333333333', '333323333',
                                '332233333', '223233333', '233333333',
                                '333333233', '223333323', '333333333']),
                        (4, 27, ['232', '232']),
                        (22, 0, ['33', '32', '32']),
                        (21, 15, big)],
               paths=[(0, [(4, 9), (4, 14), (10, 14)]),
                      (0, [(7, 9), (7, 12), (10, 12)]),
                      (0, [(9, 5), (12, 5), (12, 7), (11, 7), (11, 11)]),
                      (1, [(5, 26), (5, 22), (8, 22), (8, 21), (10, 21),
                           (10, 20), (11, 20), (11, 15)]),
                      (3, [(14, 14), (15, 14), (15, 16), (20, 16)]),
                      (3, [(14, 12), (22, 12), (22, 14)]),
                      (2, [(22, 2), (22, 6), (16, 6), (16, 9), (13, 9),
                           (13, 11)])]),
  ]
  return {'train': train, 'test': test}
