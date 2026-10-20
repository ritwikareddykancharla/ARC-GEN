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

"""Generator for ARC task 9bbf930d (markers escape through bar corridors).

Rule. Background is 7. Column 0 is a stripe of 6 markers and column 1 is
background. Horizontal bars lie on even rows and start at x=2 or x=3.
A row y is released when all three conditions hold:
  (1) the first non-background cells of rows y-1 and y+1 share a colour;
  (2) those two cells sit at the same x;
  (3) row y is background at that x.
For each released row, the 6 at (y, 0) becomes 7. A walker starts at
(y, 1) heading right. It moves straight while the next cell is background.
When it is blocked, it turns into the unique perpendicular background
neighbour whose two flanking cells are equal and non-background. With zero
or two such openings it stops, and a 6 is written at the stop cell. Every
walk reads the input grid.

Random scenes are built from latent objects:
  * Bar tokens: corridor pairs (same colour and start), an optional blocked
    pair (same colour and start, with a connector cell at the start column
    in the gap, so condition 3 fails), and single bars. Adjacent singles
    sometimes share a colour but differ in start, so only condition 2 fails.
  * One route design per corridor:
      open      runs to the right edge;
      cap       closed by a bracket;
      badturn   an opening with unequal flanks, so the walker stops;
      fork      two valid openings, so the walker stops;
      down/up   a channel to the bottom or top edge;
      downstop/upstop   a channel that ends on a bar;
      downturn/upturn   channel, then right along a gap row to the edge;
      zigdown/zigup     the rich route class. Right, then a vertical
          channel, then a LEFT turn along a gap row (hook flank above,
          stop bar below), then a blocker cell, then a third turn back into
          the original vertical direction through gaps split into one to
          three bars. The walk ends either on an unsplit bar (both side
          openings symmetric, so it stops) or at the grid edge. A two-turn
          variant instead ends on the leftward leg at the blocker.
  * Hard negatives on bar rows (decoys):
      isolated  equal-colour stubs in both neighbouring gap rows at
                different x. The upper stub lies where the bar row is
                background, so conditions 1 and 3 hold and only condition 2
                rejects the row;
      samex     the same x, inside the bar (only condition 3 rejects);
      inbar     different x, both inside the bar.
  * Decorations: turn flanks in the corridor colour or a foreign colour,
    channel walls, bar runs past hooks, and one-cell stubs in gap rows.
Every dead end comes from the planned route. A local copy of the rule is
used only as a bounded consistency filter: an attempt is discarded when the
walker, the released-row set, end uniqueness, or the strict dominance of
colour 7 disagrees with the design.

Scope. Width is 10..30 and height is odd, 11..29. After 400 failed
attempts, alternate attempts use only local designs, so dense or narrow
requests still succeed. Fixtures are replayed from explicit rectangle
segments; their dead ends are derived by the local walker, because the
original mazes are not members of the design family.
"""

import random

import common

BG = 7
MARK = 6
PALETTE = [0, 1, 2, 3, 4, 5, 8, 9]


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _paint(width, height, segments):
  g = common.grid(width, height, BG)
  for r in range(height):
    g[r][0] = MARK
  for color, r0, c0, r1, c1 in segments:
    for r in range(r0, r1 + 1):
      for c in range(c0, c1 + 1):
        g[r][c] = color
  return g


def _first(g, r):
  for x in range(1, len(g[r])):
    if g[r][x] != BG:
      return x, g[r][x]
  return None, None


def _released(g):
  rows = []
  for y in range(1, len(g) - 1):
    if g[y][0] != MARK or g[y][1] != BG:
      continue
    xa, ca = _first(g, y - 1)
    xb, cb = _first(g, y + 1)
    if ca is None or cb is None or ca != cb or xa != xb:
      continue
    if g[y][xa] != BG:
      continue
    rows.append(y)
  return rows


def _opening(g, r, c, dr, dc):
  height, width = len(g), len(g[0])
  if not (0 <= r < height and 0 <= c < width) or g[r][c] != BG:
    return False
  sides = ((r + dc, c + dr), (r - dc, c - dr))
  for sr, sc in sides:
    if not (0 <= sr < height and 0 <= sc < width):
      return False
  a = g[sides[0][0]][sides[0][1]]
  b = g[sides[1][0]][sides[1][1]]
  return a != BG and b != BG and a == b


def _walk(g, y):
  height, width = len(g), len(g[0])
  r, c, dr, dc = y, 1, 0, 1
  for _ in range(4 * height * width):
    nr, nc = r + dr, c + dc
    if 0 <= nr < height and 0 <= nc < width and g[nr][nc] == BG:
      r, c = nr, nc
      continue
    options = []
    for tr, tc in ((dc, dr), (-dc, -dr)):
      if _opening(g, r + tr, c + tc, tr, tc):
        options.append((tr, tc))
    if len(options) != 1:
      break
    dr, dc = options[0]
    r, c = r + dr, c + dc
  return r, c


def _bg_dominant(g):
  counts = {}
  for row in g:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  top = counts.get(BG, 0)
  return all(c < top for v, c in counts.items() if v != BG)


def _try_scene(width, n, count, zig_mode, relax):
  """Builds one latent scene; returns (segments, ends, zig_rows) or None."""
  height = 2 * n - 1
  nblock = 1 if count < n // 2 and random.random() < 0.35 else 0
  tokens = ['P'] * count + ['B'] * nblock
  tokens += ['S'] * (n - 2 * (count + nblock))
  random.shuffle(tokens)
  colors, starts, pairs, blocked = [], [], [], []
  prev, prev_start, prev_single = None, None, False
  for tok in tokens:
    if tok == 'S' and prev_single and random.random() < 0.25:
      # Same colour as the previous single bar, different start: no corridor.
      color, start = prev, 5 - prev_start
    else:
      color = random.choice([p for p in PALETTE if p != prev])
      start = 2 if random.random() < 0.75 else 3
    if tok == 'P':
      pairs.append(len(colors))
    elif tok == 'B':
      blocked.append(len(colors))
    size = 1 if tok == 'S' else 2
    colors += [color] * size
    starts += [start] * size
    prev, prev_start, prev_single = color, start, tok == 'S'
  lo = [s + 3 for s in starts]
  hi = [width - 1] * n
  cells, clash, splits = {}, [], {}
  runs, channels, vchannels, wall_plans = [], [], [], []
  ends, zig_rows = {}, []
  claimed, reserved = set(), set()

  def put(r, x, col):
    if cells.get((r, x), col) != col:
      clash.append((r, x))
    cells[(r, x)] = col

  def pin(bar, x):
    lo[bar], hi[bar] = max(lo[bar], x), min(hi[bar], x)

  corridor_rows = set(2 * k + 1 for k in pairs)
  for k in blocked:
    put(2 * k + 1, starts[k], colors[k])
  gaps = [g for g in range(1, height - 1, 2)
          if g not in corridor_rows and (g - 1) // 2 not in blocked]

  def hook_turn(k, e, downward):
    # Blocks corridor row 2k+1 at e+1 and opens a vertical turn at column e.
    y, color, start = 2 * k + 1, colors[k], starts[k]
    put(y, e + 1, color)
    turn, other = (k + 1, k) if downward else (k, k + 1)
    lo[other] = max(lo[other], e + 1)
    near = set(colors[b] for b in (k - 1, k + 2) if 0 <= b < n)
    if e >= start + 5 and random.random() < 0.3:
      flank = random.choice(
          [p for p in PALETTE if p != color and p not in near])
      pin(turn, e - 2)
      put(2 * turn, e - 1, flank)
    else:
      flank = color
      pin(turn, e - 1)
    put(2 * turn, e + 1, flank)
    if random.random() < 0.4:
      runs.append((turn, e + 2, color))

  def zig_params(k, downward, final_turn):
    # Feasible (e, x2, z, zb, sb, splits, w, end_row, stop) or None.
    y, s = 2 * k + 1, starts[k]
    dv = 1 if downward else -1
    edge = n - 1 if downward else 0
    opts = []
    for z in gaps:
      if z in claimed or z in reserved or (z - y) * dv < 4:
        continue
      zb, sb = (z - dv) // 2, (z + dv) // 2
      if not final_turn:
        opts.append((z, zb, sb, [], None, z, None))
        continue
      for m in range(3):
        last = sb + dv * m
        if not 0 <= last < n:
          break
        sp = [sb + dv * i for i in range(m + 1)]
        if last == edge:
          opts.append((z, zb, sb, sp, None, 2 * last, None))
          break
        w = 2 * last + dv
        if w in claimed or w in reserved:
          continue
        opts.append((z, zb, sb, sp, w, w, last + dv))
    random.shuffle(opts)
    for z, zb, sb, sp, w, end_row, stop in opts:
      bars = [zb, sb] + sp + ([stop] if stop is not None else [])
      x2_min = max(starts[b] for b in bars) + 2
      e_min = max(s + 4, x2_min + 3, starts[zb] + 5)
      if e_min > width - 2:
        continue
      e = random.randint(e_min, width - 2)
      x2 = random.randint(x2_min, e - 3)
      return (e, x2, z, zb, sb, sp, w, end_row, stop)
    return None

  def apply_zig(k, downward, final_turn, params):
    e, x2, z, zb, sb, sp, w, end_row, stop = params
    y = 2 * k + 1
    hook_turn(k, e, downward)
    channels.append((e, min(y, z), max(y, z)))
    # Left opening at (z, e-1): hook cell on the crossed bar plus stop bar.
    pin(zb, e - 2)
    put(2 * zb, e - 1, colors[sb])
    lo[sb] = max(lo[sb], e)
    claimed.add(z)
    reserved.add(z)
    put(z, x2 - 1, random.choice(PALETTE))
    if final_turn:
      for b in sp:
        lo[b] = max(lo[b], x2 + 1)
        splits.setdefault(b, []).append(x2)
      if stop is not None:
        lo[stop] = max(lo[stop], x2 + 1)
        claimed.add(w)
        reserved.add(w)
      vchannels.append((x2, min(z, end_row), max(z, end_row)))
      ends[y] = (end_row, x2)
      zig_rows.append(y)
    else:
      ends[y] = (z, x2)
    if random.random() < 0.5:
      span = (y + 2, z - 2) if downward else (z + 2, y - 2)
      wall_plans.append((e + 1, span[0], span[1], random.choice(PALETTE)))

  order = pairs[:]
  random.shuffle(order)
  if zig_mode == 'force':
    chosen = None
    for k in order:
      for downward in random.sample([True, False], 2):
        params = zig_params(k, downward, True)
        if params is not None:
          apply_zig(k, downward, True, params)
          chosen = k
          break
      if chosen is not None:
        break
    if chosen is None:
      return None
    order.remove(chosen)
  for k in order:
    y, color, start = 2 * k + 1, colors[k], starts[k]
    below = [z for z in gaps if z >= y + 2 and z not in claimed]
    above = [z for z in gaps if z <= y - 2 and z not in claimed]
    roomy = start + 4 <= width - 2
    final_turn = random.random() < 0.7
    zig = {}
    if relax:
      options = [('open', 3), ('cap', 3)]
      if roomy:
        options += [('badturn', 1), ('fork', 1)]
    else:
      options = [('open', 2), ('cap', 2)]
      if roomy:
        options += [('down', 2), ('up', 2), ('badturn', 1), ('fork', 1)]
        if below:
          options.append(('downstop', 2))
        if above:
          options.append(('upstop', 2))
        if any(z >= y + 4 for z in below):
          options.append(('downturn', 2))
        if any(z <= y - 4 for z in above):
          options.append(('upturn', 2))
      if zig_mode != 'forbid':
        for name, downward in (('zigdown', True), ('zigup', False)):
          params = zig_params(k, downward, final_turn)
          if params is not None:
            zig[name] = (downward, params)
            options.append((name, 2))
    kind = random.choices([o[0] for o in options], [o[1] for o in options])[0]
    if kind in zig:
      apply_zig(k, zig[kind][0], final_turn, zig[kind][1])
      continue
    if kind == 'open':
      ends[y] = (y, width - 1)
      continue
    if kind == 'cap':
      x = random.randint(start + 4, width - 1)
      pin(k, x)
      pin(k + 1, x)
      put(y, x, color)
      ends[y] = (y, x - 1)
      continue
    e = random.randint(start + 4, width - 2)
    if kind == 'fork':
      # Both perpendicular neighbours are valid openings: the walker stops.
      put(y, e + 1, color)
      for b in (k, k + 1):
        pin(b, e - 1)
        put(2 * b, e + 1, color)
      ends[y] = (y, e)
      continue
    if kind == 'badturn':
      # The only opening has unequal flanks, so it is not a valid turn.
      put(y, e + 1, color)
      turn, other = (k + 1, k) if random.random() < 0.5 else (k, k + 1)
      lo[other] = max(lo[other], e + 1)
      pin(turn, e - 1)
      put(2 * turn, e + 1, random.choice([p for p in PALETTE if p != color]))
      ends[y] = (y, e)
      continue
    downward = kind.startswith('down')
    hook_turn(k, e, downward)
    walled = random.random() < 0.5
    wall_color = random.choice(PALETTE)
    if kind == 'down':
      channels.append((e, y, height - 1))
      ends[y] = (height - 1, e)
      span = (y + 2, height - 1)
    elif kind == 'up':
      channels.append((e, 0, y))
      ends[y] = (0, e)
      span = (0, y - 2)
    elif kind in ('downstop', 'upstop'):
      z = random.choice(below if kind == 'downstop' else above)
      claimed.add(z)
      if kind == 'downstop':
        channels.append((e, y, z))
        stop = (z + 1) // 2
        span = (y + 2, z)
      else:
        channels.append((e, z, y))
        stop = (z - 1) // 2
        span = (z, y - 2)
      lo[stop] = max(lo[stop], e)
      ends[y] = (z, e)
    else:
      if kind == 'downturn':
        z = random.choice([g for g in below if g >= y + 4])
        channels.append((e, y, z))
        stop, hook = (z + 1) // 2, z - 1
        span = (y + 2, z - 2)
      else:
        z = random.choice([g for g in above if g <= y - 4])
        channels.append((e, z, y))
        stop, hook = (z - 1) // 2, z + 1
        span = (z + 2, y - 2)
      claimed.add(z)
      reserved.add(z)
      lo[stop] = max(lo[stop], e + 1)
      wall_color = colors[stop]
      put(hook, e + 1, wall_color)
      ends[y] = (z, width - 1)
    if walled:
      wall_plans.append((e + 1, span[0], span[1], wall_color))
  for col, r0, r1, wc in wall_plans:
    for r in range(r0, r1 + 1):
      if r not in corridor_rows and r not in reserved:
        put(r, col, wc)
  for e, a, b in channels:
    for bar in range(n):
      if a <= 2 * bar <= b:
        hi[bar] = min(hi[bar], e - 1)
  if clash or any(lo[b] > hi[b] for b in range(n)):
    return None

  def crossed(r, x):
    for c, a, b in channels + vchannels:
      if x == c and a <= r <= b:
        return True
    return False

  if any(crossed(r, x) for r, x in cells):
    return None
  ext = [random.randint(lo[b], hi[b]) for b in range(n)]
  for r, x in cells:
    if r % 2 == 0 and starts[r // 2] <= x <= ext[r // 2]:
      return None
  for b in list(splits):
    xs = sorted(set(splits[b]))
    if xs[0] < starts[b] + 2 or xs[-1] > ext[b] - 1:
      return None
    if any(q - p < 3 for p, q in zip(xs, xs[1:])):
      return None
    splits[b] = xs
  segments = []
  for b in range(n):
    a = starts[b]
    for x in splits.get(b, []):
      segments.append((colors[b], 2 * b, a, 2 * b, x - 1))
      a = x + 1
    segments.append((colors[b], 2 * b, a, 2 * b, ext[b]))
  segments += [(col, r, x, r, x) for (r, x), col in sorted(cells.items())]
  for bar, x0, color in runs:
    x = x0
    while x < width and not crossed(2 * bar, x) and (2 * bar, x) not in cells:
      x += 1
    if x - 1 >= x0:
      segments.append((color, 2 * bar, x0, 2 * bar, random.randint(x0, x - 1)))
  tmp = _paint(width, height, segments)
  gapset = set(gaps)

  def free(r):
    return r in gapset and r not in reserved and r not in claimed

  def first_x(r):
    x, _ = _first(tmp, r)
    return width if x is None else x

  def add(r, x, col):
    segments.append((col, r, x, r, x))
    tmp[r][x] = col

  # Decoy bar rows (hard negatives for conditions 2 and 3).
  decoy_rows = set()
  for _ in range(random.choice([0, 1, 1, 2, 2])):
    mode = random.choices(['isolated', 'inbar', 'samex'], [4, 2, 2])[0]
    cands = [b for b in range(1, n - 1)
             if free(2 * b - 1) and free(2 * b + 1)
             and 2 * b - 1 not in decoy_rows and 2 * b + 1 not in decoy_rows]
    random.shuffle(cands)
    for b in cands:
      up, dn, row = 2 * b - 1, 2 * b + 1, tmp[2 * b]
      ups = [x for x in range(starts[b] + 1, first_x(up))
             if not crossed(up, x)]
      dns = [x for x in range(starts[b] + 1, first_x(dn))
             if not crossed(dn, x)]
      if mode == 'isolated':
        # Bar row is background at the upper stub: only condition 2 fails.
        tops = [x for x in ups if row[x] == BG]
        choices = [(a, d) for a in tops for d in dns if d != a]
        color = colors[b] if random.random() < 0.6 else random.choice(PALETTE)
      else:
        in_u = [x for x in ups if row[x] != BG]
        in_d = [x for x in dns if row[x] != BG]
        if mode == 'samex':
          choices = [(x, x) for x in in_u if x in in_d]
        else:
          choices = [(a, d) for a in in_u for d in in_d if a != d]
        color = colors[b]
      if not choices:
        continue
      xa, xd = random.choice(choices)
      add(up, xa, color)
      add(dn, xd, color)
      decoy_rows.update((up, dn))
      break
  for g in gaps:
    if g in reserved or g in decoy_rows or random.random() >= 0.35:
      continue
    b = random.choice([(g - 1) // 2, (g + 1) // 2])
    xs = [x for x in range(starts[b] + 1, ext[b] + 1)
          if tmp[2 * b][x] != BG and tmp[g][x] == BG and not crossed(g, x)]
    if xs:
      add(g, random.choice(xs), colors[b])
  return segments, ends, zig_rows


def _check_random(width, height, num_corridors, zigzag):
  for name, v in (('width', width), ('height', height),
                  ('num_corridors', num_corridors)):
    if v is not None and not _is_int(v):
      raise ValueError('%s must be an int (not bool or float)' % name)
  if zigzag is not None and not isinstance(zigzag, bool):
    raise ValueError('zigzag must be True, False or None')
  if width is not None and not 10 <= width <= 30:
    raise ValueError('random-mode width must be in 10..30')
  if height is not None and (not 11 <= height <= 29 or height % 2 == 0):
    raise ValueError('random-mode height must be odd and in 11..29')
  if num_corridors is not None:
    if not 1 <= num_corridors <= 7:
      raise ValueError('num_corridors must be in 1..7')
    if height is not None and num_corridors > (height + 1) // 4:
      raise ValueError('too many corridors for this height')


def _sample_scene(width, height, num_corridors, zigzag):
  for attempt in range(3000):
    relax = attempt >= 400 and attempt % 2 == 1
    if zigzag is True:
      mode = 'force'
    elif zigzag is False:
      mode = 'forbid'
    else:
      mode = 'force' if random.random() < 0.35 else 'free'
    w = width if width is not None else random.randint(10, 30)
    if height is not None:
      n = (height + 1) // 2
    else:
      n = random.randint(max(6, 2 * (num_corridors or 0)), 15)
    if num_corridors is not None:
      count = num_corridors
    else:
      count = random.randint(1, n // 2)
    scene = _try_scene(w, n, count, mode, relax)
    if scene is None:
      continue
    segments, ends, zig_rows = scene
    if mode == 'force' and not zig_rows:
      continue
    h = 2 * n - 1
    g = _paint(w, h, segments)
    if sorted(_released(g)) != sorted(ends):
      continue
    if len(set(ends.values())) != len(ends):
      continue
    if any(_walk(g, y) != ends[y] for y in ends):
      continue
    if not _bg_dominant(g):
      continue
    return w, h, segments, ends
  raise RuntimeError('could not build a consistent scene')


def _check_segments(width, height, segments):
  if width is None or height is None:
    raise ValueError('segments replay requires explicit width and height')
  if not _is_int(width) or not _is_int(height):
    raise ValueError('width and height must be ints')
  if not (2 <= width <= 30 and 3 <= height <= 30):
    raise ValueError('grid size out of range')
  if not isinstance(segments, (list, tuple)):
    raise ValueError('segments must be a list of 5-tuples')
  for seg in segments:
    if not isinstance(seg, (list, tuple)) or len(seg) != 5:
      raise ValueError('each segment must be (colour, r0, c0, r1, c1)')
    if not all(_is_int(v) for v in seg):
      raise ValueError('segment entries must be ints')
    color, r0, c0, r1, c1 = seg
    if color in (BG, MARK) or not 0 <= color <= 9:
      raise ValueError('segment colour must be 0..9 and not 6 or 7')
    if not (0 <= r0 <= r1 < height and 1 <= c0 <= c1 < width):
      raise ValueError('segment out of bounds or overlapping the stripe')


def generate(width=None, height=None, num_corridors=None, zigzag=None,
             segments=None):
  """Returns an input/output pair for task 9bbf930d.

  Args:
    width: grid width (int, 10..30). Random mode samples 10..30 when None.
      Bools, floats and out-of-range values raise ValueError.
    height: grid height (odd int, 11..29). Bars sit on even rows and the
      last row is a bar. Random mode samples odd heights 11..29 when None.
    num_corridors: number of released corridor rows, an int in 1..7. It must
      satisfy num_corridors <= (height + 1) // 4 when height is given (at
      that maximum every bar is paired). Sampled in 1..(bars // 2)
      when None.
    zigzag: True forces at least one corridor to use the rich route: right,
      vertical channel, LEFT leg, then a third turn through split bars.
      False forbids zig routes. None lets roughly 35% of scenes force one,
      with zig routes otherwise optional. Must be a bool or None.
    segments: optional list of (colour, r0, c0, r1, c1) filled rectangles on
      a background-7 grid whose column 0 is the 6 stripe, used to replay a
      specific scene. width and height are then required, and
      num_corridors and zigzag must be None. Dead ends are derived by the
      local rule walker in this mode only.
  """
  if segments is None:
    _check_random(width, height, num_corridors, zigzag)
    width, height, segments, ends = _sample_scene(
        width, height, num_corridors, zigzag)
    grid = _paint(width, height, segments)
  else:
    if num_corridors is not None or zigzag is not None:
      raise ValueError('num_corridors/zigzag are incompatible with segments')
    _check_segments(width, height, segments)
    grid = _paint(width, height, segments)
    ends = dict((y, _walk(grid, y)) for y in _released(grid))
  output = [row[:] for row in grid]
  for y in sorted(ends):
    output[y][0] = BG
  for y in sorted(ends):
    r, c = ends[y]
    output[r][c] = MARK
  return {'input': grid, 'output': output}


_P1 = [(1, 0, 2, 0, 12), (1, 2, 2, 2, 12), (4, 2, 13, 4, 13),
       (4, 2, 15, 6, 15), (4, 4, 2, 4, 13), (4, 6, 2, 6, 15),
       (0, 8, 2, 8, 13), (9, 10, 3, 10, 15), (9, 10, 15, 13, 15),
       (9, 12, 3, 12, 13), (9, 12, 13, 13, 13), (8, 14, 3, 14, 13),
       (3, 16, 2, 16, 13)]

_P2 = [(c, 2 * i, 2, 2 * i, 11)
       for i, c in enumerate([3, 8, 1, 1, 5, 0, 0, 9, 3, 3])]

_P3 = [(4, 0, 2, 0, 15), (4, 1, 9, 3, 9), (4, 1, 15, 4, 15),
       (4, 2, 2, 2, 7), (4, 2, 11, 2, 13), (4, 3, 7, 3, 7),
       (4, 3, 11, 3, 11), (4, 3, 13, 4, 13), (2, 4, 2, 4, 7),
       (2, 6, 2, 6, 7), (5, 6, 9, 8, 9), (5, 6, 11, 10, 11),
       (5, 8, 2, 8, 9), (5, 10, 2, 10, 11), (9, 6, 13, 10, 13),
       (0, 6, 15, 10, 15), (3, 12, 2, 12, 6), (3, 12, 10, 12, 15),
       (3, 14, 2, 14, 6), (3, 14, 10, 14, 13), (3, 12, 15, 15, 15),
       (3, 14, 13, 15, 13), (0, 16, 2, 16, 13)]

_T1 = [(9, 0, 2, 0, 8), (9, 2, 2, 2, 8), (9, 0, 16, 0, 20),
       (9, 0, 20, 6, 20), (9, 2, 16, 2, 18), (9, 2, 18, 6, 18),
       (0, 4, 2, 4, 8), (0, 6, 2, 6, 8), (0, 8, 2, 8, 8),
       (0, 2, 13, 4, 13), (0, 4, 12, 4, 13), (0, 2, 15, 6, 15),
       (0, 6, 12, 6, 15), (0, 6, 14, 13, 14), (0, 8, 12, 15, 12),
       (0, 13, 14, 13, 16), (0, 15, 12, 15, 16), (8, 8, 15, 8, 18),
       (8, 10, 15, 10, 18), (8, 10, 2, 10, 6), (1, 9, 8, 12, 8),
       (1, 9, 10, 14, 10), (1, 12, 2, 12, 8), (1, 14, 2, 14, 10),
       (4, 16, 2, 16, 9), (4, 18, 2, 18, 9), (4, 16, 13, 16, 16),
       (4, 16, 16, 20, 16), (4, 18, 13, 18, 14), (4, 18, 14, 20, 14),
       (2, 18, 10, 20, 10), (2, 18, 12, 22, 12), (2, 20, 2, 20, 10),
       (2, 22, 2, 22, 12), (9, 19, 18, 20, 18), (9, 20, 17, 20, 18),
       (9, 19, 20, 22, 20), (9, 22, 17, 22, 20)]


def validate():
  """Rebuilds the canonical fixtures from explicit scene segments."""
  train = [
      generate(width=16, height=17, segments=_P1),
      generate(width=14, height=19, segments=_P2),
      generate(width=16, height=17, segments=_P3),
  ]
  test = [generate(width=21, height=23, segments=_T1)]
  return {'train': train, 'test': test}
