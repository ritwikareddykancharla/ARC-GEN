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

"""ARC task 880c1354: rotate border-region colours one step clockwise.

Rule: cells of colour 4 (an inner body) and colour 7 (outlines) form a fixed
skeleton. Every other cell belongs to a coloured region. Each region touches the
grid border along exactly one contiguous stretch. A clockwise walk around the
border (top row left to right, right column down, bottom row right to left, left
column up) gives a cyclic order of the regions. Each region keeps its shape and
takes the colour of the previous region in that cycle. With two regions this is
a swap. Cells of colour 4 and 7 never change.

Scope: random scenes have a width and height of 6..16. Explicit sizes reach 30;
all non-8x8 sizes are synthetic extensions of the 8x8 fixtures. A random scene uses 2..5
regions, weighted towards 3 and 4. Explicit requests may use 2..8 regions if the
border is long enough. Region colours are distinct and come from
{0,1,2,3,5,6,8,9}; 0 is a legal region colour, as in the test fixture.

Construction: the border cycle is cut into arcs separated by skeleton gaps. The
total gap length is drawn from k up to about 55% of the perimeter (skewed short)
and split randomly, so long skeleton stretches on the border occur, as in the
fixtures. Different arcs must be at Chebyshev distance >= 2. Each region grows
inward from its arc by weighted random 4-connected growth through interior cells
only, so its border footprint stays exactly its arc. Regions stay at Chebyshev
distance >= 2, so they are separate under 4- and 8-connectivity. Non-region
cells that are 4-adjacent to a region become 7. Some border gaps are also
outlined fully in 7; otherwise the 4 body may reach the border (fixture pair 1).
The remaining cells are 4. Detached 4 islands become 7, so there is exactly one
4 body.

The output comes from the latent labels and the clockwise colour list. No solver
is used. The fixtures are rebuilt from explicit label layouts plus colour lists.
These layouts are checked for the structural invariants of the rule. Explicit
layouts need not have the random sampler's single 4 body. Random growth can
produce irregular outlines and holes absent from the finite fixtures; these
are morphological extensions, not additional colour-transition rules.
"""

import random

import common

COLOURS = [0, 1, 2, 3, 5, 6, 8, 9]
LETTERS = 'abcdefgh'
MIN_SIDE = 6
MAX_SIDE = 30
RANDOM_MAX_SIDE = 16
DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _border_walk(w, h):
  """Clockwise border path starting at the top-left corner."""
  path = [(0, x) for x in range(w)]
  path += [(y, w - 1) for y in range(1, h)]
  path += [(h - 1, x) for x in range(w - 2, -1, -1)]
  path += [(y, 0) for y in range(h - 2, 0, -1)]
  return path


def _max_regions(w, h):
  """Perimeter-based sampling bound, not a guarantee for every random draw."""
  return min(len(COLOURS), (2 * (w + h) - 4) // 5)


def _components4(cells):
  """4-connected components of a set of (r, c) cells."""
  todo = set(cells)
  comps = []
  while todo:
    seed = todo.pop()
    comp = [seed]
    stack = [seed]
    while stack:
      r, c = stack.pop()
      for dr, dc in DIRS4:
        p = (r + dr, c + dc)
        if p in todo:
          todo.remove(p)
          comp.append(p)
          stack.append(p)
    comps.append(comp)
  return comps


def _arcs_separated(arcs):
  """True if cells of different arcs are at Chebyshev distance >= 2."""
  for i in range(len(arcs)):
    for j in range(i + 1, len(arcs)):
      for (r1, c1) in arcs[i]:
        for (r2, c2) in arcs[j]:
          if max(abs(r1 - r2), abs(c1 - c2)) < 2:
            return False
  return True


def _pick_arcs(w, h, k):
  """Cut the border cycle into k arcs (clockwise order) separated by gaps."""
  path = _border_walk(w, h)
  n = len(path)
  hi = max(k, min(n - 2 * k, int(n * 0.55)))
  for _ in range(200):
    total_gap = random.randint(k, random.randint(k, hi))
    gaps = [1] * k
    gw = [random.uniform(0.2, 1.0) for _ in range(k)]
    for _ in range(total_gap - k):
      gaps[random.choices(range(k), weights=gw)[0]] += 1
    rest = n - total_gap
    if rest < 2 * k:
      continue
    parts = [2] * k
    weights = [random.uniform(0.3, 1.0) for _ in range(k)]
    for _ in range(rest - 2 * k):
      parts[random.choices(range(k), weights=weights)[0]] += 1
    pos = random.randrange(n)
    arcs = []
    for i in range(k):
      arcs.append([path[(pos + j) % n] for j in range(parts[i])])
      pos += parts[i] + gaps[i]
    if _arcs_separated(arcs):
      return arcs
  return None


def _grow(w, h, arcs):
  """Grow regions inward from their arcs; returns label grid (-1 = skeleton)."""
  k = len(arcs)
  label = [[-1] * w for _ in range(h)]
  cells = []
  for i, arc in enumerate(arcs):
    cells.append(list(arc))
    for (r, c) in arc:
      label[r][c] = i
  interior = (h - 2) * (w - 2)
  budget = int(interior * random.uniform(0.1, 0.45))
  weights = [random.uniform(0.3, 1.0) for _ in range(k)]
  stuck = set()

  def allowed(r, c, i):
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        v = label[r + dr][c + dc]
        if v != -1 and v != i:
          return False
    return True

  grown = 0
  for _ in range(4 * interior + 10):
    if grown >= budget or len(stuck) == k:
      break
    live = [j for j in range(k) if j not in stuck]
    i = random.choices(live, weights=[weights[j] for j in live])[0]
    cands = set()
    for (r, c) in cells[i]:
      for dr, dc in DIRS4:
        rr, cc = r + dr, c + dc
        if 1 <= rr < h - 1 and 1 <= cc < w - 1 and label[rr][cc] == -1:
          if allowed(rr, cc, i):
            cands.add((rr, cc))
    if not cands:
      stuck.add(i)  # Candidates only shrink when other regions grow.
      continue
    r, c = random.choice(sorted(cands))
    label[r][c] = i
    cells[i].append((r, c))
    grown += 1
  return label


def _gap_runs(path, label):
  """Maximal runs of non-region border cells along the clockwise path."""
  n = len(path)
  start = 0
  while label[path[start][0]][path[start][1]] < 0:
    start += 1
  runs, cur = [], []
  for t in range(1, n + 1):
    r, c = path[(start + t) % n]
    if label[r][c] < 0:
      cur.append((r, c))
    elif cur:
      runs.append(cur)
      cur = []
  return runs


def _build_skeleton(label):
  """Choose 4/7 for every non-region cell; None if no 4 body remains."""
  h, w = len(label), len(label[0])
  sk = [[None] * w for _ in range(h)]
  for r in range(h):
    for c in range(w):
      if label[r][c] >= 0:
        continue
      v = 4
      for dr, dc in DIRS4:
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w and label[rr][cc] >= 0:
          v = 7
      sk[r][c] = v
  p = random.choice((0.0, 0.35, 0.7))
  for run in _gap_runs(_border_walk(w, h), label):
    if random.random() < p:
      for (r, c) in run:
        sk[r][c] = 7
  fours = [(r, c) for r in range(h) for c in range(w) if sk[r][c] == 4]
  comps = _components4(fours)
  if not comps:
    return None
  comps.sort(key=len, reverse=True)
  for comp in comps[1:]:
    for (r, c) in comp:
      sk[r][c] = 7
  return sk


def _render(label, colors, skeleton):
  """Build input/output grids from region labels and clockwise colours."""
  h, w = len(label), len(label[0])
  k = len(colors)
  inp = common.grid(w, h, 0)
  out = common.grid(w, h, 0)
  for r in range(h):
    for c in range(w):
      i = label[r][c]
      if i >= 0:
        inp[r][c] = colors[i]
        out[r][c] = colors[(i - 1) % k]
      else:
        inp[r][c] = skeleton[r][c]
        out[r][c] = skeleton[r][c]
  return {'input': inp, 'output': out}


def _check_colors(colors):
  if not isinstance(colors, (list, tuple)):
    raise ValueError('colors must be a list or tuple')
  cols = list(colors)
  if len(cols) < 2 or len(cols) > len(COLOURS):
    raise ValueError('colors must list 2..8 region colours')
  for c in cols:
    if not _is_int(c):
      raise ValueError('region colours must be ints')
    if c not in COLOURS:
      raise ValueError('region colours must be in 0..9 and not 4 or 7')
  if len(set(cols)) != len(cols):
    raise ValueError('region colours must be distinct')
  return cols


def _check_layout(label, skeleton, k):
  """Raise ValueError unless the layout satisfies the rule invariants."""
  h, w = len(label), len(label[0])
  path = _border_walk(w, h)
  n = len(path)
  order = []
  for (r, c) in path:
    i = label[r][c]
    if i >= 0 and i not in order:
      order.append(i)
  if len(order) != k:
    raise ValueError('every region must touch the border')
  for j in range(k):
    if order[(j + 1) % k] != (order[j] + 1) % k:
      raise ValueError('region letters must follow clockwise border order')
  for i in range(k):
    flags = [label[r][c] == i for (r, c) in path]
    starts = sum(1 for j in range(n) if flags[j] and not flags[j - 1])
    if starts != 1:
      raise ValueError('each region must meet the border in one arc')
    cells = [(r, c) for r in range(h) for c in range(w) if label[r][c] == i]
    if len(_components4(cells)) != 1:
      raise ValueError('each region must be 4-connected')
  for r in range(h):
    for c in range(w):
      i = label[r][c]
      for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
          rr, cc = r + dr, c + dc
          if not (0 <= rr < h and 0 <= cc < w):
            continue
          j = label[rr][cc]
          if i >= 0 and j >= 0 and i != j:
            raise ValueError('different regions must not touch')
          if (i < 0 and skeleton[r][c] == 4 and j >= 0 and
              abs(dr) + abs(dc) == 1):
            raise ValueError('a 4 cell may not be 4-adjacent to a region')


def _from_layout(layout, colors):
  """Rebuild a pair from an explicit label layout (fixture replay)."""
  if colors is None:
    raise ValueError('layout requires colors')
  cols = _check_colors(colors)
  if (not isinstance(layout, (list, tuple)) or not layout
      or not isinstance(layout[0], str) or not layout[0]):
    raise ValueError('layout must be a non-empty list of strings')
  width = len(layout[0])
  if not (3 <= len(layout) <= MAX_SIDE and 3 <= width <= MAX_SIDE):
    raise ValueError('layout sides must be 3..30')
  label, skeleton = [], []
  for row in layout:
    if not isinstance(row, str) or len(row) != width:
      raise ValueError('layout rows must be strings of equal length')
    lrow, srow = [], []
    for ch in row:
      if ch in '47':
        lrow.append(-1)
        srow.append(int(ch))
      elif ch in LETTERS:
        lrow.append(LETTERS.index(ch))
        srow.append(None)
      else:
        raise ValueError('layout characters must be 4, 7 or a..h')
    label.append(lrow)
    skeleton.append(srow)
  used = sorted({v for row in label for v in row if v >= 0})
  if used != list(range(len(cols))):
    raise ValueError('layout labels must be a,b,... matching colors')
  _check_layout(label, skeleton, len(cols))
  return _render(label, cols, skeleton)


def generate(width=None, height=None, num_regions=None, colors=None,
             layout=None):
  """Generate one input/output pair.

  Args:
    width: grid width (int). Random is 6..16; explicit values may be 6..30.
    height: grid height (int). Random is 6..16; explicit values may be 6..30.
    num_regions: number of border regions (int). Random is 2..5, weighted
      towards 3 and 4 and capped by the perimeter. Explicit values may be 2..8
      and must fit the border (at most (2*(w+h)-4)//5). It must equal
      len(colors) if both are given.
    colors: region colours in clockwise border order. They must be distinct
      ints drawn from {0,1,2,3,5,6,8,9}. If given, they fix the region count.
    layout: optional list of strings for fixture replay. '4'/'7' are skeleton
      cells and letters 'a'..'h' are region labels in clockwise order. It needs
      `colors`, cannot be combined with width, height or num_regions, and is
      checked for the rule's structural invariants. Layout sides may be 3..30.
  """
  if layout is not None:
    if width is not None or height is not None or num_regions is not None:
      raise ValueError('layout cannot be combined with width/height/num_regions')
    return _from_layout(layout, colors)

  for name, v in (('width', width), ('height', height)):
    if v is None:
      continue
    if not _is_int(v):
      raise ValueError('%s must be an int' % name)
    if not MIN_SIDE <= v <= MAX_SIDE:
      raise ValueError('%s must be in %d..%d' % (name, MIN_SIDE, MAX_SIDE))
  if num_regions is not None and not _is_int(num_regions):
    raise ValueError('num_regions must be an int')
  cols_fixed = None
  if colors is not None:
    cols_fixed = _check_colors(colors)
    if num_regions is not None and num_regions != len(cols_fixed):
      raise ValueError('num_regions must equal len(colors)')
    num_regions = len(cols_fixed)
  if num_regions is not None and not 2 <= num_regions <= len(COLOURS):
    raise ValueError('num_regions must be in 2..8')
  if num_regions is not None and width is not None and height is not None:
    if num_regions > _max_regions(width, height):
      raise ValueError('too many regions for this border length')

  for _ in range(300):
    w = width if width is not None else random.randint(MIN_SIDE, RANDOM_MAX_SIDE)
    h = height if height is not None else random.randint(MIN_SIDE,
                                                         RANDOM_MAX_SIDE)
    if num_regions is not None:
      k = num_regions
      if k > _max_regions(w, h):
        continue
    else:
      cap = max(2, min(5, (2 * (w + h) - 4) // 6))
      options = list(range(2, cap + 1))
      k = random.choices(options, weights=[1, 3, 3, 2][:len(options)])[0]
    cols = list(cols_fixed) if cols_fixed is not None else random.sample(
        COLOURS, k)
    arcs = _pick_arcs(w, h, k)
    if arcs is None:
      continue
    label = _grow(w, h, arcs)
    skeleton = _build_skeleton(label)
    if skeleton is None:
      continue
    fours = sum(row.count(4) for row in skeleton)
    if fours < max(2, (w * h) // 16):
      continue
    return _render(label, cols, skeleton)
  raise RuntimeError('could not construct scene for the requested parameters')


def validate():
  """Rebuild the canonical fixtures from explicit layouts."""
  train = [
      generate(colors=[6, 2, 3, 1], layout=[
          'aa7447bb', 'a744447b', '74444447', '44444447',
          '7444777c', 'd7447ccc', 'dd747ccc', 'ddd77ccc']),
      generate(colors=[1, 6, 9], layout=[
          'aa7447bb', 'a74447bb', '744447bb', 'c74447bb',
          'cc7447bb', 'ccc747bb', 'cccc77bb', 'ccccc7bb']),
      generate(colors=[6, 5], layout=[
          'aaaaaaaa', 'aaaaaaaa', '7777777a', '74444447',
          '74444777', '74777bbb', '77bbbbbb', '7bbbbbbb']),
  ]
  test = [
      generate(colors=[6, 0, 3], layout=[
          'aa777bbb', 'aa7447bb', 'a74447bb', '744447bb',
          '444447bb', '777747bb', 'cccc7bbb', 'cccc7bbb']),
  ]
  return {'train': train, 'test': test}
