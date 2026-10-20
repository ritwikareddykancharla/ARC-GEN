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

"""ARC task 332f06d7: slide a square block through a walled corridor.

Rule: the grid has walls (3), a corridor (1), an s x s mover block (0) and
an s x s goal block (2). The mover slides through the corridor. Every cell it
covers must be non-wall and inside the grid. If it can reach the goal
position, it replaces the goal block there. Otherwise it stops at the unique
reachable position farthest from its start, measured in unit slide steps.
In both cases its old cells become corridor colour 1.

Scope of the random generator (tree or widened-room topology):
* Block size is 1..4.
* Lattice coordinates are random with an irregular pitch of at least s+1.
* A random tree is grown on the lattice. Each tree node and edge is carved
  as a tube exactly s cells wide, with at least one wall between
  non-incident tubes.
* The mover starts at one leaf and the goal sits at another leaf.
* Either leaf may be pushed flush against the grid edge.
* Widened-room topology adds rectangular/staircase rooms and optional cycles.
* Narrow dead-end spurs (width < s) are added as distractors.
* In the unreachable case (s >= 2), one edge on the start-to-goal path is
  carved as a strip narrower than s. The block then stops at the farthest
  position of its own component, which is required to be unique.

Fixture replay uses explicit latent arguments: a wall layout, the block size
and the start and goal top-left corners.
"""

import random
from collections import deque

import common

WALL, PATH, MOVER, GOAL = 3, 1, 0, 2
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _slide(openm, s, start, goal):
  """Search over block top-left positions from the mover's start.

  Returns (destination, goal_reached, farthest_is_unique).
  """
  h, w = len(openm), len(openm[0])

  def ok(y, x):
    if y < 0 or x < 0 or y + s > h or x + s > w:
      return False
    for a in range(s):
      row = openm[y + a]
      for b in range(s):
        if not row[x + b]:
          return False
    return True

  if not ok(*start) or not ok(*goal):
    raise ValueError("Start and goal must fit fully inside the open layout")
  dist = {start: 0}
  order = [start]
  queue = deque([start])
  while queue:
    y, x = queue.popleft()
    for dy, dx in DIRS:
      n = (y + dy, x + dx)
      if n not in dist and ok(*n):
        dist[n] = dist[(y, x)] + 1
        order.append(n)
        queue.append(n)
  if goal in dist:
    return goal, True, True
  far = max(dist.values())
  cands = [p for p in order if dist[p] == far]
  return cands[0], False, len(cands) == 1


def _render(openm, s, start, goal, dest):
  h, w = len(openm), len(openm[0])
  grid = common.grid(w, h, WALL)
  for r in range(h):
    for c in range(w):
      if openm[r][c]:
        grid[r][c] = PATH
  for a in range(s):
    for b in range(s):
      grid[goal[0] + a][goal[1] + b] = GOAL
  for a in range(s):
    for b in range(s):
      grid[start[0] + a][start[1] + b] = MOVER
  out = [row[:] for row in grid]
  for a in range(s):
    for b in range(s):
      out[start[0] + a][start[1] + b] = PATH
  for a in range(s):
    for b in range(s):
      out[dest[0] + a][dest[1] + b] = MOVER
  return {"input": grid, "output": out}


def _axis(s, lo, limit):
  coords = [1 + lo]
  while len(coords) < 8:
    p = s + 1 + random.choice((0, 0, 1, 1, 2, 3))
    if coords[-1] + p + s + 1 > limit:
      break
    coords.append(coords[-1] + p)
  return coords


def _random_scene(s, reachable, width, height, topology):
  for _ in range(400):
    lo_lim = min(30, 3 * s + 4)
    lim_h = height if height is not None else random.randint(lo_lim, 30)
    lim_w = width if width is not None else random.randint(lo_lim, 30)
    mt = random.choice((0, 0, 1))
    ml = random.choice((0, 0, 1))
    rows = _axis(s, mt, lim_h)
    cols = _axis(s, ml, lim_w)
    nr, nc = len(rows), len(cols)
    if nr * nc < 3:
      continue
    mb = random.randint(0, max(0, min(2, lim_h - (rows[-1] + s + 1))))
    mr = random.randint(0, max(0, min(2, lim_w - (cols[-1] + s + 1))))
    h, w = lim_h, lim_w
    mb = h - (rows[-1] + s + 1)
    mr = w - (cols[-1] + s + 1)
    if h > 30 or w > 30:
      continue
    # Grow a random tree on the lattice.
    target = random.randint(3, min(nr * nc, 14))
    root = (random.randrange(nr), random.randrange(nc))
    tree = {root}
    adj = {root: set()}
    last = root
    for _ in range(300):
      if len(tree) >= target:
        break
      base = last if random.random() < 0.7 else random.choice(sorted(tree))
      nbrs = []
      for dy, dx in DIRS:
        n = (base[0] + dy, base[1] + dx)
        if 0 <= n[0] < nr and 0 <= n[1] < nc and n not in tree:
          nbrs.append(n)
      if not nbrs:
        continue
      nxt = random.choice(nbrs)
      tree.add(nxt)
      adj[nxt] = {base}
      adj[base].add(nxt)
      last = nxt
    if len(tree) < 3:
      continue
    leaves = sorted(n for n in tree if len(adj[n]) == 1)
    if len(leaves) < 2:
      continue
    start_n, goal_n = random.sample(leaves, 2)
    # Tree path from the start leaf to the goal leaf.
    par = {start_n: None}
    q = deque([start_n])
    while q:
      a = q.popleft()
      for b in adj[a]:
        if b not in par:
          par[b] = a
          q.append(b)
    path = [goal_n]
    while par[path[-1]] is not None:
      path.append(par[path[-1]])
    path.reverse()
    narrow = None
    if not reachable:
      if len(path) < 3:
        continue
      k = random.randint(1, len(path) - 2)
      narrow = {path[k], path[k + 1]}

    openm = [[False] * w for _ in range(h)]

    def carve(r0, r1, c0, c1):
      for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
          openm[r][c] = True

    for (i, j) in tree:
      carve(rows[i], rows[i] + s - 1, cols[j], cols[j] + s - 1)
    slots = set()
    for a in sorted(tree):
      for b in sorted(adj[a]):
        if not a < b:
          continue
        slots.add((a, b))
        (i1, j1), (i2, j2) = a, b
        thin = narrow is not None and {a, b} == narrow
        if thin:
          wd = random.randint(1, s - 1)
          off = random.randint(0, s - wd)
        else:
          wd, off = s, 0
        if i1 == i2:
          carve(rows[i1] + off, rows[i1] + off + wd - 1,
                cols[j1] + s, cols[j2] - 1)
        else:
          carve(rows[i1] + s, rows[i2] - 1,
                cols[j1] + off, cols[j1] + off + wd - 1)

    margins = {(-1, 0): mt, (1, 0): mb, (0, -1): ml, (0, 1): mr}

    def outward(node):
      i, j = node
      res = []
      if i == 0 and mt == 0:
        res.append((-1, 0))
      if i == nr - 1 and mb == 0:
        res.append((1, 0))
      if j == 0 and ml == 0:
        res.append((0, -1))
      if j == nc - 1 and mr == 0:
        res.append((0, 1))
      return res

    used = set()
    pos = {}
    for node, prob in ((start_n, 0.25), (goal_n, 0.4)):
      p = (rows[node[0]], cols[node[1]])
      outs = outward(node)
      if outs and random.random() < prob:
        d = random.choice(outs)
        p = (p[0] + d[0], p[1] + d[1])
        carve(p[0], p[0] + s - 1, p[1], p[1] + s - 1)
        used.add((node, d))
      pos[node] = p

    if s >= 2:
      for _ in range(random.randint(0, 3)):
        node = random.choice(sorted(tree))
        d = random.choice(DIRS)
        if (node, d) in used:
          continue
        nb = (node[0] + d[0], node[1] + d[1])
        if nb in adj[node]:
          continue
        inside = 0 <= nb[0] < nr and 0 <= nb[1] < nc
        slot = None
        if inside:
          slot = (min(node, nb), max(node, nb))
          if slot in slots:
            continue
          if d[0]:
            gap = abs(rows[nb[0]] - rows[node[0]])
          else:
            gap = abs(cols[nb[1]] - cols[node[1]])
          maxlen = gap - s - 1
        else:
          maxlen = margins[d]
        if maxlen < 1:
          continue
        ln = random.randint(1, maxlen)
        wd = random.randint(1, s - 1)
        off = random.randint(0, s - wd)
        r, c = rows[node[0]], cols[node[1]]
        if d == (0, 1):
          carve(r + off, r + off + wd - 1, c + s, c + s + ln - 1)
        elif d == (0, -1):
          carve(r + off, r + off + wd - 1, c - ln, c - 1)
        elif d == (1, 0):
          carve(r + s, r + s + ln - 1, c + off, c + off + wd - 1)
        else:
          carve(r - ln, r - 1, c + off, c + off + wd - 1)
        if slot is not None:
          slots.add(slot)
        used.add((node, d))

    if topology == "rooms":
      # Widen selected junctions, with optional staircase-shaped boundaries.
      # These can create alternate paths; reachability and unique stopping are
      # checked below after all edits, not assumed from the original tree.
      nodes = sorted(tree)
      for node in random.sample(nodes, min(len(nodes), random.randint(1, 4))):
        r, c = rows[node[0]], cols[node[1]]
        up, down, left, right = [random.randint(1, s+2) for _ in range(4)]
        y0, y1 = max(0,r-up), min(h-1,r+s-1+down)
        x0, x1 = max(0,c-left), min(w-1,c+s-1+right)
        staircase = random.random() < 0.5
        for y in range(y0,y1+1):
          trim = min(max(0,r-y),max(0,(x1-x0-s)//2)) if staircase else 0
          carve(y,y,x0+trim,x1-trim)
      # Join some nearby tree nodes that did not previously share an edge.
      extra = [(a,b) for a in nodes for b in nodes if a < b and b not in adj[a]
               and abs(a[0]-b[0])+abs(a[1]-b[1]) == 1]
      for a,b in random.sample(extra,min(len(extra),random.randint(0,2))):
        if a[0] == b[0]:
          carve(rows[a[0]],rows[a[0]]+s-1,cols[a[1]],cols[b[1]]+s-1)
        else:
          carve(rows[a[0]],rows[b[0]]+s-1,cols[a[1]],cols[a[1]]+s-1)

    start = pos[start_n]
    goal = pos[goal_n]
    dest, reached, unique = _slide(openm, s, start, goal)
    if reached != reachable or not unique or dest == start:
      continue
    return openm, start, goal, dest
  raise RuntimeError("could not build a valid corridor scene")


def generate(size=None, reachable=None, layout=None, start=None, goal=None,
             width=None, height=None, topology=None):
  """Build one input/output pair.

  Args:
    size: side length s of the square mover and goal blocks (1..4).
    reachable: whether the goal can be reached. s=1 is always reachable.
    width, height: exact canvas dimensions, random minimum 3*size+4.
    topology: "tree" or "rooms" (random mixture); rooms may add cycles.
    layout: optional list of strings, '#' for wall and '.' for open, with the
      block cells marked open. Used to replay the original fixtures.
    start: (row, col) top-left of the mover block when layout is given.
    goal: (row, col) top-left of the goal block when layout is given.
  """
  if size is not None and (not isinstance(size,int) or not 1 <= size <= 4):
    raise ValueError("size must be in 1..4")
  if topology not in (None,"tree","rooms"):
    raise ValueError("Unknown topology")
  for d in (width,height):
    if d is not None and (not isinstance(d,int) or not 1 <= d <= 30):
      raise ValueError("Dimensions must be in 1..30")
  if layout is not None:
    if size is None or start is None or goal is None:
      raise ValueError("Explicit layout requires size, start and goal")
    if not layout or not layout[0] or max(len(layout),len(layout[0])) > 30 or any(len(row)!=len(layout[0]) or any(ch not in '.#' for ch in row) for row in layout):
      raise ValueError("Layout must be rectangular using only . and #")
    if (height is not None and height != len(layout)) or (width is not None and width != len(layout[0])):
      raise ValueError("Layout does not match requested dimensions")
    if topology is not None:
      raise ValueError("topology applies only to random construction")
    if len(start)!=2 or len(goal)!=2 or any(not isinstance(x,int) for x in list(start)+list(goal)):
      raise ValueError("Positions must be integer coordinate pairs")
    if abs(start[0]-goal[0]) < size and abs(start[1]-goal[1]) < size:
      raise ValueError("Mover and goal must not overlap")
    openm = [[ch == "." for ch in row] for row in layout]
    start, goal = tuple(start), tuple(goal)
    dest, reached, _ = _slide(openm, size, start, goal)
    if reachable is not None and reached != reachable:
      raise ValueError("Requested reachability does not match layout")
    return _render(openm, size, start, goal, dest)
  if start is not None or goal is not None:
    raise ValueError("Explicit positions require layout")
  if size is None:
    if reachable is False:
      size = random.choice((2, 2, 3, 3, 4))
    else:
      size = random.choice((1, 2, 2, 3, 3, 4))
  if reachable is None:
    reachable = True if size == 1 else random.random() < 0.5
  if size == 1 and not reachable:
    raise ValueError("Random unreachable scenes require size >= 2")
  if any(d is not None and d < 3*size+4 for d in (width,height)):
    raise ValueError("Random dimensions must be at least 3*size+4")
  topology = topology if topology is not None else random.choice(("tree","rooms"))
  openm, start, goal, dest = _random_scene(size, reachable, width, height, topology)
  return _render(openm, size, start, goal, dest)


def validate():
  """Reconstruct the canonical fixtures from explicit latent layouts."""
  l1 = ["#..#########", "#..#########", "#..#########", "#..#......##",
        "#..#......##", "#..#..#...##", "#..#..#....#", "#.....#....#",
        "#.....##..##", "#...####..##", "########..##", "############"]
  l2 = ["##############", "##############", "#####.......##",
        "#####.......##", "#####..#######", "#####..#######",
        "#####..#######", "#####.....####", "#####.....####",
        "#########.####", "#.........####", "#.........####",
        "#..###########", "#..###########"]
  l3 = ["################", "...............#", ".......##......#",
        ".....#####.....#", "#############..#", "###.......###..#",
        "###.......###..#", "###.......###..#", "##....#...###..#",
        "##....#..###...#", "##....#..###...#", "##...##..###...#",
        "#....##........#", "#....##........#", "#....##........#",
        "################"]
  l4 = ["##########", "#...######", "###.#...##", "###.#.#.##",
        "###...#.##", "#######.##", "####....##", "####.#####",
        "####.#####", "####.#####"]
  lt = ["####################", "#.......######.....#",
        "#..................#", "#..................#",
        "#..................#", "#....#########.....#",
        "#............##....#", "#............###...#",
        "#............####..#", "#............####..#",
        "#########....###...#", "#.......#....##....#",
        "#.......#....##....#", "#.......#.....#....#",
        "#.......#.....#.....", "####..........#.....",
        "####.........##.....", "###..........##.....",
        "###...........######", "####################"]
  train = [
      generate(size=2, layout=l1, start=(9, 8), goal=(0, 1)),
      generate(size=2, layout=l2, start=(2, 10), goal=(12, 1)),
      generate(size=3, layout=l3, start=(12, 1), goal=(1, 0)),
      generate(size=1, layout=l4, start=(1, 1), goal=(9, 4)),
  ]
  test = [generate(size=4, layout=lt, start=(11, 1), goal=(14, 16))]
  return {"train": train, "test": test}
