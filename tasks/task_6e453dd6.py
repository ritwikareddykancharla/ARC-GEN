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

"""ARC task 6e453dd6: slide shapes to a divider and flag holed rows.

The background is colour 6. A full-height column of colour 5 divides the
grid. Several colour-0 shapes lie to the left of the divider. Each shape is
8-connected, and neighbouring shapes are separated by at least one blank row.
The right side of the divider is empty.

Output:
- Every shape slides rigidly right until its rightmost column sits directly
  left of the divider.
- Each row of each shifted shape is then checked. A row is marked when both of
  these hold:
  - the shape has a cell touching the divider in that row;
  - the row's cells are not contiguous, so there is a background gap between
    them.
- Each marked row is painted with colour 2 from just right of the divider to
  the right edge.

Scope:
- Shapes are always on the left of the divider, as in every demonstration.
- Colours 6/5/0/2 are fixed.
- Sampled: grid height (8..30), divider column (4..16), right-side width,
  shape count and shape forms. Widths and heights beyond the fixtures are
  synthetic extensions that the rule permits.
- Shape forms are rings with optional internal bars, open C-rings, ladders,
  solid blocks and random polyomino blobs. Each form may carry a short tail.
- One shape is always a ring that is not flush with the divider. This
  guarantees at least one slide and at least one marked row.
- Other shapes act as distractors: solid rows, gapped rows that do not touch
  the divider, and shapes that are already flush.
"""

import random

import common

BG, DIV, INK, MARK = 6, 5, 0, 2


def _parse(pattern):
  if (not pattern or not all(isinstance(row, str) for row in pattern)
      or not pattern[0] or any(len(row) != len(pattern[0]) for row in pattern)
      or any(ch not in '.X' for row in pattern for ch in row)):
    raise ValueError('pattern must be a nonempty rectangle of X and .')
  cells = {(r, c) for r, row in enumerate(pattern)
           for c, ch in enumerate(row) if ch == 'X'}
  if not cells or not _connected(cells):
    raise ValueError('each shape must be nonempty and 8-connected')
  return cells


def _normalize(cells):
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  return {(r - r0, c - c0) for r, c in cells}


def _dims(cells):
  return (max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1)


def _connected(cells):
  cells = set(cells)
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        n = (r + dr, c + dc)
        if n in cells and n not in seen:
          seen.add(n)
          stack.append(n)
  return len(seen) == len(cells)


def _ring(h, w):
  return {(r, c) for r in range(h) for c in range(w)
          if r in (0, h - 1) or c in (0, w - 1)}


def _solid(maxh, maxw):
  h = random.randint(2, min(3, maxh))
  w = random.randint(2, min(3, maxw))
  return {(r, c) for r in range(h) for c in range(w)}


def _marked_rows(cells):
  """Relative rows touching the right edge of the shape and containing a gap."""
  _, w = _dims(cells)
  rows = {}
  for r, c in cells:
    rows.setdefault(r, []).append(c)
  out = []
  for r, xs in rows.items():
    if (w - 1) in xs and len(set(xs)) < max(xs) - min(xs) + 1:
      out.append(r)
  return sorted(out)


def _make_shape(maxh, maxw):
  """Builds a random 8-connected shape fitting inside maxh x maxw (>= 2x2)."""
  kinds = ['ring'] * 3 + ['open'] * 2 + ['ladder'] * 2 + ['solid', 'blob', 'blob']
  for _ in range(60):
    kind = random.choice(kinds)
    if kind in ('ring', 'open', 'ladder') and (maxh < 3 or maxw < 3):
      kind = 'solid'
    if kind == 'ring' or kind == 'open':
      h = random.randint(3, min(6, maxh))
      w = random.randint(3, min(6, maxw))
      cells = _ring(h, w)
      if kind == 'ring':
        for c in range(2, w - 2):
          if random.random() < 0.35:
            cells |= {(r, c) for r in range(1, h - 1)}
        for r in range(2, h - 2):
          if random.random() < 0.25:
            cells |= {(r, c) for c in range(1, w - 1)}
      else:
        side = random.choice(['right', 'right', 'left', 'top', 'bottom'])
        if side in ('right', 'left'):
          a = random.randint(1, h - 2)
          b = random.randint(a, h - 2)
          col = w - 1 if side == 'right' else 0
          cells -= {(r, col) for r in range(a, b + 1)}
        else:
          a = random.randint(1, w - 2)
          b = random.randint(a, w - 2)
          row = 0 if side == 'top' else h - 1
          cells -= {(row, c) for c in range(a, b + 1)}
    elif kind == 'ladder':
      h = random.randint(3, min(7, maxh))
      w = random.randint(3, min(4, maxw))
      cells = {(0, c) for c in range(w)} | {(h - 1, c) for c in range(w)}
      for r in range(1, h - 1):
        if random.random() < 0.3:
          cells |= {(r, c) for c in range(w)}
        else:
          opt = random.choice(['both', 'both', 'left', 'right'])
          if opt in ('both', 'left'):
            cells.add((r, 0))
          if opt in ('both', 'right'):
            cells.add((r, w - 1))
    elif kind == 'solid':
      cells = _solid(maxh, maxw)
    else:
      h = random.randint(2, min(5, maxh))
      w = random.randint(2, min(5, maxw))
      k = random.randint(3, h * w - 1)
      cells = {(random.randrange(h), random.randrange(w))}
      for _ in range(200):
        if len(cells) >= k:
          break
        r, c = random.choice(sorted(cells))
        dr, dc = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        if 0 <= r + dr < h and 0 <= c + dc < w:
          cells.add((r + dr, c + dc))
    cells = _normalize(cells)
    if random.random() < 0.35:
      sh, sw = _dims(cells)
      direction = random.choice(['up', 'down', 'left', 'right'])
      length = random.randint(1, 2)
      if direction == 'down':
        r, c = random.choice(sorted(p for p in cells if p[0] == sh - 1))
        cells |= {(r + i, c) for i in range(1, length + 1)}
      elif direction == 'up':
        r, c = random.choice(sorted(p for p in cells if p[0] == 0))
        cells |= {(r - i, c) for i in range(1, length + 1)}
      elif direction == 'left':
        r, c = random.choice(sorted(p for p in cells if p[1] == 0))
        cells |= {(r, c - i) for i in range(1, length + 1)}
      else:
        r, c = random.choice(sorted(p for p in cells if p[1] == sw - 1))
        cells |= {(r, c + i) for i in range(1, length + 1)}
      cells = _normalize(cells)
    h, w = _dims(cells)
    if h < 2 or w < 2 or h > maxh or w > maxw:
      continue
    if not _connected(cells):
      continue
    return cells
  return _solid(maxh, maxw)


def _guaranteed_ring(maxh, dcol, simple):
  """A ring narrower than dcol whose middle rows touch its right edge with gaps."""
  if simple:
    return _ring(3, 3)
  h = random.randint(3, min(6, maxh))
  w = random.randint(3, min(6, dcol - 1))
  cells = _ring(h, w)
  if w >= 5 and random.random() < 0.4:
    c = random.randint(2, w - 3)
    cells |= {(r, c) for r in range(1, h - 1)}
  return cells


def _sample_forms(height, dcol, k, simple):
  """Samples k forms whose heights plus separators fit inside height."""
  forms = []
  used = 0
  for i in range(k):
    sep = 1 if i else 0
    maxh = height - used - sep - (k - 1 - i) * 3
    maxh = min(maxh, height - 1)
    if i == 0:
      cells = _guaranteed_ring(maxh, dcol, simple)
      forms.append((cells, True))
    else:
      if simple:
        cells = {(0, 0), (0, 1), (1, 0), (1, 1)}
      else:
        cells = _make_shape(maxh, min(dcol, 7))
      forms.append((cells, False))
    used += _dims(cells)[0] + sep
  random.shuffle(forms)
  return forms


def _layout(forms, height, dcol):
  k = len(forms)
  extra = height - (sum(_dims(c)[0] for c, _ in forms) + k - 1)
  slots = [0] * (k + 1)
  for _ in range(extra):
    slots[random.randint(0, k)] += 1
  shapes = []
  top = slots[0]
  for i, (cells, must_move) in enumerate(forms):
    h, w = _dims(cells)
    if must_move:
      left = random.randint(0, dcol - w - 1)
    elif random.random() < 0.25:
      left = dcol - w
    else:
      left = random.randint(0, dcol - w)
    shapes.append((top, left, cells))
    top += h + 1 + slots[i + 1]
  return shapes


def _palette_ok(width, height, shapes):
  ink = sum(len(cells) for _, _, cells in shapes)
  bg = width * height - height - ink
  return bg > ink and bg > height


def _resolve_dims(width, height, divider):
  if height is None:
    height = random.randint(8, 30)
  elif not 5 <= height <= 30:
    raise ValueError('height must be in 5..30')
  if width is None and divider is None:
    divider = random.randint(4, 16)
    width = divider + 1 + random.randint(2, min(8, 29 - divider))
  elif divider is None:
    if not 6 <= width <= 30:
      raise ValueError('width must be in 6..30')
    divider = random.randint(4, max(4, min(16, width - 3)))
  elif width is None:
    if not 4 <= divider <= 28:
      raise ValueError('divider must be in 4..28')
    width = divider + 1 + random.randint(min(2, 29 - divider),
                                         min(8, 29 - divider))
  else:
    if divider < 4 or width > 30 or width < divider + 2:
      raise ValueError('need 4 <= divider and divider + 2 <= width <= 30')
  return width, height, divider


def _sample_scene(width, height, divider, num_shapes):
  width, height, dcol = _resolve_dims(width, height, divider)
  kmax = height // 3
  if num_shapes is None:
    num_shapes = random.randint(min(2, kmax), min(6, kmax))
  elif not 1 <= num_shapes <= kmax:
    raise ValueError('num_shapes must be in 1..height // 3')
  for _ in range(40):
    forms = _sample_forms(height, dcol, num_shapes, simple=False)
    shapes = _layout(forms, height, dcol)
    if _palette_ok(width, height, shapes):
      return width, height, dcol, shapes
  # Low-density construction (3x3 ring plus 2x2 blocks, random placement).
  # Background dominance is provable here for every allowed size.
  forms = _sample_forms(height, dcol, num_shapes, simple=True)
  return width, height, dcol, _layout(forms, height, dcol)


def _check_explicit(width, height, divider, scene):
  if not (1 <= height <= 30 and 1 <= width <= 30 and 0 < divider < width - 1):
    raise ValueError('invalid explicit dimensions')
  if not scene or not _palette_ok(width, height, scene):
    raise ValueError('require shapes and a dominant colour-6 background')
  prev_bottom = -2
  for top, left, cells in sorted(scene, key=lambda s: s[0]):
    if type(top) is not int or type(left) is not int:
      raise ValueError('shape offsets must be integers')
    h, w = _dims(cells)
    if top < 0 or left < 0 or top + h > height or left + w > divider:
      raise ValueError('shape out of bounds or crosses the divider')
    if top <= prev_bottom + 1:
      raise ValueError('shapes must be separated by a blank row')
    if top == 0 and h == height and any(
        all((r, c) in cells for r in range(height)) for c in range(w)):
      raise ValueError('a full-height ink column creates an extra divider')
    prev_bottom = top + h - 1


def _render(width, height, dcol, shapes):
  inp = common.grid(width, height, BG)
  out = common.grid(width, height, BG)
  for r in range(height):
    inp[r][dcol] = DIV
    out[r][dcol] = DIV
  for top, left, cells in shapes:
    _, w = _dims(cells)
    new_left = dcol - w
    for r, c in cells:
      inp[top + r][left + c] = INK
    for r, c in cells:
      out[top + r][new_left + c] = INK
    for r in _marked_rows(cells):
      for x in range(dcol + 1, width):
        out[top + r][x] = MARK
  return {'input': inp, 'output': out}


def generate(width=None, height=None, divider=None, shapes=None,
             num_shapes=None):
  """Returns an input/output pair.

  Args:
    width: grid width. In random mode it is honoured if given (6..30) and the
      divider must leave at least one column on its right. Required when shapes
      is given.
    height: grid height. In random mode it is honoured if given (5..30).
      Required when shapes is given.
    divider: column index of the colour-5 divider. In random mode it is
      honoured if given (>= 4). Required when shapes is given.
    shapes: optional list of (top, left, pattern) triples. Each pattern is a
      list of strings in which 'X' marks a colour-0 cell. Shapes must lie left
      of the divider and be separated by blank rows. If None, a fresh random
      scene is sampled.
    num_shapes: number of shapes in random mode (1..height // 3). If shapes is
      given, it must equal len(shapes).
  """
  for name, value in (('width', width), ('height', height),
                      ('divider', divider), ('num_shapes', num_shapes)):
    if value is not None and type(value) is not int:
      raise ValueError(name + ' must be an integer')
  if shapes is None:
    width, height, divider, scene = _sample_scene(width, height, divider,
                                                  num_shapes)
  else:
    if width is None or height is None or divider is None:
      raise ValueError('explicit shapes require width, height and divider')
    if num_shapes is not None and num_shapes != len(shapes):
      raise ValueError('num_shapes does not match len(shapes)')
    scene = [(top, left, _parse(p)) for top, left, p in shapes]
    _check_explicit(width, height, divider, scene)
  return _render(width, height, divider, scene)


def validate():
  """Reconstructs the canonical examples via explicit latent parameters."""
  train = [
      generate(width=16, height=16, divider=11, shapes=[
          (0, 0, ['XXXX..', 'XX.X..', '.XXXX.', 'XXXXXX',
                  '...X.X', '...X.X', '...X.X', '...XXX']),
          (11, 8, ['XXX', 'X.X', 'X.X', 'XXX']),
      ]),
      generate(width=10, height=16, divider=5, shapes=[
          (0, 0, ['XXX.', 'X.X.', 'XXXX', '.X.X', '.XXX']),
          (7, 0, ['XXX', 'X.X', 'XXX', 'X..', 'XXX']),
          (13, 0, ['XXX', 'X.X', 'XXX']),
      ]),
      generate(width=10, height=20, divider=7, shapes=[
          (0, 1, ['XXXXX', 'X...X', 'XXXXX']),
          (4, 2, ['XXXX', 'X..X', 'X..X', 'XXXX']),
          (9, 4, ['XX', 'XX']),
          (12, 1, ['XXXXX', 'X.X.X', 'XXXXX']),
          (16, 1, ['XXXX', 'X..X', 'XXXX']),
      ]),
  ]
  test = [
      generate(width=12, height=25, divider=8, shapes=[
          (2, 1, ['XXXX.', 'X.X..', 'XXXXX', '....X', '....X']),
          (8, 4, ['XXX', '..X', 'XXX']),
          (12, 3, ['XXXX', 'X..X', 'XXXX']),
          (16, 0, ['.XXX', '.X.X', 'XXXX', '.X.X', '.XXX']),
          (22, 5, ['XXX', 'X.X', 'XXX']),
      ]),
  ]
  return {'train': train, 'test': test}
