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

"""ARC task 2ccd9fef: continue the animation shown in a strip of framed panels.

Rule: the input is a strip of n equal panels, stacked vertically (axis 0) or
horizontally (axis 1). Every panel carries the same decorative frame on a
background colour. The last panel is the bare frame. The other panels show
successive steps of a small animation. Each object either grows by repeatedly
inserting the same block of rows or columns at a fixed index, or translates.
In both cases its bounding box shifts by a constant offset per step. The output
is the bare last panel with the next step of its own sequence drawn in.
With sequence period 1, every panel belongs to one sequence. With period 2,
two sequences with different colour sets alternate. The last panel then
continues the sequence that has its own parity, and the other sequence is a
distractor.

Scope: the frame is a random mirror-symmetric decorative ring (thickness 1 or
2, one or two colours) around an all-background interior. The objects are
connected 1-2 colour patterns built from a prefix, k copies of a block, and a
suffix. They grow along one axis, with an along-axis drift of -d, 0 or +d per
step. There are also pure translating objects that move one cell per step.
The strip has 3-6 panels and the cross-strip panel side reaches 30; the along-strip side is
limited by the complete strip fitting inside 30 cells.
"""

import collections
import copy
import random

import common


def _pattern(obj, k):
  rows = [list(r) for r in obj['prefix']]
  for _ in range(obj['start'] + k):
    rows.extend([list(r) for r in obj['block']])
  rows.extend([list(r) for r in obj['suffix']])
  if obj.get('transpose'):
    rows = [list(col) for col in zip(*rows)]
  return rows


def _origin(obj, k):
  return (obj['pos'][0] + k * obj['vel'][0], obj['pos'][1] + k * obj['vel'][1])


def _cells(obj, k):
  y, x = _origin(obj, k)
  pat = _pattern(obj, k)
  return {(y + r, x + c) for r, row in enumerate(pat)
          for c, v in enumerate(row) if v >= 0}


def _paint(panel, obj, k):
  y, x = _origin(obj, k)
  for r, row in enumerate(_pattern(obj, k)):
    for c, v in enumerate(row):
      if v >= 0 and 0 <= y + r < len(panel) and 0 <= x + c < len(panel[0]):
        panel[y + r][x + c] = v


def _build(template, axis, n, objects, distractors):
  panels = [copy.deepcopy(template) for _ in range(n)]
  output = copy.deepcopy(template)
  if distractors:
    tgt = [i for i in range(n - 1) if (n - 1 - i) % 2 == 0]
    dis = [i for i in range(n - 1) if (n - 1 - i) % 2 == 1]
    for j, i in enumerate(tgt):
      for obj in objects:
        _paint(panels[i], obj, j)
    for j, i in enumerate(dis):
      for obj in distractors:
        _paint(panels[i], obj, j)
    final = len(tgt)
  else:
    for i in range(n - 1):
      for obj in objects:
        _paint(panels[i], obj, i)
    final = n - 1
  for obj in objects:
    _paint(output, obj, final)
  if axis == 0:
    grid = [list(row) for panel in panels for row in panel]
  else:
    grid = [[v for panel in panels for v in panel[r]]
            for r in range(len(template))]
  return grid, output, panels


def _tight(pat):
  if not pat or not pat[0]:
    return False
  return (any(v >= 0 for v in pat[0]) and any(v >= 0 for v in pat[-1]) and
          any(row[0] >= 0 for row in pat) and any(row[-1] >= 0 for row in pat))


def _connected(pat):
  cells = {(r, c) for r, row in enumerate(pat)
           for c, v in enumerate(row) if v >= 0}
  if not cells:
    return False
  first = next(iter(cells))
  seen, stack = {first}, [first]
  while stack:
    y, x = stack.pop()
    for nb in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
      if nb in cells and nb not in seen:
        seen.add(nb)
        stack.append(nb)
  return len(seen) == len(cells)


def _shape_ok(obj, nstates, cols):
  for k in range(nstates):
    pat = _pattern(obj, k)
    if not _tight(pat) or not _connected(pat):
      return False
    if set(v for row in pat for v in row if v >= 0) != set(cols):
      return False
  return True


def _row(cols, width, fill):
  main = random.choice(cols)
  row = []
  for _ in range(width):
    if random.random() < fill:
      row.append(main if random.random() < 0.75 else random.choice(cols))
    else:
      row.append(-1)
  return row


def _growth_obj(cols, nstates, ih, iw):
  transpose = random.random() < 0.5
  lg, lc = (iw, ih) if transpose else (ih, iw)
  width = random.randint(1, min(4, lc))
  d = random.choice([1, 1, 1, 2])
  npre = random.choice([0, 0, 1, 1, 2])
  nsuf = random.choice([0, 0, 1, 2])
  start = random.choice([0, 1, 1, 2])
  if npre + nsuf + start * d == 0:
    start = 1
  if npre + nsuf + (start + nstates - 1) * d > lg:
    return None
  fill = random.choice([1.0, 1.0, 0.8, 0.65])
  step = random.choice([0, 0, -d, d])
  obj = {
      'prefix': [_row(cols, width, fill) for _ in range(npre)],
      'block': [_row(cols, width, fill) for _ in range(d)],
      'suffix': [_row(cols, width, fill) for _ in range(nsuf)],
      'start': start,
      'pos': (0, 0),
      'vel': (0, step) if transpose else (step, 0),
      'transpose': transpose,
  }
  return obj if _shape_ok(obj, nstates, cols) else None


def _move_obj(cols, nstates, ih, iw):
  h = random.randint(1, min(3, ih))
  w = random.randint(1, min(3, iw))
  fill = random.choice([1.0, 0.75])
  pattern = [_row(cols, w, fill) for _ in range(h)]
  if sum(1 for row in pattern for v in row if v >= 0) < 2:
    return None
  vel = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1),
                       (1, 1), (1, -1), (-1, 1), (-1, -1)])
  obj = {'prefix': pattern, 'block': [], 'suffix': [], 'start': 0,
         'pos': (0, 0), 'vel': vel, 'transpose': False}
  return obj if _shape_ok(obj, nstates, cols) else None


def _pos_range(obj, nstates, interior):
  iy0, ix0, iy1, ix1 = interior
  vy, vx = obj['vel']
  ylo, xlo, yhi, xhi = -99, -99, 99, 99
  for k in range(nstates):
    pat = _pattern(obj, k)
    h, w = len(pat), len(pat[0])
    ylo = max(ylo, iy0 - k * vy)
    yhi = min(yhi, iy1 - h + 1 - k * vy)
    xlo = max(xlo, ix0 - k * vx)
    xhi = min(xhi, ix1 - w + 1 - k * vx)
  if ylo > yhi or xlo > xhi:
    return None
  return ylo, yhi, xlo, xhi


def _separated(obj, placed, nstates):
  for k in range(nstates):
    mine = _cells(obj, k)
    for other in placed:
      for (y, x) in _cells(other, k):
        for dy in (-1, 0, 1):
          for dx in (-1, 0, 1):
            if (y + dy, x + dx) in mine:
              return False
  return True


def _make_sequence(groups, nstates, interior):
  ih = interior[2] - interior[0] + 1
  iw = interior[3] - interior[1] + 1
  placed = []
  for idx, cols in enumerate(groups):
    done = False
    for _ in range(80):
      if idx == 0 or random.random() < 0.8:
        obj = _growth_obj(cols, nstates, ih, iw)
      else:
        obj = _move_obj(cols, nstates, ih, iw)
      if obj is None:
        continue
      rng = _pos_range(obj, nstates, interior)
      if rng is None:
        continue
      obj['pos'] = (random.randint(rng[0], rng[1]),
                    random.randint(rng[2], rng[3]))
      if _separated(obj, placed, nstates):
        placed.append(obj)
        done = True
        break
    if not done:
      return None
  return placed


def _make_frame(ph, pw, t, bg, colours):
  density = random.uniform(0.35, 0.7)
  choice = {}
  panel = [list(row) for row in common.grid(pw, ph, bg)]
  count = 0
  for r in range(ph):
    for c in range(pw):
      if min(r, ph - 1 - r, c, pw - 1 - c) >= t:
        continue
      key = (min(r, ph - 1 - r), min(c, pw - 1 - c))
      if key not in choice:
        choice[key] = random.choice(colours) if random.random() < density else bg
      panel[r][c] = choice[key]
      if panel[r][c] != bg:
        count += 1
  return panel if count >= 4 else None


def _colour_groups(palette, count):
  pal = list(palette)
  random.shuffle(pal)
  groups = []
  for _ in range(count):
    k = 2 if random.random() < 0.3 and len(pal) >= 2 else 1
    if len(pal) < k:
      return None
    groups.append(pal[:k])
    pal = pal[k:]
  return groups


def _detect_period(g, bg):
  # Local constraint check: the smallest frame period must be the true one.
  h, w = len(g), len(g[0])
  for axis in (0, 1):
    length = h if axis == 0 else w
    for p in range(2, length // 3 + 1):
      if length % p:
        continue
      n = length // p
      rows = p if axis == 0 else h
      cols = w if axis == 0 else p
      ok = True
      for r in range(rows):
        for c in range(cols):
          v = g[(n - 1) * p + r][c] if axis == 0 else g[r][(n - 1) * p + c]
          if v == bg:
            continue
          for k in range(n - 1):
            u = g[k * p + r][c] if axis == 0 else g[r][k * p + c]
            if u != v:
              ok = False
              break
          if not ok:
            break
        if not ok:
          break
      if ok:
        return axis, p
  return None


def _bg_ok(grid, bg):
  counts = collections.Counter(v for row in grid for v in row)
  return all(counts[bg] > c for col, c in counts.items() if col != bg)


def _q_ok(panels, template, q):
  sets = []
  for panel in panels[:-1]:
    sets.append(frozenset(panel[r][c] for r in range(len(template))
                          for c in range(len(template[0]))
                          if panel[r][c] != template[r][c]))
  if q == 1:
    return all(s == sets[0] for s in sets)
  return sets[0] != sets[1] and all(
      sets[k] == sets[k - 2] for k in range(2, len(sets)))


def _sample(axis_hint, n_hint, panel_height, panel_width, sequence_period):
  for _ in range(2000):
    bg = random.randrange(10)
    others = [c for c in range(10) if c != bg]
    random.shuffle(others)
    nf = random.choice([1, 1, 2])
    frame_cols, palette = others[:nf], others[nf:]
    axis = axis_hint if axis_hint in (0, 1) else random.randrange(2)
    if n_hint is not None:
      n = n_hint
      q = 2 if n >= 5 and random.random() < 0.5 else 1
    else:
      q = 2 if random.random() < 0.3 else 1
      n = random.choice([5, 5, 6]) if q == 2 else random.choice([3, 3, 4, 5])
    if sequence_period is not None:
      q = sequence_period
      if n_hint is None and q == 2:
        n = random.choice([5, 6])
    if n < 3 or 5 * n > 30 or (q == 2 and n < 5):
      continue
    p = random.randint(5, min(11, 30 // n))
    cross = random.randint(7 if q == 2 else 5, 30)
    ph, pw = (p, cross) if axis == 0 else (cross, p)
    ph = panel_height if panel_height is not None else ph
    pw = panel_width if panel_width is not None else pw
    p = ph if axis == 0 else pw
    if p * n > 30:
      continue
    t = 2 if min(ph, pw) >= 8 and random.random() < 0.35 else 1
    template = _make_frame(ph, pw, t, bg, frame_cols)
    if template is None:
      continue
    interior = (t, t, ph - t - 1, pw - t - 1)
    if q == 1:
      groups = _colour_groups(palette, random.choice([1, 2, 2, 3]))
      if groups is None:
        continue
      objects = _make_sequence(groups, n, interior)
      distractors = []
      if objects is None:
        continue
    else:
      ntgt = len([i for i in range(n - 1) if (n - 1 - i) % 2 == 0])
      ndis = (n - 1) - ntgt
      groups = _colour_groups(palette, random.choice([1, 1, 2]))
      dgroups = _colour_groups(palette, random.choice([1, 1, 2]))
      if groups is None or dgroups is None:
        continue
      if set().union(*groups) == set().union(*dgroups):
        continue
      objects = _make_sequence(groups, ntgt + 1, interior)
      distractors = _make_sequence(dgroups, ndis, interior)
      if objects is None or distractors is None:
        continue
    grid, _, panels = _build(template, axis, n, objects, distractors)
    if not _bg_ok(grid, bg):
      continue
    if _detect_period(grid, bg) != (axis, p):
      continue
    if not _q_ok(panels, template, q):
      continue
    return template, axis, n, objects, distractors
  raise RuntimeError('could not sample a valid scene')


def generate(template=None, axis=None, num_panels=None, objects=None,
             distractors=None, panel_height=None, panel_width=None,
             sequence_period=None):
  """Returns an input/output pair for task 2ccd9fef.

  Args:
    template: the bare frame panel (list of rows). Supply both template and
      objects for explicit mode; neither for a fresh random scene.
    panel_height: requested panel height (5..30 for sampling).
    panel_width: requested panel width (5..30 for sampling).
    sequence_period: 1 or 2; period 2 needs at least five panels.
    axis: 0 if the panels are stacked vertically, 1 if horizontally.
    num_panels: number of panels in the strip. The last panel is bare.
    objects: target-sequence objects, as dicts with keys prefix, block,
      suffix (pattern rows, -1 = empty), start (initial block copies), pos
      ((y, x) of state 0), vel ((dy, dx) per step) and transpose (growth
      along columns).
    distractors: optional objects of a second, interleaved sequence. If any
      are given, the sequence period is 2: the target occupies the panels
      with the last panel's parity, and the distractors fill the others.
  """
  if axis not in (None, 0, 1):
    raise ValueError("axis must be 0 or 1")
  if num_panels is not None and (not isinstance(num_panels, int) or not 3 <= num_panels <= 6):
    raise ValueError("num_panels must be in 3..6")
  if sequence_period not in (None, 1, 2):
    raise ValueError("sequence_period must be 1 or 2")
  if sequence_period == 2 and num_panels is not None and num_panels < 5:
    raise ValueError("Period 2 requires at least five panels")
  for d in (panel_height, panel_width):
    if d is not None and (not isinstance(d, int) or not 5 <= d <= 30):
      raise ValueError("Requested panel dimensions must be in 5..30")
  if (template is None) != (objects is None):
    raise ValueError("Explicit mode requires both template and objects")
  if template is None:
    if distractors is not None:
      raise ValueError("Explicit distractors require template and objects")
    if axis is not None and num_panels is not None:
      along = panel_height if axis == 0 else panel_width
      if along is not None and along * num_panels > 30:
        raise ValueError("Requested strip exceeds 30 cells")
    template, axis, num_panels, objects, distractors = _sample(axis, num_panels, panel_height, panel_width, sequence_period)
  else:
    if axis is None or num_panels is None or not template or not template[0] or any(len(row) != len(template[0]) for row in template):
      raise ValueError("Explicit mode requires valid frame, axis and panel count")
    if (panel_height is not None and panel_height != len(template)) or (panel_width is not None and panel_width != len(template[0])):
      raise ValueError("Template does not match requested dimensions")
    if sequence_period is not None and sequence_period != (2 if distractors else 1):
      raise ValueError("Distractors do not match sequence_period")
  if max(len(template),len(template[0])) > 30 or (len(template) if axis == 0 else len(template[0])) * num_panels > 30:
    raise ValueError("Strip exceeds 30 cells")
  grid, output, _ = _build(template, axis, num_panels, objects,
                           distractors or [])
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  frame1 = [[1, 4, 1, 1, 1, 1, 1, 1, 1, 4, 1],
            [4, 4, 1, 1, 1, 1, 1, 1, 1, 4, 4],
            [1] * 11, [1] * 11, [1] * 11, [1] * 11,
            [4, 4, 1, 1, 1, 1, 1, 1, 1, 4, 4],
            [1, 4, 1, 1, 1, 1, 1, 1, 1, 4, 1]]
  frame2 = [[8, 2, 2, 2, 2, 2, 2, 2, 2, 2, 8],
            [2, 8, 8, 2, 8, 8, 8, 2, 8, 8, 2],
            [2, 8, 2, 2, 2, 2, 2, 2, 2, 8, 2],
            [2] * 11,
            [2, 8, 2, 2, 2, 2, 2, 2, 2, 8, 2],
            [2, 8, 8, 2, 8, 8, 8, 2, 8, 8, 2],
            [8, 2, 2, 2, 2, 2, 2, 2, 2, 2, 8]]
  frame3 = [[2, 2, 8, 2, 2], [2, 8, 8, 8, 2], [8, 8, 8, 8, 8],
            [8, 8, 8, 8, 8], [2, 8, 8, 8, 2], [2, 8, 8, 8, 2],
            [2, 8, 8, 8, 2], [8, 8, 8, 8, 8], [8, 8, 8, 8, 8],
            [2, 8, 8, 8, 2], [2, 2, 8, 2, 2]]
  frame4 = [[1, 3, 3, 3, 1, 3, 3, 3, 1], [3, 1, 3, 1, 1, 1, 3, 1, 3],
            [3] * 9, [3, 1, 3, 3, 3, 3, 3, 1, 3], [3] * 9,
            [1, 1, 3, 3, 3, 3, 3, 1, 1], [3] * 9,
            [3, 1, 3, 3, 3, 3, 3, 1, 3], [3] * 9,
            [3, 1, 3, 1, 1, 1, 3, 1, 3], [1, 3, 3, 3, 1, 3, 3, 3, 1]]
  train = [
      generate(template=frame1, axis=0, num_panels=3, objects=[
          {'prefix': [], 'block': [[3, 3]], 'suffix': [], 'start': 1,
           'pos': (3, 2), 'vel': (0, 0), 'transpose': True},
          {'prefix': [], 'block': [[8, -1, -1, 8]], 'suffix': [[8, 8, 8, 8]],
           'start': 1, 'pos': (2, 7), 'vel': (0, -1), 'transpose': True}]),
      generate(template=frame2, axis=0, num_panels=3, objects=[
          {'prefix': [], 'block': [[1, 4, 1]], 'suffix': [[4, 4, 4]],
           'start': 2, 'pos': (2, 2), 'vel': (0, 0), 'transpose': True}]),
  ]
  test = [
      generate(template=frame3, axis=1, num_panels=5, objects=[
          {'prefix': [[1, 6, 1]],
           'block': [[1, 1, 1], [1, 6, 1], [1, 1, 1], [1, 6, 1]],
           'suffix': [], 'start': 0, 'pos': (1, 1), 'vel': (0, 0),
           'transpose': False}], distractors=[
          {'prefix': [[4, 6, 4], [4, 4, 4], [4, 6, 4]],
           'block': [[4, 4, 4], [4, 6, 4], [4, 4, 4], [4, 6, 4]],
           'suffix': [], 'start': 0, 'pos': (1, 1), 'vel': (0, 0),
           'transpose': False}]),
      generate(template=frame4, axis=1, num_panels=3, objects=[
          {'prefix': [[4, 4, 4, 4, 4]], 'block': [[-1, -1, 4, -1, -1]],
           'suffix': [], 'start': 1, 'pos': (3, 2), 'vel': (1, 0),
           'transpose': False},
          {'prefix': [], 'block': [[6, 6]], 'suffix': [], 'start': 1,
           'pos': (8, 2), 'vel': (-1, 0), 'transpose': False},
          {'prefix': [], 'block': [[6, 6]], 'suffix': [], 'start': 1,
           'pos': (8, 5), 'vel': (-1, 0), 'transpose': False}]),
  ]
  return {'train': train, 'test': test}
