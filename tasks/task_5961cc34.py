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

"""ARC-GEN style generator for task 5961cc34 (beam relay through marked blobs).

Rule: the background is 8. On it are a launcher, several blobs of colour 1,
and one 3 marker attached to one face of each blob. The launcher is a single
4 cell with a straight tail of 2s behind it. The 4 fires a 1-wide beam of 2,
away from its tail. When the beam reaches a blob, the blob and its marker turn
2. The beam then leaves through the marker and is as wide as the marker. It
travels outward on the side of the blob's bounding box where the marker lies,
until it hits the next blob or leaves the grid. A marker embedded in the
right face, inside the bounding box (as in the test example), sends the beam
right. The launcher and its tail become 2. Blobs and markers the beam never
reaches are erased to 8, so the output contains only 2 on 8.

Scope: random grids are 14..30 per side; explicit sizes of 10..30 are
accepted. The launcher's tail touches a border. The launcher fires up most
often, as in every original example; firing down, left or right is a
synthetic extension. A scene has 0..4 chained hits and markers 1 or 2 cells
wide. Blobs are rounded, with the marker centred on one face. A right-face
marker is sometimes notched into the blob's outermost column, as in the test
example. A scene also has 0..3 untouched distractor units (blob plus marker),
which are erased.

Scenes are built constructively. Each next blob is placed on the current beam
so that every lane of the beam strikes it on the same step. Every unit is
separated from every other object by at least one background cell, so each
marker is 8-adjacent only to its own blob. No beam segment runs next to a unit
it does not hit. The output is painted from the recorded beam segments and
the hit units; the input is not re-solved.

Not supported: blobs without markers, corner markers, notched markers on
faces other than the right one, and beams that return to an already converted
blob.
"""

import random

import common

BG, BLOB, MARK, LAUNCH, BEAM = 8, 1, 3, 4, 2
DIRS = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}
OPP = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}
N_HIT_CHOICES = [0, 1, 1, 2, 2, 2, 3, 3, 4]
DIR_CHOICES = ['up', 'up', 'up', 'down', 'left', 'right']


def _dot(cell, vec):
  return cell[0] * vec[0] + cell[1] * vec[1]


def _perp(d):
  return (0, 1) if d[0] != 0 else (1, 0)


def _cell(p, a, d):
  """Cell with perpendicular coordinate p and along-d coordinate a."""
  if d[0] != 0:
    return (a * d[0], p)
  return (p, a * d[1])


def _dilate(cells):
  out = set()
  for r, c in cells:
    for a in (-1, 0, 1):
      for b in (-1, 0, 1):
        out.add((r + a, c + b))
  return out


def _connected(cells):
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen, stack = {start}, [start]
  while stack:
    r, c = stack.pop()
    for nb in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
      if nb in cells and nb not in seen:
        seen.add(nb)
        stack.append(nb)
  return len(seen) == len(cells)


def _exit_of(blob, mark):
  """Exit side for a marker, or None when it is not unambiguous.

  A marker wholly outside the blob's bounding box on one side exits on that
  side. A marker inside the bounding box is accepted only when it sits in a
  notch whose single open side is the right one. That is the right-face case
  of the test example, and it is also what the bounding-box convention gives
  for an in-box marker.
  """
  y0 = min(r for r, _ in blob)
  y1 = max(r for r, _ in blob)
  x0 = min(c for _, c in blob)
  x1 = max(c for _, c in blob)
  in_cols = all(x0 <= c <= x1 for _, c in mark)
  in_rows = all(y0 <= r <= y1 for r, _ in mark)
  if in_cols and all(r < y0 for r, _ in mark):
    return 'up'
  if in_cols and all(r > y1 for r, _ in mark):
    return 'down'
  if in_rows and all(c < x0 for _, c in mark):
    return 'left'
  if in_rows and all(c > x1 for _, c in mark):
    return 'right'
  if in_cols and in_rows:
    bset = set(blob)
    open_sides = [n for n, (dr, dc) in DIRS.items()
                  if all((r + dr, c + dc) not in bset for r, c in mark)]
    if open_sides == ['right']:
      return 'right'
  return None


def _pattern_cells(top, left, pattern):
  blob, mark = [], []
  for r, row in enumerate(pattern):
    for c, ch in enumerate(row):
      if ch == '1':
        blob.append((top + r, left + c))
      elif ch == '3':
        mark.append((top + r, left + c))
  return blob, mark


def _shape(m, exit_name):
  """Rounded blob plus an m-wide marker on side exit_name (local coords).

  For exit 'right' the marker may be notched into the blob's outermost
  column, as in the test example. This is done only when the blob stays
  4-connected.
  """
  low = 2 if m == 2 else 1
  widths, peak = None, m + 2
  for _ in range(60):
    peak = m + 2 * random.randint(1, 3)
    first = random.choice(list(range(m, peak + 1, 2)))
    last = random.choice(list(range(low, peak + 1, 2)))
    plateau = random.randint(1, 2)
    cand = (list(range(first, peak, 2)) + [peak] * plateau +
            list(range(peak - 2, last - 1, -2)))
    if 2 <= len(cand) <= 7:
      widths = cand
      break
  if widths is None:
    widths = [peak, peak]
  notch = (exit_name == 'right' and len(widths) >= 2 and
           widths[0] >= m + 2 and widths[1] >= widths[0] and
           random.random() < 0.4)
  mark = [(0, (peak - m) // 2 + j) for j in range(m)]
  mset = set(mark)
  off = 0 if notch else 1
  blob = []
  for i, w in enumerate(widths):
    for j in range(w):
      cell = (i + off, (peak - w) // 2 + j)
      if cell in mset:
        continue
      blob.append(cell)

  def rot(cell):
    r, c = cell
    if exit_name == 'up':
      return (r, c)
    if exit_name == 'down':
      return (-r, c)
    if exit_name == 'left':
      return (c, r)
    return (c, -r)

  blob = [rot(x) for x in blob]
  mark = [rot(x) for x in mark]
  allc = blob + mark
  r0 = min(x[0] for x in allc)
  c0 = min(x[1] for x in allc)
  blob = [(r - r0, c - c0) for r, c in blob]
  mark = [(r - r0, c - c0) for r, c in mark]
  return blob, mark


def _trace(height, width, start, dname, units):
  """Trace the beam over explicit latent units (fixture replay only)."""
  blob_of = {}
  for i, u in enumerate(units):
    for cell in u['blob']:
      blob_of[cell] = i
  painted, used, front = set(), set(), [start]
  for _ in range(len(units) + 1):
    dr, dc = DIRS[dname]
    hit = None
    for _ in range(height + width):
      nxt = [(r + dr, c + dc) for r, c in front]
      if any(not (0 <= r < height and 0 <= c < width) for r, c in nxt):
        break
      hs = [blob_of[x] for x in nxt if x in blob_of]
      if hs:
        hit = hs[0]
        break
      painted.update(nxt)
      front = nxt
    if hit is None or hit in used:
      break
    used.add(hit)
    u = units[hit]
    painted.update(u['blob'])
    painted.update(u['mark'])
    front = sorted(u['mark'])
    dname = u['exit']
  return painted


def _launcher_cells(r, c, dname, tail):
  dr, dc = DIRS[dname]
  return [(r, c)] + [(r - dr * k, c - dc * k) for k in range(1, tail + 1)]


def _paint(height, width, launch, units, beam_cells):
  grid_in = common.grid(width, height, BG)
  grid_out = common.grid(width, height, BG)
  for k, (y, x) in enumerate(launch):
    grid_in[y][x] = LAUNCH if k == 0 else BEAM
    grid_out[y][x] = BEAM
  for u in units:
    for y, x in u['blob']:
      grid_in[y][x] = BLOB
    for y, x in u['mark']:
      grid_in[y][x] = MARK
  for y, x in beam_cells:
    grid_out[y][x] = BEAM
  return {'input': grid_in, 'output': grid_out}


def _construct(height, width, n_hits, n_distractors, dname):
  """Build one scene with exactly n_hits hits and n_distractors units."""
  H, W = height, width
  tail = random.randint(2, 3)
  dr, dc = DIRS[dname]
  if dr != 0:
    r = H - 1 - tail if dr < 0 else tail
    c = random.randint(2, W - 3)
  else:
    c = W - 1 - tail if dc < 0 else tail
    r = random.randint(2, H - 3)
  launch = _launcher_cells(r, c, dname, tail)
  occ = {cell: -1 for cell in launch}
  path = set()
  units, hits = [], []
  front, src = [(r, c)], -1

  for _ in range(n_hits):
    d = DIRS[dname]
    perp = _perp(d)
    lanes = [_dot(x, perp) for x in front]
    fdot = _dot(front[0], d)
    blocked = _dilate([x for x, o in occ.items() if o != src])
    placed = False
    for _ in range(40):
      m = random.choice([1, 2, 2])
      ex = random.choice([x for x in DIRS if x != OPP[dname]])
      blob, mark = _shape(m, ex)
      g = random.randint(2, 8)
      first = {}
      for cell in blob:
        q, a = _dot(cell, perp), _dot(cell, d)
        if q not in first or a < first[q]:
          first[q] = a
      offsets = []
      for q in first:
        tp = lanes[0] - q
        vals = [first.get(l - tp) for l in lanes]
        if None in vals or len(set(vals)) != 1:
          continue
        offsets.append((tp, vals[0]))
      random.shuffle(offsets)
      for tp, h in offsets:
        s = fdot + g + 1 - h
        t = (tp * perp[0] + s * d[0], tp * perp[1] + s * d[1])
        nb = [(a + t[0], b + t[1]) for a, b in blob]
        nm = [(a + t[0], b + t[1]) for a, b in mark]
        cells = nb + nm
        if any(not (1 <= y <= H - 2 and 1 <= x <= W - 2) for y, x in cells):
          continue
        seg = [_cell(l, fdot + j, d) for l in lanes for j in range(1, g + 1)]
        if any(x in blocked for x in seg):
          continue
        dil = _dilate(cells)
        if any(x in occ or x in path for x in dil):
          continue
        idx = len(units)
        units.append({'blob': nb, 'mark': nm, 'exit': ex})
        hits.append(idx)
        for cell in cells:
          occ[cell] = idx
        path.update(seg)
        front, dname, src = sorted(nm), ex, idx
        placed = True
        break
      if placed:
        break
    if not placed:
      return None

  # Final segment to the border; it must not pass next to any other object.
  d = DIRS[dname]
  blocked = _dilate([x for x, o in occ.items() if o != src])
  cur, steps = list(front), 0
  for _ in range(H + W):
    nxt = [(y + d[0], x + d[1]) for y, x in cur]
    if any(not (0 <= y < H and 0 <= x < W) for y, x in nxt):
      break
    if any(x in blocked for x in nxt):
      return None
    path.update(nxt)
    cur = nxt
    steps += 1
  if steps < 2:
    return None

  # Distractors: complete units the beam never touches (exact count).
  for _ in range(n_distractors):
    placed = False
    for _ in range(60):
      m = random.choice([1, 2, 2])
      ex = random.choice(list(DIRS))
      blob, mark = _shape(m, ex)
      hh = max(y for y, _ in blob + mark) + 1
      ww = max(x for _, x in blob + mark) + 1
      if hh > H - 2 or ww > W - 2:
        continue
      ty = random.randint(1, H - 1 - hh)
      tx = random.randint(1, W - 1 - ww)
      nb = [(y + ty, x + tx) for y, x in blob]
      nm = [(y + ty, x + tx) for y, x in mark]
      if any(x in occ or x in path for x in _dilate(nb + nm)):
        continue
      idx = len(units)
      units.append({'blob': nb, 'mark': nm, 'exit': ex})
      for cell in nb + nm:
        occ[cell] = idx
      placed = True
      break
    if not placed:
      return None

  beam = set(path)
  for i in hits:
    beam.update(units[i]['blob'])
    beam.update(units[i]['mark'])
  return _paint(H, W, launch, units, beam)


def _render_explicit(height, width, launcher, units):
  """Render explicit latent objects and trace the beam over them."""
  H, W = height, width
  r, c, dname, tail = launcher
  if dname not in DIRS or tail < 1:
    raise ValueError('bad launcher specification')
  launch = _launcher_cells(r, c, dname, tail)
  owner = {}
  for y, x in launch:
    if not (0 <= y < H and 0 <= x < W):
      raise ValueError('launcher out of bounds')
    owner[(y, x)] = -1
  objs = []
  for i, (top, left, pattern, ex) in enumerate(units):
    if not pattern or not pattern[0] or any(len(row)!=len(pattern[0]) for row in pattern):
      raise ValueError("unit pattern must be a nonempty rectangle")
    if any(ch not in ".13" for row in pattern for ch in row):
      raise ValueError("unit pattern may use only dot, 1 and 3")
    b, m = _pattern_cells(top, left, pattern)
    if not b or not m:
      raise ValueError('each unit needs blob and marker cells')
    for cell in b + m:
      if not (0 <= cell[0] < H and 0 <= cell[1] < W):
        raise ValueError('unit out of bounds')
      if cell in owner:
        raise ValueError('overlapping objects')
      owner[cell] = i
    if not _connected(b) or not _connected(m):
      raise ValueError('blob and marker must each be one component')
    if not any(x in _dilate(b) for x in m):
      raise ValueError('marker must touch its blob')
    got = _exit_of(b, m)
    if got is None or (ex is not None and ex != got):
      raise ValueError('marker side inconsistent with stated exit')
    objs.append({'blob': b, 'mark': m, 'exit': got})
  for i, u in enumerate(objs):
    for cell in _dilate(u['blob'] + u['mark']):
      o = owner.get(cell)
      if o is not None and o != i and o != -1:
        raise ValueError('units must be separated by background')
  beam = _trace(H, W, (r, c), dname, objs)
  return _paint(H, W, launch, objs, beam)


def generate(height=None, width=None, launcher=None, units=None,
             n_hits=None, n_distractors=None, direction=None):
  """Generate one input/output pair.

  Args:
    height: grid height (rows). Sampled in 14..30 if None; 10..30 if given.
    width: grid width (columns). Sampled in 14..30 if None; 10..30 if given.
    launcher: optional explicit (row, col, direction, tail_length) of the 4
      cell. The direction is the beam direction, and the tail of 2s lies
      behind it. Must be given together with units, height and width.
    units: optional explicit list of (top, left, pattern, exit). pattern is a
      list of strings using '1' for blob cells, '3' for marker cells and '.'
      for empty cells. exit is checked against the marker's side; None
      derives it. With launcher and units, the scene is rendered exactly and
      the beam is traced over these latent objects. This is used for fixture
      reconstruction.
    n_hits: exact number of chained blob hits for random scenes (0..4).
    n_distractors: exact number of untouched distractor units (0..3).
    direction: beam direction of the launcher for random scenes.
  """
  for name, v in (('height', height), ('width', width)):
    if v is not None and not 10 <= v <= 30:
      raise ValueError(name + ' must be in 10..30')
  if (launcher is None) != (units is None):
    raise ValueError('launcher and units must be given together')
  if launcher is not None:
    if height is None or width is None:
      raise ValueError('explicit scenes need height and width')
    if (n_hits is not None or n_distractors is not None or
        direction is not None):
      raise ValueError('n_hits/n_distractors/direction are random-only')
    return _render_explicit(height, width, launcher, units)
  if n_hits is not None and not 0 <= n_hits <= 4:
    raise ValueError('n_hits must be in 0..4')
  if n_distractors is not None and not 0 <= n_distractors <= 3:
    raise ValueError('n_distractors must be in 0..3')
  if direction is not None and direction not in DIRS:
    raise ValueError('direction must be up, down, left or right')
  for _ in range(400):
    H = height if height is not None else random.randint(14, 30)
    W = width if width is not None else random.randint(14, 30)
    k = n_hits if n_hits is not None else random.choice(N_HIT_CHOICES)
    nd = n_distractors if n_distractors is not None else random.randint(0, 3)
    if n_distractors is None and k == 0 and nd == 0:
      nd = 1
    dname = direction if direction is not None else random.choice(DIR_CHOICES)
    res = _construct(H, W, k, nd, dname)
    if res is not None:
      return res
  raise RuntimeError('could not construct a scene with the requested '
                     'parameters; try a larger grid or fewer objects')


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  up_t4 = ['.33.', '1111', '1111', '.11.']
  big_up = ['..33..', '.1111.', '111111', '111111', '.1111.', '..11..']
  train = [
      generate(height=13, width=15, launcher=(9, 8, 'up', 3), units=[
          (1, 1, ['.33.', '1111', '1111', '1111', '.11.'], 'up')]),
      generate(height=23, width=25, launcher=(20, 10, 'up', 2), units=[
          (3, 1, up_t4, 'up'),
          (3, 8, ['.11.', '1113', '1113', '.11.'], 'right'),
          (3, 18, up_t4, 'up'),
          (12, 7, ['..33..', '.1111.', '111111', '.1111.', '..11..'],
           'up')]),
      generate(height=23, width=22, launcher=(20, 16, 'up', 2), units=[
          (2, 2, ['..11..', '.1111.', '111111', '111111', '.1111.',
                  '..33..'], 'down'),
          (2, 14, ['..11..', '.1111.', '311111', '311111', '.1111.',
                   '..11..'], 'left'),
          (12, 2, ['..11..', '.1111.', '311111', '311111', '.1111.',
                   '..11..'], 'left')]),
      generate(height=23, width=22, launcher=(19, 5, 'up', 3), units=[
          (3, 2, ['..11..', '.1111.', '111113', '111113', '.1111.',
                  '..11..'], 'right'),
          (12, 13, ['.11.', '3111', '.11.'], 'left')]),
  ]
  test = [
      generate(height=27, width=27, launcher=(23, 5, 'up', 3), units=[
          (2, 1, ['..1111..', '.111111.', '11111111', '11111113',
                  '11111113', '11111111', '.111111.', '..1111..'], 'right'),
          (3, 14, big_up, 'up'),
          (12, 14, big_up, 'up')]),
  ]
  return {'train': train, 'test': test}
