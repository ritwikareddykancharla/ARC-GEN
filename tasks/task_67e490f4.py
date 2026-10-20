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

"""ARC-GEN style generator for task 67e490f4.

Rule: the input holds one large solid rectangle of colour `big_color`. The
rectangle is pierced by holes in the background colour. Small single-colour
polyomino pieces are scattered over the rest of the grid. The output is the
rectangle, cropped out. Each hole is filled with a colour chosen by the
hole's shape. Pieces are compared with the hole up to rotation and
reflection. Among the pieces of that shape, the colour with the most copies
wins. If no piece has the hole's shape, the hole takes the rectangle's
colour. The fallback is only sampled when allow_unmatched=True.

Scope: the following are all sampled:
  * grid sides: 18..30 by default, 14..30 when given explicitly; sizes
    below 30 are synthetic extensions;
  * background colour and rectangle colour;
  * rectangle size and position;
  * rectangle style: a compact block or a full-width band.
Hole shapes are fresh hole-free polyominoes mixed with a fixture catalogue,
with 2-4 hole classes per scene. Pure procedural or catalogue modes are
also available. Holes are laid out with one of four symmetries: none,
left-right, up-down or four-fold mirror. Each winning colour gets 1-4 pieces.
Competing colours get strictly fewer copies of the same shape, so no
majority is tied. Decoy shapes that match no hole may also appear. Pieces
are shown in random orientations. Holes and pieces never touch each other,
even diagonally. Pieces never touch the rectangle.
"""

import random

import common

_LIB = [
    ["#"],
    ["##"],
    ["###"],
    ["####"],
    ["#####"],
    ["##", "#."],
    ["##", "##"],
    ["###", "#.."],
    ["###", ".#."],
    ["##.", ".##"],
    [".#.", "###", ".#."],
    ["###", "#..", "#.."],
    ["#.#", "###"],
    ["###", ".#.", ".#."],
    ["####", "#..."],
    ["##", "##", "#."],
    ["##.", ".#.", ".##"],
    ["#..", "##.", ".##"],
    ["######", "#....#"],
]


def _cells(pattern):
  if (not pattern or not pattern[0] or
      any(len(row)!=len(pattern[0]) for row in pattern) or
      any(ch not in "#." for row in pattern for ch in row) or
      not any("#" in row for row in pattern)):
    raise ValueError("pattern must be a nonempty rectangular #/. mask")
  return [(r, c) for r, row in enumerate(pattern)
          for c, ch in enumerate(row) if ch == "#"]


def _norm(cells):
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _orient(cells, k):
  out = []
  for r, c in cells:
    if k & 4:
      r, c = c, r
    if k & 1:
      r = -r
    if k & 2:
      c = -c
    out.append((r, c))
  return _norm(out)


def _canon(cells):
  return min(_orient(cells, k) for k in range(8))


def _dims(cells):
  return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _halo(cells):
  out = set()
  for r, c in cells:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        out.add((r + dr, c + dc))
  return out


def _build(width, height, bg, big_color, box, holes, pieces):
  """holes: box-relative cell lists; pieces: (colour, absolute cells)."""
  top, left, bh, bw = box
  grid = common.grid(width, height, bg)
  for r in range(bh):
    for c in range(bw):
      grid[top + r][left + c] = big_color
  for cells in holes:
    for r, c in cells:
      grid[top + r][left + c] = bg
  table = {}
  for colour, cells in pieces:
    for r, c in cells:
      grid[r][c] = colour
    key = _canon(cells)
    counts = table.setdefault(key, {})
    counts[colour] = counts.get(colour, 0) + 1
  output = [[big_color] * bw for _ in range(bh)]
  for cells in holes:
    counts = table.get(_canon(cells))
    if counts:
      best = max(counts.values())
      winners = [k for k, v in counts.items() if v == best]
      if len(winners) != 1:
        raise ValueError("tied majority colour for a hole shape")
      colour = winners[0]
    else:
      colour = big_color
    for r, c in cells:
      output[r][c] = colour
  return {"input": grid, "output": output}


def _connected(bh, bw, hole_set):
  cells = [(r, c) for r in range(bh) for c in range(bw)
           if (r, c) not in hole_set]
  seen = {cells[0]}
  stack = [cells[0]]
  while stack:
    r, c = stack.pop()
    for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
      if 0 <= nr < bh and 0 <= nc < bw and (nr, nc) not in hole_set:
        if (nr, nc) not in seen:
          seen.add((nr, nc))
          stack.append((nr, nc))
  return len(seen) == len(cells)


def _place_holes(classes, fits, bh, bw, sym, holes, blocked):
  """Places hole copies for each class; returns False if a class fails."""
  for idx in classes:
    want = random.randint(1, 3) if sym == "none" else random.randint(1, 2)
    placed = 0
    for _ in range(80):
      if placed >= want:
        break
      shape = random.choice(fits[idx])
      a, b = _dims(shape)
      if bh - 1 - a < 1 or bw - 1 - b < 1:
        continue
      r0 = random.randint(1, bh - 1 - a)
      c0 = random.randint(1, bw - 1 - b)
      copies = [frozenset((r0 + r, c0 + c) for r, c in shape)]
      if sym in ("lr", "both"):
        copies += [frozenset((r, bw - 1 - c) for r, c in x) for x in copies]
      if sym in ("ud", "both"):
        copies += [frozenset((bh - 1 - r, c) for r, c in x) for x in copies]
      uniq = []
      for x in copies:
        if x not in uniq:
          uniq.append(x)
      good = True
      for i, x in enumerate(uniq):
        if any(cell in blocked for cell in x):
          good = False
        for y in uniq[i + 1:]:
          if x & _halo(y):
            good = False
      if not good:
        continue
      for x in uniq:
        holes.append(sorted(x))
        blocked |= _halo(x)
      placed += 1
    if placed == 0:
      return False
  return True


def _shape_bank(mode):
  """Sample fresh connected, hole-free shapes outside catalogue D4 classes."""
  if mode == "library":
    return list(_LIB)
  seen = {_canon(_cells(p)) for p in _LIB}
  fresh = []
  for _ in range(1000):
    if len(fresh)>=10:
      break
    h,w = random.randint(2,4),random.randint(2,5)
    count = random.randint(3,min(9,h*w))
    cells = {(random.randrange(h),random.randrange(w))}
    while len(cells)<count:
      frontier = {(y+dy,x+dx) for y,x in cells
                  for dy,dx in ((0,1),(0,-1),(1,0),(-1,0))
                  if 0<=y+dy<h and 0<=x+dx<w} - cells
      cells.add(random.choice(sorted(frontier)))
    cells = _norm(cells)
    key = _canon(cells)
    bh,bw = _dims(cells)
    # The complement in a padded box must remain connected: no inner islands.
    if key in seen or not _connected(bh+2,bw+2,{(y+1,x+1) for y,x in cells}):
      continue
    seen.add(key)
    fresh.append(["".join("#" if (y,x) in cells else "." for x in range(bw))
                  for y in range(bh)])
  if len(fresh)<10:
    raise ValueError("could not sample enough distinct fresh shape classes")
  return fresh if mode=="procedural" else list(_LIB)+fresh


def _random_scene(width, height, bg, big_color, allow_unmatched, shape_mode):
  patterns = _shape_bank(shape_mode)
  for _ in range(500):
    w_ = width if width is not None else random.randint(18, 30)
    h_ = height if height is not None else random.randint(18, 30)
    b_ = bg if bg is not None else random.randint(0, 9)
    if big_color is not None and big_color == b_:
      continue
    pool = [x for x in range(10) if x != b_]
    k_ = big_color if big_color is not None else random.choice(pool)
    others = [x for x in range(10) if x not in (b_, k_)]
    if random.random() < 0.25:
      bh = random.randint(5, min(8, h_ // 2 - 1))
      bw, left = w_, 0
    else:
      bh = random.randint(7, min(13, h_ - 6))
      bw = random.randint(7, min(13, w_ - 6))
      left = random.randint(0, w_ - bw)
    top = random.randint(0, h_ - bh)
    ih, iw = bh - 2, bw - 2
    fits = {}
    for i, pat in enumerate(patterns):
      base = _cells(pat)
      ors = sorted({_orient(base, k) for k in range(8)})
      ors = [o for o in ors if _dims(o)[0] <= ih and _dims(o)[1] <= iw]
      if ors:
        fits[i] = ors
    need = 3 if allow_unmatched else 2
    if len(fits) < need:
      continue
    nclass = random.randint(2, min(4, len(fits) - (need - 2)))
    classes = random.sample(sorted(fits), nclass)
    extra = []
    if allow_unmatched:
      extra = random.sample([i for i in sorted(fits) if i not in classes], 1)
    sym = random.choice(["none", "lr", "ud", "both"])
    holes = []
    if not _place_holes(classes + extra, fits, bh, bw, sym, holes, set()):
      continue
    hole_set = set(c for h in holes for c in h)
    if not _connected(bh, bw, hole_set):
      continue
    free = w_ * h_ - min(h_, bh + 2) * min(w_, bw + 2)
    budget = min(24, free // 12)
    specs = []
    for idx in classes:
      base = _cells(patterns[idx])
      win = random.choice(others)
      n_w = random.choice([1, 2, 2, 3, 3, 4])
      specs += [(win, base)] * n_w
      if n_w >= 2:
        m = random.choice([0, 1, 1, 2])
        for dcol in random.sample([o for o in others if o != win], m):
          specs += [(dcol, base)] * random.randint(1, n_w - 1)
    spare = [i for i in range(len(patterns)) if i not in classes + extra]
    for idx in random.sample(spare, random.randint(0, 2)):
      base = _cells(patterns[idx])
      for _ in range(random.randint(1, 2)):
        specs.append((random.choice(others), base))
    if len(specs) > budget:
      continue
    random.shuffle(specs)
    pblocked = set((r, c) for r in range(top - 1, top + bh + 1)
                   for c in range(left - 1, left + bw + 1))
    pieces = []
    ok_all = True
    for colour, base in specs:
      shape = _orient(base, random.randrange(8))
      a, b = _dims(shape)
      done = False
      if a <= h_ and b <= w_:
        for _ in range(300):
          r0 = random.randint(0, h_ - a)
          c0 = random.randint(0, w_ - b)
          cells = [(r0 + r, c0 + c) for r, c in shape]
          if any(cell in pblocked for cell in cells):
            continue
          pblocked |= _halo(cells)
          pieces.append((colour, cells))
          done = True
          break
      if not done:
        ok_all = False
        break
    if not ok_all:
      continue
    result = _build(w_, h_, b_, k_, (top, left, bh, bw), holes, pieces)
    counts = {}
    for row in result["input"]:
      for v in row:
        counts[v] = counts.get(v, 0) + 1
    if any(v >= counts[b_] for k, v in counts.items() if k != b_):
      continue
    return result
  raise RuntimeError("could not construct a valid scene")


def _check_colour(name, value):
  if value is not None and (type(value) is not int or value not in range(10)):
    raise ValueError(name + " must be a colour 0..9")


def generate(width=None, height=None, bg=None, big_color=None, box=None,
             holes=None, pieces=None, allow_unmatched=False, shape_mode=None):
  """Returns an input/output pair.

  Args:
    width: grid width; sampled 18..30 if None, explicit range 14..30.
    height: grid height; sampled 18..30 if None, explicit range 14..30.
    bg: background colour (sampled if None).
    big_color: colour of the pierced rectangle (sampled if None, != bg).
    box: (top, left, rect_height, rect_width) of the rectangle.
    holes: list of (row, col, pattern) holes. Offsets are relative to the
      box. pattern is a list of strings with '#' cells.
    pieces: list of (colour, row, col, pattern) loose pieces, in absolute
      grid coordinates.
    allow_unmatched: in random mode, add one hole class that no piece
      matches. That class shows the rectangle-colour fallback.
    shape_mode: 'mixed' (default), 'procedural', or 'library'. Procedural
      shapes are freshly sampled and exclude catalogue congruence classes.
  box, holes and pieces must be given together. Giving them selects
  explicit (fixture) mode, which also requires width, height, bg and
  big_color. If none of the three is given, a fresh random scene is built.
  """
  _check_colour("bg", bg)
  _check_colour("big_color", big_color)
  if type(allow_unmatched) is not bool:
    raise ValueError("allow_unmatched must be a boolean")
  if shape_mode not in (None,"mixed","procedural","library"):
    raise ValueError("unknown shape_mode")
  if bg is not None and big_color is not None and bg == big_color:
    raise ValueError("bg and big_color must differ")
  given = [box is not None, holes is not None, pieces is not None]
  if any(given) and not all(given):
    raise ValueError("box, holes and pieces must be given together")
  if all(given):
    if shape_mode is not None:
      raise ValueError("shape_mode only applies to random generation")
    if None in (width, height, bg, big_color):
      raise ValueError("explicit mode needs width, height, bg, big_color")
    if any(type(v) is not int or not 1<=v<=30 for v in (width,height)):
      raise ValueError("explicit grid sides must be integers in 1..30")
    top,left,bh,bw=box
    if (any(type(v) is not int for v in box) or min(top,left)<0
        or min(bh,bw)<1 or top+bh>height or left+bw>width):
      raise ValueError("rectangle box is outside the grid")
    hole_cells = [[(r + dr, c + dc) for dr, dc in _cells(p)]
                  for r, c, p in holes]
    piece_cells = [(col, [(r + dr, c + dc) for dr, dc in _cells(p)])
                   for col, r, c, p in pieces]
    used=set()
    for cells in hole_cells:
      if any(type(y) is not int or type(x) is not int or
             not(0<y<bh-1 and 0<x<bw-1) for y,x in cells):
        raise ValueError("holes must be strictly inside the rectangle")
      if used.intersection(cells):
        raise ValueError("holes overlap")
      used.update(cells)
    if not _connected(bh,bw,used):
      raise ValueError("pierced rectangle must stay connected")
    occupied=set()
    for colour,cells in piece_cells:
      _check_colour("piece",colour)
      if colour==bg:
        raise ValueError("piece cannot use background")
      if any(type(y) is not int or type(x) is not int or
             not(0<=y<height and 0<=x<width) or
             (top<=y<top+bh and left<=x<left+bw) for y,x in cells):
        raise ValueError("pieces must lie outside the rectangle inside the grid")
      if occupied.intersection(cells):
        raise ValueError("pieces overlap")
      occupied.update(cells)
    return _build(width, height, bg, big_color, box, hole_cells, piece_cells)
  for name, value in (("width", width), ("height", height)):
    if value is not None and (type(value) is not int or not 14 <= value <= 30):
      raise ValueError(name + " must be in 14..30 for random scenes")
  return _random_scene(width, height, bg, big_color, allow_unmatched,
                       shape_mode or "mixed")


def validate():
  """Reconstructs the original task pairs from explicit latent scenes."""
  sq = ["##", "##"]
  vd = ["#", "#"]
  hd = ["##"]
  pl = [".#.", "###", ".#."]
  s = ["#"]
  train = [
      generate(width=30, height=30, bg=1, big_color=4, box=(1, 15, 11, 11),
               holes=[(1, 1, sq), (1, 8, sq), (8, 1, sq), (8, 8, sq),
                      (1, 5, vd), (8, 5, vd), (5, 1, hd), (5, 8, hd),
                      (4, 4, pl)],
               pieces=[(8, 1, 3, sq), (2, 3, 8, sq), (2, 6, 2, sq),
                       (6, 8, 7, pl), (2, 13, 27, vd), (5, 14, 3, pl),
                       (8, 14, 10, sq), (2, 15, 17, sq), (8, 15, 22, sq),
                       (5, 18, 17, pl), (3, 22, 12, sq), (8, 22, 23, sq),
                       (8, 24, 2, sq), (9, 25, 19, vd), (9, 28, 9, hd)]),
      generate(width=30, height=30, bg=8, big_color=1, box=(1, 2, 13, 13),
               holes=[(1, 1, ["##", "#."]), (1, 10, ["##", ".#"]),
                      (10, 1, ["#.", "##"]), (10, 10, [".#", "##"]),
                      (1, 6, s), (6, 1, s), (6, 11, s), (11, 6, s),
                      (3, 3, ["###", "#..", "#.."]),
                      (3, 7, ["###", "..#", "..#"]),
                      (7, 3, ["#..", "#..", "###"]),
                      (7, 7, ["..#", "..#", "###"]), (5, 5, pl)],
               pieces=[(5, 1, 21, s), (2, 1, 24, ["#.", "##"]),
                       (4, 4, 18, ["##", "#."]), (2, 4, 27, ["##", ".#"]),
                       (5, 6, 22, s), (5, 9, 18, s),
                       (4, 9, 22, ["#.", "##"]), (7, 10, 26, pl),
                       (3, 12, 18, ["#..", "#..", "###"]), (5, 14, 23, s),
                       (2, 16, 3, [".#", "##"]), (5, 16, 12, s),
                       (9, 16, 15, pl), (5, 16, 26, s),
                       (3, 17, 23, ["###", "#..", "#.."]), (5, 18, 7, s),
                       (4, 18, 10, ["##", "#."]), (5, 20, 2, s),
                       (5, 20, 21, s), (6, 21, 16, ["###", "#..", "#.."]),
                       (7, 20, 26, pl), (4, 22, 6, ["#.", "##"]),
                       (5, 22, 10, s), (5, 23, 1, s), (7, 23, 22, pl),
                       (9, 25, 3, pl), (7, 25, 10, pl), (5, 26, 28, s),
                       (9, 26, 17, pl), (5, 28, 14, s), (5, 28, 24, s)]),
  ]
  v5 = ["#"] * 5
  test = [
      generate(width=30, height=30, bg=1, big_color=4, box=(0, 0, 7, 30),
               holes=[(1, 1, ["##", "#."]), (4, 1, ["#.", "##"]),
                      (1, 27, ["##", ".#"]), (4, 27, [".#", "##"]),
                      (2, 3, pl), (2, 24, pl),
                      (1, 6, ["###", ".#."]), (4, 6, [".#.", "###"]),
                      (1, 21, ["###", ".#."]), (4, 21, [".#.", "###"]),
                      (1, 10, v5), (1, 19, v5),
                      (1, 12, ["######", "#....#"]),
                      (4, 12, ["#....#", "######"]), (3, 14, hd)],
               pieces=[(8, 7, 13, pl), (7, 8, 2, [".#", "##"]),
                       (9, 8, 7, [".#.", "###"]), (2, 8, 25, hd),
                       (6, 9, 22, pl), (8, 10, 18, ["##", ".#"]),
                       (8, 12, 8, pl), (3, 12, 26, ["#.", "##"]),
                       (2, 14, 2, vd), (6, 14, 15, pl),
                       (9, 14, 21, ["#.", "##", "#."]),
                       (9, 16, 6, ["###", ".#."]), (6, 18, 1, pl),
                       (7, 18, 12, ["##", ".#"]),
                       (9, 18, 16, ["##", "#.", "#.", "#.", "#.", "##"]),
                       (8, 18, 24, pl), (3, 19, 6, pl),
                       (3, 21, 28, [".#", "##", ".#"]),
                       (2, 22, 11, [".#.", "###"]), (8, 22, 19, pl),
                       (2, 24, 7, vd), (7, 25, 2, ["#.", "##"]),
                       (2, 25, 16, ["#.", "##", "#."]), (9, 25, 25, pl),
                       (6, 27, 8, ["#####"]),
                       (3, 27, 20, [".#.", "###"])]),
  ]
  return {"train": train, "test": test}
