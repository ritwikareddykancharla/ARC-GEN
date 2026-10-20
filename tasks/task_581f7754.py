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

"""ARC task 581f7754 (curated teaching copy): slide shapes onto marker lines.

Rule: the grid has a background colour, lone single-cell markers on the
border (not on corners) and multicolour shapes. A marker on the left or right
edge fixes a row. A marker on the top or bottom edge fixes a column. Every
shape that contains a marker colour is rigidly translated along one axis, so
that its key cell lands on that marker's line. The key colour is the
least-frequent marker colour inside the shape. Lone interior cells of a marker
colour are shapes too, so they also move. Shapes with no marker colour, and
the markers themselves, stay put. Moving shapes are erased first and then
redrawn. Cells pushed off the grid are dropped.

Scope: the random scenes use one axis per grid. Either all markers sit on the
left and right edges, or (by transposing) all sit on the top and bottom edges.
There are 1 to 3 marker colours, each on a random side, with an optional
duplicate marker on the opposite edge. Shapes are blobs, closed or open
frames (optionally with an interior key cell), bars or lone cells, with
optional accent colours. Some moving shapes have a body that is itself
another marker colour, which tests the least-frequent key rule. Static
distractor shapes and lone distractor cells are included. Some scenes let a
moving shape be partly pushed off the grid, as in the first test pair. Every
shape occupies its own column band (row band after transposing), separated
by at least one background column, and stays at Chebyshev distance >= 2 from
all markers, so nothing touches in the input and nothing overlaps in the
output. Grid sizes from 7 to 30 per side are supported; default sizes go a
little beyond the fixtures (synthetic extension).

validate() rebuilds the curated teaching copy through explicit latent
arguments. In that copy, train[1].output has an 8-cell correction from
upstream PR arcprize/ARC-AGI-2#52.
"""

import copy
import random

import common


def _cells(r0, c0, sprite):
  out = []
  for i, row in enumerate(sprite):
    for j, ch in enumerate(row):
      if ch != ".":
        out.append((r0 + i, c0 + j, int(ch)))
  return out


def _render(width, height, background, markers, shapes):
  """Draws the latent scene and applies the latent translation rule."""
  grid = common.grid(width, height, background)
  for r, c, col in markers:
    if not (0 <= r < height and 0 <= c < width):
      raise ValueError("marker outside the grid")
    grid[r][c] = col
  objs = []
  for r0, c0, sprite in shapes:
    cells = sorted(_cells(r0, c0, sprite))
    for r, c, col in cells:
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError("shape outside the grid")
      grid[r][c] = col
    objs.append(cells)
  lines = {}
  for r, c, col in sorted(markers):
    on_lr = c in (0, width - 1)
    on_tb = r in (0, height - 1)
    if on_lr and not on_tb:
      lines.setdefault(col, (r, None))
    elif on_tb and not on_lr:
      lines.setdefault(col, (None, c))
  output = copy.deepcopy(grid)
  moves = []
  for cells in sorted(objs):
    counts = {}
    for _, _, col in cells:
      counts[col] = counts.get(col, 0) + 1
    cand = [col for col in counts if col in lines]
    if not cand:
      continue
    key = min(cand, key=lambda col: counts[col])
    kr, kc = next((r, c) for r, c, col in cells if col == key)
    row, column = lines[key]
    dr = row - kr if row is not None else 0
    dc = column - kc if column is not None else 0
    moves.append((cells, dr, dc))
  for cells, _, _ in moves:
    for r, c, _ in cells:
      output[r][c] = background
  for cells, dr, dc in moves:
    for r, c, col in cells:
      nr, nc = r + dr, c + dc
      if 0 <= nr < height and 0 <= nc < width:
        output[nr][nc] = col
  return {"input": grid, "output": output}


def _connected(shape):
  shape = set(shape)
  if not shape:
    return False
  start = min(shape)
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
      p = (r + dr, c + dc)
      if p in shape and p not in seen:
        seen.add(p)
        stack.append(p)
  return len(seen) == len(shape)


def _blob(h, w, size):
  cells = {(random.randrange(h), random.randrange(w))}
  for _ in range(600):
    if len(cells) >= size:
      break
    r, c = random.choice(sorted(cells))
    dr, dc = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
    nr, nc = r + dr, c + dc
    if 0 <= nr < h and 0 <= nc < w:
      cells.add((nr, nc))
  return cells


def _sprite_colours(w, kind, key, body, accent):
  """Returns a dict of relative cell -> colour for one shape."""
  if kind == "lone":
    return {(0, 0): key}
  if kind == "lone_distractor":
    return {(0, 0): body}
  if w >= 3 and random.random() < 0.45:
    h = random.randint(3, 5)
    shape = set((i, j) for i in range(h) for j in range(w)
                if i in (0, h - 1) or j in (0, w - 1))
    if random.random() < 0.3:
      side = random.randrange(4)
      if side == 0:
        shape -= set((0, j) for j in range(1, w - 1))
      elif side == 1:
        shape -= set((h - 1, j) for j in range(1, w - 1))
      elif side == 2:
        shape -= set((i, 0) for i in range(1, h - 1))
      else:
        shape -= set((i, w - 1) for i in range(1, h - 1))
    interior = [(i, j) for i in range(1, h - 1) for j in range(1, w - 1)]
    if interior and random.random() < 0.5:
      kc = random.choice(interior)
      shape.add(kc)
    else:
      kc = random.choice(sorted(shape))
  else:
    h = random.randint(1, 5)
    if h * w < 2:
      h = 2
    size = random.randint(max(2, (h * w + 1) // 2), h * w)
    shape = _blob(h, w, size)
    kc = random.choice(sorted(shape))
  if not _connected(shape):
    return None
  colours = {p: body for p in shape}
  if key is not None:
    colours[kc] = key
  if accent is not None and random.random() < 0.3:
    choices = [p for p in sorted(shape) if p != kc]
    if choices:
      colours[random.choice(choices)] = accent
  return colours


def _far(cells, markers):
  for r, c in cells:
    for mr, mc, _ in markers:
      if max(abs(r - mr), abs(c - mc)) < 2:
        return False
  return True


def _make_shape(hc, c0, w, kind, key, body, accent, mrow, mcols, markers,
                allow_clip):
  for _ in range(30):
    colours = _sprite_colours(w, kind, key, body, accent)
    if colours is None:
      continue
    counts = {}
    for col in colours.values():
      counts[col] = counts.get(col, 0) + 1
    present = [col for col in counts if col in mcols]
    if kind in ("move", "lone"):
      if counts.get(key) != 1:
        continue
      if any(counts[col] < 2 for col in present if col != key):
        continue
    else:
      if present:
        continue
    mi = min(i for i, _ in colours)
    mj = min(j for _, j in colours)
    rel = {(i - mi, j - mj): col for (i, j), col in colours.items()}
    sh = max(i for i, _ in rel) + 1
    sw = max(j for _, j in rel) + 1
    if sh > hc:
      continue
    sprite = []
    for i in range(sh):
      sprite.append("".join(str(rel[(i, j)]) if (i, j) in rel else "."
                            for j in range(sw)))
    cc0 = c0 + mj
    target = None
    if kind in ("move", "lone"):
      kr = next(i for (i, j), col in rel.items() if col == key)
      target = mrow[key] - kr
      # The key cell always lands on the marker line (inside the grid); other
      # cells may leave the grid only in scenes that allow clipping.
      if not allow_clip and not 0 <= target <= hc - sh:
        continue
    if len(rel) == 1:
      lo, hi = 1, hc - 2
    else:
      lo, hi = 0, hc - sh
    starts = []
    for s in range(lo, hi + 1):
      if s == target:
        continue
      if _far([(s + i, cc0 + j) for (i, j) in rel], markers):
        starts.append(s)
    if not starts:
      continue
    return (random.choice(starts), cc0, sprite)
  return None


def _spaced_lines(length, count):
  """Picks count distinct interior lines at mutual distance >= 2."""
  cand = list(range(1, length - 1))
  random.shuffle(cand)
  chosen = []
  for r in cand:
    if all(abs(r - q) >= 2 for q in chosen):
      chosen.append(r)
      if len(chosen) == count:
        return chosen
  return None


def _random_scene(width, height, background, axis, num_marker_colours):
  want = axis if axis is not None else random.choice(["row", "col"])
  # hc is the extent along which shapes slide; wc holds the column bands.
  if want == "row":
    fixed_hc, fixed_wc = height, width
  else:
    fixed_hc, fixed_wc = width, height
  for _ in range(400):
    hc = fixed_hc if fixed_hc is not None else random.randint(8, 30)
    wc = fixed_wc if fixed_wc is not None else random.randint(8, 30)
    bg = background if background is not None else random.randrange(10)
    palette = [c for c in range(10) if c != bg]
    random.shuffle(palette)
    nm = (num_marker_colours if num_marker_colours is not None
          else random.randint(1, 3))
    mcols = palette[:nm]
    others = palette[nm:]
    rows = _spaced_lines(hc, nm)
    if rows is None:
      continue
    markers = []
    mrow = {}
    for col, r in zip(mcols, rows):
      mrow[col] = r
      side = random.choice([0, wc - 1])
      markers.append((r, side, col))
      if random.random() < 0.15:
        markers.append((r, wc - 1 - side, col))
    bands = []
    cur = random.randint(1, 3)
    for _ in range(14):
      w = random.choice([1, 2, 3, 3, 4])
      if cur + w - 1 > wc - 2:
        break
      bands.append((cur, w))
      cur += w + 1 + random.randint(0, 2)
    if len(bands) < 2:
      continue
    if len(bands) > 7:
      bands = sorted(random.sample(bands, 7))
    allow_clip = random.random() < 0.3
    shapes = []
    moving = 0
    for c0, w in bands:
      u = random.random()
      accent = random.choice(others) if random.random() < 0.5 else None
      if u < 0.15:
        kind, key, body = "lone", random.choice(mcols), None
      elif u < 0.27:
        kind, key, body = "distractor", None, random.choice(others)
      elif u < 0.33:
        kind, key, body = "lone_distractor", None, random.choice(others)
      else:
        kind, key = "move", random.choice(mcols)
        if nm >= 2 and random.random() < 0.3:
          body = random.choice([c for c in mcols if c != key])
        else:
          body = random.choice(others)
      if accent == body:
        accent = None
      shape = _make_shape(hc, c0, w, kind, key, body, accent, mrow, mcols,
                          markers, allow_clip)
      if shape is None:
        continue
      shapes.append(shape)
      if kind in ("move", "lone"):
        moving += 1
    if moving < 1 or len(shapes) < 2:
      continue
    used = len(markers)
    for r0, c0, sprite in shapes:
      used += len(_cells(r0, c0, sprite))
    if used * 2 >= hc * wc:
      continue
    out_w, out_h = wc, hc
    if want == "col":
      markers = [(c, r, col) for r, c, col in markers]
      shapes = [(c0, r0, ["".join(row[j] for row in sprite)
                          for j in range(len(sprite[0]))])
                for r0, c0, sprite in shapes]
      out_w, out_h = hc, wc
    return out_w, out_h, bg, markers, shapes
  raise RuntimeError("could not build a scene for the requested controls")


def _check_explicit(width,height,background,markers,shapes):
  groups=[]
  marker_colours=set()
  for r,c,col in markers:
    if not (0<=r<height and 0<=c<width) or (r in (0,height-1))==(c in (0,width-1)):
      raise ValueError("marker must lie on exactly one border")
    if not isinstance(col,int) or col not in range(10) or col==background:
      raise ValueError("invalid marker colour")
    groups.append({(r,c)});marker_colours.add(col)
  for r,c,sprite in shapes:
    if not sprite or not sprite[0] or any(len(row)!=len(sprite[0]) for row in sprite):
      raise ValueError("sprite must be a nonempty rectangle")
    if any(ch not in ".0123456789" for row in sprite for ch in row):
      raise ValueError("sprite needs dots or colour digits")
    cells=_cells(r,c,sprite)
    if not cells or any(col==background for _,_,col in cells):
      raise ValueError("sprite must contain nonbackground cells")
    points={(y,x) for y,x,col in cells}
    if not _connected(points):
      raise ValueError("each sprite must be 4-connected")
    groups.append(points)
  occupied=set()
  for cells in groups:
    if any(not(0<=y<height and 0<=x<width) for y,x in cells):
      raise ValueError("object outside canvas")
    halo=cells | {(y+dy,x+dx) for y,x in cells for dy,dx in ((1,0),(-1,0),(0,1),(0,-1))}
    if halo & occupied:
      raise ValueError("input objects overlap or touch orthogonally")
    occupied |= cells


def generate(width=None, height=None, background=None, markers=None,
             shapes=None, axis=None, num_marker_colours=None):
  """Builds one input/output pair.

  Args:
    width: grid width. Required with an explicit scene; for random scenes an
      optional fixed width in 7..30.
    height: grid height. Required with an explicit scene; for random scenes an
      optional fixed height in 7..30.
    background: background colour. Required with an explicit scene; optional
      fixed colour 0..9 for random scenes.
    markers: explicit scene only: list of (row, col, colour) lone border cells.
    shapes: explicit scene only: list of (top, left, sprite). A sprite is a
      list of digit strings, where '.' means transparent.
    axis: random scenes only: 'row' (left/right markers, vertical slides) or
      'col' (top/bottom markers, horizontal slides). None picks one.
    num_marker_colours: random scenes only: number of marker colours (1..3).
  """
  for value in (width,height):
    if value is not None and (not isinstance(value,int) or not 1<=value<=30):
      raise ValueError("canvas sides must be integers in 1..30")
  if background is not None and (not isinstance(background,int) or background not in range(10)):
    raise ValueError("background must be a colour 0..9")
  if markers is not None or shapes is not None:
    if markers is None or shapes is None:
      raise ValueError("explicit scenes need both markers and shapes")
    if width is None or height is None or background is None:
      raise ValueError("explicit scenes need width, height and background")
    if axis is not None or num_marker_colours is not None:
      raise ValueError("axis/num_marker_colours only apply to random scenes")
    _check_explicit(width,height,background,markers,shapes)
    return _render(width, height, background, markers, shapes)
  if axis not in (None, "row", "col"):
    raise ValueError("axis must be 'row', 'col' or None")
  if num_marker_colours not in (None, 1, 2, 3):
    raise ValueError("num_marker_colours must be 1, 2 or 3")
  if background is not None and not 0 <= background <= 9:
    raise ValueError("background must be a colour 0..9")
  for v in (width, height):
    if v is not None and not 7 <= v <= 30:
      raise ValueError("random scene sizes must be in 7..30")
  scene = _random_scene(width, height, background, axis, num_marker_colours)
  return _render(*scene)


def validate():
  """Rebuilds the curated teaching fixtures from explicit latent scenes."""
  train = [
      generate(width=8, height=18, background=1, markers=[(17, 5, 4)],
               shapes=[(3, 1, ["888", "848"]),
                       (8, 4, ["..8", "884", "..8"]),
                       (13, 1, ["8.8", "848", "8.8", "888"])]),
      generate(width=21, height=10, background=8,
               markers=[(4, 0, 1), (8, 0, 6)],
               shapes=[(2, 2, ["4", "4", "4", "4", "6"]),
                       (2, 9, ["333", "313", "333"]),
                       (4, 4, ["333", "3.3", "3.3", "313"]),
                       (5, 14, ["...3", "3133", "...3"])]),
      generate(width=11, height=22, background=3, markers=[(0, 4, 2)],
               shapes=[(3, 1, ["111", ".1.", ".2.", "111"]),
                       (10, 3, ["11111", "1...1", "11121"]),
                       (16, 3, [".111.", "11211", "..1.."])]),
  ]
  test = [
      generate(width=20, height=14, background=8,
               markers=[(3, 0, 6), (10, 0, 4), (12, 0, 2), (12, 19, 2)],
               shapes=[(0, 3, ["666", "646"]),
                       (1, 13, ["464", "444", ".4."]),
                       (3, 6, ["2"]),
                       (5, 7, ["2"]),
                       (5, 3, [".4.", "444", "4.4", "444", ".6."]),
                       (6, 8, ["..4", "444", "446", "..4"]),
                       (6, 17, ["333", "3.3", "3.3", "363"]),
                       (7, 1, ["2"]),
                       (10, 12, ["2"])]),
      generate(width=22, height=11, background=4,
               markers=[(3, 21, 2), (8, 21, 8)],
               shapes=[(0, 12, ["31", "31", ".1", ".1", ".1", ".1", ".8"]),
                       (1, 1, ["..111..", "111.1..", "..1.111", "..121.."]),
                       (4, 15, ["..1", "111", "1.1", "2.1"]),
                       (6, 9, ["121", "1.1", "111"])]),
  ]
  return {"train": train, "test": test}
