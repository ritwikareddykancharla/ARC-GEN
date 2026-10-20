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

"""ARC task 446ef5d2: assemble jigsaw fragments at the L marker's empty corner.

Rule: the input contains a 3-cell L marker and several connected multicolour
fragments. The marker is the only colour with exactly three cells, and it fills
three cells of a 2x2 box. Most fragment cells use one dominant frame colour.
The fragments are translated, never rotated, so that they tile one solid
rectangle whose whole outer border is frame colour. One corner of that
rectangle sits on the empty cell of the marker's 2x2 box, and the rectangle
extends away from the marker. The output is the background with only the
assembled rectangle on it. The marker and the scattered fragments are erased.

Scope: the generator builds a latent rectangle h x w. Each side is 4..24, the
short side is at most 12 and the area is at most 240; small sizes are favoured.
The rectangle is filled with the frame colour, and the interior gets one to
four accent shapes in one to three accent colours. The shapes do not touch and
are hollow rings, solid blocks with optional frame holes, or bars. Randomised
region growing cuts the rectangle into 3..10 compact, irregular, 4-connected
pieces of at least three cells each. One of four anchor corners is chosen, and
the rectangle and marker are placed on a 10..30 grid. The pieces are then
scattered so that no two pieces touch, and no piece touches the marker, not
even diagonally.

A local exact-cover search with a node budget rejects any scene that admits a
differently coloured framed tiling, including tilings for another
factorisation of the area. The frame colour must be strictly the most common
fragment colour. No fragment colour may occur exactly three times. The
background must strictly dominate.

validate() rebuilds the four canonical pairs from explicit latent parameters:
the rectangle contents, a piece label map and each piece's input bounding-box
position.
"""

import random

import common

_CORNERS = ('tl', 'tr', 'bl', 'br')


def _neighbors4(r, c):
  return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))


def _marker_cells(corner, top, left, h, w):
  """Returns (anchor cell, three marker cells) for the given anchor corner."""
  if corner == 'tl':
    ar, ac = top, left
    return (ar, ac), [(ar - 1, ac - 1), (ar - 1, ac), (ar, ac - 1)]
  if corner == 'tr':
    ar, ac = top, left + w - 1
    return (ar, ac), [(ar - 1, ac), (ar - 1, ac + 1), (ar, ac + 1)]
  if corner == 'bl':
    ar, ac = top + h - 1, left
    return (ar, ac), [(ar, ac - 1), (ar + 1, ac - 1), (ar + 1, ac)]
  ar, ac = top + h - 1, left + w - 1
  return (ar, ac), [(ar, ac + 1), (ar + 1, ac), (ar + 1, ac + 1)]


def _groups(labels):
  """Maps each label to its cells in reading order."""
  groups = {}
  for r, row in enumerate(labels):
    for c, key in enumerate(row):
      groups.setdefault(key, []).append((r, c))
  return groups


def _render(height, width, bg, marker, corner, rect_top, rect_left, rect,
            labels, offsets):
  h, w = len(rect), len(rect[0])
  grid_in = common.grid(width, height, bg)
  grid_out = common.grid(width, height, bg)
  for r in range(h):
    for c in range(w):
      grid_out[rect_top + r][rect_left + c] = rect[r][c]
  for key, cells in _groups(labels).items():
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    orow, ocol = offsets[key]
    for r, c in cells:
      grid_in[orow + r - mr][ocol + c - mc] = rect[r][c]
  _, mcells = _marker_cells(corner, rect_top, rect_left, h, w)
  for r, c in mcells:
    grid_in[r][c] = marker
  return {'input': grid_in, 'output': grid_out}


def _decorate(h, w, frame, accents):
  """Frame-filled rectangle with 1..4 separated accent shapes inside."""
  rect = [[frame] * w for _ in range(h)]
  ih, iw = h - 2, w - 2
  taken = set()
  want = random.randint(1, 4)
  placed = 0
  for _ in range(80):
    if placed >= want:
      break
    kind = random.choice(('ring', 'ring', 'block', 'bar'))
    if kind == 'ring':
      if ih < 3 or iw < 3:
        continue
      sh, sw = random.randint(3, ih), random.randint(3, iw)
    elif kind == 'block':
      sh = random.randint(1, min(4, ih))
      sw = random.randint(1, min(6, iw))
      if sh * sw < 2:
        continue
    else:
      if random.random() < 0.5:
        sh, sw = 1, random.randint(2, iw)
      else:
        sh, sw = random.randint(2, ih), 1
    r0 = random.randint(1, 1 + ih - sh)
    c0 = random.randint(1, 1 + iw - sw)
    box = [(r, c) for r in range(r0, r0 + sh) for c in range(c0, c0 + sw)]
    clash = False
    for r, c in box:
      for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
          if (r + dr, c + dc) in taken:
            clash = True
    if clash:
      continue
    color = random.choice(accents)
    if kind == 'ring':
      cells = [p for p in box
               if p[0] in (r0, r0 + sh - 1) or p[1] in (c0, c0 + sw - 1)]
    elif kind == 'block':
      cells = list(box)
      if sh >= 2 and sw >= 2 and random.random() < 0.5:
        holes = set(random.sample(cells,
                                  random.randint(1, max(1, len(cells) // 4))))
        cells = [p for p in cells if p not in holes]
    else:
      cells = box
    for r, c in cells:
      rect[r][c] = color
    taken.update(box)
    placed += 1
  return rect, placed


def _partition(h, w, k):
  """Randomised compact region growing into k 4-connected pieces."""
  owner = [[-1] * w for _ in range(h)]
  seeds = random.sample([(r, c) for r in range(h) for c in range(w)], k)
  members = []
  for i, (r, c) in enumerate(seeds):
    owner[r][c] = i
    members.append([(r, c)])
  remaining = h * w - k
  while remaining > 0:
    options, weights = [], []
    for i in range(k):
      front = {}
      for r, c in members[i]:
        for nr, nc in _neighbors4(r, c):
          if 0 <= nr < h and 0 <= nc < w and owner[nr][nc] == -1:
            front[(nr, nc)] = front.get((nr, nc), 0) + 1
      if front:
        options.append((i, front))
        weights.append(1.0 / len(members[i]))
    i, front = random.choices(options, weights=weights)[0]
    cands = list(front)
    cell = random.choices(cands, weights=[front[q] ** 3 for q in cands])[0]
    owner[cell[0]][cell[1]] = i
    members[i].append(cell)
    remaining -= 1
  return owner


def _place_rect(corner, height, width, h, w):
  if corner in ('tl', 'tr'):
    top = random.randint(1, height - h)
  else:
    top = random.randint(0, height - h - 1)
  if corner in ('tl', 'bl'):
    left = random.randint(1, width - w)
  else:
    left = random.randint(0, width - w - 1)
  return top, left


def _scatter(groups, height, width, marker_cells):
  """Places pieces so that no two objects touch, even diagonally."""
  blocked = set()

  def block(r, c):
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        blocked.add((r + dr, c + dc))

  for r, c in marker_cells:
    block(r, c)
  order = sorted(groups, key=lambda q: (-len(groups[q]), random.random()))
  offsets = {}
  for key in order:
    cells = groups[key]
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    norm = [(r - mr, c - mc) for r, c in cells]
    bh = max(r for r, _ in norm) + 1
    bw = max(c for _, c in norm) + 1
    if bh > height or bw > width:
      return None
    spot = None
    for _ in range(300):
      r0 = random.randint(0, height - bh)
      c0 = random.randint(0, width - bw)
      if all((r0 + r, c0 + c) not in blocked for r, c in norm):
        spot = (r0, c0)
        break
    if spot is None:
      return None
    offsets[key] = spot
    for r, c in norm:
      block(spot[0] + r, spot[1] + c)
  return offsets


def _unique_assembly(pieces, frame, anchor, corner, height, width, h, target):
  """True iff every framed translation-tiling reproduces the latent picture."""
  area = len(target)
  dy = 1 if corner in ('tl', 'tr') else -1
  dx = 1 if corner in ('tl', 'bl') else -1
  budget = [60000]
  bad = [False]
  n = len(pieces)
  for hh in range(1, area + 1):
    if area % hh:
      continue
    ww = area // hh
    ty = anchor[0] if dy == 1 else anchor[0] - hh + 1
    tx = anchor[1] if dx == 1 else anchor[1] - ww + 1
    if ty < 0 or tx < 0 or ty + hh > height or tx + ww > width:
      continue
    cells = [-1] * area
    used = [False] * n

    def rec(start, hh=hh, ww=ww, cells=cells, used=used):
      if bad[0]:
        return
      if budget[0] <= 0:
        bad[0] = True
        return
      budget[0] -= 1
      k = start
      while k < area and cells[k] != -1:
        k += 1
      if k == area:
        if hh != h or cells != target:
          bad[0] = True
        return
      ey, ex = divmod(k, ww)
      for i in range(n):
        if used[i]:
          continue
        ok = True
        for ry, rx, col in pieces[i]:
          yy, xx = ey + ry, ex + rx
          if (yy < 0 or xx < 0 or yy >= hh or xx >= ww or
              cells[yy * ww + xx] != -1):
            ok = False
            break
          if ((yy == 0 or yy == hh - 1 or xx == 0 or xx == ww - 1) and
              col != frame):
            ok = False
            break
        if not ok:
          continue
        for ry, rx, col in pieces[i]:
          cells[(ey + ry) * ww + ex + rx] = col
        used[i] = True
        rec(k)
        used[i] = False
        for ry, rx, col in pieces[i]:
          cells[(ey + ry) * ww + ex + rx] = -1
        if bad[0]:
          return

    rec(0)
    if bad[0]:
      return False
  return True


def generate(height=None, width=None, bg=None, marker=None, corner=None,
             rect_top=None, rect_left=None, rect_rows=None, labels=None,
             offsets=None):
  """Generates one jigsaw-assembly pair.

  Args:
    height: grid height. Random 10..30 if None. If given, it must leave room
      for a rectangle of at least 4 rows plus the marker.
    width: grid width. Random 10..30 if None. Same constraint as height.
    bg: background colour. Random if None.
    marker: colour of the 3-cell L marker. Random if None; must differ from bg.
    corner: which rectangle corner sits at the marker's empty cell. One of
      'tl', 'tr', 'bl', 'br'. Random if None.
    rect_top: row of the assembled rectangle. Explicit mode only.
    rect_left: column of the assembled rectangle. Explicit mode only.
    rect_rows: assembled rectangle contents, as digit strings or lists of
      ints. Supplying it selects explicit (fixture) mode, which then requires
      every other argument.
    labels: same-shaped map assigning each rectangle cell to a piece key.
      Explicit mode only.
    offsets: dict mapping each piece key to the (row, col) of that piece's
      bounding-box top-left in the input. Explicit mode only.
  """
  if rect_rows is not None:
    if any(v is None for v in (height, width, bg, marker, corner, rect_top,
                               rect_left, labels, offsets)):
      raise ValueError('explicit mode requires every latent parameter')
    rect = [[int(ch) for ch in row] if isinstance(row, str)
            else [int(v) for v in row] for row in rect_rows]
    labs = [list(row) for row in labels]
    if (not rect or not rect[0] or any(len(row) != len(rect[0]) for row in rect)
        or len(labs) != len(rect) or any(len(row) != len(rect[0]) for row in labs)):
      raise ValueError('rectangle and labels must have the same rectangular shape')
    if (not 1 <= height <= 30 or not 1 <= width <= 30 or
        bg not in range(10) or marker not in range(10) or bg == marker or
        corner not in _CORNERS):
      raise ValueError('invalid dimensions, palette or corner')
    if (rect_top < 0 or rect_left < 0 or rect_top + len(rect) > height or
        rect_left + len(rect[0]) > width or
        any(c not in range(10) or c in (bg, marker) for row in rect for c in row)):
      raise ValueError('rectangle outside grid or invalid rectangle palette')
    _, mark_cells = _marker_cells(corner, rect_top, rect_left, len(rect), len(rect[0]))
    if any(not (0 <= r < height and 0 <= c < width) for r, c in mark_cells):
      raise ValueError('marker outside grid')
    groups = _groups(labs)
    if set(groups) != set(offsets):
      raise ValueError('piece offsets must match the labels')
    occupied = set()
    for key, cells in groups.items():
      y, x = offsets[key]
      mr, mc = min(r for r, _ in cells), min(c for _, c in cells)
      points = {(y + r - mr, x + c - mc) for r, c in cells}
      if any(not (0 <= r < height and 0 <= c < width) for r, c in points):
        raise ValueError('fragment outside grid')
      if points & set(mark_cells):
        raise ValueError('fragment overlaps the marker')
      if any((r + dr, c + dc) in occupied for r, c in points
             for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
        raise ValueError('fragments touch one another')
      occupied.update(points)
    return _render(height, width, bg, marker, corner, rect_top, rect_left,
                   rect, labs, offsets)
  if any(v is not None for v in (rect_top, rect_left, labels, offsets)):
    raise ValueError('rect_top/rect_left/labels/offsets require rect_rows')
  for v in (height, width):
    if v is not None and not 1 <= v <= 30:
      raise ValueError('grid sides must be within 1..30')
  if any(c is not None and c not in range(10) for c in (bg, marker)):
    raise ValueError('colours must be in 0..9')
  if bg is not None and marker is not None and bg == marker:
    raise ValueError('marker colour must differ from background')
  if corner is not None and corner not in _CORNERS:
    raise ValueError('corner must be one of tl, tr, bl, br')
  hi_h = 24 if height is None else min(24, height - 1)
  hi_w = 24 if width is None else min(24, width - 1)
  if hi_h < 4 or hi_w < 4:
    raise ValueError('grid too small for a framed rectangle and marker')
  if height is not None and width is not None and height * width < 88:
    raise ValueError('grid too small to scatter the fragments')
  for _ in range(500):
    h = random.randint(4, random.randint(4, hi_h))
    w = random.randint(4, random.randint(4, hi_w))
    if min(h, w) > 12 or h * w > 240:
      continue
    area = h * w
    hgt = height if height is not None else random.randint(max(10, h + 3), 30)
    wid = width if width is not None else random.randint(max(10, w + 3), 30)
    if hgt < h + 1 or wid < w + 1 or hgt * wid < 3 * area + 40:
      continue
    bgc = bg if bg is not None else random.choice([c for c in range(10) if c != marker])
    others = [c for c in range(10) if c != bgc]
    mk = marker if marker is not None else random.choice(others)
    others = [c for c in others if c != mk]
    frame = random.choice(others)
    others = [c for c in others if c != frame]
    accents = random.sample(others, random.randint(1, 3))
    rect, placed = _decorate(h, w, frame, accents)
    if not placed:
      continue
    counts = {}
    for row in rect:
      for v in row:
        counts[v] = counts.get(v, 0) + 1
    fc = counts[frame]
    if any(c != frame and (n >= fc or n == 3) for c, n in counts.items()):
      continue
    k = random.randint(3, max(3, min(10, area // 8)))
    labs = _partition(h, w, k)
    groups = _groups(labs)
    if len(groups) != k or min(len(g) for g in groups.values()) < 3:
      continue
    pieces, sigs = [], set()
    for key in sorted(groups):
      cells = groups[key]
      fy, fx = cells[0]
      piece = [(r - fy, c - fx, rect[r][c]) for r, c in cells]
      sig = tuple(piece)
      if sig in sigs:
        break
      sigs.add(sig)
      pieces.append(piece)
    if len(pieces) != k:
      continue
    cor = corner if corner is not None else random.choice(_CORNERS)
    top, left = _place_rect(cor, hgt, wid, h, w)
    anchor, mcells = _marker_cells(cor, top, left, h, w)
    offs = _scatter(groups, hgt, wid, mcells)
    if offs is None:
      continue
    target = [v for row in rect for v in row]
    if not _unique_assembly(pieces, frame, anchor, cor, hgt, wid, h, target):
      continue
    return _render(hgt, wid, bgc, mk, cor, top, left, rect, labs, offs)
  raise RuntimeError('could not build a valid jigsaw scene')


def validate():
  """Rebuilds the canonical pairs from explicit latent parameters."""
  train = [
      generate(height=12, width=20, bg=8, marker=4, corner='br',
               rect_top=3, rect_left=7,
               rect_rows=['77777777777', '70000000707', '70700070007',
                          '77777777777', '72722222227', '72227777727',
                          '77777777777'],
               labels=['AAAAABBBBBB'] * 3 + ['AAAAACCCDDD'] * 4,
               offsets={'A': (4, 1), 'B': (1, 9), 'C': (0, 17),
                        'D': (6, 15)}),
      generate(height=10, width=10, bg=8, marker=4, corner='tl',
               rect_top=2, rect_left=2,
               rect_rows=['333333', '399993', '399993', '399993', '393333',
                          '333333'],
               labels=['AAABBB'] * 3 + ['CCCDDD'] * 3,
               offsets={'A': (2, 2), 'B': (6, 1), 'C': (6, 6),
                        'D': (1, 6)}),
  ]
  test = [
      generate(height=26, width=26, bg=4, marker=2, corner='bl',
               rect_top=2, rect_left=2,
               rect_rows=['1111111111', '1333333331', '1311111131',
                          '1311111131', '1311111131', '1333333331',
                          '1111111111', '1111111111', '1166666661',
                          '1161111161', '1161111161', '1166666661',
                          '1111111111', '1111111111', '1777777111',
                          '1711117111', '1711117111', '1711117111',
                          '1711117111', '1777777111', '1111111111',
                          '1111111111'],
               labels=(['AAAABBBBBB'] * 4 + ['CCCCDDDDDD'] * 3 +
                       ['CCCCEEEFFF'] * 3 + ['GGGGGEEFFF'] * 3 +
                       ['GGGGHHHHHH'] * 4 + ['GGGGIIIIII'] +
                       ['JJJJIIIIII'] * 4),
               offsets={'A': (1, 18), 'B': (13, 7), 'C': (2, 1),
                        'D': (6, 6), 'E': (11, 0), 'F': (1, 23),
                        'G': (16, 14), 'H': (15, 20), 'I': (6, 16),
                        'J': (20, 2)}),
      generate(height=20, width=20, bg=8, marker=4, corner='tr',
               rect_top=2, rect_left=2,
               rect_rows=['9999999999999999', '9333399999939939',
                          '9399399933333339', '9333333339933339',
                          '9399333339933339', '9333399933333339',
                          '9999999999999999'],
               labels=['AAABBBBCCCDDDEEE'] * 4 + ['AAABBBBCCCDDDFFF'] * 3,
               offsets={'A': (3, 0), 'B': (1, 6), 'C': (8, 13),
                        'D': (13, 3), 'E': (2, 15), 'F': (17, 11)}),
  ]
  return {'train': train, 'test': test}
