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

"""Generator for ARC-AGI task f341894c: dominoes turn their 6 toward the 7.

Rule: the background is 8. The grid holds single 7 marks and 1/6 dominoes.
A domino is one 1 cell and one 6 cell side by side, either horizontal or
vertical. Every domino lies on a line that contains a 7: its row if it is
horizontal, its column if it is vertical. In the output, the end of each
domino nearer the closest 7 on that line becomes 6 and the other end
becomes 1. Dominoes that already face their 7 keep their colours. The 7s
and the background never change.

Scope: random scenes mix isolated dominoes with tightly packed clusters.
There are two kinds of cluster:
  * parallel stacks: horizontal dominoes stacked vertically, or vertical
    dominoes side by side. These match the checkerboard and the 2x2 block
    of the test.
  * offset step pairs, matching the test's column 10/11 pair.
Inside a cluster, the lines that run through touching cells of different
dominoes, perpendicular to the dominoes, never carry a 7. That makes the
pairing of cells into dominoes unique, and it holds for both the
greedy-scan reading and the semantic reading. Different clusters never
touch orthogonally. They may touch diagonally, as in the test.

Each domino line normally carries exactly one 7. That 7 may be shared with
other collinear dominoes, or it may be the 7 placed for a perpendicular
domino at a corner. Two 7s on one domino line happen only through the
explicit double_seven_prob control: both ends of a single domino's line get
a 7, and the strictly nearer one wins. Equal distances are never sampled.
This double case is a synthetic extension; no fixture shows it. With
probability distractor_prob, one unused border 7 is added off every domino
line. Every sample flips at least one domino.

Grid sizes are 8..30 per side, usually 8..20, and often square. Sides above
the fixture maximum of 18 are a synthetic extension. Explicit height/width
requests may use 6..30. Random 7s sit only on border cells, as in all
fixtures.
"""

import random

import common

BACKGROUND = 8
MARK = 7
COLORS = (1, 6)
MIN_SIDE = 6
MAX_SIDE = 30
DEFAULT_DOUBLE_PROB = 0.08
DEFAULT_DISTRACTOR_PROB = 0.25


def _domino_cells(domino):
  """Returns the two cells of a domino (row, col, orient, ...)."""
  y, x, orient = domino[0], domino[1], domino[2]
  if orient == 'h':
    return [(y, x), (y, x + 1)]
  return [(y, x), (y + 1, x)]


def _domino_line(domino):
  """The ('r', row) or ('c', col) line the domino is read along."""
  if domino[2] == 'h':
    return ('r', domino[0])
  return ('c', domino[1])


def _on_line(cell, domino):
  """True if cell lies on the row/column the domino is read along."""
  if domino[2] == 'h':
    return cell[0] == domino[0]
  return cell[1] == domino[1]


def _line_sevens(grid, domino):
  """All 7 cells on the line the domino is read along."""
  height, width = len(grid), len(grid[0])
  y, x, orient = domino[0], domino[1], domino[2]
  if orient == 'h':
    return [(y, c) for c in range(width) if grid[y][c] == MARK]
  return [(r, x) for r in range(height) if grid[r][x] == MARK]


def _count_line_sevens(grid, line):
  """Number of 7s on the ('r', index) row or ('c', index) column."""
  kind, idx = line
  if kind == 'r':
    return sum(1 for v in grid[idx] if v == MARK)
  return sum(1 for row in grid if row[idx] == MARK)


def _line_has_seven(grid, line):
  """True if the ('r', index) row or ('c', index) column contains a 7."""
  return _count_line_sevens(grid, line) > 0


def _facing_end(grid, domino):
  """Index (0 or 1) of the domino end nearer its closest 7, or None.

  None is returned when the line has no 7 or two 7s are equally close.
  """
  cells = _domino_cells(domino)
  best = None
  hits = 0
  for sy, sx in _line_sevens(grid, domino):
    dists = [abs(sy - cy) + abs(sx - cx) for cy, cx in cells]
    nearest = min(dists)
    end = 0 if dists[0] < dists[1] else 1
    if best is None or nearest < best[0]:
      best = (nearest, end)
      hits = 1
    elif nearest == best[0]:
      hits += 1
  if best is None or hits != 1:
    return None
  return best[1]


def _around(cells, height, width):
  """The cells plus their 8-neighbours, clipped to the grid."""
  out = set()
  for y, x in cells:
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        ny, nx = y + dy, x + dx
        if 0 <= ny < height and 0 <= nx < width:
          out.add((ny, nx))
  return out


def _around4(cells, height, width):
  """The cells plus their orthogonal neighbours, clipped to the grid."""
  out = set()
  for y, x in cells:
    for dy, dx in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
      ny, nx = y + dy, x + dx
      if 0 <= ny < height and 0 <= nx < width:
        out.add((ny, nx))
  return out


def _cluster_layout(kind, orient, size, mirror):
  """Returns the layout of one cluster.

  The result holds the first-cell offsets of the cluster's dominoes and the
  lines that must stay free of 7s so the packed cells pair up
  unambiguously.
  """
  if kind == 'single':
    return [(0, 0)], []
  if kind == 'stack':
    if orient == 'h':
      return [(i, 0) for i in range(size)], [('c', 0), ('c', 1)]
    return [(0, i) for i in range(size)], [('r', 0), ('r', 1)]
  firsts = [(0, 1), (1, 0)] if mirror else [(0, 0), (1, 1)]
  if orient == 'v':
    return firsts, [('r', 1)]
  return firsts, [('c', 1)]


def _seven_ok(grid, cell, forbidden, rows_no7, cols_no7, pending):
  """True if a 7 may be written at cell."""
  y, x = cell
  if grid[y][x] != BACKGROUND or cell in forbidden or cell in pending:
    return False
  return y not in rows_no7 and x not in cols_no7


def _check_pairing(grid, dominoes):
  """Raises ValueError if the declared pairing is not the only reading.

  Two orthogonally adjacent cells from different dominoes, with opposite
  colours, must lie on a 7-free line. Otherwise they could form a domino
  themselves.
  """
  owner = {}
  for i, d in enumerate(dominoes):
    for cell in _domino_cells(d):
      owner[cell] = i
  for (y, x), i in owner.items():
    for ny, nx, line in ((y, x + 1, ('r', y)), (y + 1, x, ('c', x))):
      j = owner.get((ny, nx))
      if j is None or j == i:
        continue
      if grid[y][x] == grid[ny][nx]:
        continue
      if _line_has_seven(grid, line):
        raise ValueError('cells %r and %r of different dominoes could pair '
                         'along a line with a 7' % ((y, x), (ny, nx)))


def _try_scene(height, width, double_prob, distractor_prob):
  """One attempt at a random scene; returns (dominoes, sevens) or None."""
  grid = common.grid(width, height, BACKGROUND)
  blocked = set()
  near_domino = set()
  rows_no7 = set()
  cols_no7 = set()
  dominoes = []
  perp_lines = []
  double_lines = set()
  area = height * width
  minimum = 3 if area >= 64 else 2
  low = max(minimum, area // 30)
  target = random.randint(low, max(low, area // 18))
  attempts = 0
  while len(dominoes) < target and attempts < 500:
    attempts += 1
    roll = random.random()
    if roll < 0.6:
      kind, size = 'single', 1
    elif roll < 0.84:
      kind, size = 'stack', random.choice([2, 2, 2, 3, 3, 4])
    else:
      kind, size = 'step', 2
    orient = random.choice('hv')
    firsts, rel_lines = _cluster_layout(kind, orient, size,
                                        random.random() < 0.5)
    rel_cells = []
    for fy, fx in firsts:
      rel_cells.extend(_domino_cells((fy, fx, orient)))
    box_h = max(cy for cy, _ in rel_cells) + 1
    box_w = max(cx for _, cx in rel_cells) + 1
    if box_h > height or box_w > width:
      continue
    oy = random.randint(0, height - box_h)
    ox = random.randint(0, width - box_w)
    cells = [(oy + cy, ox + cx) for cy, cx in rel_cells]
    if any(c in blocked for c in cells):
      continue
    lines = [(k, (oy if k == 'r' else ox) + off) for k, off in rel_lines]
    if any(_line_has_seven(grid, ln) for ln in lines):
      continue
    new_rows = rows_no7 | {i for k, i in lines if k == 'r'}
    new_cols = cols_no7 | {i for k, i in lines if k == 'c'}
    halo = _around(cells, height, width)
    forbidden = near_domino | halo
    new_dominoes = [(oy + fy, ox + fx, orient) for fy, fx in firsts]
    pending = []
    new_doubles = set()
    ok = True
    for d in new_dominoes:
      if _line_sevens(grid, d) or any(_on_line(s, d) for s in pending):
        continue
      if d[2] == 'h':
        ends = [(d[0], 0), (d[0], width - 1)]
      else:
        ends = [(0, d[1]), (height - 1, d[1])]
      random.shuffle(ends)
      usable = [e for e in ends
                if _seven_ok(grid, e, forbidden, new_rows, new_cols, pending)]
      if not usable:
        ok = False
        break
      pending.append(usable[0])
      if (kind == 'single' and len(usable) == 2
          and random.random() < double_prob):
        pending.append(usable[1])
        new_doubles.add(_domino_line(d))
    if not ok:
      continue
    for sy, sx in pending:
      grid[sy][sx] = MARK
    allowed = double_lines | new_doubles
    everyone = dominoes + new_dominoes
    bad = any(_facing_end(grid, d) is None for d in everyone)
    if not bad:
      # Only deliberately sampled double lines may carry two 7s; a 7 that
      # was placed for one domino must not land on another domino's line.
      for d in everyone:
        ln = _domino_line(d)
        n = _count_line_sevens(grid, ln)
        if n >= 2 and (ln not in allowed or n > 2):
          bad = True
          break
    if bad:
      for sy, sx in pending:
        grid[sy][sx] = BACKGROUND
      continue
    for cy, cx in cells:
      grid[cy][cx] = COLORS[0]
    # Clusters may touch diagonally but never orthogonally; dominoes never
    # touch a 7, even diagonally.
    blocked |= _around4(cells, height, width) | _around(pending, height, width)
    near_domino |= halo
    rows_no7, cols_no7 = new_rows, new_cols
    dominoes.extend(new_dominoes)
    perp_lines.extend(lines)
    double_lines = allowed
  if len(dominoes) < minimum:
    return None
  if random.random() < distractor_prob:
    border = [(r, c) for r in range(height) for c in range(width)
              if r in (0, height - 1) or c in (0, width - 1)]
    random.shuffle(border)
    for cell in border:
      if not _seven_ok(grid, cell, near_domino, rows_no7, cols_no7, []):
        continue
      if any(_on_line(cell, d) for d in dominoes):
        continue
      grid[cell[0]][cell[1]] = MARK
      break
  for ln in perp_lines:
    if _line_has_seven(grid, ln):
      return None
  colored = []
  flips = 0
  for d in dominoes:
    end = _facing_end(grid, d)
    if end is None:
      return None
    first = random.choice(COLORS)
    if (first == 6) != (end == 0):
      flips += 1
    colored.append((d[0], d[1], d[2], first))
  if flips == 0:
    i = random.randrange(len(colored))
    y, x, o, first = colored[i]
    colored[i] = (y, x, o, 7 - first)
  sevens = [(r, c) for r in range(height) for c in range(width)
            if grid[r][c] == MARK]
  return colored, sevens


def _sample_side():
  """Samples one grid side, mostly in the fixture range."""
  if random.random() < 0.75:
    return random.randint(8, 20)
  return random.randint(21, MAX_SIDE)


def _sample_scene(height, width, double_prob, distractor_prob):
  """Samples (height, width, dominoes, sevens) for a fresh random scene.

  A height or width that is given is honoured; missing sides are sampled.
  """
  for side in (height, width):
    if side is not None and not MIN_SIDE <= side <= MAX_SIDE:
      raise ValueError('random scenes need sides in %d..%d'
                       % (MIN_SIDE, MAX_SIDE))
  for _ in range(100):
    if height is None and width is None:
      h = _sample_side()
      w = h if random.random() < 0.6 else _sample_side()
    else:
      h = height if height is not None else _sample_side()
      w = width if width is not None else _sample_side()
    scene = _try_scene(h, w, double_prob, distractor_prob)
    if scene is not None:
      return h, w, scene[0], scene[1]
  raise RuntimeError('could not construct a domino scene of the requested '
                     'size')


def _check_prob(name, value, default):
  """Returns a probability argument or its default; rejects bad values."""
  if value is None:
    return default
  if not 0.0 <= value <= 1.0:
    raise ValueError('%s must be in [0, 1]' % name)
  return value


def _check_latents(height, width, dominoes, sevens):
  """Raises ValueError for malformed explicit scene parameters."""
  if not (1 <= height <= MAX_SIDE and 1 <= width <= MAX_SIDE):
    raise ValueError('grid sides must be in 1..30')
  used = set()
  for r, c in sevens:
    if not (0 <= r < height and 0 <= c < width) or (r, c) in used:
      raise ValueError('bad 7 position %r' % ((r, c),))
    used.add((r, c))
  for d in dominoes:
    if len(d) != 4 or d[2] not in ('h', 'v') or d[3] not in COLORS:
      raise ValueError('bad domino %r' % (d,))
    for cy, cx in _domino_cells(d):
      if not (0 <= cy < height and 0 <= cx < width) or (cy, cx) in used:
        raise ValueError('domino %r is out of bounds or overlaps' % (d,))
      used.add((cy, cx))


def generate(height=None, width=None, dominoes=None, sevens=None,
             double_seven_prob=None, distractor_prob=None):
  """Returns an input/output pair for task f341894c.

  Args:
    height: number of rows. If dominoes/sevens are omitted, a random scene
      of this height (6..30) is built; otherwise height is required.
    width: number of columns, with the same treatment as height.
    dominoes: list of (row, col, orient, first_color) tuples. (row, col) is
      the left cell of a horizontal ('h') domino or the top cell of a
      vertical ('v') domino. first_color is the input colour (1 or 6) of
      that cell; the other cell gets the complementary colour.
    sevens: list of (row, col) positions of the 7 marks. Must be given
      together with dominoes.
    double_seven_prob: random mode only. Chance that an isolated domino
      gets a 7 at both ends of its line (default 0.08). With 0, every
      domino line carries exactly one 7.
    distractor_prob: random mode only. Chance of one extra border 7 that
      lies off every domino line (default 0.25).

  If dominoes and sevens are both None, a fresh random scene is sampled.
  Supplying only one of them raises ValueError. Explicit scenes must give
  every domino a unique nearest 7 and must pair unambiguously; otherwise
  ValueError is raised.
  """
  if (dominoes is None) != (sevens is None):
    raise ValueError('dominoes and sevens must be given together')
  if dominoes is None:
    dp = _check_prob('double_seven_prob', double_seven_prob,
                     DEFAULT_DOUBLE_PROB)
    xp = _check_prob('distractor_prob', distractor_prob,
                     DEFAULT_DISTRACTOR_PROB)
    height, width, dominoes, sevens = _sample_scene(height, width, dp, xp)
  else:
    if double_seven_prob is not None or distractor_prob is not None:
      raise ValueError('sampling probabilities apply only to random scenes')
    if height is None or width is None:
      raise ValueError('explicit dominoes/sevens require height and width')
  _check_latents(height, width, dominoes, sevens)
  grid = common.grid(width, height, BACKGROUND)
  for r, c in sevens:
    grid[r][c] = MARK
  for y, x, orient, first in dominoes:
    (ay, ax), (by, bx) = _domino_cells((y, x, orient))
    grid[ay][ax] = first
    grid[by][bx] = 7 - first
  _check_pairing(grid, dominoes)
  output = [row[:] for row in grid]
  for domino in dominoes:
    end = _facing_end(grid, domino)
    if end is None:
      raise ValueError('domino %r has no unique nearest 7' % (domino,))
    cells = _domino_cells(domino)
    (sy, sx), (oy, ox) = cells[end], cells[1 - end]
    output[sy][sx] = 6
    output[oy][ox] = 1
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the canonical train/test pairs from explicit latents."""
  train = [
      generate(height=10, width=10,
               dominoes=[(2, 0, 'h', 1), (4, 4, 'h', 6), (5, 2, 'v', 6),
                         (5, 6, 'v', 6), (7, 7, 'v', 6)],
               sevens=[(0, 7), (2, 9), (4, 9), (9, 2), (9, 6)]),
      generate(height=8, width=8,
               dominoes=[(2, 1, 'v', 6), (2, 7, 'v', 1), (3, 3, 'v', 1),
                         (6, 5, 'h', 1)],
               sevens=[(0, 1), (0, 7), (6, 0), (7, 3)]),
      generate(height=14, width=14,
               dominoes=[(1, 2, 'h', 1), (4, 8, 'h', 6), (5, 8, 'h', 1),
                         (6, 4, 'v', 1), (6, 12, 'v', 6), (10, 7, 'h', 1),
                         (12, 0, 'v', 1)],
               sevens=[(0, 0), (0, 12), (1, 13), (4, 13), (5, 13), (10, 13),
                       (13, 4)]),
  ]
  test = [
      generate(height=18, width=18,
               dominoes=[(1, 2, 'h', 6), (2, 14, 'h', 6), (3, 4, 'h', 1),
                         (5, 8, 'h', 1), (6, 8, 'h', 6), (7, 8, 'h', 1),
                         (8, 8, 'h', 6), (9, 10, 'v', 1), (10, 11, 'v', 1),
                         (12, 3, 'h', 1), (13, 6, 'v', 1), (13, 7, 'v', 1),
                         (13, 13, 'v', 6), (15, 14, 'h', 1)],
               sevens=[(0, 6), (0, 7), (0, 10), (0, 13), (1, 0), (2, 17),
                       (3, 0), (5, 17), (6, 17), (7, 0), (8, 17), (12, 0),
                       (15, 0), (17, 11)]),
  ]
  return {'train': train, 'test': test}
