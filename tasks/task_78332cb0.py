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

"""ARC task 78332cb0: chain panels into a single strip.

Rule: the input is a layout of equal-sized panels on background 7, separated
by full divider lines of colour 6. Each panel holds one monochrome shape.
Every shape touches only the two edges of one chain axis: top/bottom for a
vertical chain, or left/right for a horizontal chain. Each contact is a single
interior cell. Exactly one panel has no entry contact (top or left), and it
starts the chain. Each following panel's entry cell lines up with the
previous panel's exit cell (bottom or right). The last panel has no exit.
The output concatenates the panels in chain order along the chain axis, with
one divider line between neighbours.

A middle panel may enter and leave at the same position. Its shape is then a
straight bar across the whole panel, as with the 1 in train pair 3. In a 1xN
layout with a vertical chain, or an Nx1 layout with a horizontal chain, such
a bar is a full grid line of the shape colour. It competes with the real
dividers. The divider colour is the colour that forms the most full lines,
and the generator keeps shape-colour full lines strictly fewer than the
divider lines.

When two panels share an entry position, which is unavoidable after a bar,
the complete chain must still be unique. The correct successor need not be
the first in reading order: all panels must be used before reaching the end.
Random samples also include non-adjacent repeated contacts (short detours).

Scope: the original layouts are 2x2, 1xN and Nx1 with N in 2..4. As
synthetic extensions the generator also samples 1x5, 5x1, 1x6, 6x1, 2x3 and
3x2 layouts wherever the 30-cell limit allows them. Default panel sides are
4..10, and explicit sides of 3..28 are accepted when they fit. The chain axis
is independent of the layout where the size limits allow it. Background 7 and
divider 6 are fixed, as in every original example. Shape colours come from
the other eight colours and may repeat. Shapes are an L/Z backbone joining
the contact cells, grown with random interior cells. Bars are straight lines,
sometimes with extra interior cells.
"""

import random

import common

BG = 7
DIV = 6
PALETTE = [0, 1, 2, 3, 4, 5, 8, 9]
LAYOUTS = [((2, 2), 4), ((1, 3), 2), ((3, 1), 2), ((1, 4), 2), ((4, 1), 2),
           ((1, 2), 1), ((2, 1), 1), ((1, 5), 1), ((5, 1), 1), ((2, 3), 1),
           ((3, 2), 1), ((1, 6), 1), ((6, 1), 1)]
SIZE_CHOICES = list(range(4, 11))


def _shape(H, W, a, b, extras=None):
  """Build a connected shape in canonical orientation (entry=top, exit=bottom).

  a: entry column, or None for the chain start.
  b: exit column, or None for the chain end. If a == b the backbone is a
    straight full-height bar.
  extras: number of interior cells to grow; sampled if None.
  """
  r = random.randint(1, H - 2)
  cells = set()
  a2 = random.randint(1, W - 2) if a is None else a
  b2 = random.randint(1, W - 2) if b is None else b
  if a is not None:
    for y in range(0, r + 1):
      cells.add((y, a))
  if b is not None:
    for y in range(r, H):
      cells.add((y, b))
  for x in range(min(a2, b2), max(a2, b2) + 1):
    cells.add((r, x))
  if extras is None:
    limit = max(len(cells), (H * W * 2) // 5)
    extras = random.randint(0, min(6, limit - len(cells)))
  for _ in range(extras):
    cands = []
    for y in range(1, H - 1):
      for x in range(1, W - 1):
        if (y, x) in cells:
          continue
        if any((y + dy, x + dx) in cells
               for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))):
          cands.append((y, x))
    if not cands:
      break
    cells.add(random.choice(cands))
  return cells


def _parse(bitmap):
  return {(y, x) for y, row in enumerate(bitmap)
          for x, ch in enumerate(row) if ch == 'x'}


def _contacts(cells, ph, pw, vertical):
  """Return (entry, exit) contact tuples of a panel, or None when absent."""
  if vertical:
    ent = tuple(sorted(x for (y, x) in cells if y == 0))
    ext = tuple(sorted(x for (y, x) in cells if y == ph - 1))
  else:
    ent = tuple(sorted(y for (y, x) in cells if x == 0))
    ext = tuple(sorted(y for (y, x) in cells if x == pw - 1))
  return (ent or None), (ext or None)


def _chain_ok(entries, exits, order):
  """Check that the slots form exactly one chain, equal to order.

  Reading order is irrelevant; a unique complete path is required.
  """
  n = len(entries)
  starts = [s for s in range(n) if entries[s] is None]
  ends = [s for s in range(n) if exits[s] is None]
  if len(starts) != 1 or len(ends) != 1:
    return False
  found = []

  def walk(path, used):
    if len(found) > 1:
      return
    cur = path[-1]
    if len(path) == n:
      if exits[cur] is None:
        found.append(list(path))
      return
    if exits[cur] is None:
      return
    for s in range(n):
      if s not in used and entries[s] == exits[cur]:
        used.add(s)
        path.append(s)
        walk(path, used)
        path.pop()
        used.discard(s)

  walk([starts[0]], {starts[0]})
  if len(found) != 1 or found[0] != list(order):
    return False
  return True


def _render(rows, cols, ph, pw, vertical, order, colors, cellsets):
  n = rows * cols
  height = rows * ph + rows - 1
  width = cols * pw + cols - 1
  grid = common.grid(width, height, BG)
  for i in range(1, rows):
    for x in range(width):
      grid[i * (ph + 1) - 1][x] = DIV
  for j in range(1, cols):
    for y in range(height):
      grid[y][j * (pw + 1) - 1] = DIV
  for s in range(n):
    oy, ox = (s // cols) * (ph + 1), (s % cols) * (pw + 1)
    for (y, x) in cellsets[s]:
      grid[oy + y][ox + x] = colors[s]
  if vertical:
    out = common.grid(pw, n * ph + n - 1, BG)
    for k in range(1, n):
      for x in range(pw):
        out[k * (ph + 1) - 1][x] = DIV
  else:
    out = common.grid(n * pw + n - 1, ph, BG)
    for k in range(1, n):
      for y in range(ph):
        out[y][k * (pw + 1) - 1] = DIV
  for k, s in enumerate(order):
    oy, ox = (k * (ph + 1), 0) if vertical else (0, k * (pw + 1))
    for (y, x) in cellsets[s]:
      out[oy + y][ox + x] = colors[s]
  return grid, out


def _valid(grid, rows, cols):
  """Check that the divider colour is unambiguous and the background dominates."""
  ndiv = (rows - 1) + (cols - 1)
  counts = {}
  lines = [list(r) for r in grid] + [list(c) for c in zip(*grid)]
  for line in lines:
    if len(set(line)) == 1 and line[0] not in (BG, DIV):
      counts[line[0]] = counts.get(line[0], 0) + 1
  if counts and max(counts.values()) >= ndiv:
    return False
  hist = {}
  for row in grid:
    for v in row:
      hist[v] = hist.get(v, 0) + 1
  bgc = hist.get(BG, 0)
  return all(c < bgc for v, c in hist.items() if v != BG)


def _check_side(v, name):
  if v is None:
    return
  if isinstance(v, bool) or not isinstance(v, int) or not 3 <= v <= 28:
    raise ValueError(name + ' must be an integer in 3..28')


def _sizes(rows, cols, vert, height, width):
  """List the (panel height, panel width) pairs that fit the constraints."""
  n = rows * cols
  phs = [height] if height is not None else SIZE_CHOICES
  pws = [width] if width is not None else SIZE_CHOICES
  res = []
  for ph in phs:
    for pw in pws:
      along, cross = (ph, pw) if vert else (pw, ph)
      if along < 3 or cross < n + 1:
        continue
      if n * along + n - 1 > 30:
        continue
      if rows * ph + rows - 1 > 30 or cols * pw + cols - 1 > 30:
        continue
      res.append((ph, pw))
  return res


def _aligned(rows, cols, vert):
  return (vert and cols == 1) or ((not vert) and rows == 1)


def _plan(rows, cols, height, width, vertical, order, colors, repeat):
  """Resolve the partial controls into one feasible (layout, axis, sizes)."""
  for v, name in ((rows, 'rows'), (cols, 'cols')):
    if v is not None and (isinstance(v, bool) or not isinstance(v, int)
                          or v < 1):
      raise ValueError(name + ' must be a positive integer')
  _check_side(height, 'height')
  _check_side(width, 'width')
  if vertical is not None and type(vertical) is not bool:
    raise ValueError('vertical must be True, False or None')
  if repeat is not None and type(repeat) is not bool:
    raise ValueError('repeat_contacts must be True, False or None')
  n_req = None
  for seq in (order, colors):
    if seq is not None:
      if n_req is not None and len(seq) != n_req:
        raise ValueError('order and colors must have the same length')
      n_req = len(seq)
  if order is not None and (any(type(x) is not int for x in order) or sorted(order) != list(range(len(order)))):
    raise ValueError('order must be a permutation of the slot indices')
  if colors is not None and any(type(c) is not int or c not in PALETTE for c in colors):
    raise ValueError('shape colours must avoid background 7 and divider 6')
  if rows is not None and cols is not None:
    cands = [((rows, cols), 1)]
  else:
    cands = [(lc, w) for lc, w in LAYOUTS
             if (rows is None or lc[0] == rows)
             and (cols is None or lc[1] == cols)]
  verts = [vertical] if vertical is not None else [True, False]
  options = []
  for (r, c), w in cands:
    n = r * c
    if not 2 <= n <= 6 or (n_req is not None and n != n_req):
      continue
    if repeat and n < 3:
      continue  # A bar needs a middle panel.
    for v in verts:
      if (order is not None and _aligned(r, c, v)
          and list(order) == list(range(n))):
        continue  # Would be an identity sample.
      sizes = _sizes(r, c, v, height, width)
      if sizes:
        options.append((r, c, v, sizes, w))
  if not options:
    raise ValueError('incompatible generation parameters')
  return random.choices(options, weights=[o[4] for o in options])[0][:4]


def _sample(rows, cols, vert, sizes, order, colors, repeat):
  n = rows * cols
  weights = [(3 if ph == 5 else 1) * (3 if pw == 5 else 1)
             for ph, pw in sizes]
  ph, pw = random.choices(sizes, weights=weights)[0]
  along, cross = (ph, pw) if vert else (pw, ph)
  if order is not None:
    slots = list(order)
  else:
    slots = list(range(n))
    random.shuffle(slots)
    if _aligned(rows, cols, vert) and slots == sorted(slots):
      slots.reverse()
  if colors is not None:
    cols_by_slot = list(colors)
  elif random.random() < 0.3:
    cols_by_slot = [random.choice(PALETTE)] * n
  else:
    cols_by_slot = [random.choice(PALETTE) for _ in range(n)]
  # contacts[k] is the exit of chain position k and the entry of k + 1.
  contacts = random.sample(range(1, cross - 1), n - 1)
  if repeat is None and n >= 4 and random.random() < .25:
    contacts = [random.randrange(1, cross - 1) for _ in range(n - 1)]
  if repeat is None:
    want = n >= 3 and random.random() < 0.35
  else:
    want = repeat
  bars = []
  if want:
    # A bar repeats its contact; shuffle order freely, including greedy traps.
    cands = list(range(1, n - 1))
    if not cands:
      if repeat and order is not None:
        raise ValueError('order leaves no valid position for a bar panel')
      return None
    random.shuffle(cands)
    bars.append(cands[0])
    for p in cands[1:]:
      if random.random() < 0.3 and all(abs(p - q) > 1 for q in bars):
        bars.append(p)
    for p in sorted(bars):
      contacts[p] = contacts[p - 1]
  entries = [None] * n
  exits = [None] * n
  for k in range(n):
    entries[slots[k]] = (contacts[k - 1],) if k > 0 else None
    exits[slots[k]] = (contacts[k],) if k < n - 1 else None
  if not _chain_ok(entries, exits, slots):
    return None
  cellsets = [None] * n
  for k in range(n):
    a = contacts[k - 1] if k > 0 else None
    b = contacts[k] if k < n - 1 else None
    extras = 0 if (k in bars and random.random() < 0.5) else None
    canon = _shape(along, cross, a, b, extras)
    cells = canon if vert else {(x, y) for (y, x) in canon}
    cellsets[slots[k]] = cells
  grid, out = _render(rows, cols, ph, pw, vert, slots, cols_by_slot, cellsets)
  if not _valid(grid, rows, cols):
    return None
  return grid, out


def generate(rows=None, cols=None, height=None, width=None, vertical=None,
             order=None, colors=None, repeat_contacts=None, bitmaps=None):
  """Generate one input/output pair.

  rows, cols: panel layout (panel rows x panel columns). Either one may be
    given alone, and the other is then chosen from the supported layouts.
  height, width: size of each panel (integers 3..28 that must fit 30 cells).
  vertical: True if the chain runs top->bottom, False if left->right.
  order: slot indices (reading order) listed in chain order.
  colors: shape colour for each slot (reading order), from PALETTE.
  repeat_contacts: True forces at least one straight bar panel (entry ==
    exit, which repeats a contact position). False forbids bars. None
    samples them sometimes.
  bitmaps: for each slot, a list of strings with 'x' marking shape cells.
    This is used for fixture replay, and rows, cols, height, width,
    vertical, order and colors are then required. The bitmaps must form the
    stated unique chain. If bitmaps is None, a fresh random scene is built
    and every given argument constrains the sampler. Incompatible
    combinations raise ValueError.
  """
  for value, name in ((rows, 'rows'), (cols, 'cols')):
    if value is not None and (type(value) is not int or not 1 <= value <= 6):
      raise ValueError(name + ' must be an integer 1..6')
  _check_side(height, 'height')
  _check_side(width, 'width')
  if vertical is not None and type(vertical) is not bool:
    raise ValueError('vertical must be boolean')
  if repeat_contacts is not None and type(repeat_contacts) is not bool:
    raise ValueError('repeat_contacts must be boolean')
  if bitmaps is not None:
    needed = (rows, cols, height, width, vertical, order, colors)
    if any(v is None for v in needed):
      raise ValueError('bitmap replay needs every layout argument')
    if repeat_contacts is not None:
      raise ValueError('repeat_contacts only applies to random generation')
    n = rows * cols
    if not 2 <= n <= 6:
      raise ValueError('need two to six panels')
    if len(bitmaps) != n or len(order) != n or len(colors) != n:
      raise ValueError('bitmaps, order and colors must cover every slot')
    if any(type(x) is not int for x in order) or sorted(order) != list(range(n)):
      raise ValueError('order must be a permutation of the slot indices')
    if any(type(c) is not int or c not in PALETTE for c in colors):
      raise ValueError('shape colours must avoid background 7 and divider 6')
    for b in bitmaps:
      if len(b) != height or any(len(row) != width for row in b):
        raise ValueError('bitmap size must match height and width')
      if any(ch not in '.x' for line in b for ch in line):
        raise ValueError('bitmap may only contain dot and x')
    if (rows * height + rows - 1 > 30 or cols * width + cols - 1 > 30
        or n * (height if vertical else width) + n - 1 > 30):
      raise ValueError('grid exceeds 30 cells')
    cellsets = [_parse(b) for b in bitmaps]
    entries, exits = [], []
    for cells in cellsets:
      if not cells:
        raise ValueError('panel shape must not be empty')
      reached, todo = set(), [next(iter(cells))]
      while todo:
        y, x = todo.pop()
        if (y,x) in reached:
          continue
        reached.add((y,x))
        todo.extend(q for q in ((y-1,x),(y+1,x),(y,x-1),(y,x+1))
                    if q in cells and q not in reached)
      if reached != cells:
        raise ValueError('panel shape must be connected')
      if any((x in (0,width-1) if vertical else y in (0,height-1))
             for y,x in cells):
        raise ValueError('shape touches a cross-axis edge')
      e, x = _contacts(cells, height, width, vertical)
      if (e is not None and len(e)!=1) or (x is not None and len(x)!=1):
        raise ValueError('contacts must be single cells')
      entries.append(e)
      exits.append(x)
    if not _chain_ok(entries, exits, order):
      raise ValueError('bitmaps do not form the stated unique chain')
    grid, out = _render(rows, cols, height, width, vertical, order, colors,
                        cellsets)
    if not _valid(grid, rows, cols):
      raise ValueError('background or divider is ambiguous')
    return {'input': grid, 'output': out}
  r, c, v, sizes = _plan(rows, cols, height, width, vertical, order, colors,
                         repeat_contacts)
  for _ in range(300):
    res = _sample(r, c, v, sizes, order, colors, repeat_contacts)
    if res is not None:
      return {'input': res[0], 'output': res[1]}
  raise RuntimeError('could not sample a valid scene')


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(rows=2, cols=2, height=5, width=5, vertical=True,
               order=[0, 3, 1, 2], colors=[2, 4, 1, 3],
               bitmaps=[
                   ['.....', '.....', '.....', '.xxx.', '..x..'],
                   ['.x...', '.xxx.', '...x.', '...x.', '...x.'],
                   ['...x.', '.xxx.', '.xxx.', '.xxx.', '.....'],
                   ['..x..', '.xx..', '.x...', '.x...', '.x...'],
               ]),
      generate(rows=3, cols=1, height=5, width=5, vertical=False,
               order=[2, 1, 0], colors=[8, 2, 9],
               bitmaps=[
                   ['.....', '..xx.', '..xx.', 'xxx..', '.....'],
                   ['.....', 'xxx..', '..xx.', '...xx', '.....'],
                   ['.....', '.x.xx', '.xxx.', '.x...', '.....'],
               ]),
      generate(rows=1, cols=3, height=5, width=5, vertical=True,
               order=[0, 1, 2], colors=[8, 1, 9],
               bitmaps=[
                   ['.....', '.xxx.', '..x..', '..x..', '..x..'],
                   ['..x..', '..x..', '..x..', '..x..', '..x..'],
                   ['..x..', '.xxx.', '.....', '.....', '.....'],
               ]),
  ]
  test = [
      generate(rows=2, cols=2, height=5, width=5, vertical=False,
               order=[2, 3, 1, 0], colors=[4, 4, 4, 4],
               bitmaps=[
                   ['.....', '.xxx.', 'xx.x.', '.xxx.', '.....'],
                   ['.....', 'xxxx.', '...xx', '.xxx.', '.....'],
                   ['.....', '.xxx.', '.x.x.', '.x.xx', '.....'],
                   ['.....', '.x.xx', '.x.x.', 'xxxx.', '.....'],
               ]),
      generate(rows=4, cols=1, height=5, width=5, vertical=True,
               order=[3, 1, 2, 0], colors=[9, 2, 2, 9],
               bitmaps=[
                   ['...x.', '..xx.', '.xx..', '.x...', '.....'],
                   ['.x...', '.x...', '.xx..', '..x..', '..x..'],
                   ['..x..', '.xxx.', '...x.', '...x.', '...x.'],
                   ['.....', '...x.', '..xx.', '.xx..', '.x...'],
               ]),
  ]
  return {'train': train, 'test': test}
