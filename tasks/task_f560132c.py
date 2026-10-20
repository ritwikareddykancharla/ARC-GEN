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

"""ARC-GEN style generator for task f560132c.

Rule: the input holds four single-colour pieces on a black background. One
piece, the container, carries a 2x2 key of four distinct colours. Count the
key cells as part of the container. The four pieces then tile an NxN square,
where N*N is the total piece area. The container keeps its original
orientation and sits in the top-left corner. Each other piece may be turned
by quarter turns, but never mirrored, so that it fills one of the remaining
corners. Each piece is anchored by its bounding box. Every piece is painted
with the key colour of the corner it occupies.

Construction:

1. An NxN square is cut into four corner-anchored, 4-connected regions. The
   regions are grown over a randomly sized coarse block grid, which keeps the
   shapes blocky as in ARC.
2. The top-left region becomes the container. A 2x2 key is embedded where
   removing it leaves the container 4-connected with the same bounding box.
3. The other three regions are turned by random quarter turns and scattered
   on the input canvas. Their bounding boxes are kept at least one empty row
   or column apart.
4. An exhaustive corner-tiling search rejects any partition that admits a
   second rotation-only tiling, so the answer is unambiguous. This includes
   tilings that put the container in another corner.
5. About half of the random samples are softly steered towards partitions
   that are "mirror-decisive": a solver that also allowed mirrored pieces
   would find a different tiling. This exercises the no-mirroring constraint.

Scope:

- Random output sides are 6..14. Sides other than the fixture sizes 8, 10 and
  12 are synthetic extensions.
- If a drawn size fails its bounded search, a new size is drawn, so the size
  distribution may lean slightly towards larger sides.
- Input canvases are up to 30x30 and may be non-square.
- Eight distinct non-black colours are used: four for the key and four for
  the pieces.
- The generator never places the container in a corner other than top-left.
  It never generates mirrored input pieces, distractor objects or non-black
  backgrounds.
"""

import collections
import itertools
import random

import common

_CORNERS = ((0, 0), (0, 1), (1, 0), (1, 1))
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _is_int(v):
  """True for genuine integers (bool is rejected)."""
  return isinstance(v, int) and not isinstance(v, bool)


def _split(n):
  """Splits length n into random segments of length 1..3."""
  parts = []
  while n > 0:
    s = min(random.choice([1, 2, 2, 3, 3]), n)
    parts.append(s)
    n -= s
  return parts


def _random_regions(n):
  """Grows four corner-seeded regions over a random coarse block grid."""
  rows, cols = _split(n), _split(n)
  kh, kw = len(rows), len(cols)
  if kh < 2 or kw < 2:
    return None
  owner = [[-1] * kw for _ in range(kh)]
  area = [0, 0, 0, 0]
  seeds = ((0, 0), (0, kw - 1), (kh - 1, 0), (kh - 1, kw - 1))
  for k, (r, c) in enumerate(seeds):
    owner[r][c] = k
    area[k] += rows[r] * cols[c]
  remaining = kh * kw - 4
  while remaining > 0:
    frontier = [[], [], [], []]
    for r in range(kh):
      for c in range(kw):
        if owner[r][c] != -1:
          continue
        for dr, dc in _DIRS:
          rr, cc = r + dr, c + dc
          if 0 <= rr < kh and 0 <= cc < kw and owner[rr][cc] != -1:
            frontier[owner[rr][cc]].append((r, c))
    choices = [k for k in range(4) if frontier[k]]
    weights = [1.0 / (area[k] + 1) for k in choices]
    k = random.choices(choices, weights)[0]
    r, c = random.choice(frontier[k])
    owner[r][c] = k
    area[k] += rows[r] * cols[c]
    remaining -= 1
  row_of, col_of = [], []
  for i, s in enumerate(rows):
    row_of.extend([i] * s)
  for j, s in enumerate(cols):
    col_of.extend([j] * s)
  return [[owner[row_of[r]][col_of[c]] for c in range(n)] for r in range(n)]


def _connected(cells):
  """True if the cell set is non-empty and 4-connected."""
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr, dc in _DIRS:
      nb = (r + dr, c + dc)
      if nb in cells and nb not in seen:
        seen.add(nb)
        stack.append(nb)
  return len(seen) == len(cells)


def _bbox(cells):
  rs = [r for r, _ in cells]
  cs = [c for _, c in cells]
  return (min(rs), min(cs), max(rs), max(cs))


def _normalise(cells):
  """Returns (height, width, frozenset of local cells)."""
  r0, c0, r1, c1 = _bbox(cells)
  return (r1 - r0 + 1, c1 - c0 + 1,
          frozenset((r - r0, c - c0) for r, c in cells))


def _rotate(shape):
  """Rotates a shape a quarter turn clockwise."""
  h, w, cells = shape
  return (w, h, frozenset((c, h - 1 - r) for r, c in cells))


def _flip(shape):
  """Mirrors a shape left to right."""
  h, w, cells = shape
  return (h, w, frozenset((r, w - 1 - c) for r, c in cells))


def _rotations(shape):
  res, seen, s = [], set(), shape
  for _ in range(4):
    if s not in seen:
      seen.add(s)
      res.append(s)
    s = _rotate(s)
  return res


def _orientations(shape, mirror):
  """Distinct rotations, plus mirrored rotations when mirror is set."""
  res = _rotations(shape)
  if mirror:
    for s in _rotations(_flip(shape)):
      if s not in res:
        res.append(s)
  return res


def _analyse(reg, n):
  """Checks the partition and returns (cells per region, shapes)."""
  cells = [[], [], [], []]
  for r in range(n):
    for c in range(n):
      cells[reg[r][c]].append((r, c))
  for k, (cy, cx) in enumerate(_CORNERS):
    corner = (0 if cy == 0 else n - 1, 0 if cx == 0 else n - 1)
    if corner not in set(cells[k]):
      return None
    if len(cells[k]) < 3 or not _connected(cells[k]):
      return None
  return cells, [_normalise(c) for c in cells]


def _mask(shape, corner, n):
  h, w, cells = shape
  if h > n or w > n:
    return None
  y0 = 0 if corner[0] == 0 else n - h
  x0 = 0 if corner[1] == 0 else n - w
  m = 0
  for r, c in cells:
    m |= 1 << ((y0 + r) * n + x0 + c)
  return m


def _tilings(n, shapes, limit=2, mirror=False):
  """Distinct corner tilings; container fixed, others rotated (or mirrored).

  A tiling is recorded as the tuple of occupied masks per corner. Two tilings
  are therefore distinct exactly when they give different outputs.
  """
  opts = []
  for i, shp in enumerate(shapes):
    orients = [shp] if i == 0 else _orientations(shp, mirror)
    row = []
    for corner in _CORNERS:
      ms = [_mask(o, corner, n) for o in orients]
      row.append([m for m in ms if m is not None])
    opts.append(row)
  full = (1 << (n * n)) - 1
  found = set()
  for perm in itertools.permutations(range(4)):
    stack = [(0, 0, ())]
    while stack:
      k, occ, acc = stack.pop()
      if k == 4:
        if occ == full:
          found.add(acc)
          if len(found) >= limit:
            return found
        continue
      for m in opts[perm[k]][k]:
        if not m & occ:
          stack.append((k + 1, occ | m, acc + (m,)))
  return found


def _mirror_decisive(n, shapes):
  """True if also allowing mirrored pieces would admit another tiling."""
  return len(_tilings(n, shapes, limit=2, mirror=True)) >= 2


def _key_positions(cells):
  """2x2 spots whose removal keeps the container connected, same bbox."""
  s = set(cells)
  box = _bbox(s)
  spots = []
  for r, c in sorted(s):
    block = {(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)}
    if not block <= s:
      continue
    rest = s - block
    if len(rest) < 3 or _bbox(rest) != box or not _connected(rest):
      continue
    spots.append((r, c))
  return spots


def _key_hits_corner(key_pos, n):
  """True if the 2x2 key block covers the TR, BL or BR corner cell."""
  kr, kc = key_pos
  block = {(kr + i, kc + j) for i in range(2) for j in range(2)}
  return bool(block & {(0, n - 1), (n - 1, 0), (n - 1, n - 1)})


def _sample_partition(n, key_pos, mode, attempts):
  """Samples an unambiguous partition of side n.

  mode True requires a mirror-decisive partition and False forbids one.
  None prefers one or the other at random, with a bounded soft fallback.
  Returns (regions, cells, shapes, key spots) or None.
  """
  want = mode if mode is not None else random.random() < 0.5
  fallback = None
  misses = 0
  for _ in range(attempts):
    reg = _random_regions(n)
    if reg is None:
      continue
    info = _analyse(reg, n)
    if info is None:
      continue
    cells, shapes = info
    if min(len(c) for c in cells) < max(4, n * n // 12):
      continue
    if len(cells[0]) < 8:
      continue
    spots = _key_positions(cells[0])
    if not spots or (key_pos is not None and key_pos not in spots):
      continue
    if len(_tilings(n, shapes)) != 1:
      continue
    cand = (reg, cells, shapes, spots)
    if _mirror_decisive(n, shapes) == want:
      return cand
    if mode is None:
      if fallback is None:
        fallback = cand
      misses += 1
      if misses >= 25:
        return fallback
  return fallback


def _apart(a, b):
  """Boxes (r, c, h, w) separated by at least one empty row or column."""
  return (a[0] + a[2] < b[0] or b[0] + b[2] < a[0] or
          a[1] + a[3] < b[1] or b[1] + b[3] < a[1])


def _layout(dims, width, height):
  """Random scattered placement; None if it fails within a bounded budget."""
  for _ in range(300):
    boxes = []
    for h, w in dims:
      for _ in range(60):
        box = (random.randint(0, height - h), random.randint(0, width - w), h, w)
        if all(_apart(box, b) for b in boxes):
          boxes.append(box)
          break
      else:
        break
    if len(boxes) == len(dims):
      return [(b[0], b[1]) for b in boxes]
  return None


def _quadrant(dims, width, height, grow_w, grow_h):
  """Shuffled 2x2 arrangement; grows only dimensions not fixed by caller."""
  order = list(range(4))
  random.shuffle(order)
  slot = {order[s]: s for s in range(4)}
  cw = [max(dims[order[0]][1], dims[order[2]][1]),
        max(dims[order[1]][1], dims[order[3]][1])]
  rh = [max(dims[order[0]][0], dims[order[1]][0]),
        max(dims[order[2]][0], dims[order[3]][0])]
  need_w, need_h = cw[0] + cw[1] + 1, rh[0] + rh[1] + 1
  if grow_w:
    width = max(width, need_w)
  if grow_h:
    height = max(height, need_h)
  if need_w > width or need_h > height or width > 30 or height > 30:
    return None
  ox = random.randint(0, width - need_w)
  oy = random.randint(0, height - need_h)
  positions = []
  for i in range(4):
    sr, sc = divmod(slot[i], 2)
    positions.append((oy + (0 if sr == 0 else rh[0] + 1),
                      ox + (0 if sc == 0 else cw[0] + 1)))
  return positions, width, height


def _check_colours(vals, count, name):
  if len(vals) != count:
    raise ValueError('%s must hold %d distinct colours' % (name, count))
  for v in vals:
    if not _is_int(v) or not 1 <= v <= 9:
      raise ValueError('%s colours must be integers in 1..9' % name)
  if len(set(vals)) != count:
    raise ValueError('%s must hold %d distinct colours' % (name, count))


def _parse_regions(regions):
  """Strictly parses region rows (strings of '0'..'3' or int lists)."""
  if isinstance(regions, str) or not isinstance(regions, (list, tuple)):
    raise ValueError('regions must be a list of rows')
  rows = []
  for row in regions:
    if isinstance(row, str):
      if any(ch not in '0123' for ch in row):
        raise ValueError('region ids must be 0..3')
      rows.append([int(ch) for ch in row])
    elif isinstance(row, (list, tuple)):
      if any(not _is_int(v) or v not in (0, 1, 2, 3) for v in row):
        raise ValueError('region ids must be integers 0..3')
      rows.append(list(row))
    else:
      raise ValueError('each region row must be a string or a list')
  return rows


def generate(size=None, regions=None, key=None, key_pos=None, colors=None,
             rotations=None, positions=None, width=None, height=None,
             decisive=None, require_unique=None):
  """Builds one input/output pair.

  Args:
    size: side N of the output square, 6..14. It is random in 6..14 when
      omitted. If regions is given, size must equal its side.
    regions: N rows describing the output partition. Each row is a string or
      an int list of region ids: 0=TL (container), 1=TR, 2=BL, 3=BR.
    key: 2x2 list of distinct key colours, indexed by corner (row, col).
    key_pos: (row, col) of the key's top-left cell inside the container. This
      is also its output position, because the container is top-left. It must
      be a valid key spot: the container stays connected with the same bbox.
      It may never cover the TR, BL or BR corner cell.
    colors: four distinct input colours for the [container, TR, BL, BR]
      pieces. They must be disjoint from the key colours.
    rotations: three integer clockwise quarter-turn counts. They are applied
      to the TR, BL and BR regions to give their appearance in the input.
    positions: input (row, col) of each piece's bounding-box corner. This
      requires explicit regions and rotations.
    width: input width (1..30). Never enlarged when supplied.
    height: input height (1..30). Never enlarged when supplied.
    decisive: controls mirror-decisive partitions, where a solver that also
      allowed mirrored pieces would find a different tiling.
      - None (default): prefers such a partition with probability 1/2, with
        a bounded soft fallback.
      - True: requires one. False: forbids one. Either raises RuntimeError
        if the bounded search fails.
      - With explicit regions, the flag is checked and a mismatch raises
        ValueError.
    require_unique: applies only to explicit regions.
      - None or True: raise ValueError unless exactly one rotation-only
        corner tiling exists.
      - False: replay the regions without that check.
      Random partitions are always required to be unique, so passing False
      without regions raises ValueError.
  """
  if positions is not None and (regions is None or rotations is None):
    raise ValueError('positions requires explicit regions and rotations')
  for name, v in (('width', width), ('height', height)):
    if v is not None and (not _is_int(v) or not 1 <= v <= 30):
      raise ValueError('%s must be an integer in 1..30' % name)
  if size is not None:
    if not _is_int(size):
      raise ValueError('size must be an integer')
    if regions is None and not 6 <= size <= 14:
      raise ValueError('size must be in 6..14')
  if decisive is not None and not isinstance(decisive, bool):
    raise ValueError('decisive must be None, True or False')
  if require_unique is not None and not isinstance(require_unique, bool):
    raise ValueError('require_unique must be None, True or False')
  if regions is None and require_unique is False:
    raise ValueError('random partitions are always unique; '
                     'require_unique=False needs explicit regions')
  if key is not None:
    key = [list(row) for row in key]
    if len(key) != 2 or any(len(row) != 2 for row in key):
      raise ValueError('key must be 2x2')
    _check_colours([v for row in key for v in row], 4, 'key')
  if colors is not None:
    colors = list(colors)
    _check_colours(colors, 4, 'colors')
  if key is not None and colors is not None:
    if set(colors) & {v for row in key for v in row}:
      raise ValueError('key and piece colours must be disjoint')
  if rotations is not None:
    rotations = list(rotations)
    if len(rotations) != 3:
      raise ValueError('rotations needs three entries (TR, BL, BR)')
    if any(not _is_int(v) for v in rotations):
      raise ValueError('rotations must be integers')
  parsed = _parse_regions(regions) if regions is not None else None
  if key_pos is not None:
    key_pos = tuple(key_pos)
    if len(key_pos) != 2 or any(not _is_int(v) for v in key_pos):
      raise ValueError('key_pos must be two integers')
    if min(key_pos) < 0:
      raise ValueError('key_pos lies outside the output square')
    if parsed is not None or size is not None:
      side = len(parsed) if parsed is not None else size
      if max(key_pos) > side - 2:
        raise ValueError('key_pos lies outside the output square')
      if _key_hits_corner(key_pos, side):
        raise ValueError('key_pos covers a corner owned by another piece')
    elif max(key_pos) + 3 > 14:
      raise ValueError('key_pos does not fit any supported random size')

  if parsed is None:
    if size is not None:
      sizes = [size]
      budget = 1500
    else:
      lo_n = 6 if key_pos is None else max(6, max(key_pos) + 3)
      sizes = [random.randint(lo_n, 14) for _ in range(4)]
      budget = 500
    picked = None
    n = sizes[0]
    for n in sizes:
      picked = _sample_partition(n, key_pos, decisive, budget)
      if picked is not None:
        break
    if picked is None:
      raise RuntimeError('could not build an unambiguous tiling')
    reg, cells, shapes, spots = picked
  else:
    reg = parsed
    n = len(reg)
    if n < 2 or n > 30 or any(len(row) != n for row in reg):
      raise ValueError('regions must be a square partition')
    if size is not None and size != n:
      raise ValueError('size does not match regions')
    info = _analyse(reg, n)
    if info is None:
      raise ValueError('invalid region partition')
    cells, shapes = info
    spots = _key_positions(cells[0])
    if not spots:
      raise ValueError('container has no valid key spot')
    if require_unique is not False and len(_tilings(n, shapes)) != 1:
      raise ValueError('regions admit more than one rotation-only tiling')
    if decisive is not None and _mirror_decisive(n, shapes) != decisive:
      raise ValueError('regions do not match the requested decisive flag')
  if key_pos is None:
    inner = [s for s in spots if s[0] >= 1 and s[1] >= 1]
    key_pos = random.choice(inner or spots)
  elif key_pos not in spots:
    raise ValueError('key_pos is not a valid key spot in the container')

  used = set()
  if key is not None:
    used |= {v for row in key for v in row}
  if colors is not None:
    used |= set(colors)
  free = [c for c in range(1, 10) if c not in used]
  random.shuffle(free)
  if key is None:
    key = [[free.pop(), free.pop()], [free.pop(), free.pop()]]
  if colors is None:
    colors = [free.pop() for _ in range(4)]

  if rotations is None:
    rotations = [random.randint(0, 3) for _ in range(3)]
  placed = [shapes[0]]
  for i in range(1, 4):
    s = shapes[i]
    for _ in range(rotations[i - 1] % 4):
      s = _rotate(s)
    placed.append(s)
  dims = [(s[0], s[1]) for s in placed]
  maxh = max(h for h, _ in dims)
  maxw = max(w for _, w in dims)

  if positions is None:
    grow_w, grow_h = width is None, height is None
    lo = min(30, max(14, n + 6))
    w_cur = width if width is not None else random.randint(lo, 30)
    h_cur = height if height is not None else random.randint(lo, 30)
    if grow_w:
      w_cur = max(w_cur, maxw)
    if grow_h:
      h_cur = max(h_cur, maxh)
    if w_cur < maxw or h_cur < maxh:
      raise ValueError('canvas too small for the pieces')
    positions = None
    for _ in range(6):
      positions = _layout(dims, w_cur, h_cur)
      if positions is not None:
        break
      if grow_w:
        w_cur = min(30, w_cur + 3)
      if grow_h:
        h_cur = min(30, h_cur + 3)
    if positions is None:
      res = _quadrant(dims, w_cur, h_cur, grow_w, grow_h)
      if res is None:
        raise ValueError('pieces cannot be laid out on the requested canvas')
      positions, w_cur, h_cur = res
    width, height = w_cur, h_cur
  else:
    positions = [tuple(p) for p in positions]
    if len(positions) != 4 or any(len(p) != 2 for p in positions):
      raise ValueError('positions needs four (row, col) entries')
    if any(not _is_int(v) for p in positions for v in p):
      raise ValueError('positions must be integers')
    if width is None:
      width = max(p[1] + d[1] for p, d in zip(positions, dims))
    if height is None:
      height = max(p[0] + d[0] for p, d in zip(positions, dims))
    boxes = [(p[0], p[1], d[0], d[1]) for p, d in zip(positions, dims)]
    for b in boxes:
      if b[0] < 0 or b[1] < 0 or b[0] + b[2] > height or b[1] + b[3] > width:
        raise ValueError('piece outside the canvas')
    for a, b in itertools.combinations(boxes, 2):
      if not _apart(a, b):
        raise ValueError('piece bounding boxes must be separated')
  if width > 30 or height > 30:
    raise ValueError('canvas exceeds 30x30')

  grid = common.grid(width, height, 0)
  if len(grid) != height or any(len(row) != width for row in grid):
    raise RuntimeError('canvas has unexpected dimensions')
  kr, kc = key_pos
  for i, (_, _, cs) in enumerate(placed):
    pr, pc = positions[i]
    for r, c in cs:
      val = colors[i]
      if i == 0 and kr <= r <= kr + 1 and kc <= c <= kc + 1:
        val = key[r - kr][c - kc]
      grid[pr + r][pc + c] = val
  counts = collections.Counter(v for row in grid for v in row)
  if any(cnt >= counts[0] for col, cnt in counts.items() if col != 0):
    raise ValueError('background must remain the most frequent colour')
  output = [[key[reg[r][c] // 2][reg[r][c] % 2] for c in range(n)]
            for r in range(n)]
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the canonical pairs from explicit latent parameters.

  All three supplied pairs are asserted unique under rotation-only tiling.
  The query's uniqueness was also checked by an independent visible-input
  exact-cover implementation during host review.
  """
  train = [
      generate(regions=['00000111', '00003111', '00033111', '00333111',
                        '03333333', '22233333', '22233333', '22222333'],
               key=[[1, 5], [8, 9]], key_pos=(1, 1), colors=[2, 7, 3, 4],
               rotations=[1, 3, 2],
               positions=[(1, 1), (2, 12), (13, 14), (10, 1)],
               width=20, height=20, require_unique=True),
      generate(regions=['0001111111', '0001111111', '0000011111',
                        '0000011111', '0000033333', '2220033333',
                        '2200003333', '2200003333', '2222233333',
                        '2222233333'],
               key=[[2, 4], [8, 3]], key_pos=(2, 1), colors=[6, 1, 5, 9],
               rotations=[1, 2, 3],
               positions=[(4, 4), (12, 15), (1, 12), (14, 1)],
               width=20, height=20, require_unique=True),
  ]
  test = [
      generate(regions=['000000000011', '000000000011', '000011110011',
                        '000011110011', '001111110011', '001111111111',
                        '000000011113', '000000011113', '222111111113',
                        '222211111333', '222221111333', '222222111333'],
               key=[[3, 6], [4, 8]], key_pos=(1, 1), colors=[9, 5, 2, 7],
               rotations=[2, 0, 2],
               positions=[(4, 3), (6, 16), (20, 17), (19, 3)],
               width=26, height=26, require_unique=True),
  ]
  return {'train': train, 'test': test}
