# Copyright 2026 Ritwika Kancharla
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0; you may not use this file
# except in compliance with the License. You may obtain a copy of the License
# at http://www.apache.org/licenses/LICENSE-2.0

"""Generator for ARC task fc7cae8d.

Rule: two adjacent borders of the grid carry full edge lines in two distinct
colours. Each edge line has a ragged fringe of its own colour, 0..2 cells deep.
The other two borders carry dotted grey (5) lines.

One rectangle sits inside the grid. Two of its adjacent sides each carry a
marker line, and the marker colours match the two edge-line colours. The
output is the rectangle without the markers, with any 0 bites kept as 0.

The rectangle is re-oriented by the one transform, out of the 8 rotations and
reflections, that sends each marker side to the border side of the same
colour. Both markers are needed: one marker alone cannot tell a rotation from
a reflection. Train pair 1 needs the anti-transpose.

Scope:
  * Default random grid sizes are 14..30 per side, either independent or
    square. Explicit sizes 12..30 are accepted. Sizes other than the fixture
    sizes (22 and 29) are synthetic extensions of the same layout.
  * All four corner placements of the full edge lines are sampled. All eight
    output orientations are sampled, so the markers can sit on any adjacent
    pair of rectangle sides.
  * Rectangle size, position and fill are random. The rectangle uses 1..4
    glyph colours.
  * Interior glyph kinds are segments, dashes, blobs, small hollow boxes,
    period-2 bar bands and L-shaped lines. Large rectangles get up to 8
    pieces. Some glyphs may run onto the rectangle's own border ring, as in
    the test fixture.
  * Edge bites (0 holes) appear only on the two non-marker sides. They are 1
    or 2 deep, and sometimes stepped. In random scenes a bite never covers a
    corner cell shared with a marker side, which matches all fixtures.
  * Fringe depth is 0..2. Endpoint fringe cells may reach a neighbouring
    border line. The test fixture shows this for the horizontal line; the
    vertical-line case is a synthetic extension. Grey dots are occasionally
    two deep.
  * Random and explicit scenes are rejected when the cropped rectangle has
    any dihedral symmetry, so no wrong rotation or reflection can reproduce
    the answer.
  * Not supported: more than one rectangle, distractor objects in the open
    field, markers on opposite sides, or grey used as an edge colour.
"""

import collections
import random

import common

_PALETTE = (1, 2, 3, 4, 6, 7, 8, 9)
_DOT = 5
_FLIP = {0: 0, 1: 3, 2: 2, 3: 1}
_MIN_SIZE, _MAX_SIZE = 12, 30
_MIN_AREA = 12
_N4 = ((0, 1), (0, -1), (1, 0), (-1, 0))
_N8 = tuple((dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1))


def _is_int(value):
  """True for genuine ints (bools are rejected)."""
  return isinstance(value, int) and not isinstance(value, bool)


def _side_map(flip, turns, side):
  """Side (0 top, 1 right, 2 bottom, 3 left) after fliplr then CCW turns."""
  if flip:
    side = _FLIP[side]
  return (side - turns) % 4


def _preimage(flip, turns, side):
  return [s for s in range(4) if _side_map(flip, turns, s) == side][0]


def _orientation(hside, vside, hmark, vmark):
  for flip in (False, True):
    for turns in range(4):
      if (_side_map(flip, turns, hmark) == hside and
          _side_map(flip, turns, vmark) == vside):
        return flip, turns
  raise ValueError('marker sides are not compatible with the edge sides')


def _orient(rows, flip, turns):
  out = [list(row) for row in rows]
  if flip:
    out = [row[::-1] for row in out]
  for _ in range(turns):
    out = [list(row) for row in zip(*out)][::-1]
  return out


def _asymmetric(rows, flip, turns):
  """True if no other orientation reproduces the chosen output."""
  chosen = _orient(rows, flip, turns)
  for f in (False, True):
    for k in range(4):
      if (f, k) != (flip, turns) and _orient(rows, f, k) == chosen:
        return False
  return True


def _marker_cells(side, top, left, rh, rw):
  if side == 0:
    return [(top - 1, left + c) for c in range(rw)]
  if side == 2:
    return [(top + rh, left + c) for c in range(rw)]
  if side == 3:
    return [(top + r, left - 1) for r in range(rh)]
  return [(top + r, left + rw) for r in range(rh)]


def _draw_border(height, width, hside, vside, hcolor, vcolor, hfringe,
                 vfringe, hdots, vdots):
  """Draws the dotted borders, edge lines and fringes on a blank grid."""
  g = common.grid(width, height, 0)
  dside = 4 - vside
  for y in range(height):
    for e in range(int(vdots[y])):
      g[y][e if dside == 3 else width - 1 - e] = _DOT
  dside = 2 - hside
  for x in range(width):
    for e in range(int(hdots[x])):
      g[e if dside == 0 else height - 1 - e][x] = _DOT
  vx, step = (0, 1) if vside == 3 else (width - 1, -1)
  for y in range(height):
    g[y][vx] = vcolor
    for e in range(1, int(vfringe[y]) + 1):
      g[y][vx + step * e] = vcolor
  hy, step = (0, 1) if hside == 0 else (height - 1, -1)
  for x in range(width):
    g[hy][x] = hcolor
    for e in range(1, int(hfringe[x]) + 1):
      g[hy + step * e][x] = hcolor
  return g


def _build(height, width, hside, vside, hcolor, vcolor, hfringe, vfringe,
           hdots, vdots, top, left, rect, hmark, vmark):
  """Draws the scene from latent parameters and derives the answer."""
  g = _draw_border(height, width, hside, vside, hcolor, vcolor, hfringe,
                   vfringe, hdots, vdots)
  crop = [[int(v) for v in row] for row in rect]
  rh, rw = len(crop), len(crop[0])
  for r in range(rh):
    for c in range(rw):
      g[top + r][left + c] = crop[r][c]
  for side, color in ((hmark, hcolor), (vmark, vcolor)):
    for y, x in _marker_cells(side, top, left, rh, rw):
      g[y][x] = color
  flip, turns = _orientation(hside, vside, hmark, vmark)
  return {'input': g, 'output': _orient(crop, flip, turns)}


def _fringe(length):
  density = random.uniform(0.15, 0.4)
  chars = []
  for i in range(length):
    if i in (0, length - 1):
      chars.append('1' if random.random() < 0.15 else '0')
    elif random.random() < density:
      chars.append('2' if random.random() < 0.15 else '1')
    else:
      chars.append('0')
  return ''.join(chars)


def _dots(length):
  chars = ['0'] * length
  for _ in range(50):
    density = random.uniform(0.3, 0.55)
    chars = []
    for i in range(length):
      if random.random() < density:
        deep = 2 <= i <= length - 3 and random.random() < 0.05
        chars.append('2' if deep else '1')
      else:
        chars.append('0')
    if sum(1 for c in chars[1:-1] if c != '0') >= 5:
      return ''.join(chars)
  for i in random.sample(range(1, length - 1), 5):
    chars[i] = '1'
  return ''.join(chars)


def _paint_content(rows, rh, rw, colors):
  """Paints random glyphs of the given colours onto the rect rows."""
  area = max(1, (rh - 2) * (rw - 2))
  count = random.randint(1, min(8, 1 + area // 10))
  for _ in range(count):
    if random.random() < 0.3:
      r0, r1, c0, c1 = 0, rh - 1, 0, rw - 1
    else:
      r0, r1, c0, c1 = 1, rh - 2, 1, rw - 2
    ih, iw = r1 - r0 + 1, c1 - c0 + 1
    color = random.choice(colors)
    kind = random.choice(('seg', 'seg', 'dash', 'blob', 'box', 'bars',
                          'ell'))
    horizontal = random.random() < 0.5
    span = iw if horizontal else ih
    perp = ih if horizontal else iw
    if kind == 'box' and ih >= 3 and iw >= 3:
      bh = random.randint(3, min(5, ih))
      bw = random.randint(3, min(5, iw))
      y = random.randint(r0, r1 - bh + 1)
      x = random.randint(c0, c1 - bw + 1)
      for r in range(bh):
        for c in range(bw):
          if r in (0, bh - 1) or c in (0, bw - 1):
            rows[y + r][x + c] = color
    elif kind == 'blob':
      cells = [(random.randint(r0, r1), random.randint(c0, c1))]
      size = random.randint(2, 6)
      for _ in range(40):
        if len(cells) >= size:
          break
        cy, cx = random.choice(cells)
        dy, dx = random.choice(_N4)
        ny, nx = cy + dy, cx + dx
        if r0 <= ny <= r1 and c0 <= nx <= c1 and (ny, nx) not in cells:
          cells.append((ny, nx))
      for cy, cx in cells:
        rows[cy][cx] = color
    elif kind == 'bars':
      thick = 2 if perp >= 2 and random.random() < 0.7 else 1
      length = random.randint(min(3, span), span)
      if horizontal:
        y = random.randint(r0, r1 - thick + 1)
        x = random.randint(c0, c1 - length + 1)
        for t in range(0, length, 2):
          for d in range(thick):
            rows[y + d][x + t] = color
      else:
        y = random.randint(r0, r1 - length + 1)
        x = random.randint(c0, c1 - thick + 1)
        for t in range(0, length, 2):
          for d in range(thick):
            rows[y + t][x + d] = color
    elif kind == 'ell':
      y = random.randint(r0, r1)
      x = random.randint(c0, c1)
      dy = random.choice((-1, 1))
      dx = random.choice((-1, 1))
      ylim = (r1 - y) if dy > 0 else (y - r0)
      xlim = (c1 - x) if dx > 0 else (x - c0)
      a = random.randint(0, ylim)
      b = random.randint(0, xlim)
      for t in range(a + 1):
        rows[y + dy * t][x] = color
      for t in range(b + 1):
        rows[y][x + dx * t] = color
    else:
      length = random.randint(min(2, span), span)
      gap = 2 if (kind == 'dash' and length >= 3) else 1
      if horizontal:
        y = random.randint(r0, r1)
        x = random.randint(c0, c1 - length + 1)
        for t in range(0, length, gap):
          rows[y][x + t] = color
      else:
        y = random.randint(r0, r1 - length + 1)
        x = random.randint(c0, c1)
        for t in range(0, length, gap):
          rows[y + t][x] = color


def _bites(rh, rw, sides, marks):
  """Returns bite holes on the given sides, avoiding marker-side corners."""
  holes = set()
  for side in sides:
    if random.random() >= 0.6:
      continue
    if side in (0, 2):
      side_len, perp, ends = rw, rh, (3, 1)
    else:
      side_len, perp, ends = rh, rw, (0, 2)
    lo = 1 if ends[0] in marks else 0
    hi = side_len - 2 if ends[1] in marks else side_len - 1
    if hi < lo:
      continue
    for _ in range(random.randint(1, 2)):
      length = random.randint(1, max(1, (hi - lo + 1) // 3))
      start = random.randint(lo, hi - length + 1)
      deep = perp >= 5 and random.random() < 0.3
      stepped = deep and length >= 3 and random.random() < 0.6
      for t in range(start, start + length):
        if stepped:
          depth = 1 if t in (start, start + length - 1) else 2
        else:
          depth = 2 if deep else 1
        for e in range(depth):
          if side == 0:
            holes.add((e, t))
          elif side == 2:
            holes.add((rh - 1 - e, t))
          elif side == 3:
            holes.add((t, e))
          else:
            holes.add((t, rw - 1 - e))
  return holes


def _connected(cells):
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  todo = [start]
  while todo:
    y, x = todo.pop()
    for dy, dx in _N4:
      n = (y + dy, x + dx)
      if n in cells and n not in seen:
        seen.add(n)
        todo.append(n)
  return len(seen) == len(cells)


def _ring_ok(rows):
  """Every border row and column of the rect has a non-zero cell."""
  return bool(any(rows[0]) and any(rows[-1]) and
              any(row[0] for row in rows) and any(row[-1] for row in rows))


def _rect_connected(rows, marks):
  rh, rw = len(rows), len(rows[0])
  cells = {(r, c) for r in range(rh) for c in range(rw) if rows[r][c]}
  for side in marks:
    cells.update(_marker_cells(side, 0, 0, rh, rw))
  return _connected(cells)


def _make_rect(rh, rw, fill, colors, hole_sides, marks):
  for _ in range(40):
    rows = [[fill] * rw for _ in range(rh)]
    _paint_content(rows, rh, rw, colors)
    for r, c in _bites(rh, rw, hole_sides, marks):
      rows[r][c] = 0
    if sum(1 for row in rows for v in row if v not in (0, fill)) < 2:
      continue
    if not _ring_ok(rows):
      continue
    if _rect_connected(rows, marks):
      return rows
  return None


def _scene_ok(g, hside, vside, hcolor, vcolor):
  h, w = len(g), len(g[0])
  lines = {0: g[0], 1: [row[w - 1] for row in g], 2: g[h - 1],
           3: [row[0] for row in g]}
  expected = {hside: hcolor, vside: vcolor, 2 - hside: _DOT, 4 - vside: _DOT}
  for side, line in lines.items():
    common_vals = collections.Counter(v for v in line if v).most_common(2)
    if not common_vals or common_vals[0][0] != expected[side]:
      return False
    if len(common_vals) > 1 and common_vals[1][1] == common_vals[0][1]:
      return False
  totals = collections.Counter(v for row in g for v in row)
  return all(n < totals[0] for v, n in totals.items() if v != 0)


def _random_scene(height, width, hside, vside, hcolor, vcolor, hmark, vmark):
  for _ in range(300):
    hgt = height if height is not None else random.randint(14, _MAX_SIZE)
    if width is not None:
      wid = width
    elif height is None and random.random() < 0.4:
      wid = hgt
    else:
      wid = random.randint(14, _MAX_SIZE)
    hs = hside if hside is not None else random.choice((0, 2))
    vs = vside if vside is not None else random.choice((1, 3))
    hc = hcolor if hcolor is not None else random.choice(
        [c for c in _PALETTE if c != vcolor])
    vc = vcolor if vcolor is not None else random.choice(
        [c for c in _PALETTE if c != hc])
    remaining = [c for c in _PALETTE if c not in (hc, vc)]
    fill = random.choice(remaining)
    rest = [c for c in remaining if c != fill]
    content = random.sample(rest, random.randint(1, min(4, len(rest))))
    hfr, vfr = _fringe(wid), _fringe(hgt)
    hdt, vdt = _dots(wid), _dots(hgt)
    options = []
    for flip in (False, True):
      for turns in range(4):
        hm, vm = _preimage(flip, turns, hs), _preimage(flip, turns, vs)
        if ((hmark is None or hm == hmark) and
            (vmark is None or vm == vmark)):
          options.append((hm, vm))
    if not options:
      raise ValueError('hmark/vmark incompatible with the edge sides')
    hmk, vmk = random.choice(options)
    margin = {hs: max(int(c) for c in hfr) + 2,
              vs: max(int(c) for c in vfr) + 2,
              2 - hs: max(2, max(int(c) for c in hdt) + 1),
              4 - vs: max(2, max(int(c) for c in vdt) + 1)}
    avail_h = hgt - margin[0] - margin[2]
    avail_w = wid - margin[1] - margin[3]
    if avail_h < 4 or avail_w < 4:
      continue
    rh = random.randint(3, avail_h - 1)
    lo = max(3, -(-_MIN_AREA // rh))
    if lo > avail_w - 1:
      continue
    rw = random.randint(lo, avail_w - 1)
    if rh * rw > 0.35 * hgt * wid:
      continue
    vert_mark = hmk if hmk in (0, 2) else vmk
    horz_mark = vmk if vmk in (1, 3) else hmk
    y0 = random.randint(margin[0], hgt - margin[2] - rh - 1)
    x0 = random.randint(margin[3], wid - margin[1] - rw - 1)
    top = y0 + (1 if vert_mark == 0 else 0)
    left = x0 + (1 if horz_mark == 3 else 0)
    hole_sides = [s for s in range(4) if s not in (hmk, vmk)]
    rect = _make_rect(rh, rw, fill, content, hole_sides, (hmk, vmk))
    if rect is None:
      continue
    flip, turns = _orientation(hs, vs, hmk, vmk)
    if not _asymmetric(rect, flip, turns):
      continue
    pair = _build(hgt, wid, hs, vs, hc, vc, hfr, vfr, hdt, vdt, top, left,
                  rect, hmk, vmk)
    if _scene_ok(pair['input'], hs, vs, hc, vc):
      return pair
  raise RuntimeError('could not construct a valid scene')


def _check_random_args(height, width, hside, vside, hcolor, vcolor, hmark,
                       vmark):
  for name, value in (('height', height), ('width', width)):
    if value is not None and (not _is_int(value) or
                              not _MIN_SIZE <= value <= _MAX_SIZE):
      raise ValueError('%s must be an int in %d..%d' %
                       (name, _MIN_SIZE, _MAX_SIZE))
  if hside is not None and (not _is_int(hside) or hside not in (0, 2)):
    raise ValueError('hside must be 0 (top) or 2 (bottom)')
  if vside is not None and (not _is_int(vside) or vside not in (1, 3)):
    raise ValueError('vside must be 1 (right) or 3 (left)')
  for name, value in (('hcolor', hcolor), ('vcolor', vcolor)):
    if value is not None and (not _is_int(value) or value not in _PALETTE):
      raise ValueError('%s must be one of %s' % (name, _PALETTE))
  if hcolor is not None and hcolor == vcolor:
    raise ValueError('hcolor and vcolor must differ')
  for name, value in (('hmark', hmark), ('vmark', vmark)):
    if value is not None and (not _is_int(value) or
                              value not in (0, 1, 2, 3)):
      raise ValueError('%s must be a side 0..3' % name)
  if hmark is not None and vmark is not None and (hmark - vmark) % 2 != 1:
    raise ValueError('hmark and vmark must be adjacent rectangle sides')


def _depths(name, seq, n):
  """Normalises a depth string or int sequence to a list of ints 0..2."""
  if isinstance(seq, str):
    if len(seq) != n or any(ch not in '012' for ch in seq):
      raise ValueError('%s must be %d digits 0..2' % (name, n))
    return [int(ch) for ch in seq]
  try:
    values = list(seq)
  except TypeError:
    raise ValueError('%s must be a string or sequence' % name)
  if len(values) != n or any(not _is_int(v) or v not in (0, 1, 2)
                             for v in values):
    raise ValueError('%s must be %d ints 0..2' % (name, n))
  return values


def _rect_rows(rect):
  """Normalises rect rows (digit strings or int lists) to int lists."""
  if isinstance(rect, str):
    raise ValueError('rect must be a sequence of rows')
  rows = []
  try:
    for row in rect:
      if isinstance(row, str):
        if any(ch not in '0123456789' for ch in row):
          raise ValueError('rect rows must contain digits 0..9')
        rows.append([int(ch) for ch in row])
      else:
        vals = list(row)
        if any(not _is_int(v) or not 0 <= v <= 9 for v in vals):
          raise ValueError('rect values must be ints 0..9')
        rows.append(vals)
  except TypeError:
    raise ValueError('rect must be a sequence of rows')
  if not rows or not rows[0] or any(len(r) != len(rows[0]) for r in rows):
    raise ValueError('rect must be a non-empty rectangle')
  return rows


def _check_explicit(height, width, hside, vside, hcolor, vcolor, hfringe,
                    vfringe, hdots, vdots, top, left, rect, hmark, vmark):
  """Validates explicit latent arguments; returns normalised sequences."""
  _check_random_args(height, width, hside, vside, hcolor, vcolor, hmark,
                     vmark)
  hfr = _depths('hfringe', hfringe, width)
  vfr = _depths('vfringe', vfringe, height)
  hdt = _depths('hdots', hdots, width)
  vdt = _depths('vdots', vdots, height)
  rows = _rect_rows(rect)
  if not _is_int(top) or not _is_int(left):
    raise ValueError('top and left must be ints')
  rh, rw = len(rows), len(rows[0])
  if any(v in (hcolor, vcolor, _DOT) for row in rows for v in row):
    raise ValueError('rect may not use the edge colours or grey 5')
  if not _ring_ok(rows):
    raise ValueError('every rect border row and column needs a non-zero cell')
  if not _rect_connected(rows, (hmark, vmark)):
    raise ValueError('rect plus markers must be 4-connected')
  flip, turns = _orientation(hside, vside, hmark, vmark)
  if not _asymmetric(rows, flip, turns):
    raise ValueError('rect is symmetric, so the orientation is unobservable')
  cells = [(top + r, left + c) for r in range(rh) for c in range(rw)]
  for side in (hmark, vmark):
    cells.extend(_marker_cells(side, top, left, rh, rw))
  for y, x in cells:
    if not (1 <= y <= height - 2 and 1 <= x <= width - 2):
      raise ValueError('rect and markers must lie strictly inside the grid')
  border = _draw_border(height, width, hside, vside, hcolor, vcolor, hfr,
                        vfr, hdt, vdt)
  for y, x in cells:
    for dy, dx in _N8:
      ny, nx = y + dy, x + dx
      if 0 <= ny < height and 0 <= nx < width and border[ny][nx]:
        raise ValueError('rect must keep a one-cell gap from the borders')
  return hfr, vfr, hdt, vdt, rows


def generate(height=None, width=None, hside=None, vside=None, hcolor=None,
             vcolor=None, hfringe=None, vfringe=None, hdots=None, vdots=None,
             top=None, left=None, rect=None, hmark=None, vmark=None):
  """Returns an input/output pair for task fc7cae8d.

  If rect is None, a fresh random scene is built. In that case height, width,
  hside, vside, hcolor, vcolor, hmark and vmark are honoured when given.
  hfringe, vfringe, hdots, vdots, top and left are rejected, because they
  need an explicit rect.

  If rect is given, every argument must be supplied. The arguments are
  validated (types, sizes, sides, colours, lengths, bounds, border gap,
  connectivity, asymmetry, border-line majorities), and the scene is drawn
  exactly from them.

  Args:
    height: grid height in rows (int 12..30).
    width: grid width in columns (int 12..30).
    hside: border of the full horizontal edge line (0 top, 2 bottom).
    vside: border of the full vertical edge line (1 right, 3 left).
    hcolor: colour of the full horizontal edge line (not 0 or 5).
    vcolor: colour of the full vertical edge line (not 0, 5 or hcolor).
    hfringe: per-column fringe depth (0..2) beside the horizontal line.
    vfringe: per-row fringe depth (0..2) beside the vertical line.
    hdots: per-column grey dot depth (0..2) on the opposite horizontal border.
    vdots: per-row grey dot depth (0..2) on the opposite vertical border.
    top: row of the rectangle's top-left cell.
    left: column of the rectangle's top-left cell.
    rect: rectangle rows as digit strings or int lists (0 = bite hole).
    hmark: rectangle side holding the hcolor marker line (0..3).
    vmark: rectangle side holding the vcolor marker line (0..3).
  """
  if rect is not None:
    named = (('height', height), ('width', width), ('hside', hside),
             ('vside', vside), ('hcolor', hcolor), ('vcolor', vcolor),
             ('hfringe', hfringe), ('vfringe', vfringe), ('hdots', hdots),
             ('vdots', vdots), ('top', top), ('left', left),
             ('hmark', hmark), ('vmark', vmark))
    missing = [name for name, value in named if value is None]
    if missing:
      raise ValueError('explicit rect requires: ' + ', '.join(missing))
    hfr, vfr, hdt, vdt, rows = _check_explicit(
        height, width, hside, vside, hcolor, vcolor, hfringe, vfringe, hdots,
        vdots, top, left, rect, hmark, vmark)
    pair = _build(height, width, hside, vside, hcolor, vcolor, hfr, vfr, hdt,
                  vdt, top, left, rows, hmark, vmark)
    if not _scene_ok(pair['input'], hside, vside, hcolor, vcolor):
      raise ValueError('border lines or background majority are ambiguous')
    return pair
  layout = (('hfringe', hfringe), ('vfringe', vfringe), ('hdots', hdots),
            ('vdots', vdots), ('top', top), ('left', left))
  given = [name for name, value in layout if value is not None]
  if given:
    raise ValueError('these arguments require an explicit rect: ' +
                     ', '.join(given))
  _check_random_args(height, width, hside, vside, hcolor, vcolor, hmark,
                     vmark)
  return _random_scene(height, width, hside, vside, hcolor, vcolor, hmark,
                       vmark)


def validate():
  """Reconstructs the canonical fixtures through explicit latent arguments."""
  train = [
      generate(height=22, width=22, hside=0, vside=3, hcolor=4, vcolor=6,
               hfringe='0010001100000001001000',
               vfringe='0000011000100000101000',
               hdots='0011000101011000110011',
               vdots='0101101001010000110011',
               top=4, left=4, hmark=1, vmark=2,
               rect=['11111110111', '01111118111', '11111118111',
                     '00111118111', '00111118111', '11111118111',
                     '11111118111', '11111118111', '11111118111',
                     '11111228221', '11111211111', '18888811131',
                     '11111211131', '11111213331', '11111111111']),
      generate(height=22, width=22, hside=2, vside=1, hcolor=3, vcolor=1,
               hfringe='0100011000010001011000',
               vfringe='0010010000011001000000',
               hdots='1101001000110100010110',
               vdots='1010101101001000010100',
               top=6, left=4, hmark=3, vmark=2,
               rect=['2222222222', '2422222882', '2222222222',
                     '2222222222', '2222222222', '2222222222',
                     '2424442442', '2424242422', '2444244422',
                     '2222222222']),
      generate(height=22, width=22, hside=2, vside=3, hcolor=4, vcolor=2,
               hfringe='0001101002100100011010',
               vfringe='0100000011000100001000',
               hdots='0001010011001000101001',
               vdots='1010011010011001010110',
               top=5, left=4, hmark=3, vmark=0,
               rect=['88888', '89888', '89888', '83660', '88880']),
  ]
  test = [
      generate(height=29, width=29, hside=0, vside=1, hcolor=2, vcolor=3,
               hfringe='10100101120101011010001011211',
               vfringe='00001100101001100110000121010',
               hdots='10110101110010110010010011000',
               vdots='00101001101000110101121101101',
               top=4, left=4, hmark=3, vmark=2,
               rect=['47000004464444440004', '47400044464666664744',
                     '47444444464644464740', '47444444464444464740',
                     '47464666664444464744', '47466444444444664744',
                     '47444444444444444740', '47777777777777777744',
                     '44444444444444444444', '48894949494949494944',
                     '48894949494949494944', '44444444444444444444']),
  ]
  return {'train': train, 'test': test}
