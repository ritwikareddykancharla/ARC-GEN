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

"""ARC task da6e95e5: crop the shape whose corner frame shares its colour.

Rule: the grid has a plain background and several frames. Each frame is four
L-shaped corner brackets of one colour. Every bracket arm in a grid has the
same length, 2 or 3. Each frame holds one small single-colour shape that is
8-connected. The shape's bounding box sits exactly 2 cells inside the frame's
outer box. Exactly one frame holds a shape of the frame's own colour. The
output is that shape's bounding box, cropped from the input with the
background kept.

Scope: these values are all sampled:
  * the background colour;
  * the arm length;
  * the shape size, 2..5 per side and shared by every frame in a grid, as in
    the examples;
  * the frame count, 3..6 by default and capped by what fits;
  * the frame positions;
  * the frame and shape colours.

Frame colours may vary, may repeat (including the target's colour), or may all
be the same. Non-target shapes never match their own frame's colour. They often
use a different frame's colour as a decoy. Frames are separated by at least one
background row or column, so no components touch. Layouts are either free
random placements or jittered lattices. Lattice capacity is checked first, so
the requested frame counts always fit.

Scene validity: the target shape must be the only component whose bounding
box, grown by 2, has four corners of its own colour. A bracket of the target
frame can pass this test when same-coloured neighbouring frames supply its
grown corners. Such scenes are resampled, or rejected when replayed. The
background must be the strictly most common colour.

Every example is 30x30, and most random samples keep that size. As a
synthetic extension, other grid sizes are sampled from 16..30 per side. Only
sizes that can hold the requested frames are drawn. Explicit sides of 6..30,
shape sides of 1 or 6, and 2, 7 or 8 frames are also synthetic extensions.
A scene needs room for two frames of (side+4) cells plus a one-cell gap.
With the default 2..5 shape sides, one grid side must therefore be at least
13. Infeasible requests raise ValueError.
"""

import random

import common


def _is_int(x):
  return isinstance(x, int) and not isinstance(x, bool)


def _frame_cells(top, left, fh, fw, arm):
  cells = set()
  b, r = top + fh - 1, left + fw - 1
  for k in range(arm):
    cells.update([(top, left + k), (top + k, left), (top, r - k), (top + k, r),
                  (b, left + k), (b - k, left), (b, r - k), (b - k, r)])
  return cells


def _render(bg, arm, frames, wid=30, hgt=30):
  g = common.grid(wid, hgt, bg)
  if len(g) != hgt or any(len(row) != wid for row in g):
    raise ValueError('common.grid returned an unexpected shape')
  for top, left, fc, sc, pat in frames:
    h, w = len(pat), len(pat[0])
    if top < 0 or left < 0 or top + h + 4 > hgt or left + w + 4 > wid:
      raise ValueError('frame out of bounds')
    for r, c in _frame_cells(top, left, h + 4, w + 4, arm):
      g[r][c] = fc
    for i, row in enumerate(pat):
      for j, ch in enumerate(row):
        if ch == '#':
          g[top + 2 + i][left + 2 + j] = sc
  return g


def _connected(cells):
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen, stack = {start}, [start]
  while stack:
    r, c = stack.pop()
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        n = (r + dr, c + dc)
        if n in cells and n not in seen:
          seen.add(n)
          stack.append(n)
  return len(seen) == len(cells)


def _spans(cells, h, w):
  rs = [r for r, _ in cells]
  cs = [c for _, c in cells]
  return (min(rs) == 0 and max(rs) == h - 1 and min(cs) == 0
          and max(cs) == w - 1)


def _random_pattern(h, w):
  for _ in range(80):
    p = random.uniform(0.45, 0.8)
    cells = {(r, c) for r in range(h) for c in range(w) if random.random() < p}
    if cells and _spans(cells, h, w) and _connected(cells):
      return [''.join('#' if (r, c) in cells else '.' for c in range(w))
              for r in range(h)]
  return ['#' * w for _ in range(h)]


def _components(g, bg):
  hgt, wid = len(g), len(g[0])
  seen, comps = set(), []
  for y in range(hgt):
    for x in range(wid):
      if g[y][x] == bg or (y, x) in seen:
        continue
      col, stack, cells = g[y][x], [(y, x)], []
      seen.add((y, x))
      while stack:
        r, c = stack.pop()
        cells.append((r, c))
        for dr in (-1, 0, 1):
          for dc in (-1, 0, 1):
            nr, nc = r + dr, c + dc
            if (0 <= nr < hgt and 0 <= nc < wid and (nr, nc) not in seen
                and g[nr][nc] == col):
              seen.add((nr, nc))
              stack.append((nr, nc))
      comps.append((col, cells))
  return comps


def _corner_hits(g, bg):
  """Boxes of components whose box grown by 2 has own-colour corners."""
  hgt, wid = len(g), len(g[0])
  hits = []
  for col, cells in _components(g, bg):
    y0 = min(r for r, _ in cells) - 2
    y1 = max(r for r, _ in cells) + 2
    x0 = min(c for _, c in cells) - 2
    x1 = max(c for _, c in cells) + 2
    if y0 < 0 or x0 < 0 or y1 >= hgt or x1 >= wid:
      continue
    if all(g[y][x] == col for y, x in ((y0, x0), (y0, x1), (y1, x0), (y1, x1))):
      hits.append((y0 + 2, x0 + 2, y1 - 2, x1 - 2, col))
  return hits


def _bg_dominant(g, bg):
  """The background must be the strictly most common colour."""
  counts = [0] * 10
  for row in g:
    for v in row:
      counts[v] += 1
  return all(counts[bg] > counts[c] for c in range(10) if c != bg)


def _target_ok(g, bg, frames):
  """Ambiguity check: the target must be the only corner-test match.

  This is a local scene-validity check, not the archived solver. A bracket
  of the target frame can pass the corner test when neighbouring same-colour
  frames happen to supply its outer corners, so such scenes are resampled.
  """
  if not _bg_dominant(g, bg):
    return False
  hits = _corner_hits(g, bg)
  if len(hits) != 1:
    return False
  for t, l, fc, sc, pat in frames:
    if fc == sc:
      box = (t + 2, l + 2, t + 1 + len(pat), l + 1 + len(pat[0]), sc)
      return hits[0] == box
  return False


def _apart(t, l, other, fh, fw, gap):
  t2, l2 = other
  return abs(t - t2) >= fh + gap or abs(l - l2) >= fw + gap


def _place(hgt, wid, fh, fw, want, gap):
  """Free random placement with at least `gap` background lines between."""
  boxes = []
  for _ in range(want):
    for _ in range(150):
      t, l = random.randint(0, hgt - fh), random.randint(0, wid - fw)
      if all(_apart(t, l, b, fh, fw, gap) for b in boxes):
        boxes.append((t, l))
        break
    else:
      return None
  return boxes


def _cap(hgt, wid, h, w):
  """Frames that fit in a lattice with one-cell gaps."""
  return ((hgt + 1) // (h + 5)) * ((wid + 1) // (w + 5))


def _fitting(hgt, wid, hs, ws, need):
  """Shape sizes (h, w) whose lattice holds at least `need` frames."""
  return [(h, w) for h in hs for w in ws if _cap(hgt, wid, h, w) >= need]


def _spread(n, size, k):
  """Starts of k blocks of `size`, at least 1 apart, with random slack."""
  slack = n - k * size - (k - 1)
  extra = [0] * (k + 1)
  for _ in range(slack):
    extra[random.randrange(k + 1)] += 1
  pos, out = extra[0], []
  for i in range(k):
    out.append(pos)
    pos += size + 1 + extra[i + 1]
  return out


def _lattice(hgt, wid, fh, fw, want):
  """Jittered lattice layout. It always succeeds when _cap >= want."""
  rows = (hgt + 1) // (fh + 1)
  cols = (wid + 1) // (fw + 1)
  shapes = [(r, c) for r in range(1, rows + 1) for c in range(1, cols + 1)
            if r * c >= want]
  r, c = random.choice(shapes)
  tops = _spread(hgt, fh, r)
  lefts = _spread(wid, fw, c)
  slots = [(t, l) for t in tops for l in lefts]
  return random.sample(slots, want)


def _colours(bg, n, target):
  """Frame and shape colours. Only the target frame matches its shape."""
  others = [c for c in range(10) if c != bg]
  if random.random() < 0.25:
    fcs = [random.choice(others)] * n
  else:
    fcs = [random.choice(others) for _ in range(n)]
    rest = [i for i in range(n) if i != target]
    if len(rest) >= 2 and random.random() < 0.35:
      fcs[random.choice(rest)] = fcs[target]
  scs = []
  for i in range(n):
    if i == target:
      scs.append(fcs[i])
    else:
      scs.append(random.choice([c for c in others if c != fcs[i]]))
  # Decoy: a non-target shape takes the colour of a different frame.
  pairs = [(i, j) for i in range(n) if i != target for j in range(n)
           if j != i and fcs[j] != fcs[i]]
  if pairs and random.random() < 0.85:
    i, j = random.choice(pairs)
    scs[i] = fcs[j]
  return list(zip(fcs, scs))


def _assign(bg, boxes, h, w):
  target = random.randrange(len(boxes))
  cols = _colours(bg, len(boxes), target)
  return [(t, l, cols[i][0], cols[i][1], _random_pattern(h, w))
          for i, (t, l) in enumerate(boxes)]


def _check_replay(bg, arm, frames, wid, hgt):
  """Validates an explicit scene and rejects malformed input."""
  if not (_is_int(wid) and _is_int(hgt) and 6 <= wid <= 30
          and 6 <= hgt <= 30):
    raise ValueError('width and height must be integers in 6..30')
  if not (_is_int(bg) and 0 <= bg <= 9):
    raise ValueError('background must be an integer 0..9')
  if not (_is_int(arm) and arm in (2, 3)):
    raise ValueError('arm must be the integer 2 or 3')
  if len(frames) < 2:
    raise ValueError('a scene needs at least two frames')
  boxes = []
  for f in frames:
    if len(f) != 5:
      raise ValueError('each frame is (top, left, frame_colour, shape_colour,'
                       ' pattern)')
    top, left, fc, sc, pat = f
    if not all(_is_int(v) for v in (top, left, fc, sc)):
      raise ValueError('frame anchors and colours must be integers')
    if not (0 <= fc <= 9 and 0 <= sc <= 9) or bg in (fc, sc):
      raise ValueError('frame/shape colours must be 0..9 and not background')
    if (not isinstance(pat, (list, tuple)) or not pat
        or not all(isinstance(row, str) for row in pat)):
      raise ValueError('a pattern is a non-empty list of strings')
    if not pat[0] or any(len(row) != len(pat[0]) for row in pat):
      raise ValueError('patterns must be non-empty rectangles')
    if any(ch not in '#.' for row in pat for ch in row):
      raise ValueError('patterns use only # and .')
    h, w = len(pat), len(pat[0])
    if arm == 3 and min(h, w) < 3:
      raise ValueError('arm 3 needs both shape sides >= 3')
    cells = {(r, c) for r, row in enumerate(pat)
             for c, ch in enumerate(row) if ch == '#'}
    if not _connected(cells) or not _spans(cells, h, w):
      raise ValueError('shape must be 8-connected and span its box')
    if top < 0 or left < 0 or top + h + 4 > hgt or left + w + 4 > wid:
      raise ValueError('frame out of bounds')
    boxes.append((top, left, h + 4, w + 4))
  for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
      t1, l1, h1, w1 = boxes[i]
      t2, l2, h2, w2 = boxes[j]
      if not (t2 >= t1 + h1 + 1 or t1 >= t2 + h2 + 1
              or l2 >= l1 + w1 + 1 or l1 >= l2 + w2 + 1):
        raise ValueError('frames must be separated by background')


def _size_candidates(width, height, hs, ws, need):
  """Grid sizes (wid, hgt) that can hold `need` frames of some shape size.

  Unspecified sides are drawn from 16..30. If none of those fit, 6..30 is
  tried as a synthetic extension.
  """
  for lo in (16, 6):
    wopts = [width] if width is not None else list(range(lo, 31))
    hopts = [height] if height is not None else list(range(lo, 31))
    out = [(wd, ht) for wd in wopts for ht in hopts
           if _fitting(ht, wd, hs, ws, need)]
    if out:
      return out
  return []


def _random_scene(bg, arm, width, height, num_frames, sh, sw):
  for name, v in (('width', width), ('height', height), ('background', bg),
                  ('arm', arm), ('num_frames', num_frames),
                  ('shape_height', sh), ('shape_width', sw)):
    if v is not None and not _is_int(v):
      raise ValueError(name + ' must be an integer')
  for name, v in (('width', width), ('height', height)):
    if v is not None and not 6 <= v <= 30:
      raise ValueError(name + ' must lie in 6..30')
  if bg is None:
    bg = random.randint(0, 9)
  elif not 0 <= bg <= 9:
    raise ValueError('background must be 0..9')
  if num_frames is not None and not 2 <= num_frames <= 8:
    raise ValueError('num_frames must lie in 2..8')
  if arm is not None and arm not in (2, 3):
    raise ValueError('arm must be 2 or 3')
  for s in (sh, sw):
    if s is not None and not 1 <= s <= 6:
      raise ValueError('shape sides must lie in 1..6')
    if s is not None and arm == 3 and s < 3:
      raise ValueError('arm 3 needs both shape sides >= 3')
  lo = 3 if arm == 3 else 2
  hs = [sh] if sh is not None else list(range(lo, 6))
  ws = [sw] if sw is not None else list(range(lo, 6))
  need = num_frames if num_frames is not None else 3
  cands = _size_candidates(width, height, hs, ws, need)
  if not cands and num_frames is None:
    need = 2
    cands = _size_candidates(width, height, hs, ws, need)
  if not cands:
    raise ValueError('requested scene parameters are infeasible: two frames'
                     ' need (side+4) cells each plus a one-cell gap')
  if (width is None and height is None and (30, 30) in cands
      and random.random() < 0.7):
    wid, hgt = 30, 30
  else:
    wid, hgt = random.choice(cands)
  pairs = _fitting(hgt, wid, hs, ws, need)
  h, w = random.choice(pairs)
  cap = _cap(hgt, wid, h, w)
  if num_frames is not None:
    want = num_frames
  else:
    want = random.randint(min(3, cap), min(6, cap))
  if arm is None:
    arm = random.choice([2, 3]) if min(h, w) >= 3 else 2
  fh, fw = h + 4, w + 4
  for attempt in range(160):
    boxes = None
    if attempt % 2 == 0:
      gap = 1 if random.random() < 0.6 else 2
      boxes = _place(hgt, wid, fh, fw, want, gap)
    if boxes is None:
      boxes = _lattice(hgt, wid, fh, fw, want)
    frames = _assign(bg, boxes, h, w)
    if _target_ok(_render(bg, arm, frames, wid, hgt), bg, frames):
      return bg, arm, frames, wid, hgt
  raise ValueError('could not build an unambiguous scene with the requested'
                   ' parameters')


def generate(background=None, arm=None, frames=None, width=None, height=None,
             num_frames=None, shape_height=None, shape_width=None):
  """Builds one input/output pair.

  Args:
    background: background colour (integer 0-9). It is sampled when None.
    arm: length of each corner-bracket arm (integer 2 or 3). It is sampled
      when None. Arm 3 needs both shape sides to be at least 3. With an
      explicit arm=3, the sampled shape sides come from 3..5.
    frames: optional list of (top, left, frame_colour, shape_colour, pattern)
      tuples, used to replay explicit scenes. A pattern is a list of
      equal-length strings, where '#' is a shape cell and '.' is background.
      The frame's outer box is (len(pattern)+4) x (len(pattern[0])+4),
      anchored at (top, left). At least two frames are required, and exactly
      one entry must have frame_colour == shape_colour. Frames must be
      separated by background. The target must be the unique corner-test
      match, and the background must be the most common colour. Explicit
      frames need background and arm, and cannot be combined with num_frames
      or the shape sizes.
    width, height: grid size (integers 6..30). Explicit frames default to
      30x30. When both sides are unspecified, a random scene uses 30x30 70%
      of the time. Otherwise each unspecified side is drawn from 16..30
      (6..30 as a fallback), and only sizes that can hold the requested
      frames are drawn. One side must be at least 13 with default shape
      sizes, or at least 11 with shape side 1. Infeasible requests raise
      ValueError.
    num_frames: number of frames in a random scene (integer 2..8). It is
      sampled from 3..6 when None, capped by what fits. The requested count
      is honoured exactly; an infeasible request raises ValueError.
    shape_height, shape_width: shared size of the inner shapes in a random
      scene (integers 1..6 when given). Each is sampled from 2..5 (3..5 for
      arm 3) when None, restricted to sizes that fit the frame count.
  """
  if frames is not None:
    if background is None or arm is None:
      raise ValueError('explicit frames require background and arm')
    if (num_frames is not None or shape_height is not None
        or shape_width is not None):
      raise ValueError('num_frames/shape sizes only apply to random scenes')
    if not isinstance(frames, (list, tuple)):
      raise ValueError('frames must be a list of 5-tuples')
    if not all(isinstance(f, (list, tuple)) for f in frames):
      raise ValueError('each frame must be a list or tuple')
    wid = 30 if width is None else width
    hgt = 30 if height is None else height
    frames = [tuple(f) for f in frames]
    _check_replay(background, arm, frames, wid, hgt)
    replay = True
  else:
    background, arm, frames, wid, hgt = _random_scene(
        background, arm, width, height, num_frames, shape_height, shape_width)
    replay = False
  targets = [f for f in frames if f[2] == f[3]]
  if len(targets) != 1:
    raise ValueError('exactly one frame must match its shape colour')
  grid = _render(background, arm, frames, wid, hgt)
  if replay and not _target_ok(grid, background, frames):
    raise ValueError('explicit scene is ambiguous under the corner test')
  sc, pat = targets[0][3], targets[0][4]
  output = [[sc if ch == '#' else background for ch in row] for row in pat]
  return {'input': grid, 'output': output}


def validate():
  """Rebuilds the canonical fixtures from explicit latent parameters."""
  train = [
      generate(background=3, arm=2, frames=[
          (2, 4, 4, 6, ['###', '.#.', '#.#']),
          (6, 15, 8, 1, ['###', '.#.', '###']),
          (11, 2, 4, 4, ['##.', '.##', '##.']),
          (16, 18, 9, 2, ['#..', '.#.', '..#']),
          (21, 6, 2, 8, ['###', '#.#', '.#.']),
      ]),
      generate(background=8, arm=2, frames=[
          (3, 16, 1, 6, ['##', '.#']),
          (6, 4, 1, 4, ['##', '##']),
          (15, 19, 1, 1, ['.#', '##']),
          (18, 4, 1, 2, ['#.', '##']),
          (23, 13, 1, 3, ['##', '##']),
      ]),
      generate(background=4, arm=3, frames=[
          (2, 2, 2, 2, ['.###.', '##.##', '.#.#.', '.#.#.']),
          (4, 13, 8, 2, ['.#.#.', '##.##', '#####', '.#.#.']),
          (14, 3, 6, 3, ['.###.', '#####', '.#.#.', '##.##']),
          (17, 15, 1, 8, ['.###.', '##.##', '.#.#.', '#####']),
      ]),
  ]
  test = [
      generate(background=4, arm=2, frames=[
          (1, 3, 1, 3, ['#.#', '###', '.#.']),
          (3, 12, 6, 8, ['#.#', '.#.', '.#.']),
          (12, 4, 3, 8, ['###', '#.#', '###']),
          (13, 16, 2, 1, ['#.#', '.#.', '###']),
          (21, 19, 1, 9, ['.#.', '###', '.#.']),
          (22, 3, 2, 2, ['#.#', '.#.', '#.#']),
      ]),
      generate(background=1, arm=3, frames=[
          (1, 13, 6, 4, ['##.', '###', '.##']),
          (3, 2, 4, 3, ['##.', '.#.', '###']),
          (10, 10, 2, 8, ['###', '.#.', '.#.']),
          (11, 20, 9, 9, ['###', '.#.', '###']),
          (19, 2, 3, 8, ['##.', '.##', '.#.']),
          (22, 11, 7, 3, ['###', '#.#', '.#.']),
      ]),
  ]
  return {'train': train, 'test': test}
