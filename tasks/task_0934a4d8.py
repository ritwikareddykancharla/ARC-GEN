# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (Apache-2.0).
# You may not use this file except in compliance with that license.
# Distributed on an AS IS basis, without warranties or conditions of any kind.

"""ARC task 0934a4d8: recover the patch hidden under a solid colour-8 block.

Rule: each input is the top-left 30x30 window of a 32x32 pattern. The pattern
is mirror-symmetric left-right and top-bottom (x <-> 31-x, y <-> 31-y), so the
last two rows and columns of the pattern are cut off. The 16x16 generating
quadrant is built from 8x8 blocks. The two diagonal blocks are each
anti-transpose symmetric. The two off-diagonal blocks are transposes of each
other. A solid rectangle of colour 8 hides part of the window. The output is
the pattern that lies under that rectangle.

Scope: canonical fixtures retain 30x30 grids and 8x8 blocks. The random
constructor also extrapolates the same symmetry mechanism to blocks of
size 4..8, giving grid sides 14, 18, 22, 26 and 30. These smaller sizes are
synthetic extensions, not sizes demonstrated in the originals. It varies:
  * the palette (4-8 colours from 1-7 and 9, never 8);
  * the quadrant content, with the block transpose/anti-transpose structure;
  * the hidden rectangle (sides 2-9) and its position.
In interior layouts every hidden cell has a visible mirror partner. Edge
layouts reproduce the test-style wrinkle: the rectangle touches the left (or
top) border and straddles the horizontal (or vertical) mirror axis. Some
cells there can only be recovered through the off-diagonal block transpose.
Their positions are restricted to the band where that transpose holds
throughout a local neighbourhood.
"""

import random

import common

_W = 30
_HALF = 16
_LAST = 31
_B = 8
_MASK = 8
_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def _parse_quadrant(quadrant):
  rows = []
  for row in quadrant:
    rows.append([int(c) for c in row])
  if len(rows) not in range(8, 17, 2) or any(len(r) != len(rows) for r in rows):
    raise ValueError('quadrant must be square with even side 8..16')
  if any(v not in range(10) or v == _MASK for row in rows for v in row):
    raise ValueError('quadrant colours must be 0..9 excluding mask colour 8')
  return rows


def _random_quadrant(palette, block_symmetry, block_size=8):
  half = 2 * block_size
  q = [[0] * half for _ in range(half)]
  if not block_symmetry:
    for r in range(half):
      for c in range(half):
        q[r][c] = random.choice(palette)
    return q
  # Diagonal 8x8 blocks: anti-transpose symmetric, (i, j) <-> (7-j, 7-i).
  for b in range(2):
    off = b * block_size
    for i in range(block_size):
      for j in range(block_size - i):
        v = random.choice(palette)
        q[off + i][off + j] = v
        q[off + block_size - 1 - j][off + block_size - 1 - i] = v
  # Off-diagonal blocks are transposes of each other.
  for i in range(block_size):
    for j in range(block_size):
      v = random.choice(palette)
      q[i][block_size + j] = v
      q[block_size + j][i] = v
  return q


def _pattern(q):
  side = 2 * len(q) - 2
  last = side + 1
  return [[q[min(y, last - y)][min(x, last - x)] for x in range(side)]
          for y in range(side)]


def _in_box(y, x, box):
  top, left, h, w = box
  return top <= y < top + h and left <= x < left + w


def _unrecoverable(box, side=30):
  """Hidden cells with no visible in-grid mirror partner."""
  top, left, h, w = box
  last = side + 1
  bad = []
  for y in range(top, top + h):
    for x in range(left, left + w):
      ok = False
      for py, px in ((y, last - x), (last - y, x), (last - y, last - x)):
        if 0 <= py < side and 0 <= px < side and not _in_box(py, px, box):
          ok = True
          break
      if not ok:
        bad.append((y, x))
  return bad


def _transpose_supported(cells, box):
  """Cells must lie where the plain transpose holds in a 13x13 window."""
  for y, x in cells:
    left_edge = x <= 1 and 14 <= y <= 17
    top_edge = y <= 1 and 14 <= x <= 17
    if not (left_edge or top_edge):
      return False
    if _in_box(x, y, box):
      return False
  return True


def _sample_box(layout, block_symmetry, side=30):
  for _ in range(500):
    if layout == 'edge':
      thick = random.randint(2, 6)
      span = random.randint(4, 9)
      start = random.randint(max(0, 17 - span), 15)
      if random.random() < 0.5:
        box = (start, 0, span, thick)
      else:
        box = (0, start, thick, span)
    else:
      h = random.randint(2, min(9, side // 2))
      w = random.randint(2, min(9, side // 2))
      box = (random.randint(0, side - h), random.randint(0, side - w), h, w)
    bad = _unrecoverable(box, side)
    if layout == 'edge':
      if bad and block_symmetry and _transpose_supported(bad, box):
        return box
    elif not bad:
      return box
  raise RuntimeError('no recoverable mask found for requested layout')


def generate(quadrant=None, box=None, num_colors=None, palette=None,
             block_symmetry=None, layout=None, block_size=None):
  """Builds one input/output pair.

  Args:
    quadrant: optional even-sided 8..16 generating quadrant, given as rows of ints or
      digit strings. The full pattern is its 4-fold mirror image.
    box: optional (top, left, height, width) of the colour-8 rectangle.
    num_colors: optional palette size (4-8) used when the quadrant is random.
    palette: optional explicit palette (must avoid colour 8).
    block_symmetry: whether the random quadrant gets the 8x8 block
      transpose / anti-transpose structure (default True).
    layout: 'interior' (all hidden cells have a mirror partner) or 'edge'
      (test-style rectangle on the border that needs the block transpose).
      Edge sampling is supported only for block_size=8.
    block_size: random block side 4..8; default weighted toward 7 and 8.
  """
  if block_symmetry is None:
    block_symmetry = True
  if layout not in (None, 'interior', 'edge'):
    raise ValueError('layout must be interior or edge')
  if quadrant is not None:
    q = _parse_quadrant(quadrant)
    inferred = len(q) // 2
    if block_size is not None and block_size != inferred:
      raise ValueError('block_size conflicts with explicit quadrant')
    block_size = inferred
  else:
    if block_size is None:
      block_size = 8 if layout == 'edge' else random.choices([4,5,6,7,8], [1,2,3,4,6])[0]
    if block_size not in range(4, 9):
      raise ValueError('block_size must be 4..8')
    if palette is None:
      if num_colors is None:
        num_colors = random.randint(4, 8)
      palette = random.sample(_COLORS, num_colors)
    if not palette or any(c not in range(10) or c == 8 for c in palette):
      raise ValueError('palette must contain colours 0..9 excluding mask colour 8')
    q = _random_quadrant(list(palette), block_symmetry, block_size)
  side = 4 * block_size - 2
  if layout == 'edge' and (not block_symmetry or block_size != 8):
    raise ValueError('edge layout requires block symmetry and block_size=8')
  if box is None:
    if layout is None:
      use_edge = block_symmetry and block_size == 8 and random.random() < 0.3
      layout = 'edge' if use_edge else 'interior'
    box = _sample_box(layout, block_symmetry, side)
  top, left, h, w = box
  if not (h > 0 and w > 0 and 0 <= top <= side-h and 0 <= left <= side-w):
    raise ValueError('mask box must lie inside the grid')
  full = _pattern(q)
  grid_in = [row[:] for row in full]
  output = common.grid(w, h, 0)
  for r in range(h):
    for c in range(w):
      output[r][c] = full[top + r][left + c]
      grid_in[top + r][left + c] = _MASK
  return {'input': grid_in, 'output': output}


_TRAIN = [
    ([
        '3533665414994399', '5333664541993491', '1135546691149945',
        '1153456619419144', '6999353343999269', '9699533334919996',
        '9969113599446992', '9996115391549699', '1491439955724324',
        '4119349145273442', '9914994564552443', '9941914445454234',
        '4399996959775572', '3491299695774527', '9944699977595455',
        '9154962977954645'], (14, 25, 9, 4)),
    ([
        '9923447533663564', '7935445733666346', '3299754441336447',
        '2379574414334674', '7793995336646799', '7739793253462699',
        '9377329964479267', '3977237946742926', '3341356424771672',
        '3314634622716127', '6633644711247216', '6633467413222761',
        '3664629299972417', '5346762999792277', '6447996297993124',
        '4674997679991122'], (2, 21, 4, 5)),
    ([
        '1944992766997672', '7144997266996727', '2719279944667251',
        '7271729944662755', '9672194476729264', '6927714467279946',
        '7296271972554592', '2769727127155499', '6644767237149776',
        '6644672743447967', '9966725137377697', '9966275577436779',
        '7672994566593744', '6727295466954341', '7255649959667737',
        '2715462995667343'], (19, 12, 3, 7)),
    ([
        '3119567114573991', '1395651741754313', '6931715699149114',
        '9113176599411341', '6667315934916725', '6676139193137652',
        '6766193191146967', '7666961313419676', '1499399111615255',
        '4199431311162555', '5714911422115552', '7541134121115525',
        '3491676976331161', '9313769667331116', '9114256733761211',
        '1341527633672211'], (7, 26, 4, 4)),
]

_TEST = [
    ([
        '4413577961664477', '4433759766664472', '3444795751617799',
        '4344977515667219', '9774443344779732', '7947443144727923',
        '7497344477917497', '4779434472994779', '6651447772264622',
        '1615447237666422', '6666779991722246', '6616721915372264',
        '4477977499167266', '4472794799613762', '7791329716995172',
        '7299237961991937'], (14, 0, 9, 3)),
]


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [generate(quadrant=q, box=b) for q, b in _TRAIN]
  test = [generate(quadrant=q, box=b) for q, b in _TEST]
  return {'train': train, 'test': test}
