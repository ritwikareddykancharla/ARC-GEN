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

"""ARC task 79369cc6: complete rotated or mirrored copies of a 4/6 motif.

Rule: the grid holds one 3x3 motif made only of colours 4 and 6. Its 4s span
all three rows and all three columns, so the bounding box of the 4s is the
motif box. Elsewhere the 6-cells of the motif appear again in any of the 8
dihedral orientations. A copy may be clipped by the grid edge, but only its
4-positions are ever clipped; every 6 of a copy lies inside the grid. All other
cells are noise in colours 0, 1, 6 and 8. A placement counts as a copy when
every motif-6 lands on an in-grid 6 and no in-grid 4-position holds a 4 or a 6.
The output paints colour 4 onto every in-grid 4-position of each copy, in the
orientation that matched. Everything else is unchanged.

Scope: random scenes use grids of 10..30 cells per side. The fixtures span
12..19, so the wider range is a synthetic extension. Explicit sizes from 6 to
30 are accepted. Each scene samples a fresh motif with 3-6 sixes (the fixtures
use 3-5; 6 is a synthetic extension), any spanning 4-set is reachable, a
per-scene density of noise 6s, the motif position, and 1-3 non-overlapping
copies in random orientations. About 35% of random scenes are clipping
scenes. Such a scene uses a motif with an all-4 edge row or column. Its first
copy is placed deliberately against an edge or into a corner so that 4-cells
fall off the grid, and later copies are clipped with probability 0.3.
Accidental extra matches are removed constructively. Unprotected noise 6s are
recoloured, or, when the extra match reuses only protected 6s, a 6 blocker is
placed on one of its 4-positions. Best effort also breaks blocked near-copies
(all 6s present, a 4-position holding a 6) when they own an unprotected 6.
Fixture replay passes the original input as `background` together with the
explicit motif and copy list. Replay asserts that the motif and copy 6s are
already present and that the listed copies are exactly the matches present.
The output is always painted from the latent copy list.
Random scenes may also contain deliberately blocked near-copies: their 6s
match, but one of the required 4-positions already contains a 6. These must
remain unchanged. Their full boxes are protected during noise repair.
"""

import random

import common


_FILL = (0, 1, 8)
_NOISE = (0, 1, 8, 6)


def _orient(m, k, flip):
  """Rotate m counter-clockwise k times (numpy rot90 style), then mirror."""
  t = [list(row) for row in m]
  for _ in range(k % 4):
    h, w = len(t), len(t[0])
    t = [[t[j][w - 1 - i] for j in range(h)] for i in range(w)]
  if flip:
    t = [row[::-1] for row in t]
  return t


def _key(t):
  return tuple(tuple(r) for r in t)


def _orientations(m):
  res, seen = [], set()
  for k in range(4):
    for flip in (False, True):
      t = _orient(m, k, flip)
      if _key(t) not in seen:
        seen.add(_key(t))
        res.append(t)
  return res


def _cells(t, value):
  return [(dy, dx) for dy in range(3) for dx in range(3) if t[dy][dx] == value]


def _box_overlap(a, b):
  return abs(a[0] - b[0]) < 3 and abs(a[1] - b[1]) < 3


def _clipped(r, c, hgt, wid):
  return not (0 <= r <= hgt - 3 and 0 <= c <= wid - 3)


def _copy_fits(t, r, c, hgt, wid):
  """True when every 6 is in-grid and at least one 4-cell is in-grid."""
  n4 = 0
  for dy in range(3):
    for dx in range(3):
      inside = 0 <= r + dy < hgt and 0 <= c + dx < wid
      if t[dy][dx] == 6 and not inside:
        return False
      if t[dy][dx] == 4 and inside:
        n4 += 1
  return n4 > 0


def _spans(m):
  fours = _cells(m, 4)
  return len({y for y, _ in fours}) == 3 and len({x for _, x in fours}) == 3


def _clippable(m):
  """A copy can be clipped only if some edge row or column is all 4."""
  lines = [m[0], m[2], [m[y][0] for y in range(3)], [m[y][2] for y in range(3)]]
  return any(all(v == 4 for v in line) for line in lines)


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _check_motif(m):
  if (not isinstance(m, (list, tuple)) or len(m) != 3 or
      any(not isinstance(r, (list, tuple)) or len(r) != 3 for r in m)):
    raise ValueError('motif must be a 3x3 grid')
  cells = [m[y][x] for y in range(3) for x in range(3)]
  if any(not _is_int(v) or v not in (4, 6) for v in cells):
    raise ValueError('motif may only use colours 4 and 6')
  if not _spans(m):
    raise ValueError('motif 4s must span all three rows and columns')
  if cells.count(6) < 3:
    raise ValueError('motif needs at least three 6s')
  return [list(r) for r in m]


def _check_copies(copies, m, hgt, wid):
  if not isinstance(copies, (list, tuple)):
    raise ValueError('copies must be a list')
  out = []
  for item in copies:
    if not isinstance(item, (list, tuple)) or len(item) != 4:
      raise ValueError('each copy is (row, col, k, flip)')
    r, c, k, flip = item
    if not (_is_int(r) and _is_int(c)):
      raise ValueError('copy row and col must be integers')
    if not _is_int(k) or k not in (0, 1, 2, 3):
      raise ValueError('k must be an integer 0..3')
    if not isinstance(flip, (bool, int)) or flip not in (0, 1):
      raise ValueError('flip must be a boolean')
    flip = bool(flip)
    if not _copy_fits(_orient(m, k, flip), r, c, hgt, wid):
      raise ValueError('copy %r must keep its 6s in-grid and show a 4' % (item,))
    if any(_box_overlap((r, c), (o[0], o[1])) for o in out):
      raise ValueError('copies must not overlap')
    out.append((r, c, k, flip))
  if not out:
    raise ValueError('at least one copy is required')
  return out


def _scan(grid, m, mrow, mcol):
  """Return (exact matches, blocked near-matches) as (row, col, key) sets.

  Exact: every motif-6 on an in-grid 6 and no in-grid 4-position on 4/6.
  Blocked: every motif-6 on an in-grid 6 but some in-grid 4-position on 4/6.
  The motif itself (identity orientation at its own box) is skipped.
  """
  hgt, wid = len(grid), len(grid[0])
  mk = _key(m)
  exact, blocked = set(), set()
  for t in _orientations(m):
    tk = _key(t)
    sixes, fours = _cells(t, 6), _cells(t, 4)
    for y in range(-2, hgt):
      for x in range(-2, wid):
        if (y, x) == (mrow, mcol) and tk == mk:
          continue
        ok = True
        for dy, dx in sixes:
          yy, xx = y + dy, x + dx
          if not (0 <= yy < hgt and 0 <= xx < wid) or grid[yy][xx] != 6:
            ok = False
            break
        if not ok:
          continue
        clean = True
        for dy, dx in fours:
          yy, xx = y + dy, x + dx
          if 0 <= yy < hgt and 0 <= xx < wid and grid[yy][xx] in (4, 6):
            clean = False
            break
        (exact if clean else blocked).add((y, x, tk))
  return exact, blocked


def _paint(grid, m, copies):
  out = [row[:] for row in grid]
  hgt, wid = len(grid), len(grid[0])
  for (r, c, k, flip) in copies:
    t = _orient(m, k, flip)
    for dy in range(3):
      for dx in range(3):
        y, x = r + dy, c + dx
        if t[dy][dx] == 4 and 0 <= y < hgt and 0 <= x < wid:
          out[y][x] = 4
  return out


def _random_motif(clippable=None):
  """Uniform-ish spanning 4/6 mask; optionally require an all-4 edge line."""
  for _ in range(500):
    if clippable:
      n6 = random.choice((3, 4))
    else:
      n6 = random.choices((3, 4, 5, 6), (3, 4, 3, 1))[0]
    sixes = set(random.sample(range(9), n6))
    m = [[6 if 3 * y + x in sixes else 4 for x in range(3)] for y in range(3)]
    if not _spans(m):
      continue
    if clippable is not None and _clippable(m) != clippable:
      continue
    return m
  raise RuntimeError('could not sample a motif')


def _repair(grid, m, mrow, mcol, intended, protected):
  """Remove unintended matches; best-effort removal of blocked near-copies."""
  hgt, wid = len(grid), len(grid[0])
  for _ in range(60):
    exact, blocked = _scan(grid, m, mrow, mcol)
    if not intended <= exact:
      return False
    changed = False
    for (ey, ex, ek) in sorted(exact - intended):
      sixes = [(ey + dy, ex + dx) for dy, dx in _cells(ek, 6)]
      fours = [(ey + dy, ex + dx) for dy, dx in _cells(ek, 4)
               if 0 <= ey + dy < hgt and 0 <= ex + dx < wid]
      if any(grid[y][x] != 6 for y, x in sixes):
        continue
      if any(grid[y][x] in (4, 6) for y, x in fours):
        continue
      cands = [p for p in sixes if p not in protected]
      if cands:
        y, x = random.choice(cands)
        grid[y][x] = random.choice(_FILL)
      else:
        blockers = [p for p in fours if p not in protected]
        if not blockers:
          return False
        y, x = random.choice(blockers)
        grid[y][x] = 6
        protected.add((y, x))
      changed = True
    for (ey, ex, ek) in sorted(blocked):
      sixes = [(ey + dy, ex + dx) for dy, dx in _cells(ek, 6)]
      if any(grid[y][x] != 6 for y, x in sixes):
        continue
      cands = [p for p in sixes if p not in protected]
      if cands:
        y, x = random.choice(cands)
        grid[y][x] = random.choice(_FILL)
        changed = True
    if not changed:
      return True
  return False


def _clip_candidates(m, hgt, wid, boxes):
  """All clipped placements whose 6s stay in-grid and that show a 4."""
  res = []
  for k in range(4):
    for flip in (False, True):
      t = _orient(m, k, flip)
      for r in range(-2, hgt):
        for c in range(-2, wid):
          if not _clipped(r, c, hgt, wid):
            continue
          if any(_box_overlap((r, c), b) for b in boxes):
            continue
          if _copy_fits(t, r, c, hgt, wid):
            res.append((r, c, k, flip))
  return res


def _replay(background, motif, motif_row, motif_col, copies, width, height,
            num_copies, clip):
  if motif is None or motif_row is None or motif_col is None or copies is None:
    raise ValueError('background replay needs motif, motif_row, motif_col '
                     'and copies')
  if not isinstance(background, (list, tuple)) or not background:
    raise ValueError('background must be a non-empty grid')
  hgt, wid = len(background), len(background[0])
  if any(len(r) != wid for r in background):
    raise ValueError('background must be rectangular')
  if not (6 <= hgt <= 30 and 6 <= wid <= 30):
    raise ValueError('background must be 6..30 per side')
  if (width is not None and width != wid) or (
      height is not None and height != hgt):
    raise ValueError('width/height disagree with background')
  if num_copies is not None and num_copies != len(copies):
    raise ValueError('num_copies disagrees with copies')
  if not (_is_int(motif_row) and _is_int(motif_col) and
          0 <= motif_row <= hgt - 3 and 0 <= motif_col <= wid - 3):
    raise ValueError('motif box must lie inside the grid')
  chosen = _check_copies(copies, motif, hgt, wid)
  if any(_box_overlap((motif_row, motif_col), (r, c)) for r, c, _, _ in chosen):
    raise ValueError('copies must not overlap the motif')
  if clip is not None and any(
      _clipped(r, c, hgt, wid) for r, c, _, _ in chosen) != bool(clip):
    raise ValueError('clip disagrees with copies')
  grid = [list(r) for r in background]
  for y in range(hgt):
    for x in range(wid):
      v = grid[y][x]
      if motif_row <= y < motif_row + 3 and motif_col <= x < motif_col + 3:
        if v != motif[y - motif_row][x - motif_col]:
          raise ValueError('background does not hold the motif at its box')
      elif not _is_int(v) or v not in (0, 1, 6, 8):
        raise ValueError('background cells outside the motif must be 0/1/6/8')
  intended = set()
  for (r, c, k, flip) in chosen:
    t = _orient(motif, k, flip)
    for dy, dx in _cells(t, 6):
      if grid[r + dy][c + dx] != 6:
        raise ValueError('copy %r is missing a 6' % ((r, c, k, flip),))
    intended.add((r, c, _key(t)))
  exact, _ = _scan(grid, motif, motif_row, motif_col)
  if exact != intended:
    raise ValueError('background copies disagree with the listed copies')
  return {'input': grid, 'output': _paint(grid, motif, chosen)}


def generate(width=None, height=None, motif=None, motif_row=None,
             motif_col=None, copies=None, num_copies=None, clip=None,
             background=None, num_decoys=None):
  """Build one input/output pair.

  Args:
    width: grid width (random 10..30; explicit 6..30).
    height: grid height (random 10..30; explicit 6..30).
    motif: 3x3 grid of 4/6 values whose 4s span every row and column, with at
      least three 6s. Random when None.
    motif_row: top row of the motif box; random when None.
    motif_col: left column of the motif box; random when None.
    copies: list of (row, col, k, flip). k counts counter-clockwise quarter
      turns, and flip then mirrors columns. row and col may be negative or run
      past the edge, as long as every 6 stays in-grid and a 4 shows. This
      requires motif, width and height, because its meaning depends on them.
    num_copies: number of copies to sample (1..6, default random 1..3). It must
      equal len(copies) when both are given.
    clip: True forces at least one edge-clipped copy (the motif needs an all-4
      edge row or column). False forbids clipped copies. None picks a clipping
      scene about 35% of the time when the motif allows it. With explicit
      copies it must agree with them.
    background: full original input grid for fixture replay. The motif and
      every listed copy 6 must already be present, and no unlisted match may
      exist.
    num_decoys: 0..4 deliberately blocked copies. Random 0..2 when None on
      grids of at least 10x10; zero otherwise. Not a replay option.
  """
  if clip is not None and type(clip) is not bool:
    raise ValueError('clip must be a boolean')
  if num_decoys is not None and (not _is_int(num_decoys) or not 0 <= num_decoys <= 4):
    raise ValueError('num_decoys must be an integer 0..4')
  for name, v in (('width', width), ('height', height)):
    if v is not None and (not _is_int(v) or not 6 <= v <= 30):
      raise ValueError('%s must be an integer 6..30' % name)
  if num_copies is not None and (not _is_int(num_copies) or not 1 <= num_copies <= 6):
    raise ValueError('num_copies must be an integer 1..6')
  if motif is not None:
    motif = _check_motif(motif)
  if background is not None:
    if num_decoys is not None:
      raise ValueError('num_decoys is a random-construction control, not replay')
    return _replay(background, motif, motif_row, motif_col, copies, width,
                   height, num_copies, clip)
  for name, v in (('width', width), ('height', height)):
    if v is not None and (not _is_int(v) or not 6 <= v <= 30):
      raise ValueError('%s must be an integer 6..30' % name)
  if motif_row is not None and (not _is_int(motif_row) or not 0 <= motif_row <= (
      height if height is not None else 30) - 3):
    raise ValueError('motif_row out of range')
  if motif_col is not None and (not _is_int(motif_col) or not 0 <= motif_col <= (
      width if width is not None else 30) - 3):
    raise ValueError('motif_col out of range')
  if num_copies is not None:
    if copies is not None and num_copies != len(copies):
      raise ValueError('num_copies disagrees with copies')
    if not _is_int(num_copies) or not 1 <= num_copies <= 6:
      raise ValueError('num_copies must be 1..6')
  fixed = None
  if copies is not None:
    if motif is None or width is None or height is None:
      raise ValueError('explicit copies require motif, width and height')
    fixed = _check_copies(copies, motif, height, width)
    if motif_row is not None and motif_col is not None and any(
        _box_overlap((motif_row, motif_col), (r, c)) for r, c, _, _ in fixed):
      raise ValueError('copies must not overlap the motif')
    has_clip = any(_clipped(r, c, height, width) for r, c, _, _ in fixed)
    if clip is not None and bool(clip) != has_clip:
      raise ValueError('clip disagrees with copies')
    want_clip = has_clip
  elif clip is not None:
    want_clip = bool(clip)
    if want_clip and motif is not None and not _clippable(motif):
      raise ValueError('clip=True needs a motif with an all-4 edge line')
  else:
    allowed = motif is None or _clippable(motif)
    want_clip = allowed and random.random() < 0.35

  for _ in range(200):
    if height is not None:
      hgt = height
    else:
      lo = 10 if motif_row is None else max(10, motif_row + 3)
      hgt = random.randint(lo, 30)
    if width is not None:
      wid = width
    else:
      lo = 10 if motif_col is None else max(10, motif_col + 3)
      wid = random.randint(lo, 30)
    if motif is not None:
      m = motif
    else:
      m = _random_motif(True if want_clip else None)
    mrow = motif_row if motif_row is not None else random.randint(0, hgt - 3)
    mcol = motif_col if motif_col is not None else random.randint(0, wid - 3)
    if fixed is not None and any(
        _box_overlap((mrow, mcol), (r, c)) for r, c, _, _ in fixed):
      continue

    six_w = random.randint(6, 13)
    grid = common.grid(wid, hgt, 0)
    for y in range(hgt):
      for x in range(wid):
        grid[y][x] = random.choices(_NOISE, (35, 30, 26, six_w))[0]
    protected = set()
    for dy in range(3):
      for dx in range(3):
        grid[mrow + dy][mcol + dx] = m[dy][dx]
        protected.add((mrow + dy, mcol + dx))

    if fixed is not None:
      chosen = list(fixed)
    else:
      n = num_copies if num_copies is not None else random.randint(1, 3)
      boxes = [(mrow, mcol)]
      chosen = []
      for i in range(n):
        do_clip = want_clip and (i == 0 or random.random() < 0.3)
        pick = None
        if do_clip:
          cands = _clip_candidates(m, hgt, wid, boxes)
          if cands:
            pick = random.choice(cands)
        else:
          for _ in range(100):
            k, flip = random.randint(0, 3), random.random() < 0.5
            r, c = random.randint(0, hgt - 3), random.randint(0, wid - 3)
            if any(_box_overlap((r, c), b) for b in boxes):
              continue
            pick = (r, c, k, flip)
            break
        if pick is None:
          break
        boxes.append((pick[0], pick[1]))
        chosen.append(pick)
      if len(chosen) != n:
        continue

    intended = set()
    for (r, c, k, flip) in chosen:
      t = _orient(m, k, flip)
      intended.add((r, c, _key(t)))
      for dy in range(3):
        for dx in range(3):
          y, x = r + dy, c + dx
          if 0 <= y < hgt and 0 <= x < wid:
            grid[y][x] = 6 if t[dy][dx] == 6 else random.choice(_FILL)
            protected.add((y, x))
    # All required 6s are present, but an additional 6 invalidates the copy.
    # Construct the hard negative from latent geometry, not reference filtering.
    decoys = []
    boxes = [(mrow, mcol)] + [(r, c) for r, c, _, _ in chosen]
    count = num_decoys if num_decoys is not None else (
        random.randint(0, 2) if min(hgt, wid) >= 10 else 0)
    for i in range(count):
      for attempt in range(100):
        r, c = random.randrange(hgt - 2), random.randrange(wid - 2)
        if any(abs(r - y) < 4 and abs(c - x) < 4 for y, x in boxes):
          continue
        t = _orient(m, random.randrange(4), random.choice((False, True)))
        blocker = random.choice(_cells(t, 4))
        for dy in range(3):
          for dx in range(3):
            grid[r + dy][c + dx] = (6 if t[dy][dx] == 6 or (dy, dx) == blocker
                                     else random.choice(_FILL))
            protected.add((r + dy, c + dx))
        boxes.append((r, c))
        decoys.append((r, c))
        break
    if len(decoys) != count:
      continue
    if _repair(grid, m, mrow, mcol, intended, protected):
      return {'input': grid, 'output': _paint(grid, m, chosen)}
  raise RuntimeError('could not build a valid scene for these parameters')


def _rows(strs):
  return [[int(ch) for ch in s] for s in strs]


def validate():
  """Reconstruct the canonical fixtures through explicit generate calls."""
  bg1 = _rows([
      '1060000801888111', '0186160000611881', '0181010066100811',
      '0011161106601180', '0100101101101661', '0000060188081101',
      '1118100811088111', '8811061818688186', '1161810111606818',
      '0088646018010018', '0180466108111110', '1116464800010868',
      '6011111081011800', '0111181118818880', '0100600081688600',
      '1111888111081181', '8110061010101111', '6010188886118188'])
  bg2 = _rows([
      '818081801011', '101186011668', '018808010610', '080800006886',
      '180800068800', '466860801108', '446801811186', '644080601010',
      '881188800080', '068800018888', '000000000806', '101880608818',
      '100816601088', '818811018088', '011006180081', '188808861860',
      '806181668011', '808080808081', '810011088008'])
  bg3 = _rows([
      '81886001001080100', '68100804661000801', '08180106440080008',
      '11011084441881018', '16600866000000008', '08600800110600018',
      '08080088818080006', '01016001100811686', '00101808801181180',
      '08081068800006811', '00006011811880888', '88806818100018116',
      '88001018018010001', '08818681610600806', '10881080011001000',
      '00080010880008066', '10000010801160601'])
  bg4 = _rows([
      '068006166111001', '108168811010801', '006018011000101',
      '111866680018086', '108086068111118', '006010088118160',
      '018106888601660', '100000180008108', '010811180081186',
      '011101100111081', '808884446118680', '108116448181011',
      '061006641100888', '811008808800111', '118801888800168',
      '081801806160660'])
  train = [
      generate(background=bg1, motif=[[6, 4, 6], [4, 6, 6], [4, 6, 4]],
               motif_row=9, motif_col=4, copies=[(1, 8, 3, False)]),
      generate(background=bg2, motif=[[4, 6, 6], [4, 4, 6], [6, 4, 4]],
               motif_row=5, motif_col=0,
               copies=[(14, 5, 2, True), (1, 9, 1, False)]),
      generate(background=bg3, motif=[[4, 6, 6], [6, 4, 4], [4, 4, 4]],
               motif_row=1, motif_col=7, copies=[(15, 14, 0, False)]),
  ]
  test = [
      generate(background=bg4, motif=[[4, 4, 4], [6, 4, 4], [6, 6, 4]],
               motif_row=10, motif_col=5,
               copies=[(4, 11, 0, True), (13, 11, 0, True), (3, 3, 2, False)]),
  ]
  return {'train': train, 'test': test}
