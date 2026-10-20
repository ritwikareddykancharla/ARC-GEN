"""ARC task 4ff4c9da: copy an 8-template onto same-coloured objects of the same shape.

Rule:
  The input is a square plaid grid that is symmetric about its main diagonal.
  Each row/column index has a layer type. Cell (y, x) shows the colour of
  max(type[y], type[x]). The top layer forms single-width separator lines that
  cut the grid into small blocks. Inside the blocks, cells of a middle colour
  form small objects (bars, L, T, plus and cross shapes). Some blocks may hold
  extra painted motif tiles, like the diamond tiles of the third training pair.
  One or more whole objects of a hidden colour have been repainted 8; these are
  the templates. The output repaints 8 every object (8-connected component) of
  the template's hidden colour whose shape matches the template exactly, with
  the same orientation. Same-shaped objects of other colours are left alone.
  So are differently shaped objects or transposed objects of the hidden colour.

Scope:
  Random scenes are square grids of side 12..30 by default (10..30 on request).
  Sizes outside the fixture range 17..27 are synthetic extensions of the same
  plaid construction. Colours are 0/1/2 and the fixed marker is 8. Layer
  schemes are [0,a,b] (separators b, objects a) or [0,a,b,a] (weak a, objects
  b, separators a), with {a, b} = {1, 2}. A caller may pass any palette of
  length 3 or 4 that follows the same layer convention. Blocks are 1..3 wide.
  Optional random motif tiles are painted into off-diagonal blocks and
  mirrored by transpose. There are 1..3 templates, each of a distinct shape of
  2..6 cells that occurs at least twice. Every scene also has at least one
  hidden-colour object of a non-template shape. Mirror recovery scenes leave
  transposed template cells visible. Clean-line recovery scenes hide at least
  one mirror cell and require redundant clean rows/columns to recover it.
  The latter omit motif patches and are sampled in one quarter of scenes.

Copyright 2026 Ritwika Kancharla
Licensed under the Apache License, Version 2.0.
"""

import random

import common

MARK = 8
_MIN_SIZE, _MAX_SIZE = 10, 30


def _components(grid, color):
  """8-connected components of `color`, each a list of (y, x) cells."""
  h, w = len(grid), len(grid[0])
  seen = [[False] * w for _ in range(h)]
  comps = []
  for y in range(h):
    for x in range(w):
      if grid[y][x] != color or seen[y][x]:
        continue
      seen[y][x] = True
      stack, cells = [(y, x)], []
      while stack:
        cy, cx = stack.pop()
        cells.append((cy, cx))
        for dy in (-1, 0, 1):
          for dx in (-1, 0, 1):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx]:
              if grid[ny][nx] == color:
                seen[ny][nx] = True
                stack.append((ny, nx))
      comps.append(cells)
  return comps


def _shape(cells):
  y0 = min(y for y, _ in cells)
  x0 = min(x for _, x in cells)
  return tuple(sorted((y - y0, x - x0) for y, x in cells))


def _plaid(types, palette, patches):
  """Symmetric plaid grid with transpose-mirrored patch tiles."""
  n = len(types)
  g = common.grid(n, n, 0)
  for y in range(n):
    for x in range(n):
      g[y][x] = palette[max(types[y], types[x])]
  for top, left, tile in patches or []:
    for r in range(len(tile)):
      for c in range(len(tile[0])):
        g[top + r][left + c] = tile[r][c]
        g[left + c][top + r] = tile[r][c]
  return g


def _blocks(types, sep):
  runs, i, n = [], 0, len(types)
  while i < n:
    if types[i] == sep:
      i += 1
      continue
    j = i
    while j < n and types[j] != sep:
      j += 1
    runs.append((i, j - i))
    i = j
  return runs


def _hidden_layer(palette):
  """Layer index of the object colour for a random-scene palette."""
  if len(palette) == 3:
    return 1
  if len(palette) == 4:
    return 2
  raise ValueError('random scenes need a palette of length 3 or 4')


def _check_random_palette(palette):
  for c in palette:
    if not isinstance(c, int) or not 0 <= c <= 9 or c == MARK:
      raise ValueError('palette colours must be 0..9 and not the marker 8')
  hidden = _hidden_layer(palette)
  color = palette[hidden]
  others = [c for i, c in enumerate(palette) if i != hidden]
  if color in others:
    raise ValueError('object colour must differ from every other layer colour')


def _random_types(num_layers, target):
  sep = num_layers - 1
  types = []
  while len(types) < target:
    size = min(random.choice([1, 2, 2, 3, 3]), target - len(types))
    for _ in range(size):
      if num_layers == 3:
        types.append(random.choice([0, 1]))
      else:
        types.append(random.choices([0, 1, 2], [3, 2, 3])[0])
    if len(types) < target:
      types.append(sep)
  return types


def _random_patches(types, palette, color):
  """Paint one random motif tile into 2-3 off-diagonal blocks."""
  runs = _blocks(types, len(palette) - 1)
  lens = sorted(set(l for _, l in runs))
  options = [(h, w) for h in lens for w in lens if h * w >= 3]
  if not options:
    return [], None
  h, w = random.choice(options)
  pairs = [(i, j) for i in range(len(runs)) for j in range(len(runs))
           if i != j and runs[i][1] == h and runs[j][1] == w]
  random.shuffle(pairs)
  want = random.randint(2, 3)
  used, chosen = set(), []
  for i, j in pairs:
    if (i, j) in used or (j, i) in used:
      continue
    chosen.append((i, j))
    used.add((i, j))
    used.add((j, i))
    if len(chosen) == want:
      break
  if len(chosen) < 2:
    return [], None
  size = random.randint(2, min(5, h * w - 1))
  cells = {(random.randrange(h), random.randrange(w))}
  for _ in range(200):
    if len(cells) >= size:
      break
    y, x = random.choice(sorted(cells))
    ny, nx = y + random.randint(-1, 1), x + random.randint(-1, 1)
    if 0 <= ny < h and 0 <= nx < w:
      cells.add((ny, nx))
  if len(cells) < 2:
    return [], None
  others = [c for c in sorted(set(palette)) if c != color]
  tile = [[color if (r, c) in cells else random.choice(others)
           for c in range(w)] for r in range(h)]
  patches = [(runs[i][0], runs[j][0], tile) for i, j in chosen]
  return patches, _shape(list(cells))


def _clean_recoverable(base, masked):
  """Require unambiguous clean-line evidence for every hidden mirror cell."""
  n = len(base)
  rows = [y for y in range(n) if all((y, x) not in masked for x in range(n))]
  cols = [x for x in range(n) if all((y, x) not in masked for y in range(n))]
  needed = 0
  for y, x in masked:
    if (x, y) not in masked:
      continue
    needed += 1
    matches = [base[z][x] for z in rows
               if all((y, j) in masked or base[z][j] == base[y][j]
                      for j in range(n))]
    if not matches:
      matches = [base[y][z] for z in cols
                 if all((i, x) in masked or base[i][z] == base[i][x]
                        for i in range(n))]
    if not matches or set(matches) != {base[y][x]}:
      return False
  return needed > 0


def _random_scene(size, palette, num_templates, recovery):
  for _ in range(500):
    if palette is None:
      a, b = random.sample([1, 2], 2)
      pal = [0, a, b] if random.random() < 0.5 else [0, a, b, a]
    else:
      pal = list(palette)
    color = pal[_hidden_layer(pal)]
    n = size if size is not None else random.randint(12, _MAX_SIZE)
    types = _random_types(len(pal), n)
    patches, motif = [], None
    if recovery == "mirror" and random.random() < 0.35:
      patches, motif = _random_patches(types, pal, color)
    grid = _plaid(types, pal, patches)
    groups = {}
    for cells in _components(grid, color):
      groups.setdefault(_shape(cells), []).append(cells)
    eligible = [k for k, v in groups.items()
                if len(v) >= 2 and 2 <= len(k) <= 6]
    if num_templates is None:
      want = min(random.choice([1, 1, 2, 2, 3]), len(eligible))
    else:
      want = num_templates
    if want < 1 or len(eligible) < want:
      continue
    random.shuffle(eligible)
    if motif in eligible and random.random() < 0.75:
      eligible.remove(motif)
      eligible.insert(0, motif)
    chosen = eligible[:want]
    distractors = sum(len(v) for k, v in groups.items() if k not in chosen)
    if distractors < 1:
      continue
    tcells, anchors, ok = set(), [], True
    for key in chosen:
      cands = groups[key][:]
      random.shuffle(cands)
      if recovery == "clean":
        cands.sort(key=lambda cells: not any((x, y) in cells for y, x in cells))
      picked = None
      for cells in cands:
        new = tcells | set(cells)
        if recovery == "clean" or all((x, y) not in new for (y, x) in new):
          picked = cells
          break
      if picked is None:
        ok = False
        break
      tcells |= set(picked)
      anchors.append(min(picked))
    if ok and (recovery != "clean" or _clean_recoverable(grid, tcells)):
      return types, pal, patches, anchors
  raise ValueError('could not build a valid scene for the requested controls')


def generate(types=None, palette=None, patches=None, templates=None,
             size=None, num_templates=None, recovery=None):
  """Build one example.

  Args:
    types: layer index for every row/column (square plaid). If None, a random
      scene is built, and patches/templates must also be None.
    palette: colour of each layer; the last layer is the separator layer. For
      random scenes it must have length 3 (objects = layer 1) or length 4
      (objects = layer 2). With explicit types it defaults to [0,1,2] or
      [0,1,2,1], depending on max(types).
    patches: list of (top, left, tile) painted at (top, left) and, transposed,
      at (left, top). Needs explicit types.
    templates: list of (y, x) anchor cells. The component containing each
      anchor is painted 8 in the input. Needs explicit types.
    size: grid side for random scenes (10..30). It must equal len(types) if
      both are given.
    recovery: "mirror" or "clean" for random scenes; default mixes both.
      Clean mode guarantees at least one hidden mirror needing a clean line.
    num_templates: number of distinct-shape templates for random scenes
      (1..3). It must equal len(templates) if both are given.
  """
  if recovery not in (None, "mirror", "clean"):
    raise ValueError("recovery must be mirror or clean")
  if types is not None and recovery is not None:
    raise ValueError("recovery applies only to random scenes")
  if types is None:
    if patches is not None or templates is not None:
      raise ValueError('patches/templates require explicit types')
    if size is not None and not _MIN_SIZE <= size <= _MAX_SIZE:
      raise ValueError('size must be in 10..30')
    if num_templates is not None and not 1 <= num_templates <= 3:
      raise ValueError('num_templates must be in 1..3')
    if palette is not None:
      _check_random_palette(palette)
    recovery = recovery or random.choice(["mirror", "mirror", "mirror", "clean"])
    types, palette, patches, templates = _random_scene(
        size, palette, num_templates, recovery)
  else:
    if not 1 <= len(types) <= _MAX_SIZE:
      raise ValueError('types length must be 1..30')
    if size is not None and size != len(types):
      raise ValueError('size conflicts with len(types)')
    if palette is None:
      palette = [0, 1, 2] if max(types) <= 2 else [0, 1, 2, 1]
    if min(types) < 0 or max(types) >= len(palette):
      raise ValueError('types index outside palette')
    if any(not isinstance(c, int) or c not in range(10) or c == MARK for c in palette):
      raise ValueError("palette needs colours 0..9 excluding marker 8")
    if num_templates is not None and num_templates != len(templates or []):
      raise ValueError('num_templates conflicts with templates')
    n = len(types)
    for top, left, tile in patches or []:
      if not tile or not tile[0] or any(len(row) != len(tile[0]) for row in tile):
        raise ValueError("patch must be a nonempty rectangle")
      if any(not isinstance(c, int) or c not in range(10) for row in tile for c in row):
        raise ValueError("patch colours must be 0..9")
      th, tw = len(tile), len(tile[0])
      if top < 0 or left < 0 or top + max(th, tw) > n or left + max(th, tw) > n:
        raise ValueError('patch out of bounds')
      if any(MARK in row for row in tile):
        raise ValueError('patch tiles must not contain the marker 8')
  base = _plaid(types, palette, patches)
  inp = [row[:] for row in base]
  out = [row[:] for row in base]
  for ay, ax in templates or []:
    if not (0 <= ay < len(base) and 0 <= ax < len(base)):
      raise ValueError("template anchor outside canvas")
    color = base[ay][ax]
    comps = _components(base, color)
    own = [c for c in comps if (ay, ax) in c][0]
    key = _shape(own)
    for y, x in own:
      inp[y][x] = MARK
    for cells in comps:
      if _shape(cells) == key:
        for y, x in cells:
          out[y][x] = MARK
  return {'input': inp, 'output': out}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  diamond = [[1, 2, 1], [2, 1, 2], [1, 2, 0]]
  train = [
      generate(types=[0, 0, 1, 2, 1, 2, 0, 2, 1, 1, 0, 2, 0, 0, 1, 2, 0, 2,
                      0, 2, 1, 0, 0],
               palette=[0, 2, 1], templates=[(6, 8), (8, 16)]),
      generate(types=[0, 0, 1, 2, 0, 1, 0, 2, 1, 0, 0, 2, 0, 0, 1, 2, 0, 1,
                      0, 2, 1],
               palette=[0, 1, 2], templates=[(4, 17)]),
      generate(types=[0, 0, 1, 3, 2, 2, 0, 3, 1, 2, 0, 3, 0, 0, 2, 3, 0],
               palette=[0, 1, 2, 1],
               patches=[(4, 4, diamond), (4, 8, diamond), (8, 8, diamond)],
               templates=[(4, 5), (9, 0)]),
  ]
  test = [
      generate(types=[0, 0, 3, 1, 2, 3, 0, 1, 3, 2, 0, 3, 0, 0, 3, 1, 0, 3,
                      0, 2, 3, 0, 0, 3, 2, 0, 3],
               palette=[0, 1, 2, 1], templates=[(3, 4), (9, 9)]),
  ]
  return {'train': train, 'test': test}
