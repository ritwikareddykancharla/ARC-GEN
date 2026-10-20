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

"""ARC task 5dbc8537: fill the holes of a frame with the scattered pieces.

Rule: the input has a solid rectangular frame region of one colour along one
side of the grid (left, right, top or bottom). One background line separates
it from the rest of the grid. Holes of background colour are cut into the
frame. The rest of the grid holds rectangular pieces, which may be
multicoloured. Background separates the pieces from each other. The output is
the frame region with every hole tiled exactly by the pieces. Pieces are not
rotated and each piece is used once. One connected hole may be filled by
several pieces.

Scope: the frame side, frame depth, grid size, background colour, frame colour,
piece shapes and piece colourings are all sampled. Colourings are solid,
checkerboard, bordered checker, end-capped or staggered. Pieces of the same
shape share one colouring, as in every demonstration, so duplicates occur.
Holes may be isolated, or they may touch to form compound holes. A local
exhaustive tiling check rejects any scene whose holes could be filled in more
than one visibly different way. Grid sizes other than those in the fixtures
are synthetic extensions of the same mechanism.
"""

import collections
import random

import common

SIDES = ("left", "right", "top", "bottom")


def _solid(h, w, colour):
  return [[colour] * w for _ in range(h)]


def _box(width, height, side, extent):
  """Returns (row0, col0, box_height, box_width) of the frame region."""
  if side == "left":
    return 0, 0, height, extent
  if side == "right":
    return 0, width - extent, height, extent
  if side == "top":
    return 0, 0, extent, width
  return height - extent, 0, extent, width


def _in_region(r, c, width, height, side, extent):
  """True if (r, c) is in the piece area (outside the box and the gap line)."""
  if side == "left":
    return c > extent
  if side == "right":
    return c < width - extent - 1
  if side == "top":
    return r > extent
  return r < height - extent - 1


def _hole_allowed(side, bh, bw, r, c):
  """Holes avoid the inner edge line and the two outer corners of the box.

  This keeps the bounding box of the frame colour equal to the frame region.
  """
  if side == "left":
    return c != bw - 1 and not (c == 0 and r in (0, bh - 1))
  if side == "right":
    return c != 0 and not (c == bw - 1 and r in (0, bh - 1))
  if side == "top":
    return r != bh - 1 and not (r == 0 and c in (0, bw - 1))
  return r != 0 and not (r == bh - 1 and c in (0, bw - 1))


def _pattern(h, w, palette):
  """Samples a colouring for an h x w rectangular piece."""
  c1, c2 = random.sample(palette, 2)
  kinds = ["solid"] * 3
  if h * w >= 2:
    kinds.append("checker")
  if h >= 3 and w >= 3:
    kinds += ["bordered", "bordered"]
  if h >= 3 or w >= 3:
    kinds.append("cap")
  if h == 2 and w >= 3:
    kinds.append("stagger")
  kind = random.choice(kinds)
  if kind == "solid":
    return _solid(h, w, c1)
  if kind == "checker":
    return [[c1 if (r + c) % 2 == 0 else c2 for c in range(w)]
            for r in range(h)]
  if kind == "bordered":
    return [[c2 if (0 < r < h - 1 and 0 < c < w - 1 and (r + c) % 2 == 0)
             else c1 for c in range(w)] for r in range(h)]
  if kind == "stagger":
    return [[c1] * (w - 1) + [c2], [c2] + [c1] * (w - 1)]
  pat = _solid(h, w, c1)
  if h >= 3 and (w < 3 or random.random() < 0.5):
    rr = random.choice((0, h - 1))
    pat[rr] = [c2] * w
  else:
    cc = random.choice((0, w - 1))
    for row in pat:
      row[cc] = c2
  return pat


def _unique_fill(holes, patterns, limit=30000):
  """True if every exact tiling of the holes gives the same colouring."""
  keys = [tuple((r, c, v) for r, row in enumerate(p) for c, v in enumerate(row))
          for p in patterns]
  counts = collections.Counter(keys)
  distinct = list(counts)
  free = set(holes)
  fill = {}
  results = set()
  budget = [limit]

  def search():
    budget[0] -= 1
    if budget[0] < 0:
      return True
    if not free:
      results.add(tuple(sorted(fill.items())))
      return len(results) > 1
    y, x = min(free)
    for k in distinct:
      if counts[k] == 0:
        continue
      cells = [(y + dy, x + dx) for dy, dx, _ in k]
      if all(cell in free for cell in cells):
        counts[k] -= 1
        for cell, item in zip(cells, k):
          free.discard(cell)
          fill[cell] = item[2]
        stop = search()
        for cell in cells:
          free.add(cell)
          del fill[cell]
        counts[k] += 1
        if stop:
          return True
    return False

  search()
  return budget[0] >= 0 and len(results) == 1


def _render(width, height, side, extent, background, frame, pieces):
  grid = common.grid(width, height, background)
  r0, c0, bh, bw = _box(width, height, side, extent)
  for r in range(bh):
    for c in range(bw):
      grid[r0 + r][c0 + c] = frame
  out = [[frame] * bw for _ in range(bh)]
  for pattern, target, source in pieces:
    tr, tc = target
    sr, sc = source
    for dr, row in enumerate(pattern):
      for dc, colour in enumerate(row):
        grid[r0 + tr + dr][c0 + tc + dc] = background
        out[tr + dr][tc + dc] = colour
        grid[sr + dr][sc + dc] = colour
  return grid, out


def _axes(side, width, height):
  """Returns (along, across) sizes for a side: along is the frame-depth axis."""
  if side in ("left", "right"):
    return width, height
  return height, width


def _feasible_sides(width, height, side, extent):
  """Returns the sides compatible with the given overrides, or raises."""
  for name, val in (("width", width), ("height", height)):
    if val is not None and (type(val) is not int or not 1 <= val <= 30):
      raise ValueError("%s must be in 1..30" % name)
  if side is not None and side not in SIDES:
    raise ValueError("side must be one of %s" % (SIDES,))
  if extent is not None and (type(extent) is not int or extent < 4):
    raise ValueError("extent must be at least 4")
  options = []
  for s in ([side] if side is not None else SIDES):
    along, across = _axes(s, width, height)
    if across is not None and across < 4:
      continue
    if along is not None:
      if extent is not None:
        if along - extent - 1 < max(4, extent - 4):
          continue
      elif along < 9:
        continue
    elif extent is not None and extent > 16:
      continue
    options.append(s)
  if not options:
    raise ValueError("width/height/side/extent overrides leave no room for a "
                     "piece area large enough to hold the pieces")
  return options


def _pick_extent(along):
  """Samples a frame depth; caps it when the grid size on that axis is fixed."""
  if along is None:
    return random.randint(5, 10)
  hi = min(10, along - 5, (along + 3) // 2)
  if hi < 4:
    return None
  return random.randint(min(5, hi), hi)


def _sample_scene(width, height, sides, extent, background, frame, relaxed,
                  num_pieces=None):
  """Builds one random latent scene, or returns None if constraints fail."""
  side = random.choice(sides)
  bg = background if background is not None else random.randint(0, 9)
  if frame is not None:
    fr = frame
  else:
    fr = random.choice([c for c in range(10) if c != bg])
  palette = [c for c in range(10) if c not in (bg, fr)]
  along, across = _axes(side, width, height)
  ext = extent if extent is not None else _pick_extent(along)
  if ext is None:
    return None
  if along is None:
    hi = min(20, 29 - ext)
    lo = max(min(max(6, ext - 2), hi), ext - 4, 4)
    if lo > hi:
      return None
    along = ext + 1 + random.randint(lo, hi)
  if across is None:
    across = random.randint(10, 30)
  if side in ("left", "right"):
    w, h = along, across
    reg_h, reg_w = h, w - ext - 1
  else:
    w, h = across, along
    reg_h, reg_w = h - ext - 1, w
  if not (1 <= w <= 30 and 1 <= h <= 30) or ext < 4:
    return None
  if reg_h < 4 or reg_w < 4:
    return None
  r0, c0, bh, bw = _box(w, h, side, ext)
  if bh < 4 or bw < 4:
    return None
  allowed = set((r, c) for r in range(bh) for c in range(bw)
                if _hole_allowed(side, bh, bw, r, c))
  maxh = min(6, reg_h, bh)
  maxw = min(6, reg_w, bw)
  touch = (not relaxed) and random.random() < 0.55
  if relaxed:
    target = int(bh * bw * random.uniform(0.12, 0.2))
  else:
    target = int(bh * bw * random.uniform(0.22, 0.45))
  holes = set()
  placed = []
  shapes = {}
  for _ in range(150):
    if ((num_pieces is None and (len(holes) >= target or len(placed) >= 14))
        or (num_pieces is not None and len(placed) >= num_pieces)):
      break
    if random.random() < 0.18:
      ph = pw = 1
    else:
      ph = random.randint(1, maxh)
      pw = random.randint(1, maxw)
      if ph * pw < 2 or ph * pw > 24:
        continue
    pat = shapes[(ph, pw)] if (ph, pw) in shapes else _pattern(ph, pw, palette)
    want_adj = touch and bool(holes) and random.random() < 0.5
    spot = None
    spot_cells = None
    for _ in range(40):
      tr = random.randint(0, bh - ph)
      tc = random.randint(0, bw - pw)
      cells = [(tr + i, tc + j) for i in range(ph) for j in range(pw)]
      if any(cell not in allowed or cell in holes for cell in cells):
        continue
      adj = any((a + da, b + db) in holes for a, b in cells
                for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)))
      if want_adj and not adj:
        continue
      if not touch and adj:
        continue
      spot, spot_cells = (tr, tc), cells
      break
    if spot is None:
      continue
    shapes[(ph, pw)] = pat
    holes.update(spot_cells)
    placed.append([pat, spot, None])
  if len(placed) < 3 or (num_pieces is not None and len(placed) != num_pieces):
    return None
  # Scatter the pieces in the piece area, separated by background (8-gap).
  blocked = set()
  order = sorted(range(len(placed)),
                 key=lambda i: -len(placed[i][0]) * len(placed[i][0][0]))
  for i in order:
    pat = placed[i][0]
    ph, pw = len(pat), len(pat[0])
    src = None
    src_cells = None
    for _ in range(400):
      sr = random.randint(0, h - ph)
      sc = random.randint(0, w - pw)
      cells = [(sr + a, sc + b) for a in range(ph) for b in range(pw)]
      if all(_in_region(a, b, w, h, side, ext) and (a, b) not in blocked
             for a, b in cells):
        src, src_cells = (sr, sc), cells
        break
    if src is None:
      return None
    placed[i][2] = src
    for a, b in src_cells:
      for da in (-1, 0, 1):
        for db in (-1, 0, 1):
          blocked.add((a + da, b + db))
  pieces = [(p, t, s) for p, t, s in placed]
  grid, _ = _render(w, h, side, ext, bg, fr, pieces)
  counts = collections.Counter(v for row in grid for v in row)
  others = [n for col, n in counts.items() if col not in (bg, fr)]
  if counts[bg] <= counts[fr] or any(n >= counts[fr] for n in others):
    return None
  if not _unique_fill(holes, [p for p, _, _ in pieces]):
    return None
  return w, h, side, ext, bg, fr, pieces


def _check_pieces(width, height, side, extent, background, frame, pieces):
  """Validate explicit latent geometry before writing cells."""
  if (any(type(v) is not int or not 1 <= v <= 30 for v in (width, height))
      or side not in SIDES or type(extent) is not int
      or not 1 <= extent < (width if side in ('left','right') else height)):
    raise ValueError("invalid frame geometry")
  _, _, bh, bw = _box(width, height, side, extent)
  targets, sources = set(), set()
  for pattern, target, source in pieces:
    if (not pattern or not pattern[0] or
        any(len(row) != len(pattern[0]) for row in pattern) or
        any(type(v) is not int or v not in range(10) or v in (background,frame)
            for row in pattern for v in row)):
      raise ValueError("piece must be a solid rectangular array of piece colours")
    if any(type(v) is not int for v in tuple(target)+tuple(source)):
      raise ValueError("piece origins must be integers")
    tr, tc = target
    sr, sc = source
    dest = {(tr+y,tc+x) for y in range(len(pattern))
            for x in range(len(pattern[0]))}
    src = {(sr+y,sc+x) for y in range(len(pattern))
           for x in range(len(pattern[0]))}
    if (dest & targets or any(not (0<=y<bh and 0<=x<bw)
                              for y,x in dest)):
      raise ValueError("piece targets overlap or leave the frame")
    if any(not (0<=y<height and 0<=x<width and
                _in_region(y,x,width,height,side,extent)) for y,x in src):
      raise ValueError("piece source leaves the outside piece area")
    if any((y+dy,x+dx) in sources for y,x in src
           for dy in (-1,0,1) for dx in (-1,0,1)):
      raise ValueError("source pieces must be separated")
    targets.update(dest)
    sources.update(src)
  if not pieces or not _unique_fill(targets,[p for p,_,_ in pieces]):
    raise ValueError("pieces need one visibly unique exact tiling")


def generate(width=None, height=None, side=None, extent=None,
             background=None, frame=None, pieces=None, num_pieces=None):
  """Returns an input/output pair.

  Args:
    width: grid width (sampled if None).
    height: grid height (sampled if None).
    side: side of the grid holding the frame: left, right, top or bottom.
    extent: depth of the frame region measured from that side (at least 4).
    background: background colour.
    frame: frame colour (must differ from background).
    num_pieces: exact random piece count in 3..20. With explicit pieces,
      must equal their count. Placement failure raises instead of dropping
      pieces. Without this control the density determines the count.
    pieces: list of (pattern, (target_row, target_col), (source_row,
      source_col)). pattern is a rectangular list of colour rows. target is
      measured in frame-box coordinates. source is the top-left grid cell
      where the piece lies in the input. When pieces is given, all other
      arguments are required and the scene is rendered exactly. If pieces is
      None, a fresh random scene is built and the other arguments act as
      optional overrides. Incompatible overrides raise ValueError.
  """
  for name, val in (("background", background), ("frame", frame)):
    if val is not None and (type(val) is not int or not 0 <= val <= 9):
      raise ValueError("%s must be a colour in 0..9" % name)
  if background is not None and frame is not None and background == frame:
    raise ValueError("frame colour must differ from background")
  if pieces is not None:
    missing = [n for n, v in (("width", width), ("height", height),
                               ("side", side), ("extent", extent),
                               ("background", background), ("frame", frame))
               if v is None]
    if missing:
      raise ValueError("explicit pieces require: %s" % ", ".join(missing))
    if num_pieces is not None and num_pieces != len(pieces):
      raise ValueError("num_pieces does not match explicit pieces")
    _check_pieces(width,height,side,extent,background,frame,pieces)
  else:
    if num_pieces is not None and (type(num_pieces) is not int or
                                   not 3 <= num_pieces <= 20):
      raise ValueError("num_pieces must be an integer in 3..20")
    sides = _feasible_sides(width, height, side, extent)
    scene = None
    for attempt in range(400):
      scene = _sample_scene(width, height, sides, extent, background, frame,
                            relaxed=attempt >= 250, num_pieces=num_pieces)
      if scene is not None:
        break
    if scene is None:
      raise RuntimeError("could not construct a valid scene for the overrides")
    width, height, side, extent, background, frame, pieces = scene
  grid, out = _render(width, height, side, extent, background, frame, pieces)
  return {"input": grid, "output": out}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  checker47 = [[4, 7, 4, 7, 4, 7], [7, 4, 7, 4, 7, 4],
               [4, 7, 4, 7, 4, 7], [7, 4, 7, 4, 7, 4]]
  ones = [[1, 1, 1], [1, 9, 1], [1, 1, 1], [1, 9, 1], [1, 1, 1]]
  sixeight = [[6, 6, 6, 6, 6], [6, 8, 6, 8, 6], [6, 6, 8, 6, 6],
              [6, 8, 6, 8, 6], [6, 6, 8, 6, 6], [6, 6, 6, 6, 6]]
  fournine = [[4, 4]] * 6 + [[9, 9]]
  twofive = [[2, 2, 2], [2, 5, 2], [2, 2, 2], [2, 5, 2], [2, 2, 2],
             [2, 5, 2], [2, 2, 2]]
  small47 = [[4, 7, 4, 7], [7, 4, 7, 4], [4, 7, 4, 7]]
  stag = [[9, 9, 9, 8], [8, 9, 9, 9]]
  s449 = [[4, 4, 9], [9, 4, 4]]
  train = [
      generate(width=15, height=15, side="left", extent=7, background=4,
               frame=9, pieces=[
                   (_solid(2, 5, 8), (0, 1), (1, 10)),
                   (_solid(6, 2, 3), (2, 2), (4, 8)),
                   (_solid(2, 2, 1), (8, 1), (4, 11)),
                   (_solid(1, 4, 5), (10, 2), (7, 11)),
                   (_solid(1, 4, 5), (14, 2), (11, 8)),
                   (_solid(3, 2, 7), (11, 3), (10, 13)),
                   ([[0]], (6, 4), (13, 9)),
               ]),
      generate(width=20, height=20, side="bottom", extent=9, background=8,
               frame=2, pieces=[
                   (checker47, (3, 13), (1, 1)),
                   (_solid(5, 1, 9), (2, 10), (2, 8)),
                   (_solid(5, 2, 6), (3, 2), (1, 10)),
                   (ones, (2, 4), (2, 14)),
                   ([[0]], (1, 5), (4, 18)),
                   ([[0]], (4, 19), (7, 18)),
                   (_solid(4, 2, 5), (1, 11), (6, 2)),
                   (_solid(2, 3, 3), (6, 7), (8, 6)),
                   (_solid(2, 2, 4), (3, 0), (8, 15)),
               ]),
  ]
  test = [
      generate(width=25, height=25, side="top", extent=10, background=1,
               frame=3, pieces=[
                   (_solid(8, 2, 9), (1, 22), (11, 1)),
                   (sixeight, (2, 11), (11, 7)),
                   (fournine, (1, 3), (11, 15)),
                   (fournine, (1, 7), (17, 4)),
                   (twofive, (2, 0), (11, 19)),
                   (_solid(2, 4, 7), (3, 16), (18, 7)),
                   (_solid(2, 2, 8), (2, 5), (19, 22)),
                   (_solid(2, 2, 8), (5, 9), (21, 1)),
                   (_solid(3, 2, 5), (2, 20), (20, 14)),
                   (_solid(4, 1, 6), (5, 24), (20, 19)),
                   ([[0]], (1, 13), (21, 7)),
                   ([[0]], (2, 18), (21, 9)),
                   ([[0]], (5, 18), (23, 7)),
                   ([[0]], (6, 6), (23, 9)),
               ]),
      generate(width=20, height=20, side="left", extent=8, background=3,
               frame=1, pieces=[
                   (small47, (13, 1), (1, 9)),
                   (stag, (11, 3), (1, 14)),
                   (_solid(2, 2, 6), (6, 2), (4, 16)),
                   (_solid(2, 2, 6), (16, 3), (5, 9)),
                   (_solid(1, 2, 5), (0, 1), (7, 13)),
                   (_solid(1, 2, 5), (1, 2), (9, 15)),
                   (_solid(1, 2, 5), (2, 3), (16, 13)),
                   (_solid(1, 2, 5), (3, 4), (18, 14)),
                   (s449, (8, 1), (8, 9)),
                   (s449, (18, 2), (17, 9)),
                   (_solid(1, 3, 8), (10, 2), (11, 10)),
                   ([[0]], (6, 5), (12, 18)),
                   ([[0]], (16, 5), (14, 18)),
                   ([[0]], (18, 5), (16, 18)),
                   (_solid(2, 6, 2), (4, 1), (13, 10)),
               ]),
  ]
  return {"train": train, "test": test}
