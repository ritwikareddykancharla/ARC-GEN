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

"""ARC-GEN style generator for task c9680e90.

Rule: the background is 7. A full line of 9s splits the grid into two halves
of equal size. Each red 2 on one side has a chain of 6s attached to it. Each 2
is mirrored by a grey 5 on the other side. To make the output, erase all 6s,
2s and 5s. Move each 2 to the far end of its chain, which is the chain cell
farthest from the 2. Then draw a new 5 at the mirror image of each moved 2
across the divider. With the divider at row d, row y maps to row 2*d - y in
the same column.

Scope: by default the divider is horizontal and sits at the middle row of a
grid with an odd height, and the chains are below it, as in every fixture.
Random heights are odd values in 5..29. Random widths are 5..30, and explicit
widths may be 3..30. Grids larger than the 7..11 fixtures are a synthetic
extension. Each chain is an induced simple path of 6s, so its far end is
unique. A 6 never touches a cell of another object. Two 2s may touch, as in
the third training example, under the touching_reds control. Every row other
than the divider keeps a 7, and 7 is always the strict majority colour.

Two layout engines build the chain half:
  * Grown (the default for sparse scenes). Reds are placed at random and
    chains grow one cell at a time. Chains may go straight or turn, up to
    max_chain_length cells. These are the richest scenes.
  * Dense packing. It is used when a requested count is above half the
    capacity, when a grown attempt fails, when dense=True, and for about 15%
    of default samples. A checked greedy packer lays deterministic tilings
    of red/6 dominoes. The tiling is reflected at random and a random subset
    of the requested size is kept. Then 2s are swapped with their 6, and
    chains are extended (straight or turning) wherever the no-touch, row and
    majority constraints still hold. Dense scenes trade chain length and
    turning for object count.

Capacity: the advertised capacity of a half is the size of the largest pack
the dense engine builds for it, capped at 30 objects. With touching 2s
allowed, the main tiling is period-3 stripes: a column of 2s whose 6s
alternate left and right by row. A 2x30 half therefore holds 20 objects.
With touching forbidden, the main tiling is a 2x2-block checkerboard of
dominoes, so a 2x30 half holds 15. Any requested count up to the capacity is
built exactly, and requested counts are never reduced. Larger requests raise
ValueError before any sampling.

Opt-in synthetic extensions:
  * orientation='vertical' transposes the scene, so the divider becomes a
    column.
  * chain_side='before' puts the chains above (or left of) the divider and
    the 5s below (or right of) it.
Explicit one-row halves (divider-crossing side 3) are supported when
background dominance and the requested count are feasible; defaults still
sample 5..29. Off-centre dividers, branching chains and chainless 2s are
not generated.
"""

import functools
import random

import common

BG = 7
DIV = 9
RED = 2
CHAIN = 6
GREY = 5
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
MAX_OBJECTS = 30
MIN_SPAN = 3
MAX_SPAN = 29
DENSE_SHARE = 0.15
# Domino orientations as (red offset, 6 offset) from the scan cell.
ORIENTS = {
    "R>": ((0, 0), (0, 1)),
    "<R": ((0, 1), (0, 0)),
    "Rv": ((0, 0), (1, 0)),
    "^R": ((1, 0), (0, 0)),
}


def _neighbors(r, c):
  return [(r + dr, c + dc) for dr, dc in DIRS]


def _adjacent(a, b):
  return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _int_arg(name, v, lo, hi):
  """Return v if it is a true int in lo..hi (or None); else raise ValueError."""
  if v is None:
    return None
  if not _is_int(v):
    raise ValueError("%s must be an int" % name)
  if not lo <= v <= hi:
    raise ValueError("%s must be in %d..%d" % (name, lo, hi))
  return v


def _sample_length(max_len):
  """Chain length favouring 2..4 so that long and turning chains are common."""
  lengths = list(range(1, max_len + 1))
  weights = [1 if n == 1 else (3 if n <= 4 else 2) for n in lengths]
  return random.choices(lengths, weights)[0]


# Dense packing. Coordinates are local to the chain half: local row i in
# 0..h-1 is canonical row d + 1 + i, and h = d.


def _majority_ok(h, w, n, cells):
  """True if 7 strictly outnumbers 9, 2, 5 and 6 (n objects, cells 6s)."""
  bg = 2 * h * w - 2 * n - cells
  return bg > w and bg > n and bg > cells


def _domino_ok(red, six, owner, touch, h, w):
  """Can a red with a single 6 be added beside the owned cells?"""
  for cell in (red, six):
    if not (0 <= cell[0] < h and 0 <= cell[1] < w) or cell in owner:
      return False
  for nb in _neighbors(*six):
    if nb != red and nb in owner:
      return False
  for nb in _neighbors(*red):
    if nb != six and nb in owner and (not touch or owner[nb] != RED):
      return False
  return True


def _greedy(h, w, touch, order):
  """Add dominoes in order whenever all scene constraints still hold."""
  owner = {}
  used = [0] * h
  objs = []
  for red, six in order:
    if not _domino_ok(red, six, owner, touch, h, w):
      continue
    used[red[0]] += 1
    used[six[0]] += 1
    n = len(objs) + 1
    if (used[red[0]] >= w or used[six[0]] >= w
        or not _majority_ok(h, w, n, n)):
      used[red[0]] -= 1
      used[six[0]] -= 1
      continue
    owner[red] = RED
    owner[six] = CHAIN
    objs.append((red, six))
  return tuple(objs)


def _raster(h, w, prefs):
  out = []
  for i in range(h):
    for j in range(w):
      for key in prefs:
        (a, b), (c, e) = ORIENTS[key]
        out.append(((i + a, j + b), (i + c, j + e)))
  return out


def _checker_h(h, w, off, par):
  """2x2-block checkerboard of horizontal dominoes."""
  out = []
  for i in range(h):
    for j in range(-1, w):
      k = j - off
      if k % 2 == 0 and (k // 2 + i) % 2 == par:
        out.append(((i, j), (i, j + 1)))
  return out


def _checker_v(h, w, off, par):
  """2x2-block checkerboard of vertical dominoes."""
  out = []
  for j in range(w):
    for i in range(-1, h):
      k = i - off
      if k % 2 == 0 and (k // 2 + j) % 2 == par:
        out.append(((i, j), (i + 1, j)))
  return out


def _stripes_v(h, w, off, par):
  """Period-3 columns of 2s with 6s alternating left and right by row."""
  out = []
  for i in range(h):
    side = -1 if (i + par) % 2 == 0 else 1
    for j in range(w):
      if (j - off) % 3 == 0:
        out.append(((i, j), (i, j + side)))
  return out


def _stripes_h(h, w, off, par):
  """Period-3 rows of 2s with 6s alternating above and below by column."""
  out = []
  for i in range(h):
    if (i - off) % 3:
      continue
    for j in range(w):
      side = -1 if (j + par) % 2 == 0 else 1
      out.append(((i, j), (i + side, j)))
  return out


def _orders(h, w, touch):
  orders = []
  if touch:
    fill = _raster(h, w, ("R>", "<R", "Rv", "^R"))
    for off in range(3):
      for par in range(2):
        orders.append(_stripes_v(h, w, off, par) + fill)
    for off in range(3):
      orders.append(_stripes_h(h, w, off, 0) + fill)
    orders.append(fill)
  else:
    fill = _raster(h, w, ("R>", "Rv"))
    for off in range(2):
      for par in range(2):
        orders.append(_checker_h(h, w, off, par) + fill)
        orders.append(_checker_v(h, w, off, par) + fill)
    orders.append(fill)
    orders.append(_raster(h, w, ("Rv", "R>")))
  return orders


@functools.lru_cache(maxsize=None)
def _packs(h, w, touch):
  """Deterministic dense packs of red/6 dominoes for an h x w half."""
  seen = set()
  packs = []
  for order in _orders(h, w, touch):
    pack = _greedy(h, w, touch, order)
    key = frozenset(pack)
    if pack and key not in seen:
      seen.add(key)
      packs.append(pack)
  return tuple(packs)


def _has_pair(pack):
  reds = set(red for red, _ in pack)
  return any(nb in reds for red in reds for nb in _neighbors(*red))


def _mode_packs(h, w, touching_reds):
  """Packs usable for the touching mode (True needs an adjacent 2-pair)."""
  out = []
  if touching_reds is not True:
    out.extend(_packs(h, w, False))
  if touching_reds is not False:
    for pack in _packs(h, w, True):
      if touching_reds is None or _has_pair(pack):
        out.append(pack)
  return out


def _capacity(h, w, touching_reds):
  """Constructive capacity of an h x w chain half (at most MAX_OBJECTS)."""
  sizes = [len(p) for p in _mode_packs(h, w, touching_reds)]
  return min(MAX_OBJECTS, max(sizes) if sizes else 0)


def _embellish(h, w, base, touching_reds, max_len, locked):
  """Swap 2s with their 6 and extend chains where constraints allow."""
  allow_touch = touching_reds is not False
  objs = [(red, list(chain)) for red, chain in base]
  owner = {}
  used = [0] * h
  cells = 0
  for red, chain in objs:
    owner[red] = RED
    used[red[0]] += 1
    for cell in chain:
      owner[cell] = CHAIN
      used[cell[0]] += 1
      cells += 1
  n = len(objs)
  for k in range(locked, n):
    red, chain = objs[k]
    if random.random() < 0.5:
      continue
    six = chain[0]
    del owner[red]
    del owner[six]
    if _domino_ok(six, red, owner, allow_touch, h, w):
      red, six = six, red
    owner[red] = RED
    owner[six] = CHAIN
    objs[k] = (red, [six])
  if max_len < 2:
    return objs
  order = list(range(n))
  random.shuffle(order)
  for k in order:
    if random.random() < 0.3:
      continue
    red, chain = objs[k]
    goal = _sample_length(max_len)
    while len(chain) < goal:
      end = chain[-1]
      prev = chain[-2] if len(chain) > 1 else red
      heading = (end[0] - prev[0], end[1] - prev[1])
      cands = []
      for dr, dc in DIRS:
        nb = (end[0] + dr, end[1] + dc)
        if not (0 <= nb[0] < h and 0 <= nb[1] < w) or nb in owner:
          continue
        if used[nb[0]] + 1 >= w:
          continue
        if any(m != end and m in owner for m in _neighbors(*nb)):
          continue
        cands.append(((dr, dc), nb))
      if not cands or not _majority_ok(h, w, n, cells + 1):
        break
      straight = [cd for cd in cands if cd[0] == heading]
      if straight and random.random() < 0.6:
        nb = straight[0][1]
      else:
        nb = random.choice(cands)[1]
      chain.append(nb)
      owner[nb] = CHAIN
      used[nb[0]] += 1
      cells += 1
  return objs


def _dense_objects(d, fw, n, touching_reds, max_len):
  """Build exactly n objects from a constructive pack (canonical coords)."""
  cands = [p for p in _mode_packs(d, fw, touching_reds) if len(p) >= n]
  if not cands:
    raise ValueError("num_objects exceeds the constructive capacity")
  pack = random.choice(cands)
  flip_r = random.random() < 0.5
  flip_c = random.random() < 0.5

  def tf(cell):
    i, j = cell
    return (d - 1 - i if flip_r else i, fw - 1 - j if flip_c else j)

  objs = [(tf(red), tf(six)) for red, six in pack]
  if touching_reds:
    index = {red: k for k, (red, _) in enumerate(objs)}
    pairs = []
    for k, (red, _) in enumerate(objs):
      for nb in _neighbors(*red):
        if index.get(nb, -1) > k:
          pairs.append((k, index[nb]))
    a, b = random.choice(pairs)
    rest = [k for k in range(len(objs)) if k not in (a, b)]
    chosen = [a, b] + random.sample(rest, n - 2)
    locked = 2
  else:
    chosen = random.sample(range(len(objs)), n)
    locked = 0
  base = [(objs[k][0], [objs[k][1]]) for k in chosen]
  rich = _embellish(d, fw, base, touching_reds, max_len, locked)
  fh = 2 * d + 1
  for cand in (rich, base):
    canon = [((d + 1 + red[0], red[1]), [(d + 1 + y, x) for y, x in chain])
             for red, chain in cand]
    if _scene_ok(_render(fh, fw, canon), fh):
      return canon
  raise ValueError("dense packing violated the scene invariants")


# Grown layout (canonical frame: chains in rows d+1..fh-1).


def _in_lower(cell, fh, fw):
  d = (fh - 1) // 2
  return d + 1 <= cell[0] <= fh - 1 and 0 <= cell[1] < fw


def _red_ok(cell, fh, fw, owner):
  if not _in_lower(cell, fh, fw) or cell in owner:
    return False
  for n in _neighbors(*cell):
    if owner.get(n) == CHAIN:
      return False
  return True


def _touches_red(cell, owner):
  return any(owner.get(n) == RED for n in _neighbors(*cell))


def _pick_red(fh, fw, owner, want_adjacent):
  """Pick a red cell; want_adjacent asks for one touching an existing red."""
  if want_adjacent:
    options = []
    for cell, kind in owner.items():
      if kind != RED:
        continue
      for n in _neighbors(*cell):
        if _red_ok(n, fh, fw, owner):
          options.append(n)
    if options:
      return random.choice(options)
    return None
  d = (fh - 1) // 2
  cell = (random.randint(d + 1, fh - 1), random.randint(0, fw - 1))
  if _red_ok(cell, fh, fw, owner):
    return cell
  return None


def _grow_path(fh, fw, owner, red, length):
  """Grow an induced path of 6s from red; returns [red, 6, 6, ...] or None."""
  path = [red]
  used = {red}
  direction = None
  for _ in range(length):
    cur = path[-1]
    cands = []
    for dr, dc in DIRS:
      n = (cur[0] + dr, cur[1] + dc)
      if not _in_lower(n, fh, fw) or n in used or n in owner:
        continue
      ok = True
      for m in _neighbors(*n):
        if m in owner or (m in used and m != cur):
          ok = False
          break
      if ok:
        cands.append(((dr, dc), n))
    if not cands:
      break
    straight = [cd for cd in cands if cd[0] == direction]
    if straight and random.random() < 0.6:
      direction, n = straight[0]
    else:
      direction, n = random.choice(cands)
    path.append(n)
    used.add(n)
  if len(path) < 2:
    return None
  return path


def _has_touching_reds(objects):
  reds = [red for red, _ in objects]
  for i in range(len(reds)):
    for j in range(i + 1, len(reds)):
      if _adjacent(reds[i], reds[j]):
        return True
  return False


def _grown_objects(fh, fw, target, touching_reds, max_len, attempts):
  """Randomly grown scene with exactly target objects, or None."""
  for _ in range(attempts):
    owner = {}
    objs = []
    for _ in range(30 * target + 30):
      if len(objs) >= target:
        break
      need_adj = bool(touching_reds) and bool(objs) and (
          not _has_touching_reds(objs))
      want_adj = need_adj or (bool(objs) and touching_reds is not False
                              and random.random() < 0.25)
      red = _pick_red(fh, fw, owner, want_adj)
      if red is None and want_adj and not need_adj:
        red = _pick_red(fh, fw, owner, False)
      if red is None:
        continue
      if touching_reds is False and _touches_red(red, owner):
        continue
      path = _grow_path(fh, fw, owner, red, _sample_length(max_len))
      if path is None:
        continue
      objs.append((path[0], path[1:]))
      owner[path[0]] = RED
      for cell in path[1:]:
        owner[cell] = CHAIN
    if len(objs) != target:
      continue
    if touching_reds and not _has_touching_reds(objs):
      continue
    if not _scene_ok(_render(fh, fw, objs), fh):
      continue
    return objs
  return None


# Rendering and frames.


def _render(fh, fw, objects):
  """Draw the input and output in the canonical frame (chains below)."""
  d = (fh - 1) // 2
  inp = common.grid(fw, fh, BG)
  out = common.grid(fw, fh, BG)
  for x in range(fw):
    inp[d][x] = DIV
    out[d][x] = DIV
  for (r, c), chain in objects:
    inp[r][c] = RED
    inp[2 * d - r][c] = GREY
    for (y, x) in chain:
      inp[y][x] = CHAIN
  for _, chain in objects:
    fr, fc = chain[-1]
    out[fr][fc] = RED
    out[2 * d - fr][fc] = GREY
  return {"input": inp, "output": out}


def _scene_ok(pair, fh):
  """No row but the divider lacks background, and 7 is the majority colour."""
  d = (fh - 1) // 2
  for g in (pair["input"], pair["output"]):
    for r, row in enumerate(g):
      if r != d and BG not in row:
        return False
    counts = {}
    for row in g:
      for v in row:
        counts[v] = counts.get(v, 0) + 1
    bg_count = counts.get(BG, 0)
    for colour, n in counts.items():
      if colour != BG and n >= bg_count:
        return False
  return True


def _transpose(g):
  return [list(row) for row in zip(*g)]


def _finish(pair, before, vertical):
  """Map the canonical frame to the final frame: flip rows, then transpose."""
  inp, out = pair["input"], pair["output"]
  if before:
    inp = [list(row) for row in inp[::-1]]
    out = [list(row) for row in out[::-1]]
  if vertical:
    inp = _transpose(inp)
    out = _transpose(out)
  return {"input": inp, "output": out}


def _to_frame(cell, fh, before, vertical):
  """Inverse of _finish for one final-grid (row, col) coordinate."""
  if (not isinstance(cell, (list, tuple)) or len(cell) != 2
      or not _is_int(cell[0]) or not _is_int(cell[1])):
    raise ValueError("object coordinates must be (int, int) pairs")
  r, c = cell
  if vertical:
    r, c = c, r
  if before:
    r = fh - 1 - r
  return (r, c)


def _is_induced_path(cells):
  """True if consecutive cells touch and no other pair of cells touches."""
  if len(set(cells)) != len(cells):
    return False
  for i in range(len(cells)):
    for j in range(i + 1, len(cells)):
      touch = _adjacent(cells[i], cells[j])
      if j == i + 1 and not touch:
        return False
      if j > i + 1 and touch:
        return False
  return True


def _fits(cells, owner):
  """A new red may touch reds only; a new 6 may touch no other object."""
  red = cells[0]
  if red in owner:
    return False
  for n in _neighbors(*red):
    if owner.get(n) == CHAIN:
      return False
  for cell in cells[1:]:
    if cell in owner:
      return False
    for n in _neighbors(*cell):
      if n in owner:
        return False
  return True


def _check_explicit(fh, fw, objects):
  """Raise ValueError if explicit objects break the scene invariants."""
  owner = {}
  for red, chain in objects:
    if not chain:
      raise ValueError("every red needs a chain of at least one 6")
    cells = [red] + chain
    for cell in cells:
      if not _in_lower(cell, fh, fw):
        raise ValueError("object cell outside the chain half")
    if not _is_induced_path(cells):
      raise ValueError("chain must be an induced path starting at its red")
    if not _fits(cells, owner):
      raise ValueError("objects overlap or chains touch another object")
    owner[cells[0]] = RED
    for cell in cells[1:]:
      owner[cell] = CHAIN


def _choose_size(span, length, n, touching_reds):
  """Pick (fh, fw) whose constructive capacity holds n; checked up front."""
  best = (span if span is not None else MAX_SPAN,
          length if length is not None else 30)
  if n > _capacity((best[0] - 1) // 2, best[1], touching_reds):
    raise ValueError("num_objects exceeds the constructive capacity")
  if span is not None and length is not None:
    return best
  for _ in range(40):
    fh = span if span is not None else 2 * random.randint(2, 14) + 1
    fw = length if length is not None else random.randint(5, 30)
    d = (fh - 1) // 2
    if d * fw < 2 * n:
      continue
    if n <= _capacity(d, fw, touching_reds):
      return fh, fw
  return best


def generate(height=None, width=None, num_objects=None, max_chain_length=None,
             touching_reds=None, orientation=None, chain_side=None,
             dense=None, objects=None):
  """Generate one input/output pair.

  Args:
    height: grid height. With a horizontal divider it must be odd (3..29) and
      the divider row is (height - 1) // 2. With a vertical divider it is the
      divider-parallel length (3..30, sampled 5..30). Sampled when None.
    width: grid width. With a horizontal divider it is 3..30 (sampled 5..30).
      With a vertical divider it must be odd (3..29).
    num_objects: exact number of red/chain objects (1..30). It must not
      exceed the constructive capacity of the grid (see the module
      docstring). The count is never reduced.
    max_chain_length: largest number of 6s in a chain (1..30, default 6).
    touching_reds: True forces at least one pair of 4-adjacent 2s. False
      forbids adjacent 2s. None lets them occur.
    orientation: None or 'horizontal' (as in all fixtures), or 'vertical'
      (synthetic extension: the whole scene is transposed).
    chain_side: None or 'after' (chains below or right of the divider, as in
      all fixtures), or 'before' (synthetic extension).
    dense: None chooses the layout engine automatically. True forces the
      dense packing engine (more objects, shorter chains).
    objects: explicit list of (red_cell, chain_cells) in final-grid
      (row, col) coordinates. chain_cells is the ordered, non-empty list of
      6-cells going away from the red, ending at the far end. height and
      width are required. max_chain_length, touching_reds and dense must be
      None.
  """
  if orientation is None or orientation == "horizontal":
    vertical = False
  elif orientation == "vertical":
    vertical = True
  else:
    raise ValueError("orientation must be None, 'horizontal' or 'vertical'")
  if chain_side is None or chain_side == "after":
    before = False
  elif chain_side == "before":
    before = True
  else:
    raise ValueError("chain_side must be None, 'after' or 'before'")
  if touching_reds is not None and not isinstance(touching_reds, bool):
    raise ValueError("touching_reds must be None, True or False")
  if dense is not None and dense is not True:
    raise ValueError("dense must be None or True")

  height = _int_arg("height", height, 3, 30)
  width = _int_arg("width", width, 3, 30)
  num_objects = _int_arg("num_objects", num_objects, 1, MAX_OBJECTS)
  max_chain_length = _int_arg("max_chain_length", max_chain_length, 1, 30)

  span = width if vertical else height
  length = height if vertical else width
  if span is not None and (span % 2 != 1 or not MIN_SPAN <= span <= MAX_SPAN):
    raise ValueError("divider-crossing side must be odd and in 3..29")

  if objects is not None:
    if height is None or width is None:
      raise ValueError("explicit objects require height and width")
    if (max_chain_length is not None or touching_reds is not None
        or dense is not None):
      raise ValueError("sampling controls do not apply to explicit objects")
    if not isinstance(objects, (list, tuple)):
      raise ValueError("objects must be a list of (red_cell, chain_cells)")
    if not 1 <= len(objects) <= MAX_OBJECTS:
      raise ValueError("objects must hold 1..%d objects" % MAX_OBJECTS)
    if num_objects is not None and num_objects != len(objects):
      raise ValueError("num_objects does not match len(objects)")
    objs = []
    for item in objects:
      if not isinstance(item, (list, tuple)) or len(item) != 2:
        raise ValueError("each object must be (red_cell, chain_cells)")
      red, chain = item
      if not isinstance(chain, (list, tuple)):
        raise ValueError("chain_cells must be a list of cells")
      red = _to_frame(red, span, before, vertical)
      chain = [_to_frame(x, span, before, vertical) for x in chain]
      objs.append((red, chain))
    _check_explicit(span, length, objs)
    pair = _render(span, length, objs)
    if not _scene_ok(pair, span):
      raise ValueError("scene has a background-free row or 7 is not dominant")
    return _finish(pair, before, vertical)

  if touching_reds and num_objects is not None and num_objects < 2:
    raise ValueError("touching_reds=True needs at least two objects")
  max_len = max_chain_length if max_chain_length is not None else 6
  if span is not None and length is not None:
    minimum = 2 if touching_reds else 1
    if _capacity((span - 1) // 2, length, touching_reds) < minimum:
      raise ValueError("canvas has no feasible objects for the touching mode")

  if num_objects is not None:
    fh, fw = _choose_size(span, length, num_objects, touching_reds)
    d = (fh - 1) // 2
    target = num_objects
    cap = _capacity(d, fw, touching_reds)
    use_dense = bool(dense) or 2 * target > cap
  else:
    fh = span if span is not None else 2 * random.randint(2, 14) + 1
    fw = length if length is not None else random.randint(5, 30)
    d = (fh - 1) // 2
    use_dense = bool(dense) or random.random() < DENSE_SHARE
    if use_dense:
      cap = _capacity(d, fw, touching_reds)
      lo = 2 if touching_reds else 1
      target = random.randint(max(lo, (cap + 1) // 2), cap)
    else:
      cap = None
      target = random.randint(1, max(1, min(8, (d * fw) // 6)))
      if touching_reds:
        target = max(2, target)

  objs = None
  if not use_dense:
    objs = _grown_objects(fh, fw, target, touching_reds, max_len, 25)
    if objs is None and cap is None:
      # Only a sampled (never a requested) count may be bounded here.
      cap = _capacity(d, fw, touching_reds)
      target = min(target, cap)
  if objs is None:
    objs = _dense_objects(d, fw, target, touching_reds, max_len)
  pair = _render(fh, fw, objs)
  return _finish(pair, before, vertical)


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(height=9, width=9, objects=[
          ((5, 5), [(6, 5), (7, 5)]),
          ((6, 8), [(6, 7)]),
          ((8, 2), [(8, 3)]),
      ]),
      generate(height=7, width=7, objects=[
          ((5, 1), [(5, 2)]),
          ((6, 4), [(5, 4)]),
      ]),
      generate(height=9, width=9, objects=[
          ((6, 2), [(7, 2)]),
          ((6, 3), [(5, 3)]),
          ((8, 0), [(8, 1)]),
          ((8, 7), [(7, 7), (6, 7)]),
      ]),
  ]
  test = [
      generate(height=11, width=11, objects=[
          ((6, 3), [(7, 3)]),
          ((6, 10), [(6, 9), (6, 8)]),
          ((8, 7), [(8, 8), (8, 9)]),
          ((10, 7), [(10, 6), (10, 5), (10, 4), (10, 3)]),
          ((10, 9), [(10, 10)]),
      ]),
  ]
  return {"train": train, "test": test}
