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

"""Generator for ARC task 16b78196: jigsaw pieces locking onto a notched wall.

Rule: a thick wall spans the whole grid. It runs horizontally, or vertically
in the transposed variant. Its two long edges are jagged, with notches
(missing cells) and single-cell bumps. Small single-colour pieces float
elsewhere. In the output every piece is translated so that it locks into a
jagged edge. Pieces are never rotated or flipped. One notch seeds a chain of
same-width pieces. Each piece's near profile exactly complements the current
edge, so that every column touches. The chain ends when the outer edge of the
last piece is straight. Every piece is used exactly once. The wall is
unchanged, including any unused decoy notches and bumps.

Scope: the scene is built from latent parameters:
  * grid size;
  * wall colour, position and thickness;
  * notch/bump profiles on both edges;
  * one to three chains of distinct widths (3..6), with one to three pieces
    each;
  * the cut profiles between consecutive pieces;
  * piece colours;
  * the scattered input positions.
A chain is generated as a tiling of a column strip. That means pieces are
always 4-connected and exactly fill the notch plus a rectangle. Decoy notches
and bumps are sampled on both edges. A local ambiguity guard rejects scenes
where the pieces of any width admit a jigsaw cover other than the intended
one. The guard is a constraint check only. The answer is always rendered from
the latent chain placement.
"""

import random

import common


def _profile(width, notches):
  """Per-column notch depths from a {column: depth} dict or a full list."""
  prof = [0] * width
  if notches is None:
    return prof
  if isinstance(notches, dict):
    for x, depth in notches.items():
      if not isinstance(x, int) or not 0 <= x < width:
        raise ValueError("Notch column outside wall")
      prof[x] = depth
    return prof
  if len(notches) != width:
    raise ValueError("Notch profile length must equal native width")
  return list(notches)


def _wall_cells(width, wall_top, thickness, top_n, bottom_n):
  wall_bottom = wall_top + thickness - 1
  cells = set()
  for x in range(width):
    for y in range(wall_top + top_n[x], wall_bottom - bottom_n[x] + 1):
      cells.add((y, x))
  return cells


def _build_pieces(wall_top, wall_bottom, top_n, bottom_n, chains):
  """Pieces in chain order with target cells and bbox-relative shapes."""
  pieces = []
  for side, x0, bounds, colours in chains:
    w = len(bounds[0])
    prof = top_n if side == 'top' else bottom_n
    lower = [1 - prof[x0 + c] for c in range(w)]
    for upper, colour in zip(bounds, colours):
      cells = []
      for c in range(w):
        for u in range(lower[c], upper[c]):
          y = wall_top - u if side == 'top' else wall_bottom + u
          cells.append((y, x0 + c))
      min_y = min(y for y, _ in cells)
      rel = sorted((y - min_y, x - x0) for y, x in cells)
      pieces.append({'colour': colour, 'cells': cells, 'rel': rel,
                     'origin': (min_y, x0), 'width': w})
      lower = upper
  return pieces


def _geometry(scene):
  wall = _wall_cells(scene['width'], scene['wall_top'],
                     scene['wall_thickness'], scene['top_n'],
                     scene['bottom_n'])
  wall_bottom = scene['wall_top'] + scene['wall_thickness'] - 1
  pieces = _build_pieces(scene['wall_top'], wall_bottom, scene['top_n'],
                         scene['bottom_n'], scene['chains'])
  return pieces, wall


def _make_bounds(g0, k):
  """Sample k cut profiles above the wall surface g0 (last one flat)."""
  w = len(g0)
  bounds = []
  prev = g0
  for i in range(1, k + 1):
    if i == k:
      cur = [max(prev) + random.randint(1, 2)] * w
    else:
      for _ in range(60):
        cur = [prev[c] + random.randint(1, 3) for c in range(w)]
        if len(set(cur)) == 1:
          continue
        if all(max(prev[c], prev[c + 1]) < min(cur[c], cur[c + 1])
               for c in range(w - 1)):
          break
      else:
        return None
    bounds.append(cur)
    prev = cur
  if bounds[-1][0] - min(g0) > 9:
    return None
  return bounds


def _jigsaw_covers(height, width, wall, edges, specs, ids, limit=2):
  """Up to `limit` jigsaw covers of the pieces `ids` (one width group)."""
  w = specs[ids[0]][0]
  found = []

  def extend(side, x, edge, avail, placed):
    if placed and len(set(edge)) == 1:
      found.append(tuple(placed))
      return
    for pi in avail:
      _, rel, top, bot = specs[pi]
      near = bot if side < 0 else top
      offs = set(edge[c] + side - near[c] for c in range(w))
      if len(offs) != 1:
        continue
      oy = offs.pop()
      if any(not 0 <= oy + dy < height or (oy + dy, x + dx) in wall
             for dy, dx in rel):
        continue
      far = top if side < 0 else bot
      extend(side, x, [oy + far[c] for c in range(w)],
             [q for q in avail if q != pi], placed + [(pi, oy, x)])

  for side, edge in ((-1, edges[0]), (1, edges[1])):
    for x in range(width - w + 1):
      seg = edge[x:x + w]
      if len(set(seg)) > 1:
        extend(side, x, seg, ids, [])

  covers = []

  def cover(remaining, occupied, chosen):
    if len(covers) >= limit:
      return
    if not remaining:
      covers.append(frozenset(chosen))
      return
    pi = min(remaining)
    for chain in found:
      members = set(p[0] for p in chain)
      if pi not in members or not members <= remaining:
        continue
      cells = set()
      for qi, oy, ox in chain:
        cells.update((oy + dy, ox + dx) for dy, dx in specs[qi][1])
      if cells & occupied:
        continue
      cover(remaining - members, occupied | cells, chosen + list(chain))

  cover(frozenset(ids), frozenset(), [])
  return covers


def _unique_cover(scene, pieces, wall):
  """True iff each width group has exactly the intended jigsaw cover."""
  width, height = scene['width'], scene['height']
  wall_bottom = scene['wall_top'] + scene['wall_thickness'] - 1
  top_edge = [scene['wall_top'] + scene['top_n'][x] for x in range(width)]
  bot_edge = [wall_bottom - scene['bottom_n'][x] for x in range(width)]
  specs = []
  for p in pieces:
    w = p['width']
    top = [min(dy for dy, dx in p['rel'] if dx == c) for c in range(w)]
    bot = [max(dy for dy, dx in p['rel'] if dx == c) for c in range(w)]
    specs.append((w, p['rel'], top, bot))
  groups = {}
  for i, s in enumerate(specs):
    groups.setdefault(s[0], []).append(i)
  for ids in groups.values():
    covers = _jigsaw_covers(height, width, wall, (top_edge, bot_edge),
                            specs, ids)
    intended = frozenset((i, pieces[i]['origin'][0], pieces[i]['origin'][1])
                         for i in ids)
    if covers != [intended]:
      return False
  return True


def _scatter(height, width, wall, pieces):
  """Place pieces loosely, never touching the wall or each other (8-nbhd)."""
  occupied = set(wall)
  positions = [None] * len(pieces)
  order = list(range(len(pieces)))
  random.shuffle(order)
  for pi in order:
    rel = pieces[pi]['rel']
    ph = max(dy for dy, _ in rel) + 1
    pw = pieces[pi]['width']
    if ph > height or pw > width:
      return None
    for _ in range(300):
      r = random.randint(0, height - ph)
      c = random.randint(0, width - pw)
      cells = [(r + dy, c + dx) for dy, dx in rel]
      if any((y + a, x + b) in occupied for y, x in cells
             for a in (-1, 0, 1) for b in (-1, 0, 1)):
        continue
      occupied.update(cells)
      positions[pi] = (r, c)
      break
    else:
      return None
  return positions


def _sample_scene(width, height, wall_color, vertical):
  for _ in range(500):
    w_grid = width if width is not None else random.randint(18, 30)
    h_grid = height if height is not None else random.randint(22, 30)
    wc = wall_color if wall_color is not None else random.randint(1, 9)
    vert = vertical if vertical is not None else random.random() < 0.35
    thickness = random.randint(5, 7)
    n_chains = random.choice([1, 2, 2, 3, 3])
    widths = random.sample([3, 4, 5, 6], n_chains)
    counts = [random.choice([1, 2, 2, 3, 3]) for _ in widths]
    if sum(counts) < 2:
      continue
    sides = [random.choice(['top', 'bottom']) for _ in widths]
    total = sum(widths) + 2 * (n_chains - 1)
    if total > w_grid:
      continue
    slack = w_grid - total
    cuts = sorted(random.randint(0, slack) for _ in widths)
    order = list(range(n_chains))
    random.shuffle(order)
    starts = [0] * n_chains
    x = 0
    prev = 0
    for idx, cut in zip(order, cuts):
      x += cut - prev
      prev = cut
      starts[idx] = x
      x += widths[idx] + 2
    top_n = [0] * w_grid
    bottom_n = [0] * w_grid
    reserved = {'top': set(), 'bottom': set()}
    chain_bounds = []
    ok = True
    for i in range(n_chains):
      w = widths[i]
      for _t in range(40):
        notch = [random.choice([-1, 0, 0, 1, 1, 2]) for _ in range(w)]
        if len(set(notch)) > 1 and max(notch) >= 1:
          break
      else:
        ok = False
        break
      bounds = _make_bounds([1 - v for v in notch], counts[i])
      if bounds is None:
        ok = False
        break
      prof = top_n if sides[i] == 'top' else bottom_n
      for c in range(w):
        prof[starts[i] + c] = notch[c]
      reserved[sides[i]].update(range(starts[i] - 1, starts[i] + w + 1))
      chain_bounds.append(bounds)
    if not ok:
      continue
    for side, prof in (('top', top_n), ('bottom', bottom_n)):
      for xx in range(w_grid):
        if xx not in reserved[side] and random.random() < 0.15:
          prof[xx] = random.choice([-1, 1, 1, 2])
    need_top = max([b[-1][0] - 1 for b, s in zip(chain_bounds, sides)
                    if s == 'top'] + [0])
    need_bottom = max([b[-1][0] - 1 for b, s in zip(chain_bounds, sides)
                       if s == 'bottom'] + [0])
    lo = max(1, need_top)
    hi = min(h_grid - thickness - 1, h_grid - thickness - need_bottom)
    if lo > hi:
      continue
    wall_top = random.randint(lo, hi)
    palette = [c for c in range(1, 10) if c != wc]
    chains = []
    for i in range(n_chains):
      colours = []
      for _ in range(counts[i]):
        colours.append(random.choice(
            [c for c in palette if not colours or c != colours[-1]]))
      chains.append((sides[i], starts[i], chain_bounds[i], colours))
    scene = {'width': w_grid, 'height': h_grid, 'wall_color': wc,
             'wall_top': wall_top, 'wall_thickness': thickness,
             'top_n': top_n, 'bottom_n': bottom_n, 'chains': chains,
             'vertical': vert}
    pieces, wall = _geometry(scene)
    if not _unique_cover(scene, pieces, wall):
      continue
    positions = _scatter(h_grid, w_grid, wall, pieces)
    if positions is None:
      continue
    scene['positions'] = positions
    return scene
  raise RuntimeError('could not build a jigsaw scene')


def _transpose(g):
  return [list(row) for row in zip(*g)]


def generate(width=None, height=None, wall_color=None, wall_top=None,
             wall_thickness=None, top_notches=None, bottom_notches=None,
             chains=None, positions=None, vertical=None):
  """Returns an input/output pair for the notched-wall jigsaw task.

  All geometry is given in the native frame, where the wall is horizontal.
  When vertical is True, both grids are transposed at the end.

  Args:
    width: native grid width, i.e. the wall length (random 18..30).
    height: native grid height (random 22..30).
    wall_color: colour of the wall (random 1..9); pieces never use it.
    wall_top: first row of the nominal wall band.
    wall_thickness: number of rows in the nominal band (5..7).
    top_notches: {column: depth} for the top edge. Depth 1 or 2 means
      missing cells; -1 means a one-cell bump.
    bottom_notches: the same for the bottom edge.
    chains: list of (side, x0, boundaries, colours). Side is 'top' or
      'bottom'. Columns run x0..x0+w-1. Boundaries is a list of k
      per-column profiles g_1..g_k, measured outward from the band edge,
      with g_k flat. Piece i fills levels g_{i-1} to g_i - 1, where
      g_0 = 1 - notch depth.
    positions: input bbox top-left (row, col) of each piece in chain order.
    vertical: transpose the finished scene so that the wall runs vertically.
  If chains is None, a fresh random scene is sampled. In that case only
  width, height, wall_color and vertical are honoured. Partial explicit wall
  geometry without chains is rejected rather than silently ignored.
  """
  for dimension in (width, height):
    if dimension is not None and (not isinstance(dimension, int) or not 1 <= dimension <= 30):
      raise ValueError("Native dimensions must be integers in 1..30")
  if wall_color is not None and wall_color not in range(1, 10):
    raise ValueError("Wall colour must be in 1..9")
  if chains is None:
    if any(v is not None for v in (wall_top, wall_thickness, top_notches, bottom_notches, positions)):
      raise ValueError("Partial wall geometry requires explicit chains")
    if (width is not None and width < 18) or (height is not None and height < 22):
      raise ValueError("Random native width requires 18..30 and height 22..30")
    scene = _sample_scene(width, height, wall_color, vertical)
  else:
    if any(v is None for v in (width, height, wall_color, wall_top, wall_thickness, positions)):
      raise ValueError("Explicit chains require complete wall geometry and positions")
    if not chains or wall_thickness < 1:
      raise ValueError("At least one chain and a positive wall thickness required")
    for side, x0, bounds, colours in chains:
      if (side not in ('top', 'bottom') or not bounds or not bounds[0] or
          len(bounds) != len(colours) or any(len(b) != len(bounds[0]) for b in bounds) or
          not 0 <= x0 <= width - len(bounds[0]) or
          any(c not in range(1, 10) or c == wall_color for c in colours)):
        raise ValueError("Invalid chain profiles or colours")
    scene = {'width': width, 'height': height, 'wall_color': wall_color,
             'wall_top': wall_top, 'wall_thickness': wall_thickness,
             'top_n': _profile(width, top_notches),
             'bottom_n': _profile(width, bottom_notches),
             'chains': chains, 'positions': positions,
             'vertical': bool(vertical)}
  pieces, wall = _geometry(scene)
  w_grid, h_grid = scene['width'], scene['height']
  if len(scene['positions']) != len(pieces):
    raise ValueError("One input position required per piece")
  occupied_in, occupied_out = set(wall), set(wall)
  if any(not (0 <= y < h_grid and 0 <= x < w_grid) for y, x in wall):
    raise ValueError("Wall outside native grid")
  for piece, (r, c) in zip(pieces, scene['positions']):
    input_cells = {(r + dy, c + dx) for dy, dx in piece['rel']}
    output_cells = set(piece['cells'])
    if any(not (0 <= y < h_grid and 0 <= x < w_grid) for y, x in input_cells | output_cells):
      raise ValueError("Piece outside native grid")
    if input_cells & occupied_in or output_cells & occupied_out:
      raise ValueError("Pieces overlap wall or each other")
    occupied_in.update(input_cells)
    occupied_out.update(output_cells)
  inp = common.grid(w_grid, h_grid, 0)
  out = common.grid(w_grid, h_grid, 0)
  for y, x in wall:
    inp[y][x] = scene['wall_color']
    out[y][x] = scene['wall_color']
  for piece, (r, c) in zip(pieces, scene['positions']):
    for y, x in piece['cells']:
      out[y][x] = piece['colour']
    for dy, dx in piece['rel']:
      inp[r + dy][c + dx] = piece['colour']
  if scene['vertical']:
    inp = _transpose(inp)
    out = _transpose(out)
  return {'input': inp, 'output': out}


def validate():
  """Reconstructs the canonical pairs from explicit latent parameters."""
  train = [
      generate(width=30, height=30, wall_color=8, wall_top=14,
               wall_thickness=5,
               top_notches={5: 1, 6: 2, 7: 1, 15: 1, 26: 1},
               bottom_notches={8: 1, 17: 1, 18: 1, 24: 2, 25: 1},
               chains=[('top', 4, [[3, 2, 3, 2, 3], [5, 4, 4, 4, 5],
                                   [6, 6, 6, 6, 6]], [2, 1, 6]),
                       ('bottom', 16, [[2, 3, 3, 2], [7, 6, 5, 4],
                                       [8, 8, 8, 8]], [3, 4, 3])],
               positions=[(23, 3), (23, 16), (8, 23), (4, 18), (2, 7),
                          (22, 23)],
               vertical=False),
      generate(width=30, height=30, wall_color=2, wall_top=8,
               wall_thickness=5, top_notches={},
               bottom_notches={3: -1, 9: -1, 10: 1, 12: -1, 18: 1, 22: -1,
                               23: 1, 24: 1, 28: -1},
               chains=[('bottom', 9, [[4, 3, 3, 4], [6, 7, 5, 6],
                                      [8, 8, 8, 8]], [1, 3, 4])],
               positions=[(1, 13), (21, 15), (17, 3)],
               vertical=False),
  ]
  test = [
      generate(width=30, height=30, wall_color=3, wall_top=9,
               wall_thickness=7,
               top_notches={2: 1, 3: 2, 6: 1, 13: 1, 14: 1, 18: 1, 19: 2,
                            20: 1, 24: 1},
               bottom_notches={2: 1, 11: 1, 12: 1, 13: 1, 17: 1, 18: 1,
                               27: 1},
               chains=[('top', 1, [[5, 4, 3, 2], [6, 6, 6, 6]], [8, 6]),
                       ('bottom', 16, [[3, 4, 2, 3], [7, 5, 5, 7],
                                       [8, 8, 8, 8]], [2, 4, 1])],
               positions=[(18, 3), (0, 13), (21, 16), (2, 4), (21, 24)],
               vertical=True),
  ]
  return {'train': train, 'test': test}
