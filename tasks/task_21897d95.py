"""Generator for ARC task 21897d95: T markers repaint regions; an L marker rotates.

Rule:
  The input is a patchwork of solid colour regions. Small T markers of colour
  1 sit on it. Each T is a bar of three cells plus one stem cell from the
  middle of the bar. The bar centre is usually 1 but may be another colour.
  Each T sits inside one region (its owner), and its stem points across a
  region boundary. The region containing the cell two steps from the centre
  along the stem is repainted. The paint is the T's centre colour if that is
  not 1; otherwise it is the owner's colour. Every repaint uses the original,
  marker-erased layout, so repaints do not cascade, and all markers vanish.
  If a 5-cell L of colour 9 is present, it is erased too and the whole result
  is rotated. A top-right corner means counter-clockwise; a top-left corner
  means clockwise.

Scope:
  Random scenes are guillotine partitions of an 8..30 x 8..30 canvas into
  3..8 initially rectangular regions, optionally deformed by connected
  boundary transfers to make non-rectangular regions. Colours come from {0,2..9}. A colour may repeat
  only for regions that do not touch, including at corners. Each scene has
  2..6 T markers pointing up, down, left or right, sometimes with a non-1
  centre. Each region is targeted at most once, and markers keep a clear
  margin from each other. An optional colour-9 L marker (top-right or
  top-left corner) sits inside a region.

  validate() rebuilds the six canonical pairs through explicit generate()
  calls. For each fixture, the listed T latents (centre, direction, centre
  colour, owner colour) and the L latents (box corner, orientation,
  underlying colour) are used to erase the markers from the fixture rows. This
  recovers the region canvas, which is passed to generate() together with
  those latents.
"""

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

import random

import common

DIRS = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
PALETTE = [0, 2, 3, 4, 5, 6, 7, 8, 9]


def _t_cells(cy, cx, d):
  """Returns the two bar ends and the stem cell of a T centred at (cy, cx)."""
  dy, dx = DIRS[d]
  py, px = dx, dy
  return [(cy + py, cx + px), (cy - py, cx - px), (cy + dy, cx + dx)]


def _l_cells(r, c, orient):
  """Cells of a 3x3 L whose box starts at (r, c); orient is 'TR' or 'TL'."""
  cells = [(r, c), (r, c + 1), (r, c + 2)]
  col = c + 2 if orient == 'TR' else c
  return cells + [(r + 1, col), (r + 2, col)]


def _components(canvas):
  h, w = len(canvas), len(canvas[0])
  label = [[-1] * w for _ in range(h)]
  comps = []
  for y in range(h):
    for x in range(w):
      if label[y][x] >= 0:
        continue
      idx = len(comps)
      cells, stack = [], [(y, x)]
      label[y][x] = idx
      while stack:
        cy, cx = stack.pop()
        cells.append((cy, cx))
        for dy, dx in DIRS.values():
          ny, nx = cy + dy, cx + dx
          if 0 <= ny < h and 0 <= nx < w and label[ny][nx] < 0:
            if canvas[ny][nx] == canvas[cy][cx]:
              label[ny][nx] = idx
              stack.append((ny, nx))
      comps.append(cells)
  return label, comps


def _rotate(g, orient):
  h, w = len(g), len(g[0])
  if orient == 'TR':  # counter-clockwise
    return [[g[j][w - 1 - i] for j in range(h)] for i in range(w)]
  return [[g[h - 1 - j][i] for j in range(h)] for i in range(w)]  # clockwise


def _render(canvas, markers, lshape, lcolor):
  h, w = len(canvas), len(canvas[0])
  grid = [list(row) for row in canvas]
  for cy, cx, d, centre in markers:
    for y, x in _t_cells(cy, cx, d):
      grid[y][x] = 1
    grid[cy][cx] = centre
  if lshape:
    r, c, orient = lshape
    for y, x in _l_cells(r, c, orient):
      grid[y][x] = lcolor
  label, comps = _components(canvas)
  out = [list(row) for row in canvas]
  for cy, cx, d, centre in sorted(markers):
    dy, dx = DIRS[d]
    ty, tx = cy + 2 * dy, cx + 2 * dx
    if not (0 <= ty < h and 0 <= tx < w):
      continue
    paint = centre if centre != 1 else canvas[cy][cx]
    for y, x in comps[label[ty][tx]]:
      out[y][x] = paint
  if lshape:
    out = _rotate(out, lshape[2])
  return {'input': grid, 'output': out}


def _partition(h, w, n, minside=2):
  rects = [(0, 0, h, w)]
  for _ in range(80):
    if len(rects) >= n:
      break
    i = random.randrange(len(rects))
    r, c, rh, rw = rects[i]
    opts = []
    if rh >= 2 * minside:
      opts.append('h')
    if rw >= 2 * minside:
      opts.append('v')
    if not opts:
      continue
    if random.choice(opts) == 'h':
      cut = random.randint(minside, rh - minside)
      new = [(r, c, cut, rw), (r + cut, c, rh - cut, rw)]
    else:
      cut = random.randint(minside, rw - minside)
      new = [(r, c, rh, cut), (r, c + cut, rh, rw - cut)]
    rects[i:i + 1] = new
  return rects


def _touch(a, b):
  ar, ac, ah, aw = a
  br, bc, bh, bw = b
  return ar <= br + bh and br <= ar + ah and ac <= bc + bw and bc <= ac + aw


def _colour(rects, palette):
  cols = []
  for i, a in enumerate(rects):
    banned = {cols[j] for j in range(i) if _touch(a, rects[j])}
    cols.append(random.choice([c for c in palette if c not in banned]))
  return cols


def _t_candidates(rects, h, w):
  cands = []
  for (r, c, rh, rw) in rects:
    if rh >= 2 and rw >= 3:
      for cx in range(c + 1, c + rw - 1):
        if r > 0:
          cands.append((r + 1, cx, 'U', r, r + 1, cx - 1, cx + 1, r - 1, cx))
        if r + rh < h:
          cy = r + rh - 2
          cands.append((cy, cx, 'D', cy, cy + 1, cx - 1, cx + 1, r + rh, cx))
    if rw >= 2 and rh >= 3:
      for cy in range(r + 1, r + rh - 1):
        if c > 0:
          cands.append((cy, c + 1, 'L', cy - 1, cy + 1, c, c + 1, cy, c - 1))
        if c + rw < w:
          cx = c + rw - 2
          cands.append((cy, cx, 'R', cy - 1, cy + 1, cx, cx + 1, cy, c + rw))
  return cands


def _connected_cells(cells):
  if not cells:
    return False
  seen = {next(iter(cells))}
  stack = list(seen)
  while stack:
    y,x = stack.pop()
    for dy,dx in DIRS.values():
      p = (y+dy,x+dx)
      if p in cells and p not in seen:
        seen.add(p)
        stack.append(p)
  return len(seen) == len(cells)


def _bend_boundaries(owner):
  """Transfer small boundary patches while preserving every region's connectivity."""
  h,w = len(owner),len(owner[0])
  for _ in range(random.randint(8,30)):
    edges = [(y,x,dy,dx) for y in range(h) for x in range(w)
             for dy,dx in DIRS.values() if 0<=y+dy<h and 0<=x+dx<w
             and owner[y][x] != owner[y+dy][x+dx]]
    if not edges:
      break
    y,x,dy,dx = random.choice(edges)
    old,new = owner[y][x],owner[y+dy][x+dx]
    depth,span = random.randint(1,2),random.randint(1,4)
    patch = {(y-i*dy+j*dx,x-i*dx+j*dy)
             for i in range(depth) for j in range(span)}
    if any(not(0<=r<h and 0<=c<w) or owner[r][c]!=old for r,c in patch):
      continue
    remaining = {(r,c) for r in range(h) for c in range(w)
                 if owner[r][c]==old and (r,c) not in patch}
    if len(remaining)<6 or not _connected_cells(remaining):
      continue
    for r,c in patch:
      owner[r][c]=new
  return owner


def _colour_owner(owner, palette):
  h,w = len(owner),len(owner[0])
  neighbours = {}
  for y in range(h):
    for x in range(w):
      a=owner[y][x]
      neighbours.setdefault(a,set())
      for dy in (-1,0,1):
        for dx in (-1,0,1):
          if 0<=y+dy<h and 0<=x+dx<w:
            b=owner[y+dy][x+dx]
            if a!=b:neighbours[a].add(b)
  colours={}
  for a in sorted(neighbours):
    banned={colours[b] for b in neighbours[a] if b in colours}
    choices=[c for c in palette if c not in banned]
    if not choices:return None
    colours[a]=random.choice(choices)
  return colours


def _generic_t_candidates(owner):
  h,w = len(owner),len(owner[0])
  candidates=[]
  for cy in range(h):
    for cx in range(w):
      for d,(dy,dx) in DIRS.items():
        ty,tx=cy+2*dy,cx+2*dx
        if not(0<=ty<h and 0<=tx<w) or owner[ty][tx]==owner[cy][cx]:
          continue
        cells=_t_cells(cy,cx,d)+[(cy,cx)]
        y0,y1=min(y for y,x in cells),max(y for y,x in cells)
        x0,x1=min(x for y,x in cells),max(x for y,x in cells)
        if y0<0 or x0<0 or y1>=h or x1>=w:
          continue
        if all(owner[y][x]==owner[cy][cx] for y in range(y0,y1+1) for x in range(x0,x1+1)):
          candidates.append((cy,cx,d,y0,y1,x0,x1,ty,tx))
  return candidates


def _has_unintended_corner(grid, lshape):
  """The archived solver treats any-colour five-cell L as a rotation cue.

  Reject incidental region fragments with that shape, even though the
  intended rotation cue is colour 9. This preserves checker agreement;
  it is a declared restriction of generated scenes, not a new task rule.
  """
  expected = set(_l_cells(*lshape)) if lshape else set()
  _,groups = _components(grid)
  for cells in groups:
    y,x = cells[0]
    if grid[y][x]==1 or len(cells)!=5 or set(cells)==expected:
      continue
    y0,y1=min(y for y,x in cells),max(y for y,x in cells)
    x0,x1=min(x for y,x in cells),max(x for y,x in cells)
    if y1-y0!=2 or x1-x0!=2:continue
    cs=set(cells)
    for cy in (y0,y1):
      for cx in (x0,x1):
        if all((cy,xx) in cs for xx in range(x0,x1+1)) and all((yy,cx) in cs for yy in range(y0,y1+1)):
          return True
  return False


def _random_scene(height, width, num_regions, num_markers, rotate, irregular=None):
  for _ in range(500):
    h = height if height else random.randint(8, 30)
    w = width if width else random.randint(8, 30)
    use_l = rotate if rotate is not None else random.random() < 0.4
    n = num_regions if num_regions else random.randint(3, 8)
    rects = _partition(h, w, n)
    if len(rects) != n:
      continue
    palette = [c for c in PALETTE if not (use_l and c == 9)]
    owner = [[-1] * w for _ in range(h)]
    for i,(r,c,rh,rw) in enumerate(rects):
      for y in range(r,r+rh):
        for x in range(c,c+rw):owner[y][x]=i
    use_irregular = irregular if irregular is not None else random.random()<0.6
    if use_irregular:
      owner = _bend_boundaries(owner)
      if not any(len(cells)!=((max(y for y,x in cells)-min(y for y,x in cells)+1)*
                             (max(x for y,x in cells)-min(x for y,x in cells)+1))
                 for cells in [{(y,x) for y in range(h) for x in range(w) if owner[y][x]==i} for i in range(n)]):
        continue
    colours = _colour_owner(owner,palette)
    if colours is None:continue
    canvas = [[colours[owner[y][x]] for x in range(w)] for y in range(h)]
    occupied = set()
    lshape = None
    if use_l:
      spots = []
      for y in range(h-2):
        for x in range(w-2):
          if all(owner[r][c]==owner[y][x] for r in range(max(0,y-1),min(h,y+4))
                 for c in range(max(0,x-1),min(w,x+4))):
            spots.append((y,x))
      if not spots:
        continue
      ly, lx = random.choice(spots)
      lshape = (ly, lx, random.choice(['TR', 'TL']))
      for y in range(ly - 1, ly + 4):
        for x in range(lx - 1, lx + 4):
          occupied.add((y, x))
    cands = _generic_t_candidates(owner)
    random.shuffle(cands)
    want = num_markers if num_markers else random.randint(2, 6)
    markers, targeted = [], set()
    for cy, cx, d, y0, y1, x0, x1, ty, tx in cands:
      if len(markers) >= want:
        break
      tid = owner[ty][tx]
      if tid in targeted:
        continue
      halo = {(y, x) for y in range(y0 - 1, y1 + 2)
              for x in range(x0 - 1, x1 + 2)}
      if halo & occupied:
        continue
      occupied |= halo
      targeted.add(tid)
      centre = 1
      if random.random() < 0.4:
        near = {canvas[y][x] for (y, x) in halo if 0 <= y < h and 0 <= x < w}
        near |= {1, canvas[cy][cx], canvas[ty][tx]}
        choices = [k for k in range(10) if k not in near]
        if choices:
          centre = random.choice(choices)
      markers.append((cy, cx, d, centre))
    if len(markers) < (want if num_markers is not None else 2):
      continue
    if _has_unintended_corner(_render(canvas,markers,lshape,9)['input'],lshape):
      continue
    return canvas, markers, lshape
  raise ValueError('could not build a scene with these parameters')


def generate(height=None, width=None, num_regions=None, num_markers=None,
             rotate=None, canvas=None, markers=None, lshape=None, lcolor=9,
             irregular=None):
  """Returns an input/output pair for task 21897d95.

  Args:
    height: grid height for random scenes (default 8..30).
    width: grid width for random scenes (default 8..30).
    num_regions: exact number of connected regions (default 3..8).
    num_markers: exact requested T count; default attempts 2..6, at least 2.
    rotate: force presence (True) or absence (False) of the L marker.
    canvas: explicit marker-free region layout (list of rows).
    markers: explicit T markers as (centre_row, centre_col, dir, centre_colour);
      dir is one of 'U', 'D', 'L', 'R' and gives the stem direction.
    lshape: explicit L marker (box_row, box_col, 'TR' or 'TL') or None.
    lcolor: colour of the L marker (9 in the task).
    irregular: True forces a non-rectangular region layout, False rectangles;
      default mixes both. Deformations preserve connected regions.
  """
  if canvas is None:
    if markers is not None or lshape is not None:
      raise ValueError('explicit markers require an explicit canvas')
    if any(v is not None and not 8<=v<=30 for v in (height,width)):
      raise ValueError('random canvas dimensions must be 8..30')
    if num_regions is not None and num_regions not in range(3,9):
      raise ValueError('num_regions must be 3..8')
    if num_markers is not None and num_markers not in range(2,9):
      raise ValueError('num_markers must be 2..8')
    if num_regions is not None and num_markers is not None and num_markers>num_regions:
      raise ValueError('one target per region: num_markers cannot exceed num_regions')
    if lcolor != 9:
      raise ValueError('random L markers use colour 9')
    canvas, markers, lshape = _random_scene(height,width,num_regions,num_markers,rotate,irregular)
  else:
    canvas = [list(row) for row in canvas]
    markers = [tuple(m) for m in (markers or [])]
  return _render(canvas, markers, lshape, lcolor)


def _erase(rows, tees, lspec=None):
  """Erases listed markers from fixture rows; returns canvas/markers/lshape."""
  canvas = [[int(ch) for ch in row] for row in rows]
  plain = []
  for cy, cx, d, centre, own in tees:
    for y, x in _t_cells(cy, cx, d) + [(cy, cx)]:
      canvas[y][x] = own
    plain.append((cy, cx, d, centre))
  lshape = None
  if lspec:
    r, c, orient, under = lspec
    for y, x in _l_cells(r, c, orient):
      canvas[y][x] = under
    lshape = (r, c, orient)
  return canvas, plain, lshape


def validate():
  """Reconstructs the canonical pairs from explicit latent parameters."""
  train1 = ['666667774444', '666667774444', '666167774444', '666317774999',
            '666167774449', '666667774449', '666667174444', '666667114444',
            '666667174444', '666667774444', '771777777777', '710177777111',
            '777777777717', '888888888888', '888888888888', '888888888888']
  train2 = ['7777771733', '7777771133', '7777771733', '8883177731',
            '8881177716', '8183177731', '8113319133', '8183371733',
            '8883355533', '8883355533']
  train3 = ['666313333', '666113333', '666313333', '666444414', '666444111',
            '666444444', '666616444', '666611444', '666616444', '555444444',
            '999888888', '955888171', '955888818', '555444444']
  train4 = ['2222212333', '2222211333', '2222212333', '6666166313',
            '6661116113', '1116666313', '6166666333', '4444444333',
            '4444444333', '4444444333']
  test1 = [
      '9' * 30,
      '9' * 25 + '77999',
      '9' * 11 + '3331333333' + '999' + '7777' + '99',
      '9999' + '3' * 9 + '111' + '3' * 5 + '999' + '7777' + '99',
      '999' + '3' * 19 + '99' + '7777' + '99',
      '99' + '3' * 20 + '999' + '1' + '9999',
      '99' + '3' * 20 + '99' + '111' + '99' + '4',
      '9' + '3333' + '01' + '0' * 9 + '3' * 6 + '9' * 6 + '44',
      '9' + '333' + '0181' + '0' * 14 + '9' * 5 + '444',
      '9' + '33' + '0' * 10 + '2122' + '0' * 5 + '9' * 5 + '444',
      '9' + '33' + '0' * 7 + '222111' + '2222' + '00' + '9999' + '4444',
      '9' + '33' + '0' * 6 + '2' * 12 + '0' + '9999' + '4444',
      '9' + '33' + '0' * 5 + '2' * 14 + '9999' + '4444',
      '9' + '33' + '0' * 5 + '2' * 15 + '99' + '4' * 5,
      '666' + '0' * 5 + '2' * 15 + '99' + '4' * 5,
      '666' + '0' * 5 + '2' * 15 + '99' + '4' * 5,
      '6666' + '0' * 11 + '2' * 8 + '99' + '4' * 5,
      '6666' + '00111' + '0' * 6 + '2' * 9 + '9' + '4' * 5,
      '6' * 6 + '01' + '0' * 6 + '2' * 10 + '9' + '4' * 5,
      '6' * 12 + '00' + '2' * 10 + '9' + '4' * 5,
      '6' * 12 + '16' + '2' * 10 + '99' + '4444',
      '6' * 12 + '11' + '2' * 9 + '999' + '4444',
      '6' * 12 + '169' + '2' * 8 + '999' + '88' + '44',
      '6' * 14 + '9' + '2' * 7 + '999' + '888' + '44',
      '6' * 13 + '999' + '2222' + '9999' + '8888' + '44',
      '6' * 11 + '9' * 11 + '8' * 6 + '18',
      '6' * 5 + '9' * 11 + '8' * 11 + '111',
      '9' * 12 + '199' + '8' * 15,
      '9' * 12 + '01' + '8' * 16,
      '9' * 12 + '19' + '8' * 16,
  ]
  test2 = (['5' * 24, '5' * 24, '5' * 20 + '111' + '5', '5' * 21 + '155',
            '331333' + '8' * 12 + '6' * 6, '311133' + '8' * 12 + '6' * 6,
            '3' * 6 + '888999' + '8' * 6 + '6' * 6]
           + ['3' * 6 + '888889' + '8' * 6 + '6' * 6] * 2
           + ['3' * 6 + '8' * 12 + '6' * 6] * 5
           + ['3' * 6 + '8171' + '8' * 8 + '6' * 6,
              '3' * 6 + '881' + '8' * 9 + '6' * 6,
              '3' * 6 + '4' * 6 + '1' + '4' * 5 + '6' * 6,
              '3' * 6 + '4' * 5 + '111' + '4' * 4 + '6' * 6,
              '3' * 6 + '4' * 12 + '661116',
              '3' * 6 + '4' * 12 + '666166',
              '221' + '2' * 21, '2111' + '2' * 20, '2' * 24, '2' * 24])
  c1, m1, l1 = _erase(train1, [(3, 3, 'R', 3, 6), (7, 6, 'R', 1, 7),
                               (11, 2, 'U', 0, 7), (11, 10, 'D', 1, 7)],
                      (3, 9, 'TR', 4))
  c2, m2, l2 = _erase(train2, [(1, 6, 'R', 1, 7), (4, 4, 'L', 1, 3),
                               (4, 9, 'L', 6, 3), (6, 1, 'R', 1, 8),
                               (6, 6, 'D', 9, 7)])
  c3, m3, l3 = _erase(train3, [(1, 4, 'L', 1, 3), (4, 7, 'U', 1, 4),
                               (7, 4, 'R', 1, 6), (11, 7, 'D', 7, 8)],
                      (10, 0, 'TL', 5))
  c4, m4, l4 = _erase(train4, [(1, 5, 'R', 1, 2), (4, 4, 'U', 1, 6),
                               (4, 8, 'L', 1, 3), (5, 1, 'D', 1, 6)])
  c5, m5, l5 = _erase(test1, [(3, 14, 'U', 1, 3), (6, 25, 'U', 1, 9),
                              (8, 6, 'U', 8, 0), (10, 14, 'U', 1, 2),
                              (17, 7, 'D', 1, 0), (21, 12, 'R', 1, 6),
                              (26, 28, 'U', 1, 8), (28, 12, 'R', 0, 9)])
  c6, m6, l6 = _erase(test2, [(2, 21, 'D', 1, 5), (5, 2, 'U', 1, 3),
                              (14, 8, 'D', 7, 8), (17, 12, 'U', 1, 4),
                              (18, 21, 'D', 1, 6), (21, 2, 'U', 1, 2)],
                      (6, 9, 'TR', 8))
  train = [
      generate(canvas=c1, markers=m1, lshape=l1),
      generate(canvas=c2, markers=m2, lshape=l2),
      generate(canvas=c3, markers=m3, lshape=l3),
      generate(canvas=c4, markers=m4, lshape=l4),
  ]
  test = [
      generate(canvas=c5, markers=m5, lshape=l5),
      generate(canvas=c6, markers=m6, lshape=l6),
  ]
  return {'train': train, 'test': test}
