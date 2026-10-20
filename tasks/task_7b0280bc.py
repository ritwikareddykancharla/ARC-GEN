"""Generator for ARC task 7b0280bc: highlight the chain between two endpoint blocks.

Rule. Each grid is a network drawn on a uniform background in three other colours:
  * many filled square blocks of a node colour;
  * exactly two square blocks of an endpoint colour;
  * thin straight or diagonal strokes of a line colour.
A stroke is one 8-connected piece of the line colour. It links every block its cells touch,
and diagonal contact counts. The output finds the shortest chain of pieces joining the two
endpoint blocks, where pieces are blocks and strokes. Strokes on that chain become 5 and
intermediate node blocks become 3. Everything else is unchanged: the endpoints, dead-end
branches, longer alternative routes and disconnected parts.

Scope of random generation (a synthetic extension of the fixtures):
  * blocks are 2x2 or 3x3, and all blocks in one scene share one size;
  * strokes are 1 or 2 cells thick (2-thick strokes go with 3x3 blocks by default);
  * grid sides are sampled independently, from 12..30 by default and up to 30;
  * the four input colours are distinct, drawn from {0,1,2,4,6,7,8,9}, and never 3 or 5.

How random scenes are built:
  * A spanning forest is built with union-find. Optional extra links then close cycles, so
    a longer alternative route often exists and the shortest-chain choice matters.
  * Every stroke touches exactly the one or two blocks it was built for and no other
    stroke. The latent piece graph therefore equals the graph read from the painted grid.
  * The endpoints are chosen so that the shortest endpoint route is strictly unique and at
    least two links long. Every scene also has an off-chain node block and an off-chain
    stroke.
  * The answer is the unique shortest path in the latent block/link graph. It is not
    re-read from the painted grid.

Fixtures are rebuilt through explicit latent arguments: a block list, endpoint indices and
stroke cell lists, decoded from run-length descriptions of the original inputs. Explicit
scenes are checked so that the supplied pieces equal the painted connected components. The
answer is then the unique shortest chain over those pieces. Ambiguous, disconnected
or stroke-free endpoint routes are rejected.
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

import random
from collections import deque

import common

_LINE_OUT = 5
_NODE_OUT = 3
_PALETTE = (0, 1, 2, 4, 6, 7, 8, 9)
_EIGHT = tuple((dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
_FOUR = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DENSITY = 0.7


def _components(grid, color, diagonal):
  """Connected components of one colour, discovered in row-major order."""
  height, width = len(grid), len(grid[0])
  seen = [[False] * width for _ in range(height)]
  dirs = _EIGHT if diagonal else _FOUR
  comps = []
  for r in range(height):
    for c in range(width):
      if seen[r][c] or grid[r][c] != color:
        continue
      seen[r][c] = True
      stack, cells = [(r, c)], []
      while stack:
        y, x = stack.pop()
        cells.append((y, x))
        for dy, dx in dirs:
          ny, nx = y + dy, x + dx
          if (0 <= ny < height and 0 <= nx < width and not seen[ny][nx]
              and grid[ny][nx] == color):
            seen[ny][nx] = True
            stack.append((ny, nx))
      comps.append(sorted(cells))
  return comps


def _block_cells(block):
  r, c, s = block
  return [(y, x) for y in range(r, r + s) for x in range(c, c + s)]


def _paint(width, height, background, line_color, node_color, end_color,
           blocks, ends, strokes):
  grid = common.grid(width, height, background)
  for i, block in enumerate(blocks):
    color = end_color if i in ends else node_color
    for y, x in _block_cells(block):
      grid[y][x] = color
  for cells in strokes:
    for y, x in cells:
      grid[y][x] = line_color
  return grid


def _has_bent_component(grid, color):
  """The line colour must have a non-square 4-component, so roles are identifiable."""
  for cells in _components(grid, color, False):
    ys = [y for y, _ in cells]
    xs = [x for _, x in cells]
    hh, ww = max(ys) - min(ys) + 1, max(xs) - min(xs) + 1
    if hh != ww or len(cells) != hh * ww:
      return True
  return False


def _chain(pieces, width, height):
  """Shortest chain of touching pieces between the two endpoint pieces."""
  label = [[-1] * width for _ in range(height)]
  for i, (_, cells) in enumerate(pieces):
    for y, x in cells:
      label[y][x] = i
  adj = [set() for _ in pieces]
  for i, (_, cells) in enumerate(pieces):
    for y, x in cells:
      for dy, dx in _EIGHT:
        ny, nx = y + dy, x + dx
        if 0 <= ny < height and 0 <= nx < width:
          j = label[ny][nx]
          if j >= 0 and j != i:
            adj[i].add(j)
  end_ids = [i for i, p in enumerate(pieces) if p[0] == "end"]
  start, goal = end_ids[0], end_ids[1]
  dist, count, prev = _shortest(adj, start)
  if goal not in dist or count[goal] != 1:
    raise ValueError("endpoints must have a unique shortest chain")
  chain = []
  u = goal if goal in prev else None
  while u is not None:
    chain.append(u)
    u = prev[u]
  if not any(pieces[i][0] == "line" for i in chain):
    raise ValueError("endpoint chain must include a stroke")
  return chain


def _render(grid, width, height, blocks, ends, strokes):
  """Explicit-scene answer: shortest chain over the (validated) latent pieces."""
  end_blocks = sorted(tuple(blocks[i]) for i in ends)
  node_blocks = sorted(tuple(b) for i, b in enumerate(blocks) if i not in ends)
  pieces = [("end", _block_cells(b)) for b in end_blocks]
  pieces += [("node", _block_cells(b)) for b in node_blocks]
  ordered = sorted((sorted(tuple(p) for p in cells) for cells in strokes),
                   key=lambda cells: cells[0])
  pieces += [("line", cells) for cells in ordered]
  output = [row[:] for row in grid]
  for i in _chain(pieces, width, height):
    kind, cells = pieces[i]
    if kind == "end":
      continue
    color = _LINE_OUT if kind == "line" else _NODE_OUT
    for y, x in cells:
      output[y][x] = color
  return {"input": grid, "output": output}


def _render_latent(scene, links):
  """Random-scene answer: recolour the unique shortest latent route."""
  grid = _paint(**scene)
  blocks, strokes = scene["blocks"], scene["strokes"]
  adj = [[] for _ in blocks]
  for k, link in enumerate(links):
    if link is None:
      continue
    i, j = link
    adj[i].append((j, k))
    adj[j].append((i, k))
  start, goal = scene["ends"]
  prev = {start: None}
  queue = deque([start])
  while queue:
    u = queue.popleft()
    for v, k in adj[u]:
      if v not in prev:
        prev[v] = (u, k)
        queue.append(v)
  output = [row[:] for row in grid]
  u = goal
  while prev[u] is not None:
    w, k = prev[u]
    for y, x in strokes[k]:
      output[y][x] = _LINE_OUT
    if w != start:
      for y, x in _block_cells(blocks[w]):
        output[y][x] = _NODE_OUT
    u = w
  return {"input": grid, "output": output}


def _block_gap(a, b):
  (r1, c1, s1), (r2, c2, s2) = a, b
  vg = max(r2 - (r1 + s1), r1 - (r2 + s2))
  hg = max(c2 - (c1 + s1), c1 - (c2 + s2))
  return max(vg, hg)


def _anchor_ring(block, t, height, width):
  """Top-left anchors of t x t squares that touch a block without overlapping it."""
  r, c, s = block
  out = []
  for y in range(r - t, r + s + 1):
    for x in range(c - t, c + s + 1):
      if r - t + 1 <= y <= r + s - 1 and c - t + 1 <= x <= c + s - 1:
        continue
      if 0 <= y and y + t <= height and 0 <= x and x + t <= width:
        out.append((y, x))
  return out


def _dilate(anchors, t):
  return {(y + i, x + j) for y, x in anchors for i in range(t) for j in range(t)}


def _steps(p, q, k):
  """Anchor path p->q: k straight steps, then the diagonal run, then the rest straight."""
  dr, dc = q[0] - p[0], q[1] - p[1]
  sr = (dr > 0) - (dr < 0)
  sc = (dc > 0) - (dc < 0)
  nd = min(abs(dr), abs(dc))
  ns = max(abs(dr), abs(dc)) - nd
  straight = (sr, 0) if abs(dr) > abs(dc) else (0, sc)
  moves = [straight] * k + [(sr, sc)] * nd + [straight] * (ns - k)
  cur, path = p, [p]
  for my, mx in moves:
    cur = (cur[0] + my, cur[1] + mx)
    path.append(cur)
  return path


def _fits(cells, occ, allowed, height, width):
  """Stroke cells are free and touch exactly the allowed pieces, all of them."""
  for y, x in cells:
    if not (0 <= y < height and 0 <= x < width) or occ[y][x] != -1:
      return False
  touched = set()
  for y, x in cells:
    for dy, dx in _EIGHT:
      ny, nx = y + dy, x + dx
      if 0 <= ny < height and 0 <= nx < width and occ[ny][nx] != -1:
        if occ[ny][nx] not in allowed:
          return False
        touched.add(occ[ny][nx])
  return touched == set(allowed)


def _try_connect(a, b, blocks, t, occ, height, width):
  ra = _anchor_ring(blocks[a], t, height, width)
  rb = _anchor_ring(blocks[b], t, height, width)
  if not ra or not rb:
    return None
  pairs = [(max(abs(p[0] - q[0]), abs(p[1] - q[1])), p, q)
           for p in ra for q in rb]
  dmin = min(d for d, _, _ in pairs)
  near = [(p, q) for d, p, q in pairs if d <= dmin + 1]
  for _ in range(8):
    p, q = random.choice(near)
    ns = abs(abs(q[0] - p[0]) - abs(q[1] - p[1]))
    cells = _dilate(_steps(p, q, random.randint(0, ns)), t)
    if _fits(cells, occ, {a, b}, height, width):
      return cells
  return None


def _try_dead_end(a, blocks, t, occ, height, width):
  ring = _anchor_ring(blocks[a], t, height, width)
  if not ring:
    return None
  r, c, s = blocks[a]
  for _ in range(8):
    p = random.choice(ring)
    dy = -1 if p[0] < r - t + 1 else (1 if p[0] > r + s - 1 else 0)
    dx = -1 if p[1] < c - t + 1 else (1 if p[1] > c + s - 1 else 0)
    if dy and dx:
      opts = [(dy, dx), (dy, 0), (0, dx)]
    elif dy:
      opts = [(dy, 0), (dy, -1), (dy, 1)]
    else:
      opts = [(0, dx), (-1, dx), (1, dx)]
    move = random.choice(opts)
    length = random.randint(2, 5)
    bend = random.randint(1, length)
    cur, path = p, [p]
    for i in range(length):
      if i == bend:
        move = random.choice(opts)
      cur = (cur[0] + move[0], cur[1] + move[1])
      path.append(cur)
    cells = _dilate(path, t)
    if _fits(cells, occ, {a}, height, width):
      return cells
  return None


def _find(parent, i):
  while parent[i] != i:
    parent[i] = parent[parent[i]]
    i = parent[i]
  return i


def _shortest(adj, start):
  """BFS distances, shortest-path counts and predecessors in the block graph."""
  dist, count, prev = {start: 0}, {start: 1}, {start: None}
  queue = deque([start])
  while queue:
    u = queue.popleft()
    for v in adj[u]:
      if v not in dist:
        dist[v] = dist[u] + 1
        count[v] = count[u]
        prev[v] = u
        queue.append(v)
      elif dist[v] == dist[u] + 1:
        count[v] += count[u]
  return dist, count, prev


def _connected_without(adj, a, b, edge):
  banned = set(edge)
  seen, stack = {a}, [a]
  while stack:
    u = stack.pop()
    if u == b:
      return True
    for v in adj[u]:
      if {u, v} == banned or v in seen:
        continue
      seen.add(v)
      stack.append(v)
  return False


def _capacity(h, w, s, t):
  """Upper bound on how many blocks fit with the required spacing."""
  gap = 2 + t
  return ((h + gap) // (s + gap)) * ((w + gap) // (s + gap))


def _feasible(h, w, s, t, num_blocks):
  cap = _capacity(h, w, s, t)
  return cap >= 6 and (num_blocks is None or num_blocks <= _DENSITY * cap)


def _thicknesses(s, thickness):
  if thickness is not None:
    return [thickness]
  return [1, 2] if s == 3 else [1]


def _random_scene(width, height, background, line_color, node_color,
                  end_color, block_size, thickness, num_blocks, extra_links):
  sizes = [block_size] if block_size is not None else [2, 3]
  if not any(_feasible(height or 30, width or 30, s, t, num_blocks)
             for s in sizes for t in _thicknesses(s, thickness)):
    raise ValueError("grid too small or num_blocks too dense for the requested "
                     "block_size/thickness")
  for _ in range(500):
    s = block_size if block_size is not None else random.choice((2, 2, 3))
    t = random.choice(_thicknesses(s, thickness))
    lo = (12 if s == 2 else 16) + (4 if t == 2 else 0)
    h = height if height is not None else random.randint(lo, 30)
    w_opts = [width] if width is not None else list(range(lo, 31))
    w_opts = [x for x in w_opts if _feasible(h, x, s, t, num_blocks)]
    if not w_opts:
      continue
    w = random.choice(w_opts)
    given = (background, line_color, node_color, end_color)
    pool = [c for c in _PALETTE if c not in given]
    random.shuffle(pool)
    bg, line, node, end = [c if c is not None else pool.pop() for c in given]
    gap = 2 + t
    cap = _capacity(h, w, s, t)
    n_max = max(6, min(13, h * w // (10 * s * s), int(_DENSITY * cap)))
    target = num_blocks if num_blocks is not None else random.randint(6, n_max)
    blocks = []
    for _ in range(600):
      if len(blocks) >= target:
        break
      cand = (random.randint(0, h - s), random.randint(0, w - s), s)
      if all(_block_gap(cand, b) >= gap for b in blocks):
        blocks.append(cand)
    n = len(blocks)
    if n < 5 or (num_blocks is not None and n != num_blocks):
      continue
    occ = [[-1] * w for _ in range(h)]
    for i, b in enumerate(blocks):
      for y, x in _block_cells(b):
        occ[y][x] = i
    pairs = []
    for i in range(n):
      for j in range(i + 1, n):
        g = _block_gap(blocks[i], blocks[j])
        if g <= 7 + 2 * s:
          pairs.append((g + random.uniform(0, 5), i, j))
    pairs.sort()
    parent = list(range(n))
    strokes, links, linked = [], [], set()

    def add_stroke(cells, link):
      for y, x in cells:
        occ[y][x] = n + len(strokes)
      strokes.append(cells)
      links.append(link)
      if link is not None:
        linked.add(link)

    for _, i, j in pairs:
      if _find(parent, i) == _find(parent, j) or random.random() < 0.12:
        continue
      cells = _try_connect(i, j, blocks, t, occ, h, w)
      if cells is None:
        continue
      add_stroke(cells, (i, j))
      parent[_find(parent, i)] = _find(parent, j)
    # Cycle-closing links: these create longer alternative routes.
    if extra_links is not None:
      want = extra_links
    else:
      want = random.randint(1, 3) if random.random() < 0.7 else 0
    extra = [(i, j) for _, i, j in pairs
             if (i, j) not in linked and _find(parent, i) == _find(parent, j)]
    random.shuffle(extra)
    added = 0
    for i, j in extra:
      if added >= want:
        break
      cells = _try_connect(i, j, blocks, t, occ, h, w)
      if cells is None:
        continue
      add_stroke(cells, (i, j))
      added += 1
    if added != want:
      continue
    for _ in range(random.randint(1, 3)):
      a = random.randrange(n)
      cells = _try_dead_end(a, blocks, t, occ, h, w)
      if cells is not None:
        add_stroke(cells, None)
    adj = [[] for _ in range(n)]
    for link in links:
      if link is not None:
        i, j = link
        adj[i].append(j)
        adj[j].append(i)
    cands = []
    for i in range(n):
      dist, count, prev = _shortest(adj, i)
      for j, d in dist.items():
        if j <= i or d < 2 or n - 1 - d < 1 or len(strokes) <= d:
          continue
        if count[j] != 1:
          continue  # tied shortest routes would be ambiguous
        path = [j]
        while prev[path[-1]] is not None:
          path.append(prev[path[-1]])
        alt = any(_connected_without(adj, i, j, (path[k], path[k + 1]))
                  for k in range(len(path) - 1))
        cands.append((i, j, d, alt))
    if not cands:
      continue
    alts = [c for c in cands if c[3]]
    if alts and random.random() < 0.75:
      cands = alts
    i, j, _, _ = random.choices(cands, weights=[c[2] ** 2 for c in cands])[0]
    scene = {
        "width": w, "height": h, "background": bg, "line_color": line,
        "node_color": node, "end_color": end, "blocks": blocks,
        "ends": [i, j], "strokes": [sorted(cells) for cells in strokes],
    }
    grid = _paint(**scene)
    if not _has_bent_component(grid, line):
      continue
    if sum(v != bg for row in grid for v in row) * 2 >= h * w:
      continue
    return scene, links
  raise ValueError("could not build a valid network scene with these controls")


def _check_color(value):
  if value is not None and (type(value) is not int or value not in _PALETTE):
    raise ValueError("input colours must be in {0,1,2,4,6,7,8,9} (3 and 5 are "
                     "reserved for the output)")


def _check_explicit(width, height, background, line_color, node_color,
                    end_color, blocks, ends, strokes):
  """Validates an explicit scene and returns its painted input grid."""
  if len(ends) != 2 or ends[0] == ends[1]:
    raise ValueError("ends must name two distinct blocks")
  for e in ends:
    if type(e) is not int or not 0 <= e < len(blocks):
      raise ValueError("endpoint index out of range")
  if len(blocks) - 2 < 3:
    raise ValueError("need at least three node blocks besides the endpoints")
  owner = {}
  for i, block in enumerate(blocks):
    if len(block) != 3 or not all(type(v) is int for v in block):
      raise ValueError("blocks must be integer (row, col, size) triples")
    r, c, s = block
    if s < 1 or r < 0 or c < 0 or r + s > height or c + s > width:
      raise ValueError("block size must be positive and inside the grid")
    for cell in _block_cells(block):
      if cell in owner:
        raise ValueError("blocks overlap")
      owner[cell] = i
  if not strokes:
    raise ValueError("at least one stroke is required")
  for cells in strokes:
    if not cells:
      raise ValueError("strokes must be non-empty")
    for p in cells:
      if not isinstance(p, (list, tuple)) or len(p) != 2 or any(type(v) is not int for v in p):
        raise ValueError("stroke cells must be integer (row, col) pairs")
      y, x = p
      if not (0 <= y < height and 0 <= x < width):
        raise ValueError("stroke cell out of bounds")
      if (y, x) in owner:
        raise ValueError("stroke cells overlap blocks or other strokes")
      owner[(y, x)] = -1
  grid = _paint(width, height, background, line_color, node_color, end_color,
                blocks, ends, strokes)
  given = sorted(sorted(tuple(p) for p in cells) for cells in strokes)
  if given != sorted(_components(grid, line_color, True)):
    raise ValueError("strokes must be exactly the 8-connected line components")
  nodes = [i for i in range(len(blocks)) if i not in ends]
  for color, idxs in ((end_color, ends), (node_color, nodes)):
    want = sorted(sorted(_block_cells(blocks[i])) for i in idxs)
    if want != sorted(_components(grid, color, False)):
      raise ValueError("same-colour blocks must not touch (4-adjacency)")
  if not _has_bent_component(grid, line_color):
    raise ValueError("line colour needs a non-square component")
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  if any(counts[v] >= counts.get(background, 0) for v in counts if v != background):
    raise ValueError("background must be the strictly most frequent colour")
  return grid


def generate(width=None, height=None, background=None, line_color=None,
             node_color=None, end_color=None, block_size=None, thickness=None,
             num_blocks=None, extra_links=None, blocks=None, ends=None,
             strokes=None):
  """Returns an input/output pair.

  Args:
    width: grid width (columns), 1..30. Random scenes reject sides that are too small.
    height: grid height (rows), 1..30. Random scenes reject sides that are too small.
    background: background colour.
    line_color: colour of the strokes.
    node_color: colour of the ordinary (node) blocks.
    end_color: colour of the two endpoint blocks.
    block_size: side of the square blocks, 2 or 3 (random scenes only).
    thickness: stroke thickness, 1 or 2 (random scenes only).
    num_blocks: exact number of blocks, 5..16 (random scenes only). Values above about
      70% of the packing bound for the grid are rejected.
    extra_links: exact number of cycle-closing links, 0..3 (random scenes only).
    blocks: explicit list of (row, col, size) square blocks.
    ends: indices into blocks of the two endpoint blocks.
    strokes: explicit list of stroke cell lists [(row, col), ...]. Each stroke must be
      exactly one 8-connected component of the painted line colour.

  Supplied colours must be distinct and must avoid 3 and 5. Explicit scenes need
  blocks, ends, strokes, width, height and all four colours together, and they reject
  the random-only controls.
  """
  for name, value in (("width", width), ("height", height),
                      ("block_size", block_size), ("thickness", thickness),
                      ("num_blocks", num_blocks), ("extra_links", extra_links)):
    if value is not None and type(value) is not int:
      raise ValueError(name + " must be an integer")
  colors = (background, line_color, node_color, end_color)
  for value in colors:
    _check_color(value)
  given = [c for c in colors if c is not None]
  if len(set(given)) != len(given):
    raise ValueError("supplied colours must be distinct")
  for dim in (width, height):
    if dim is not None and not 1 <= dim <= 30:
      raise ValueError("grid sides must be 1..30")
  explicit = (blocks, ends, strokes)
  if any(v is not None for v in explicit):
    if any(v is None for v in explicit):
      raise ValueError("blocks, ends and strokes must be given together")
    if width is None or height is None or None in colors:
      raise ValueError("explicit scenes need width, height and all colours")
    if any(v is not None for v in (block_size, thickness, num_blocks,
                                   extra_links)):
      raise ValueError("block_size/thickness/num_blocks/extra_links apply to "
                       "random scenes")
    grid = _check_explicit(width, height, background, line_color, node_color,
                           end_color, blocks, ends, strokes)
    return _render(grid, width, height, blocks, ends, strokes)
  if block_size not in (None, 2, 3):
    raise ValueError("block_size must be 2 or 3")
  if thickness not in (None, 1, 2):
    raise ValueError("thickness must be 1 or 2")
  if num_blocks is not None and not 5 <= num_blocks <= 16:
    raise ValueError("num_blocks must be 5..16")
  if extra_links is not None and not 0 <= extra_links <= 3:
    raise ValueError("extra_links must be 0..3")
  scene, links = _random_scene(width, height, background, line_color,
                               node_color, end_color, block_size, thickness,
                               num_blocks, extra_links)
  return _render_latent(scene, links)


def _decode(rows):
  grid = []
  for row in rows:
    vals = []
    for tok in row.split():
      if "*" in tok:
        a, b = tok.split("*")
        vals.extend([int(a)] * int(b))
      else:
        vals.append(int(tok))
    grid.append(vals)
  return grid


def _fixture_scene(rows, background, line_color, node_color, end_color):
  """Turns a run-length fixture input into explicit latent objects."""
  grid = _decode(rows)
  blocks, ends = [], []
  for color in (end_color, node_color):
    for cells in _components(grid, color, False):
      r0 = min(y for y, _ in cells)
      c0 = min(x for _, x in cells)
      size = max(y for y, _ in cells) - r0 + 1
      if color == end_color:
        ends.append(len(blocks))
      blocks.append((r0, c0, size))
  strokes = _components(grid, line_color, True)
  return {"width": len(grid[0]), "height": len(grid),
          "background": background, "line_color": line_color,
          "node_color": node_color, "end_color": end_color,
          "blocks": blocks, "ends": ends, "strokes": strokes}


_P1 = [
    "8*18",
    "8*7 0 2*2 8*5 1*2 8",
    "8*6 0 8 2*2 8*5 1*2 8",
    "8*2 2*2 8 0 8*3 0 8*4 0 8 0 8",
    "8*2 2*2 0 8*4 0 8*3 0 8*2 0 8",
    "8*2 0 8*6 0 8*3 0 8*2 0 8",
    "8*2 0 8*6 0 8*3 0 8*2 0 8",
    "8*3 0 8*5 0 8*2 0 8*3 0 8",
    "8*3 0 8*6 0 8 2*2 8*2 0 8",
    "8*3 1*2 8*5 0 8 2*2 8*2 0 8",
    "8*3 1*2 8*5 0 8*5 0 8",
    "8*3 0 8*6 0 8*4 0 8*2",
    "8*4 0 8*5 0 8*3 0 8*3",
    "8*4 0 8*5 2*2 8 0 8*4",
    "8*4 2*2 8*2 0*2 2*2 0 8*5",
    "8*4 2*2 0*2 8*10",
    "8*18",
    "8*18",
]

_P2 = [
    "9*6 4 7*2 4 9*5",
    "9*3 7*2 4 9 7*2 9 4 6*2 9*2",
    "9*3 7*2 9*6 6*2 4 9",
    "9*3 4 9 4 9*8 4",
    "9*3 4 9*2 4 9*7 4",
    "9 4 6*2 9*3 4 9*5 4 9",
    "4 9 6*2 9*3 4 9*4 7*2 9",
    "4 9*6 7*2 4*3 7*2 9",
    "4 9*6 7*2 9*4 4 9",
    "4 9 7*2 4 9*3 4 9*4 4 9",
    "4 9 7*2 9 4 9*3 4 9*2 4 9*2",
    "4 9*4 4 9*3 4 9*2 4 9*2",
    "9 4 9*3 7*2 9*2 7*2 9 4 9*2",
    "9*2 4*3 7*2 9*2 7*2 9 7*2 9",
    "9*12 7*2 9",
]

_P3 = [
    "7*20",
    "7*2 1*2 6*6 7*10",
    "7*2 1*2 7*6 6*4 7*6",
    "7*2 6 7*11 6 7*5",
    "7*2 6 7*10 2*2 7*5",
    "7*2 6 7*9 6 2*2 7*5",
    "7*2 6 7*8 6 7*2 6 7*5",
    "7*2 6 7*7 1*2 7*2 6 7*5",
    "7 6*2 7*7 1*2 7*2 6 7*5",
    "7 6 7*8 6 7*3 6 7*5",
    "7 6 7*5 1*2 7 6 7*4 6 7*4",
    "7 6 7*4 6 1*2 6 7*5 6 7*4",
    "7 6 7*3 6 7*10 6 7*3",
    "7 6 7*2 1*2 7*10 6 7*3",
    "7 6 7*2 1*2 6*2 7*7 6 7*4",
    "7 6 7*2 6 7*3 6*2 7*4 1*2 7*4",
    "7 6 7 6 7*6 6*4 1*2 7*4",
    "7 2*2 7*17",
    "7 2*2 7*17",
    "7*20",
]

_T1 = [
    "4*30",
    "4*30",
    "4*2 9*3 1*7 9*3 1*8 4*7",
    "4*2 9*3 1*7 9*3 1*8 4*7",
    "4*2 9*3 4*7 9*3 4*6 1*2 4*7",
    "4*2 1*2 4*7 1*2 4*8 9*3 4*6",
    "4*2 1*2 4*6 1*3 4*8 9*3 4*6",
    "4*2 1*2 4*5 1*3 4*8 1 9*3 4*6",
    "4*2 1*2 4*2 0*3 1*2 4*8 1*2 4 1*2 4*6",
    "4*2 1*2 4*2 0*3 4*9 1*2 4*3 1*2 4*5",
    "4*3 1*2 4 0*3 4*8 1*2 4*5 1*2 4*4",
    "4*3 1*2 4*2 1*2 4*7 1*2 4*7 1*2 4*3",
    "4*3 1*2 4*2 1*2 4*4 9*3 1 4*7 9*3 4*3",
    "4*3 1*2 4*2 1*2 4*4 9*3 4*8 9*3 4*3",
    "4*3 1*2 4*2 1*2 4*4 9*3 4*8 9*3 4*3",
    "4*3 9*3 4 1*2 4*4 1*2 4*9 1*2 4*4",
    "4*3 9*3 4 1*2 4*4 1*2 4*8 1*2 4*5",
    "4*3 9*3 4 1*2 4*4 1*2 4*7 1*2 4*6",
    "4*7 1*2 4*4 1*2 4*6 0*3 4*6",
    "4*7 1*2 4*4 1*2 4*6 0*3 4*6",
    "4*7 9*3 4*3 1*2 4*6 0*3 4*6",
    "4*7 9*3 4*3 1*2 4*5 1*2 4*8",
    "4*7 9*3 4*3 1*2 4*4 1*2 4*9",
    "4*8 1*2 4*3 1*2 4*3 1*2 4*10",
    "4*9 1*2 4*2 1*2 4*2 1*2 4*11",
    "4*10 1*2 4 9*3 1*2 4*12",
    "4*11 1*2 9*3 1 4*13",
    "4*12 1 9*3 4*14",
    "4*30",
    "4*30",
]


def validate():
  """Reconstructs the canonical fixtures through explicit latent arguments."""
  train = [
      generate(**_fixture_scene(_P1, 8, 0, 2, 1)),
      generate(**_fixture_scene(_P2, 9, 4, 7, 6)),
      generate(**_fixture_scene(_P3, 7, 6, 1, 2)),
  ]
  test = [generate(**_fixture_scene(_T1, 4, 1, 9, 0))]
  return {"train": train, "test": test}
