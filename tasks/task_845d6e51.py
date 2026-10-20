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

"""ARC task 845d6e51: recolour green shapes by the matching legend form.

Rule: a legend box sits in the top-left corner. A grey (5) wall row and a
grey wall column close it off. Inside the box are a few small polyominoes.
Each one has its own colour and its own free form. Every green (3) shape
outside the box has the same form as exactly one legend shape, allowing
rotations. In the reflection extension, mirror images also match. The output
recolours each green shape with the colour of that legend shape. Everything
else is unchanged.

Scope: random scenes vary the following:
  * the grid width and height (6-30). Grids larger than 18 are synthetic
    extensions;
  * the wall row (2-5, or 2-4 by default) and the wall column (3-28);
  * the number of legend shapes (2-4 by default, up to 5 on request);
  * the legend forms, drawn from all 20 free polyominoes of 2-5 cells;
  * the displayed orientation and the colour of each legend shape;
  * the number, orientation and placement of the green copies. The green
    density is similar to the fixtures.

The legend is packed left to right, with at least one empty column between
shapes. Legend construction is width-aware: forms and orientations are chosen
to fit the box. Impossible requests, such as two distinct forms in a 2x3 box,
are rejected immediately. When the wall column is fixed and roomy, the spare
columns are spread across the box.

About half of the default scenes force two legend shapes to share a cell
count, as in fixture pair 3, so that size alone cannot decide the match. About
half of the default scenes allow rotations only. The rest contain at least one
chiral legend form and at least one green mirror copy of it, which the
reference matcher accepts. The fixtures only show achiral forms, so mirrored
chiral copies are a synthetic extension.

Green shapes are 8-separated from each other. They never enter the legend box.
They may touch the grey wall from outside, as in fixture pair 3. Every legend
form appears at least once among the greens.
"""

import functools
import random

import common

GREEN = 3
WALL = 5
PALETTE = (1, 2, 4, 6, 7, 8, 9)
ROTATIONS = (0, 3, 5, 6)  # Dihedral codes of _orient with determinant +1.
MIRRORS = (1, 2, 4, 7)  # Dihedral codes of _orient with determinant -1.
MAX_GREENS = 40
ATTEMPTS = 200
DIRS = ((0, 1), (1, 0), (0, -1), (-1, 0))


def _orient(cells, k):
  """Applies dihedral transform k (0-7) and shifts the result to the origin."""
  pts = []
  for r, c in cells:
    if k & 4:
      r, c = c, r
    if k & 1:
      r = -r
    if k & 2:
      c = -c
    pts.append((r, c))
  mr = min(p[0] for p in pts)
  mc = min(p[1] for p in pts)
  return tuple(sorted((r - mr, c - mc) for r, c in pts))


def _norm(cells):
  """Returns the canonical free form of a cell set."""
  return min(_orient(cells, k) for k in range(8))


def _dims(shape):
  return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _connected(cells):
  """True if the cell set is 4-connected."""
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr, dc in DIRS:
      n = (r + dr, c + dc)
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _enumerate_forms():
  """All free polyominoes of 2-5 cells (1 + 2 + 5 + 12 = 20 forms)."""
  level = {((0, 0),)}
  forms = []
  for _ in range(2, 6):
    nxt = set()
    for form in level:
      cells = set(form)
      for r, c in form:
        for dr, dc in DIRS:
          n = (r + dr, c + dc)
          if n not in cells:
            nxt.add(_norm(cells | {n}))
    level = nxt
    forms.extend(sorted(nxt))
  return tuple(forms)


FORMS = _enumerate_forms()


def _is_chiral(form):
  rots = set(_orient(form, k) for k in ROTATIONS)
  return _orient(form, 1) not in rots


@functools.lru_cache(maxsize=None)
def _candidates(wall_row, budget):
  """Legend-eligible forms: (form, size, min_width, chiral, orientations).

  An orientation is eligible if it fits in wall_row rows and budget columns.
  """
  out = []
  for form in FORMS:
    orients = tuple(sorted(set(
        o for o in (_orient(form, k) for k in range(8))
        if _dims(o)[0] <= wall_row and _dims(o)[1] <= budget)))
    if not orients:
      continue
    min_w = min(_dims(o)[1] for o in orients)
    out.append((form, len(form), min_w, _is_chiral(form), orients))
  out.sort(key=lambda e: (e[2], e[1], e[0]))
  return tuple(out)


def _satisfies(combo, shared, chiral):
  sizes = [e[1] for e in combo]
  if shared is True and len(set(sizes)) == len(sizes):
    return False
  if shared is False and len(set(sizes)) < len(sizes):
    return False
  if chiral and not any(e[3] for e in combo):
    return False
  return True


def _search(cands, count, budget, shared, chiral):
  """Pruned search for count distinct forms that pack into budget columns.

  Shapes are packed with one empty column between neighbours.
  """
  chosen = []

  def rec(start, used):
    need = count - len(chosen)
    if need == 0:
      return list(chosen) if _satisfies(chosen, shared, chiral) else None
    rest = sorted(e[2] for e in cands[start:])
    if len(rest) < need:
      return None
    gaps = need if chosen else need - 1
    if used + sum(rest[:need]) + gaps > budget:
      return None
    sizes = set(e[1] for e in chosen)
    has_chiral = any(e[3] for e in chosen)
    for i in range(start, len(cands)):
      e = cands[i]
      if shared is False and e[1] in sizes:
        continue
      if (shared is True and need == 1 and len(sizes) == len(chosen)
          and e[1] not in sizes):
        continue
      if chiral and need == 1 and not has_chiral and not e[3]:
        continue
      add = e[2] + (1 if chosen else 0)
      if used + add > budget:
        continue
      chosen.append(e)
      res = rec(i + 1, used + add)
      chosen.pop()
      if res is not None:
        return res
    return None

  return rec(0, 0)


@functools.lru_cache(maxsize=None)
def _feasible(wall_row, count, budget, shared, chiral):
  cands = _candidates(wall_row, budget)
  return _search(cands, count, budget, shared, chiral) is not None


def _sample_sizes(count, shared, caps):
  """Cell counts for the legend shapes, limited by the eligible forms per size."""
  caps = dict(caps)
  available = sorted(s for s in caps if caps[s] > 0)
  if shared is False:
    if count > len(available):
      return None
    return random.sample(available, count)
  sizes = []
  if shared:
    opts = [s for s in available if caps[s] >= 2]
    if not opts:
      return None
    s = random.choice(opts)
    sizes = [s, s]
    caps[s] -= 2
  while len(sizes) < count:
    opts = [s for s in sorted(caps) if caps[s] > 0]
    if not opts:
      return None
    s = random.choice(opts)
    sizes.append(s)
    caps[s] -= 1
  return sizes


def _pick_legend(wall_row, count, budget, shared, chiral):
  """Chooses count distinct legend forms. Sizes are drawn first, then forms."""
  cands = _candidates(wall_row, budget)
  by_size = {}
  for e in cands:
    by_size.setdefault(e[1], []).append(e)
  caps = {s: len(v) for s, v in by_size.items()}
  for _ in range(60):
    sizes = _sample_sizes(count, shared, caps)
    if sizes is None:
      break
    combo = []
    for s in sorted(set(sizes)):
      combo.extend(random.sample(by_size[s], sizes.count(s)))
    if (sum(e[2] for e in combo) + count - 1 <= budget
        and _satisfies(combo, shared, chiral)):
      random.shuffle(combo)
      return combo
  shuffled = list(cands)
  random.shuffle(shuffled)
  combo = _search(shuffled, count, budget, shared, chiral)
  if combo is not None:
    random.shuffle(combo)
  return combo


def _orient_legend(combo, budget):
  """Picks a displayed orientation per form, keeping the column budget."""
  shapes = []
  used = 0
  for i, e in enumerate(combo):
    later = sum(x[2] for x in combo[i + 1:]) + (len(combo) - 1 - i)
    gap = 1 if i else 0
    limit = budget - used - gap - later
    opts = [o for o in e[4] if _dims(o)[1] <= limit]
    shape = random.choice(opts)
    shapes.append(shape)
    used += gap + _dims(shape)[1]
  return shapes


def _layout(shapes, wall_row, budget, fixed):
  """Places legend shapes left to right and returns (cell lists, wall_col)."""
  n = len(shapes)
  total = sum(_dims(s)[1] for s in shapes) + n - 1
  slack = budget - total
  if fixed:
    slots = [0] * (n + 1)
    for _ in range(slack):
      slots[random.randrange(n + 1)] += 1
  else:
    slots = [random.randint(0, 1) for _ in range(n + 1)]
    while sum(slots) > slack:
      slots[random.choice([i for i, v in enumerate(slots) if v > 0])] -= 1
  col = slots[0]
  cell_lists = []
  for i, shape in enumerate(shapes):
    h, w = _dims(shape)
    top = random.randint(0, wall_row - h)
    cell_lists.append([(top + r, col + c) for r, c in shape])
    col += w
    if i < n - 1:
      col += 1 + slots[i + 1]
  return cell_lists, col + slots[n]


def _place(shape, ks, height, width, wall_row, wall_col, occupied):
  """Places an orientation (from ks) of shape, 8-separated from occupied.

  The cells may touch the wall from outside but never enter the legend box.
  """
  for _ in range(100):
    cand = _orient(shape, random.choice(ks))
    h, w = _dims(cand)
    if h > height or w > width:
      continue
    r0 = random.randint(0, height - h)
    c0 = random.randint(0, width - w)
    cells = [(r0 + r, c0 + c) for r, c in cand]
    if any(r <= wall_row and c <= wall_col for r, c in cells):
      continue
    if any((r + dr, c + dc) in occupied for r, c in cells
           for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
      continue
    return cells
  return None


def _sample_dims(width, height, wall_row, wall_col, num_greens):
  for _ in range(20):
    if width is not None:
      w = width
    else:
      # Include the narrow right-hand strips present in the demonstrations.
      lo = max(10, min(30, wall_col + 3))
      w = random.randint(lo, min(30, max(lo, wall_col + 16)))
    if height is not None:
      h = height
    else:
      lo = max(8, wall_row + 6)
      h = random.randint(lo, max(lo, random.choice([16, 20, 25, 30])))
    free = w * h - (wall_row + 1) * (wall_col + 1)
    if num_greens is None or free >= 14 * num_greens:
      return w, h
  return (width if width is not None else 30,
          height if height is not None else 30)


def _random_scene(width, height, wall_row, wall_col, num_shapes, num_greens,
                  reflections, shared_size):
  """Samples latent scene parameters, honouring any fixed arguments."""
  if wall_row is not None:
    wr_opts = [wall_row]
  else:
    wr_opts = [wr for wr in (2, 3, 3, 3, 4)
               if height is None or wr + 4 <= height]
  if wall_col is not None:
    budget = wall_col
  elif width is not None:
    budget = min(28, width - 1)
  else:
    budget = 28
  if num_shapes is not None:
    counts = [num_shapes]
  else:
    counts = [c for c in (2, 3, 4) if num_greens is None or c <= num_greens]
  need_chiral = reflections is True
  configs = [(wr, c) for wr in sorted(set(wr_opts)) for c in counts
             if _feasible(wr, c, budget, shared_size, need_chiral)]
  if not configs:
    raise ValueError('no legend with the requested shape count, size and '
                     'reflection constraints fits the legend box')
  wr_pool = [wr for wr in wr_opts if any(w == wr for w, _ in configs)]
  for _ in range(ATTEMPTS):
    wr = random.choice(wr_pool)
    count = random.choice([c for w, c in configs if w == wr])
    if shared_size is not None:
      forced = shared_size
    elif (random.random() < 0.5
          and _feasible(wr, count, budget, True, need_chiral)):
      forced = True
    else:
      forced = None
    if reflections is not None:
      refl = reflections
    else:
      refl = random.random() < 0.5
      if refl and not _feasible(wr, count, budget, forced, True):
        refl = False
    combo = _pick_legend(wr, count, budget, forced, refl)
    if combo is None:
      continue
    shapes = _orient_legend(combo, budget)
    cell_lists, wc = _layout(shapes, wr, budget, wall_col is not None)
    colours = random.sample(PALETTE, count)
    legend = list(zip(colours, cell_lists))
    w_grid, h_grid = _sample_dims(width, height, wr, wc, num_greens)
    ks = tuple(range(8)) if refl else ROTATIONS
    first = list(range(count))
    random.shuffle(first)
    mirror_idx = None
    if refl:
      mirror_idx = random.choice([i for i, e in enumerate(combo) if e[3]])
      first.remove(mirror_idx)
      first.insert(0, mirror_idx)
    if num_greens is not None:
      extras = num_greens - count
    else:
      free = w_grid * h_grid - (wr + 1) * (wc + 1)
      lo = max(1, free // 60)
      hi = min(MAX_GREENS - count, max(lo + 1, free // 22))
      extras = random.randint(min(lo, hi), hi)
    order = first + [random.randrange(count) for _ in range(extras)]
    occupied = set()
    greens = []
    failed = False
    for pos, idx in enumerate(order):
      use = MIRRORS if (pos == 0 and mirror_idx is not None) else ks
      cells = _place(shapes[idx], use, h_grid, w_grid, wr, wc, occupied)
      if cells is None:
        if pos < count or num_greens is not None:
          failed = True
          break
        continue
      occupied.update(cells)
      greens.append((idx, cells))
    if failed:
      continue
    random.shuffle(greens)
    return {'width': w_grid, 'height': h_grid, 'wall_row': wr,
            'wall_col': wc, 'legend': legend, 'greens': greens,
            'reflections': refl, 'shared_size': forced}
  raise ValueError('could not place the green shapes for the requested '
                   'parameters')


def _as_int(value, name):
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(name + ' must be an integer')
  return value


def _opt_int(value, name):
  return None if value is None else _as_int(value, name)


def _coerce_shapes(items, name):
  """Turns [(key, [(r, c), ...]), ...] with lists or tuples into tuples."""
  if not isinstance(items, (list, tuple)):
    raise ValueError(name + ' must be a list or tuple')
  out = []
  for item in items:
    if not isinstance(item, (list, tuple)) or len(item) != 2:
      raise ValueError(name + ' entries must be (key, cells) pairs')
    key = _as_int(item[0], name)
    if not isinstance(item[1], (list, tuple)):
      raise ValueError(name + ' cells must be a list or tuple')
    cells = []
    for p in item[1]:
      if not isinstance(p, (list, tuple)) or len(p) != 2:
        raise ValueError(name + ' cells must be (row, col) pairs')
      cells.append((_as_int(p[0], name), _as_int(p[1], name)))
    if not cells or len(set(cells)) != len(cells):
      raise ValueError(name + ' shapes must be non-empty without duplicates')
    out.append((key, cells))
  return out


def _build(width, height, wall_row, wall_col, legend, greens,
           reflections=None, shared_size=None):
  """Renders a scene and its answer after checking the invariants."""
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError('grid size out of range')
  if not (1 <= wall_row < height and 1 <= wall_col < width):
    raise ValueError('wall outside grid')
  if len(legend) < 2:
    raise ValueError('need at least two legend shapes')
  colours = [colour for colour, _ in legend]
  if len(set(colours)) != len(colours):
    raise ValueError('legend colours must be distinct')
  forms = []
  owner = {}
  for i, (colour, cells) in enumerate(legend):
    if colour in (0, GREEN, WALL) or not 0 <= colour <= 9:
      raise ValueError('bad legend colour')
    if not _connected(cells):
      raise ValueError('legend shape must be 4-connected')
    for r, c in cells:
      if not (0 <= r < wall_row and 0 <= c < wall_col) or (r, c) in owner:
        raise ValueError('legend cell outside box or overlapping')
      owner[(r, c)] = i
    forms.append(_norm(cells))
  for (r, c), i in owner.items():
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        j = owner.get((r + dr, c + dc))
        if j is not None and j != i:
          raise ValueError('legend shapes must not touch')
  if len(set(forms)) != len(forms):
    raise ValueError('legend forms must be distinct')
  if shared_size is not None:
    sizes = [len(cells) for _, cells in legend]
    if (len(set(sizes)) < len(sizes)) != shared_size:
      raise ValueError('shared_size disagrees with legend')
  for idx, _ in greens:
    if not 0 <= idx < len(legend):
      raise ValueError('bad legend index')
  if set(idx for idx, _ in greens) != set(range(len(legend))):
    raise ValueError('every legend form must appear among the greens')
  mirrored = False
  green_cells = set()
  for idx, cells in greens:
    if _norm(cells) != forms[idx]:
      raise ValueError('green shape does not match its legend form')
    rots = set(_orient(legend[idx][1], k) for k in ROTATIONS)
    if _orient(cells, 0) not in rots:
      mirrored = True
    for r, c in cells:
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError('green cell out of bounds')
      if r <= wall_row and c <= wall_col:
        raise ValueError('green cell inside legend box')
      for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
          if (r + dr, c + dc) in green_cells:
            raise ValueError('green shapes overlap or touch')
    green_cells.update(cells)
  if reflections is False and mirrored:
    raise ValueError('green mirror copy present but reflections=False')
  if reflections is True and not mirrored:
    raise ValueError('reflections=True needs at least one mirror copy')
  grid = common.grid(width, height, 0)
  for c in range(wall_col + 1):
    grid[wall_row][c] = WALL
  for r in range(wall_row + 1):
    grid[r][wall_col] = WALL
  for colour, cells in legend:
    for r, c in cells:
      grid[r][c] = colour
  output = [row[:] for row in grid]
  for idx, cells in greens:
    colour = legend[idx][0]
    for r, c in cells:
      grid[r][c] = GREEN
      output[r][c] = colour
  return {'input': grid, 'output': output}


def generate(width=None, height=None, wall_row=None, wall_col=None,
             legend=None, greens=None, num_shapes=None, num_greens=None,
             reflections=None, shared_size=None):
  """Builds an input/output pair.

  Args:
    width: grid width. Random scenes accept 6-30 and need width > wall_col.
      Random if None.
    height: grid height. Random scenes accept 6-30 and need
      height >= wall_row + 4. Random if None.
    wall_row: row index of the grey wall row, which spans columns
      0..wall_col. Random scenes accept 2-5. Random (2-4) if None.
    wall_col: column index of the grey wall column, which spans rows
      0..wall_row. Random scenes accept 3-28. Combinations whose box cannot
      hold the requested legend are rejected immediately. Random if None.
    legend: list of (colour, [(row, col), ...]) legend shapes strictly inside
      the box. Shapes must not touch. Lists or tuples are accepted. If None, a
      fresh random scene is sampled, honouring the other arguments.
    greens: list of (legend_index, [(row, col), ...]) green shapes. Each one
      must have the same free form as legend[legend_index]. Requires legend.
    num_shapes: number of legend shapes (2-5) for random scenes.
    num_greens: exact number of green shapes, from num_shapes (or 2) to 40.
    reflections: True means at least one green is a mirror copy of a chiral
      legend form. False means greens are rotations only. None picks one at
      random in random mode and skips the check in explicit mode.
    shared_size: True means at least two legend shapes share a cell count.
      False means all legend cell counts differ (needs num_shapes <= 4).
      None forces sharing half the time in random mode. In explicit mode a
      non-None value is checked against the legend.
  """
  for name, flag in (('reflections', reflections),
                     ('shared_size', shared_size)):
    if flag is not None and not isinstance(flag, bool):
      raise ValueError(name + ' must be None, True or False')
  width = _opt_int(width, 'width')
  height = _opt_int(height, 'height')
  wall_row = _opt_int(wall_row, 'wall_row')
  wall_col = _opt_int(wall_col, 'wall_col')
  num_shapes = _opt_int(num_shapes, 'num_shapes')
  num_greens = _opt_int(num_greens, 'num_greens')
  if legend is None:
    if greens is not None:
      raise ValueError('greens requires an explicit legend')
    if wall_row is not None and not 2 <= wall_row <= 5:
      raise ValueError('wall_row must be in 2..5')
    if wall_col is not None and not 3 <= wall_col <= 28:
      raise ValueError('wall_col must be in 3..28')
    if num_shapes is not None and not 2 <= num_shapes <= 5:
      raise ValueError('num_shapes must be in 2..5')
    if shared_size is False and num_shapes is not None and num_shapes > 4:
      raise ValueError('distinct sizes allow at most 4 legend shapes')
    if width is not None:
      if not 6 <= width <= 30:
        raise ValueError('width must be in 6..30')
      if wall_col is not None and width <= wall_col:
        raise ValueError('width must exceed wall_col')
    if height is not None:
      if not 6 <= height <= 30:
        raise ValueError('height must be in 6..30')
      if height < (wall_row if wall_row is not None else 2) + 4:
        raise ValueError('height must be at least wall_row + 4')
    if num_greens is not None:
      low = num_shapes if num_shapes is not None else 2
      if not low <= num_greens <= MAX_GREENS:
        raise ValueError('num_greens must cover every form and be <= 40')
    return _build(**_random_scene(width, height, wall_row, wall_col,
                                  num_shapes, num_greens, reflections,
                                  shared_size))
  if None in (width, height, wall_row, wall_col) or greens is None:
    raise ValueError('explicit legend needs width, height, walls and greens')
  legend = _coerce_shapes(legend, 'legend')
  greens = _coerce_shapes(greens, 'greens')
  if num_shapes is not None and num_shapes != len(legend):
    raise ValueError('num_shapes disagrees with legend')
  if num_greens is not None and num_greens != len(greens):
    raise ValueError('num_greens disagrees with greens')
  return _build(width, height, wall_row, wall_col, legend, greens,
                reflections=reflections, shared_size=shared_size)


def validate():
  """Reconstructs the canonical fixtures through explicit latent parameters."""
  train = [
      generate(width=16, height=16, wall_row=3, wall_col=10,
               legend=[(2, [(0, 1), (1, 1)]),
                       (4, [(0, 3), (0, 4), (1, 3)]),
                       (1, [(0, 6), (0, 7), (0, 8), (1, 7)])],
               greens=[(2, [(0, 13), (1, 13), (1, 14), (2, 13)]),
                       (1, [(5, 1), (6, 1), (6, 2)]),
                       (0, [(5, 5), (6, 5)]),
                       (2, [(5, 11), (5, 12), (5, 13), (6, 12)]),
                       (0, [(7, 8), (8, 8)]),
                       (0, [(9, 1), (9, 2)]),
                       (1, [(9, 12), (9, 13), (10, 13)]),
                       (2, [(11, 1), (11, 2), (11, 3), (12, 2)]),
                       (1, [(11, 7), (12, 6), (12, 7)]),
                       (1, [(12, 10), (12, 11), (13, 10)]),
                       (2, [(13, 14), (14, 13), (14, 14), (15, 14)]),
                       (0, [(14, 3), (14, 4)])]),
      generate(width=16, height=16, wall_row=3, wall_col=7,
               legend=[(2, [(0, 1), (1, 0), (1, 1), (1, 2)]),
                       (1, [(0, 4), (0, 5), (1, 4)])],
               greens=[(0, [(1, 10), (1, 11), (1, 12), (2, 11)]),
                       (1, [(4, 13), (4, 14), (5, 13)]),
                       (0, [(6, 2), (7, 1), (7, 2), (8, 2)]),
                       (1, [(6, 7), (6, 8), (7, 8)]),
                       (0, [(10, 11), (11, 10), (11, 11), (11, 12)]),
                       (1, [(11, 3), (12, 2), (12, 3)]),
                       (0, [(13, 6), (14, 6), (14, 7), (15, 6)]),
                       (1, [(13, 13), (14, 12), (14, 13)])]),
      generate(width=10, height=10, wall_row=3, wall_col=7,
               legend=[(2, [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)]),
                       (7, [(0, 4), (1, 3), (1, 4), (1, 5), (2, 4)])],
               greens=[(1, [(4, 2), (5, 1), (5, 2), (5, 3), (6, 2)]),
                       (0, [(5, 5), (5, 7), (6, 5), (6, 6), (6, 7)]),
                       (0, [(8, 3), (8, 4), (8, 5), (9, 3), (9, 5)])]),
  ]
  test = [
      generate(width=17, height=18, wall_row=3, wall_col=11,
               legend=[(2, [(0, 1), (1, 0), (1, 1)]),
                       (1, [(0, 3), (1, 3), (1, 4), (2, 3)]),
                       (4, [(0, 6), (0, 7), (1, 6), (2, 6), (2, 7)]),
                       (8, [(1, 9), (1, 10)])],
               greens=[(3, [(1, 14), (2, 14)]),
                       (3, [(4, 15), (4, 16)]),
                       (1, [(5, 4), (6, 3), (6, 4), (6, 5)]),
                       (0, [(6, 0), (6, 1), (7, 0)]),
                       (2, [(7, 8), (7, 9), (8, 9), (9, 8), (9, 9)]),
                       (1, [(8, 13), (9, 13), (9, 14), (10, 13)]),
                       (2, [(11, 2), (11, 3), (11, 4), (12, 2), (12, 4)]),
                       (3, [(12, 15), (13, 15)]),
                       (1, [(13, 9), (13, 10), (13, 11), (14, 10)]),
                       (3, [(15, 4), (15, 5)]),
                       (0, [(15, 14), (16, 13), (16, 14)]),
                       (0, [(16, 0), (16, 1), (17, 1)])]),
  ]
  return {'train': train, 'test': test}
