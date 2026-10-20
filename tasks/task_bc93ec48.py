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

"""ARC-GEN style generator for task bc93ec48.

Rule: each grid corner cell is either background (7) or part of a one-colour
4-connected object. Every corner object is copied one corner clockwise
(TL->TR->BR->BL->TL). The copy is a plain translation, with no rotation or
flip, that puts the object's bounding box flush in the new corner. Only the
copied object's own cells are painted, so any earlier contents that the copy
does not cover survive. Every copy reads from the input. An empty
(background) corner sends nothing.

Scope: random scenes use background 7 by default, which is fixed in the task.
Grid sides are usually sampled from 7..16, the fixture range. Sometimes they
are sampled from 17..30 as a synthetic extension. Explicit random sizes from
5 to 30 are accepted, including non-square grids.

Each corner holds a random rectangle, holds a random 4-connected blob, or is
empty. By default at least two corners are occupied; num_corners can request
exactly 1..4 occupied corners. Corner and distractor sizes scale with the
grid. One-colour distractor objects are scattered over the grid. Some
distractors deliberately sit next to an empty corner without covering it, as
the 2 square does in the second demonstration. In about half of the scenes,
distractors may touch a corner object of a different colour, as the 8 next to
the 6 does in the first demonstration. In about half of the scenes,
distractors may also touch each other (different colours, or same colour only
diagonally), as several distractors do in the fixtures.

Random-scene invariants:
- A distractor never touches a same-colour corner object, not even
  diagonally, so 4- and 8-connected readings of every corner object agree.
- Same-colour distractors never touch orthogonally.
- Distractors never cover a corner cell.
- Corner objects are smaller than half the grid in each dimension, so the
  four stamps never overlap and corner objects never touch.
- The background is strictly the most frequent input colour.
- Input and output differ.

Every scene, explicit or random, is checked against its latent description
before it is returned:
- Each declared corner object must be exactly the one-colour 4-connected
  input component at its corner.
- Each corner declared empty must be background.
- No corner component may occupy several grid corners.
- No two stamps may overlap.
- The background must be strictly the most frequent colour.
- At least one corner is occupied and the output differs from the input.
"""

import random

import common

_CORNER_NAMES = ['top-left', 'top-right', 'bottom-right', 'bottom-left']


def _is_int(x):
  return isinstance(x, int) and not isinstance(x, bool)


def _cells(pattern):
  return [(r, c) for r, row in enumerate(pattern)
          for c, ch in enumerate(row) if ch == '#']


def _connected(cells):
  """True when the cell set is non-empty and 4-connected."""
  cells = set(cells)
  if not cells:
    return False
  start = min(cells)
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for n in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _grow(maxh, maxw, n):
  """Random 4-connected cell set inside a maxh x maxw box containing (0,0)."""
  cells = {(0, 0)}
  n = min(n, maxh * maxw)
  for _ in range(60 * n + 60):
    if len(cells) >= n:
      break
    r, c = random.choice(sorted(cells))
    dr, dc = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
    nr, nc = r + dr, c + dc
    if 0 <= nr < maxh and 0 <= nc < maxw:
      cells.add((nr, nc))
  return cells


def _to_pattern(cells):
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  h = max(r for r, _ in cells) - r0 + 1
  w = max(c for _, c in cells) - c0 + 1
  rows = [['.'] * w for _ in range(h)]
  for r, c in cells:
    rows[r - r0][c - c0] = '#'
  return [''.join(row) for row in rows]


def _corner_origin(index, h, w, height, width):
  top = index in (0, 1)
  left = index in (0, 3)
  return (0 if top else height - h), (0 if left else width - w)


def _corner_cells(height, width):
  return [(0, 0), (0, width - 1), (height - 1, width - 1), (height - 1, 0)]


def _neighbours(r, c):
  for dr in (-1, 0, 1):
    for dc in (-1, 0, 1):
      if dr or dc:
        yield r + dr, c + dc


def _component(grid, r, c):
  """One-colour 4-connected component of grid containing (r, c)."""
  colour = grid[r][c]
  height, width = len(grid), len(grid[0])
  seen = {(r, c)}
  stack = [(r, c)]
  while stack:
    y, x = stack.pop()
    for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
      if (0 <= ny < height and 0 <= nx < width and (ny, nx) not in seen
          and grid[ny][nx] == colour):
        seen.add((ny, nx))
        stack.append((ny, nx))
  return seen


def _check_colour(colour, background):
  if not _is_int(colour) or not 0 <= colour <= 9:
    raise ValueError('colours must be integers 0..9')
  if colour == background:
    raise ValueError('object colour must differ from the background')


def _check_pattern(pattern, corner_index=None):
  """Checks a '#'/'.' pattern: it fills its bounding box and is connected."""
  if not isinstance(pattern, (list, tuple)) or not pattern:
    raise ValueError('pattern must be a non-empty list of strings')
  w = len(pattern[0]) if isinstance(pattern[0], str) else 0
  if w == 0:
    raise ValueError('pattern rows must be non-empty strings')
  for row in pattern:
    if not isinstance(row, str) or len(row) != w or set(row) - set('#.'):
      raise ValueError('pattern rows must be equal-length #/. strings')
  if ('#' not in pattern[0] or '#' not in pattern[-1]
      or not any(row[0] == '#' for row in pattern)
      or not any(row[-1] == '#' for row in pattern)):
    raise ValueError('pattern must fill its bounding box')
  if not _connected(_cells(pattern)):
    raise ValueError('pattern must be 4-connected')
  if corner_index is not None:
    r = 0 if corner_index in (0, 1) else len(pattern) - 1
    c = 0 if corner_index in (0, 3) else w - 1
    if pattern[r][c] != '#':
      raise ValueError('corner pattern must cover the '
                       + _CORNER_NAMES[corner_index] + ' grid cell')


def _placeable(cells, colour, owner, corner_cells, allow_contact, loose):
  """Placement test for one distractor.

  Corner objects may only be touched by distractors of another colour, and
  only when allow_contact is set. Other distractors may be touched only when
  loose is set, and then a same-colour distractor may touch only diagonally.
  """
  cellset = set(cells)
  for cell in cells:
    if cell in owner or cell in corner_cells:
      return False
    r, c = cell
    for n in _neighbours(r, c):
      if n in cellset or n not in owner:
        continue
      ncolour, tag = owner[n]
      orth = abs(n[0] - r) + abs(n[1] - c) == 1
      if tag == 'corner':
        if ncolour == colour or not allow_contact:
          return False
      else:
        if not loose:
          return False
        if ncolour == colour and orth:
          return False
  return True


def _background_dominant(grid, background):
  counts = [0] * 10
  for row in grid:
    for v in row:
      counts[v] += 1
  return all(counts[background] > counts[c] for c in range(10)
             if c != background)


def _render(width, height, background, corners, others):
  """Paints the input and stamps every corner object one corner clockwise.

  Returns (pair, problem). The problem is None when the latent scene agrees
  with the rule-level reading of the painted input. Otherwise it is a string
  that describes the inconsistency.
  """
  for side in (width, height):
    if not _is_int(side) or not 2 <= side <= 30:
      raise ValueError('grid sides must be integers in 2..30')
  if not isinstance(corners, (list, tuple)) or len(corners) != 4:
    raise ValueError('corners must list TL, TR, BR, BL entries')
  if not isinstance(others, (list, tuple)):
    raise ValueError('others must be a list')
  grid = common.grid(width, height, background)
  latent = []
  for i, entry in enumerate(corners):
    if entry is None:
      latent.append(None)
      continue
    if not isinstance(entry, (list, tuple)) or len(entry) != 2:
      raise ValueError('corner entries must be None or (colour, pattern)')
    colour, pattern = entry
    _check_colour(colour, background)
    _check_pattern(pattern, i)
    h, w = len(pattern), len(pattern[0])
    if h > height or w > width:
      raise ValueError('corner pattern does not fit in the grid')
    r0, c0 = _corner_origin(i, h, w, height, width)
    cells = {(r0 + r, c0 + c) for r, c in _cells(pattern)}
    for r, c in cells:
      grid[r][c] = colour
    latent.append((colour, pattern, cells))
  for entry in others:
    if not isinstance(entry, (list, tuple)) or len(entry) != 4:
      raise ValueError('distractors must be (colour, row, col, pattern)')
    colour, r0, c0, pattern = entry
    _check_colour(colour, background)
    if not _is_int(r0) or not _is_int(c0):
      raise ValueError('distractor row/col must be integers')
    _check_pattern(pattern)
    h, w = len(pattern), len(pattern[0])
    if r0 < 0 or c0 < 0 or r0 + h > height or c0 + w > width:
      raise ValueError('distractor out of bounds')
    for r, c in _cells(pattern):
      grid[r0 + r][c0 + c] = colour
  problem = None
  if all(entry is None for entry in latent):
    problem = 'no corner is occupied'
  corner_cells = _corner_cells(height, width)
  for entry in latent:
    if entry is not None and len(entry[2].intersection(corner_cells)) != 1:
      problem = 'one corner object cannot occupy several grid corners'
      break
  for i, entry in enumerate(latent):
    if problem is not None:
      break
    cr, cc = corner_cells[i]
    if entry is None:
      if grid[cr][cc] != background:
        problem = _CORNER_NAMES[i] + ' corner declared empty is not background'
    elif (grid[cr][cc] != entry[0]
          or _component(grid, cr, cc) != entry[2]):
      problem = (_CORNER_NAMES[i] + ' corner object differs from the input '
                 'component at that corner')
  if problem is None and not _background_dominant(grid, background):
    problem = 'background is not strictly the most frequent colour'
  output = [row[:] for row in grid]
  stamped = set()
  for i, entry in enumerate(latent):
    if entry is None:
      continue
    colour, pattern, _ = entry
    h, w = len(pattern), len(pattern[0])
    r0, c0 = _corner_origin((i + 1) % 4, h, w, height, width)
    for r, c in _cells(pattern):
      cell = (r0 + r, c0 + c)
      if cell in stamped and problem is None:
        problem = 'two clockwise stamps overlap'
      stamped.add(cell)
      output[cell[0]][cell[1]] = colour
  if problem is None and output == grid:
    problem = 'output equals input'
  return {'input': grid, 'output': output}, problem


def _caps(height, width):
  """Corner caps stay below half the grid; distractor caps grow slowly."""
  caph = min(max(4, height // 4) + (height >= 14), (height - 1) // 2)
  capw = min(max(4, width // 4) + (width >= 14), (width - 1) // 2)
  dcap = max(3, min(height, width) // 6)
  return caph, capw, dcap


def _distractor_pattern(dcap):
  if random.random() < 0.3:
    length = random.randint(2, dcap + 1)
    local = ({(0, k) for k in range(length)} if random.random() < 0.5
             else {(k, 0) for k in range(length)})
  else:
    local = _grow(dcap, dcap, random.randint(1, min(dcap * dcap, 2 * dcap - 1)))
  return _to_pattern(local)


def _sample(height, width, background, num_corners):
  """Samples latent corner objects and distractors."""
  colours = [c for c in range(10) if c != background]
  if num_corners is None:
    present = [random.random() < 0.8 for _ in range(4)]
    if sum(present) < 2:
      for i in random.sample(range(4), 2):
        present[i] = True
  else:
    chosen = set(random.sample(range(4), num_corners))
    present = [i in chosen for i in range(4)]
  caph, capw, dcap = _caps(height, width)
  corner_cells = _corner_cells(height, width)
  corner_set = set(corner_cells)
  owner = {}
  corners = []
  boxes = []
  for i in range(4):
    if not present[i]:
      corners.append(None)
      continue
    if random.random() < 0.45:
      h, w = random.randint(1, caph), random.randint(1, capw)
      local = {(r, c) for r in range(h) for c in range(w)}
    else:
      local = _grow(caph, capw, random.randint(2, max(2, caph * capw)))
    pattern = _to_pattern(local)
    if i in (1, 2):
      pattern = [row[::-1] for row in pattern]
    if i in (2, 3):
      pattern = pattern[::-1]
    h, w = len(pattern), len(pattern[0])
    r0, c0 = _corner_origin(i, h, w, height, width)
    colour = random.choice(colours)
    for r, c in _cells(pattern):
      owner[(r0 + r, c0 + c)] = (colour, 'corner')
    corners.append((colour, pattern))
    boxes.append((r0, c0, h, w))
  allow_contact = random.random() < 0.5
  loose = random.random() < 0.5
  others = []

  def place(pattern, colour, r0, c0):
    h, w = len(pattern), len(pattern[0])
    if r0 < 0 or c0 < 0 or r0 + h > height or c0 + w > width:
      return False
    cells = [(r0 + r, c0 + c) for r, c in _cells(pattern)]
    if not _placeable(cells, colour, owner, corner_set, allow_contact, loose):
      return False
    for cell in cells:
      owner[cell] = (colour, 'other')
    others.append((colour, r0, c0, pattern))
    return True

  # Near-miss distractors next to empty corners (they must not be copied).
  for i in range(4):
    if present[i] or random.random() >= 0.65:
      continue
    cr, cc = corner_cells[i]
    for _ in range(30):
      pattern = _distractor_pattern(dcap)
      h, w = len(pattern), len(pattern[0])
      if h > height or w > width:
        continue
      dr, dc = random.randint(0, 1), random.randint(0, 1)
      r0 = dr if i in (0, 1) else height - h - dr
      c0 = dc if i in (0, 3) else width - w - dc
      near = any(max(abs(r0 + r - cr), abs(c0 + c - cc)) == 1
                 for r, c in _cells(pattern))
      if near and place(pattern, random.choice(colours), r0, c0):
        break

  target = random.randint(2, max(3, height * width // 14))
  for _ in range(target):
    for _ in range(30):
      pattern = _distractor_pattern(dcap)
      h, w = len(pattern), len(pattern[0])
      if h > height or w > width:
        continue
      colour = random.choice(colours)
      if allow_contact and boxes and random.random() < 0.4:
        br0, bc0, bh, bw = random.choice(boxes)
        r0 = random.randint(max(0, br0 - h), min(height - h, br0 + bh))
        c0 = random.randint(max(0, bc0 - w), min(width - w, bc0 + bw))
      elif loose and others and random.random() < 0.3:
        _, or0, oc0, opat = random.choice(others)
        oh, ow = len(opat), len(opat[0])
        r0 = random.randint(max(0, or0 - h), min(height - h, or0 + oh))
        c0 = random.randint(max(0, oc0 - w), min(width - w, oc0 + ow))
      else:
        r0 = random.randint(0, height - h)
        c0 = random.randint(0, width - w)
      if place(pattern, colour, r0, c0):
        break
  return corners, others


def _random_side():
  if random.random() < 0.85:
    return random.randint(7, 16)
  return random.randint(17, 30)


def generate(width=None, height=None, background=None, corners=None,
             others=None, num_corners=None):
  """Builds one input/output pair.

  Args:
    width: grid width (columns). If None, it is sampled, usually from 7..16
      and occasionally from 17..30. Random scenes accept 5..30. Explicit
      scenes accept 2..30.
    height: grid height (rows). It is sampled the same way as width.
    background: background colour. Defaults to 7, which is fixed in the task.
    corners: list of four entries in clockwise order TL, TR, BR, BL. Each
      entry is None (an empty corner) or (colour, pattern). The pattern is a
      list of '#'/'.' strings. It must be 4-connected, exactly fill its
      bounding box, and cover the grid corner cell. It is drawn as the object
      sits in that corner. When corners is given, width and height are
      required. The scene is rejected with ValueError if any of these hold:
      - no corner is occupied;
      - the painted input's corner component differs from the declared object;
      - an empty corner is not background;
      - one component occupies several grid corners;
      - stamps overlap;
      - the background is not strictly the most frequent colour;
      - the output equals the input.
    others: list of (colour, row, col, pattern) distractor objects. They are
      painted after the corner objects. This argument is only allowed
      together with explicit corners.
    num_corners: random mode only. Exact number (1..4) of occupied corners.
      If None, each corner is occupied with probability 0.8 and at least two
      are forced.
  """
  if background is None:
    background = 7
  if not _is_int(background) or not 0 <= background <= 9:
    raise ValueError('background must be an integer 0..9')
  if num_corners is not None:
    if corners is not None:
      raise ValueError('num_corners is only for random scenes')
    if not _is_int(num_corners) or not 1 <= num_corners <= 4:
      raise ValueError('num_corners must be an integer 1..4')
  if corners is not None:
    if width is None or height is None:
      raise ValueError('explicit corners require width and height')
    pair, problem = _render(width, height, background, corners,
                            others if others is not None else [])
    if problem is not None:
      raise ValueError('inconsistent explicit scene: ' + problem)
    return pair
  if others is not None:
    raise ValueError('others is only supported together with explicit corners')
  for side in (width, height):
    if side is not None and (not _is_int(side) or not 5 <= side <= 30):
      raise ValueError('random scenes need integer sides in 5..30')
  for _ in range(300):
    h = height if height is not None else _random_side()
    if width is not None:
      w = width
    elif random.random() < 0.6:
      w = h
    else:
      w = _random_side()
    sampled_corners, sampled_others = _sample(h, w, background, num_corners)
    pair, problem = _render(w, h, background, sampled_corners, sampled_others)
    if problem is not None:
      continue
    return pair
  raise RuntimeError('failed to sample a valid scene')


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(10, 10, 7,
               [(4, ['##', '##']), (6, ['##', '.#', '.#', '.#']),
                (9, ['#.', '##']), (2, ['#', '#'])],
               [(9, 0, 6, ['#.', '##', '##']), (8, 2, 8, ['#']),
                (5, 3, 4, ['#.', '##']), (5, 5, 1, ['#.', '##']),
                (8, 7, 2, ['.#', '##'])]),
      generate(8, 8, 7,
               [(5, ['#', '#', '#']), (9, ['##', '##']),
                (5, ['#', '#', '#']), None],
               [(3, 0, 2, ['#', '#']), (5, 3, 3, ['###']),
                (3, 4, 4, ['#', '#', '#']), (2, 6, 1, ['##', '##'])]),
      generate(8, 8, 7,
               [(6, ['#', '#']), (2, ['###']), (4, ['#', '#']),
                (5, ['##', '##'])],
               [(3, 0, 2, ['##', '##']), (6, 1, 7, ['#', '#']),
                (5, 2, 3, ['#']), (5, 3, 4, ['#']),
                (2, 3, 1, ['#..', '###']), (6, 5, 3, ['##'])]),
  ]
  test = [
      generate(16, 16, 7,
               [(8, ['##', '##', '##']), (5, ['##', '##']),
                (8, ['#', '#', '#']), (1, ['####', '####', '####'])],
               [(6, 0, 9, ['#', '#', '#', '#', '#']), (5, 2, 5, ['###']),
                (9, 3, 6, ['#', '#', '#']), (8, 2, 15, ['#']),
                (9, 2, 11, ['##', '#.']), (8, 3, 13, ['##', '##']),
                (9, 5, 1, ['###', '.#.']), (8, 7, 7, ['####', '.#..']),
                (3, 8, 12, ['####']), (2, 9, 2, ['##', '##']),
                (9, 10, 5, ['##', '##']), (6, 11, 0, ['#', '#']),
                (8, 12, 11, ['##', '##']), (6, 15, 4, ['##'])]),
  ]
  return {'train': train, 'test': test}
