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

"""ARC-GEN style generator for task df978a02.

Rule: four single-colour, 8-connected shapes sit above, below, left of and
right of one empty background centre cell. The centre is the background cell
whose four rays (up, down, left and right) hit four distinct colours with the
smallest total ray length. Each shape's tip is the first cell its ray hits.
The colour with the most cells wins. The three losing tips become background.
The winner keeps its tip and gains a 3-cell line one step beyond its far edge
on the centre's row or column. The line is centred on that axis.

Scope: the background is 8 by default, and any colour may be requested.
Random grids are 12-24 per side by default, and 8-30 per side is accepted.
Every fixture is 16x16 with background 8. Other sizes, non-square grids,
other backgrounds and tip distance 3 are synthetic extensions. Four distinct
shape colours are drawn. The centre position, the tip distances (1-3), the
shape lengths (2-8) and the lateral extents all vary. Tip distances are
sampled jointly so that a vertical tip and a horizontal tip are never both at
distance 1, because such tips would touch diagonally.

A random shape is a width-1 tip followed by a stack of depth segments. A
segment is usually a solid lateral interval through the axis. It can instead
have a hole on the axis, be a comb with gaps at odd lateral offsets, or lie
wholly to one side of the axis. Every maximal run of a new segment must touch
the previous segment at least diagonally. The one exception is a run that
dangles, such as a comb tine. In that case the segment may repeat and is then
closed by a solid row spanning it, as in the fixture '#.#.#' / '#####' rows.
So every shape is one 8-connected component, as in all fixtures. Losers may
reach the grid edge. The winner always leaves room for its stamp.

The winner's farthest cell on the centre axis is also its farthest cell in
its direction, as in every fixture, so the stamp always lies wholly beyond
the shape. The fixtures do not decide between 'beyond the axis cell' and
'beyond the shape', so that case is not sampled.

Other invariants:
- Shapes are mutually 8-separated.
- The largest shape is strictly largest.
- The background is a strict majority.
- The random centre is the unique minimum-ray centre.
- The stamp lands on background that is not 8-adjacent to any loser.

About 35% of scenes require a decoy loser. A decoy is deeper than the winner,
has a larger bounding box, or has a strictly nearer tip.

Fixtures are rebuilt from explicit latent shapes, given per direction as
colour, origin and '#' pattern, plus the grid size and the centre. Explicit
scenes must be 8-connected per shape and lie strictly on their own side of
the centre. An explicit centre may tie the minimum ray total only if it is
first in row-major order, which is the reference tie-break.
"""

import itertools
import random

import common

DIRS = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}
ORDER = ('up', 'down', 'left', 'right')
VERTICAL = ('up', 'down')
HORIZONTAL = ('left', 'right')


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _pattern_cells(origin, pattern):
  top, left = origin
  cells = []
  for r, row in enumerate(pattern):
    for c, ch in enumerate(row):
      if ch == '#':
        cells.append((top + r, left + c))
  return cells


def _pos(cy, cx, name, t, s):
  dy, dx = DIRS[name]
  if dy:
    return (cy + dy * t, cx + s)
  return (cy + s, cx + dx * t)


def _signed_depth(cy, cx, name, cell):
  dy, dx = DIRS[name]
  r, c = cell
  return (r - cy) * dy if dy else (c - cx) * dx


def _axis_range(cy, cx, name, cells):
  dy, dx = DIRS[name]
  ts = []
  for r, c in cells:
    if dy and c == cx and (r - cy) * dy > 0:
      ts.append((r - cy) * dy)
    if dx and r == cy and (c - cx) * dx > 0:
      ts.append((c - cx) * dx)
  if not ts:
    raise ValueError('shape %s does not touch the centre axis' % name)
  return min(ts), max(ts)


def _depth(cy, cx, name, cells):
  return max(_signed_depth(cy, cx, name, cell) for cell in cells)


def _bbox_area(cells):
  rs = [r for r, _ in cells]
  cs = [c for _, c in cells]
  return (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)


def _connected(cells):
  """True if the cells form one 8-connected component."""
  cells = set(cells)
  if not cells:
    return False
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


def _has_decoy(cy, cx, latent, win):
  """True if some loser is deeper, has a larger bbox or a nearer tip."""
  wcells = latent[win][1]
  wd = _depth(cy, cx, win, wcells)
  wa = _bbox_area(wcells)
  wt = _axis_range(cy, cx, win, wcells)[0]
  for n in ORDER:
    if n == win:
      continue
    cells = latent[n][1]
    if (_depth(cy, cx, n, cells) > wd or _bbox_area(cells) > wa or
        _axis_range(cy, cx, n, cells)[0] < wt):
      return True
  return False


def _ray_total(g, bg, y, x):
  h, w = len(g), len(g[0])
  total, cols = 0, []
  for dy, dx in DIRS.values():
    yy, xx, d = y + dy, x + dx, 1
    while 0 <= yy < h and 0 <= xx < w and g[yy][xx] == bg:
      yy += dy
      xx += dx
      d += 1
    if not (0 <= yy < h and 0 <= xx < w):
      return None
    cols.append(g[yy][xx])
    total += d
  if len(set(cols)) < 4:
    return None
  return total


def _centre_status(g, bg, cy, cx):
  """Classify the candidate centre against every other background cell.

  Returns 'unique' if the centre is the strict minimum. Returns 'first' if it
  is tied but first in row-major order. Otherwise returns None.
  """
  if g[cy][cx] != bg:
    return None
  mine = _ray_total(g, bg, cy, cx)
  if mine is None:
    return None
  status = 'unique'
  for y in range(len(g)):
    for x in range(len(g[0])):
      if (y, x) == (cy, cx) or g[y][x] != bg:
        continue
      t = _ray_total(g, bg, y, x)
      if t is None:
        continue
      if t < mine:
        return None
      if t == mine:
        if (y, x) < (cy, cx):
          return None
        status = 'first'
  return status


def _first_hit(g, bg, cy, cx, name):
  h, w = len(g), len(g[0])
  dy, dx = DIRS[name]
  yy, xx = cy + dy, cx + dx
  while 0 <= yy < h and 0 <= xx < w and g[yy][xx] == bg:
    yy += dy
    xx += dx
  if not (0 <= yy < h and 0 <= xx < w):
    return None
  return (yy, xx)


def _lateral_room(h, w, cy, cx, name):
  """Room for the negative and positive lateral offsets s of a shape."""
  if DIRS[name][0]:
    return cx, w - 1 - cx
  return cy, h - 1 - cy


def _tip_combos(space, winner):
  """All tip-distance assignments in which adjacent tips do not touch.

  A vertical tip at distance dv and a horizontal tip at distance dh are at
  Chebyshev distance max(dv, dh), so at least one of them must be >= 2.
  An arm with room sp may use tip distance up to min(3, sp - 1). A requested
  winner arm needs d <= sp - 2 so that its stamp fits inside the grid.
  """
  ranges = []
  for name in ORDER:
    hi = min(3, space[name] - 1)
    if winner == name:
      hi = min(hi, space[name] - 2)
    ranges.append(range(1, hi + 1))
  combos = []
  for combo in itertools.product(*ranges):
    d = dict(zip(ORDER, combo))
    if all(max(d[v], d[z]) >= 2 for v in VERTICAL for z in HORIZONTAL):
      combos.append(d)
  return combos


def _runs(seg):
  """Maximal runs of consecutive lateral offsets."""
  runs, cur = [], []
  for s in sorted(seg):
    if cur and s != cur[-1] + 1:
      runs.append(cur)
      cur = []
    cur.append(s)
  if cur:
    runs.append(cur)
  return runs


def _runs_touch(seg, prev):
  """True if every run of seg touches prev at least diagonally."""
  near = set()
  for p in prev:
    near.update((p - 1, p, p + 1))
  return all(any(s in near for s in run) for run in _runs(seg))


def _segment(a, b, amax, bmax, prev, plain, sym):
  """Lateral offsets of one depth segment; some run touches prev."""
  full = set(range(-a, b + 1))
  seg = full
  if not plain:
    roll = random.random()
    if roll < 0.12 and a >= 1 and b >= 1:
      seg = full - {0}  # hole on the axis
    elif roll < 0.24 and (a >= 2 or b >= 2):
      seg = set(s for s in full if s % 2 == 0)  # comb, gaps at odd offsets
    elif roll < 0.36 and not sym and (a >= 1 or b >= 1):
      options = []
      if a >= 1:
        lo = random.randint(1, a)
        options.append(set(range(-a, -lo + 1)))
      if b >= 1:
        lo = random.randint(1, b)
        options.append(set(range(lo, b + 1)))
      seg = random.choice(options)
  near = set()
  for p in prev:
    near.update((p - 1, p, p + 1))
  if seg & near:
    return seg
  lo = max(-amax, min(-a, min(prev)))
  hi = min(bmax, max(b, max(prev)))
  return set(range(lo, hi + 1))


def _random_shape(cy, cx, name, d, length, amax, bmax):
  """One 8-connected shape: a tip plus depth segments.

  A segment with a run that dangles (it does not touch the previous segment)
  is either repeated or closed. The closing row is solid and spans the
  segment. A dangling final segment is replaced by a bridging solid row.
  """
  cells = [_pos(cy, cx, name, d, 0)]
  sym = random.random() < 0.4
  plain = random.random() < 0.5
  cap = min(amax, bmax)
  a = random.randint(0, cap if sym else amax)
  b = a if sym else random.randint(0, bmax)
  prev = {0}
  pending = None
  for k in range(1, length):
    last = k == length - 1
    if pending is not None:
      if last or random.random() < 0.5:
        seg = set(range(min(pending), max(pending) + 1))
        pending = None
      else:
        seg = set(pending)
    else:
      if k > 1:
        if sym:
          a = min(cap, max(0, a + random.choice([-1, 0, 0, 1])))
          b = a
        else:
          a = min(amax, max(0, a + random.choice([-1, 0, 0, 1])))
          b = min(bmax, max(0, b + random.choice([-1, 0, 0, 1])))
      seg = _segment(a, b, amax, bmax, prev, plain, sym)
      if not _runs_touch(seg, prev):
        if last:
          lo = min(min(seg), min(prev))
          hi = max(max(seg), max(prev))
          seg = set(range(lo, hi + 1))
        else:
          pending = set(seg)
    for s in sorted(seg):
      cells.append(_pos(cy, cx, name, d + k, s))
    prev = seg
  return cells


def _build(width, height, bg, shapes):
  g = common.grid(width, height, bg)
  for name in ORDER:
    colour, cells = shapes[name]
    for r, c in cells:
      g[r][c] = colour
  return g


def _winner(shapes):
  sizes = sorted((len(shapes[n][1]) for n in ORDER), reverse=True)
  if sizes[0] == sizes[1]:
    return None
  return max(ORDER, key=lambda n: len(shapes[n][1]))


def _stamp_cells(cy, cx, shapes, win):
  _, tmax = _axis_range(cy, cx, win, shapes[win][1])
  return [_pos(cy, cx, win, tmax + 1, s) for s in (-1, 0, 1)]


def _stamp_ok(owner, stamp, win, h, w):
  """Stamp cells are in-grid background, not 8-adjacent to any loser."""
  for r, c in stamp:
    if not (0 <= r < h and 0 <= c < w) or (r, c) in owner:
      return False
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        o = owner.get((r + dr, c + dc))
        if o is not None and o != win:
          return False
  return True


def _far_edge_on_axis(cy, cx, shapes, win):
  cells = shapes[win][1]
  return _axis_range(cy, cx, win, cells)[1] == _depth(cy, cx, win, cells)


def _answer(g, bg, cy, cx, shapes, win):
  out = [row[:] for row in g]
  for name in ORDER:
    if name != win:
      tmin, _ = _axis_range(cy, cx, name, shapes[name][1])
      r, c = _pos(cy, cx, name, tmin, 0)
      out[r][c] = bg
  for r, c in _stamp_cells(cy, cx, shapes, win):
    out[r][c] = shapes[win][0]
  return out


def _separated(shapes, h, w):
  owner = {}
  for name in ORDER:
    for r, c in shapes[name][1]:
      if not (0 <= r < h and 0 <= c < w) or (r, c) in owner:
        return None
      owner[(r, c)] = name
  for (r, c), name in owner.items():
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        o = owner.get((r + dr, c + dc))
        if o is not None and o != name:
          return None
  return owner


def _check_colour(c, what):
  if not _is_int(c) or not 0 <= c <= 9:
    raise ValueError('%s must be an int colour 0-9' % what)


def _check_dim(v, what):
  if not _is_int(v) or not 8 <= v <= 30:
    raise ValueError('%s must be an int in 8..30' % what)


def _check_center(center):
  if (not isinstance(center, (tuple, list)) or len(center) != 2 or
      not all(_is_int(v) for v in center)):
    raise ValueError('center must be a (row, col) pair of ints')


def _explicit(width, height, center, shapes, bg):
  if width is None or height is None or center is None:
    raise ValueError('explicit shapes need width, height and center')
  _check_dim(width, 'width')
  _check_dim(height, 'height')
  _check_center(center)
  if not isinstance(shapes, dict) or set(shapes) != set(ORDER):
    raise ValueError('shapes must give exactly up/down/left/right')
  cy, cx = center
  if not (0 <= cy < height and 0 <= cx < width):
    raise ValueError('center lies outside the grid')
  latent = {}
  for n in ORDER:
    spec = shapes[n]
    if not isinstance(spec, (tuple, list)) or len(spec) != 3:
      raise ValueError('each shape is (colour, (top, left), pattern)')
    colour, origin, pattern = spec
    _check_colour(colour, 'shape colour')
    if (not isinstance(origin, (tuple, list)) or len(origin) != 2 or
        not all(_is_int(v) for v in origin)):
      raise ValueError('shape origin must be a (top, left) pair of ints')
    if (not isinstance(pattern, (tuple, list)) or
        not all(isinstance(row, str) for row in pattern)):
      raise ValueError('shape pattern must be a list of strings')
    latent[n] = (colour, _pattern_cells(origin, pattern))
  cols = [latent[n][0] for n in ORDER]
  if len(set(cols)) != 4 or bg in cols:
    raise ValueError('shape colours must be distinct and differ from bg')
  for n in ORDER:
    cells = latent[n][1]
    if not cells:
      raise ValueError('shape %s is empty' % n)
    if any(_signed_depth(cy, cx, n, cell) <= 0 for cell in cells):
      raise ValueError('shape %s must lie strictly on its own side' % n)
    if not _connected(cells):
      raise ValueError('shape %s must be one 8-connected component' % n)
  owner = _separated(latent, height, width)
  if owner is None:
    raise ValueError('explicit shapes overlap, touch or leave the grid')
  if (cy, cx) in owner:
    raise ValueError('centre must be background')
  if 2 * len(owner) >= width * height:
    raise ValueError('background must be a strict majority')
  win = _winner(latent)
  if win is None:
    raise ValueError('explicit shapes tie for largest')
  g = _build(width, height, bg, latent)
  for n in ORDER:
    hit = _first_hit(g, bg, cy, cx, n)
    if hit is None or hit not in set(latent[n][1]):
      raise ValueError('the %s ray does not hit the %s shape first' % (n, n))
  if _centre_status(g, bg, cy, cx) is None:
    raise ValueError('center is not the selected minimum-ray centre')
  if not _far_edge_on_axis(cy, cx, latent, win):
    raise ValueError('winner far edge must lie on the centre axis')
  if not _stamp_ok(owner, _stamp_cells(cy, cx, latent, win), win, height,
                   width):
    raise ValueError('winner stamp leaves the grid or touches a shape')
  return {'input': g, 'output': _answer(g, bg, cy, cx, latent, win)}


def generate(width=None, height=None, center=None, shapes=None,
             background=None, colors=None, winner=None):
  """Build one df978a02 example.

  Args:
    width: grid width (8-30). Random scenes sample 12-24 when omitted.
    height: grid height (8-30). Random scenes sample 12-24 when omitted.
    center: (row, col) of the empty centre cell. Random scenes need at least
      3 cells of room on every side (3 <= row <= height-4, and the same for
      col).
    shapes: optional full latent specification. This is a dict mapping each
      of up/down/left/right to (colour, (top, left), pattern rows using '#').
      It requires width, height and center, and cannot be combined with
      colors or winner. The scene is checked:
      - each shape is 8-connected and strictly on its own side;
      - shapes are 8-separated;
      - the rays hit their own shapes;
      - the centre is the selected centre;
      - the winner's far edge is on the axis;
      - the stamp lands on in-grid background away from losers;
      - the background is a strict majority.
    background: background colour. Defaults to 8.
    colors: optional 4 distinct non-background shape colours, given in
      up/down/left/right order.
    winner: optional direction name ('up', 'down', 'left' or 'right') that the
      largest shape must occupy.
  """
  bg = 8 if background is None else background
  _check_colour(bg, 'background')
  if shapes is not None:
    if colors is not None or winner is not None:
      raise ValueError('shapes is a full specification; omit colors/winner')
    return _explicit(width, height, center, shapes, bg)

  if winner is not None and winner not in ORDER:
    raise ValueError('winner must be one of %s' % (ORDER,))
  if colors is not None:
    colors = list(colors)
    if len(colors) != 4:
      raise ValueError('colors needs exactly 4 entries')
    for c in colors:
      _check_colour(c, 'color')
    if len(set(colors)) != 4 or bg in colors:
      raise ValueError('colors must be distinct and differ from background')
  if width is not None:
    _check_dim(width, 'width')
  if height is not None:
    _check_dim(height, 'height')
  if center is not None:
    _check_center(center)
    ccy, ccx = center
    if ccy < 3 or ccx < 3:
      raise ValueError('center needs at least 3 cells of room on each side')
    if height is not None and ccy > height - 4:
      raise ValueError('center row too close to the bottom edge')
    if width is not None and ccx > width - 4:
      raise ValueError('center column too close to the right edge')
    if ccy + 4 > 30 or ccx + 4 > 30:
      raise ValueError('center too far from the origin')

  want_decoy = random.random() < 0.35
  for attempt in range(3000):
    if height is not None:
      h = height
    else:
      lo = 12 if center is None else max(12, center[0] + 4)
      h = random.randint(lo, min(30, max(lo, 24)))
    if width is not None:
      w = width
    else:
      lo = 12 if center is None else max(12, center[1] + 4)
      w = random.randint(lo, min(30, max(lo, 24)))
    if center is not None:
      cy, cx = center
    else:
      cy, cx = random.randint(3, h - 4), random.randint(3, w - 4)
    cols = list(colors) if colors is not None else random.sample(
        [c for c in range(10) if c != bg], 4)
    space = {'up': cy, 'down': h - 1 - cy, 'left': cx, 'right': w - 1 - cx}
    combos = _tip_combos(space, winner)
    if not combos:
      continue
    tips = random.choice(combos)
    rcap = max(1, min(4, min(h, w) // 4))
    latent = {}
    for i, name in enumerate(ORDER):
      sp = space[name]
      d = tips[name]
      # Normally the shape stays one cell off the far edge. When d = sp - 1 a
      # 2-long shape reaches the edge; such a shape can only be a loser.
      length = random.randint(2, max(2, min(8, sp - d)))
      rmax = random.randint(1, rcap)
      low, high = _lateral_room(h, w, cy, cx, name)
      latent[name] = (cols[i], _random_shape(
          cy, cx, name, d, length, min(rmax, low), min(rmax, high)))
    if not all(_connected(latent[n][1]) for n in ORDER):
      continue  # defensive; construction keeps every shape connected
    owner = _separated(latent, h, w)
    if owner is None:
      continue
    if 2 * len(owner) >= h * w:
      continue  # the background must be a strict majority colour
    win = _winner(latent)
    if win is None:
      continue
    if winner is not None and win != winner:
      continue
    if not _far_edge_on_axis(cy, cx, latent, win):
      continue
    if want_decoy and attempt < 1500 and not _has_decoy(cy, cx, latent, win):
      continue
    if not _stamp_ok(owner, _stamp_cells(cy, cx, latent, win), win, h, w):
      continue
    g = _build(w, h, bg, latent)
    if _centre_status(g, bg, cy, cx) != 'unique':
      continue
    return {'input': g, 'output': _answer(g, bg, cy, cx, latent, win)}
  raise RuntimeError('could not build a df978a02 scene for these settings')


def validate():
  """Rebuild the canonical fixtures from explicit latent shapes."""
  train = [
      generate(width=16, height=16, center=(8, 7), shapes={
          'up': (4, (2, 6), ['###', '###', '###', '###', '###', '.#.']),
          'down': (7, (9, 6), ['.#.', '.#.', '#.#']),
          'left': (2, (4, 0), ['##', '.##', '..##', '...##', '....##',
                               '...##', '...#']),
          'right': (9, (7, 9), ['.#', '#', '.#']),
      }),
      generate(width=16, height=16, center=(8, 7), shapes={
          'up': (4, (4, 6), ['.#', '###', '###', '.#']),
          'down': (1, (9, 6), ['.#', '##', '.#']),
          'left': (6, (6, 3), ['#', '##', '###', '##']),
          'right': (7, (6, 9), ['..#', '.##', '###', '.##', '..#']),
      }),
      generate(width=16, height=16, center=(8, 7), shapes={
          'up': (3, (3, 3), ['#########', '.#######', '..#####', '....#']),
          'down': (0, (9, 5), ['..#', '..#', '#.#.#', '#.#.#', '#.#.#',
                               '#####']),
          'left': (1, (5, 2), ['#', '##', '###', '####', '###', '#']),
          'right': (5, (7, 9), ['.##', '###', '.##']),
      }),
  ]
  test = [
      generate(width=16, height=16, center=(7, 7), shapes={
          'up': (9, (2, 3), ['..#####', '########', '..#####', '....#']),
          'down': (1, (9, 4), ['...#', '#######', '...#']),
          'left': (6, (6, 1), ['..##', '#####', '..##']),
          'right': (2, (4, 9), ['...###', '...#', '.###', '####', '.###',
                                '...#', '...###']),
      }),
  ]
  return {'train': train, 'test': test}
