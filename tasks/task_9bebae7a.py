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

"""ARC task 9bebae7a: a magenta marker tells where to mirror the yellow figure.

Rule: the input holds a yellow (4) figure, which may be split into several
pieces, and one magenta (6) marker. The marker is either a T (a bar of 3 plus
a stem of 2) or an asymmetric cross (a bar of 4 crossed by a bar of 3). Each
marker has one long arm: the stem of the T, or the 2-cell arm of the cross.
The mirror direction is the long-arm direction rotated 90 degrees
counter-clockwise in image coordinates, (dy, dx) -> (-dx, dy). So stem-down
gives right, long-left gives down, long-right gives up and stem-up gives
left. The rule is chiral: the four orientations that never appear in the
fixtures are defined by rotating attested markers (and their directions),
never by reflecting them. In the output the marker is erased. The mirror
image of the figure's tight bounding box is then stamped flush against that
box on the chosen side, sharing an edge with it. The copy may cover cells
where the marker used to be.

Scope: the background is 0 and the colours 4 and 6 are fixed, as in the task.
Random grids are 6..30 per side, with most mass at 6..16 (the fixtures use
6..13, so larger sizes are a synthetic extension). Sampled figure boxes range
from 2 cells up to what the canvas allows once the reflection is duplicated:
half the canvas along the mirror axis and the whole canvas across it, after
any explicit position controls. About 30% of extents are drawn small (2..6) to
keep ARC-sized figures common. The figure density is capped so that yellow
stays below a quarter of the grid. Sampled figures are either random fills
with an exact box (often several pieces) or grown 8-connected blobs cropped
tight. They have at least 3 cells and are asymmetric about BOTH axes, so the
reflected copy differs from a plain translated copy and from a 180-degree
rotated copy. Explicit patterns (used for the fixtures) only need a tight
rectangular box, at least 3 cells and asymmetry about the mirror axis. They
may be one row or one column thin and any size that fits. All 8 marker
orientations are sampled. T stem-down/up and cross long-left/right are
attested. T stem-left/right and cross long-up/down are a synthetic extension
by rotation equivariance. The marker box never overlaps the figure box, and
no magenta cell touches yellow, even diagonally. When possible, about 35% of
scenes put the marker where the copy will land. The copy always fits in the
grid, and 0 is strictly the most common colour in both input and output.
"""

import random

import common

_DIRS = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}
_ARMS = ('down', 'left', 'right', 'up')
_KINDS = ('T', 'cross')

_MARKERS = {
    ('T', 'down'): [[1, 1, 1], [0, 1, 0], [0, 1, 0]],
    ('T', 'up'): [[0, 1, 0], [0, 1, 0], [1, 1, 1]],
    ('T', 'right'): [[1, 0, 0], [1, 1, 1], [1, 0, 0]],
    ('T', 'left'): [[0, 0, 1], [1, 1, 1], [0, 0, 1]],
    ('cross', 'left'): [[0, 0, 1, 0], [1, 1, 1, 1], [0, 0, 1, 0]],
    ('cross', 'right'): [[0, 1, 0, 0], [1, 1, 1, 1], [0, 1, 0, 0]],
    ('cross', 'up'): [[0, 1, 0], [0, 1, 0], [1, 1, 1], [0, 1, 0]],
    ('cross', 'down'): [[0, 1, 0], [1, 1, 1], [0, 1, 0], [0, 1, 0]],
}

_NEIGH8 = ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1),
           (-1, -1))


def _mirror_dir(arm):
  """Rotate the long-arm direction 90 degrees CCW in image coordinates."""
  dy, dx = _DIRS[arm]
  return (-dx, dy)


def _check_int(name, v):
  if v is None:
    return
  if isinstance(v, bool) or not isinstance(v, int):
    raise ValueError('%s must be an int' % name)


def _parse(pattern):
  """Strictly parse a pattern given as '0'/'1' strings or 0/1 int rows."""
  if isinstance(pattern, str) or not isinstance(pattern, (list, tuple)):
    raise ValueError('pattern must be a list of rows')
  if not pattern:
    raise ValueError('pattern must be non-empty')
  rows = []
  for row in pattern:
    if isinstance(row, str):
      vals = []
      for c in row:
        if c not in '01':
          raise ValueError('pattern strings may contain only 0/1')
        vals.append(1 if c == '1' else 0)
    elif isinstance(row, (list, tuple)):
      vals = []
      for c in row:
        if isinstance(c, bool) or not isinstance(c, int) or c not in (0, 1):
          raise ValueError('pattern rows may contain only 0/1 ints')
        vals.append(c)
    else:
      raise ValueError('pattern rows must be strings or lists')
    rows.append(vals)
  return rows


def _count(pat):
  return sum(sum(row) for row in pat)


def _hflip(pat):
  return [list(row[::-1]) for row in pat]


def _vflip(pat):
  return [list(row) for row in pat[::-1]]


def _mirrored(pat, dy, dx):
  """Reflection across the mirror axis (left-right for a sideways mirror)."""
  return _hflip(pat) if dx else _vflip(pat)


def _other_flip(pat, dy, dx):
  return _vflip(pat) if dx else _hflip(pat)


def _tight(pat):
  if not pat or not pat[0]:
    return False
  w = len(pat[0])
  if any(len(r) != w for r in pat):
    return False
  return (any(pat[0]) and any(pat[-1]) and any(r[0] for r in pat) and
          any(r[-1] for r in pat))


def _crop(pat):
  """Crop a 0/1 pattern to its tight bounding box (None if empty)."""
  rs = [i for i, r in enumerate(pat) if any(r)]
  if not rs:
    return None
  cs = [j for j in range(len(pat[0])) if any(r[j] for r in pat)]
  return [list(row[cs[0]:cs[-1] + 1]) for row in pat[rs[0]:rs[-1] + 1]]


def _explicit_ok(pat, arm):
  """Fixture-compatible validity: tight, >=3 cells, mirror-axis asymmetric."""
  dy, dx = _mirror_dir(arm)
  return (_tight(pat) and _count(pat) >= 3 and
          _mirrored(pat, dy, dx) != pat)


def _sampled_ok(pat, arm):
  """Stricter validity for sampled figures: asymmetric about both axes."""
  dy, dx = _mirror_dir(arm)
  return (len(pat) >= 2 and len(pat[0]) >= 2 and _explicit_ok(pat, arm) and
          _other_flip(pat, dy, dx) != pat)


def _start_range(size, n, d):
  """Valid figure starts along one axis, given mirror component d."""
  if d < 0:
    return n, size - n
  if d > 0:
    return 0, size - 2 * n
  return 0, size - n


def _max_extent(size, f, d):
  """Largest figure extent along an axis, given an optional fixed start."""
  if f is None:
    return size // 2 if d else size
  if d < 0:
    return min(f, size - f)
  if d > 0:
    return (size - f) // 2
  return size - f


def _min_size(n, f, d, need_m):
  """Smallest canvas extent compatible with figure extent/start and marker."""
  n0 = 2 if n is None else n
  if f is None:
    base = 2 * n0 if d else n0
  elif d < 0:
    if f < n0:
      return 99
    base = f + n0
  elif d > 0:
    base = f + 2 * n0
  else:
    base = f + n0
  return max(base, need_m)


def _axis_feasible(size, n, f, d, m, msz):
  need_m = msz + (m if m is not None else 0)
  if size is None:
    return _min_size(n, f, d, need_m) <= 30
  if size < need_m:
    return False
  return _max_extent(size, f, d) >= (2 if n is None else n)


def _combo_feasible(kind, arm, height, width, fixed, ft, fl, mt, ml):
  dy, dx = _mirror_dir(arm)
  mk = _MARKERS[(kind, arm)]
  if fixed is not None:
    if not _explicit_ok(fixed, arm):
      return False
    h, w = len(fixed), len(fixed[0])
  else:
    h = w = None
  return (_axis_feasible(height, h, ft, dy, mt, len(mk)) and
          _axis_feasible(width, w, fl, dx, ml, len(mk[0])))


def _pick_size(size, n, f, d, m, msz):
  if size is not None:
    return size
  lo = max(6, _min_size(n, f, d, msz + (m if m is not None else 0)))
  hi = max(lo, random.choice((12, 14, 16, 22, 30)))
  return random.randint(lo, min(30, hi))


def _pick_start(size, n, d, f):
  lo, hi = _start_range(size, n, d)
  if f is not None:
    return f if lo <= f <= hi else None
  if lo > hi:
    return None
  return random.randint(lo, hi)


def _sample_extent(nmax):
  if nmax > 6 and random.random() < 0.3:
    return random.randint(2, 6)
  return random.randint(2, nmax)


def _fill_pattern(h, w, p):
  """Random fill whose tight box is exactly h x w."""
  pat = [[1 if random.random() < p else 0 for _ in range(w)]
         for _ in range(h)]
  if not any(pat[0]):
    pat[0][random.randrange(w)] = 1
  if not any(pat[-1]):
    pat[-1][random.randrange(w)] = 1
  if not any(r[0] for r in pat):
    pat[random.randrange(h)][0] = 1
  if not any(r[-1] for r in pat):
    pat[random.randrange(h)][-1] = 1
  return pat


def _grow_pattern(h, w, target):
  """Grow an 8-connected blob inside an h x w box, cropped tight."""
  start = (random.randrange(h), random.randrange(w))
  cells = {start}
  order = [start]
  for _ in range(30 * target + 50):
    if len(cells) >= target:
      break
    i, j = random.choice(order)
    di, dj = random.choice(_NEIGH8)
    ni, nj = i + di, j + dj
    if 0 <= ni < h and 0 <= nj < w and (ni, nj) not in cells:
      cells.add((ni, nj))
      order.append((ni, nj))
  return _crop([[1 if (i, j) in cells else 0 for j in range(w)]
                for i in range(h)])


def _random_pattern(h, w, arm, cap):
  area = h * w
  for _ in range(40):
    if random.random() < 0.5:
      p = min(random.uniform(0.4, 0.72), cap / float(area))
      pat = _fill_pattern(h, w, max(p, 0.2))
    else:
      hi = min(area * 3 // 4, cap)
      if hi < 3:
        continue
      lo = min(max(3, area * 2 // 5), hi)
      pat = _grow_pattern(h, w, random.randint(lo, hi))
    if pat is not None and _sampled_ok(pat, arm) and _count(pat) <= cap:
      return pat
  return None


def _cells(pat, top, left):
  out = set()
  for i, row in enumerate(pat):
    for j, v in enumerate(row):
      if v:
        out.add((top + i, left + j))
  return out


def _dilate(cells):
  out = set()
  for (r, c) in cells:
    for a in (-1, 0, 1):
      for b in (-1, 0, 1):
        out.add((r + a, c + b))
  return out


def _copy_origin(ft, fl, h, w, dy, dx):
  if dx:
    return ft, (fl + w if dx > 0 else fl - w)
  return (ft + h if dy > 0 else ft - h), fl


def _marker_ok(H, W, mk, mt, ml, box, forbidden):
  mh, mw = len(mk), len(mk[0])
  if mt < 0 or ml < 0 or mt + mh > H or ml + mw > W:
    return False
  ft, fl, h, w = box
  if not (mt + mh <= ft or mt >= ft + h or ml + mw <= fl or ml >= fl + w):
    return False
  for i, row in enumerate(mk):
    for j, v in enumerate(row):
      if v and (mt + i, ml + j) in forbidden:
        return False
  return True


def _scene_ok(H, W, pat, ft, fl, kind, arm, mt, ml):
  if not (1 <= H <= 30 and 1 <= W <= 30):
    return False
  if not _explicit_ok(pat, arm):
    return False
  dy, dx = _mirror_dir(arm)
  h, w = len(pat), len(pat[0])
  lo, hi = _start_range(H, h, dy)
  if not lo <= ft <= hi:
    return False
  lo, hi = _start_range(W, w, dx)
  if not lo <= fl <= hi:
    return False
  mk = _MARKERS[(kind, arm)]
  yellow = _cells(pat, ft, fl)
  if not _marker_ok(H, W, mk, mt, ml, (ft, fl, h, w), _dilate(yellow)):
    return False
  ny = len(yellow)
  nm = _count(mk)
  zeros_in = H * W - ny - nm
  zeros_out = H * W - 2 * ny
  return zeros_in > ny and zeros_in > nm and zeros_out > 2 * ny


def _sample_scene(kind, arm, height, width, fixed, fig_top, fig_left,
                  marker_top, marker_left):
  dy, dx = _mirror_dir(arm)
  mk = _MARKERS[(kind, arm)]
  mh, mw = len(mk), len(mk[0])
  fh = len(fixed) if fixed is not None else None
  fw = len(fixed[0]) if fixed is not None else None
  H = _pick_size(height, fh, fig_top, dy, marker_top, mh)
  W = _pick_size(width, fw, fig_left, dx, marker_left, mw)
  if fixed is not None:
    pat = fixed
  else:
    hmax = _max_extent(H, fig_top, dy)
    wmax = _max_extent(W, fig_left, dx)
    if hmax < 2 or wmax < 2:
      return None
    pat = _random_pattern(_sample_extent(hmax), _sample_extent(wmax), arm,
                          (H * W - 1) // 4)
    if pat is None:
      return None
  h, w = len(pat), len(pat[0])
  ft = _pick_start(H, h, dy, fig_top)
  fl = _pick_start(W, w, dx, fig_left)
  if ft is None or fl is None:
    return None
  forbidden = _dilate(_cells(pat, ft, fl))
  box = (ft, fl, h, w)
  rows = [marker_top] if marker_top is not None else range(H - mh + 1)
  cols = [marker_left] if marker_left is not None else range(W - mw + 1)
  spots = [(r, c) for r in rows for c in cols
           if _marker_ok(H, W, mk, r, c, box, forbidden)]
  if not spots:
    return None
  nt, nl = _copy_origin(ft, fl, h, w, dy, dx)
  copy = _cells(_mirrored(pat, dy, dx), nt, nl)
  hard = [s for s in spots if _cells(mk, s[0], s[1]) & copy]
  if hard and random.random() < 0.35:
    mt, ml = random.choice(hard)
  else:
    mt, ml = random.choice(spots)
  scene = (H, W, pat, ft, fl, kind, arm, mt, ml)
  if not _scene_ok(*scene):
    return None
  return scene


def generate(height=None, width=None, pattern=None, fig_top=None,
             fig_left=None, kind=None, arm=None, marker_top=None,
             marker_left=None):
  """Build one input/output pair.

  Any argument left as None is sampled, conditioned on the explicit ones.
  Invalid types, sizes outside 1..30, positions outside 0..29 or outside
  a given size, unknown kind/arm, malformed patterns and impossible
  per-axis extents are rejected up front with ValueError. Remaining
  placement conflicts use a bounded 300-attempt search. A fully
  specified call is tried once and raises ValueError if the scene is invalid
  (for example the marker touching yellow).

  Args:
    height, width: grid size (rows, columns), ints in 1..30.
    pattern: list of '0'/'1' strings or 0/1 int rows giving the yellow
      figure's tight bounding box. Explicit patterns need at least 3 cells
      and asymmetry about the mirror axis only.
    fig_top, fig_left: top-left corner of the figure box.
    kind: 'T' or 'cross', the marker type.
    arm: 'up'/'down'/'left'/'right', the direction of the marker's long arm.
    marker_top, marker_left: top-left corner of the marker's bounding box.
  """
  for name, v in (('height', height), ('width', width), ('fig_top', fig_top),
                  ('fig_left', fig_left), ('marker_top', marker_top),
                  ('marker_left', marker_left)):
    _check_int(name, v)
  for name, v in (('height', height), ('width', width)):
    if v is not None and not 1 <= v <= 30:
      raise ValueError('%s must be in 1..30' % name)
  for name, v, size in (('fig_top', fig_top, height),
                        ('fig_left', fig_left, width),
                        ('marker_top', marker_top, height),
                        ('marker_left', marker_left, width)):
    if v is None:
      continue
    if not 0 <= v < 30:
      raise ValueError('%s must be in 0..29' % name)
    if size is not None and v >= size:
      raise ValueError('%s lies outside the grid' % name)
  if kind is not None and (not isinstance(kind, str) or kind not in _KINDS):
    raise ValueError('kind must be T or cross')
  if arm is not None and (not isinstance(arm, str) or arm not in _ARMS):
    raise ValueError('arm must be up, down, left or right')
  fixed = None
  arms = [arm] if arm is not None else list(_ARMS)
  kinds = [kind] if kind is not None else list(_KINDS)
  if pattern is not None:
    fixed = _parse(pattern)
    if not _tight(fixed):
      raise ValueError('pattern must be rectangular with a tight box')
    if not any(_explicit_ok(fixed, a) for a in arms):
      raise ValueError('pattern is too small or symmetric on the mirror axis')
  combos = [(k, a) for k in kinds for a in arms
            if _combo_feasible(k, a, height, width, fixed, fig_top, fig_left,
                               marker_top, marker_left)]
  if not combos:
    raise ValueError('controls admit no valid scene')
  given = [height, width, pattern, fig_top, fig_left, kind, arm, marker_top,
           marker_left]
  attempts = 1 if all(v is not None for v in given) else 300
  for _ in range(attempts):
    k, a = random.choice(combos)
    scene = _sample_scene(k, a, height, width, fixed, fig_top, fig_left,
                          marker_top, marker_left)
    if scene is not None:
      return _render(*scene)
  raise ValueError('no valid scene for the given parameters')


def _render(H, W, pat, ft, fl, kind, arm, mt, ml):
  h, w = len(pat), len(pat[0])
  mk = _MARKERS[(kind, arm)]
  grid = common.grid(W, H, 0)
  out = common.grid(W, H, 0)
  for (r, c) in _cells(pat, ft, fl):
    grid[r][c] = 4
    out[r][c] = 4
  for (r, c) in _cells(mk, mt, ml):
    grid[r][c] = 6
  dy, dx = _mirror_dir(arm)
  nt, nl = _copy_origin(ft, fl, h, w, dy, dx)
  for (r, c) in _cells(_mirrored(pat, dy, dx), nt, nl):
    out[r][c] = 4
  return {'input': grid, 'output': out}


def validate():
  """Rebuild the canonical examples from explicit latent parameters."""
  train = [
      generate(11, 10, ['011', '110', '101', '010'], 1, 4, 'T', 'down', 7, 1),
      generate(12, 10, ['00010', '01110', '11111', '01100'], 1, 2, 'cross',
               'left', 8, 2),
      generate(10, 10, ['010', '001', '110', '111'], 2, 1, 'T', 'down', 7, 5),
      generate(11, 13, ['001010', '101111', '011110'], 4, 3, 'cross', 'right',
               8, 8),
      generate(6, 10, ['0111110', '1111011', '0100000'], 0, 2, 'cross',
               'left', 3, 4),
  ]
  test = [
      generate(11, 12, ['0100', '1110', '0010', '0111', '0110'], 1, 5, 'T',
               'up', 7, 1),
  ]
  return {'train': train, 'test': test}
