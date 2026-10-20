"""Generator for ARC task fea12743.

Rule
----
One-cell background-0 gutters cut the grid into a lattice of 4x4 tiles. Tile
origins are at row/column 1 + 5k. Each tile holds a pattern of colour-2
cells. The tile with the unique largest number of filled cells is recoloured
3. The other tiles whose cells all lie inside the max tile are candidates.
The first candidate pair, in reading-order combinations, whose union rebuilds
the max tile exactly is recoloured 8. Every other tile keeps colour 2.

Scope
-----
* Tile size 4 and gutter width 1 are fixed. The canonical lattice is 3x2
  tiles (a 16x11 grid). When no layout is requested it is used 60% of the
  time. Other lattices with at least four tiles, up to 5x5 tiles (26x26),
  are synthetic extensions. The rule is defined for any such lattice.
* Background 0 stays the strict majority colour, as in every canonical
  scene. This is enforced with an ink budget: 2 * total ink < grid area.
* The max tile has 6..15 cells. It is a 4-connected blob, an unconstrained
  scatter, or a perturbed frame/ring template under a random square
  symmetry. The templates include the diagonally joined ring of the test.
* The max tile is split into two strictly smaller parts, which may overlap.
  In equal-size scenes the parts and every distractor share one cell count,
  so cell count cannot identify the 8-tiles.
* Family scenes imitate canonical train 1 and the test. Sizes are equal, and
  the parts are within 1-2 cells of the max. Every distractor is a perturbed
  copy of the max tile: a near-complete subset, or a copy with 1-2 cells
  moved outside the max.
* Other distractor kinds:
  - competing subsets of the max tile;
  - forced near-miss subsets;
  - near-miss copies that have outside cells;
  - random blobs or scatters with an outside cell;
  - duplicated distractors (a synthetic extension).
* Rejection rules:
  - A candidate that would complete a new qualifying pair is rejected.
  - A random scene is rejected if a non-max tile equals the union of two of
    its strict sub-tiles. Such a scene would allow a competing 'union' reading.
* Tie scenes need at least five tiles. One part is duplicated, as in
  canonical pair 2. Exactly two pairs then qualify, and the earlier copy in
  reading order becomes 8. Ties between disjoint pairs are not generated.
* Colours 0 / 2 / 3 / 8 are intrinsic and never changed.

Copyright 2026 Ritwika Kancharla
Licensed under the Apache License, Version 2.0.
"""

import itertools
import random

import common

TILE = 4
STEP = 5
MAX_SIDE_TILES = 5  # 5 * STEP + 1 = 26 <= 30
BACKGROUND = 0
INK = 2
MAX_COLOR = 3
PART_COLOR = 8
ROLE_COLOR = {'max': MAX_COLOR, 'part': PART_COLOR, 'other': INK}
ROLE_NAMES = ('max', 'part', 'other')
ALL_CELLS = list(range(TILE * TILE))
MIN_TILES = 4
MIN_TIE_TILES = 5
MIN_MAX_SIZE = 6
MAX_MAX_SIZE = 15
SHAPES = ('blob', 'scatter', 'ring')
SHAPE_WEIGHTS = (0.4, 0.25, 0.35)
EXTRA_LAYOUTS = [(1, 4), (4, 1), (1, 5), (5, 1), (2, 2), (2, 3), (3, 3),
                 (4, 2), (2, 4), (4, 3), (3, 4), (4, 4), (5, 2), (2, 5),
                 (5, 3), (3, 5), (5, 4), (4, 5), (5, 5)]
TEMPLATES = [
    ('####', '#..#', '#..#', '####'),  # square frame
    ('.##.', '#..#', '#..#', '.##.'),  # rounded ring (diagonal joins)
    ('.##.', '####', '####', '.##.'),  # rounded disc
    ('####', '#...', '#...', '####'),  # C shape
    ('####', '.#.#', '.#.#', '####'),  # bars
    ('#..#', '####', '####', '#..#'),  # H-like
]


def _check_int(name, v):
  """Rejects non-int (including bool and float) optional integer controls."""
  if v is not None and (isinstance(v, bool) or not isinstance(v, int)):
    raise ValueError('%s must be an int or None' % name)


def _check_bool(name, v):
  """Rejects optional boolean controls that are not real bools."""
  if v is not None and not isinstance(v, bool):
    raise ValueError('%s must be True, False or None' % name)


def _ink_budget(tile_rows, tile_cols):
  """Largest ink count that keeps background 0 the strict majority colour."""
  total = (tile_rows * STEP + 1) * (tile_cols * STEP + 1)
  return (total - 1) // 2


def _parse_tile(tile):
  """Converts 4 strings ('#' filled, '.' empty) or a 4x4 0/1 list to cells."""
  if len(tile) != TILE or any(len(row) != TILE for row in tile):
    raise ValueError('each tile must be 4x4')
  cells = set()
  for r in range(TILE):
    for c in range(TILE):
      v = tile[r][c]
      if isinstance(v, str):
        if v not in ('#', '.'):
          raise ValueError('tile strings may only contain # and .')
        filled = v == '#'
      elif isinstance(v, int) and not isinstance(v, bool) and v in (0, 1):
        filled = v == 1
      else:
        raise ValueError('tile list entries must be the ints 0 or 1')
      if filled:
        cells.add(r * TILE + c)
  return frozenset(cells)


def _neighbors(cell):
  r, c = divmod(cell, TILE)
  out = []
  if r > 0:
    out.append(cell - TILE)
  if r < TILE - 1:
    out.append(cell + TILE)
  if c > 0:
    out.append(cell - 1)
  if c < TILE - 1:
    out.append(cell + 1)
  return out


def _random_blob(size):
  """Random 4-connected set of `size` cells inside the 4x4 tile."""
  cells = {random.choice(ALL_CELLS)}
  while len(cells) < size:
    frontier = sorted({n for c in cells for n in _neighbors(c)
                       if n not in cells})
    cells.add(random.choice(frontier))
  return frozenset(cells)


def _d4(cells, k):
  """Applies one of the 8 square symmetries (index k) to a cell set."""
  out = set()
  for cell in cells:
    r, c = divmod(cell, TILE)
    if k & 4:
      c = TILE - 1 - c
    for _ in range(k & 3):
      r, c = c, TILE - 1 - r
    out.add(r * TILE + c)
  return frozenset(out)


def _make_max(shape, size):
  """Samples the max tile from the requested shape source."""
  if shape == 'blob':
    return _random_blob(size or random.randint(7, MAX_MAX_SIZE))
  if shape == 'scatter':
    return frozenset(random.sample(ALL_CELLS,
                                   size or random.randint(7, MAX_MAX_SIZE)))
  cells = set(_d4(_parse_tile(random.choice(TEMPLATES)),
                  random.randint(0, 7)))
  if size is None:
    size = min(MAX_MAX_SIZE, max(7, len(cells) + random.randint(-2, 2)))
  while len(cells) < size:
    cells.add(random.choice([c for c in ALL_CELLS if c not in cells]))
  while len(cells) > size:
    cells.remove(random.choice(sorted(cells)))
  return frozenset(cells)


def _split_max(m):
  """Two parts, each a strict subset of m, whose union is exactly m."""
  cells = sorted(m)
  random.shuffle(cells)
  cut = random.randint(2, len(cells) - 2)
  left_core, right_core = cells[:cut], cells[cut:]
  left = set(left_core)
  right = set(right_core)
  # Optional overlap; neither part ever absorbs the other's whole core.
  right |= set(random.sample(left_core, random.randint(0, len(left_core) - 1)))
  left |= set(random.sample(right_core, random.randint(0, len(right_core) - 1)))
  return frozenset(left), frozenset(right)


def _split_equal(m, s):
  """Two parts of exactly s cells each (|m|/2 <= s < |m|), union m."""
  cells = sorted(m)
  random.shuffle(cells)
  overlap = 2 * s - len(m)
  only = len(m) - s
  shared = cells[:overlap]
  left = shared + cells[overlap:overlap + only]
  right = shared + cells[overlap + only:]
  return frozenset(left), frozenset(right)


def _subset_distractor(m, size):
  """Competing candidate: a strict, non-empty subset of the max tile."""
  if size is None:
    size = random.randint(2, len(m) - 1)
  return frozenset(random.sample(sorted(m), size))


def _near_miss_subset(m, part, size):
  """Subset of m whose union with `part` misses 1-2 cells of m."""
  rest = sorted(m - part)
  if not rest:
    return None
  k = random.randint(1, min(2, len(rest)))
  kept = random.sample(rest, len(rest) - k)
  part_cells = sorted(part)
  if size is None:
    t = random.randint(0 if kept else 1, len(part_cells))
  else:
    t = size - len(kept)
    if t < 0 or t > len(part_cells):
      return None
  d = frozenset(kept + random.sample(part_cells, t))
  return d if d else None


def _outside_distractor(m, size):
  """A tile smaller than m with at least one cell outside m."""
  outside = [c for c in ALL_CELLS if c not in m]
  if size is not None:
    if random.random() < 0.4:
      for _ in range(20):
        blob = _random_blob(size)
        if blob - m:
          return blob
    j = random.randint(1, min(size, len(outside), 3))
    inside = random.sample(sorted(m), size - j)
    return frozenset(inside + random.sample(outside, j))
  kind = random.random()
  if kind < 0.4:
    # Near miss: drop k cells of m and add j < k outside cells.
    k = random.randint(2, min(5, len(m) - 1))
    j = random.randint(1, min(k - 1, len(outside)))
    keep = random.sample(sorted(m), len(m) - k)
    return frozenset(keep + random.sample(outside, j))
  size = random.randint(2, len(m) - 1)
  if kind < 0.7:
    for _ in range(20):
      blob = _random_blob(size)
      if blob - m:
        return blob
  seed = random.choice(outside)
  pool = [c for c in ALL_CELLS if c != seed]
  return frozenset([seed] + random.sample(pool, size - 1))


def _family_distractor(m, size, allow_subset):
  """Perturbed copy of m with `size` cells (canonical train1/test style).

  Either a near-complete subset of m, or a copy of m with 1-2 cells moved
  outside it. The latter is never a subset of m.
  """
  if allow_subset and random.random() < 0.3:
    return frozenset(random.sample(sorted(m), size))
  outside = [c for c in ALL_CELLS if c not in m]
  j = random.randint(1, min(2, len(outside), size))
  inside = random.sample(sorted(m), size - j)
  return frozenset(inside + random.sample(outside, j))


def _completes(cand, subset_tiles, m):
  """True if cand would form a new pair whose union is m."""
  return cand <= m and any((cand | t) == m for t in subset_tiles)


def _has_near_miss(patterns, roles, m):
  """True if a genuine distractor (not a part copy) nearly completes m."""
  parts = [p for p, r in zip(patterns, roles) if r == 'part']
  for p, r in zip(patterns, roles):
    if r == 'other' and p <= m and p not in parts:
      for q in parts:
        if 1 <= len(m - (p | q)) <= 2:
          return True
  return False


def _union_ambiguous(patterns, mi):
  """True if a non-max tile equals the union of two of its strict sub-tiles."""
  n = len(patterns)
  for t in range(n):
    if t == mi:
      continue
    target = patterns[t]
    inside = [i for i in range(n)
              if i != t and i != mi and patterns[i] < target]
    for a, b in itertools.combinations(inside, 2):
      if (patterns[a] | patterns[b]) == target:
        return True
  return False


def _scene_ok(patterns, roles, budget, tie=None, equal=False, near=False,
              allow_empty=False):
  """Checks the roles agree with the rule and the scene is well posed."""
  if not allow_empty and any(len(p) == 0 for p in patterns):
    return False
  if sum(len(p) for p in patterns) > budget:
    return False  # background 0 must remain the strict majority colour
  mi = roles.index('max')
  m = patterns[mi]
  sizes = [len(p) for p in patterns]
  if sizes.count(len(m)) != 1 or max(sizes) != len(m):
    return False
  subs = [i for i, p in enumerate(patterns) if i != mi and p <= m]
  pairs = [(a, b) for a, b in itertools.combinations(subs, 2)
           if (patterns[a] | patterns[b]) == m]
  wanted = tuple(i for i, r in enumerate(roles) if r == 'part')
  if not pairs or pairs[0] != wanted:
    return False
  if tie is not None and len(pairs) != (2 if tie else 1):
    return False
  if equal and len({len(p) for i, p in enumerate(patterns) if i != mi}) != 1:
    return False
  if near and not _has_near_miss(patterns, roles, m):
    return False
  return True


def _sample_scene(n_tiles, budget, tie, equal, near, shape, max_size, family):
  """Samples tile patterns and roles for `n_tiles` tiles."""
  for _ in range(200):
    m = _make_max(shape, max_size)
    if equal:
      s_lo = (len(m) + 1) // 2
      if family:
        s_lo = max(s_lo, len(m) - 2)
      s_hi = min(len(m) - 1, (budget - len(m)) // (n_tiles - 1))
      if s_hi < s_lo:
        continue
      s = random.randint(s_lo, s_hi)
      left, right = _split_equal(m, s)
    else:
      s = None
      left, right = _split_max(m)
    if random.random() < 0.5:
      left, right = right, left
    items = [(m, 'max'), (left, 'partA'), (right, 'partB')]
    if tie:
      items.append((left, 'copyA'))
    subset_tiles = [left, right]
    others = []
    failed = False
    for idx in range(n_tiles - len(items)):
      d = None
      if near and idx == 0:
        for _ in range(30):
          cand = _near_miss_subset(m, random.choice((left, right)), s)
          if cand is not None and not _completes(cand, subset_tiles, m):
            d = cand
            break
        if d is None:
          failed = True
          break
      elif others and random.random() < 0.2:
        d = random.choice(others)  # synthetic duplicated distractor
      else:
        for _ in range(30):
          if family:
            cand = _family_distractor(m, s, True)
          elif random.random() < 0.45:
            cand = _subset_distractor(m, s)
          else:
            cand = _outside_distractor(m, s)
          if not _completes(cand, subset_tiles, m):
            d = cand
            break
        if d is None:
          # Never a subset of m, so it can never complete a pair.
          if family:
            d = _family_distractor(m, s, False)
          else:
            d = _outside_distractor(m, s)
      others.append(d)
      if d <= m:
        subset_tiles.append(d)
      items.append((d, 'other'))
    if failed:
      continue
    random.shuffle(items)
    patterns, roles = [], []
    seen_a = False
    for pattern, tag in items:
      patterns.append(pattern)
      if tag in ('partA', 'copyA'):
        # Reading-order tie-break: the earlier copy of the part wins.
        roles.append('other' if seen_a else 'part')
        seen_a = True
      elif tag == 'partB':
        roles.append('part')
      else:
        roles.append(tag)
    if (_scene_ok(patterns, roles, budget, tie, equal, near) and
        not _union_ambiguous(patterns, roles.index('max'))):
      return patterns, roles
  raise RuntimeError('could not sample a valid fea12743 scene')


def _choose_layout(tile_rows, tile_cols, min_tiles):
  """Fills in missing lattice dimensions, honouring given ones."""
  for name, v in (('tile_rows', tile_rows), ('tile_cols', tile_cols)):
    _check_int(name, v)
    if v is not None and not 1 <= v <= MAX_SIDE_TILES:
      raise ValueError('tile_rows/tile_cols must be in 1..%d' % MAX_SIDE_TILES)
  if tile_rows is None and tile_cols is None:
    if min_tiles <= 6 and random.random() < 0.6:
      return 3, 2
    options = [lc for lc in EXTRA_LAYOUTS if lc[0] * lc[1] >= min_tiles]
    return random.choice(options)
  if tile_rows is None:
    options = [r for r in range(1, MAX_SIDE_TILES + 1)
               if r * tile_cols >= min_tiles]
    if not options:
      raise ValueError('tile_cols too small for the requested scene')
    return random.choice(options), tile_cols
  if tile_cols is None:
    options = [c for c in range(1, MAX_SIDE_TILES + 1)
               if tile_rows * c >= min_tiles]
    if not options:
      raise ValueError('tile_rows too small for the requested scene')
    return tile_rows, random.choice(options)
  if tile_rows * tile_cols < min_tiles:
    raise ValueError('lattice needs at least %d tiles' % min_tiles)
  return tile_rows, tile_cols


def generate(tiles=None, roles=None, tile_rows=None, tile_cols=None,
             tie=None, equal_sizes=None, max_size=None, max_shape=None,
             near_miss=None, family=None):
  """Returns {'input': grid, 'output': grid} for one scene.

  Args:
    tiles: optional list of tile patterns in reading order, used to replay
      fixtures. Each tile is four strings ('#' = filled, '.' = empty) or a
      4x4 list of the ints 0/1. Requires `roles`, `tile_rows` and
      `tile_cols`. It cannot be combined with any random-scene option.
      Empty tiles are allowed in replay only.
    roles: list of role strings, one per tile: 'max', 'part' or 'other'.
      Exactly one 'max' and two 'part' are required. Only valid with
      `tiles`. The roles are checked against the rule and the background
      majority invariant; inconsistent roles raise ValueError.
    tile_rows: int number of tile rows, 1..5. Default: sampled, usually 3.
    tile_cols: int number of tile columns, 1..5. Default: sampled, usually
      2. Random scenes need at least 4 tiles, or at least 5 when tie=True.
    tie: bool. If True, one part tile is duplicated, so exactly two pairs
      qualify and the reading-order tie-break decides. If False, exactly one
      pair qualifies. Default: sampled, 20% when there are at least 5 tiles.
    equal_sizes: bool. If True, the two parts and all distractors have the
      same cell count (clamped so background 0 stays the majority colour).
      If False, sizes are drawn independently and may coincide. Default:
      True for family scenes, otherwise sampled at 40%.
    max_size: int cell count of the max tile, 6..15. Default: sampled.
    max_shape: 'blob' (4-connected), 'scatter' (any cells) or 'ring'
      (perturbed frame/ring template). Default: sampled.
    near_miss: bool. If True, at least one genuine distractor is a subset of
      the max tile whose union with one part misses only 1-2 max cells. If
      False, none is forced, though one may still arise. Default: sampled,
      60%.
    family: bool. If True, sizes are equal, the parts lie within 1-2 cells
      of the max size, and every distractor is a perturbed copy of the max
      tile (canonical train1/test style). Incompatible with
      equal_sizes=False. Default: sampled at 35% unless equal_sizes=False.
  """
  scene_opts = (tie, equal_sizes, max_size, max_shape, near_miss, family)
  if tiles is not None:
    if roles is None or tile_rows is None or tile_cols is None:
      raise ValueError('tiles requires roles, tile_rows and tile_cols')
    if any(v is not None for v in scene_opts):
      raise ValueError('random scene options cannot be combined with tiles')
    _choose_layout(tile_rows, tile_cols, 3)
    patterns = [_parse_tile(t) for t in tiles]
    roles = list(roles)
    n = tile_rows * tile_cols
    if len(patterns) != n or len(roles) != n:
      raise ValueError('tiles/roles must match tile_rows * tile_cols')
    if any(not isinstance(r, str) or r not in ROLE_NAMES for r in roles):
      raise ValueError('unknown role')
    if roles.count('max') != 1 or roles.count('part') != 2:
      raise ValueError('need exactly one max and two part tiles')
    if not _scene_ok(patterns, roles, _ink_budget(tile_rows, tile_cols),
                     allow_empty=True):
      raise ValueError('roles are inconsistent with the task rule')
  else:
    if roles is not None:
      raise ValueError('roles is only valid together with tiles')
    for name, v in (('tie', tie), ('equal_sizes', equal_sizes),
                    ('near_miss', near_miss), ('family', family)):
      _check_bool(name, v)
    _check_int('max_size', max_size)
    if max_size is not None and not MIN_MAX_SIZE <= max_size <= MAX_MAX_SIZE:
      raise ValueError('max_size must be in %d..%d' % (MIN_MAX_SIZE,
                                                       MAX_MAX_SIZE))
    if max_shape is not None and (not isinstance(max_shape, str) or
                                  max_shape not in SHAPES):
      raise ValueError('max_shape must be one of %s' % (SHAPES,))
    if family and equal_sizes is False:
      raise ValueError('family scenes require equal_sizes')
    tile_rows, tile_cols = _choose_layout(
        tile_rows, tile_cols, MIN_TIE_TILES if tie else MIN_TILES)
    n = tile_rows * tile_cols
    if tie is None:
      tie = n >= MIN_TIE_TILES and random.random() < 0.2
    if family is None:
      family = equal_sizes is not False and random.random() < 0.35
    if equal_sizes is None:
      equal_sizes = family or random.random() < 0.4
    if near_miss is None:
      near_miss = random.random() < 0.6
    if max_shape is None:
      max_shape = random.choices(SHAPES, weights=SHAPE_WEIGHTS)[0]
    patterns, roles = _sample_scene(n, _ink_budget(tile_rows, tile_cols),
                                    tie, equal_sizes, near_miss, max_shape,
                                    max_size, family)

  height = tile_rows * STEP + 1
  width = tile_cols * STEP + 1
  grid = common.grid(width, height, BACKGROUND)
  output = common.grid(width, height, BACKGROUND)
  origins = [(1 + ty * STEP, 1 + tx * STEP)
             for ty in range(tile_rows) for tx in range(tile_cols)]
  for (y0, x0), cells, role in zip(origins, patterns, roles):
    color = ROLE_COLOR[role]
    for cell in cells:
      r, c = divmod(cell, TILE)
      grid[y0 + r][x0 + c] = INK
      output[y0 + r][x0 + c] = color
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the canonical train/test pairs through explicit calls."""
  train = [
      generate(
          tiles=[['####', '#.##', '#..#', '####'],
                 ['####', '#..#', '#.##', '####'],
                 ['####', '#..#', '##.#', '####'],
                 ['####', '#.##', '##.#', '####'],
                 ['####', '##.#', '#..#', '####'],
                 ['####', '#..#', '#.##', '####']],
          roles=['part', 'other', 'part', 'max', 'other', 'other'],
          tile_rows=3, tile_cols=2),
      generate(
          tiles=[['####', '#...', '#...', '####'],
                 ['####', '.#..', '.#..', '####'],
                 ['####', '...#', '...#', '####'],
                 ['####', '..#.', '..#.', '####'],
                 ['####', '.#..', '.#..', '####'],
                 ['####', '.#.#', '.#.#', '####']],
          roles=['other', 'part', 'part', 'other', 'other', 'max'],
          tile_rows=3, tile_cols=2),
      generate(
          tiles=[['.##.', '####', '#.##', '.##.'],
                 ['.##.', '####', '#..#', '....'],
                 ['.##.', '...#', '.###', '.##.'],
                 ['.##.', '..##', '..##', '.##.'],
                 ['.##.', '#...', '###.', '.##.'],
                 ['....', '##.#', '##.#', '.##.']],
          roles=['max', 'part', 'other', 'part', 'other', 'other'],
          tile_rows=3, tile_cols=2),
  ]
  test = [
      generate(
          tiles=[['.##.', '#...', '#..#', '..##'],
                 ['.##.', '...#', '#..#', '##..'],
                 ['##..', '#..#', '...#', '.##.'],
                 ['..##', '#..#', '#...', '.##.'],
                 ['####', '#..#', '#..#', '.##.'],
                 ['.##.', '#...', '#..#', '..##']],
          roles=['other', 'other', 'part', 'part', 'max', 'other'],
          tile_rows=3, tile_cols=2),
  ]
  return {'train': train, 'test': test}
