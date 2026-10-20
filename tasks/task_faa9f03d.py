"""Generator for ARC task faa9f03d: repair damaged paths and obey 4-markers.

Rule: a black grid holds axis-aligned coloured paths. Each path is one cell
wide and a single colour. The input shows the paths damaged in three ways:
  * some corners and path ends are drawn as 2;
  * a straight run may be missing single cells;
  * a crossing cell may show the wrong colour, or be blank.
A 4 sits on the cell just past a corner K, in line with the limb that
leaves K. The output does four things:
  * redraws every path solid, so each 2 takes its path's colour and each
    one-cell gap is filled;
  * deletes the marked limb and everything beyond it;
  * redirects the path from K straight through the 4 to the grid edge;
  * paints the paths in one global layer order, so every crossing shows the
    upper path. A redirected ray always lies above the paths it crosses.

The layer order must be readable from the input. Each output crossing is
shown in one of four ways:
  (a) the lower path's colour (the usual, reversed cue);
  (b) blank, where the marker-axis tie rule picks the true upper path;
  (c) blank and undecided, when another crossing of the same colour pair
      still carries a cue;
  (d) the upper path's colour. This happens only when a type (b) blank
      crossing already fixes that pair. That blank overrides the visible
      cue, as at cell (2,1) of demonstration 4.
Crossings on deleted limbs may show either colour or be blank.
For pairs that never cross, the layer order does not affect the output.

Scope:
  * Paths: 2-5 paths of distinct colours from {1,3,5,6,7,8,9}, or from an
    optional palette subset. Colours 5, 8 and 9 are a synthetic palette
    extension; the demonstrations use only 1, 3, 6 and 7.
  * Size: default grids are 10..20 cells per side; 6..30 is accepted.
    Every size other than 12x12 is a synthetic extension. When num_paths
    is 4 or 5 and the size is not given, the sampled size starts at 12 or
    14 so that the requested count fits.
  * Construction: paths are placed one at a time. Each new polyline is
    retried against the paths already placed, so crowded scenes (five
    paths) do not depend on all paths being valid together by chance.
  * Failure: very small explicit sizes, or hard count requests on small
    grids (for example 6x6 with five paths), can raise RuntimeError after
    bounded retries. There is no fixed fallback scene.
  * Shape: each path is a polyline with 1-7 segments. Inner segments have
    4 or more cells. A final segment may be a short 2-3 cell hook.
  * Markers: 0-2 per scene. Two markers may sit on the same path, one at
    each end.
  * Gaps: a one-cell gap is never placed next to a crossing whose
    perpendicular neighbours are both 2, because that gap would not be
    bridged.
  * Distribution narrowing: random mode keeps differently coloured strands
    from touching except at crossings. It also keeps same-colour runs, and
    any 2, at least 3 cells apart along a line.

Fixture replay: fixtures are rebuilt from explicit latent paths, layer
order, markers and input-damage overrides. Explicit mode is a latent
renderer for replay. It checks structure (types, bounds, axis alignment, no
self-overlap, marker placement). It does not check the random-mode
cue-consistency constraints, because the demonstrations themselves contain
touching strands.
"""

# Copyright 2026 Ritwika Kancharla
# Licensed under the Apache License, Version 2.0.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

import random

import common

PALETTE = (1, 3, 5, 6, 7, 8, 9)
CORNER = 2
MARK = 4
DIRS = ((0, 1), (0, -1), (1, 0), (-1, 0))
MIN_SIDE, MAX_SIDE = 6, 30
# Probabilities for the harder crossing displays when a marker makes them
# legal. Type (b): blank decided by marker axis. Type (d): upper colour
# shown on a pair that a type (b) blank already fixes.
P_AXIS_BLANK = 0.6
P_LOOSE_BLANK = 0.25
P_UPPER_SHOWN = 0.5
# Bounded retry budgets.
SIZE_DRAWS = 8
SCENE_TRIES = 120
PATH_TRIES = 40


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _is_seq(v):
  return isinstance(v, (list, tuple))


def _check_int(name, v, lo, hi):
  if v is None:
    return
  if not _is_int(v):
    raise ValueError('%s must be an integer' % name)
  if not lo <= v <= hi:
    raise ValueError('%s must be in %d..%d' % (name, lo, hi))


def _sign(v):
  return (v > 0) - (v < 0)


def _segments(verts):
  """Returns [(axis, cells)] for each consecutive vertex pair."""
  segs = []
  for a, b in zip(verts, verts[1:]):
    dr, dc = _sign(b[0] - a[0]), _sign(b[1] - a[1])
    n = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
    cells = [(a[0] + dr * t, a[1] + dc * t) for t in range(n + 1)]
    segs.append(('v' if dr else 'h', cells))
  return segs


def _cells(verts):
  out = [tuple(verts[0])]
  for _, seg in _segments(verts):
    out.extend(seg[1:])
  return out


def _edge_ray(height, width, start, d):
  ray = []
  r, c = start[0] + d[0], start[1] + d[1]
  while 0 <= r < height and 0 <= c < width:
    ray.append((r, c))
    r, c = r + d[0], c + d[1]
  return ray


def _marker_geometry(verts, side, k):
  """Returns corner K and the redirect direction, away from the limb."""
  K = tuple(verts[k])
  nb = verts[k + 1] if side == 'end' else verts[k - 1]
  return K, (_sign(K[0] - nb[0]), _sign(K[1] - nb[1]))


def _final_verts(height, width, verts, marks):
  lo, hi = 0, len(verts) - 1
  for side, k in marks:
    if side == 'start':
      lo = k
    else:
      hi = k
  out = list(verts[lo:hi + 1])
  for side, k in marks:
    K, d = _marker_geometry(verts, side, k)
    tip = _edge_ray(height, width, K, d)[-1]
    if side == 'start':
      out.insert(0, tip)
    else:
      out.append(tip)
  return out


def _render(height, width, paths, order, markers, overrides):
  rank = {c: i for i, c in enumerate(order)}
  layered = sorted(range(len(paths)), key=lambda i: rank[paths[i][0]])
  grid_in = common.grid(width, height, 0)
  grid_out = common.grid(width, height, 0)
  if len(grid_in) != height or any(len(row) != width for row in grid_in):
    raise RuntimeError('common.grid returned an unexpected shape')
  marks = {}
  for i, side, k in markers:
    marks.setdefault(i, []).append((side, k))
  for i in layered:
    colour, verts = paths[i]
    for r, c in _cells(verts):
      grid_in[r][c] = colour
    final = _final_verts(height, width, verts, marks.get(i, []))
    for r, c in _cells(final):
      grid_out[r][c] = colour
  for i, side, k in markers:
    K, d = _marker_geometry(paths[i][1], side, k)
    grid_in[K[0] + d[0]][K[1] + d[1]] = MARK
  for r, c, v in overrides:
    grid_in[r][c] = v
  return {'input': grid_in, 'output': grid_out}


def _geometry(polys):
  """Maps cell -> [(path, axis or None for vertices)], or None if invalid."""
  info = {}
  for i, verts in enumerate(polys):
    cells = _cells(verts)
    if len(set(cells)) != len(cells):
      return None
    axis = {}
    for ax, seg in _segments(verts):
      if len(seg) < 2:
        return None
      for cell in seg[1:-1]:
        axis[cell] = ax
    for cell in cells:
      info.setdefault(cell, []).append((i, axis.get(cell)))
  for lst in info.values():
    if len(lst) > 2:
      return None
    if len(lst) == 2:
      if lst[0][1] is None or lst[1][1] is None or lst[0][1] == lst[1][1]:
        return None
  for (r, c), lst in info.items():
    own = {i for i, _ in lst}
    for dr, dc in DIRS:
      nb = info.get((r + dr, c + dc))
      if nb:
        other = {i for i, _ in nb}
        if (own - other) and (other - own):
          return None
  return info


def _spacing_ok(polys, twos):
  """Keeps distinct runs of one colour at least 3 cells apart.

  A 2 counts as a cell of every colour.
  """
  for verts in polys:
    pool = set(_cells(verts)) | set(twos)
    for axis in ('h', 'v'):
      lines, covered = {}, set()
      for ax, seg in _segments(verts):
        if ax != axis:
          continue
        key = seg[0][0] if axis == 'h' else seg[0][1]
        pos = [p[1] if axis == 'h' else p[0] for p in seg]
        lines.setdefault(key, []).append((min(pos), max(pos)))
        covered.update(seg)
      for cell in pool - covered:
        key, pos = (cell[0], cell[1]) if axis == 'h' else (cell[1], cell[0])
        lines.setdefault(key, []).append((pos, pos))
      for pieces in lines.values():
        pieces.sort()
        for a, b in zip(pieces, pieces[1:]):
          if b[0] - a[1] < 3:
            return False
  return True


def _holes_ok(grid_in, polys, colours):
  """Each run's holes are single and interior, and 2+ true cells remain."""
  for verts, col in zip(polys, colours):
    for _, seg in _segments(verts):
      vis, prev, last = 0, False, len(seg) - 1
      for idx, (r, c) in enumerate(seg):
        v = grid_in[r][c]
        hole = v not in (col, CORNER)
        if hole and (idx == 0 or idx == last or prev):
          return False
        vis += v == col
        prev = hole
      if vis < 2:
        return False
  return True


def _bridges_ok(grid_in, polys, colours):
  """Rejects one-cell holes that a line scan would refuse to bridge.

  A hole is not bridged when a run cell beside it shows the path colour and
  has path-colour-or-2 cells on both perpendicular sides. That cell looks
  like the middle of a crossing line.
  """
  height, width = len(grid_in), len(grid_in[0])

  def on(r, c, col):
    return (0 <= r < height and 0 <= c < width and
            grid_in[r][c] in (col, CORNER))

  for verts, col in zip(polys, colours):
    for ax, seg in _segments(verts):
      for idx in range(1, len(seg) - 1):
        r, c = seg[idx]
        if grid_in[r][c] in (col, CORNER):
          continue
        for nr, nc in (seg[idx - 1], seg[idx + 1]):
          if grid_in[nr][nc] != col:
            continue
          if ax == 'h':
            blocked = on(nr - 1, nc, col) and on(nr + 1, nc, col)
          else:
            blocked = on(nr, nc - 1, col) and on(nr, nc + 1, col)
          if blocked:
            return False
  return True


def _input_ok(grid_in, polys, colours):
  return (_holes_ok(grid_in, polys, colours) and
          _bridges_ok(grid_in, polys, colours))


def _blank_top(a, axis_a, b, axis_b, ext):
  """Upper strand implied at a blank crossing, or None if undecided."""
  pref = set()
  for col, ax in ((a, axis_a), (b, axis_b)):
    if ax in ext.get(col, ()):
      pref.add(ax)
  if not pref:
    for axes in ext.values():
      pref |= axes
  in_a, in_b = axis_a in pref, axis_b in pref
  if in_a and not in_b:
    return a
  if in_b and not in_a:
    return b
  return None


def _room(height, width, p, d):
  if d == (0, 1):
    return width - 1 - p[1]
  if d == (0, -1):
    return p[1]
  if d == (1, 0):
    return height - 1 - p[0]
  return p[0]


def _random_polyline(height, width, crowded=False):
  """Draws one axis-aligned polyline.

  Args:
    height: grid height.
    width: grid width.
    crowded: when True (4-5 paths), fewer segments are drawn so that the
      paths fit together without touching.
  """
  if random.random() < 0.8:
    side = random.randrange(4)
    if side == 0:
      p, d = (0, random.randrange(1, width - 1)), (1, 0)
    elif side == 1:
      p, d = (height - 1, random.randrange(1, width - 1)), (-1, 0)
    elif side == 2:
      p, d = (random.randrange(1, height - 1), 0), (0, 1)
    else:
      p, d = (random.randrange(1, height - 1), width - 1), (0, -1)
  else:
    p = (random.randrange(1, height - 1), random.randrange(1, width - 1))
    d = random.choice(DIRS)
  if crowded:
    if min(height, width) >= 18 and random.random() < 0.1:
      nseg = 5
    else:
      nseg = random.choice((1, 2, 2, 3, 3, 4))
  elif min(height, width) >= 14 and random.random() < 0.2:
    nseg = random.randint(5, 7)
  else:
    nseg = random.choice((1, 2, 2, 3, 3, 3, 4, 4, 5))
  verts = [p]
  for s in range(nseg):
    room = _room(height, width, p, d)
    last = s == nseg - 1
    if last and s >= 1 and room >= 1 and random.random() < 0.15:
      # A short end hook of 2-3 cells, as in demonstrations 1 and 3.
      step = random.randint(1, min(2, room))
    else:
      top = room if last else room - 1
      if top < 3:
        break
      if last and random.random() < 0.5:
        step = room
      else:
        step = random.randint(3, top)
    p = (p[0] + d[0] * step, p[1] + d[1] * step)
    verts.append(p)
    turns = [(d[1], d[0]), (-d[1], -d[0])]
    good = [t for t in turns if _room(height, width, p, t) >= 4]
    d = random.choice(good or turns)
  return verts if len(verts) >= 2 else None


def _place_paths(height, width, n):
  """Places n polylines one by one, each checked against those placed."""
  crowded = n >= 4
  polys = []
  for _ in range(n):
    placed = False
    for _ in range(PATH_TRIES):
      poly = _random_polyline(height, width, crowded)
      if not poly or not _spacing_ok([poly], set()):
        continue
      if _geometry(polys + [poly]) is None:
        continue
      polys.append(poly)
      placed = True
      break
    if not placed:
      return None
  return polys


def _pick_marker(polys, markers):
  i = random.randrange(len(polys))
  verts = polys[i]
  if len(verts) < 3:
    return None
  side = random.choice(('start', 'end'))
  k = random.randint(1, len(verts) - 2)
  for j, s, kk in markers:
    if j == i:
      if s == side:
        return None
      if side == 'end' and k <= kk:
        return None
      if side == 'start' and k >= kk:
        return None
  return (i, side, k)


def _check_markers(height, width, polys, colours, qinfo, markers):
  geo = []
  for i, side, k in markers:
    K, d = _marker_geometry(polys[i], side, k)
    ray = _edge_ray(height, width, K, d)
    if not ray:
      return None
    geo.append((i, K, d, ray))
  marks = {}
  for i, side, k in markers:
    marks.setdefault(i, []).append((side, k))
  finals = [_final_verts(height, width, polys[i], marks.get(i, []))
            for i in range(len(polys))]
  fsets = [set(_cells(v)) for v in finals]
  above = set()
  for idx, (i, K, d, ray) in enumerate(geo):
    own = set(_cells(polys[i]))
    rax = 'h' if d[1] else 'v'
    M = ray[0]
    if M in qinfo:
      return None
    for dr, dc in DIRS:
      nb = (M[0] + dr, M[1] + dc)
      if nb != K and nb in qinfo:
        return None
    for cell in ray:
      if cell in own:
        return None
      for dr, dc in DIRS:
        nb = (cell[0] + dr, cell[1] + dc)
        if nb in own and nb != K:
          return None
      for jdx, (_, _, _, ray2) in enumerate(geo):
        if jdx == idx:
          continue
        m2 = ray2[0]
        if cell in ray2:
          return None
        if max(abs(cell[0] - m2[0]), abs(cell[1] - m2[1])) <= 1:
          return None
      if cell in qinfo:
        lst = qinfo[cell]
        j, ax = lst[0]
        if len(lst) != 1 or ax is None or ax == rax or cell not in fsets[j]:
          return None
        above.add((colours[i], colours[j]))
  finfo = _geometry(finals)
  if finfo is None:
    return None
  return finfo, above


def _attach_markers(height, width, polys, colours, qinfo, want):
  for _ in range(15):
    markers = []
    for _ in range(4 * want):
      if len(markers) == want:
        break
      cand = _pick_marker(polys, markers)
      if cand:
        markers.append(cand)
    if len(markers) != want:
      continue
    checked = _check_markers(height, width, polys, colours, qinfo, markers)
    if checked:
      return [list(m) for m in markers], checked[0], checked[1]
  return None


def _random_order(colours, above):
  remaining, order = list(colours), []
  while remaining:
    avail = [c for c in remaining
             if not any(u == c and l in remaining for u, l in above)]
    if not avail:
      return None
    c = random.choice(avail)
    order.append(c)
    remaining.remove(c)
  return order


def _decorate(height, width, polys, colours, qinfo, markers, finfo, order):
  """Chooses crossing displays, 2s and gaps; returns overrides or None."""
  rank = {c: i for i, c in enumerate(order)}
  ext = {}
  for i, side, k in markers:
    _, d = _marker_geometry(polys[i], side, k)
    ext.setdefault(colours[i], set()).add('h' if d[1] else 'v')
  over, protected, settled, loose = {}, set(), {}, {}
  anchored, shown = set(), []
  for cell in sorted(finfo):
    lst = finfo[cell]
    if len(lst) != 2:
      continue
    (i, ai), (j, aj) = lst
    ci, cj = colours[i], colours[j]
    key = (min(ci, cj), max(ci, cj))
    settled.setdefault(key, False)
    if len(qinfo.get(cell, ())) < 2:
      # A ray crossing: the input shows the crossed path, which is lower.
      protected.add(cell)
      settled[key] = True
      continue
    top, bot = (ci, cj) if rank[ci] > rank[cj] else (cj, ci)
    pref = _blank_top(ci, ai, cj, aj, ext)
    roll = random.random()
    if pref == top and roll < P_AXIS_BLANK:
      over[cell] = 0
      settled[key] = True
      anchored.add(key)
    elif pref is None and roll < P_LOOSE_BLANK:
      over[cell] = 0
      loose.setdefault(key, []).append((cell, bot))
    else:
      over[cell] = bot
      settled[key] = True
      shown.append((cell, key, top))
  for key, ok in settled.items():
    if not ok:
      cell, bot = loose[key][0]
      over[cell] = bot
  # A decided blank crossing fixes its pair before any visible cue is read,
  # so other crossings of that pair may show the upper colour (demo 4).
  for cell, key, top in shown:
    if key in anchored and random.random() < P_UPPER_SHOWN:
      over[cell] = top
  for cell in sorted(qinfo):
    lst = qinfo[cell]
    if len(lst) == 2 and cell not in over:
      over[cell] = random.choice(
          (colours[lst[0][0]], colours[lst[1][0]], 0))
  paths = list(zip(colours, polys))

  def show():
    items = sorted((r, c, v) for (r, c), v in over.items())
    return _render(height, width, paths, order, markers, items)

  if not _input_ok(show()['input'], polys, colours):
    return None
  ends = []
  for poly in polys:
    for idx, v in enumerate(poly):
      ends.append((tuple(v), 0.18 if idx in (0, len(poly) - 1) else 0.5))
  random.shuffle(ends)
  for v, p in ends:
    if random.random() >= p:
      continue
    over[v] = CORNER
    twos = {c for c, val in over.items() if val == CORNER}
    if not (_spacing_ok(polys, twos) and
            _input_ok(show()['input'], polys, colours)):
      del over[v]
  gaps = sorted(c for c, lst in qinfo.items()
                if len(lst) == 1 and lst[0][1] is not None
                and c not in protected)
  random.shuffle(gaps)
  want, made = random.randint(0, 4), 0
  for cell in gaps:
    if made >= want:
      break
    over[cell] = 0
    if _input_ok(show()['input'], polys, colours):
      made += 1
    else:
      del over[cell]
  pair = show()
  if pair['input'] == pair['output']:
    return None
  counts = {}
  for row in pair['input']:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  if any(v != 0 and n >= counts.get(0, 0) for v, n in counts.items()):
    return None
  return sorted([r, c, v] for (r, c), v in over.items())


def _draw_size(height, width, n):
  """Samples missing dimensions; larger minimum for crowded scenes."""
  lo = 10
  if n is not None and n >= 4:
    lo = 10 + 2 * (n - 3)
  h = height or random.randint(lo, 20)
  w = width or random.randint(lo, 20)
  return h, w


def _sample(height, width, num_paths, num_markers, palette):
  """Draws a target configuration, then retries only the geometry."""
  pool = tuple(palette) if palette else PALETTE
  for _ in range(SIZE_DRAWS):
    h, w = _draw_size(height, width, num_paths)
    if num_paths:
      n = num_paths
    else:
      n = random.choice((2, 2, 3, 3, 3, 4, 4))
      if min(h, w) >= 14 and random.random() < 0.15:
        n = 5
      n = min(n, len(pool))
    if num_markers is not None:
      want = num_markers
    else:
      want = random.choice((0, 0, 1, 1, 1, 2, 2))
    for _ in range(SCENE_TRIES):
      colours = random.sample(pool, n)
      polys = _place_paths(h, w, n)
      if polys is None:
        continue
      qinfo = _geometry(polys)
      if qinfo is None or not _spacing_ok(polys, set()):
        continue
      attached = _attach_markers(h, w, polys, colours, qinfo, want)
      if attached is None:
        continue
      markers, finfo, above = attached
      if not any(len(lst) == 2 for lst in finfo.values()):
        continue
      order = _random_order(colours, above)
      if order is None:
        continue
      over = _decorate(h, w, polys, colours, qinfo, markers, finfo, order)
      if over is None:
        continue
      return h, w, list(zip(colours, polys)), order, markers, over
  raise RuntimeError('could not construct a scene with the requested '
                     'size/path/marker settings')


def _check_palette(palette, num_paths):
  if palette is None:
    return None
  if not _is_seq(palette):
    raise ValueError('palette must be a list or tuple of colours')
  pal = list(palette)
  for c in pal:
    if not _is_int(c) or c not in PALETTE:
      raise ValueError('palette colours must come from %s' % (PALETTE,))
  if len(set(pal)) != len(pal):
    raise ValueError('palette colours must be distinct')
  if len(pal) < 2:
    raise ValueError('palette needs at least two colours')
  if num_paths is not None and len(pal) < num_paths:
    raise ValueError('palette is smaller than num_paths')
  return pal


def _normalise_paths(paths):
  if not _is_seq(paths):
    raise ValueError('paths must be a list of [colour, vertices]')
  out = []
  for item in paths:
    if not _is_seq(item) or len(item) != 2:
      raise ValueError('path must be [colour, vertices]')
    colour, verts = item
    if not _is_int(colour):
      raise ValueError('path colour must be an integer')
    if not _is_seq(verts):
      raise ValueError('path vertices must be a list')
    vs = []
    for v in verts:
      if (not _is_seq(v) or len(v) != 2 or not _is_int(v[0]) or
          not _is_int(v[1])):
        raise ValueError('path vertex must be [row, col] integers')
      vs.append((v[0], v[1]))
    out.append((colour, vs))
  return out


def _normalise_triples(name, items):
  if items is None:
    return []
  if not _is_seq(items):
    raise ValueError('%s must be a list' % name)
  out = []
  for m in items:
    if not _is_seq(m) or len(m) != 3:
      raise ValueError('each %s entry must have three fields' % name)
    out.append(tuple(m))
  return out


def _check_explicit(height, width, paths, markers, overrides):
  colours = {c for c, _ in paths}
  occupied = set()
  for colour, verts in paths:
    if not 1 <= colour <= 9 or colour in (CORNER, MARK):
      raise ValueError('path colour must be in 1..9 and not 2 or 4')
    if len(verts) < 2:
      raise ValueError('a path needs at least two vertices')
    for r, c in verts:
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError('path vertex out of bounds')
    for a, b in zip(verts, verts[1:]):
      if (a[0] != b[0]) == (a[1] != b[1]):
        raise ValueError('segments must be axis-aligned and non-empty')
    cells = _cells(verts)
    if len(set(cells)) != len(cells):
      raise ValueError('a path may not overlap itself')
    occupied.update(cells)
  seen, mark_cells = {}, set()
  for i, side, k in markers:
    if not _is_int(i) or not _is_int(k):
      raise ValueError('marker index and vertex must be integers')
    if not 0 <= i < len(paths):
      raise ValueError('marker path index out of range')
    if side not in ('start', 'end'):
      raise ValueError('marker side must be start or end')
    if not 1 <= k <= len(paths[i][1]) - 2:
      raise ValueError('marker vertex must be an interior corner')
    if (i, side) in seen:
      raise ValueError('at most one marker per path end')
    seen[(i, side)] = k
    K, d = _marker_geometry(paths[i][1], side, k)
    M = (K[0] + d[0], K[1] + d[1])
    if not (0 <= M[0] < height and 0 <= M[1] < width):
      raise ValueError('marker cell out of bounds')
    if M in occupied:
      raise ValueError('marker cell may not lie on a path')
    mark_cells.add(M)
  for (i, side), k in seen.items():
    if side == 'start' and (i, 'end') in seen and k >= seen[(i, 'end')]:
      raise ValueError('start marker must precede end marker')
  for o in overrides:
    if not all(_is_int(x) for x in o):
      raise ValueError('override must be [row, col, value] integers')
    r, c, v = o
    if not (0 <= r < height and 0 <= c < width):
      raise ValueError('override out of bounds')
    if (r, c) in mark_cells:
      raise ValueError('override may not replace a 4-marker')
    if v not in colours and v not in (0, CORNER):
      raise ValueError('override value must be 0, 2 or a path colour')


def generate(height=None, width=None, num_paths=None, num_markers=None,
             palette=None, paths=None, order=None, markers=None,
             overrides=None):
  """Returns {'input': grid, 'output': grid}.

  Args:
    height: grid height, an integer in 6..30. Random when None (10..20, or
      12..20 / 14..20 when num_paths is 4 / 5). Defaults to 12 when
      explicit paths are given without a height.
    width: grid width, an integer in 6..30. Sampled like height when None.
      Defaults to 12 when explicit paths are given without a width.
    num_paths: number of paths (2..5) for random scenes. When paths is
      given, it must equal len(paths).
    num_markers: number of 4-markers (0..2) for random scenes. When paths
      is given, it must equal len(markers).
    palette: optional colour pool for random mode. It is a list of distinct
      colours from (1, 3, 5, 6, 7, 8, 9), with at least two entries and at
      least num_paths entries. Path colours are sampled from it. It must be
      None when explicit paths are given.
    paths: list of [colour, [[row, col], ...]] axis-aligned polylines, as
      they exist in the INPUT before marker redirection. When None, a fresh
      random scene is built, and order, markers and overrides must also be
      None.
    order: path colours from the bottom layer to the top layer. Defaults to
      sorted colours for explicit paths.
    markers: list of [path_index, side, k], where side is 'start' or 'end'.
      Vertex k is an interior corner K. The limb on that side of K is
      deleted, and the path is redirected from K away from that limb to the
      grid edge. The 4 sits on the first cell past K.
    overrides: list of [row, col, value] entries giving input damage. Use 2
      at corners or ends, 0 for gaps or blank crossings, and a path colour
      to set the colour shown at a crossing.
  """
  _check_int('height', height, MIN_SIDE, MAX_SIDE)
  _check_int('width', width, MIN_SIDE, MAX_SIDE)
  _check_int('num_paths', num_paths, 2, 5)
  _check_int('num_markers', num_markers, 0, 2)
  if paths is None:
    if order is not None or markers is not None or overrides is not None:
      raise ValueError('order/markers/overrides require explicit paths')
    pal = _check_palette(palette, num_paths)
    height, width, paths, order, markers, overrides = _sample(
        height, width, num_paths, num_markers, pal)
  else:
    if palette is not None:
      raise ValueError('palette applies only to random scenes')
    if num_paths is not None and (not _is_seq(paths) or
                                  num_paths != len(paths)):
      raise ValueError('num_paths does not match len(paths)')
    if num_markers is not None:
      if markers is not None and not _is_seq(markers):
        raise ValueError('markers must be a list')
      if num_markers != len(markers or []):
        raise ValueError('num_markers does not match len(markers)')
  height, width = height or 12, width or 12
  paths = _normalise_paths(paths)
  colours = [c for c, _ in paths]
  if len(set(colours)) != len(colours):
    raise ValueError('path colours must be distinct')
  if order is None:
    order = sorted(colours)
  if not _is_seq(order) or not all(_is_int(c) for c in order):
    raise ValueError('order must be a list of integer colours')
  if sorted(order) != sorted(colours):
    raise ValueError('order must be a permutation of the path colours')
  markers = _normalise_triples('markers', markers)
  overrides = _normalise_triples('overrides', overrides)
  _check_explicit(height, width, paths, markers, overrides)
  return _render(height, width, paths, order, markers, overrides)


def validate():
  """Rebuilds the canonical fixtures from explicit latent parameters."""
  train = [
      generate(height=12, width=12,
               paths=[[1, [[1, 0], [1, 3], [5, 3], [5, 6], [10, 6],
                           [10, 10], [11, 10], [11, 11]]],
                      [3, [[3, 0], [3, 4], [8, 4], [8, 9], [0, 9]]]],
               order=[3, 1], markers=[],
               overrides=[[3, 0, 2], [3, 3, 3], [3, 4, 2], [5, 4, 3],
                          [8, 4, 2], [8, 6, 3], [8, 8, 0], [8, 9, 2],
                          [10, 8, 0]]),
      generate(height=12, width=12,
               paths=[[7, [[1, 0], [1, 3], [5, 3], [5, 6], [7, 6], [7, 2],
                           [10, 2], [10, 10], [0, 10]]],
                      [3, [[9, 0], [9, 8], [2, 8], [2, 0]]]],
               order=[7, 3], markers=[[1, 'end', 2]],
               overrides=[[2, 5, 0], [4, 3, 0], [4, 8, 0], [5, 10, 0],
                          [9, 2, 0]]),
      generate(height=12, width=12,
               paths=[[7, [[0, 2], [6, 2], [6, 0]]],
                      [3, [[0, 4], [3, 4], [3, 0]]],
                      [6, [[0, 6], [4, 6], [4, 11]]],
                      [1, [[0, 9], [8, 9], [8, 4], [11, 4]]]],
               order=[7, 3, 1, 6], markers=[],
               overrides=[[0, 9, 2], [1, 4, 0], [1, 6, 0], [3, 2, 7],
                          [3, 4, 2], [4, 7, 0], [4, 9, 1], [6, 1, 0],
                          [6, 9, 0], [8, 4, 2], [8, 9, 2], [10, 4, 0]]),
      generate(height=12, width=12,
               paths=[[1, [[0, 1], [5, 1], [5, 6], [0, 6]]],
                      [6, [[2, 0], [2, 10], [0, 10]]]],
               order=[6, 1], markers=[[1, 'end', 1]],
               overrides=[[2, 6, 0], [2, 8, 0], [4, 1, 0], [5, 4, 0]]),
  ]
  test = [
      generate(height=12, width=12,
               paths=[[7, [[0, 4], [3, 4], [3, 1], [9, 1], [9, 7], [3, 7],
                           [3, 10], [0, 10]]],
                      [6, [[7, 0], [7, 11]]]],
               order=[6, 7], markers=[[0, 'start', 2], [0, 'end', 6]],
               overrides=[[3, 1, 2], [3, 4, 2], [3, 7, 2], [3, 10, 2],
                          [7, 1, 6], [7, 7, 0], [9, 1, 2], [9, 7, 2]]),
  ]
  return {'train': train, 'test': test}
