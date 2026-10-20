# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the License); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0.  Software
# distributed under the License is distributed on an AS IS BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

"""Generator for ARC task a47bf94d (wires between glyph markers).

Rule. Each marker is a 3x3 glyph in a colour other than 0, 5, 8 or 9. A
glyph is a solid block, an X or a diamond. Markers sit at the ends of wires
of colour 8. Cells of colour 5 are decorations on a wire. Solid blocks of
colour 9 hide parts of the wiring, and a wire leaves a block on the far side,
going straight on when it can. Trace each wire from its marker to its other
end. The glyph centre at that end is two steps past the last wire cell.
  * If a marker already sits at that centre, nothing changes.
  * A solid source becomes a diamond, and an X of its colour is drawn at the
    far end.
  * An X source gets a diamond at the far end.
  * A diamond source gets an X at the far end.

Latent scene model. A scene is a list of wires. Each wire is
(colour, start_kind, end_kind, corner points), plus 9-block rectangles and
visible 5 decoration cells. The input is rendered from this description.
The output is derived from the known wire connections: for each wire with
exactly one glyph, the rule above is applied at the wire's two end slots. No
grid is ever parsed to produce an output. validate() rebuilds the original
fixtures from explicit latent descriptions (generate(width=..., height=...,
wires=..., blocks=..., decorations=...)). These are transcriptions of the
fixture wiring, including the free-form routes, the wire running beside a 9
block, the turn just outside a 9 block and the hidden turn.

Consistency guard. Every scene, explicit or random, is checked with a local
strict re-statement of the tracing rule. Each glyph must reach its latent
partner slot without any order-dependent choice:
  * one start direction;
  * one turn candidate;
  * a unique straight exit from a block, or a single exit.
Random scenes that fail the check are rejected and resampled. Explicit
scenes that fail it raise ValueError. The guard never supplies an output.

Random scenes. There are 2..6 wires between two facing rows of glyph
slots. Each wire has one of three route shapes:
  * straight: no turn;
  * Z: two turns on a private lane;
  * jog: four turns via a private middle column, possibly a back-tracking
    detour.
Columns share a parity and are at least two apart, and lanes are at least
two rows apart. So bare crossings are clean four-way crossings.

Up to four separated 9 blocks are dropped near crossings, corners or any
wire cell in the lane band. Allowed occlusion junctions include:
  * straight runs and crossings;
  * hidden turns and U detours;
  * wires running beside a block;
  * turns just outside a block;
  * odd port counts.
Each is accepted only if strict tracing stays unique and correct.
Decorations flank crossings on one wire, and a flank hidden by a block is
simply omitted.

Default scenes are hard. On some side, at least two single-source wires
have dangling far ends there, and the source order differs from the far-end
order (an inversion). So neither 'straight across' nor 'k-th source to k-th
empty end' solves the scene. Explicit configs that cannot satisfy this
(e.g. one lone source) are accepted as broader controls. The finished scene
is rotated or reflected as a whole.

Not supported in random scenes:
  * glyphs on two perpendicular sides at once;
  * free routes with more than four turns;
  * wires running beside glyphs;
  * decorations away from crossings.
These appear only through the explicit latent arguments, as in the fixtures.
"""

import random

import common

_COLOURS = (1, 2, 3, 4, 6, 7)
_KINDS = ('S', 'X', 'D')
_PAIRS = (('X', 'D'), ('D', 'X'))
_PATTERNS = {
    'S': [(a, b) for a in range(3) for b in range(3)],
    'X': [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)],
    'D': [(0, 1), (1, 0), (1, 2), (2, 1)],
}
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_MAX_COLUMNS = 13
_MAX_BLOCKS = 4


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _sgn(v):
  return (v > 0) - (v < 0)


def _stamp(g, cy, cx, colour, kind):
  h, w = len(g), len(g[0])
  for yy in range(cy - 1, cy + 2):
    for xx in range(cx - 1, cx + 2):
      if 0 <= yy < h and 0 <= xx < w:
        g[yy][xx] = 0
  for a, b in _PATTERNS[kind]:
    yy, xx = cy - 1 + a, cx - 1 + b
    if 0 <= yy < h and 0 <= xx < w:
      g[yy][xx] = colour


def _dihedral(g, k):
  out = [row[:] for row in g]
  if k >= 4:
    out = [list(r) for r in zip(*out)]
  for _ in range(k % 4):
    out = [list(r) for r in zip(*out[::-1])]
  return out


def _expand(points):
  cells = [tuple(points[0])]
  for (y0, x0), (y1, x1) in zip(points, points[1:]):
    dy, dx = _sgn(y1 - y0), _sgn(x1 - x0)
    y, x = y0, x0
    while (y, x) != (y1, x1):
      y += dy
      x += dx
      cells.append((y, x))
  return cells


def _ends(points):
  # Glyph slot centres at the start and at the end of a wire.
  (y0, x0), (y1, x1) = points[0], points[1]
  d0 = (_sgn(y1 - y0), _sgn(x1 - x0))
  (ya, xa), (yb, xb) = points[-2], points[-1]
  d1 = (_sgn(yb - ya), _sgn(xb - xa))
  return ((y0 - 2 * d0[0], x0 - 2 * d0[1]),
          (yb + 2 * d1[0], xb + 2 * d1[1]))


def _render(scene):
  g = common.grid(scene['width'], scene['height'], 0)
  for _, _, _, pts in scene['wires']:
    for y, x in _expand(pts):
      g[y][x] = 8
  for y, x in scene['decorations']:
    g[y][x] = 5
  for r, c, bh, bw in scene['blocks']:
    for y in range(r, r + bh):
      for x in range(c, c + bw):
        g[y][x] = 9
  for colour, k0, k1, pts in scene['wires']:
    a, b = _ends(pts)
    if k0:
      _stamp(g, a[0], a[1], colour, k0)
    if k1:
      _stamp(g, b[0], b[1], colour, k1)
  return g


def _derive(scene, inp):
  # Output from the known latent connections only.
  out = [row[:] for row in inp]
  for colour, k0, k1, pts in scene['wires']:
    if k0 and k1:
      continue
    a, b = _ends(pts)
    if k0:
      kind, here, there = k0, a, b
    else:
      kind, here, there = k1, b, a
    if kind == 'S':
      _stamp(out, here[0], here[1], colour, 'D')
      _stamp(out, there[0], there[1], colour, 'X')
    elif kind == 'X':
      _stamp(out, there[0], there[1], colour, 'D')
    else:
      _stamp(out, there[0], there[1], colour, 'X')
  return out


def _port_map(g):
  h, w = len(g), len(g[0])
  owner = {}
  ports = []
  for y in range(h):
    for x in range(w):
      if g[y][x] != 9 or (y, x) in owner:
        continue
      idx = len(ports)
      owner[(y, x)] = idx
      comp = [(y, x)]
      i = 0
      while i < len(comp):
        cy, cx = comp[i]
        i += 1
        for dy, dx in _DIRS:
          ny, nx = cy + dy, cx + dx
          if (0 <= ny < h and 0 <= nx < w and g[ny][nx] == 9 and
              (ny, nx) not in owner):
            owner[(ny, nx)] = idx
            comp.append((ny, nx))
      plist = []
      for cy, cx in comp:
        for dy, dx in _DIRS:
          ny, nx = cy + dy, cx + dx
          if 0 <= ny < h and 0 <= nx < w and g[ny][nx] in (5, 8):
            plist.append((ny, nx, dy, dx))
      ports.append(plist)
  return owner, ports


def _trace(g, owner, ports, centre):
  # Strict statement of the tracing rule: returns the far glyph centre, or
  # None when any step would depend on an arbitrary order.
  h, w = len(g), len(g[0])
  cy, cx = centre

  def inb(y, x):
    return 0 <= y < h and 0 <= x < w

  def pipe(y, x):
    return inb(y, x) and g[y][x] in (5, 8, 9)

  starts = [d for d in _DIRS if inb(cy + 2 * d[0], cx + 2 * d[1]) and
            g[cy + 2 * d[0]][cx + 2 * d[1]] == 8]
  if len(starts) != 1:
    return None
  d = starts[0]
  y, x = cy + 2 * d[0], cx + 2 * d[1]
  for _ in range(4 * h * w + 16):
    ny, nx = y + d[0], x + d[1]
    if inb(ny, nx) and g[ny][nx] == 9:
      exits = [p for p in ports[owner[(ny, nx)]] if (p[0], p[1]) != (y, x)]
      straight = [p for p in exits if (p[2], p[3]) == d and
                  (p[0] - y) * d[1] == (p[1] - x) * d[0]]
      if len(straight) == 1:
        p = straight[0]
      elif not straight and len(exits) == 1:
        p = exits[0]
      else:
        return None
      y, x, d = p[0], p[1], (p[2], p[3])
      continue
    if pipe(ny, nx):
      y, x = ny, nx
      continue
    turns = [t for t in ((d[1], d[0]), (-d[1], -d[0]))
             if pipe(y + t[0], x + t[1])]
    if not turns:
      return (y + 2 * d[0], x + 2 * d[1])
    if len(turns) > 1:
      return None
    d = turns[0]
    y, x = y + d[0], x + d[1]
  return None


def _check_scene(scene):
  # Returns None for a valid scene, else a description of the problem.
  h, w = scene['height'], scene['width']
  wires = scene['wires']
  if not wires:
    return 'a scene needs at least one wire'
  colours = [wr[0] for wr in wires]
  if len(set(colours)) != len(colours):
    return 'wire colours must be distinct'
  if all(wr[1] and wr[2] for wr in wires):
    return 'at least one wire must carry an unresolved source'
  occ = {}
  ends = set()
  centres = []
  for colour, k0, k1, pts in wires:
    if colour not in _COLOURS:
      return 'marker colours must come from 1,2,3,4,6,7'
    if not k0 and not k1:
      return 'every wire needs at least one marker'
    if k0 and k1 and (k0, k1) not in _PAIRS:
      return 'a connected wire must be an X/diamond pair'
    if len(pts) < 2:
      return 'a wire needs at least two points'
    dirs = []
    for p, q in zip(pts, pts[1:]):
      if p == q or (p[0] != q[0] and p[1] != q[1]):
        return 'wire segments must be non-empty and axis-aligned'
      dirs.append((_sgn(q[0] - p[0]), _sgn(q[1] - p[1])))
    for d1, d2 in zip(dirs, dirs[1:]):
      if d1[0] * d2[0] + d1[1] * d2[1] != 0:
        return 'consecutive wire segments must be perpendicular'
    cells = _expand(pts)
    inner = set(pts[1:-1])
    for j, c in enumerate(cells):
      if not (0 <= c[0] < h and 0 <= c[1] < w):
        return 'wire cell outside the grid'
      if j == 0 or j == len(cells) - 1 or c in inner:
        axis = None
      elif cells[j - 1][0] == cells[j + 1][0]:
        axis = 'h'
      else:
        axis = 'v'
      occ.setdefault(c, []).append(axis)
    ends.add(cells[0])
    ends.add(cells[-1])
    centres.extend(_ends(pts))
  for lst in occ.values():
    if len(lst) == 1:
      continue
    if len(lst) == 2 and None not in lst and lst[0] != lst[1]:
      continue
    return 'wires may only meet at clean perpendicular crossings'
  slot_cells = set()
  for i, (cy, cx) in enumerate(centres):
    for y in range(cy - 1, cy + 2):
      for x in range(cx - 1, cx + 2):
        if not (0 <= y < h and 0 <= x < w):
          return 'glyph slot outside the grid'
        if (y, x) in occ:
          return 'glyph slot overlaps a wire'
        slot_cells.add((y, x))
    for oy, ox in centres[:i]:
      if max(abs(oy - cy), abs(ox - cx)) < 4:
        return 'glyph slots must be separated by a blank cell'
  block_cells = set()
  rects = scene['blocks']
  for i, (r, c, bh, bw) in enumerate(rects):
    if bh < 1 or bw < 1 or r < 0 or c < 0 or r + bh > h or c + bw > w:
      return 'block outside the grid'
    for r2, c2, bh2, bw2 in rects[:i]:
      if r <= r2 + bh2 and r2 <= r + bh and c <= c2 + bw2 and c2 <= c + bw:
        return 'blocks must not touch'
    cells = set((y, x) for y in range(r, r + bh) for x in range(c, c + bw))
    if not any(cell in occ for cell in cells):
      return 'each block must hide some wiring'
    block_cells |= cells
  if block_cells & ends:
    return 'blocks may not hide wire ends'
  if block_cells & slot_cells:
    return 'blocks may not overlap glyph slots'
  seen = set()
  for dcell in scene['decorations']:
    if (dcell in seen or dcell not in occ or len(occ[dcell]) != 1 or
        occ[dcell][0] is None or dcell in block_cells):
      return 'decorations must sit on plain visible wire cells'
    seen.add(dcell)
  g = _render(scene)
  owner, ports = _port_map(g)
  for colour, k0, k1, pts in wires:
    a, b = _ends(pts)
    if k0 and _trace(g, owner, ports, a) != b:
      return 'wire of colour %d does not trace uniquely to its end' % colour
    if k1 and _trace(g, owner, ports, b) != a:
      return 'wire of colour %d does not trace uniquely to its end' % colour
  return None


def _layout_columns(types):
  # Column labels: S = top glyph slot, T = bottom glyph slot, B = both
  # (straight wire), M = private middle column of a jog wire. All columns
  # share a parity and are at least 2 apart; slots in one row are at least
  # 4 apart, so glyphs never touch.
  nzj = sum(1 for t in types if t != 'B')
  extras = ['B' if t == 'B' else 'M' for t in types if t != 'Z']
  for _ in range(100):
    first = random.choice('ST')
    other = 'T' if first == 'S' else 'S'
    labels = [first if i % 2 == 0 else other for i in range(2 * nzj)]
    for lab in extras:
      labels.insert(random.randint(0, len(labels)), lab)
    for _swap in range(random.randint(0, len(labels) // 2)):
      i = random.randrange(len(labels) - 1)
      labels[i], labels[i + 1] = labels[i + 1], labels[i]
    columns = {'S': [], 'T': [], 'B': [], 'M': []}
    prev, last_top, last_bot = None, None, None
    start = random.randint(1, 3)
    for lab in labels:
      x = start if prev is None else prev + 2
      if lab in 'SB' and last_top is not None:
        x = max(x, last_top + 4)
      if lab in 'TB' and last_bot is not None:
        x = max(x, last_bot + 4)
      if random.random() < 0.15:
        x += 2
      columns[lab].append(x)
      prev = x
      if lab in 'SB':
        last_top = x
      if lab in 'TB':
        last_bot = x
    base = prev + 2
    if base <= 30:
      return columns, base + random.randint(0, min(5, 30 - base))
  return None


def _single_groups(cfg):
  groups = ([], [])
  for k, (a, b) in enumerate(cfg):
    if a and not b:
      groups[0].append(k)
    elif b and not a:
      groups[1].append(k)
  return groups


def _can_be_hard(cfg):
  return any(len(grp) >= 2 for grp in _single_groups(cfg))


def _is_hard(src, tgt, cfg):
  # Some side has >= 2 dangling far ends whose sources are out of order.
  for grp in _single_groups(cfg):
    for i in grp:
      for j in grp:
        if i < j and (src[i] - src[j]) * (tgt[i] - tgt[j]) < 0:
          return True
  return False


def _single_source():
  kind = random.choice('SSSXD')
  return (kind, None) if random.random() < 0.75 else (None, kind)


def _pick_config():
  if random.random() < 0.12:
    return random.choice(list(_PAIRS))
  return _single_source()


def _sample_configs(src, tgt):
  n = len(src)
  inv = [(i, j) for i in range(n) for j in range(i + 1, n)
         if (src[i] - src[j]) * (tgt[i] - tgt[j]) < 0]
  if not inv:
    return None
  cfg = [_pick_config() for _ in range(n)]
  top = random.random() < 0.7
  for k in random.choice(inv):
    kind = random.choice('SSSXD')
    cfg[k] = (kind, None) if top else (None, kind)
  return cfg


def _feasible(n, ns, nj, min_n):
  return (2 <= n <= 6 and n >= min_n and 0 <= ns <= n - 1 and
          0 <= nj <= 3 and ns + nj <= n and
          2 * n - ns + nj <= _MAX_COLUMNS)


def _sample_counts(n, ns, nj, min_n):
  for _ in range(100):
    nn = n if n is not None else random.choice([2, 3, 3, 4, 4, 5, 5, 6])
    s = ns if ns is not None else random.choice([0, 0, 0, 1, 1, 2])
    j = nj if nj is not None else random.choice([0, 0, 1, 1, 2])
    if _feasible(nn, s, j, min_n):
      return nn, s, j
  return None


def _rect_ok(rect, blocks, lo, hi, width):
  r0, c0, bh, bw = rect
  if r0 < lo or r0 + bh - 1 > hi or c0 < 0 or c0 + bw > width:
    return False
  for r2, c2, bh2, bw2 in blocks:
    if (r0 <= r2 + bh2 + 1 and r2 <= r0 + bh + 1 and
        c0 <= c2 + bw2 + 1 and c2 <= c0 + bw + 1):
      return False
  return True


def _check_args(num_pipes, colours, configs, num_straight, num_jogs,
                num_blocks, decorate_prob):
  for name, v in (('num_pipes', num_pipes), ('num_straight', num_straight),
                  ('num_jogs', num_jogs), ('num_blocks', num_blocks)):
    if v is not None and not _is_int(v):
      raise ValueError(name + ' must be an integer (not bool or float)')
  if decorate_prob is not None:
    if (isinstance(decorate_prob, bool) or
        not isinstance(decorate_prob, (int, float))):
      raise ValueError('decorate_prob must be a number in [0, 1]')
    if not 0.0 <= decorate_prob <= 1.0:
      raise ValueError('decorate_prob must be in [0, 1]')
  n = num_pipes
  if n is not None and not 2 <= n <= 6:
    raise ValueError('num_pipes must be in 2..6')
  cols = None
  if colours is not None:
    if not isinstance(colours, (list, tuple)):
      raise ValueError('colours must be a list or tuple')
    cols = list(colours)
    if any(not _is_int(c) for c in cols):
      raise ValueError('colours must be integers')
    if len(set(cols)) != len(cols) or any(c not in _COLOURS for c in cols):
      raise ValueError('colours must be distinct values from 1,2,3,4,6,7')
    if n is None:
      n = len(cols)
    if not 2 <= len(cols) <= 6 or len(cols) != n:
      raise ValueError('colours must give one colour per wire (2..6)')
  cfg = None
  if configs is not None:
    if not isinstance(configs, (list, tuple)):
      raise ValueError('configs must be a list or tuple')
    cfg = []
    for item in configs:
      if not isinstance(item, (list, tuple)) or len(item) != 2:
        raise ValueError('each config must be a list/tuple '
                         '(top_kind, bottom_kind)')
      a, b = item
      for kind in (a, b):
        if kind is not None and not (isinstance(kind, str) and
                                     kind in _KINDS):
          raise ValueError('wire kinds must be S, X, D or None')
      if a is None and b is None:
        raise ValueError('every wire needs at least one marker')
      if a is not None and b is not None and (a, b) not in _PAIRS:
        raise ValueError('a connected wire must be an X/diamond pair')
      cfg.append((a, b))
    if n is None:
      n = len(cfg)
    if not 2 <= len(cfg) <= 6 or len(cfg) != n:
      raise ValueError('configs must give one entry per wire (2..6)')
    if all(a is not None and b is not None for a, b in cfg):
      raise ValueError('at least one wire must carry an unresolved source')
  if num_straight is not None and not 0 <= num_straight <= 5:
    raise ValueError('num_straight must be in 0..5')
  if num_jogs is not None and not 0 <= num_jogs <= 3:
    raise ValueError('num_jogs must be in 0..3')
  if num_blocks is not None and not 0 <= num_blocks <= _MAX_BLOCKS:
    raise ValueError('num_blocks must be in 0..4')
  min_n = num_blocks if num_blocks is not None else 0
  ok = False
  for nn in range(2, 7):
    for s in range(0, 6):
      for j in range(0, 4):
        if n is not None and nn != n:
          continue
        if num_straight is not None and s != num_straight:
          continue
        if num_jogs is not None and j != num_jogs:
          continue
        if _feasible(nn, s, j, min_n):
          ok = True
  if not ok:
    raise ValueError('incompatible wire count, num_straight, num_jogs and '
                     'num_blocks (need num_straight < wires, num_straight + '
                     'num_jogs <= wires, 2*wires - num_straight + num_jogs '
                     '<= 13, num_blocks <= wires)')
  return n, cols, cfg, min_n


def _build(n0, ns0, nj0, min_n, cols, cfg, num_blocks, decorate_prob):
  counts = _sample_counts(n0, ns0, nj0, min_n)
  if counts is None:
    return None
  n, ns, nj = counts
  types = ['B'] * ns + ['J'] * nj + ['Z'] * (n - ns - nj)
  random.shuffle(types)
  layout = _layout_columns(types)
  if layout is None:
    return None
  columns, width = layout
  pools = dict((lab, random.sample(v, len(v))) for lab, v in columns.items())
  src, tgt, mid = [None] * n, [None] * n, [None] * n
  for k, t in enumerate(types):
    if t == 'B':
      src[k] = tgt[k] = pools['B'].pop()
    else:
      src[k] = pools['S'].pop()
      tgt[k] = pools['T'].pop()
      if t == 'J':
        mid[k] = pools['M'].pop()
  if cfg is None:
    cfgs = _sample_configs(src, tgt)
    if cfgs is None:
      return None
  else:
    cfgs = cfg
    if _can_be_hard(cfgs) and not _is_hard(src, tgt, cfgs):
      return None

  nl = sum(1 if t == 'Z' else (2 if t == 'J' else 0) for t in types)
  rt = random.randint(1, 3)
  extra = random.randint(0, 4)
  if num_blocks:
    extra += num_blocks + 1
  rb = rt + 6 + 2 * (nl - 1) + extra
  if rb + 2 > 30:
    return None
  height = rb + 2 + random.randint(0, min(5, 30 - rb - 2))
  lo, hi = rt + 3, rb - 3
  m = hi - lo + 1
  vals = sorted(random.sample(range(m - nl + 1), nl))
  lanes = [lo + v + i for i, v in enumerate(vals)]
  random.shuffle(lanes)
  colours = cols if cols is not None else random.sample(_COLOURS, n)
  wires = []
  for k, t in enumerate(types):
    top, bot = (rt + 2, src[k]), (rb - 2, tgt[k])
    if t == 'B':
      pts = [top, bot]
    elif t == 'Z':
      lane = lanes.pop()
      pts = [top, (lane, src[k]), (lane, tgt[k]), bot]
    else:
      l1, l2 = sorted([lanes.pop(), lanes.pop()])
      pts = [top, (l1, src[k]), (l1, mid[k]), (l2, mid[k]), (l2, tgt[k]),
             bot]
    wires.append((colours[k], cfgs[k][0], cfgs[k][1], pts))
  scene = {'width': width, 'height': height, 'wires': wires, 'blocks': [],
           'decorations': []}
  if _check_scene(scene) is not None:
    return None

  occ = {}
  corners = set()
  endcells = set()
  for wr in wires:
    cells = _expand(wr[3])
    endcells.add(cells[0])
    endcells.add(cells[-1])
    corners.update(wr[3][1:-1])
    for c in cells:
      occ[c] = occ.get(c, 0) + 1
  crossings = sorted(c for c, v in occ.items() if v > 1)
  if not crossings:
    return None
  band = sorted(c for c in occ if lo <= c[0] <= hi)
  corner_list = sorted(corners)

  strict = num_blocks is not None
  nb = num_blocks if strict else min(n, random.choice([0, 1, 1, 2, 2, 3, 4]))
  blocks = []
  for _ in range(nb):
    placed = False
    for _try in range(60):
      roll = random.random()
      if roll < 0.4:
        anchor = random.choice(crossings)
      elif roll < 0.65:
        anchor = random.choice(corner_list)
      else:
        anchor = random.choice(band)
      bh = random.randint(2, 4)
      bw = random.randint(2, 5)
      rect = (anchor[0] - random.randint(0, bh - 1),
              anchor[1] - random.randint(0, bw - 1), bh, bw)
      if not _rect_ok(rect, blocks, lo, hi, width):
        continue
      trial = dict(scene)
      trial['blocks'] = blocks + [rect]
      if _check_scene(trial) is None:
        blocks.append(rect)
        placed = True
        break
    if strict and not placed:
      return None
  scene['blocks'] = blocks

  q = decorate_prob if decorate_prob is not None else random.uniform(0.3,
                                                                     0.9)
  hidden = set((y, x) for r0, c0, bh, bw in blocks
               for y in range(r0, r0 + bh) for x in range(c0, c0 + bw))

  def plain(c):
    return (occ.get(c) == 1 and c not in corners and c not in endcells and
            c not in hidden)

  decos = []
  for y, x in crossings:
    if random.random() >= q:
      continue
    if random.random() < 0.5:
      flanks = [(y, x - 1), (y, x + 1)]
    else:
      flanks = [(y - 1, x), (y + 1, x)]
    if any(not plain(f) and f not in hidden for f in flanks):
      continue
    for f in flanks:
      if plain(f) and f not in decos:
        decos.append(f)
  scene['decorations'] = decos
  if _check_scene(scene) is not None:
    return None
  inp = _render(scene)
  return inp, _derive(scene, inp)


def _pair(v, name):
  if (not isinstance(v, (list, tuple)) or len(v) != 2 or
      not all(_is_int(t) for t in v)):
    raise ValueError(name + ' must be a (row, col) pair of integers')
  return (v[0], v[1])


def _parse_scene(width, height, wires, blocks, decorations):
  for name, v in (('width', width), ('height', height)):
    if not _is_int(v) or not 1 <= v <= 30:
      raise ValueError(name + ' must be an integer in 1..30')
  if not isinstance(wires, (list, tuple)) or not wires:
    raise ValueError('wires must be a non-empty list')
  parsed = []
  for item in wires:
    if not isinstance(item, (list, tuple)) or len(item) != 4:
      raise ValueError('each wire must be (colour, start_kind, end_kind, '
                       'points)')
    colour, k0, k1, pts = item
    if not _is_int(colour):
      raise ValueError('wire colour must be an integer')
    for kind in (k0, k1):
      if kind is not None and not (isinstance(kind, str) and kind in _KINDS):
        raise ValueError('wire kinds must be S, X, D or None')
    if not isinstance(pts, (list, tuple)) or len(pts) < 2:
      raise ValueError('wire points must be a list of >= 2 pairs')
    parsed.append((colour, k0, k1, [_pair(p, 'wire point') for p in pts]))
  rects = []
  if blocks is not None:
    if not isinstance(blocks, (list, tuple)):
      raise ValueError('blocks must be a list')
    for b in blocks:
      if (not isinstance(b, (list, tuple)) or len(b) != 4 or
          not all(_is_int(t) for t in b)):
        raise ValueError('each block must be (row, col, height, width)')
      rects.append(tuple(b))
  decos = []
  if decorations is not None:
    if not isinstance(decorations, (list, tuple)):
      raise ValueError('decorations must be a list')
    decos = [_pair(dc, 'decoration') for dc in decorations]
  scene = {'width': width, 'height': height, 'wires': parsed,
           'blocks': rects, 'decorations': decos}
  err = _check_scene(scene)
  if err is not None:
    raise ValueError(err)
  return scene


def generate(num_pipes=None, colours=None, configs=None, num_straight=None,
             num_jogs=None, num_blocks=None, decorate_prob=None,
             orientation=None, width=None, height=None, wires=None,
             blocks=None, decorations=None):
  """Returns an input/output pair for task a47bf94d.

  Random-scene arguments (used when wires is None):
    num_pipes: number of wires (int 2..6). If omitted, it is inferred from
      colours or configs, or sampled.
    colours: optional list/tuple of distinct marker colours from
      1,2,3,4,6,7, one per wire.
    configs: optional list/tuple of (top_kind, bottom_kind) pairs, before
      orientation. Each kind is 'S', 'X', 'D' or None, and at least one of
      the two must be set. Both set means an (X, D) or (D, X) distractor. At
      least one wire must be single-source. If some side has two or more
      sources, the inversion (hard) criterion is enforced; otherwise the
      scene is a broader control.
    num_straight: number of straight wires (int 0..5, fewer than wires).
    num_jogs: number of four-turn jog wires (int 0..3). Constraint:
      2*wires - num_straight + num_jogs <= 13.
    num_blocks: exact number of 9 blocks (int 0..4, <= wires). If omitted,
      0..min(4, wires) is sampled best-effort.
    decorate_prob: probability in [0, 1] that a crossing gets 5 flanks.
    orientation: dihedral index 0..7. Random if omitted in random mode;
      identity if omitted in explicit mode.

  Explicit latent scene arguments (fixture reconstruction):
    width, height: grid size (1..30).
    wires: list of (colour, start_kind, end_kind, points). points are
      (row, col) corners of an axis-aligned route. The glyph slot of each
      end lies two cells beyond the end, along the end segment.
    blocks: list of (row, col, height, width) rectangles of colour 9.
    decorations: list of visible (row, col) cells of colour 5.
  The output is derived from the wire connections. The scene must pass the
  strict-tracing consistency check, or ValueError is raised.
  """
  if orientation is not None and (not _is_int(orientation) or
                                  not 0 <= orientation <= 7):
    raise ValueError('orientation must be an integer 0..7')
  if wires is not None:
    if any(v is not None for v in (num_pipes, colours, configs, num_straight,
                                   num_jogs, num_blocks, decorate_prob)):
      raise ValueError('explicit wires cannot be combined with random-scene '
                       'parameters')
    scene = _parse_scene(width, height, wires, blocks, decorations)
    inp = _render(scene)
    out = _derive(scene, inp)
    k = orientation if orientation is not None else 0
    return {'input': _dihedral(inp, k), 'output': _dihedral(out, k)}
  if any(v is not None for v in (width, height, blocks, decorations)):
    raise ValueError('width, height, blocks and decorations describe an '
                     'explicit scene and require wires')
  n, cols, cfg, min_n = _check_args(num_pipes, colours, configs,
                                    num_straight, num_jogs, num_blocks,
                                    decorate_prob)
  for _ in range(400):
    built = _build(n, num_straight, num_jogs, min_n, cols, cfg, num_blocks,
                   decorate_prob)
    if built is not None:
      inp, out = built
      k = orientation if orientation is not None else random.randint(0, 7)
      return {'input': _dihedral(inp, k), 'output': _dihedral(out, k)}
  raise RuntimeError('could not construct a scene with the requested '
                     'parameters')


_TRAIN_SCENES = [
    dict(width=22, height=22,
         wires=[(3, 'S', None, [(3, 5), (3, 10), (11, 10), (11, 14)]),
                (2, 'S', None, [(11, 5), (11, 7), (5, 7), (5, 13), (3, 13),
                                (3, 14)]),
                (4, 'D', 'X', [(7, 5), (7, 14)]),
                (6, 'X', None, [(15, 14), (15, 5)])],
         blocks=[(5, 9, 5, 4)],
         decorations=[(7, 6), (7, 8)]),
    dict(width=22, height=19,
         wires=[(1, 'S', None, [(4, 4), (7, 4), (7, 12), (13, 12)]),
                (2, 'S', None, [(4, 8), (13, 8)]),
                (3, 'S', None, [(4, 12), (5, 12), (5, 18), (12, 18),
                                (12, 16), (13, 16)]),
                (4, 'S', None, [(4, 16), (10, 16), (10, 4), (13, 4)])],
         blocks=[],
         decorations=[(5, 15), (5, 17), (6, 8), (8, 8), (10, 7), (10, 9),
                      (10, 11), (10, 13)]),
    dict(width=22, height=22,
         wires=[(2, 'S', None, [(4, 3), (8, 3), (8, 7), (13, 7)]),
                (1, None, 'X', [(4, 7), (6, 7), (6, 13), (12, 13), (12, 11),
                                (13, 11)]),
                (4, 'S', None, [(4, 11), (10, 11), (10, 3), (13, 3)]),
                (6, 'S', None, [(4, 15), (13, 15)])],
         blocks=[(5, 2, 2, 3), (8, 10, 2, 2), (7, 14, 3, 4)],
         decorations=[(6, 10), (6, 12), (10, 6), (10, 8)]),
]

_TEST_SCENES = [
    dict(width=26, height=26,
         wires=[(1, 'S', None, [(4, 2), (9, 2), (9, 12), (19, 12)]),
                (2, 'S', None, [(4, 12), (5, 12), (5, 15), (14, 15),
                                (14, 17), (19, 17)]),
                (3, 'S', None, [(4, 17), (12, 17), (12, 7), (19, 7)]),
                (6, 'S', None, [(4, 22), (5, 22), (5, 20), (16, 20),
                                (16, 2), (19, 2)]),
                (4, 'X', None, [(19, 22), (7, 22), (7, 7), (4, 7)])],
         blocks=[(6, 9, 5, 2), (11, 19, 3, 5), (15, 1, 3, 4),
                 (15, 12, 2, 2)],
         decorations=[(6, 15), (8, 15), (6, 17), (8, 17), (6, 20), (8, 20),
                      (11, 15), (13, 15), (12, 11), (12, 13), (15, 17),
                      (17, 17), (16, 6), (16, 8), (16, 11)]),
]


def validate():
  """Rebuilds the original fixtures from explicit latent scene descriptions."""
  train = [generate(**spec) for spec in _TRAIN_SCENES]
  test = [generate(**spec) for spec in _TEST_SCENES]
  return {'train': train, 'test': test}
