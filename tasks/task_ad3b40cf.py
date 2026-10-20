# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ARC-GEN style generator for task ad3b40cf.

Rule: the background is 8. One straight line of colour 1 runs from edge to
edge. It is vertical, horizontal, diagonal (r - c = k) or anti-diagonal
(r + c = s). Objects in two other colours sit beside it. Count the total
cells of each object colour. Every object of the colour with the strictly
smaller total is reflected across the line. A mirrored cell is painted only
where it lands inside the grid on a background cell. All other cells stay the
same.

Geometry (random generation):
- All four orientations are sampled.
- Orthogonal lines sit near the centre by default. An explicit line index may
  be anywhere that leaves room.
- Diagonals run corner to corner on square grids, as in the fixtures. As a
  synthetic extension they may also be offset diagonals on square or
  rectangular grids, up to 30 per side.
- Objects lie on one side of the line. Every object cell has offset |v| >= 2
  from the line, where v is c - col, r - row, (r - c) - k or (r + c) - s. So
  objects never share an edge with the line. On diagonal lines they may touch
  it at a corner, like the canonical test's colour-4 cell at (5,3). For
  orthogonal lines |v| >= 2 is the same as not 8-adjacent.
- Every mirrored cell stays inside the grid.

Reflectable region and exact feasibility:
- Orthogonal: D = min(line, across - 1 - line) - 1 usable columns (or rows)
  per side, times the line length L.
- Diagonal: a triangle inside the L x L square spanned by the in-grid segment.
- A scene needs two separated objects, each with at least 2 cells, with
  unequal totals. The smallest witness is a domino plus a tromino.
- Orthogonal minimum line lengths: D >= 4 needs L >= 2, D = 3 needs L >= 3,
  D = 2 needs L >= 4, and D = 1 needs L >= 6. D <= 0 is impossible.
- Diagonal: segments need L >= 6. L = 5 cannot hold the witness.
- Lines always cover at least 2 cells, so the orientation is unambiguous.
- Geometries are sampled only when they are feasible. Late attempts fall back
  to an exhaustive domino plus tromino packing. So no accepted geometry is
  dead under the default flags.

Objects and anti-proxy flags:
- 2 to 6 random 4-connected polyominoes, each with at least 2 cells and
  fitting a 4x4 box. They never touch, even diagonally.
- Objects are coloured by a random valid two-colour partition, so the totals
  are never equal.
- hard: the smaller-total colour owns strictly more objects.
- tight: the totals differ by at most 2.
- smallbreak: the larger-total colour owns an object strictly smaller than
  every rare-colour object.
- Flag values: True means required and never released. False means not
  required. None means drawn at random as a preference.
- A randomly drawn flag is dropped for an attempt whose region cannot hold
  enough objects. All randomly drawn flags are released after half the retry
  budget. Request a flag explicitly to guarantee it.

Default never samples clipped mirrors or mirrors landing on objects. Explicit
objects= mode is a documented extension that applies the clip/occlusion rule.
"""

import random

import common

BG = 8
LINE = 1
KINDS = ('vertical', 'horizontal', 'diagonal', 'antidiagonal')
ORTHO = ('vertical', 'horizontal')
PALETTE = (2, 3, 4, 5, 6, 7, 9)
MIN_DIAG = 6
ATTEMPTS = 240
RELEASE_AT = 120
FALLBACK_AT = 160
DOMINOES = (((0, 0), (0, 1)), ((0, 0), (1, 0)))
TROMINOES = (((0, 0), (0, 1), (0, 2)), ((0, 0), (1, 0), (2, 0)),
             ((0, 0), (0, 1), (1, 0)), ((0, 0), (0, 1), (1, 1)),
             ((0, 0), (1, 0), (1, 1)), ((0, 1), (1, 0), (1, 1)))


def _is_int(value):
  return isinstance(value, int) and not isinstance(value, bool)


def _line_cells(kind, height, width, line):
  """Cells of the mirror line (column, row, r - c or r + c index)."""
  if kind == 'vertical':
    return {(r, line) for r in range(height)}
  if kind == 'horizontal':
    return {(line, c) for c in range(width)}
  if kind == 'diagonal':
    return {(r, r - line) for r in range(height) if 0 <= r - line < width}
  return {(r, line - r) for r in range(height) if 0 <= line - r < width}


def _diag_len(kind, height, width, line):
  if kind == 'diagonal':
    lo, hi = max(0, line), min(height - 1, width - 1 + line)
  else:
    lo, hi = max(0, line - width + 1), min(height - 1, line)
  return max(0, hi - lo + 1)


def _mirror(kind, line, r, c):
  if kind == 'vertical':
    return r, 2 * line - c
  if kind == 'horizontal':
    return 2 * line - r, c
  if kind == 'diagonal':
    return c + line, r - line
  return line - c, line - r


def _offset(kind, line, r, c):
  if kind == 'vertical':
    return c - line
  if kind == 'horizontal':
    return r - line
  if kind == 'diagonal':
    return (r - c) - line
  return (r + c) - line


def _halo(cells):
  out = set()
  for r, c in cells:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        out.add((r + dr, c + dc))
  return out


def _shape(h, w, n):
  cells = {(random.randrange(h), random.randrange(w))}
  for _ in range(400):
    if len(cells) >= n:
      break
    r, c = random.choice(sorted(cells))
    dr, dc = random.choice(((0, 1), (1, 0), (0, -1), (-1, 0)))
    nr, nc = r + dr, c + dc
    if 0 <= nr < h and 0 <= nc < w:
      cells.add((nr, nc))
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  return sorted((r - r0, c - c0) for r, c in cells)


def _check_size(value, name):
  if value is not None and (not _is_int(value) or not 1 <= value <= 30):
    raise ValueError('%s must be an integer in 1..30' % name)


def _check_color(col):
  if not _is_int(col) or not 0 <= col <= 9 or col in (BG, LINE):
    raise ValueError('object colours must be integers 0..9 and not 1 or 8')


def _check_colors(colors):
  if colors is None:
    return None
  if not isinstance(colors, (list, tuple)) or len(colors) != 2:
    raise ValueError('colors must be a list or tuple of two colours')
  colors = tuple(colors)
  for col in colors:
    _check_color(col)
  if colors[0] == colors[1]:
    raise ValueError('colors must be two distinct colours')
  return colors


def _check_flag(value, name):
  if value is not None and not isinstance(value, bool):
    raise ValueError('%s must be True, False or None' % name)


def _depth(across, ln):
  """Usable columns (rows) per side: offset >= 2 and mirror inside grid."""
  return min(ln, across - 1 - ln) - 1


def _ortho_need(depth):
  """Exact minimum line length for a domino + tromino witness."""
  if depth >= 4:
    return 2
  if depth == 3:
    return 3
  if depth == 2:
    return 4
  if depth == 1:
    return 6
  return None


def _ortho_options(across, along, line):
  """Feasible (across, line index) pairs for an orthogonal line."""
  if across is not None:
    acrosses = [across]
  elif line is not None:
    acrosses = range(max(5, line + 3), 31)
  else:
    acrosses = range(7, 26)
  opts = []
  for a in acrosses:
    if line is not None:
      lns = [line]
    else:
      lns = [v for v in range(a // 2 - 2, a // 2 + 3) if 0 <= v < a]
    for ln in lns:
      need = _ortho_need(_depth(a, ln))
      if need is None or (along is not None and along < need):
        continue
      opts.append((a, ln))
  return opts


def _diag_pairs(kind, height, width, line):
  hs = [height] if height is not None else range(MIN_DIAG, 31)
  ws = [width] if width is not None else range(MIN_DIAG, 31)
  return [(h, w) for h in hs for w in ws
          if _diag_len(kind, h, w, line) >= MIN_DIAG]


def _compatible(kind, height, width, line):
  """True iff some feasible geometry of this kind fits the controls."""
  if kind in ORTHO:
    vertical = kind == 'vertical'
    across = width if vertical else height
    along = height if vertical else width
    return bool(_ortho_options(across, along, line))
  if line is None:
    return all(v >= MIN_DIAG for v in (height, width) if v is not None)
  return bool(_diag_pairs(kind, height, width, line))


def _sample_geometry(kind, height, width, line):
  """Return a feasible (height, width, line)."""
  if kind in ORTHO:
    vertical = kind == 'vertical'
    across = width if vertical else height
    along = height if vertical else width
    a, ln = random.choice(_ortho_options(across, along, line))
    if along is None:
      along = random.randint(max(5, _ortho_need(_depth(a, ln))), 24)
    return (along, a, ln) if vertical else (a, along, ln)
  if line is not None:
    h, w = random.choice(_diag_pairs(kind, height, width, line))
    return h, w, line
  if height is None and width is None:
    if random.random() < 0.6:
      h = w = random.randint(MIN_DIAG, 24)
    else:
      h, w = random.randint(MIN_DIAG, 26), random.randint(MIN_DIAG, 26)
  elif width is None:
    h = height
    w = height if random.random() < 0.6 else random.randint(MIN_DIAG, 26)
  elif height is None:
    w = width
    h = width if random.random() < 0.6 else random.randint(MIN_DIAG, 26)
  else:
    h, w = height, width
  if h == w and random.random() < 0.5:
    return h, w, (0 if kind == 'diagonal' else h - 1)
  centre = (h - w) // 2 if kind == 'diagonal' else (h + w - 2) // 2
  cands = [v for v in range(centre - 4, centre + 5)
           if _diag_len(kind, h, w, v) >= MIN_DIAG]
  return h, w, random.choice(cands)


def _allowed(kind, height, width, line, side):
  cells = set()
  for r in range(height):
    for c in range(width):
      if _offset(kind, line, r, c) * side < 2:
        continue
      mr, mc = _mirror(kind, line, r, c)
      if 0 <= mr < height and 0 <= mc < width:
        cells.add((r, c))
  return cells


def _place_random(allowed, count):
  """Place count separated random polyominoes, or return None."""
  anchors = sorted(allowed)
  blocked = set()
  shapes = []
  for _ in range(count):
    placed = None
    for _ in range(60):
      sh, sw = random.randint(1, 4), random.randint(1, 4)
      if sh * sw == 1:
        sw = 2
      shape = _shape(sh, sw, random.randint(max(2, sh, sw), sh * sw))
      if len(shape) < 2:
        continue
      pr, pc = random.choice(shape)
      ar, ac = random.choice(anchors)
      cells = [(ar + r - pr, ac + c - pc) for r, c in shape]
      if all(cell in allowed and cell not in blocked for cell in cells):
        placed = cells
        break
    if placed is None:
      return None
    blocked |= _halo(placed)
    shapes.append(placed)
  return shapes


def _witness(allowed):
  """Exhaustive randomised domino + separated tromino packing."""
  cells = sorted(allowed)
  order_a = cells[:]
  random.shuffle(order_a)
  for ar, ac in order_a:
    for shape in random.sample(DOMINOES, len(DOMINOES)):
      a = [(ar + dr, ac + dc) for dr, dc in shape]
      if not all(x in allowed for x in a):
        continue
      blocked = _halo(a)
      order_b = cells[:]
      random.shuffle(order_b)
      for br, bc in order_b:
        for tri in random.sample(TROMINOES, len(TROMINOES)):
          b = [(br + dr, bc + dc) for dr, dc in tri]
          if all(x in allowed and x not in blocked for x in b):
            return a, b
  return None


def _kmin(hard, smallbreak):
  if hard and smallbreak:
    return 5
  if hard or smallbreak:
    return 3
  return 2


def _assignments(sizes, hard, tight, smallbreak):
  """Masks (bit set = first colour) giving unequal totals and the flags."""
  k = len(sizes)
  out = []
  for mask in range(1, (1 << k) - 1):
    gx = [sizes[i] for i in range(k) if (mask >> i) & 1]
    gy = [sizes[i] for i in range(k) if not (mask >> i) & 1]
    tx, ty = sum(gx), sum(gy)
    if tx == ty:
      continue
    rare, other = (gx, gy) if tx < ty else (gy, gx)
    if hard and len(rare) <= len(other):
      continue
    if tight and abs(tx - ty) > 2:
      continue
    if smallbreak and min(other) >= min(rare):
      continue
    out.append(mask)
  return out


def _random_scene(height, width, kind, line, side, colors, hard, tight,
                  smallbreak):
  """Sample a scene honouring every fixed control."""
  _check_size(height, 'height')
  _check_size(width, 'width')
  if kind is not None and kind not in KINDS:
    raise ValueError('unknown kind %r' % (kind,))
  if line is not None and not _is_int(line):
    raise ValueError('line must be an integer')
  if side is not None and (not _is_int(side) or side not in (-1, 1)):
    raise ValueError('side must be -1, 1 or None')
  colors = _check_colors(colors)
  _check_flag(hard, 'hard')
  _check_flag(tight, 'tight')
  _check_flag(smallbreak, 'smallbreak')
  kinds = [kind] if kind is not None else list(KINDS)
  kinds = [k for k in kinds if _compatible(k, height, width, line)]
  if not kinds:
    raise ValueError('no mirror orientation fits the fixed size/line '
                     'controls')
  chance = {'hard': 0.4, 'tight': 0.35, 'smallbreak': 0.35}
  flags = {}
  drawn = set()
  for name, value in (('hard', hard), ('tight', tight),
                      ('smallbreak', smallbreak)):
    if value is None:
      flags[name] = random.random() < chance[name]
      drawn.add(name)
    else:
      flags[name] = value
  strict = hard is True or smallbreak is True
  for attempt in range(ATTEMPTS):
    if attempt == RELEASE_AT:
      for name in drawn:
        flags[name] = False
    k = random.choice(kinds)
    h, w, ln = _sample_geometry(k, height, width, line)
    sd = side if side is not None else random.choice((-1, 1))
    lcells = _line_cells(k, h, w, ln)
    allowed = _allowed(k, h, w, ln, sd)
    if not allowed:
      continue
    kmax = min(6, max(2, len(allowed) // 8))
    eff = dict(flags)
    for name in ('smallbreak', 'hard'):
      if name in drawn and _kmin(eff['hard'], eff['smallbreak']) > kmax:
        eff[name] = False
    kmin = _kmin(eff['hard'], eff['smallbreak'])
    if kmin > kmax:
      continue
    cols = colors if colors is not None else tuple(random.sample(PALETTE, 2))
    if attempt >= FALLBACK_AT and not strict:
      wit = _witness(allowed)
      if wit is None:
        continue
      shapes = [wit[0], wit[1]]
      mask = 1 if random.random() < 0.5 else 2
    else:
      shapes = _place_random(allowed, random.randint(kmin, kmax))
      if shapes is None:
        continue
      masks = _assignments([len(s) for s in shapes], eff['hard'],
                           eff['tight'], eff['smallbreak'])
      if not masks:
        continue
      mask = random.choice(masks)
    objects = [(cols[0] if (mask >> i) & 1 else cols[1], cells)
               for i, cells in enumerate(shapes)]
    totals = {}
    for col, cells in objects:
      totals[col] = totals.get(col, 0) + len(cells)
    nbg = h * w - len(lcells) - sum(totals.values())
    if nbg <= max([len(lcells)] + list(totals.values())):
      continue
    return h, w, k, ln, objects
  raise ValueError('requested parameters admit no valid scene within the '
                   'retry budget (explicit hard/smallbreak need room for '
                   '3-5 objects)')


def _normalise_objects(objects):
  if not isinstance(objects, (list, tuple)):
    raise ValueError('objects must be a list of (colour, cells) pairs')
  norm = []
  for obj in objects:
    if not isinstance(obj, (list, tuple)) or len(obj) != 2:
      raise ValueError('each object must be a (colour, cells) pair')
    col, cells = obj
    _check_color(col)
    if not isinstance(cells, (list, tuple)) or not cells:
      raise ValueError('object cells must be a non-empty list')
    pts = []
    for cell in cells:
      if (not isinstance(cell, (list, tuple)) or len(cell) != 2 or
          not all(_is_int(v) for v in cell)):
        raise ValueError('each cell must be an integer (row, col) pair')
      pts.append((cell[0], cell[1]))
    norm.append((col, pts))
  return norm


def generate(height=None, width=None, kind=None, line=None, side=None,
             colors=None, hard=None, tight=None, smallbreak=None,
             objects=None):
  """Build one input/output pair.

  height, width: grid size, 1..30.
  kind: 'vertical', 'horizontal', 'diagonal' (r - c == line) or
    'antidiagonal' (r + c == line).
  line: the column, row, r - c or r + c of the mirror line, depending on the
    kind. If kind is None, its meaning depends on the sampled kind.
    Explicit mode: a diagonal kind may omit line only on a square grid; the
    line then runs corner to corner.
  side: -1 or 1, the side that holds the objects (random mode only). -1
    means left, above, r - c < line or r + c < line.
  colors: two distinct object colours, not 1 or 8 (random mode only).
  hard, tight, smallbreak: anti-proxy flags (random mode only).
    True means required and never released. False means not required. None
    means a random preference that may be released.
    - hard: the rare colour has strictly more objects.
    - tight: the totals differ by at most 2.
    - smallbreak: the frequent colour owns an object smaller than every rare
      object.
  objects: explicit list of (colour, [(row, col), ...]) objects. This mode is
    an extension that applies clipping and occlusion as the rule states.
    - Requires height, width and kind, plus line for orthogonal kinds.
    - The line covers at least 2 cells.
    - Objects of different colours are not 8-adjacent.
    - No object cell shares an edge with the line.
    - The rarest colour is unique.
    - 8 is the most frequent colour.
  Incompatible fixed controls raise ValueError.
  """
  if objects is None:
    height, width, kind, line, objects = _random_scene(
        height, width, kind, line, side, colors, hard, tight, smallbreak)
  else:
    if any(v is not None for v in (side, colors, hard, tight, smallbreak)):
      raise ValueError('side/colors/flags only apply to random generation')
    if height is None or width is None or kind not in KINDS:
      raise ValueError('explicit objects need height, width and kind')
    _check_size(height, 'height')
    _check_size(width, 'width')
    if line is not None and not _is_int(line):
      raise ValueError('line must be an integer')
    if kind in ORTHO:
      if line is None:
        raise ValueError('orthogonal kinds need a line index')
      across = width if kind == 'vertical' else height
      along = height if kind == 'vertical' else width
      if not 0 <= line < across:
        raise ValueError('line index outside the grid')
      if along < 2:
        raise ValueError('an orthogonal line must cover at least two cells')
    else:
      if line is None:
        if height != width:
          raise ValueError('corner-to-corner diagonals need a square grid')
        line = 0 if kind == 'diagonal' else height - 1
      if _diag_len(kind, height, width, line) < 2:
        raise ValueError('diagonal line must cover at least two cells')
    objects = _normalise_objects(objects)
  lcells = _line_cells(kind, height, width, line)
  grid = common.grid(width, height, BG)
  for r, c in lcells:
    grid[r][c] = LINE
  totals = {}
  owner = {}
  for col, cells in objects:
    for r, c in cells:
      if not (0 <= r < height and 0 <= c < width) or (r, c) in lcells:
        raise ValueError('object cell outside grid or on the line')
      if (r, c) in owner:
        raise ValueError('object cells must not repeat or overlap')
      owner[(r, c)] = col
      grid[r][c] = col
      totals[col] = totals.get(col, 0) + 1
  for (r, c), col in owner.items():
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        nb = (r + dr, c + dc)
        if nb in owner and owner[nb] != col:
          raise ValueError('objects of different colours must not touch')
        if abs(dr) + abs(dc) == 1 and nb in lcells:
          raise ValueError('objects must not share an edge with the line')
  ranked = sorted(totals.values())
  if not ranked or (len(ranked) > 1 and ranked[0] == ranked[1]):
    raise ValueError('rarest colour must be unique')
  nbg = height * width - len(lcells) - len(owner)
  if nbg <= max([len(lcells)] + ranked):
    raise ValueError('background 8 must be the most frequent colour')
  output = [row[:] for row in grid]
  rare = min(totals, key=lambda v: totals[v])
  for col, cells in objects:
    if col != rare:
      continue
    for r, c in cells:
      mr, mc = _mirror(kind, line, r, c)
      if 0 <= mr < height and 0 <= mc < width and output[mr][mc] == BG:
        output[mr][mc] = rare
  return {'input': grid, 'output': output}


def _rect(r0, c0, h, w):
  return [(r0 + r, c0 + c) for r in range(h) for c in range(w)]


def validate():
  """Reconstruct the canonical fixtures through explicit generate calls."""
  train = [
      generate(height=9, width=9, kind='vertical', line=4, objects=[
          (5, _rect(1, 6, 2, 2)),
          (2, [(4, 6), (5, 6), (6, 6), (7, 6), (7, 7)]),
      ]),
      generate(height=16, width=16, kind='antidiagonal', line=15, objects=[
          (7, _rect(1, 1, 3, 2)),
          (7, [(1, 8), (1, 9), (1, 10), (2, 9)]),
          (6, [(2, 5), (3, 5), (3, 6)]),
          (7, [(6, 5), (7, 3), (7, 4), (7, 5)]),
          (6, _rect(9, 1, 2, 2)),
      ]),
      generate(height=15, width=15, kind='horizontal', line=7, objects=[
          (2, _rect(1, 2, 2, 2)),
          (6, _rect(2, 10, 3, 3)),
          (2, [(4, 6), (4, 7), (5, 7)]),
          (6, [(4, 1), (5, 1), (5, 2)]),
      ]),
  ]
  test = [
      generate(height=17, width=17, kind='diagonal', line=0, objects=[
          (4, [(5, 1), (5, 2), (5, 3), (6, 2), (7, 2)]),
          (7, [(9, 1), (9, 2), (10, 1)]),
          (7, [(11, 4), (12, 4), (13, 4), (14, 4), (14, 5), (15, 4),
               (15, 5)]),
          (4, [(12, 7), (12, 8), (12, 9), (13, 9), (14, 9), (15, 9)]),
          (4, _rect(13, 1, 3, 2)),
          (7, [(15, 11), (15, 12)]),
      ]),
  ]
  return {'train': train, 'test': test}
