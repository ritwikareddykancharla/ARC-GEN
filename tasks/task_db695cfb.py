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

"""ARC task db695cfb generator.

Rule: the grid has one background colour with isolated cells of colour 1
and colour 6 on it. Any two 1-cells that share a diagonal (same row-col or
same row+col) are joined by a diagonal segment of 1s. Each 6 that lies
strictly inside such a segment emits a full diagonal line of 6. The line is
perpendicular to the segment and runs to both borders. All drawing paints
background cells only.

Scope:
- Random scenes vary the grid height and width, 8..30 per side by default.
  Explicit controls accept 4..30. Sides above 25 are a synthetic extension
  beyond the fixtures.
- The background is any colour except 1 and 6. Colours 0, 2, 7 and 9 are a
  synthetic extension; the fixtures use 3, 4, 5 and 8.
- Each scene has 1..4 joined pairs by default (num_pairs accepts 1..8). Each
  pair has a random diagonal orientation and a length of 2..min(h,w)-1 steps.
  Short segments (2 steps, a single interior cell) occur with low
  probability. Each pair carries 0..3 trigger 6s on its interior. Triggers
  may sit right next to an endpoint, as in train pair 1, and in some scenes
  triggers on one segment may be consecutive (adjacent parallel 6-lines).
- Some scenes reuse a 1 as the endpoint of two pairs, one on each diagonal
  through it. This is a synthetic extension; the reference joins every
  diagonal-sharing pair, so the cell is joined twice.
- Distractors are lone 1s that share no diagonal with any other 1, and 6s
  that lie on no segment interior. In most scenes the first distractors are
  placed as near misses: a 6 next to a segment interior but off it, a 6 on
  the diagonal extension of a segment beyond an endpoint (inert, because
  only 6s strictly inside a segment trigger), a 1 whose diagonal index
  (r+c or r-c) is within 2 of another 1's, as in train pair 4, or a 1 in the
  same row or column as another 1.

Deliberately excluded, because the demonstrations never show them and so
never fix the convention:
- A 6-line crossing the interior of another 1-segment. The crossing cell's
  colour would depend on the drawing order.
- A 6-line passing over any pre-existing 1 or 6 other than its own trigger.
  The demonstrations do not show whether the line is blocked or passes on.
- Diagonally adjacent 1s (a segment with no interior), which change nothing.
- Explicit scenes without any joined pair (they would be identity pairs).

Segments may cross other segments, and 6-lines may cross other 6-lines. Both
cases are order-independent. Explicit latent scenes (as used by validate)
are checked against the same invariants before rendering. They are also
checked so that the background is the strict plurality colour.
"""

import random

import common

_BACKGROUNDS = (0, 2, 3, 4, 5, 7, 8, 9)
_MAX_PAIRS = 8
_MAX_LONE = 12


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _sign(v):
  return 1 if v > 0 else -1


def _on_diag(a, b):
  dy, dx = b[0] - a[0], b[1] - a[1]
  return dy != 0 and abs(dy) == abs(dx)


def _interior(a, b):
  dy, dx = _sign(b[0] - a[0]), _sign(b[1] - a[1])
  n = abs(b[0] - a[0])
  return [(a[0] + k * dy, a[1] + k * dx) for k in range(1, n)]


def _adjacent(a, b):
  return max(abs(a[0] - b[0]), abs(a[1] - b[1])) <= 1


def _line_cells(trigger, dy, dx, height, width):
  """List the cells of the perpendicular 6-line through trigger.

  dy, dx give the direction of the segment. The trigger cell itself is
  excluded from the list.
  """
  pdy, pdx = dy, -dx
  cells = []
  for sgn in (1, -1):
    r, c = trigger[0] + sgn * pdy, trigger[1] + sgn * pdx
    while 0 <= r < height and 0 <= c < width:
      cells.append((r, c))
      r += sgn * pdy
      c += sgn * pdx
  return cells


def _render(height, width, background, ones, sixes, pairs):
  """Paint the input and output grids from latent scene objects."""
  inp = common.grid(width, height, background)
  for (r, c) in ones:
    inp[r][c] = 1
  for (r, c) in sixes:
    inp[r][c] = 6
  out = [row[:] for row in inp]
  sixset = set(sixes)
  for a, b in pairs:
    dy, dx = _sign(b[0] - a[0]), _sign(b[1] - a[1])
    hits = []
    for (r, c) in _interior(a, b):
      if (r, c) in sixset:
        hits.append((r, c))
      elif out[r][c] == background:
        out[r][c] = 1
    for s in hits:
      for (r, c) in _line_cells(s, dy, dx, height, width):
        if out[r][c] == background:
          out[r][c] = 6
  return {"input": inp, "output": out}


def _as_cell(p):
  try:
    cell = tuple(p)
  except TypeError:
    raise ValueError("cells must be (row, col) pairs")
  if len(cell) != 2 or not all(_is_int(v) for v in cell):
    raise ValueError("cells must be (row, col) pairs of integers")
  return cell


def _as_pair(p):
  try:
    pr = tuple(p)
  except TypeError:
    raise ValueError("pairs must be (cell, cell)")
  if len(pr) != 2:
    raise ValueError("pairs must be (cell, cell)")
  return (_as_cell(pr[0]), _as_cell(pr[1]))


def _as_list(v, convert, name):
  try:
    items = list(v)
  except TypeError:
    raise ValueError("%s must be a list" % name)
  return [convert(x) for x in items]


def _check_scene(height, width, background, ones, sixes, pairs):
  """Raise ValueError if the latent scene is not a valid, unambiguous input."""
  if not (_is_int(height) and _is_int(width)):
    raise ValueError("grid sides must be integers")
  if not (1 <= height <= 30 and 1 <= width <= 30):
    raise ValueError("grid sides must be in 1..30")
  if (not _is_int(background) or background not in range(10)
      or background in (1, 6)):
    raise ValueError("background must be a colour other than 1 and 6")
  if not pairs:
    raise ValueError("a scene needs at least one joined pair")
  cells = list(ones) + list(sixes)
  if len(set(cells)) != len(cells):
    raise ValueError("object cells must be distinct")
  for (r, c) in cells:
    if not (0 <= r < height and 0 <= c < width):
      raise ValueError("object cell out of bounds")
  n_bg = height * width - len(cells)
  if n_bg <= len(ones) or n_bg <= len(sixes):
    raise ValueError("background must be the strict plurality colour")
  ones_set = set(ones)
  six_set = set(sixes)
  wanted = set()
  for a, b in pairs:
    if a not in ones_set or b not in ones_set or not _on_diag(a, b):
      raise ValueError("each pair must join two 1-cells on a common diagonal")
    wanted.add(frozenset((a, b)))
  if len(wanted) != len(pairs):
    raise ValueError("duplicate pair")
  for i in range(len(ones)):
    for j in range(i + 1, len(ones)):
      if (_on_diag(ones[i], ones[j])
          and frozenset((ones[i], ones[j])) not in wanted):
        raise ValueError("pairs must list every diagonal-sharing pair of 1s")
  all_interior = set()
  for a, b in pairs:
    for p in _interior(a, b):
      if p in ones_set:
        raise ValueError("a 1-cell may not lie inside a segment")
      all_interior.add(p)
  object_set = set(cells)
  for a, b in pairs:
    dy, dx = _sign(b[0] - a[0]), _sign(b[1] - a[1])
    for p in _interior(a, b):
      if p not in six_set:
        continue
      for q in _line_cells(p, dy, dx, height, width):
        if q in object_set:
          raise ValueError("a 6-line may not pass over another object")
        if q in all_interior:
          raise ValueError("a 6-line may not cross a segment interior")


_NEIGHBOURS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0),
               (1, 1))


def _near_miss_candidate(kind, h, w, ones, seglist, pairs):
  """Propose a distractor cell close to the decision boundary, or None."""
  if kind == 6:
    if pairs and random.random() < 0.4:
      # A 6 on the diagonal extension of a segment, beyond an endpoint.
      a, b = random.choice(pairs)
      if random.random() < 0.5:
        a, b = b, a
      dy, dx = _sign(b[0] - a[0]), _sign(b[1] - a[1])
      k = random.randint(2, 4)
      q = (b[0] + k * dy, b[1] + k * dx)
    else:
      if not seglist:
        return None
      p = random.choice(seglist)
      d = random.choice(_NEIGHBOURS)
      q = (p[0] + d[0], p[1] + d[1])
  else:
    if not ones:
      return None
    o = random.choice(ones)
    if random.random() < 0.6:
      off = random.choice((-2, -1, 1, 2))
      r = random.randrange(h)
      if random.random() < 0.5:
        c = o[0] + o[1] + off - r
      else:
        c = r - (o[0] - o[1] + off)
      q = (r, c)
    elif random.random() < 0.5:
      q = (o[0], random.randrange(w))
    else:
      q = (random.randrange(h), o[1])
  if 0 <= q[0] < h and 0 <= q[1] < w:
    return q
  return None


def _check_controls(height, width, background, num_pairs, num_lone_ones,
                    num_lone_sixes):
  for side in (height, width):
    if side is not None and (not _is_int(side) or not 4 <= side <= 30):
      raise ValueError("random scenes need integer sides in 4..30")
  if background is not None and (not _is_int(background)
                                 or background not in range(10)
                                 or background in (1, 6)):
    raise ValueError("background must be a colour other than 1 and 6")
  if num_pairs is not None and (not _is_int(num_pairs)
                                or not 1 <= num_pairs <= _MAX_PAIRS):
    raise ValueError("num_pairs must be an integer in 1..%d" % _MAX_PAIRS)
  for cnt in (num_lone_ones, num_lone_sixes):
    if cnt is not None and (not _is_int(cnt) or not 0 <= cnt <= _MAX_LONE):
      raise ValueError("distractor counts must be integers in 0..%d"
                       % _MAX_LONE)


def _pick_len(nmax):
  """Pick a segment length (steps between endpoints), at least 2."""
  if nmax < 3 or random.random() < 0.12:
    return 2
  return random.randint(3, nmax)


def _sample_scene(height, width, background, num_pairs, num_lone_ones,
                  num_lone_sixes):
  """Sample a random valid scene honouring every supplied control."""
  _check_controls(height, width, background, num_pairs, num_lone_ones,
                  num_lone_sixes)
  for _ in range(300):
    h = height if height is not None else random.randint(8, 30)
    w = width if width is not None else random.randint(8, 30)
    bg = background if background is not None else random.choice(_BACKGROUNDS)
    npairs = num_pairs if num_pairs is not None else random.choice(
        (1, 1, 2, 2, 2, 3, 3, 4))
    nlone1 = num_lone_ones if num_lone_ones is not None else random.choice(
        (0, 0, 1, 2, 3))
    nlone6 = num_lone_sixes if num_lone_sixes is not None else random.choice(
        (0, 1, 2, 2, 3, 4))
    near_miss = random.random() < 0.7
    share_prob = random.choice((0.0, 0.0, 0.3, 0.5))
    gap = 1 if random.random() < 0.3 else 2
    pairs, ones, sixes, cells = [], [], [], []
    segcells, linecells = set(), set()
    degree, dtype = {}, {}
    ok = True
    for _ in range(npairs):
      placed = False
      for attempt in range(80):
        shared = None
        if attempt < 40 and random.random() < share_prob:
          cands = [e for e in ones if degree.get(e, 0) == 1]
          if cands:
            shared = random.choice(cands)
        if shared is not None:
          # New pair on the other diagonal through an existing endpoint.
          a = shared
          dy = random.choice((1, -1))
          dx = -dtype[a] * dy
          nmax = min(h - 1 - a[0] if dy > 0 else a[0],
                     w - 1 - a[1] if dx > 0 else a[1])
          if nmax < 2:
            continue
          n = _pick_len(nmax)
          b = (a[0] + dy * n, a[1] + dx * n)
          new_ends = [b]
        else:
          n = _pick_len(min(h, w) - 1)
          dy, dx = random.choice((1, -1)), random.choice((1, -1))
          y0 = random.randint(0, h - 1 - n) if dy > 0 else random.randint(n, h - 1)
          x0 = random.randint(0, w - 1 - n) if dx > 0 else random.randint(n, w - 1)
          a, b = (y0, x0), (y0 + dy * n, x0 + dx * n)
          new_ends = [a, b]
        inner = set(_interior(a, b))
        if any(e in segcells or e in linecells for e in new_ends):
          continue
        if inner & linecells:
          continue
        if any(_adjacent(e, c) for e in new_ends for c in cells):
          continue
        if any(c in inner for c in cells):
          continue
        if any(_on_diag(e, o) for e in new_ends for o in ones if o != shared):
          continue
        t = random.choice((0, 1, 1, 2, 2, 3))
        ks = list(range(1, n))
        random.shuffle(ks)
        chosen = []
        for k in ks:
          if len(chosen) >= t:
            break
          if all(abs(k - q) >= gap for q in chosen):
            chosen.append(k)
        trig = [(a[0] + k * dy, a[1] + k * dx) for k in chosen]
        if any(s in segcells or s in linecells for s in trig):
          continue
        if any(_adjacent(s, c) for s in trig for c in cells if c != shared):
          continue
        newline = set()
        for s in trig:
          newline.update(_line_cells(s, dy, dx, h, w))
        if newline & segcells:
          continue
        if any(c in newline for c in cells):
          continue
        pairs.append((a, b))
        for e in new_ends:
          ones.append(e)
          cells.append(e)
        degree[a] = degree.get(a, 0) + 1
        degree[b] = 1
        dtype[a] = dy * dx
        dtype[b] = dy * dx
        sixes += trig
        cells += trig
        segcells |= inner
        linecells |= newline
        placed = True
        break
      if not placed:
        ok = False
        break
    if not ok:
      continue
    seglist = sorted(segcells)
    for kind, count in ((1, nlone1), (6, nlone6)):
      for idx in range(count):
        placed = False
        for attempt in range(140):
          if near_miss and idx < 2 and attempt < 40:
            p = _near_miss_candidate(kind, h, w, ones, seglist, pairs)
            if p is None:
              continue
          else:
            p = (random.randrange(h), random.randrange(w))
          if p in segcells or p in linecells:
            continue
          if any(_adjacent(p, c) for c in cells):
            continue
          if kind == 1 and any(_on_diag(p, o) for o in ones):
            continue
          (ones if kind == 1 else sixes).append(p)
          cells.append(p)
          placed = True
          break
        if not placed:
          ok = False
          break
      if not ok:
        break
    if not ok:
      continue
    n_bg = h * w - len(cells)
    if n_bg <= len(ones) or n_bg <= len(sixes):
      continue
    return h, w, bg, ones, sixes, pairs
  raise ValueError("could not construct a scene with the requested parameters")


def generate(height=None, width=None, background=None, ones=None, sixes=None,
             pairs=None, num_pairs=None, num_lone_ones=None,
             num_lone_sixes=None):
  """Generate one input/output pair.

  height, width: grid dimensions (rows, columns). For a random scene they
    act as controls and must be integers in 4..30.
  background: background colour, an integer other than 1 or 6. Also a
    random-scene control.
  ones: explicit list of (row, col) cells of colour 1.
  sixes: explicit list of (row, col) cells of colour 6.
  pairs: explicit list of ((r, c), (r, c)) pairs of 1-cells. These must be
    exactly the pairs of 1s that share a diagonal, and there must be at
    least one. Supply ones, sixes and pairs together, along with height,
    width and background.
  num_pairs: random control, the number of joined pairs (1..8).
  num_lone_ones: random control, the number of unpaired distractor 1s
    (0..12).
  num_lone_sixes: random control, the number of 6s off every segment
    interior (0..12).

  With no explicit objects, a fresh random scene is sampled. Any supplied
  controls are honoured exactly, or a ValueError is raised.
  """
  explicit = (ones, sixes, pairs)
  if any(v is not None for v in explicit):
    if any(v is None for v in (height, width, background) + explicit):
      raise ValueError("explicit scenes need height, width, background, "
                       "ones, sixes and pairs together")
    if any(v is not None for v in (num_pairs, num_lone_ones, num_lone_sixes)):
      raise ValueError("count controls apply only to random scenes")
    ones = _as_list(ones, _as_cell, "ones")
    sixes = _as_list(sixes, _as_cell, "sixes")
    pairs = _as_list(pairs, _as_pair, "pairs")
  else:
    height, width, background, ones, sixes, pairs = _sample_scene(
        height, width, background, num_pairs, num_lone_ones, num_lone_sixes)
  _check_scene(height, width, background, ones, sixes, pairs)
  return _render(height, width, background, ones, sixes, pairs)


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(15, 12, 5, [(3, 1), (9, 7)],
               [(2, 9), (5, 3), (8, 6), (13, 4)], [((3, 1), (9, 7))]),
      generate(8, 11, 8, [(1, 6), (6, 1)], [(3, 4)], [((1, 6), (6, 1))]),
      generate(9, 12, 4, [(1, 7), (7, 1)], [(6, 7)], [((1, 7), (7, 1))]),
      generate(15, 16, 8, [(2, 2), (3, 12), (11, 11), (14, 3)],
               [(1, 8), (9, 9), (10, 1), (14, 13)], [((2, 2), (11, 11))]),
      generate(9, 9, 4, [(2, 1), (7, 6)], [], [((2, 1), (7, 6))]),
  ]
  test = [
      generate(25, 21, 3,
               [(1, 9), (1, 17), (2, 2), (4, 14), (5, 2), (10, 10), (17, 9),
                (21, 18), (23, 3), (23, 11)],
               [(4, 4), (6, 6), (7, 14), (12, 19), (14, 11), (15, 2), (18, 8),
                (20, 12)],
               [((1, 17), (4, 14)), ((2, 2), (10, 10)), ((5, 2), (21, 18)),
                ((17, 9), (23, 3))]),
  ]
  return {"train": train, "test": test}
