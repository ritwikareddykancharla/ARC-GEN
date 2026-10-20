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

"""ARC task a32d8b75: legend-driven tiled stamping onto a canvas.

Rule: full columns of 6 split the grid into narrow legend strips and one
strictly wider canvas strip. The output is the canvas.

Each legend's upper area has a 0 background and holds two objects: a solid
two-colour tile and a one-colour shape. Below the upper area are two 3x3
boxes, framed by 6 and separated by full rows of 6. Box 1 holds a 4 in one
corner, which marks the anchor corner. Box 2 holds a 7 in the centre and a
second 7 on one edge, which together form the arrow.

The shape is rotated according to the arrow: up = no rotation, down = 180
degrees, right = clockwise, left = counter-clockwise. The two tile colours
are swapped, and the tile itself is not rotated. Every rotated-shape cell
becomes one copy of the swapped tile. The enlarged pattern is placed flush
in the anchor corner of the canvas. Cells outside the shape keep the canvas
colours.

Scope:
- One legend (left or right), or two legends (one on each side). Two
  legends have distinct anchors and non-overlapping stamps.
- Random legends are 4..7 wide.
- Random tiles are usually square with side 2..5. When tile_size is None,
  about 25% of tiles are rectangular (each side 2..4/5). Rectangular tiles
  are a synthetic extension that the rule supports. Side 5 is only sampled
  with a single legend.
- Hard tile decisions (hard_tile, default: random per legend with p=0.85)
  guarantee two things. First, the colour-swapped tile is not any rotation
  or reflection of the tile, so swapping cannot be mistaken for mirroring.
  Second, for a non-up arrow, rotating the tile by the arrow changes it, so
  the fact that the tile does not rotate is observable. Small tiles (<= 9
  cells) choose from an enumerated list of valid patterns, so there is no
  unbounded search. Soft tiles may be ambiguous, like the canonical test
  tile [[2,4],[4,2]].
- Random shapes are 4- or 8-connected tight masks whose eight D4 images are
  pairwise distinct. The four arrow results therefore all differ.
- Random stamps are strictly smaller than the canvas on both axes, so the
  anchor corner always matters.
- Random tile colours never occur in the canvas. Two legends use four
  distinct tile colours.
- Random layouts: tile above shape, shape above tile, or side by side.
  Every fixture stacks the tile above the shape; the other layouts are
  synthetic extensions.
- Random canvases are solid, banded, cross or blob scenes and never use 6.
- The layout is always H = separator_row + 8, so the second box ends at the
  bottom edge, as in every fixture.
- Random grid height is (tile_size + 11)..30, which is 13..30 by default.
  Total width is 11..30.
- Explicit legends accept heights 9..30. They may use symmetric shapes,
  ambiguous tiles, tile colours that also appear in the canvas, and stamps
  that span the full canvas, because the canonical fixtures need some of
  these. Explicit scenes are rejected when the stamps leave the canvas
  unchanged.
- Integer controls and cells must be real ints; bool and float are
  rejected.
"""

import functools
import itertools
import random

import common

_COLORS = [1, 2, 3, 4, 5, 7, 8, 9]
_CANVAS_COLORS = [0, 1, 2, 3, 4, 5, 7, 8, 9]
_DIRS = {'up': (0, 1), 'down': (2, 1), 'left': (1, 0), 'right': (1, 2)}
_CORNERS = {'tl': (0, 0), 'tr': (0, 2), 'bl': (2, 0), 'br': (2, 2)}
_KEYS = ('side', 'width', 'tile', 'tile_pos', 'shape', 'shape_color',
         'shape_pos', 'box_col', 'anchor', 'arrow')
_SIDE_CHOICES = (('left',), ('right',), ('left', 'right'), ('left',),
                 ('left', 'right'))


def _is_int(x):
  return type(x) is int


def _is_pos(p):
  return (isinstance(p, (list, tuple)) and len(p) == 2 and
          all(_is_int(v) for v in p))


def _is_rect(m):
  if not isinstance(m, (list, tuple)) or not m:
    return False
  if not all(isinstance(r, (list, tuple)) for r in m):
    return False
  return bool(m[0]) and all(len(r) == len(m[0]) for r in m)


def _rotate(mask, arrow):
  h, w = len(mask), len(mask[0])
  if arrow == 'up':
    return [list(row) for row in mask]
  if arrow == 'down':
    return [list(row[::-1]) for row in mask[::-1]]
  if arrow == 'right':  # clockwise
    return [[mask[h - 1 - j][i] for j in range(h)] for i in range(w)]
  return [[mask[j][w - 1 - i] for j in range(h)] for i in range(w)]


def _d4(mask):
  """All eight rotations/reflections of a rectangular matrix."""
  images = []
  cur = [list(r) for r in mask]
  for _ in range(4):
    images.append(cur)
    images.append([r[::-1] for r in cur])
    cur = _rotate(cur, 'right')
  return images


def _asymmetric(mask):
  """True when all eight rotations/reflections of the mask are distinct."""
  return sum(1 for im in _d4(mask) if im == mask) == 1


def _tile_ok(tile, arrow):
  """Hard-decision test: swap is not a D4 image; arrow rotation shows."""
  a, b = sorted({v for r in tile for v in r})
  swapped = [[b if v == a else a for v in r] for r in tile]
  if swapped in _d4(tile):
    return False
  if arrow != 'up' and _rotate(tile, arrow) == tile:
    return False
  return True


@functools.lru_cache(maxsize=None)
def _tile_patterns(th, tw, arrow, hard):
  """Enumerates valid two-colour bit patterns for small tiles."""
  n = th * tw
  res = []
  for bits in range(1, (1 << n) - 1):
    tile = [[(bits >> (i * tw + j)) & 1 for j in range(tw)]
            for i in range(th)]
    if not hard or _tile_ok(tile, arrow):
      res.append(bits)
  return tuple(res)


def _sample_tile(th, tw, ca, cb, arrow, hard):
  if th * tw <= 9:
    pats = _tile_patterns(th, tw, arrow, hard)
    if not pats:
      return None
    bits = random.choice(pats)
    return [[cb if (bits >> (i * tw + j)) & 1 else ca for j in range(tw)]
            for i in range(th)]
  for _ in range(200):
    p = random.uniform(0.25, 0.75)
    m = [[1 if random.random() < p else 0 for _ in range(tw)]
         for _ in range(th)]
    if len({v for r in m for v in r}) != 2:
      continue
    if hard and not _tile_ok(m, arrow):
      continue
    return [[cb if v else ca for v in r] for r in m]
  return None


def _legend_block(leg, height):
  w = leg['width']
  sep = height - 8
  block = [[0] * w for _ in range(height)]
  tr, tc = leg['tile_pos']
  for i, row in enumerate(leg['tile']):
    for j, v in enumerate(row):
      block[tr + i][tc + j] = v
  sr, sc = leg['shape_pos']
  for i, row in enumerate(leg['shape']):
    for j, v in enumerate(row):
      if v:
        block[sr + i][sc + j] = leg['shape_color']
  for y in range(sep, height):
    block[y] = [6] * w
  bc = leg['box_col']
  for k in range(3):
    for j in range(3):
      block[sep + 1 + k][bc + j] = 0
      block[sep + 5 + k][bc + j] = 0
  ay, ax = _CORNERS[leg['anchor']]
  block[sep + 1 + ay][bc + ax] = 4
  block[sep + 6][bc + 1] = 7
  dy, dx = _DIRS[leg['arrow']]
  block[sep + 5 + dy][bc + dx] = 7
  return block


def _rect(anchor, mh, mw, t_h, t_w, h, cw):
  sh, sw = mh * t_h, mw * t_w
  oy = h - sh if anchor[0] == 'b' else 0
  ox = cw - sw if anchor[1] == 'r' else 0
  return oy, ox, sh, sw


def _stamp_rect(leg, h, cw):
  tile = leg['tile']
  mask = _rotate(leg['shape'], leg['arrow'])
  return _rect(leg['anchor'], len(mask), len(mask[0]), len(tile),
               len(tile[0]), h, cw)


def _stamp(out, leg):
  tile = leg['tile']
  a, b = sorted({v for r in tile for v in r})
  swapped = [[b if v == a else a for v in r] for r in tile]
  mask = _rotate(leg['shape'], leg['arrow'])
  t_h, t_w = len(tile), len(tile[0])
  oy, ox, _, _ = _stamp_rect(leg, len(out), len(out[0]))
  for i, row in enumerate(mask):
    for j, v in enumerate(row):
      if not v:
        continue
      for p in range(t_h):
        for q in range(t_w):
          out[oy + i * t_h + p][ox + j * t_w + q] = swapped[p][q]


def _overlap(r1, r2):
  y1, x1, h1, w1 = r1
  y2, x2, h2, w2 = r2
  return y1 < y2 + h2 and y2 < y1 + h1 and x1 < x2 + w2 and x2 < x1 + w1


def _connected8(mask):
  cells = {(i, j) for i, r in enumerate(mask) for j, v in enumerate(r) if v}
  if not cells:
    return False
  start = min(cells)
  seen, stack = {start}, [start]
  while stack:
    y, x = stack.pop()
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        n = (y + dy, x + dx)
        if n in cells and n not in seen:
          seen.add(n)
          stack.append(n)
  return len(seen) == len(cells)


def _legend_cells(leg):
  tr, tc = leg['tile_pos']
  tile = {(tr + i, tc + j) for i, row in enumerate(leg['tile'])
          for j in range(len(row))}
  sr, sc = leg['shape_pos']
  shape = {(sr + i, sc + j) for i, row in enumerate(leg['shape'])
           for j, v in enumerate(row) if v}
  return tile, shape


def _check_canvas(canvas):
  if (not isinstance(canvas, (list, tuple)) or not canvas or
      not isinstance(canvas[0], (list, tuple)) or not canvas[0]):
    return 'canvas must be a non-empty list of non-empty rows'
  cw = len(canvas[0])
  for row in canvas:
    if not isinstance(row, (list, tuple)) or len(row) != cw:
      return 'canvas rows must all be lists of the same length'
    for v in row:
      if not _is_int(v) or v < 0 or v > 9 or v == 6:
        return 'canvas cells must be integer colours 0..9 other than 6'
  if not 9 <= len(canvas) <= 30:
    return 'canvas height must be 9..30 (the legend boxes need 8 rows)'
  return None


def _check_keys(legends):
  if not isinstance(legends, (list, tuple)) or not 1 <= len(legends) <= 2:
    return 'legends must be a list of one or two legend dicts'
  for leg in legends:
    if not isinstance(leg, dict):
      return 'each legend must be a dict'
    for k in _KEYS:
      if k not in leg:
        return 'legend is missing key %r' % k
  sides = [leg['side'] for leg in legends]
  if (any(not isinstance(s, str) or s not in ('left', 'right')
          for s in sides) or len(set(sides)) != len(sides)):
    return 'legend sides must be distinct values of left and right'
  for leg in legends:
    if not _is_int(leg['width']) or leg['width'] < 4:
      return 'legend width must be an integer >= 4 (framed 3x3 boxes)'
  return None


def _check_legend(leg, h, cw):
  lw = leg['width']
  tile = leg['tile']
  if not _is_rect(tile):
    return 'tile must be a non-empty rectangle of rows'
  if any(not _is_int(v) for r in tile for v in r):
    return 'tile cells must be integers'
  colors = {v for r in tile for v in r}
  if len(colors) != 2 or any(v < 1 or v > 9 or v == 6 for v in colors):
    return 'tile must be solid with exactly two colours other than 0 and 6'
  shape = leg['shape']
  if not _is_rect(shape):
    return 'shape must be a non-empty rectangle of rows'
  if any(not _is_int(v) or v not in (0, 1) for r in shape for v in r):
    return 'shape must be an integer 0/1 mask'
  if (not any(shape[0]) or not any(shape[-1]) or
      not any(r[0] for r in shape) or not any(r[-1] for r in shape)):
    return 'shape mask must be tight (no empty border rows or columns)'
  if not _connected8(shape):
    return 'shape must be a single 8-connected object'
  color = leg['shape_color']
  if not _is_int(color) or color < 1 or color > 9 or color == 6:
    return 'shape colour must be an integer 1..9 other than 6'
  if color in colors:
    return 'shape colour must differ from both tile colours'
  if not _is_pos(leg['tile_pos']) or not _is_pos(leg['shape_pos']):
    return 'tile_pos and shape_pos must be (row, col) integer pairs'
  sep = h - 8
  tile_cells, shape_cells = _legend_cells(leg)
  for y, x in tile_cells | shape_cells:
    if not (0 <= y < sep and 0 <= x < lw):
      return 'tile and shape must lie inside the legend upper area'
  sr, sc = leg['shape_pos']
  for y, x in tile_cells:
    if sr <= y < sr + len(shape) and sc <= x < sc + len(shape[0]):
      return 'the tile must lie outside the shape bounding box'
  for y, x in shape_cells:
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        if (y + dy, x + dx) in tile_cells:
          return 'tile and shape must not touch, even diagonally'
  bc = leg['box_col']
  if leg['side'] == 'left':
    lo, hi = 1, lw - 3
  else:
    lo, hi = 0, lw - 4
  if not _is_int(bc) or not lo <= bc <= hi:
    return ('box_col must keep both 3x3 boxes framed by 6 '
            '(left legends: 1..width-3, right legends: 0..width-4)')
  if not isinstance(leg['anchor'], str) or leg['anchor'] not in _CORNERS:
    return 'anchor must be one of tl, tr, bl, br'
  if not isinstance(leg['arrow'], str) or leg['arrow'] not in _DIRS:
    return 'arrow must be one of up, down, left, right'
  _, _, sh, sw = _stamp_rect(leg, h, cw)
  if sh > h or sw > cw:
    return 'the enlarged shape does not fit in the canvas'
  return None


def _check_scene(legends, canvas):
  err = _check_keys(legends) or _check_canvas(canvas)
  if err:
    return err
  h, cw = len(canvas), len(canvas[0])
  for leg in legends:
    err = _check_legend(leg, h, cw)
    if err:
      return err
  widths = [leg['width'] for leg in legends]
  if cw <= max(widths):
    return 'the canvas must be strictly wider than every legend'
  if cw + sum(w + 1 for w in widths) > 30:
    return 'total grid width must be at most 30'
  rects = [_stamp_rect(leg, h, cw) for leg in legends]
  if len(rects) == 2 and _overlap(rects[0], rects[1]):
    return 'the two stamps must not overlap'
  return None


def _random_mask(h, w, diagonal):
  steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
  if diagonal:
    steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
  for _ in range(200):
    hi = h * w - 1
    lo = min(hi, max(h + w - 1, (h * w + 2) // 3))
    target = random.randint(lo, hi)
    cells = {(random.randrange(h), random.randrange(w))}
    for _ in range(h * w * 30):
      if (len(cells) >= target and len({c[0] for c in cells}) == h and
          len({c[1] for c in cells}) == w):
        break
      y, x = random.choice(sorted(cells))
      dy, dx = random.choice(steps)
      ny, nx = y + dy, x + dx
      if 0 <= ny < h and 0 <= nx < w:
        cells.add((ny, nx))
    if len({c[0] for c in cells}) != h or len({c[1] for c in cells}) != w:
      continue
    if len(cells) >= h * w:
      continue
    mask = [[1 if (y, x) in cells else 0 for x in range(w)] for y in range(h)]
    if not _asymmetric(mask):
      continue
    return mask
  return None


def _random_canvas(h, w, avoid=()):
  palette = [c for c in _CANVAS_COLORS if c not in avoid]
  kind = random.choice(['solid', 'hbands', 'vbands', 'cross', 'blob'])
  a, b, c = random.sample(palette, 3)
  g = common.grid(w, h, a)
  if kind == 'hbands':
    y, i = 0, 0
    while y < h:
      k = random.randint(2, 8)
      for yy in range(y, min(h, y + k)):
        g[yy] = [(a, b)[i % 2]] * w
      y += k
      i += 1
  elif kind == 'vbands':
    x, i = 0, 0
    while x < w:
      k = random.randint(2, 7)
      for xx in range(x, min(w, x + k)):
        for yy in range(h):
          g[yy][xx] = (a, b)[i % 2]
      x += k
      i += 1
  elif kind == 'cross':
    kr, kc = random.randint(2, min(4, h)), random.randint(2, min(4, w))
    r0, c0 = random.randint(0, h - kr), random.randint(0, w - kc)
    for y in range(h):
      for x in range(w):
        if r0 <= y < r0 + kr or c0 <= x < c0 + kc:
          g[y][x] = b
  elif kind == 'blob':
    cy, cx = random.uniform(0.3, 0.7) * h, random.uniform(0.3, 0.7) * w
    ry, rx = random.uniform(0.25, 0.5) * h, random.uniform(0.25, 0.5) * w
    iy = cy + random.uniform(-1, 1) * ry / 3
    ix = cx + random.uniform(-1, 1) * rx / 3
    sy, sx = ry * random.uniform(0.2, 0.4), rx * random.uniform(0.2, 0.4)
    for y in range(h):
      for x in range(w):
        if ((y + 0.5 - cy) / ry) ** 2 + ((x + 0.5 - cx) / rx) ** 2 <= 1:
          g[y][x] = b
          if ((y + 0.5 - iy) / sy) ** 2 + ((x + 0.5 - ix) / sx) ** 2 <= 1:
            g[y][x] = c
  return g


def _sample_legend(side, lw, anchor, h, cw, tile_size, pool, rects, t_cap,
                   hard_tile):
  """Samples one legend whose stamp fits and avoids the stamps in rects."""
  sep = h - 8
  hmax = min(t_cap, sep - 3)
  wmax = min(t_cap, lw - 2)
  if tile_size is not None:
    if tile_size > min(hmax, wmax):
      return None
  elif min(hmax, wmax) < 2:
    return None
  for _ in range(30):
    if tile_size is not None:
      t_h = t_w = tile_size
    elif random.random() < 0.25:
      t_h, t_w = random.randint(2, hmax), random.randint(2, wmax)
    else:
      t_h = t_w = random.randint(2, min(hmax, wmax))
    arrow = random.choice(sorted(_DIRS))
    side_by_side = lw - t_w - 1 >= 2 and random.random() < 0.3
    if not side_by_side and sep - t_h - 1 < 2:
      continue
    dims = None
    for _ in range(40):
      if side_by_side:
        sh = random.randint(2, min(8, sep))
        sw = random.randint(2, lw - t_w - 1)
      else:
        sh = random.randint(2, min(8, sep - t_h - 1))
        sw = random.randint(2, lw)
      if sh * sw < 6:
        continue  # 2x2 masks are never asymmetric
      mh, mw = (sh, sw) if arrow in ('up', 'down') else (sw, sh)
      # Strictly smaller than the canvas on both axes: the anchor matters.
      if mh * t_h >= h or mw * t_w >= cw:
        continue
      rect = _rect(anchor, mh, mw, t_h, t_w, h, cw)
      if any(_overlap(rect, r) for r in rects):
        continue
      dims = (sh, sw)
      break
    if dims is None:
      continue
    sh, sw = dims
    mask = _random_mask(sh, sw, random.random() < 0.35)
    if mask is None:
      continue
    ca, cb = random.sample(pool, 2)
    hard = hard_tile if hard_tile is not None else random.random() < 0.85
    tile = _sample_tile(t_h, t_w, ca, cb, arrow, hard)
    if tile is None:
      continue
    cs = random.choice([c for c in _COLORS if c not in (ca, cb)])
    if side_by_side:
      free_c = lw - t_w - sw - 1
      left = random.randint(0, free_c)
      gap = 1 + random.randint(0, free_c - left)
      tr, sr = random.randint(0, sep - t_h), random.randint(0, sep - sh)
      if random.random() < 0.5:
        tile_pos, shape_pos = (tr, left), (sr, left + t_w + gap)
      else:
        shape_pos, tile_pos = (sr, left), (tr, left + sw + gap)
    else:
      free = sep - t_h - sh - 1
      top = random.randint(0, free)
      gap = 1 + random.randint(0, free - top)
      tile_c = random.randint(0, lw - t_w)
      shape_c = random.randint(0, lw - sw)
      if random.random() < 0.7:
        tile_pos, shape_pos = (top, tile_c), (top + t_h + gap, shape_c)
      else:
        shape_pos, tile_pos = (top, shape_c), (top + sh + gap, tile_c)
    if side == 'left':
      box_col = random.randint(1, lw - 3)
    else:
      box_col = random.randint(0, lw - 4)
    return {'side': side, 'width': lw, 'tile': tile, 'tile_pos': tile_pos,
            'shape': mask, 'shape_color': cs, 'shape_pos': shape_pos,
            'box_col': box_col, 'anchor': anchor, 'arrow': arrow}
  return None


def _sample_scene(height, width, sides, tile_size, canvas, hard_tile):
  if sides is not None:
    if isinstance(sides, str) or not isinstance(sides, (list, tuple)):
      raise ValueError('sides must be a tuple such as ("left",)')
    sides = tuple(sides)
    if (not 1 <= len(sides) <= 2 or
        any(not isinstance(s, str) or s not in ('left', 'right')
            for s in sides) or len(set(sides)) != len(sides)):
      raise ValueError('sides must be ("left",), ("right",) or '
                       '("left", "right")')
  if tile_size is not None and (not _is_int(tile_size) or
                                not 2 <= tile_size <= 5):
    raise ValueError('tile_size must be an integer in 2..5')
  if hard_tile is not None and type(hard_tile) is not bool:
    raise ValueError('hard_tile must be None, True or False')
  if height is not None and not _is_int(height):
    raise ValueError('height must be an integer')
  if width is not None and not _is_int(width):
    raise ValueError('width must be an integer')
  t_min = 2 if tile_size is None else tile_size
  lo_w = max(4, t_min + 2)
  hmin = t_min + 11
  cw_min = max(lo_w + 2, 2 * t_min + 1)
  pool0 = None
  cw_fixed = None
  if canvas is not None:
    err = _check_canvas(canvas)
    if err:
      raise ValueError(err)
    if height is not None and height != len(canvas):
      raise ValueError('height disagrees with the supplied canvas')
    height = len(canvas)
    cw_fixed = len(canvas[0])
    used_cols = {v for r in canvas for v in r}
    pool0 = [c for c in _COLORS if c not in used_cols]
  if height is not None and not hmin <= height <= 30:
    raise ValueError('height must be in %d..30 for these controls' % hmin)
  if width is not None and not 11 <= width <= 30:
    raise ValueError('width must be an integer in 11..30')
  w_hi = 7 if canvas is None else min(7, cw_fixed - 2)

  def feasible(sd):
    n = len(sd)
    if n == 2 and tile_size == 5:
      return False
    if pool0 is not None and len(pool0) < 2 * n:
      return False
    lo_used = n * (lo_w + 1)
    if canvas is not None:
      if cw_fixed < cw_min or w_hi < lo_w or cw_fixed + lo_used > 30:
        return False
      if width is not None and not (
          lo_used <= width - cw_fixed <= n * (w_hi + 1)):
        return False
      return True
    return lo_used + cw_min <= (30 if width is None else width)

  candidates = [sides] if sides is not None else list(_SIDE_CHOICES)
  choices = [sd for sd in candidates if feasible(sd)]
  if not choices:
    raise ValueError('no legend layout fits these controls (check width, '
                     'sides, tile_size and canvas size/colours)')
  for attempt in range(400):
    # After many failures, favour the roomiest layout: narrowest legends
    # and the widest canvas. Tight control combinations need it.
    late = attempt >= 200
    h = height if height is not None else random.randint(max(13, hmin), 30)
    sd = random.choice(choices)
    n = len(sd)
    t_cap = 5 if n == 1 else 4
    if canvas is not None and width is not None:
      target = width - cw_fixed - n
      opts = [ws for ws in itertools.product(range(lo_w, w_hi + 1),
                                             repeat=n) if sum(ws) == target]
      if not opts:
        continue
      widths = list(random.choice(opts))
    elif late and random.random() < 0.7:
      widths = [lo_w] * n
    else:
      widths = [random.randint(lo_w, w_hi) for _ in sd]
    used = sum(x + 1 for x in widths)
    if canvas is not None:
      cw = cw_fixed
    else:
      need = used + max(max(widths) + 2, cw_min)
      if need > 30 or (width is not None and width < need):
        continue
      if width is not None:
        w = width
      elif late and random.random() < 0.5:
        w = 30
      else:
        w = random.randint(max(18, need), 30)
      cw = w - used
    if cw < max(widths) + 2 or cw < cw_min or cw + used > 30:
      continue
    base = [list(r) for r in (canvas if canvas is not None
                              else _random_canvas(h, cw))]
    base_cols = {v for r in base for v in r}
    pool = [c for c in _COLORS if c not in base_cols]
    if len(pool) < 2 * n:
      continue
    anchors = random.sample(sorted(_CORNERS), n)
    legends, rects = [], []
    for side, lw, anchor in zip(sd, widths, anchors):
      leg = _sample_legend(side, lw, anchor, h, cw, tile_size, pool, rects,
                           t_cap, hard_tile)
      if leg is None:
        break
      legends.append(leg)
      tile_cols = {v for r in leg['tile'] for v in r}
      pool = [c for c in pool if c not in tile_cols]
      rects.append(_stamp_rect(leg, h, cw))
    if len(legends) != n:
      continue
    if _check_scene(legends, base) is not None:
      continue
    out = [list(r) for r in base]
    for leg in legends:
      _stamp(out, leg)
    if out == base:
      continue
    return legends, base
  raise RuntimeError('could not sample a scene for the requested controls')


def _render(legends, canvas):
  legends = sorted(legends, key=lambda l: 0 if l['side'] == 'left' else 1)
  h = len(canvas)
  blocks = [(l['side'], _legend_block(l, h)) for l in legends]
  grid = []
  for y in range(h):
    row = []
    for side, blk in blocks:
      if side == 'left':
        row += blk[y] + [6]
    row += list(canvas[y])
    for side, blk in blocks:
      if side == 'right':
        row += [6] + blk[y]
    grid.append(row)
  out = [list(r) for r in canvas]
  for leg in legends:
    _stamp(out, leg)
  return {'input': grid, 'output': out}


def generate(legends=None, canvas=None, height=None, width=None, sides=None,
             tile_size=None, hard_tile=None):
  """Build one input/output pair.

  Args:
    legends: optional list of one or two legend dicts with these keys.
      side: "left" or "right"; the sides must be distinct.
      width: int >= 4.
      tile: rows with exactly two colours; may be rectangular.
      tile_pos: (r, c).
      shape: tight 8-connected 0/1 mask rows.
      shape_color: must not be a tile colour.
      shape_pos: (r, c).
      box_col: start of the 3-wide box interior. Use 1..width-3 on the left
        and 0..width-4 on the right, so each box is framed by 6.
      anchor: "tl", "tr", "bl" or "br".
      arrow: "up", "down", "left" or "right".
      Positions are relative to the legend strip. The objects must lie above
      the separator row, and the tile must lie outside the shape bounding
      box. The stamps must change at least one canvas cell.
    canvas: optional canvas rows (no colour 6). Its row count is the grid
      height, and the separator row is height - 8. If legends is None,
      random legends are fitted around this canvas, with tile colours chosen
      outside the canvas palette.
    height, width: optional integer total grid size (plain int). They are
      used for random sampling, or with explicit legends when no canvas is
      supplied. If they are given together with a canvas, they must agree
      with it.
    sides: optional random-sampling control: ("left",), ("right",) or
      ("left", "right").
    tile_size: optional random-sampling control that forces a square tile
      side of 2..5. Side 5 needs a single legend.
    hard_tile: optional random-sampling control. True forces tiles whose
      colour swap is not a D4 image of the tile and which change under the
      arrow rotation. False allows any two-colour tile. None picks hard
      tiles with probability 0.85 per legend.
    sides, tile_size and hard_tile cannot be combined with explicit legends.
  """
  if legends is None:
    legends, canvas = _sample_scene(height, width, sides, tile_size, canvas,
                                    hard_tile)
    return _render(legends, canvas)
  if sides is not None or tile_size is not None or hard_tile is not None:
    raise ValueError('sides/tile_size/hard_tile only control random '
                     'sampling; omit them when legends are given')
  err = _check_keys(legends)
  if err:
    raise ValueError(err)
  if height is not None and not _is_int(height):
    raise ValueError('height must be an integer')
  if width is not None and not _is_int(width):
    raise ValueError('width must be an integer')
  used = sum(l['width'] + 1 for l in legends)
  if canvas is None:
    if height is None or width is None:
      raise ValueError('explicit legends need a canvas or both height and '
                       'width')
    if not 9 <= height <= 30 or width > 30:
      raise ValueError('height must be 9..30 and width at most 30')
    cw = width - used
    if cw <= max(l['width'] for l in legends):
      raise ValueError('width leaves no canvas wider than every legend')
    for leg in legends:
      err = _check_legend(leg, height, cw)
      if err:
        raise ValueError(err)
    avoid = set()
    for leg in legends:
      avoid |= {v for r in leg['tile'] for v in r}
    canvas = _random_canvas(height, cw, avoid)
  else:
    err = _check_canvas(canvas)
    if err:
      raise ValueError(err)
    if height is not None and height != len(canvas):
      raise ValueError('height disagrees with the supplied canvas')
    if width is not None and width != len(canvas[0]) + used:
      raise ValueError('width disagrees with the canvas and legends')
  err = _check_scene(legends, canvas)
  if err:
    raise ValueError(err)
  pair = _render(legends, canvas)
  if pair['output'] == [list(r) for r in canvas]:
    raise ValueError('the stamps leave the canvas unchanged, so the pair '
                     'would not show the rule')
  return pair


def _rle(spec):
  rows = []
  for count, runs in spec:
    row = []
    for color, n in runs:
      row += [color] * n
    for _ in range(count):
      rows.append(row[:])
  return rows


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  c1 = _rle([
      (1, [(5, 5), (3, 17), (5, 2)]), (1, [(5, 4), (3, 20)]),
      (1, [(5, 3), (3, 21)]), (1, [(5, 3), (3, 8), (8, 9), (3, 4)]),
      (1, [(5, 3), (3, 6), (8, 13), (3, 2)]),
      (1, [(5, 2), (3, 5), (8, 16), (3, 1)]),
      (1, [(5, 2), (3, 4), (8, 17), (3, 1)]),
      (1, [(5, 2), (3, 3), (8, 18), (3, 1)]),
      (1, [(5, 1), (3, 4), (8, 7), (1, 3), (8, 8), (3, 1)]),
      (3, [(5, 1), (3, 3), (8, 7), (1, 4), (8, 8), (3, 1)]),
      (1, [(5, 1), (3, 3), (8, 8), (1, 2), (8, 9), (3, 1)]),
      (1, [(5, 1), (3, 3), (8, 18), (3, 2)]),
      (1, [(5, 1), (3, 4), (8, 17), (3, 2)]),
      (1, [(5, 2), (3, 3), (8, 16), (3, 3)]),
      (1, [(5, 3), (3, 3), (8, 14), (3, 4)]),
      (1, [(5, 3), (3, 4), (8, 11), (3, 5), (5, 1)]),
      (1, [(5, 3), (3, 19), (5, 2)]), (1, [(5, 4), (3, 17), (5, 3)])])
  c2 = _rle([(20, [(8, 5), (9, 5), (8, 5), (9, 5), (8, 4)])])
  c3 = _rle([(5, [(5, 24)]), (5, [(4, 24)]), (5, [(5, 24)]), (5, [(4, 24)])])
  c4 = _rle([(13, [(9, 8), (0, 4), (9, 8)]), (4, [(0, 20)]),
             (13, [(9, 8), (0, 4), (9, 8)])])
  c5 = _rle([(5, [(4, 22)]), (8, [(1, 22)]), (9, [(4, 22)]), (8, [(1, 22)])])
  train = [
      generate(legends=[{
          'side': 'left', 'width': 5,
          'tile': [[7, 7, 7], [7, 7, 4], [7, 4, 7]], 'tile_pos': (1, 1),
          'shape': [[1, 1, 1, 0, 0], [0, 0, 1, 0, 0], [0, 0, 1, 0, 0],
                    [0, 1, 1, 1, 0], [1, 1, 1, 1, 1], [1, 0, 1, 0, 1]],
          'shape_color': 1, 'shape_pos': (6, 0), 'box_col': 1,
          'anchor': 'br', 'arrow': 'down'}], canvas=c1),
      generate(legends=[{
          'side': 'left', 'width': 5,
          'tile': [[1, 1, 2], [1, 1, 1], [2, 1, 2]], 'tile_pos': (1, 1),
          'shape': [[1, 0, 1], [0, 1, 0], [0, 1, 0], [1, 0, 1], [1, 0, 1],
                    [0, 1, 0]],
          'shape_color': 4, 'shape_pos': (5, 1), 'box_col': 1,
          'anchor': 'tl', 'arrow': 'up'}], canvas=c2),
      generate(legends=[{
          'side': 'left', 'width': 5,
          'tile': [[3, 3, 3], [8, 3, 8], [8, 3, 3]], 'tile_pos': (1, 1),
          'shape': [[1, 1, 1], [1, 0, 0], [1, 1, 1], [0, 0, 1], [0, 0, 1]],
          'shape_color': 2, 'shape_pos': (6, 1), 'box_col': 1,
          'anchor': 'tr', 'arrow': 'right'}], canvas=c3),
  ]
  test = [
      generate(legends=[{
          'side': 'left', 'width': 4,
          'tile': [[1, 1], [1, 3]], 'tile_pos': (1, 1),
          'shape': [[0, 1, 0, 0], [1, 1, 0, 0], [1, 0, 0, 1], [1, 1, 1, 1],
                    [0, 1, 0, 0], [0, 1, 1, 1], [0, 0, 0, 1], [0, 1, 1, 1]],
          'shape_color': 7, 'shape_pos': (9, 0), 'box_col': 1,
          'anchor': 'br', 'arrow': 'up'}, {
          'side': 'right', 'width': 4,
          'tile': [[2, 4], [4, 2]], 'tile_pos': (2, 1),
          'shape': [[0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1], [1, 1, 1, 1],
                    [1, 0, 1, 0], [1, 1, 1, 1]],
          'shape_color': 3, 'shape_pos': (6, 0), 'box_col': 0,
          'anchor': 'tl', 'arrow': 'down'}], canvas=c4),
      generate(legends=[{
          'side': 'left', 'width': 7,
          'tile': [[2, 2, 2, 2, 2], [2, 3, 3, 3, 3], [2, 2, 2, 2, 2],
                   [3, 3, 3, 3, 2], [2, 2, 2, 2, 2]], 'tile_pos': (1, 1),
          'shape': [[1, 1, 1, 1, 1], [1, 1, 0, 0, 1], [1, 0, 0, 0, 1],
                    [1, 1, 1, 0, 0]],
          'shape_color': 4, 'shape_pos': (12, 1), 'box_col': 2,
          'anchor': 'bl', 'arrow': 'left'}], canvas=c5),
  ]
  return {'train': train, 'test': test}
