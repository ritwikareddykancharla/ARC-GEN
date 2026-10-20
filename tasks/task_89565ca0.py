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

"""ARC task 89565ca0: rank overlapping partitioned frames by compartment count.

Rule: the input holds several rectangular frames. Each frame is a one-pixel
outline in its own colour, and internal walls split it into compartments.
Frames are painted in a fixed order, so a later frame covers an earlier one
where their straight walls cross. One noise colour is scattered over the grid.
It is the colour that forms the most 8-connected pieces, and it also covers
some wall cells. The output has one row per frame, sorted by compartment count
in ascending order. On a tie, the frame lying underneath comes first. Every row
is as wide as the largest count. It holds `count` cells of the frame colour,
followed by noise-colour padding.

Occlusion convention (as in the demonstrations): take a straight line of a
frame and a run of covered cells on it between two of the frame's wall cells.
Covered cells are non-background cells of a foreign colour. The run is read as
wall when it is one cell long. It is also read as wall when it is two or three
cells long and the wall visibly continues past one end of the run. The reading
is repeated until it is stable, so one repaired gap can justify the next.
Covered runs that fail this test stay open, even when they lie exactly between
two wall cells. Such a false wall arises, for example, when the crossing wall
of another frame plus noise fills a narrow compartment.

Scope: random scenes have 3-5 frames and compartment counts of 1..6. Each
grid side is 14..30 cells. This is a synthetic range that covers the fixture
sizes. Default sides start at 14, 16 and 18 for 3, 4 and 5 frames. A supplied
side may be smaller than that default, but stays in 14..30; the other side
compensates so their sum is at least twice the default minimum. When both sides
are supplied, the frame count is sampled only among counts satisfying that
sum bound, or the call is rejected if an incompatible num_frames is supplied.
The sampled count is retained across construction retries. These bounds are
sampling controls, not a proof of packability; exhausting 300 placement
attempts raises RuntimeError. A frame is an outline
plus full dividers along one axis. Each band between dividers carries its own
partial cross walls, so compartments are banded axis-aligned rectangles of
varying size. There are no L-shaped compartments. Frame extents range from
small to nearly the full grid.

Frames may overlap only where straight walls cross at right angles. Placement
is often anchored near an earlier frame, and frames may nest. Painting order
is sampled independently of placement order. At most one pair of
frames shares a count, and that pair always shows a visible crossing that
reveals the layering.

Noise does five things:
- it hides single wall cells, corners included;
- it extends existing gaps into 2-3 cell gaps;
- it builds gap chains, where two 2-cell gaps are split by one wall cell, so
  the second gap is only read as wall after the first is repaired;
- it fills narrow compartments to make false walls that cannot be bridged;
- it is scattered over the background.
The final grid of every random scene is checked in three ways. Its visible
evidence, read with the convention above, must reconstruct exactly the latent
walls of every frame, except for hidden outer corners. The noise colour must
form clearly the most 8-connected pieces. Any tie must stay visibly ordered.
The answer itself is computed from the latent frame descriptions, not from the
rendered grid.
"""

import random

import common


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _low(n):
  """Smallest default grid side for n frames."""
  return 14 + 2 * (n - 3)


def _feasible(n, height, width):
  """Whether supplied sides leave enough room for n frames."""
  if height is not None and width is not None:
    return height + width >= 2 * _low(n)
  return True


def _frame_cells(top, left, bottom, right, segments):
  """Returns the set of wall cells of a frame (outline plus segments)."""
  cells = set()
  for x in range(left, right + 1):
    cells.add((top, x))
    cells.add((bottom, x))
  for y in range(top, bottom + 1):
    cells.add((y, left))
    cells.add((y, right))
  for kind, pos, a, b in segments:
    if kind == 'v':
      for y in range(a, b + 1):
        cells.add((y, pos))
    else:
      for x in range(a, b + 1):
        cells.add((pos, x))
  return cells


def _make_frame(color, top, left, bottom, right, segments):
  """Builds a frame record from its latent description."""
  cells = _frame_cells(top, left, bottom, right, segments)
  rows, cols = {}, {}
  for (y, x) in sorted(cells):
    rows.setdefault(y, []).append(x)
    cols.setdefault(x, []).append(y)
  mask = [[(y, x) in cells for x in range(left, right + 1)]
          for y in range(top, bottom + 1)]
  return {'color': color, 'top': top, 'left': left, 'bottom': bottom,
          'right': right, 'cells': cells, 'rows': rows, 'cols': cols,
          'mask': mask,
          'corners': {(top, left), (top, right), (bottom, left),
                      (bottom, right)}}


def _compartments(frame):
  """Counts 4-connected interior regions of the clean (latent) frame."""
  cells, seen, count = frame['cells'], set(), 0
  t, l, b, r = frame['top'], frame['left'], frame['bottom'], frame['right']
  for y in range(t + 1, b):
    for x in range(l + 1, r):
      if (y, x) in cells or (y, x) in seen:
        continue
      count += 1
      seen.add((y, x))
      stack = [(y, x)]
      while stack:
        cy, cx = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
          ny, nx = cy + dy, cx + dx
          if t < ny < b and l < nx < r and (ny, nx) not in cells:
            if (ny, nx) not in seen:
              seen.add((ny, nx))
              stack.append((ny, nx))
  return count


def _render(height, width, objs, noise_color, noise):
  grid = common.grid(width, height, 0)
  for o in objs:
    for (y, x) in o['cells']:
      grid[y][x] = o['color']
  for (y, x) in noise:
    grid[y][x] = noise_color
  return grid


def _parts(total, n):
  """Splits `total` interior cells into n parts (>=2) with n-1 walls."""
  sizes = [2] * n
  for _ in range(total - (n - 1) - 2 * n):
    sizes[random.randrange(n)] += 1
  walls, pos = [], 0
  for s in sizes[:-1]:
    pos += s + 1
    walls.append(pos)
  return walls


def _sample_shape(k, max_h, max_w):
  """Samples a local frame layout with exactly k compartments."""
  for _ in range(30):
    vertical = random.random() < 0.5
    m = random.randint(1, min(k, 4))
    extra = [0] * m
    for _ in range(k - m):
      extra[random.randrange(m)] += 1
    major_lim = max_w if vertical else max_h
    minor_lim = max_h if vertical else max_w
    base = 3 * m - 1
    need = max(3 * (e + 1) - 1 for e in extra)
    if base + 2 > major_lim or need + 2 > minor_lim:
      continue
    slack_major = major_lim - base - 2
    slack_minor = minor_lim - need - 2
    # Mix compact frames with frames that can stretch across the grid.
    if random.random() < 0.6:
      slack_major = min(slack_major, 2 * m + 4)
    if random.random() < 0.6:
      slack_minor = min(slack_minor, 6)
    widths = [2] * m
    for _ in range(random.randint(0, slack_major)):
      widths[random.randrange(m)] += 1
    major = sum(widths) + m - 1
    minor = need + random.randint(0, slack_minor)
    segs, u = [], 0
    for i in range(m):
      start = u
      u = start + widths[i] + 1
      if i < m - 1:
        segs.append(('full', u, 0, 0))
      for off in _parts(minor, extra[i] + 1):
        segs.append(('part', off, start, u))
    local = []
    if vertical:
      h, w = minor + 2, major + 2
      for kind, p, a, b in segs:
        local.append(('v', p, 0, h - 1) if kind == 'full' else ('h', p, a, b))
    else:
      h, w = major + 2, minor + 2
      for kind, p, a, b in segs:
        local.append(('h', p, 0, w - 1) if kind == 'full' else ('v', p, a, b))
    return h, w, local
  return None


def _shift(local, top, left):
  out = []
  for kind, pos, a, b in local:
    if kind == 'v':
      out.append(('v', left + pos, top + a, top + b))
    else:
      out.append(('h', top + pos, left + a, left + b))
  return out


def _straight(cells, y, x):
  h = (y, x - 1) in cells and (y, x + 1) in cells
  v = (y - 1, x) in cells and (y + 1, x) in cells
  hn = (y, x - 1) in cells or (y, x + 1) in cells
  vn = (y - 1, x) in cells or (y + 1, x) in cells
  if h and not vn:
    return 'h'
  if v and not hn:
    return 'v'
  return None


def _compatible(a, b):
  """Overlaps must be perpendicular crossings of two straight walls."""
  for (y, x) in a & b:
    if {_straight(a, y, x), _straight(b, y, x)} != {'h', 'v'}:
      return False
  return True


def _place_frames(height, width, counts, tie):
  """Places frames; later frames are often anchored over earlier ones."""
  placed = []
  for idx, k in enumerate(counts):
    done = False
    for _ in range(25):
      shape = _sample_shape(k, height, width)
      if shape is None:
        continue
      fh, fw, local = shape
      anchor = None
      if tie and idx == 1:
        anchor = placed[0]
      elif placed and random.random() < 0.6:
        anchor = random.choice(placed)
      for _ in range(25):
        if anchor is not None:
          t0, l0, b0, r0 = anchor[0:4]
          ylo, yhi = max(0, t0 - fh + 2), min(height - fh, b0 - 1)
          xlo, xhi = max(0, l0 - fw + 2), min(width - fw, r0 - 1)
          if ylo > yhi or xlo > xhi:
            break
          top, left = random.randint(ylo, yhi), random.randint(xlo, xhi)
        else:
          top = random.randint(0, height - fh)
          left = random.randint(0, width - fw)
        segs = _shift(local, top, left)
        bottom, right = top + fh - 1, left + fw - 1
        cells = _frame_cells(top, left, bottom, right, segs)
        if all(_compatible(cells, p[5]) for p in placed):
          placed.append((top, left, bottom, right, segs, cells))
          done = True
          break
      if done:
        break
    if not done:
      return None
  return placed


def _bridges(wall, cand):
  """Indices of covered runs on one line that read as wall this pass."""
  n, out, j = len(wall), [], 1
  while j < n:
    if cand[j] and not wall[j] and wall[j - 1]:
      k = j
      while k < n and cand[k] and not wall[k]:
        k += 1
      if k < n and wall[k]:
        size = k - j
        ext = (j >= 2 and wall[j - 2]) or (k + 1 < n and wall[k + 1])
        if size == 1 or (size <= 3 and ext):
          out.extend(range(j, k))
      j = max(k, j + 1)
    else:
      j += 1
  return out


def _readable(grid, f):
  """True if the visible evidence reconstructs the latent walls of f.

  The occlusion convention from the module docstring is applied inside the
  frame's box, where all of its colour lives. Hidden outer corners may stay
  unread: they are isolated border cells and never join a compartment.
  """
  color, t, l = f['color'], f['top'], f['left']
  hh, ww = f['bottom'] - t + 1, f['right'] - l + 1
  wall, cand = [], []
  for i in range(hh):
    row = grid[t + i][l:l + ww]
    wall.append([v == color for v in row])
    cand.append([v != 0 and v != color for v in row])
  if not (any(wall[0]) and any(wall[-1]) and any(r[0] for r in wall) and
          any(r[-1] for r in wall)):
    return False
  wall_t = [list(c) for c in zip(*wall)]
  cand_t = [list(c) for c in zip(*cand)]
  row_live = [any(c) for c in cand]
  col_live = [any(c) for c in cand_t]
  for _ in range(10):
    add = []
    for i in range(hh):
      if row_live[i]:
        for j in _bridges(wall[i], cand[i]):
          add.append((i, j))
    for j in range(ww):
      if col_live[j]:
        for i in _bridges(wall_t[j], cand_t[j]):
          add.append((i, j))
    if not add:
      break
    for i, j in add:
      wall[i][j] = True
      wall_t[j][i] = True
  mask = f['mask']
  for i in range(hh):
    if wall[i] == mask[i]:
      continue
    for j in range(ww):
      if wall[i][j] != mask[i][j]:
        if mask[i][j] and (t + i, l + j) in f['corners']:
          continue
        return False
  return True


def _near(f, cells):
  """True if changing `cells` could alter how frame f is read."""
  for (y, x) in cells:
    if not (f['top'] <= y <= f['bottom'] and f['left'] <= x <= f['right']):
      continue
    if any(abs(v - x) <= 4 for v in f['rows'].get(y, ())):
      return True
    if any(abs(v - y) <= 4 for v in f['cols'].get(x, ())):
      return True
  return False


def _near_colour(grid, cells, old, colour):
  h, w = len(grid), len(grid[0])
  for (y, x), v in zip(cells, old):
    if v == colour:
      return True
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
      ny, nx = y + dy, x + dx
      if 0 <= ny < h and 0 <= nx < w and grid[ny][nx] == colour:
        return True
  return False


def _gap_extensions(grid, f):
  """Visible wall cells next to a covered cell on the same straight line."""
  color, cells, out = f['color'], f['cells'], []
  for (y, x) in sorted(cells):
    if grid[y][x] != color:
      continue
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
      ny, nx = y + dy, x + dx
      if ((ny, nx) in cells and grid[ny][nx] != color and
          (y - dy, x - dx) in cells):
        out.append((y, x))
        break
  return out


def _chain_sites(grid, f):
  """Sites for two 2-cell cover runs split by one visible wall cell.

  The pattern on a straight line is W W C C W C C W, where W is visible wall
  and C will be covered. Strict sites are those where the wall does not
  continue visibly past the last W. There the second run can only be read as
  wall after the first is repaired, as in the row-18 gap chain of the third
  demonstration.
  """
  color, cells = f['color'], f['cells']
  strict, loose = [], []
  for (y, x) in sorted(cells):
    for dy, dx in ((0, 1), (1, 0)):
      line = [(y + dy * i, x + dx * i) for i in range(8)]
      if not all(c in cells and grid[c[0]][c[1]] == color for c in line):
        continue
      site = [line[2], line[3], line[5], line[6]]
      after = (y + dy * 8, x + dx * 8)
      if after in cells and grid[after[0]][after[1]] == color:
        loose.append(site)
      else:
        strict.append(site)
  return strict if strict else loose


def _narrow_runs(grid, f):
  """Background cells of 2-3 cell gaps between consecutive wall cells."""
  out = []
  for y, xs in f['rows'].items():
    for p, q in zip(xs, xs[1:]):
      if 3 <= q - p <= 4:
        run = [(y, x) for x in range(p + 1, q) if grid[y][x] == 0]
        if run:
          out.append(run)
  for x, ys in f['cols'].items():
    for p, q in zip(ys, ys[1:]):
      if 3 <= q - p <= 4:
        run = [(y, x) for y in range(p + 1, q) if grid[y][x] == 0]
        if run:
          out.append(run)
  return out


def _pieces(grid, color):
  h, w = len(grid), len(grid[0])
  seen, count = set(), 0
  for y in range(h):
    for x in range(w):
      if grid[y][x] != color or (y, x) in seen:
        continue
      count += 1
      seen.add((y, x))
      stack = [(y, x)]
      while stack:
        cy, cx = stack.pop()
        for dy in (-1, 0, 1):
          for dx in (-1, 0, 1):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and grid[ny][nx] == color:
              if (ny, nx) not in seen:
                seen.add((ny, nx))
                stack.append((ny, nx))
  return count


def _votes(grid, over, under):
  """Counts visible crossings where colour `over` passes over `under`."""
  h, w = len(grid), len(grid[0])

  def val(y, x):
    return grid[y][x] if 0 <= y < h and 0 <= x < w else -1

  n = 0
  for y in range(h):
    for x in range(w):
      if grid[y][x] != over:
        continue
      l, r, u, d = val(y, x - 1), val(y, x + 1), val(y - 1, x), val(y + 1, x)
      if l == r == under and u == d == over:
        n += 1
      if u == d == under and l == r == over:
        n += 1
  return n


def _random_scene(height=None, width=None, noise_color=None, num_frames=None):
  """Builds a random latent scene, honouring any supplied controls."""
  n = num_frames if num_frames is not None else random.choice(
      [k for k in (3, 4, 5) if _feasible(k, height, width)])
  for _ in range(300):
    low = _low(n)
    if height is not None:
      h = height
    elif width is not None:
      h = random.randint(max(low, 2 * low - width), 30)
    else:
      h = random.randint(low, 30)
    if width is not None:
      w = width
    elif height is not None:
      w = random.randint(max(low, 2 * low - h), 30)
    else:
      w = random.randint(low, 30)
    if noise_color is None:
      palette = random.sample(range(1, 10), n + 1)
      nc, colors = palette[0], palette[1:]
    else:
      nc = noise_color
      colors = random.sample([c for c in range(1, 10) if c != nc], n)
    tie = random.random() < 0.35
    if tie:
      base = random.sample(range(1, 7), n - 1)
      t = random.choice(base)
      counts = [t, t] + [c for c in base if c != t]
    else:
      counts = random.sample(range(1, 7), n)
    placed = _place_frames(h, w, counts, tie)
    if placed is None:
      continue
    order = list(range(n))
    random.shuffle(order)
    specs = []
    for pos, src in enumerate(order):
      top, left, bottom, right, segs, _ = placed[src]
      specs.append((colors[pos], top, left, bottom, right, segs))
    objs = [_make_frame(*s) for s in specs]
    grid = _render(h, w, objs, nc, [])
    if not all(_readable(grid, o) for o in objs):
      continue
    over = under = None
    if tie:
      a, b = order.index(0), order.index(1)
      under, over = colors[min(a, b)], colors[max(a, b)]
      if _votes(grid, over, under) == 0 or _votes(grid, under, over) > 0:
        continue
    noise = []

    def try_noise(cells):
      old = [grid[y][x] for (y, x) in cells]
      for (y, x) in cells:
        grid[y][x] = nc
      ok = all(_readable(grid, o) for o in objs if _near(o, cells))
      if ok and over is not None and _near_colour(grid, cells, old, over):
        ok = _votes(grid, over, under) > 0
      if ok:
        noise.extend(cells)
      else:
        for (y, x), v in zip(cells, old):
          grid[y][x] = v
      return ok

    for o in objs:
      # Gap chains that need repeated repair passes.
      if random.random() < 0.4:
        sites = _chain_sites(grid, o)
        random.shuffle(sites)
        for site in sites[:4]:
          if try_noise(site):
            break
      # Single hidden wall cells (corners allowed).
      cand = [c for c in sorted(o['cells']) if grid[c[0]][c[1]] == o['color']]
      random.shuffle(cand)
      want, got = random.randint(0, 3), 0
      for c in cand[:15]:
        if got >= want:
          break
        if try_noise([c]):
          got += 1
      # Lengthen existing gaps (next to a crossing or a hidden cell).
      for _ in range(random.randint(0, 2)):
        ext = _gap_extensions(grid, o)
        if not ext:
          break
        random.shuffle(ext)
        for c in ext[:6]:
          if try_noise([c]):
            break
    for o in objs:
      # False walls: fill a narrow gap between two wall cells with noise.
      if random.random() < 0.5:
        runs = _narrow_runs(grid, o)
        random.shuffle(runs)
        for run in runs[:4]:
          if try_noise(run):
            break
    area = h * w
    target = random.randint(max(8, area // 35), max(14, area // 15))
    tries, added = 0, 0
    while added < target and tries < target * 4:
      tries += 1
      y, x = random.randrange(h), random.randrange(w)
      if grid[y][x] == 0 and try_noise([(y, x)]):
        added += 1

    def margin_ok():
      top_frame = max(_pieces(grid, o['color']) for o in objs)
      return _pieces(grid, nc) >= top_frame + 2

    ok = margin_ok()
    for _ in range(60):
      if ok:
        break
      y, x = random.randrange(h), random.randrange(w)
      if grid[y][x] == 0 and try_noise([(y, x)]):
        ok = margin_ok()
    if not ok:
      continue
    # Global re-check: the locality heuristic in _near must not hide a
    # dependency between noise cells and a frame's reading.
    if not all(_readable(grid, o) for o in objs):
      continue
    if over is not None and (_votes(grid, over, under) == 0 or
                             _votes(grid, under, over) > 0):
      continue
    return h, w, nc, specs, noise
  raise RuntimeError('could not construct a valid scene for these controls')


def _check_explicit(height, width, noise_color, frames, noise):
  """Rejects malformed explicit scenes instead of silently rendering them."""
  for v in (height, width, noise_color):
    if not _is_int(v):
      raise ValueError('height, width and noise_color must be integers')
  if not (1 <= height <= 30 and 1 <= width <= 30):
    raise ValueError('grid sides must be in 1..30')
  if not 1 <= noise_color <= 9:
    raise ValueError('noise_color must be in 1..9')
  if not isinstance(frames, (list, tuple)) or not frames:
    raise ValueError('at least one frame is required')
  for f in frames:
    if not isinstance(f, (list, tuple)) or len(f) != 6:
      raise ValueError('a frame is (color, top, left, bottom, right, segs)')
    if not all(_is_int(v) for v in f[:5]):
      raise ValueError('frame fields must be integers')
    if not isinstance(f[5], (list, tuple)):
      raise ValueError('frame segments must be a list')
  colors = [f[0] for f in frames]
  if len(set(colors)) != len(colors) or noise_color in colors:
    raise ValueError('frame colours must be distinct and differ from noise')
  for color, top, left, bottom, right, segs in frames:
    if not 1 <= color <= 9:
      raise ValueError('frame colour must be in 1..9')
    if not (0 <= top < bottom < height and 0 <= left < right < width):
      raise ValueError('frame outside the grid')
    if bottom - top < 2 or right - left < 2:
      raise ValueError('frame has no interior')
    for seg in segs:
      if not isinstance(seg, (list, tuple)) or len(seg) != 4:
        raise ValueError('a segment is (kind, pos, start, end)')
      kind, pos, a, b = seg
      if kind not in ('v', 'h') or not all(_is_int(v) for v in (pos, a, b)):
        raise ValueError('bad segment')
      if a > b:
        raise ValueError('bad segment')
      if kind == 'v' and not (left <= pos <= right and top <= a and
                              b <= bottom):
        raise ValueError('segment outside its frame')
      if kind == 'h' and not (top <= pos <= bottom and left <= a and
                              b <= right):
        raise ValueError('segment outside its frame')
  if not isinstance(noise, (list, tuple)):
    raise ValueError('noise must be a list of (row, col) cells')
  for c in noise:
    if (not isinstance(c, (list, tuple)) or len(c) != 2 or
        not all(_is_int(v) for v in c)):
      raise ValueError('noise cells must be (row, col) integer pairs')
    if not (0 <= c[0] < height and 0 <= c[1] < width):
      raise ValueError('noise cell outside the grid')


def _check_rendered(grid, objs, counts, noise_color):
  """Rejects explicit scenes whose rendering is invalid or ambiguous."""
  if max(counts) > 30:
    raise ValueError('output would be wider than 30 cells')
  noise_pieces = _pieces(grid, noise_color)
  for o in objs:
    p = _pieces(grid, o['color'])
    if p == 0:
      raise ValueError('a frame colour is completely hidden')
    if not _readable(grid, o):
      raise ValueError('visible evidence does not reconstruct the frame walls')
    if p >= noise_pieces:
      raise ValueError('the noise colour must form strictly the most '
                       '8-connected pieces')
  for i in range(len(objs)):
    for j in range(i + 1, len(objs)):
      if counts[i] == counts[j]:
        under, over = objs[i]['color'], objs[j]['color']
        if _votes(grid, over, under) <= _votes(grid, under, over):
          raise ValueError('tied frames need a visible crossing that shows '
                           'the later frame on top')


def generate(height=None, width=None, noise_color=None, frames=None,
             noise=None, num_frames=None):
  """Returns an input/output pair for task 89565ca0.

  Args:
    height: grid height. Required with explicit frames (1..30). For random
      scenes it is an optional integer in 14..30.
    width: grid width. Required with explicit frames (1..30). For random
      scenes it is an optional integer in 14..30. If both sides are given
      for a random scene, height + width must be at least 28, 32 or 36 for 3,
      4 or 5 frames.
    noise_color: colour of the scattered noise and of the output padding.
      Required with explicit frames; optional (1..9) for random scenes.
    frames: frames in painting order, bottom layer first. Each frame is
      (color, top, left, bottom, right, segments). Each segment is either
      ('v', x, y0, y1) or ('h', y, x0, x1) and marks an internal wall.
      Explicit scenes are rendered as given and must satisfy the same wall
      readability convention as random scenes. Crossing geometry itself is
      not restricted to the random sampler. Scenes are rejected with ValueError
      when the noise colour does not form strictly the most 8-connected
      pieces, when a frame colour is fully hidden, when tied frames lack a
      visible crossing that shows the later frame on top, or when the output
      would exceed 30 cells.
    noise: list of (row, col) cells painted with noise_color after the
      frames. Only accepted together with explicit frames.
    num_frames: optional number of frames (3..5) for random scenes. If
      explicit frames are given, it must equal len(frames).
  """
  if frames is None:
    if noise is not None:
      raise ValueError('noise cells can only be supplied with explicit frames')
    for v in (height, width):
      if v is not None and (not _is_int(v) or not 14 <= v <= 30):
        raise ValueError('random scenes need integer grid sides in 14..30')
    if noise_color is not None and (not _is_int(noise_color) or
                                    not 1 <= noise_color <= 9):
      raise ValueError('noise_color must be an integer in 1..9')
    if num_frames is not None and (not _is_int(num_frames) or
                                   not 3 <= num_frames <= 5):
      raise ValueError('num_frames must be an integer in 3..5')
    if num_frames is not None and not _feasible(num_frames, height, width):
      raise ValueError('grid too small for this many frames')
    height, width, noise_color, frames, noise = _random_scene(
        height, width, noise_color, num_frames)
    explicit = False
  else:
    if height is None or width is None or noise_color is None:
      raise ValueError('explicit frames need height, width and noise_color')
    if noise is None:
      noise = []
    _check_explicit(height, width, noise_color, frames, noise)
    if num_frames is not None and (not _is_int(num_frames) or
                                   num_frames != len(frames)):
      raise ValueError('num_frames disagrees with the supplied frames')
    explicit = True
  objs = [_make_frame(*f) for f in frames]
  grid = _render(height, width, objs, noise_color, noise)
  counts = [_compartments(o) for o in objs]
  if min(counts) < 1:
    raise ValueError('every frame needs at least one compartment')
  if explicit:
    _check_rendered(grid, objs, counts, noise_color)
  order = sorted(range(len(objs)), key=lambda i: (counts[i], i))
  span = max(counts)
  output = [[objs[i]['color']] * counts[i] + [noise_color] * (span - counts[i])
            for i in order]
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the canonical fixtures from explicit latent scenes."""

  def cells(spec):
    return [(y, x) for y in sorted(spec) for x in spec[y]]

  train = [
      generate(height=22, width=28, noise_color=5, frames=[
          (1, 5, 4, 10, 9, []),
          (3, 3, 2, 15, 24, [('v', 13, 3, 15)]),
          (2, 12, 10, 20, 26, [('v', 15, 12, 20), ('v', 20, 12, 20),
                               ('h', 17, 10, 15)]),
      ], noise=cells({
          0: [7, 9, 14, 24], 1: [6, 11, 12, 15, 19], 2: [0, 2],
          3: [22, 25, 26], 4: [24], 6: [3, 7], 7: [2, 8, 18], 8: [2, 23],
          9: [4, 16], 10: [15, 17], 11: [1, 3, 10, 12, 18], 12: [3, 8, 23],
          13: [8, 24], 14: [0, 13, 16], 15: [9], 16: [6, 10],
          17: [1, 2, 15, 26], 18: [27], 19: [15, 21, 27], 20: [10, 13],
          21: [5]})),
      generate(height=22, width=28, noise_color=5, frames=[
          (1, 1, 1, 10, 7, [('h', 5, 1, 7)]),
          (2, 3, 4, 14, 15, [('v', 10, 3, 14), ('h', 10, 10, 15)]),
          (4, 1, 12, 8, 26, [('v', 17, 1, 8), ('v', 22, 1, 8)]),
          (8, 10, 17, 17, 24, []),
          (3, 16, 1, 20, 14, [('v', 3, 16, 20), ('v', 7, 16, 20),
                              ('v', 11, 16, 20)]),
      ], noise=cells({
          1: [16, 18], 3: [3, 19, 24, 25], 4: [25, 26], 5: [11, 19, 20],
          6: [21, 27], 7: [4], 8: [1], 9: [18], 10: [15, 18], 11: [21, 27],
          12: [20], 13: [1, 15, 19, 20, 21], 14: [16, 20, 24, 26, 27],
          15: [8, 12, 20], 18: [8, 10], 19: [18, 22],
          20: [8, 11, 18, 19, 24, 25], 21: [4, 5, 17]})),
      generate(height=22, width=20, noise_color=7, frames=[
          (8, 1, 14, 4, 17, []),
          (1, 1, 1, 8, 9, [('v', 4, 1, 8)]),
          (2, 6, 5, 18, 15, [('v', 11, 6, 13), ('h', 13, 5, 15)]),
          (4, 15, 3, 21, 19, [('v', 9, 15, 21), ('v', 12, 15, 21),
                              ('v', 16, 15, 21)]),
      ], noise=cells({
          0: [8, 10, 15], 2: [9, 10], 3: [4, 5], 6: [5], 7: [4, 15],
          8: [19], 9: [13], 10: [17], 11: [1, 11], 12: [9], 13: [1, 5, 11],
          14: [5], 18: [8, 11, 14], 19: [0], 20: [3, 17]})),
  ]
  test = [
      generate(height=29, width=30, noise_color=9, frames=[
          (2, 1, 1, 9, 5, [('h', 3, 1, 5), ('h', 6, 1, 5)]),
          (1, 1, 16, 22, 27, []),
          (8, 3, 11, 13, 25, [('v', 18, 3, 13)]),
          (3, 8, 3, 14, 14, [('v', 6, 8, 14), ('v', 9, 8, 14),
                             ('h', 11, 3, 14)]),
          (4, 16, 1, 25, 25, [('v', 5, 16, 25), ('v', 12, 16, 25),
                              ('h', 20, 1, 12)]),
      ], noise=cells({
          1: [8], 2: [12], 3: [14], 5: [1, 8], 6: [22, 28], 7: [16],
          9: [21], 10: [28], 12: [1], 14: [10], 16: [20], 17: [15],
          18: [1, 7, 29], 19: [21], 20: [9], 21: [11], 22: [27],
          23: [2, 14, 18], 25: [28], 26: [15], 27: [8, 9], 28: [0, 21]})),
  ]
  return {'train': train, 'test': test}
