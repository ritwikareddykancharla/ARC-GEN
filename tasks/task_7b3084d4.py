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

"""ARC task 7b3084d4: reassemble scattered jigsaw pieces into a square.

Rule: the black input holds four separated pieces. Each piece has one colour
and is connected through edges or corners. The 7 piece also carries a single 5
cell. The pieces are rotated, never mirrored, parts of an NxN square, where
N*N is the number of coloured cells. The output is that square, with the 5 at
the top-left cell and each piece covering exactly one of the four corners.

Generation builds the answer first.

1. Cut an NxN square into four quadrant pieces at random split lines.
2. Push at least one short straight tab across a piece boundary so the pieces
   interlock. Tab start cells are drawn from the piece boundaries. Each piece
   stays 8-connected, keeps its own corner and holds at least 3 cells.
3. Colour the top-left piece 7 and set its corner cell to 5. The other three
   pieces get three distinct colours from {1,2,3,4,6,8,9}.
4. Reject any square whose pieces admit a second valid assembly. A valid
   assembly has the 5 at the top-left and four distinct corner owners. This
   bounded enumerator only enforces the constraint. The output is always the
   constructed square. The check also applies to explicit squares.
5. Rotate each piece by a random number of quarter turns. Place it at a
   uniformly chosen legal spot of the input. No two pieces may touch, even
   diagonally. This is enforced for explicit placements as well.

Scope:

- N is sampled from 4..14; the test uses N=14. An explicit size may be 4..16.
  An explicit square may have N from 4 to 21, limited by input area.
- There are always four pieces.
- Every example input is 20x20, and the generator samples 20x20 often. Other
  input sizes up to 30x30 are synthetic extensions. The input area must
  exceed 2*N*N so that black stays a strict majority.
- The 5 marker, its 7 piece and the black background are fixed, as in every
  example.
"""

import random

import common

BACKGROUND = 0
SIZE = 20
MARK = 5
MARK_COLOR = 7
OTHER_COLORS = [1, 2, 3, 4, 6, 8, 9]
DIRS4 = [(0, 1), (0, -1), (1, 0), (-1, 0)]
MAX_EXPLICIT_N = 21


def _is_int(v):
  """True for a genuine int (bool is rejected)."""
  return isinstance(v, int) and not isinstance(v, bool)


def _key(v):
  """Piece key of a square cell value (the 5 belongs to the 7 piece)."""
  return MARK_COLOR if v == MARK else v


def _rotate(arr, k):
  """Rotates a list of rows k quarter turns counter-clockwise."""
  for _ in range(k % 4):
    h, w = len(arr), len(arr[0])
    arr = [[arr[j][w - 1 - i] for j in range(h)] for i in range(w)]
  return arr


def _pieces(square):
  """Maps piece key to its bounding-box array (-1 marks empty cells)."""
  groups = {}
  for y, row in enumerate(square):
    for x, v in enumerate(row):
      groups.setdefault(_key(v), []).append((y, x, v))
  result = {}
  for key, cells in groups.items():
    y0 = min(c[0] for c in cells)
    x0 = min(c[1] for c in cells)
    y1 = max(c[0] for c in cells)
    x1 = max(c[1] for c in cells)
    arr = [[-1] * (x1 - x0 + 1) for _ in range(y1 - y0 + 1)]
    for y, x, v in cells:
      arr[y - y0][x - x0] = v
    result[key] = arr
  return result


def _connected(cells):
  """True if the set of (y, x) cells is non-empty and 8-connected."""
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    y, x = stack.pop()
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        nb = (y + dy, x + dx)
        if nb in cells and nb not in seen:
          seen.add(nb)
          stack.append(nb)
  return len(seen) == len(cells)


def _check_square(square):
  """Validates an explicit answer square and returns a copy of it."""
  if not isinstance(square, (list, tuple)) or any(not isinstance(row, (list, tuple)) for row in square):
    raise ValueError('square must be a sequence of rows')
  n = len(square)
  if n < 4 or n > MAX_EXPLICIT_N or any(len(row) != n for row in square):
    raise ValueError('square must be NxN with 4 <= N <= %d' % MAX_EXPLICIT_N)
  if any(not _is_int(v) for row in square for v in row):
    raise ValueError('square cells must be integers')
  sq = [list(row) for row in square]
  if sq[0][0] != MARK or sum(v == MARK for row in sq for v in row) != 1:
    raise ValueError('square needs exactly one 5, at the top-left cell')
  keys = set(_key(v) for row in sq for v in row)
  if (len(keys) != 4 or MARK_COLOR not in keys or
      not keys - {MARK_COLOR} <= set(OTHER_COLORS)):
    raise ValueError('square needs the 7 piece plus three other colours')
  for key in keys:
    cells = {(y, x) for y in range(n) for x in range(n)
             if _key(sq[y][x]) == key}
    if not _connected(cells):
      raise ValueError('every piece must be 8-connected')
  corners = {_key(sq[0][0]), _key(sq[0][n - 1]), _key(sq[n - 1][0]),
             _key(sq[n - 1][n - 1])}
  if len(corners) != 4:
    raise ValueError('each piece must own exactly one corner')
  return sq


def _render(square, placements, height, width):
  """Draws the rotated pieces of square into a height x width input.

  Raises ValueError for out-of-bounds, overlapping or touching pieces.
  """
  pieces = _pieces(square)
  for p in placements:
    if len(p) != 4 or not all(_is_int(v) for v in p):
      raise ValueError('each placement is (colour, turns, row, col) ints')
  if sorted(p[0] for p in placements) != sorted(pieces):
    raise ValueError('placements must list every piece exactly once')
  grid = common.grid(width, height, BACKGROUND)
  tag = [[-1] * width for _ in range(height)]
  for idx, (color, k, r, c) in enumerate(placements):
    arr = _rotate(pieces[color], k)
    for i, row in enumerate(arr):
      for j, v in enumerate(row):
        if v < 0:
          continue
        y, x = r + i, c + j
        if not (0 <= y < height and 0 <= x < width):
          raise ValueError('piece placed out of bounds')
        if tag[y][x] >= 0:
          raise ValueError('pieces overlap')
        for dy in (-1, 0, 1):
          for dx in (-1, 0, 1):
            yy, xx = y + dy, x + dx
            if (0 <= yy < height and 0 <= xx < width and
                tag[yy][xx] >= 0 and tag[yy][xx] != idx):
              raise ValueError('pieces must not touch, even diagonally')
        tag[y][x] = idx
        grid[y][x] = v
  return grid


def _partition(n):
  """Returns an owner map (0=TL, 1=TR, 2=BL, 3=BR) of an interlocking cut."""
  lo = max(1, n // 3)
  sr = random.randint(lo, n - lo)
  sc = random.randint(lo, n - lo)
  owner = [[(y >= sr) * 2 + (x >= sc) for x in range(n)] for y in range(n)]
  corners = {(0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)}
  members = [set() for _ in range(4)]
  for y in range(n):
    for x in range(n):
      members[owner[y][x]].add((y, x))
  tabs = random.randint(2, 3 + n // 3)
  made = 0
  for _ in range(tabs * 12):
    if made >= tabs:
      break
    starts = [(y, x, dy, dx) for y in range(n) for x in range(n)
              for dy, dx in DIRS4
              if 0 <= y + dy < n and 0 <= x + dx < n and
              owner[y + dy][x + dx] != owner[y][x]]
    y, x, dy, dx = random.choice(starts)
    a = owner[y][x]
    length = random.randint(1, max(1, n // 4))
    moved = 0
    cy, cx = y + dy, x + dx
    while moved < length and 0 <= cy < n and 0 <= cx < n:
      b = owner[cy][cx]
      if b == a or (cy, cx) in corners:
        break
      rest = members[b] - {(cy, cx)}
      if len(rest) < 3 or not _connected(rest):
        break
      members[b] = rest
      members[a].add((cy, cx))
      owner[cy][cx] = a
      moved += 1
      cy += dy
      cx += dx
    if moved:
      made += 1
  if made < 1:
    return None
  if any(len(m) < 3 or not _connected(m) for m in members):
    return None
  return owner


def _rotations(arr):
  """Distinct rotations of a piece as lists of (y, x, colour) cells."""
  seen = set()
  out = []
  for k in range(4):
    r = _rotate(arr, k)
    key = tuple(tuple(row) for row in r)
    if key in seen:
      continue
    seen.add(key)
    out.append([(i, j, v) for i, row in enumerate(r)
                for j, v in enumerate(row) if v >= 0])
  return out


def _unique(square, budget=60000):
  """True if square is the only valid assembly of its own pieces."""
  n = len(square)
  rots = [_rotations(a) for a in _pieces(square).values()]
  board = [[-1] * n for _ in range(n)]
  owner = [[-1] * n for _ in range(n)]
  used = [False] * len(rots)
  found = set()
  state = {'nodes': 0, 'aborted': False}

  def solve():
    state['nodes'] += 1
    if state['nodes'] > budget:
      state['aborted'] = True
      return True
    empty = None
    for y in range(n):
      for x in range(n):
        if board[y][x] < 0:
          empty = (y, x)
          break
      if empty is not None:
        break
    if empty is None:
      corners = {owner[0][0], owner[0][n - 1], owner[n - 1][0],
                 owner[n - 1][n - 1]}
      if board[0][0] == MARK and len(corners) == min(4, len(rots)):
        found.add(tuple(tuple(r) for r in board))
      return len(found) > 1
    ey, ex = empty
    for i, options in enumerate(rots):
      if used[i]:
        continue
      for cells in options:
        fy, fx, _ = cells[0]
        dy, dx = ey - fy, ex - fx
        fits = True
        for y, x, _ in cells:
          yy, xx = y + dy, x + dx
          if not (0 <= yy < n and 0 <= xx < n) or board[yy][xx] >= 0:
            fits = False
            break
        if not fits:
          continue
        for y, x, v in cells:
          board[y + dy][x + dx] = v
          owner[y + dy][x + dx] = i
        used[i] = True
        stop = False
        if board[0][0] == MARK:
          stop = solve()
        used[i] = False
        for y, x, _ in cells:
          board[y + dy][x + dx] = -1
          owner[y + dy][x + dx] = -1
        if stop:
          return True
    return False

  solve()
  if state['aborted']:
    return False
  return found == {tuple(tuple(r) for r in square)}


def _place(square, height, width):
  """Rotates and places pieces at uniformly chosen non-touching spots."""
  pieces = _pieces(square)
  order = sorted(pieces, key=lambda c: (
      -sum(v >= 0 for row in pieces[c] for v in row), random.random()))
  blocked = [[False] * width for _ in range(height)]
  result = []
  for color in order:
    turns = [0, 1, 2, 3]
    random.shuffle(turns)
    chosen = None
    for k in turns:
      arr = _rotate(pieces[color], k)
      h, w = len(arr), len(arr[0])
      if h > height or w > width:
        continue
      cells = [(i, j) for i in range(h) for j in range(w) if arr[i][j] >= 0]
      spots = [(r, c) for r in range(height - h + 1)
               for c in range(width - w + 1)
               if not any(blocked[r + i][c + j] for i, j in cells)]
      if spots:
        r, c = random.choice(spots)
        chosen = (k, r, c, cells)
        break
    if chosen is None:
      return None
    k, r, c, cells = chosen
    for i, j in cells:
      for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
          y, x = r + i + dy, c + j + dx
          if 0 <= y < height and 0 <= x < width:
            blocked[y][x] = True
    result.append((color, k, r, c))
  return result


def _check_side(value, name):
  if value is not None and (not _is_int(value) or not 1 <= value <= 30):
    raise ValueError(name + ' must be an integer in 1..30')


def _sample_side(n):
  """Samples one input side for an NxN answer."""
  lo = min(30, max(10, (3 * n) // 2 + 1))
  if random.random() < 0.4 and SIZE * SIZE > 2 * n * n:
    return SIZE
  return random.randint(lo, 30)


def generate(size=None, colors=None, square=None, placements=None,
             width=None, height=None):
  """Returns an input/output pair.

  Args:
    size: optional side N of the output square. It is sampled from 4..14 and
      may be given explicitly as 4..16.
    colors: optional three distinct colours from {1,2,3,4,6,8,9}. They are used
      for the top-right, bottom-left and bottom-right pieces.
    square: optional explicit NxN output square, used to rebuild fixtures. It
      cannot be combined with size or colors. It must be a valid,
      uniquely reassemblable square (checked). If placements is omitted, the
      pieces of square are placed randomly.
    placements: optional list of (piece_colour, quarter_turns, row, col). The
      piece of square with that colour (7 includes the 5) is rotated
      quarter_turns times counter-clockwise. Its bounding box is drawn with
      its top-left corner at (row, col). Pieces must not overlap or touch,
      even diagonally. Requires square.
    width: optional input width (1..30). It defaults to 20 when square is
      given; otherwise it is sampled.
    height: optional input height (1..30). It follows the same rule as width.
  """
  _check_side(width, 'width')
  _check_side(height, 'height')
  if square is not None:
    if size is not None or colors is not None:
      raise ValueError('size and colors are implied by an explicit square')
    sq = _check_square(square)
    n = len(sq)
    hh = height if height is not None else SIZE
    ww = width if width is not None else SIZE
    if hh * ww <= 2 * n * n:
      raise ValueError('input too small: black must be a strict majority')
    if not _unique(sq):
      raise ValueError('square pieces admit another valid assembly')
    if placements is None:
      for _ in range(50):
        placements = _place(sq, hh, ww)
        if placements is not None:
          break
      if placements is None:
        raise RuntimeError('could not place the pieces of the given square')
    return {'input': _render(sq, placements, hh, ww),
            'output': [list(r) for r in sq]}
  if placements is not None:
    raise ValueError('placements require an explicit square')
  if size is not None and (not _is_int(size) or not 4 <= size <= 16):
    raise ValueError('size must be an integer in 4..16')
  if colors is not None:
    if not isinstance(colors, (list, tuple)):
      raise ValueError('colors must be an ordered list or tuple')
    colors = list(colors)
    if (len(colors) != 3 or any(not _is_int(c) for c in colors) or
        len(set(colors)) != 3 or not set(colors) <= set(OTHER_COLORS)):
      raise ValueError('colors must be 3 distinct values from ' +
                       str(OTHER_COLORS))
  hmax = height if height is not None else 30
  wmax = width if width is not None else 30
  feasible_sizes = [n for n in ([size] if size is not None else range(4, 15))
                    if hmax * wmax > 2 * n * n]
  if not feasible_sizes:
    raise ValueError('input too small for any requested square size')
  for _ in range(400):
    n = random.choice(feasible_sizes)
    hh = height if height is not None else _sample_side(n)
    ww = width if width is not None else _sample_side(n)
    if hh * ww <= 2 * n * n:
      continue
    cols = list(colors) if colors is not None else random.sample(
        OTHER_COLORS, 3)
    owner = _partition(n)
    if owner is None:
      continue
    palette = [MARK_COLOR] + cols
    sq = [[palette[owner[y][x]] for x in range(n)] for y in range(n)]
    sq[0][0] = MARK
    if not _unique(sq):
      continue
    for _ in range(10):
      pl = _place(sq, hh, ww)
      if pl is not None:
        return {'input': _render(sq, pl, hh, ww),
                'output': [list(r) for r in sq]}
  raise RuntimeError('could not construct a scene')


def validate():
  """Rebuilds the canonical examples from explicit latent parameters."""
  sq1 = [[5, 7, 7, 9, 9, 9], [7, 7, 9, 9, 9, 9], [7, 4, 7, 9, 3, 9],
         [4, 4, 4, 3, 3, 3], [4, 4, 4, 4, 4, 3], [4, 4, 4, 3, 3, 3]]
  sq2 = [[5, 7, 7, 7, 7, 2, 2, 2, 2, 2], [7, 7, 7, 7, 7, 2, 2, 2, 2, 2],
         [7, 7, 7, 7, 7, 7, 2, 2, 2, 2], [7, 7, 7, 7, 7, 2, 2, 6, 2, 2],
         [7, 7, 3, 7, 7, 2, 2, 6, 2, 2], [3, 3, 3, 3, 3, 6, 6, 6, 6, 6],
         [3, 3, 3, 3, 3, 6, 6, 6, 6, 6], [3, 3, 3, 3, 3, 3, 3, 6, 6, 6],
         [3, 3, 3, 3, 3, 6, 6, 6, 6, 6], [3, 3, 3, 3, 3, 6, 6, 6, 6, 6]]
  sq3 = [[5, 7, 7, 8], [7, 8, 8, 8], [6, 6, 8, 2], [6, 6, 2, 2]]
  top = [7] * 7 + [8] * 7
  sq4 = [[5] + [7] * 6 + [8] * 7, list(top), list(top),
         [7] * 5 + [8] * 9, list(top), list(top), list(top),
         [3, 3, 3, 7, 3, 3, 3, 2, 2, 2, 8, 2, 2, 2],
         [3, 3, 3, 7, 3, 3, 3] + [2] * 7,
         [3, 3, 3, 7, 3, 3, 3] + [2] * 7,
         [3] * 10 + [2] * 4,
         [3] * 7 + [2] * 7, [3] * 7 + [2] * 7, [3] * 7 + [2] * 7]
  train = [
      generate(square=sq1, placements=[(7, 3, 3, 13), (9, 2, 3, 3),
                                       (4, 1, 11, 3), (3, 0, 16, 17)]),
      generate(square=sq2, placements=[(7, 1, 2, 3), (2, 0, 6, 15),
                                       (3, 0, 10, 0), (6, 0, 13, 8)]),
      generate(square=sq3, placements=[(7, 0, 15, 3), (8, 0, 12, 13),
                                       (6, 0, 2, 16), (2, 2, 0, 0)]),
  ]
  test = [
      generate(square=sq4, placements=[(7, 2, 8, 0), (8, 1, 11, 9),
                                       (3, 2, 1, 9), (2, 0, 0, 1)]),
  ]
  return {'train': train, 'test': test}
