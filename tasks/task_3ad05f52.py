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

"""ARC-GEN style generator for ARC task 3ad05f52.

Rule: walls of colour 8 form lattices of rectangular rooms. A door is a
one-cell gap in a wall, with wall on both sides of it. Exactly two rooms are
prefilled with a colour. Those two rooms are linked by a chain of rooms
joined through doors. Every room on that chain is filled with the colour,
and so is every door the chain uses. The chain may leave one wall structure,
cross the open background, and enter another structure. The open area is not
a room. Only the bounding-box stripe between its entry cell and its exit cell
is painted there.

Scope: one or two room lattices lie on the path. Each lattice has its own room
height and width (2..5) and its own number of rows and columns. A lattice may
be clipped by the grid border and may have missing boundary rooms. When there
are two lattices, their doors to the open area face each other across a
background gap of at least two cells. Distractors are optional: an
unconnected third lattice, and extra doors that link only off-path rooms. In
single-lattice scenes there may also be off-path doors to the outside. Scenes
are built in a canonical frame. Then one of the 8 dihedral transforms is
applied to both grids.

Random scenes may include dead-end branches attached to the route.
Distractor components cannot connect two route nodes, so the connecting path
remains unique. Not supported: multiple open-area crossings or irregular walls.
"""

import random

import common


_SIZES = (2, 3, 3, 3, 4, 4, 5)
_COLOURS = (1, 2, 3, 4, 5, 6, 7, 9)
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _miss(st):
  return {tuple(m) for m in st[6]}


def _room_rect(st, i, j):
  oy, ox, h, w = st[0], st[1], st[2], st[3]
  r0 = oy + 1 + i * (h + 1)
  c0 = ox + 1 + j * (w + 1)
  return r0, c0, r0 + h - 1, c0 + w - 1


def _clip(rect, height, width):
  r0, c0, r1, c1 = rect
  r0, c0 = max(r0, 0), max(c0, 0)
  r1, c1 = min(r1, height - 1), min(c1, width - 1)
  if r0 > r1 or c0 > c1:
    return None
  return r0, c0, r1, c1


def _extent(st):
  oy, ox, h, w, nr, nc = st[:6]
  return oy, ox, oy + nr * (h + 1), ox + nc * (w + 1)


def _draw(height, width, structures, dset):
  g = common.grid(width, height, 0)
  for st in structures:
    oy, ox, h, w, nr, nc = st[:6]
    miss = _miss(st)
    for i in range(nr):
      for j in range(nc):
        if (i, j) in miss:
          continue
        y0 = oy + i * (h + 1)
        y1 = y0 + h + 1
        x0 = ox + j * (w + 1)
        x1 = x0 + w + 1
        for y in range(max(y0, 0), min(y1, height - 1) + 1):
          for x in range(max(x0, 0), min(x1, width - 1) + 1):
            if y in (y0, y1) or x in (x0, x1):
              g[y][x] = 8
  for y, x in dset:
    g[y][x] = 0
  return g


def _paint(grid, structures, node, colour, height, width):
  s, i, j = node
  v = _clip(_room_rect(structures[s], i, j), height, width)
  if v is None:
    return
  for y in range(v[0], v[2] + 1):
    for x in range(v[1], v[3] + 1):
      grid[y][x] = colour


def _outside(st, node, door):
  r0, c0, r1, c1 = _room_rect(st, node[1], node[2])
  y, x = door

  def inside(c):
    return r0 <= c[0] <= r1 and c0 <= c[1] <= c1

  for a, b in (((y - 1, x), (y + 1, x)), ((y, x - 1), (y, x + 1))):
    if inside(a):
      return b
    if inside(b):
      return a
  return None


def _flood(g, start, dset, height, width):
  if start is None:
    return set()
  y, x = start
  if not (0 <= y < height and 0 <= x < width) or g[y][x] != 0:
    return set()
  seen = {start}
  stack = [start]
  while stack:
    cy, cx = stack.pop()
    for dy, dx in _DIRS:
      ny, nx = cy + dy, cx + dx
      if (0 <= ny < height and 0 <= nx < width and g[ny][nx] == 0 and
          (ny, nx) not in dset and (ny, nx) not in seen):
        seen.add((ny, nx))
        stack.append((ny, nx))
  return seen


def _render(height, width, colour, structures, path, doors, extra):
  dset = set(doors) | set(extra)
  g = _draw(height, width, structures, dset)
  _paint(g, structures, path[0], colour, height, width)
  _paint(g, structures, path[-1], colour, height, width)
  out = [row[:] for row in g]
  for k, node in enumerate(path):
    if node is None:
      e1 = _outside(structures[path[k - 1][0]], path[k - 1], doors[k - 1])
      e2 = _outside(structures[path[k + 1][0]], path[k + 1], doors[k])
      comp = _flood(g, e1, dset, height, width)
      if e1 is None or e2 is None:
        continue
      for y in range(min(e1[0], e2[0]), max(e1[0], e2[0]) + 1):
        for x in range(min(e1[1], e2[1]), max(e1[1], e2[1]) + 1):
          if (y, x) in comp:
            out[y][x] = colour
    else:
      _paint(out, structures, node, colour, height, width)
  for y, x in doors:
    out[y][x] = colour
  return g, out


def _pred(g, y, x, height, width):
  if g[y][x] == 8:
    return None

  def wall(a, b):
    return 0 <= a < height and 0 <= b < width and g[a][b] == 8

  if wall(y, x - 1) and wall(y, x + 1):
    return ((y - 1, x), (y + 1, x))
  if wall(y - 1, x) and wall(y + 1, x):
    return ((y, x - 1), (y, x + 1))
  return None


def _valid(height, width, g, structures, path, doors, extra):
  """Local scene-consistency checks (independent of any reference solver)."""
  dset = set(doors) | set(extra)
  if len(dset) != len(doors) + len(extra):
    return False
  pred = {}
  for y in range(height):
    for x in range(width):
      p = _pred(g, y, x, height, width)
      if p is not None:
        pred[(y, x)] = p
  if set(pred) != dset:
    return False
  lab = [[-1] * width for _ in range(height)]
  members = []
  for y in range(height):
    for x in range(width):
      if g[y][x] == 8 or (y, x) in dset or lab[y][x] >= 0:
        continue
      idx = len(members)
      cells = [(y, x)]
      lab[y][x] = idx
      k = 0
      while k < len(cells):
        cy, cx = cells[k]
        k += 1
        for dy, dx in _DIRS:
          ny, nx = cy + dy, cx + dx
          if (0 <= ny < height and 0 <= nx < width and g[ny][nx] != 8 and
              (ny, nx) not in dset and lab[ny][nx] < 0):
            lab[ny][nx] = idx
            cells.append((ny, nx))
      members.append(cells)
  for st in structures:
    miss = _miss(st)
    for i in range(st[4]):
      for j in range(st[5]):
        if (i, j) in miss:
          continue
        v = _clip(_room_rect(st, i, j), height, width)
        if v is None:
          continue
        r0, c0, r1, c1 = v
        l = lab[r0][c0]
        if l < 0 or len(members[l]) != (r1 - r0 + 1) * (c1 - c0 + 1):
          return False
        for y in range(r0, r1 + 1):
          for x in range(c0, c1 + 1):
            if lab[y][x] != l:
              return False
  boxes = []
  seen = set()
  for y in range(height):
    for x in range(width):
      if g[y][x] != 8 or (y, x) in seen:
        continue
      seen.add((y, x))
      stack = [(y, x)]
      box = [y, x, y, x]
      while stack:
        cy, cx = stack.pop()
        box = [min(box[0], cy), min(box[1], cx), max(box[2], cy),
               max(box[3], cx)]
        for dy in (-1, 0, 1):
          for dx in (-1, 0, 1):
            ny, nx = cy + dy, cx + dx
            if (0 <= ny < height and 0 <= nx < width and g[ny][nx] == 8 and
                (ny, nx) not in seen):
              seen.add((ny, nx))
              stack.append((ny, nx))
      boxes.append(box)

  def inside_any(y, x):
    return any(b[0] <= y <= b[2] and b[1] <= x <= b[3] for b in boxes)

  plabs = []
  for k, node in enumerate(path):
    if node is None:
      if k == 0 or k == len(path) - 1:
        return False
      e1 = _outside(structures[path[k - 1][0]], path[k - 1], doors[k - 1])
      e2 = _outside(structures[path[k + 1][0]], path[k + 1], doors[k])
      for e in (e1, e2):
        if e is None or not (0 <= e[0] < height and 0 <= e[1] < width):
          return False
        if lab[e[0]][e[1]] < 0:
          return False
      l = lab[e1[0]][e1[1]]
      if lab[e2[0]][e2[1]] != l:
        return False
      if all(inside_any(y, x) for y, x in members[l]):
        return False
      for y in range(min(e1[0], e2[0]), max(e1[0], e2[0]) + 1):
        for x in range(min(e1[1], e2[1]), max(e1[1], e2[1]) + 1):
          if lab[y][x] != l:
            return False
      plabs.append(l)
    else:
      s, i, j = node
      st = structures[s]
      if not (0 <= i < st[4] and 0 <= j < st[5]) or (i, j) in _miss(st):
        return False
      v = _clip(_room_rect(st, i, j), height, width)
      if v is None:
        return False
      if not any(b[0] <= v[0] and v[2] <= b[2] and b[1] <= v[1] and
                 v[3] <= b[3] for b in boxes):
        return False
      plabs.append(lab[v[0]][v[1]])
  if len(set(plabs)) != len(plabs):
    return False

  def door_labs(d):
    res = []
    for y, x in pred[d]:
      if not (0 <= y < height and 0 <= x < width) or lab[y][x] < 0:
        return None
      res.append(lab[y][x])
    return res

  for k, d in enumerate(doors):
    labs = door_labs(d)
    if labs is None or set(labs) != {plabs[k], plabs[k + 1]}:
      return False
  pset = set(plabs)
  extra_adj={}
  for d in extra:
    labs = door_labs(d)
    if labs is None or labs[0] == labs[1]:
      return False
    if labs[0] in pset and labs[1] in pset:
      return False
    extra_adj.setdefault(labs[0],set()).add(labs[1])
    extra_adj.setdefault(labs[1],set()).add(labs[0])
  visited=set()
  for root in extra_adj:
    if root in visited:continue
    comp={root};stack=[root];visited.add(root)
    while stack:
      for nb in extra_adj[stack.pop()]:
        if nb not in visited:visited.add(nb);comp.add(nb);stack.append(nb)
    # A distractor component may attach once but cannot shortcut the route.
    if len(comp & pset)>1:return False
  return True


def _door_opts(st, i, j, di, dj, height, width):
  r0, c0, r1, c1 = _room_rect(st, i, j)
  opts = []
  if di != 0:
    y = r1 + 1 if di == 1 else r0 - 1
    if y - 1 < 0 or y + 1 > height - 1:
      return []
    for x in range(max(c0, 1), min(c1, width - 2) + 1):
      opts.append((y, x))
  else:
    x = c1 + 1 if dj == 1 else c0 - 1
    if x - 1 < 0 or x + 1 > width - 1:
      return []
    for y in range(max(r0, 1), min(r1, height - 2) + 1):
      opts.append((y, x))
  return opts


def _visible(st, cell, height, width):
  return _clip(_room_rect(st, cell[0], cell[1]), height, width) is not None


def _walk(st, start, target, height, width):
  cells = [start]
  ds = []
  seen = {start}
  while len(cells) < target:
    i, j = cells[-1]
    cands = []
    for di, dj in _DIRS:
      n = (i + di, j + dj)
      if not (0 <= n[0] < st[4] and 0 <= n[1] < st[5]) or n in seen:
        continue
      if not _visible(st, n, height, width):
        continue
      opts = _door_opts(st, i, j, di, dj, height, width)
      if opts:
        cands.append((n, opts))
    if not cands:
      break
    n, opts = random.choice(cands)
    cells.append(n)
    ds.append(random.choice(opts))
    seen.add(n)
  return cells, ds


def _connected(cells):
  cells = set(cells)
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    i, j = stack.pop()
    for di, dj in _DIRS:
      n = (i + di, j + dj)
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _remove(st, keep):
  nr, nc = st[4], st[5]
  allc = {(i, j) for i in range(nr) for j in range(nc)}
  boundary = [c for c in sorted(allc)
              if (c[0] in (0, nr - 1) or c[1] in (0, nc - 1)) and
              c not in keep]
  random.shuffle(boundary)
  k = random.randint(1, 3)
  miss = set()
  for c in boundary:
    if len(miss) >= k:
      break
    trial = miss | {c}
    rest = allc - trial
    if rest and _connected(rest):
      miss = trial
  return sorted(miss)


def _place_axis(length, size, nmin, nmax):
  maxn = min((length + size - 1) // (size + 1), nmax)
  if maxn < nmin:
    return None
  n = random.randint(nmin, maxn)
  ext = n * (size + 1) + 1
  if ext <= length and random.random() < 0.6:
    o = random.randint(0, length - ext)
  else:
    o = random.randint(-size, length - ext + size)
  return o, n


def _separated(a, b):
  dy = max(b[0] - a[2], a[0] - b[2]) - 1
  dx = max(b[1] - a[3], a[1] - b[3]) - 1
  return dy >= 2 or dx >= 2


def _sample_distractor(height, width, structures):
  for _ in range(10):
    h, w = random.choice(_SIZES), random.choice(_SIZES)
    ay = _place_axis(height, h, 1, 3)
    ax = _place_axis(width, w, 1, 3)
    if ay is None or ax is None:
      continue
    st = [ay[0], ax[0], h, w, ay[1], ax[1], []]
    if all(_separated(_extent(st), _extent(o)) for o in structures):
      return st
  return None


def _extra_doors(structures, keep, height, width, outer):
  cands = []
  for s, st in enumerate(structures):
    pc = keep.get(s, set())
    miss = _miss(st)
    nr, nc = st[4], st[5]
    for i in range(nr):
      for j in range(nc):
        if (i, j) in miss or (i, j) in pc:
          continue
        if not _visible(st, (i, j), height, width):
          continue
        for di, dj in ((1, 0), (0, 1)):
          n = (i + di, j + dj)
          if (n[0] < nr and n[1] < nc and n not in miss and n not in pc and
              _visible(st, n, height, width)):
            opts = _door_opts(st, i, j, di, dj, height, width)
            if opts:
              cands.append(opts)
        if outer:
          for di, dj in _DIRS:
            n = (i + di, j + dj)
            if not (0 <= n[0] < nr and 0 <= n[1] < nc):
              opts = _door_opts(st, i, j, di, dj, height, width)
              if opts:
                cands.append(opts)
  random.shuffle(cands)
  m = random.randint(0, 3)
  return [random.choice(o) for o in cands[:m]]


def _sample_single(requested_height,requested_width):
  height = requested_height if requested_height is not None else random.randint(10,30)
  width = requested_width if requested_width is not None else random.randint(10,30)
  h, w = random.choice(_SIZES), random.choice(_SIZES)
  ay = _place_axis(height, h, 1, 5)
  ax = _place_axis(width, w, 1, 6)
  if ay is None or ax is None or ay[1] * ax[1] < 3:
    return None
  st = [ay[0], ax[0], h, w, ay[1], ax[1], []]
  rooms = [(i, j) for i in range(st[4]) for j in range(st[5])
           if _visible(st, (i, j), height, width)]
  if len(rooms) < 3:
    return None
  start = random.choice(rooms)
  cells, ds = _walk(st, start, random.randint(3, min(10, len(rooms))),
                    height, width)
  if len(cells) < 3:
    return None
  keep = set(cells)
  if random.random() < 0.4:
    st[6] = _remove(st, keep)
  structures = [st]
  if random.random() < 0.4:
    c = _sample_distractor(height, width, structures)
    if c is not None:
      structures.append(c)
  path = [(0, i, j) for i, j in cells]
  extra = _extra_doors(structures, {0: keep}, height, width,
                       random.random() < 0.3)
  return height, width, structures, path, ds, extra


def _sample_double(requested_height,requested_width):
  ha, wa = random.choice(_SIZES), random.choice(_SIZES)
  if random.random() < 0.4:
    hb, wb = ha, wa
  else:
    hb, wb = random.choice(_SIZES), random.choice(_SIZES)
  nra, nrb = random.randint(1, 3), random.randint(1, 3)
  exta = nra * (ha + 1) + 1
  extb = nrb * (hb + 1) + 1
  gap = random.randint(2, 6)
  if random.random() < 0.35:
    oya = -random.randint(1, ha)
  else:
    oya = random.randint(0, 3)
  oyb = oya + exta + gap
  if random.random() < 0.35:
    bottom = -random.randint(1, hb)
  else:
    bottom = random.randint(0, 3)
  height = requested_height if requested_height is not None else oyb + extb + bottom
  if height < 10 or height > 30:
    return None
  width = requested_width if requested_width is not None else random.randint(10,30)
  axa = _place_axis(width, wa, 1, 6)
  axb = _place_axis(width, wb, 1, 6)
  if axa is None or axb is None:
    return None
  sta = [oya, axa[0], ha, wa, nra, axa[1], []]
  stb = [oyb, axb[0], hb, wb, nrb, axb[1], []]
  exits = []
  for j in range(sta[5]):
    if _visible(sta, (nra - 1, j), height, width):
      opts = _door_opts(sta, nra - 1, j, 1, 0, height, width)
      if opts:
        exits.append((j, opts))
  entries = []
  for j in range(stb[5]):
    if _visible(stb, (0, j), height, width):
      opts = _door_opts(stb, 0, j, -1, 0, height, width)
      if opts:
        entries.append((j, opts))
  if not exits or not entries:
    return None
  ja, opts = random.choice(exits)
  exit_door = random.choice(opts)
  jb, opts = random.choice(entries)
  entry_door = random.choice(opts)
  cells_a, da = _walk(sta, (nra - 1, ja), random.randint(1, 6), height, width)
  cells_b, db = _walk(stb, (0, jb), random.randint(1, 6), height, width)
  path = ([(0, i, j) for i, j in reversed(cells_a)] + [None] +
          [(1, i, j) for i, j in cells_b])
  doors = list(reversed(da)) + [exit_door, entry_door] + db
  keep = {0: set(cells_a), 1: set(cells_b)}
  for s, st in enumerate((sta, stb)):
    if random.random() < 0.4:
      st[6] = _remove(st, keep[s])
  structures = [sta, stb]
  if random.random() < 0.3:
    c = _sample_distractor(height, width, structures)
    if c is not None:
      structures.append(c)
  extra = _extra_doors(structures, keep, height, width, False)
  return height, width, structures, path, doors, extra


def _branch_door(structures,path,doors,extra,height,width):
  """Add one dead-end attachment to the route, without a second connection."""
  keep={}
  for node in path:
    if node is not None:keep.setdefault(node[0],set()).add(tuple(node[1:]))
  options=[]
  for si,cells in keep.items():
    st=structures[si];missing=_miss(st)
    for i,j in sorted(cells):
      for di,dj in _DIRS:
        n=(i+di,j+dj)
        if not (0<=n[0]<st[4] and 0<=n[1]<st[5]) or n in cells or n in missing:continue
        if not _visible(st,n,height,width):continue
        options.extend(d for d in _door_opts(st,i,j,di,dj,height,width) if d not in doors and d not in extra)
  return random.choice(options) if options else None


def _sample_scene(colour,requested_height,requested_width,layout_mode,branches):
  for _ in range(500):
    mode=layout_mode if layout_mode is not None else random.choice(("double","double","single"))
    if mode=="double":scene=_sample_double(requested_height,requested_width)
    else:scene=_sample_single(requested_height,requested_width)
    if scene is None:
      continue
    height, width, structures, path, doors, extra = scene
    if branches:
      d=_branch_door(structures,path,doors,extra,height,width)
      if d is None:continue
      extra=extra+[d]
    col = colour if colour is not None else random.choice(_COLOURS)
    g, out = _render(height, width, col, structures, path, doors, extra)
    if g != out and _valid(height, width, g, structures, path, doors, extra):
      return height, width, col, structures, path, doors, extra
  raise RuntimeError("Could not construct requested room path")


def _xform(grid, t):
  g = [row[:] for row in grid]
  if t & 4:
    g = [list(r) for r in zip(*g)]
  if t & 1:
    g = g[::-1]
  if t & 2:
    g = [r[::-1] for r in g]
  return g


def generate(height=None, width=None, colour=None, structures=None,
             path=None, doors=None, extra_doors=None, transform=None,
             layout_mode=None, branches=None):
  """Returns an input/output pair for task 3ad05f52.

  Args:
    height: exact native grid height, before dihedral transform.
    width: exact native grid width, before dihedral transform.
    colour: fill colour of the two marked rooms (never 0 or 8).
    structures: list of wall lattices (oy, ox, h, w, nr, nc, missing).
      (oy, ox) is the top-left wall corner and may lie off-grid. h and w are
      the room height and width. nr and nc are the lattice row and column
      counts. missing lists the (i, j) rooms that are absent.
    path: chain of nodes from one marked room to the other. Each node is
      (structure index, i, j), or None for the open background area.
    doors: door cells (y, x) between consecutive path nodes.
    extra_doors: distractor door cells that join only off-path rooms.
    transform: dihedral index 0..7 applied to both grids. It is random for
      sampled scenes and defaults to 0 for explicit scenes.
    layout_mode: single or double path lattice (random if None).
    branches: add a dead-end route attachment; random boolean if None.
  """
  for dimension in (height,width):
    if dimension is not None and (not isinstance(dimension,int) or not 1<=dimension<=30):raise ValueError("Dimensions must be in 1..30")
  if colour is not None and colour not in _COLOURS:raise ValueError("Fill colour cannot be 0 or 8")
  if transform is not None and (not isinstance(transform,int) or not 0<=transform<=7):raise ValueError("transform must be in 0..7")
  if layout_mode not in (None,"single","double"):raise ValueError("Unknown layout_mode")
  if structures is None:
    if any(v is not None for v in (path,doors,extra_doors)):raise ValueError("Explicit path and doors require structures")
    if any(d is not None and d<10 for d in (height,width)):raise ValueError("Random dimensions must be at least 10")
    branch_choice=branches if branches is not None else random.random()<0.5
    height,width,colour,structures,path,doors,extra_doors=_sample_scene(colour,height,width,layout_mode,branch_choice)
    if transform is None:
      transform = random.randint(0, 7)
  elif layout_mode is not None or branches is not None:
    raise ValueError("Sampling controls cannot accompany explicit structures")
  if height is None or width is None or colour is None or not structures or not path or doors is None:
    raise ValueError("Explicit structures require complete geometry and path")
  for st in structures:
    if len(st)!=7 or any(not isinstance(v,int) for v in st[:6]) or any(not 1<=v<=30 for v in st[2:6]):raise ValueError("Invalid lattice geometry")
    if any(not (0<=i<st[4] and 0<=j<st[5]) for i,j in st[6]):raise ValueError("Invalid missing room")
  if len(path)<2 or path[0] is None or path[-1] is None or len(doors)!=len(path)-1 or path.count(None)>1:
    raise ValueError("Invalid path endpoints or door count")
  for node in path:
    if node is not None:
      si,i,j=node
      if not (0<=si<len(structures) and 0<=i<structures[si][4] and 0<=j<structures[si][5]) or (i,j) in _miss(structures[si]):raise ValueError("Invalid path node")
  if any(not (0<=r<height and 0<=c<width) for r,c in list(doors)+list(extra_doors or [])):raise ValueError("Door outside grid")
  if transform is None:
    transform = 0
  path = [None if n is None else tuple(n) for n in path]
  doors = [tuple(d) for d in doors]
  extra_doors = [tuple(d) for d in (extra_doors or [])]
  grid_in, grid_out = _render(height, width, colour, structures, path, doors,
                              extra_doors)
  return {"input": _xform(grid_in, transform),
          "output": _xform(grid_out, transform)}


def validate():
  """Rebuilds the canonical pairs from explicit latent parameters."""
  train = [
      generate(
          height=22, width=26, colour=6,
          structures=[(3, 2, 3, 3, 2, 5, [(1, 0), (1, 2), (1, 3), (1, 4)]),
                      (14, 6, 3, 3, 2, 3, [(1, 0)])],
          path=[(0, 0, 4), (0, 0, 3), (0, 0, 2), (0, 0, 1), (0, 1, 1), None,
                (1, 0, 0), (1, 0, 1), (1, 0, 2), (1, 1, 2), (1, 1, 1)],
          doors=[(5, 18), (5, 14), (5, 10), (7, 8), (11, 8), (14, 8),
                 (16, 10), (16, 14), (18, 16), (20, 14)]),
      generate(
          height=29, width=24, colour=4,
          structures=[(-1, 3, 3, 3, 8, 2, []), (-1, 18, 3, 3, 8, 2, [])],
          path=[(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 2, 1), (0, 3, 1),
                (0, 4, 1), (0, 4, 0), (0, 5, 0), (0, 5, 1), None, (1, 2, 0),
                (1, 3, 0), (1, 4, 0), (1, 5, 0), (1, 5, 1)],
          doors=[(3, 5), (5, 7), (7, 9), (11, 9), (15, 9), (17, 7), (19, 5),
                 (21, 7), (21, 11), (9, 18), (11, 20), (15, 20), (19, 20),
                 (21, 22)]),
      generate(
          height=24, width=28, colour=3,
          structures=[(1, 2, 5, 5, 3, 2, []), (7, 19, 3, 3, 3, 1, [])],
          path=[(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 2, 1), None, (1, 0, 0),
                (1, 1, 0)],
          doors=[(4, 8), (7, 11), (13, 11), (16, 14), (9, 19), (11, 21)]),
  ]
  test = [
      generate(
          height=28, width=28, colour=2,
          structures=[(2, 0, 3, 3, 2, 7, []), (17, 6, 4, 4, 2, 4, [(0, 3)])],
          path=[(0, 0, 5), (0, 1, 5), (0, 1, 4), (0, 0, 4), (0, 0, 3),
                (0, 0, 2), (0, 0, 1), (0, 1, 1), (0, 1, 2), None, (1, 0, 2),
                (1, 0, 1), (1, 0, 0), (1, 1, 0), (1, 1, 1)],
          doors=[(6, 22), (8, 20), (6, 18), (4, 16), (4, 12), (4, 8), (6, 6),
                 (8, 8), (10, 10), (17, 19), (20, 16), (19, 11), (22, 9),
                 (25, 11)]),
  ]
  return {"train": train, "test": test}
