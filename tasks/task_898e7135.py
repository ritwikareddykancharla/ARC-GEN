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

"""Task 898e7135: fit scaled puzzle pieces into the holes of an enlarged board.

Rule: the input has three kinds of object on a black background.
  * A solid single-colour board with background holes punched into it.
  * Several puzzle pieces drawn at an integer scale k, so every logical cell
    is a k x k block.
  * Noise in one extra colour: scattered single dots, and possibly a few
    small dominoes or trominoes.
The noise is discarded. The output is the board enlarged by k. Each hole is
painted with the colour of the piece whose logical shape equals the hole's
shape under some rotation or reflection. Each piece fills exactly one hole.

Scope of the random sampler:
  * The background is 0. By default k is 2 or 3. k=4 may be requested as a
    synthetic extension. The chosen scale is retained across retries, rather
    than resampled toward easier layouts. At k=4 the board is 6..7 cells per side and the
    holes are only monominoes and dominoes (rarely an I-tromino), because
    every scaled piece box must stay smaller than the board box.
  * Board sides are 5..30 // k, so the output is at most 30x30.
  * There are 2..6 holes (2..3 at k=4). Each hole is a 4-connected polyomino
    of 1..7 cells that fits a 3x4 box (k=2) or a 3x3 box (k>=3), which
    includes 7-cell shapes such as the test's H.
  * Holes never enclose a board cell and never touch the outer ring of the
    board. Holes are never 8-adjacent to each other, and the board stays
    4-connected.
  * Every scene has at least two non-congruent hole classes, and at least
    one hole has 2 or more cells, so colours cannot be assigned trivially.
    Some holes repeat an earlier shape class; the pieces then share a
    colour. Others compete with an earlier hole: same cell count, different
    shape. For k<4 scenes with 3 or more holes, competitor-free layouts are
    resampled half the time.
  * Logical hole dimensions have gcd 1, so the scale k is recoverable.
  * Each piece is a random rotation or reflection of its hole, drawn at
    scale k. Every scaled piece box is strictly smaller than the board box.
    Congruent pieces share a colour, and distinct classes get distinct
    colours.
  * Piece boxes and the board box are separated by at least one empty row
    or column, including diagonally.
  * Noise is 0..2 dominoes or I/L trominoes plus 3..15 single dots.
    Placement rules for noise:
      - every noise component is 8-isolated;
      - no noise lies in or touches the board box;
      - noise may sit inside a concave piece's box, as it does in the test
        fixture, but never touches a piece cell.
  * The input grid is 12..30 per side by default. A requested height or
    width may be 10..30. With an explicit k it must be at least 10 (k=2),
    12 (k=3) or 14 (k=4). Sizes above the fixture sizes are synthetic
    extensions of the same rule.

Explicit scenes can extend this sampling vocabulary: a single shape class,
only monomino holes, larger noise components accompanied by an isolated dot,
or a scale above 4 are accepted when the geometric and identifiability checks
pass. Noise is removed by its colour once the isolated dots identify it. At
k=4 the random vocabulary has no equal-area competing shapes; these are
scale/assembly exercises rather than hard shape-discrimination examples.
A random construction can exhaust its 1000 attempts with RuntimeError; the
documented minimum dimensions are sampling bounds, not a packing guarantee.
"""

import math
import random

import common


_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

_MAPS = (
    lambda r, c: (r, c), lambda r, c: (r, -c),
    lambda r, c: (-r, c), lambda r, c: (-r, -c),
    lambda r, c: (c, r), lambda r, c: (c, -r),
    lambda r, c: (-c, r), lambda r, c: (-c, -r),
)

_SIZES = (1, 2, 3, 4, 5, 6, 7)
_SIZE_WEIGHTS = (3, 2, 3, 3, 3, 2, 2)

_MIN_SIDE = {2: 10, 3: 12, 4: 14}

_NOISE_CLUSTERS = (
    ((0, 0), (0, 1)), ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (0, 2)), ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (1, 1)), ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)), ((0, 1), (1, 0), (1, 1)),
)


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _normalize(cells):
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _symmetries(cells):
  return [_normalize([m(r, c) for r, c in cells]) for m in _MAPS]


def _canon(cells):
  return min(_symmetries(cells))


def _dims(cells):
  cells = _normalize(cells)
  return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _connected(cells):
  """True if the cell set is non-empty and 4-connected."""
  cells = set(cells)
  if not cells:
    return False
  start = min(cells)
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr, dc in _DIRS4:
      n = (r + dr, c + dc)
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _polyomino(size, lim_h, lim_w):
  """Random 4-connected polyomino of `size` cells inside lim_h x lim_w."""
  cells = {(0, 0)}
  while len(cells) < size:
    r_lo = min(r for r, _ in cells)
    r_hi = max(r for r, _ in cells)
    c_lo = min(c for _, c in cells)
    c_hi = max(c for _, c in cells)
    cand = set()
    for r, c in cells:
      for dr, dc in _DIRS4:
        n = (r + dr, c + dc)
        if n in cells:
          continue
        if max(r_hi, n[0]) - min(r_lo, n[0]) + 1 > lim_h:
          continue
        if max(c_hi, n[1]) - min(c_lo, n[1]) + 1 > lim_w:
          continue
        cand.add(n)
    if not cand:
      return None
    cells.add(random.choice(sorted(cand)))
  return _normalize(cells)


def _encloses(shape):
  """True if the shape fully encloses some non-shape cell (4-connectivity)."""
  h, w = _dims(shape)
  cells = set(_normalize(shape))
  seen = {(-1, -1)}
  stack = [(-1, -1)]
  while stack:
    r, c = stack.pop()
    for dr, dc in _DIRS4:
      n = (r + dr, c + dc)
      if (-1 <= n[0] <= h and -1 <= n[1] <= w and n not in cells
          and n not in seen):
        seen.add(n)
        stack.append(n)
  return len(seen) + len(cells) < (h + 2) * (w + 2)


def _to_mask(cells):
  cells = _normalize(cells)
  h, w = _dims(cells)
  rows = [['0'] * w for _ in range(h)]
  for r, c in cells:
    rows[r][c] = '1'
  return [''.join(row) for row in rows]


def _board_connected(bh, bw, holes):
  cells = [(r, c) for r in range(bh) for c in range(bw) if (r, c) not in holes]
  return _connected(cells)


def _has_competitor(holes):
  """True if two non-congruent holes share a cell count."""
  by_size = {}
  for cells in holes:
    by_size.setdefault(len(cells), set()).add(_canon(cells))
  return any(len(v) >= 2 for v in by_size.values())


def _rects_touch(a, b):
  """True if two (row, col, h, w) boxes overlap or touch (8-adjacency)."""
  r, c, h, w = a
  r2, c2, h2, w2 = b
  return (r < r2 + h2 + 1 and r2 < r + h + 1 and
          c < c2 + w2 + 1 and c2 < c + w + 1)


def _piece_cells(pieces, k):
  cells = set()
  for pr, pc, _, mask in pieces:
    for r, row in enumerate(mask):
      for c, ch in enumerate(row):
        if ch == '1':
          for dr in range(k):
            for dc in range(k):
              cells.add((pr + r * k + dr, pc + c * k + dc))
  return cells


def _render(height, width, k, board, board_colour, board_pos, pieces,
            noise_colour, noise):
  grid = common.grid(width, height, 0)
  br, bc = board_pos
  for r, row in enumerate(board):
    for c, ch in enumerate(row):
      grid[br + r][bc + c] = board_colour if ch == '#' else 0
  for pr, pc, colour, mask in pieces:
    for r, row in enumerate(mask):
      for c, ch in enumerate(row):
        if ch == '1':
          for dr in range(k):
            for dc in range(k):
              grid[pr + r * k + dr][pc + c * k + dc] = colour
  for r, c in noise:
    grid[r][c] = noise_colour
  bh, bw = len(board), len(board[0])
  output = common.grid(bw * k, bh * k, board_colour)
  for r in range(bh * k):
    for c in range(bw * k):
      ch = board[r // k][c // k]
      output[r][c] = board_colour if ch == '#' else int(ch)
  return grid, output


def _zero_majority(grid):
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  zeros = counts.pop(0, 0)
  return not counts or zeros > max(counts.values())


def _draw_shape(lim_h, lim_w, used):
  """Draws a hole shape: a repeat, a same-size competitor, or a fresh one."""
  canons = {_canon(s) for s in used}
  roll = random.random()
  if used and roll < 0.2:
    return random.choice(_symmetries(random.choice(used)))
  big = [s for s in used if len(s) >= 3]
  if big and roll < 0.55:
    base = _polyomino(len(random.choice(big)), lim_h, lim_w)
    if base is None or _canon(base) in canons:
      return None
  else:
    base = _polyomino(random.choices(_SIZES, _SIZE_WEIGHTS)[0], lim_h, lim_w)
    if base is None:
      return None
  if _encloses(base):
    return None
  return random.choice(_symmetries(base))


def _k_fits(kk, height, width):
  return ((height is None or height >= _MIN_SIDE[kk]) and
          (width is None or width >= _MIN_SIDE[kk]))


def _sample(k, height, width, board_colour, noise_colour):
  kk = k if k is not None else random.choice(
      [c for c in (2, 2, 3) if _k_fits(c, height, width)])
  for _ in range(1000):
    lo = max(12, _MIN_SIDE[kk])
    gh = height if height is not None else random.randint(lo, 30)
    gw = width if width is not None else random.randint(lo, 30)
    maxs = 30 // kk
    bmin = 6 if kk == 4 else 5
    side = random.random() < 0.5
    if side:
      bh_max, bw_max = min(maxs, gh), min(maxs, gw - kk - 1)
    else:
      bh_max, bw_max = min(maxs, gh - kk - 1), min(maxs, gw)
    if bh_max < bmin or bw_max < bmin:
      continue
    bh = random.randint(bmin, bh_max)
    bw = random.randint(bmin, bw_max)
    lim_h, lim_w = (3, 4) if kk == 2 else (3, 3)
    n = random.randint(2, 3 if kk == 4 else 6)
    holes, occupied, used = [], set(), []
    for _ in range(n):
      for _ in range(60):
        shape = _draw_shape(lim_h, lim_w, used)
        if shape is None:
          continue
        h, w = _dims(shape)
        if h > bh - 2 or w > bw - 2 or kk * h * kk * w >= bh * bw:
          continue
        r0 = random.randint(1, bh - 1 - h)
        c0 = random.randint(1, bw - 1 - w)
        cells = [(r0 + r, c0 + c) for r, c in shape]
        if any((r + dr, c + dc) in occupied for r, c in cells
               for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
          continue
        occupied.update(cells)
        holes.append(cells)
        used.append(shape)
        break
    if len(holes) < 2 or not _board_connected(bh, bw, occupied):
      continue
    # Non-trivial assignment: at least two classes and a non-monomino hole.
    if (len({_canon(c) for c in holes}) < 2 or
        max(len(c) for c in holes) < 2):
      continue
    if (kk < 4 and len(holes) >= 3 and not _has_competitor(holes)
        and random.random() < 0.5):
      continue
    g = 0
    for shape in used:
      h, w = _dims(shape)
      g = math.gcd(math.gcd(g, h), w)
    if g != 1:
      continue
    palette = [c for c in range(1, 10) if c not in (board_colour, noise_colour)]
    random.shuffle(palette)
    bcol = board_colour if board_colour is not None else palette.pop()
    ncol = noise_colour if noise_colour is not None else palette.pop()
    class_colour, hole_colours = {}, []
    for cells in holes:
      key = _canon(cells)
      if key not in class_colour:
        class_colour[key] = palette.pop()
      hole_colours.append(class_colour[key])
    rows = [['#'] * bw for _ in range(bh)]
    for cells, colour in zip(holes, hole_colours):
      for r, c in cells:
        rows[r][c] = str(colour)
    board = [''.join(row) for row in rows]
    br = random.choice([0, gh - bh, random.randint(0, gh - bh)])
    bc = random.choice([0, gw - bw, random.randint(0, gw - bw)])
    rects = [(br, bc, bh, bw)]
    order = list(range(len(holes)))
    random.shuffle(order)
    pieces, ok = [], True
    for i in order:
      syms = sorted(set(_symmetries(holes[i])))
      placed = False
      for _ in range(300):
        shape = random.choice(syms)
        h, w = _dims(shape)
        ph, pw = h * kk, w * kk
        if ph > gh or pw > gw:
          continue
        r = random.randint(0, gh - ph)
        c = random.randint(0, gw - pw)
        box = (r, c, ph, pw)
        if not any(_rects_touch(box, other) for other in rects):
          rects.append(box)
          pieces.append((r, c, hole_colours[i], _to_mask(shape)))
          placed = True
          break
      if not placed:
        ok = False
        break
    if not ok:
      continue
    # Noise must avoid the whole board box and the actual piece cells.
    blk = _piece_cells(pieces, kk)
    blk.update((br + r, bc + c) for r in range(bh) for c in range(bw))

    def free(r, c):
      if not (0 <= r < gh and 0 <= c < gw):
        return False
      return all((r + dr, c + dc) not in blk
                 for dr in (-1, 0, 1) for dc in (-1, 0, 1))

    noise = []
    for _ in range(random.choice([0, 0, 1, 1, 2])):
      for _ in range(50):
        shape = random.choice(_NOISE_CLUSTERS)
        r = random.randint(0, gh - 1)
        c = random.randint(0, gw - 1)
        cells = [(r + dr, c + dc) for dr, dc in shape]
        if all(free(y, x) for y, x in cells):
          noise.extend(cells)
          blk.update(cells)
          break
    want = random.randint(3, 15)
    singles = 0
    for _ in range(400):
      if singles >= want:
        break
      r = random.randint(0, gh - 1)
      c = random.randint(0, gw - 1)
      if free(r, c):
        noise.append((r, c))
        blk.add((r, c))
        singles += 1
    if singles < 3:
      continue
    params = (gh, gw, kk, board, bcol, (br, bc), pieces, ncol, noise)
    grid, _ = _render(*params)
    if not _zero_majority(grid):
      continue
    return params
  raise RuntimeError('could not sample a valid scene for the requested controls')


def _check_explicit(height, width, k, board, board_colour, board_pos, pieces,
                    noise_colour, noise):
  """Rejects explicit scenes that would not be valid, unambiguous task pairs."""
  for name, v in (('height', height), ('width', width), ('k', k),
                  ('board_colour', board_colour),
                  ('noise_colour', noise_colour)):
    if not _is_int(v):
      raise ValueError(name + ' must be an int')
  if not (1 <= height <= 30 and 1 <= width <= 30):
    raise ValueError('height and width must be in 1..30')
  if k < 2:
    raise ValueError('k must be at least 2')
  if (not isinstance(board, (list, tuple)) or not board or
      not all(isinstance(row, str) for row in board)):
    raise ValueError('board must be a non-empty list of strings')
  bh, bw = len(board), len(board[0])
  if bw == 0 or any(len(row) != bw for row in board):
    raise ValueError('board must be a non-empty rectangle')
  if bh < 3 or bw < 3:
    raise ValueError('board must be at least 3x3')
  if bh * k > 30 or bw * k > 30:
    raise ValueError('scaled board exceeds 30x30')
  if not (1 <= board_colour <= 9 and 1 <= noise_colour <= 9):
    raise ValueError('colours must be in 1..9')
  if board_colour == noise_colour:
    raise ValueError('board_colour and noise_colour must differ')
  if (not isinstance(board_pos, (list, tuple)) or len(board_pos) != 2 or
      not all(_is_int(v) for v in board_pos)):
    raise ValueError('board_pos must be a (row, col) pair of ints')
  br, bc = board_pos
  if br < 0 or bc < 0 or br + bh > height or bc + bw > width:
    raise ValueError('board out of bounds')
  holes = set()
  for r, row in enumerate(board):
    for c, ch in enumerate(row):
      if ch == '#':
        continue
      if ch not in '123456789' or int(ch) in (board_colour, noise_colour):
        raise ValueError('hole digits must be 1..9 and differ from board/noise')
      if r in (0, bh - 1) or c in (0, bw - 1):
        raise ValueError('holes may not touch the board rim')
      holes.add((r, c))
  if not holes:
    raise ValueError('board needs at least one hole')
  if not _board_connected(bh, bw, holes):
    raise ValueError('board cells must be 4-connected')
  # Hole components (4-connected), single colour, mutually 8-separated.
  comp_of, comps = {}, []
  for start in sorted(holes):
    if start in comp_of:
      continue
    comp, stack = [], [start]
    comp_of[start] = len(comps)
    while stack:
      y, x = stack.pop()
      comp.append((y, x))
      for dy, dx in _DIRS4:
        n = (y + dy, x + dx)
        if n in holes and n not in comp_of:
          comp_of[n] = len(comps)
          stack.append(n)
    comps.append(comp)
  hole_classes = {}
  for idx, comp in enumerate(comps):
    digits = {board[y][x] for y, x in comp}
    if len(digits) != 1:
      raise ValueError('a hole mixes colours')
    for y, x in comp:
      for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
          n = (y + dy, x + dx)
          if n in comp_of and comp_of[n] != idx:
            raise ValueError('holes must not touch each other')
    hole_classes.setdefault(int(digits.pop()), []).append(_canon(comp))
  if not isinstance(pieces, (list, tuple)) or not pieces:
    raise ValueError('at least one piece is required')
  rects = [(br, bc, bh, bw)]
  piece_classes = {}
  g = 0
  for entry in pieces:
    if not isinstance(entry, (list, tuple)) or len(entry) != 4:
      raise ValueError('each piece is (row, col, colour, mask)')
    pr, pc, colour, mask = entry
    if not (_is_int(pr) and _is_int(pc) and _is_int(colour)):
      raise ValueError('piece row, col and colour must be ints')
    if not 1 <= colour <= 9 or colour in (board_colour, noise_colour):
      raise ValueError('bad piece colour')
    if (not isinstance(mask, (list, tuple)) or not mask or
        not all(isinstance(row, str) for row in mask)):
      raise ValueError('piece mask must be a non-empty list of strings')
    mh, mw = len(mask), len(mask[0])
    if mw == 0 or any(len(row) != mw or set(row) - set('01') for row in mask):
      raise ValueError('piece mask must be a rectangle of 0/1')
    cells = [(r, c) for r, row in enumerate(mask)
             for c, ch in enumerate(row) if ch == '1']
    if not cells:
      raise ValueError('empty piece mask')
    if (min(r for r, _ in cells) != 0 or min(c for _, c in cells) != 0 or
        max(r for r, _ in cells) != mh - 1 or
        max(c for _, c in cells) != mw - 1):
      raise ValueError('piece mask must be tight to its shape')
    if not _connected(cells):
      raise ValueError('piece mask must be 4-connected')
    if pr < 0 or pc < 0 or pr + mh * k > height or pc + mw * k > width:
      raise ValueError('piece out of bounds')
    if mh * k * mw * k >= bh * bw:
      raise ValueError('every piece box must be smaller than the board box')
    g = math.gcd(math.gcd(g, mh), mw)
    rects.append((pr, pc, mh * k, mw * k))
    piece_classes.setdefault(colour, []).append(_canon(cells))
  if g != 1:
    raise ValueError('logical piece dimensions must have gcd 1')
  for i in range(len(rects)):
    for j in range(i + 1, len(rects)):
      if _rects_touch(rects[i], rects[j]):
        raise ValueError('board and piece boxes must not overlap or touch')
  pcells = _piece_cells(pieces, k)
  if not isinstance(noise, (list, tuple)):
    raise ValueError('noise must be a list of (row, col) cells')
  nset = set()
  for entry in noise:
    if (not isinstance(entry, (list, tuple)) or len(entry) != 2 or
        not all(_is_int(v) for v in entry)):
      raise ValueError('noise cells must be (row, col) int pairs')
    r, c = entry
    if not (0 <= r < height and 0 <= c < width):
      raise ValueError('noise out of bounds')
    if (r, c) in nset:
      raise ValueError('duplicate noise cell')
    if br - 1 <= r <= br + bh and bc - 1 <= c <= bc + bw:
      raise ValueError('noise may not lie in or touch the board box')
    if any((r + dr, c + dc) in pcells for dr in (-1, 0, 1)
           for dc in (-1, 0, 1)):
      raise ValueError('noise may not lie on or touch a piece')
    nset.add((r, c))
  if nset and not any(
      all((r + dr, c + dc) not in nset for dr in (-1, 0, 1)
          for dc in (-1, 0, 1) if (dr, dc) != (0, 0))
      for r, c in nset):
    raise ValueError('noise needs at least one isolated single dot')
  for colour in set(hole_classes) | set(piece_classes):
    if sorted(hole_classes.get(colour, [])) != sorted(piece_classes.get(colour, [])):
      raise ValueError('holes and pieces of colour %d do not match' % colour)
  owner = {}
  for colour, shapes in piece_classes.items():
    for s in shapes:
      if owner.setdefault(s, colour) != colour:
        raise ValueError('congruent pieces must share a colour')
  grid, _ = _render(height, width, k, board, board_colour, board_pos, pieces,
                    noise_colour, noise)
  if not _zero_majority(grid):
    raise ValueError('background 0 must be the majority colour')


def generate(height=None, width=None, k=None, board=None, board_colour=None,
             board_pos=None, pieces=None, noise_colour=None, noise=None):
  """Returns an input/output pair.

  Args:
    height: input grid height (int). In random mode 10..30, and at least 12
      for k=3 or 14 for k=4.
    width: input grid width (int), with the same limits as height.
    k: integer scale of the pieces. In random mode, 2, 3 or 4; explicit
      scenes allow larger integers only if their scaled geometry fits.
    board: list of strings describing the board. '#' marks a board cell, and
      a digit marks a hole that becomes that colour in the output.
    board_colour: colour of the board, 1..9.
    board_pos: (row, col) of the board's top-left cell in the input.
    pieces: list of (row, col, colour, mask) tuples. Each mask is a list of
      '0'/'1' strings giving the logical piece shape as drawn.
    noise_colour: colour of the noise, 1..9 and different from the board.
    noise: list of (row, col) noise cells.

  If board is None, a fresh random scene is sampled. height, width, k,
  board_colour and noise_colour are then honoured as sampling controls.
  board_pos, pieces and noise need an explicit board and are rejected
  otherwise. If board is given, every argument must be supplied; noise may
  be an empty list. Explicit scenes may use one congruence class or larger
  noise components; nonempty noise must include an isolated dot to identify
  its colour. An explicit scene must also pass these checks:
    * types, bounds and colours are valid;
    * holes and pieces are congruent and holes stay off the board rim;
    * holes are separated from each other and the board stays connected;
    * boxes are separated from each other;
    * noise is isolated from the board and the pieces;
    * the piece gcd is 1 and the background is the majority colour.
  """
  if board is None:
    if board_pos is not None or pieces is not None or noise is not None:
      raise ValueError('board_pos, pieces and noise require an explicit board')
    for name, v in (('height', height), ('width', width), ('k', k),
                    ('board_colour', board_colour),
                    ('noise_colour', noise_colour)):
      if v is not None and not _is_int(v):
        raise ValueError(name + ' must be an int')
    if k is not None and k not in (2, 3, 4):
      raise ValueError('k must be 2, 3 or 4 for random scenes')
    for name, v in (('height', height), ('width', width)):
      if v is not None and not 10 <= v <= 30:
        raise ValueError(name + ' must be in 10..30 for random scenes')
    if k is not None and not _k_fits(k, height, width):
      raise ValueError('height/width must be at least %d for k=%d'
                       % (_MIN_SIDE[k], k))
    for name, v in (('board_colour', board_colour),
                    ('noise_colour', noise_colour)):
      if v is not None and not 1 <= v <= 9:
        raise ValueError(name + ' must be in 1..9')
    if board_colour is not None and board_colour == noise_colour:
      raise ValueError('board_colour and noise_colour must differ')
    params = _sample(k, height, width, board_colour, noise_colour)
  else:
    missing = [name for name, v in (
        ('height', height), ('width', width), ('k', k),
        ('board_colour', board_colour), ('board_pos', board_pos),
        ('pieces', pieces), ('noise_colour', noise_colour), ('noise', noise))
               if v is None]
    if missing:
      raise ValueError('explicit scene missing: ' + ', '.join(missing))
    _check_explicit(height, width, k, board, board_colour, board_pos, pieces,
                    noise_colour, noise)
    params = (height, width, k, board, board_colour, tuple(board_pos),
              [tuple(p) for p in pieces], noise_colour,
              [tuple(n) for n in noise])
  grid, output = _render(*params)
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the original task pairs from explicit latent scenes."""
  train = [
      generate(height=20, width=15, k=2,
               board=['######', '#88#1#', '#8####', '####3#', '##333#',
                      '######'],
               board_colour=2, board_pos=(0, 0),
               pieces=[(3, 7, 8, ['01', '11']), (10, 2, 1, ['1']),
                       (11, 9, 3, ['11', '10', '10'])],
               noise_colour=7,
               noise=[(0, 8), (3, 13), (7, 1), (8, 7), (12, 5), (15, 2),
                      (15, 14), (17, 6), (19, 12)]),
      generate(height=19, width=30, k=2,
               board=['##########', '#####4####', '#5###4444#', '########4#',
                      '##########', '#####6####', '####666###', '#####6####',
                      '##########', '#11#######', '#1########', '#11####5##',
                      '#1########', '##########'],
               board_colour=3, board_pos=(0, 20),
               pieces=[(2, 5, 1, ['1111', '0101']), (2, 16, 5, ['1']),
                       (8, 11, 4, ['0001', '1111', '1000']),
                       (10, 2, 6, ['010', '111', '010']), (15, 15, 5, ['1'])],
               noise_colour=8,
               noise=[(0, 14), (3, 1), (6, 1), (8, 7), (15, 20), (15, 24),
                      (17, 9), (18, 27)]),
  ]
  test = [
      generate(height=30, width=30, k=3,
               board=['##########', '#8#8##5#5#', '#888##555#', '#8#8####5#',
                      '#####3####', '##########', '#666#999##', '##6##9####',
                      '##6##9##3#', '##########'],
               board_colour=4, board_pos=(10, 0),
               pieces=[(0, 1, 8, ['111', '010', '111']), (7, 13, 3, ['1']),
                       (9, 18, 5, ['101', '111', '001']),
                       (20, 18, 9, ['100', '100', '111']), (21, 1, 3, ['1']),
                       (21, 7, 6, ['100', '111', '100'])],
               noise_colour=2,
               noise=[(0, 28), (1, 16), (2, 23), (3, 26), (4, 13), (4, 19),
                      (4, 26), (4, 27), (6, 23), (13, 14), (16, 13), (17, 15),
                      (21, 13), (21, 24), (22, 26), (23, 26), (27, 1),
                      (27, 3)]),
  ]
  return {'train': train, 'test': test}
