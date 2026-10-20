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

"""ARC-GEN style generator for task c4d1a9ae.

Rule: the background colour is the strictly most frequent colour. Columns
that are entirely background are separators. The remaining columns form
contiguous vertical bands, and each band holds a pattern in a single colour.
Inside every band, each background cell takes the pattern colour of the next
band to the right. The last band wraps around and takes the first band's
colour. Separator columns stay background.

Scope: by default the generator builds 3 to 7 bands. The band count is drawn
once per call, and an over-wide layout is shrunk constructively instead of
being redrawn, so large band counts are not filtered out. Two bands (and up
to nine) are accepted only through explicit arguments. A two-band output is
still unambiguous, because it is a colour swap. However, "next to the right"
and "next to the left" then give the same answer, so such a pair carries no
evidence about the direction or the wrap-around. Default band widths are
1 to 4 and separator widths are 1 or 2. Default heights run from 4 to 30,
which is a synthetic extension of the 10-row fixtures. Occasionally the
generator adds leading or trailing all-background margin columns. These are
also a synthetic extension, because the original examples have none. Every
grid is at most 30 cells per side. For fixed masks, free gaps/margins are
chosen from feasible layouts with the stated sampling weights. Dense fixed
masks can therefore force nonzero margins; impossible fixed-mask requests
raise ValueError before rendering.

The background and pattern colours are sampled and are all mutually
distinct. Each band pattern comes from one of these families:
  * a bouncing zigzag;
  * a periodic tile;
  * shifting single-cell runs;
  * contiguous multi-cell segments;
  * for 1-wide bands only, irregular on/off runs.
Each pattern is then repaired constructively. After repair, every band
column contains a pattern cell, so no band column can read as a separator.
Every band also contains at least one background cell, so the output always
differs from the input.
"""

import random
import itertools


_DEFAULT_COUNTS = [3, 3, 3, 4, 4, 5, 6, 7]


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _int_list(name, vals):
  if not isinstance(vals, (list, tuple)) or not all(_is_int(v) for v in vals):
    raise ValueError(name + ' must be a list of integers')
  return list(vals)


def _parse_mask(mask):
  """Parses a mask given as a string of rows or as a list of 0/1 rows."""
  if isinstance(mask, str):
    rows = []
    for row in mask.split():
      if any(c not in '01' for c in row):
        raise ValueError('mask strings may only contain 0 and 1')
      rows.append([int(c) for c in row])
    return rows
  if not isinstance(mask, (list, tuple)):
    raise ValueError('mask must be a string or a list of rows')
  rows = []
  for row in mask:
    rows.append(_int_list('mask row', row))
  return rows


def _zigzag(h, w):
  """Bouncing diagonal line, one cell per row (optionally with gaps)."""
  pos = random.randrange(w)
  d = random.choice([-1, 1])
  skip = random.choice([0.0, 0.0, 0.15])
  rows = []
  for _ in range(h):
    row = [0] * w
    if random.random() >= skip:
      row[pos] = 1
    rows.append(row)
    if w > 1:
      if not 0 <= pos + d < w:
        d = -d
      pos += d
  return rows


def _periodic(h, w):
  """Random tile of period 2-4, repeated vertically."""
  p = random.randint(2, 4)
  dens = random.uniform(0.3, 0.65)
  tile = [[1 if random.random() < dens else 0 for _ in range(w)]
          for _ in range(p)]
  phase = random.randrange(p)
  return [list(tile[(r + phase) % p]) for r in range(h)]


def _runs(h, w):
  """Single-cell vertical runs of length 2-4 that jump between columns."""
  rows = []
  pos = random.randrange(w)
  while len(rows) < h:
    for _ in range(random.randint(2, 4)):
      row = [0] * w
      row[pos] = 1
      rows.append(row)
    if w > 1:
      pos = random.choice([q for q in range(w) if q != pos])
  return rows[:h]


def _segments(h, w):
  """Contiguous horizontal segments (length 1..w-1), held for 1-3 rows."""
  rows = []
  while len(rows) < h:
    ln = random.randint(1, max(1, w - 1))
    st = random.randint(0, w - ln)
    for _ in range(random.randint(1, 3)):
      row = [0] * w
      for dx in range(st, st + ln):
        row[dx] = 1
      rows.append(row)
  return rows[:h]


def _onoff(h, w):
  """Irregular on/off runs of length 1-3 (used for 1-wide bands)."""
  rows = []
  on = random.random() < 0.5
  while len(rows) < h:
    for _ in range(random.randint(1, 3)):
      rows.append([1 if on else 0] * w)
    on = not on
  return rows[:h]


_WIDE_KINDS = {'zigzag': _zigzag, 'periodic': _periodic, 'runs': _runs,
               'segments': _segments}
_NARROW_KINDS = {'periodic': _periodic, 'onoff': _onoff}


def _repair(rows, h, w):
  """Ensures each column has a pattern cell and the band has a bg cell."""
  for x in range(w):
    if not any(rows[r][x] for r in range(h)):
      rows[random.randrange(h)][x] = 1
  if all(all(row) for row in rows):
    # h >= 2, so the cleared column keeps at least one pattern cell.
    rows[random.randrange(h)][random.randrange(w)] = 0
  return rows


def _band_pattern(h, w):
  kinds = _NARROW_KINDS if w == 1 else _WIDE_KINDS
  kind = random.choice(sorted(kinds))
  return _repair(kinds[kind](h, w), h, w)


def _mask_ok(rows):
  h, w = len(rows), len(rows[0])
  if any(v not in (0, 1) for row in rows for v in row):
    return False
  if not all(any(rows[r][x] for r in range(h)) for x in range(w)):
    return False
  return any(v == 0 for row in rows for v in row)


def _shrink_to_fit(ws, gs, mg, free_w, free_g, free_m):
  """Decrements free widths/gaps/margins one unit at a time until <= 30."""
  total = sum(ws) + sum(gs) + sum(mg)
  while total > 30:
    cands = []
    if free_m:
      cands += [('m', i) for i in range(2) if mg[i] > 0]
    if free_w:
      cands += [('w', i) for i in range(len(ws)) if ws[i] > 1]
    if free_g:
      cands += [('g', i) for i in range(len(gs)) if gs[i] > 1]
    if not cands:
      raise ValueError('requested layout is wider than 30 columns')
    kind, i = random.choice(cands)
    if kind == 'm':
      mg[i] -= 1
    elif kind == 'w':
      ws[i] -= 1
    else:
      gs[i] -= 1
    total -= 1
  return total


def generate(bg=None, colors=None, widths=None, gaps=None, masks=None,
             height=None, num_bands=None, margins=None):
  """Generates one input/output pair.

  Args:
    bg: background colour (0-9). It must not appear in colors.
    colors: list of distinct pattern colours, one per band, left to right.
    widths: list of band widths (each >= 1).
    gaps: list of separator widths between consecutive bands (length n-1,
      each >= 1).
    masks: list of masks, one per band. Each mask is either a string of
      space-separated rows of '0'/'1' or a list of 0/1 rows. A 1 marks a
      pattern cell. Every column needs a 1 and every mask needs a 0. When
      masks are given, they fix the height and the widths.
    height: grid height (2-30).
    num_bands: number of bands (2-9). It must agree with the other lists.
    margins: (left, right) counts of extra all-background edge columns.
  """
  if bg is not None and (not _is_int(bg) or not 0 <= bg <= 9):
    raise ValueError('bg must be an integer in 0..9')
  if colors is not None:
    colors = _int_list('colors', colors)
    if len(set(colors)) != len(colors) or any(not 0 <= c <= 9 for c in colors):
      raise ValueError('colors must be distinct values in 0..9')
    if bg is not None and bg in colors:
      raise ValueError('bg collides with a pattern colour')
  if widths is not None:
    widths = _int_list('widths', widths)
    if any(w < 1 for w in widths):
      raise ValueError('band widths must be >= 1')
  if gaps is not None:
    gaps = _int_list('gaps', gaps)
    if any(g < 1 for g in gaps):
      raise ValueError('separator widths must be >= 1')
  if height is not None and (not _is_int(height) or not 2 <= height <= 30):
    raise ValueError('height must be an integer in 2..30')
  if num_bands is not None and not _is_int(num_bands):
    raise ValueError('num_bands must be an integer')
  if margins is not None:
    margins = _int_list('margins', margins)
    if len(margins) != 2 or min(margins) < 0:
      raise ValueError('margins must be a (left, right) pair of non-negatives')
  pats = None
  if masks is not None:
    if not isinstance(masks, (list, tuple)) or not masks:
      raise ValueError('masks must be a non-empty list')
    pats = [_parse_mask(m) for m in masks]
    if not pats[0] or not pats[0][0]:
      raise ValueError('empty masks')
    mh = len(pats[0])
    for p in pats:
      if len(p) != mh or not p[0] or any(len(row) != len(p[0]) for row in p):
        raise ValueError('ragged or mismatched mask dimensions')
      if not _mask_ok(p):
        raise ValueError('each band mask needs a 1 in every column and a 0')
    if not 2 <= mh <= 30:
      raise ValueError('mask height must be in 2..30')
    if height is not None and height != mh:
      raise ValueError('height disagrees with masks')
    mws = [len(p[0]) for p in pats]
    if widths is not None and widths != mws:
      raise ValueError('widths disagree with masks')
    widths = mws
    height = mh
  sizes = set()
  if colors is not None:
    sizes.add(len(colors))
  if widths is not None:
    sizes.add(len(widths))
  if gaps is not None:
    sizes.add(len(gaps) + 1)
  if pats is not None:
    sizes.add(len(pats))
  if num_bands is not None:
    sizes.add(num_bands)
  if len(sizes) > 1:
    raise ValueError('inconsistent band counts across arguments')
  n_fixed = sizes.pop() if sizes else None
  if n_fixed is not None and not 2 <= n_fixed <= 9:
    raise ValueError('band count must be between 2 and 9')

  fixed_margin = sum(margins) if margins is not None else 0

  def min_total(k):
    # Free widths/gaps can shrink to 1 and free margins to 0.
    return ((sum(widths) if widths is not None else k) +
            (sum(gaps) if gaps is not None else k - 1) + fixed_margin)

  # The band count is drawn once per call so that rejection cannot bias the
  # realised band-count distribution toward small counts.
  if n_fixed is not None:
    if min_total(n_fixed) > 30:
      raise ValueError('requested layout is wider than 30 columns')
    n = n_fixed
  else:
    options = [k for k in _DEFAULT_COUNTS if min_total(k) <= 30]
    if not options:
      raise ValueError('requested layout is wider than 30 columns')
    n = random.choice(options)

  # Exact feasibility for fixed masks avoids retrying impossible layouts.
  # A gap has weights 3:1 for 1:2; free margins have weights 52 for (0,0)
  # and 1 for each other pair, matching the original sampling mixture.
  selected_layout = None
  if pats is not None:
    ones = [sum(map(sum, p)) for p in pats]
    choices, weights = [], []
    gap_options = [tuple(gaps)] if gaps is not None else itertools.product((1, 2), repeat=n - 1)
    margin_options = [tuple(margins)] if margins is not None else list(itertools.product(range(3), repeat=2))
    for gs0 in gap_options:
      gap_weight = 1 if gaps is not None else 3 ** gs0.count(1)
      for mg0 in margin_options:
        width0 = sum(widths) + sum(gs0) + sum(mg0)
        if width0 > 30 or height * width0 - sum(ones) <= max(ones):
          continue
        choices.append((gs0, mg0))
        weights.append(gap_weight * (1 if margins is not None else (52 if mg0 == (0, 0) else 1)))
    if not choices:
      raise ValueError('fixed masks admit no layout with strictly dominant background')
    selected_layout = random.choices(choices, weights=weights, k=1)[0]
  deterministic = pats is not None
  attempts = 1 if deterministic else 200
  for _ in range(attempts):
    if bg is not None:
      b = bg
    else:
      b = random.choice([c for c in range(10)
                         if colors is None or c not in colors])
    cols = list(colors) if colors is not None else random.sample(
        [c for c in range(10) if c != b], n)
    ws = list(widths) if widths is not None else [
        random.choice([1, 2, 2, 2, 3, 3, 4]) for _ in range(n)]
    gs = list(gaps) if gaps is not None else [
        random.choice([1, 1, 1, 2]) for _ in range(n - 1)]
    if margins is not None:
      mg = list(margins)
    elif random.random() < 0.85:
      mg = [0, 0]
    else:
      mg = [random.randint(0, 2), random.randint(0, 2)]
    if selected_layout is not None:
      gs, mg = [list(v) for v in selected_layout]
    total_w = _shrink_to_fit(ws, gs, mg, widths is None, gaps is None,
                             margins is None)
    lm = mg[0]
    h = height if height is not None else random.randint(4, 30)
    pt = pats if pats is not None else [_band_pattern(h, w) for w in ws]
    inp = [[b] * total_w for _ in range(h)]
    out = [[b] * total_w for _ in range(h)]
    x0 = lm
    for i in range(n):
      nxt = cols[(i + 1) % n]
      for r in range(h):
        for dx in range(ws[i]):
          if pt[i][r][dx]:
            inp[r][x0 + dx] = cols[i]
            out[r][x0 + dx] = cols[i]
          else:
            out[r][x0 + dx] = nxt
      x0 += ws[i]
      if i < n - 1:
        x0 += gs[i]
    counts = {}
    for row in inp:
      for v in row:
        counts[v] = counts.get(v, 0) + 1
    if any(counts.get(c, 0) >= counts[b] for c in cols):
      continue
    if inp == out:
      continue
    return {'input': inp, 'output': out}
  if deterministic:
    raise ValueError('fixed masks/gaps/margins do not leave background as '
                     'the strict majority colour')
  raise RuntimeError('could not build a valid scene with these parameters')


def validate():
  """Reconstructs the canonical fixtures through explicit generate calls."""
  train = [
      generate(bg=4, colors=[2, 6, 5], widths=[2, 2, 2], gaps=[1, 1],
               height=10, margins=(0, 0), masks=[
                   '01 10 01 10 01 10 01 10 01 10',
                   '01 01 01 10 10 10 10 01 01 01',
                   '11 01 11 01 11 01 11 01 11 01']),
      generate(bg=0, colors=[4, 3, 9], widths=[3, 1, 2], gaps=[1, 1],
               height=10, margins=(0, 0), masks=[
                   '000 100 010 001 010 100 010 001 010 100',
                   '0 1 0 1 0 1 0 1 0 1',
                   '01 10 01 01 10 01 01 10 01 01']),
  ]
  test = [
      generate(bg=5, colors=[6, 9, 8], widths=[2, 2, 2], gaps=[1, 1],
               height=10, margins=(0, 0), masks=[
                   '10 10 01 01 10 10 01 01 10 10',
                   '11 10 01 11 11 10 01 11 11 10',
                   '00 11 10 01 11 00 11 10 01 11']),
  ]
  return {'train': train, 'test': test}
