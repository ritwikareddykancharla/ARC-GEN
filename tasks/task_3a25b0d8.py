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

"""ARC task 3a25b0d8: fill an empty outline from a coloured template.

Rule: the input holds two drawings in one line colour on a uniform
background. The template has its enclosed pockets coloured. The outline is
the same design (same pocket topology) drawn with different proportions and
empty pockets. The output is the outline's bounding box. It holds only the
outline's own line cells, with background elsewhere. Each enclosed pocket is
flooded with the colour of the template pocket whose centroid is nearest.
Centroids are normalised by each shape's height and width. Template pockets
left as background stay background.

Scope of random scenes: banded designs. Each has 2-4 horizontal bands
separated by one-cell line walls. Each band holds 1-3 rectangular pockets
separated by one-cell walls. Bands of different widths are centred, which
gives stepped silhouettes. Template and outline share band and pocket counts.
Pocket heights and widths are sampled independently, so proportions differ.
Widths and colours can optionally be mirror-symmetric. Some template pockets
may stay background. The two shapes sit in disjoint bounding boxes, with at
least one empty row or column between them. The grid is sized so that the
background colour covers a strict majority of cells. This keeps the
background identifiable even when the line colour is plentiful.

The original fixtures use free-form drawings. They are replayed from explicit
template and outline sprites plus their positions. Their answer is derived
from the sprites by nearest-normalised-centroid pocket matching.
"""

import collections
import random

import common


def _components(mask):
  """Returns 4-connected components of True cells in row-major order."""
  height, width = len(mask), len(mask[0])
  seen = [[False] * width for _ in range(height)]
  comps = []
  for y in range(height):
    for x in range(width):
      if not mask[y][x] or seen[y][x]:
        continue
      seen[y][x] = True
      stack, comp = [(y, x)], []
      while stack:
        cy, cx = stack.pop()
        comp.append((cy, cx))
        for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
          if 0 <= ny < height and 0 <= nx < width:
            if mask[ny][nx] and not seen[ny][nx]:
              seen[ny][nx] = True
              stack.append((ny, nx))
      comps.append(comp)
  return comps


def _pockets(crop, line, bg):
  """Pockets of a cleaned crop: (cells, colour, norm_cy, norm_cx)."""
  height, width = len(crop), len(crop[0])
  mask = [[v != line for v in row] for row in crop]
  res = []
  for comp in _components(mask):
    vals = [crop[y][x] for y, x in comp]
    border = any(y in (0, height - 1) or x in (0, width - 1) for y, x in comp)
    if border and all(v == bg for v in vals):
      continue
    col = collections.Counter(vals).most_common(1)[0][0]
    cy = sum(y for y, _ in comp) / float(len(comp)) / max(height - 1, 1)
    cx = sum(x for _, x in comp) / float(len(comp)) / max(width - 1, 1)
    res.append((comp, col, cy, cx))
  return res


def _paste(grid, sprite, r0, c0):
  for dy, row in enumerate(sprite):
    for dx, ch in enumerate(row):
      if ch != '.':
        grid[r0 + dy][c0 + dx] = int(ch)


def _replay(template_sprite, outline_sprite, bg, width, height, tpos, opos):
  """Builds a scene from explicit sprites (used for the original fixtures)."""
  line = int(next(ch for row in outline_sprite for ch in row if ch != '.'))
  grid = common.grid(width, height, bg)
  _paste(grid, outline_sprite, opos[0], opos[1])
  _paste(grid, template_sprite, tpos[0], tpos[1])
  tcrop = [[bg if ch == '.' else int(ch) for ch in row]
           for row in template_sprite]
  out = [[line if ch != '.' else bg for ch in row] for row in outline_sprite]
  tp = _pockets(tcrop, line, bg)
  op = _pockets(out, line, bg)
  for comp, _, cy, cx in op:
    best = min(tp, key=lambda t: (t[2] - cy) ** 2 + (t[3] - cx) ** 2)
    if best[1] != bg:
      for y, x in comp:
        out[y][x] = best[1]
  return {'input': grid, 'output': out}


def _realize(counts, symmetric, max_pocket_size):
  """Samples band heights and pocket widths for a given pocket topology."""
  for _ in range(100):
    heights = [random.randint(1, max_pocket_size) for _ in counts]
    widths = []
    for n in counts:
      if symmetric:
        half = [random.randint(1, max_pocket_size) for _ in range((n + 1) // 2)]
        widths.append(half + half[:n // 2][::-1])
      else:
        widths.append([random.randint(1, max_pocket_size) for _ in range(n)])
    spans = [sum(ws) + len(ws) + 1 for ws in widths]
    if symmetric and len(set(s % 2 for s in spans)) > 1:
      continue
    return heights, widths
  return None


def _layout(heights, widths, line_ch, fills):
  """Renders a banded design. Returns (rows, pocket rects, height, width)."""
  spans = [sum(ws) + len(ws) + 1 for ws in widths]
  width = max(spans)
  height = sum(heights) + len(heights) + 1
  rows = [['.'] * width for _ in range(height)]
  lefts = [(width - s) // 2 for s in spans]
  rects = []
  y, k = 1, 0
  for b, h in enumerate(heights):
    x0, x1 = lefts[b], lefts[b] + spans[b] - 1
    if b == 0:
      a0, a1 = x0, x1
    else:
      a0 = min(x0, lefts[b - 1])
      a1 = max(x1, lefts[b - 1] + spans[b - 1] - 1)
    for x in range(a0, a1 + 1):
      rows[y - 1][x] = line_ch
    for r in range(y, y + h):
      rows[r][x0] = line_ch
    x = x0 + 1
    for w in widths[b]:
      rects.append((y, x, h, w))
      ch = fills[k]
      k += 1
      for r in range(y, y + h):
        for c in range(x, x + w):
          rows[r][c] = ch
        rows[r][x + w] = line_ch
      x += w + 1
    y += h + 1
  for x in range(lefts[-1], lefts[-1] + spans[-1]):
    rows[height - 1][x] = line_ch
  return [''.join(r) for r in rows], rects, height, width


def _centroids(dims):
  heights, widths = dims
  n = sum(len(w) for w in widths)
  _, rects, height, width = _layout(heights, widths, '1', ['.'] * n)
  return [((y + (h - 1) / 2.0) / max(height - 1, 1),
           (x + (w - 1) / 2.0) / max(width - 1, 1)) for y, x, h, w in rects]


def _unambiguous(tdims, odims):
  """Each outline pocket's nearest template pocket is its own, with margin."""
  tc, oc = _centroids(tdims), _centroids(odims)
  if len(tc) != len(oc) or len(tc) < 2:
    return False
  for i, (cy, cx) in enumerate(oc):
    d = [(cy - ty) ** 2 + (cx - tx) ** 2 for ty, tx in tc]
    others = min(d[j] for j in range(len(d)) if j != i)
    if not d[i] < 0.5 * others:
      return False
  return True


def _assign_colors(counts, symmetric, bg, line):
  pool = [c for c in range(10) if c not in (bg, line)]
  palette = random.sample(pool, random.randint(2, 5))

  def pick():
    return None if random.random() < 0.15 else random.choice(palette)

  cols = []
  for n in counts:
    if symmetric:
      half = [pick() for _ in range((n + 1) // 2)]
      cols.extend(half + half[:n // 2][::-1])
    else:
      cols.extend(pick() for _ in range(n))
  return cols


def _place(ht, wt, ho, wo, ncells, width, height, tpos, opos):
  """Places two boxes with at least one empty column/row between them.

  The grid is sized so that background cells form a strict majority.
  """
  if tpos is not None and opos is not None and width and height:
    if not (0<=tpos[0]<=height-ht and 0<=tpos[1]<=width-wt and 0<=opos[0]<=height-ho and 0<=opos[1]<=width-wo):return None
    if not (tpos[0]+ht < opos[0] or opos[0]+ho < tpos[0] or tpos[1]+wt < opos[1] or opos[1]+wo < tpos[1]):return None
    return width, height, tuple(tpos), tuple(opos)
  options = []
  if wt + wo + 1 <= 30:
    options.append('h')
  if ht + ho + 1 <= 30:
    options.append('v')
  if not options:
    return None
  mode = random.choice(options)
  if mode == 'h':
    need_w, need_h = wt + wo + 1, max(ht, ho)
  else:
    need_w, need_h = max(wt, wo), ht + ho + 1
  if need_w > 30 or need_h > 30:
    return None
  gw = gh = None
  for _ in range(40):
    cand_w = width or random.randint(need_w, min(30, need_w + 10))
    cand_h = height or random.randint(need_h, min(30, need_h + 10))
    if cand_w < need_w or cand_h < need_h:
      continue
    if cand_w * cand_h > 2 * ncells:
      gw, gh = cand_w, cand_h
      break
  if gw is None:
    return None
  first_t = random.random() < 0.5
  sizes = [(ht, wt), (ho, wo)] if first_t else [(ho, wo), (ht, wt)]
  if mode == 'h':
    slack = gw - need_w
    a = random.randint(0, slack)
    g = random.randint(0, slack - a)
    xs = [a, a + sizes[0][1] + 1 + g]
    ys = [random.randint(0, gh - s[0]) for s in sizes]
  else:
    slack = gh - need_h
    a = random.randint(0, slack)
    g = random.randint(0, slack - a)
    ys = [a, a + sizes[0][0] + 1 + g]
    xs = [random.randint(0, gw - s[1]) for s in sizes]
  pos = [(ys[0], xs[0]), (ys[1], xs[1])]
  if first_t:
    return gw, gh, pos[0], pos[1]
  return gw, gh, pos[1], pos[0]


def _sample(counts, symmetric, colors, t_heights, t_widths, o_heights,
            o_widths, bg, line, width, height, tpos, opos, max_pocket_size):
  reserved={c for c in (colors or []) if c is not None}
  bgc=bg if bg is not None else random.choice([c for c in range(10) if c not in reserved and c!=line])
  lc=line if line is not None else random.choice([c for c in range(10) if c!=bgc and c not in reserved])
  if lc == bgc:
    return None
  sym = symmetric if symmetric is not None else random.random() < 0.6
  if t_heights is not None and t_widths is not None:
    tdims = (list(t_heights), [list(w) for w in t_widths])
    cnt = [len(w) for w in tdims[1]]
  else:
    if counts is not None:
      cnt = list(counts)
    else:
      cnt = [random.randint(1, 3) for _ in range(random.randint(2, 4))]
    tdims = _realize(cnt, sym, max_pocket_size)
    if tdims is None:
      return None
  npock = sum(cnt)
  if colors is not None:
    cols = [None if (c is None or c == bgc) else c for c in colors]
    if len(cols) != npock or any(c == lc for c in cols):
      return None
    if sum(c is not None for c in cols) < 1:
      return None
  else:
    cols = _assign_colors(cnt, sym, bgc, lc)
    if sum(c is not None for c in cols) < 2:
      return None
  if o_heights is not None and o_widths is not None:
    odims = (list(o_heights), [list(w) for w in o_widths])
  else:
    odims = None
    for _ in range(80):
      cand = _realize(cnt, sym, max_pocket_size)
      if cand is None or cand == tdims:
        continue
      if _unambiguous(tdims, cand):
        odims = cand
        break
    if odims is None:
      return None
  if odims == tdims or not _unambiguous(tdims, odims):
    return None
  tchars = ['.' if c is None else str(c) for c in cols]
  tsprite, _, ht, wt = _layout(tdims[0], tdims[1], str(lc), tchars)
  osprite, _, ho, wo = _layout(odims[0], odims[1], str(lc), ['.'] * npock)
  filled, _, _, _ = _layout(odims[0], odims[1], str(lc), tchars)
  ncells = sum(ch != '.' for row in tsprite + osprite for ch in row)
  placed = _place(ht, wt, ho, wo, ncells, width, height, tpos, opos)
  if placed is None:
    return None
  gw, gh, tp, op = placed
  grid = common.grid(gw, gh, bgc)
  _paste(grid, tsprite, tp[0], tp[1])
  _paste(grid, osprite, op[0], op[1])
  nbg = sum(v == bgc for row in grid for v in row)
  if 2 * nbg <= gw * gh:
    return None
  output = [[bgc if ch == '.' else int(ch) for ch in row] for row in filled]
  return {'input': grid, 'output': output}


def generate(counts=None, symmetric=None, colors=None, t_heights=None,
             t_widths=None, o_heights=None, o_widths=None, bg=None, line=None,
             width=None, height=None, tpos=None, opos=None,
             template_sprite=None, outline_sprite=None, max_pocket_size=4):
  """Returns an input/output pair.

  Args:
    counts: pockets per band (2-4 bands, 1-3 pockets each).
    symmetric: whether pocket widths and colours mirror within each band.
    colors: flat list of template pocket colours (None = background pocket).
    t_heights: template band heights (each 1..6).
    t_widths: template pocket widths per band (each 1..6).
    o_heights: outline band heights.
    o_widths: outline pocket widths per band.
    bg: background colour.
    line: line colour shared by both drawings.
    width: grid width.
    height: grid height.
    tpos: (row, col) of the template's top-left box corner.
    opos: (row, col) of the outline's top-left box corner.
    template_sprite: rows of digits/'.' for fixture replay (with outline_sprite).
    outline_sprite: rows of digits/'.' for fixture replay.
    max_pocket_size: random band/pocket size upper bound, 1..6 (default 4).
  """
  for d in (width,height):
    if d is not None and (not isinstance(d,int) or not 1<=d<=30):raise ValueError("Dimensions must be in 1..30")
  if bg is not None and bg not in range(10):raise ValueError("Invalid background")
  if line is not None and (line not in range(10) or line==bg):raise ValueError("Invalid line colour")
  if not isinstance(max_pocket_size,int) or not 1<=max_pocket_size<=6:raise ValueError("max_pocket_size must be in 1..6")
  if (template_sprite is None)!=(outline_sprite is None):raise ValueError("Both sprites required")
  if template_sprite is not None:
    if any(v is None for v in (bg,width,height,tpos,opos)):raise ValueError("Sprite replay requires complete geometry")
    if any(v is not None for v in (counts,symmetric,colors,t_heights,t_widths,o_heights,o_widths)):
      raise ValueError("Banded controls cannot accompany explicit sprites")
    for sprite,pos in ((template_sprite,tpos),(outline_sprite,opos)):
      if not sprite or not sprite[0] or any(len(row)!=len(sprite[0]) or any(ch not in '.0123456789' for ch in row) for row in sprite):raise ValueError("Sprites must be rectangular digit arrays")
      if not (0<=pos[0]<=height-len(sprite) and 0<=pos[1]<=width-len(sprite[0])):raise ValueError("Sprite outside grid")
    line_colours={int(ch) for row in outline_sprite for ch in row if ch!='.'}
    if len(line_colours)!=1 or bg in line_colours or (line is not None and line not in line_colours):raise ValueError("Outline must have exactly one line colour")
    return _replay(template_sprite,outline_sprite,bg,width,height,tpos,opos)
  if (tpos is None)!=(opos is None) or (tpos is not None and (width is None or height is None)):
    raise ValueError("Explicit positions require both positions and dimensions")
  if (t_heights is None)!=(t_widths is None) or (o_heights is None)!=(o_widths is None):
    raise ValueError("Band heights and pocket widths must be supplied together")
  for hs,ws in ((t_heights,t_widths),(o_heights,o_widths)):
    if hs is not None:
      if not 2<=len(hs)<=4 or len(hs)!=len(ws) or any(not 1<=len(row)<=3 for row in ws):raise ValueError("Invalid band topology")
      if any(not isinstance(v,int) or not 1<=v<=6 for v in list(hs)+[x for row in ws for x in row]):raise ValueError("Pocket sides must be in 1..6")
  if counts is None and t_widths is not None:counts=[len(row) for row in t_widths]
  if counts is None and o_widths is not None:counts=[len(row) for row in o_widths]
  if counts is not None:
    if not 2<=len(counts)<=4 or any(not isinstance(n,int) or not 1<=n<=3 for n in counts):raise ValueError("Invalid pocket counts")
    for ws in (t_widths,o_widths):
      if ws is not None and [len(row) for row in ws]!=list(counts):raise ValueError("Pocket topology does not match counts")
  if colors is not None:
    if any(c is not None and (c not in range(10) or c==line) for c in colors):raise ValueError("Invalid pocket colour")
    if counts is None:raise ValueError("Explicit colours require pocket counts")
    if len(colors)!=sum(counts):raise ValueError("Pocket colour count mismatch")
    if len(set(c for c in colors if c is not None)|{v for v in (bg,line) if v is not None})>8:raise ValueError("Reserve colours for background and line")
  for _ in range(300):
    scene = _sample(counts, symmetric, colors, t_heights, t_widths, o_heights,
                    o_widths, bg, line, width, height, tpos, opos, max_pocket_size)
    if scene is not None:
      return scene
  raise RuntimeError('could not construct a valid scene')


_P1_T = ['...11111...', '..1177711..', '.111171111.', '13114141131',
         '13314441331', '11111111111', '..1661661..', '..1111111..',
         '...19991...', '....111....']
_P1_O = ['...11111...', '..11...11..', '.111...111.', '1.1111111.1',
         '1..1...1..1', '1.1111111.1', '.11..1..11.', '..1111111..',
         '...1...1...', '...1...1...', '...11111...']
_P2_T = ['.22.22.', '2442442', '.22322.', '.23332.', '.23232.', '2228222',
         '..282..', '..282..', '.22822.', '.28882.', '2222222']
_P2_O = ['.22.22.', '2..2..2', '2..2..2', '.22.22.', '.2...2.', '.2...2.',
         '2222222', '..2.2..', '..2.2..', '.22.22.', '.2...2.', '22...22',
         '2222222']
_T1_T = ['..444444444..', '.43333488884.', '.43333488884.',
         '.44433488444.', '...4444444...', '..455424554..',
         '..455424554..', '..444222444..', '.41474247414.',
         '.44474447444.', '..477747774..', '4477777777744',
         '4' + '7' * 11 + '4', '4777744477774', '4444466644444',
         '.....444.....', '......4......']
_T1_O = ['...44...44...', '..4..444..4..', '.4....4....4.',
         '.4....4....4.', '.444..4..444.', '..444444444..',
         '.4...444...4.', '.4...4.4...4.', '.4444...4444.',
         '.4.444.444.4.', '.444.444.444.', '..4...4...4..',
         '44.........44', '.4.........4.', '.4....4....4.',
         '.44444444444.', '....4...4....', '....44444....']
_T2_T = ['....222....', '....282....', '...28882...', '22222222222',
         '21127772992', '22227772222', '..2772772..', '..2222222..',
         '.288828882.', '.288828882.', '25222322252', '22.23332.22',
         '....222....', '....2.2....']
_T2_O = ['....222....', '...22.22...', '.222...222.', '2..22.22..2',
         '2..2.2.2..2', '2222...2222', '.22.....22.', '.222222222.',
         '.2...2...2.', '.2...2...2.', '2.222.222.2', '2222...2222',
         '...22.22...', '....222....']


def validate():
  """Reconstructs the canonical fixtures from explicit sprite placements."""
  train = [
      generate(template_sprite=_P1_T, outline_sprite=_P1_O, bg=8, width=22,
               height=22, tpos=(8, 10), opos=(2, 1)),
      generate(template_sprite=_P2_T, outline_sprite=_P2_O, bg=1, width=22,
               height=22, tpos=(0, 1), opos=(5, 11)),
  ]
  test = [
      generate(template_sprite=_T1_T, outline_sprite=_T1_O, bg=0, width=30,
               height=30, tpos=(1, 1), opos=(11, 16)),
      generate(template_sprite=_T2_T, outline_sprite=_T2_O, bg=4, width=28,
               height=28, tpos=(1, 13), opos=(9, 0)),
  ]
  return {'train': train, 'test': test}
