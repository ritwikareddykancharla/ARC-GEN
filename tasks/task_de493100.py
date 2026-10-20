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

"""Generator for ARC task de493100.

Rule: the input is a 30x30 crop of a 32x32 mosaic. The mosaic is mirror
symmetric left-right (column x equals column 31-x) and top-bottom (row y
equals row 31-y). One axis-aligned rectangle of the crop is painted over
with colour 7, and no other cell is 7. The output is the hidden mosaic
content under that rectangle, cropped to exactly the rectangle's size.

Latent scene: an (N+2)//2 square quadrant Q fixes the mosaic through
full[y][x] = Q[min(y, N+1-y)][min(x, N+1-x)]. At N=30 the quadrant
is 16x16. Random quadrants are tiled from
b x b motif blocks (b in 3..5 by default, 2..6 on request) on a lattice with
a random offset. The palette has 4-6 colours and never contains colour 7.
Each block is one of three kinds: an accented solid, a small-palette random
block, or a mirrored seed. Optionally (diag_symmetry) the block lattice is
made transpose symmetric, and then one to three off-diagonal blocks are
resampled. That leaves a weak, partial diagonal cue, as in the real task.
The quadrant is always forced to differ from its transpose somewhere.

A random mask rectangle has sides 2..10. It is always recoverable: every
hidden cell has at least one in-grid, unmasked mirror partner among
(y,31-x), (31-y,x) and (31-y,31-x). The hidden patch contains at least two colours, except an explicitly
requested 1x1 mask. Masks may straddle the central axes or touch the border
rows and columns 0-1. In those cases a cell loses one partner direction and
must use another one.

Scope: canonical grids are 30x30 with mirror coordinate 31. Synthetic grids
use an even side N in 12..30 and the same two-cell crop geometry, with
mirror coordinate N+1. Default sampling favours larger sides; size=30
reproduces the original regime. Smaller sides are labelled extensions. Mask colour 7 is fixed. In original train pair 1, the mask
touches columns 0-1, and eight cells there have no visible mirror partner.
Those cells are resolved only by a weak transpose cue. Explicit latent
scenes are accepted only when every hidden value is justified by an
unmasked direct partner or this fallback cue. Random masks require direct
partners; no unrelated latent answer can silently pass an unrecoverable mask.
"""

import random

SIZE = 30
AXIS = 31
QS = 16
MASK = 7
COLOURS = [1, 2, 3, 4, 5, 6, 8, 9]
MAX_SIDE = QS - 2
RANDOM_CAP = 10


def _as_int(v, name):
  if isinstance(v, (bool, float)):
    raise ValueError("%s must be an integer" % name)
  try:
    iv = int(v)
  except (TypeError, ValueError):
    raise ValueError("%s must be an integer" % name)
  if iv != v:
    raise ValueError("%s must be an integer" % name)
  return iv


def _full_mosaic(q, size=SIZE):
  axis = size + 1
  return [[q[min(y, axis - y)][min(x, axis - x)] for x in range(size)]
          for y in range(size)]


def _orbit(y, x, size=SIZE):
  axis = size + 1
  return (min(y, axis - y), min(x, axis - x))


def _recoverable(top, left, h, w, size=SIZE):
  """Every masked cell must have an unmasked in-grid mirror partner."""

  axis = size + 1

  def masked(a, b):
    return top <= a < top + h and left <= b < left + w

  for y in range(top, top + h):
    for x in range(left, left + w):
      ok = False
      for a, b in ((y, axis - x), (axis - y, x), (axis - y, axis - x)):
        if 0 <= a < size and 0 <= b < size and not masked(a, b):
          ok = True
          break
      if not ok:
        return False
  return True


def _single_orbit(top, left, h, w, size=SIZE):
  """True if every masked cell lies in one mirror orbit (always one colour)."""
  keys = set()
  for y in range(top, top + h):
    for x in range(left, left + w):
      keys.add(_orbit(y, x, size))
  return len(keys) < 2


def _nontrivial(full, top, left, h, w):
  """The hidden patch must use at least two colours."""
  vals = set()
  for y in range(top, top + h):
    for x in range(left, left + w):
      vals.add(full[y][x])
  return h * w == 1 or len(vals) >= 2


def _sample_block(palette, b):
  style = random.choice(["accent", "random", "mirror"])
  if style == "accent":
    main = random.choice(palette)
    others = [c for c in palette if c != main]
    block = [[main] * b for _ in range(b)]
    for _ in range(random.randint(1, max(2, (b * b) // 3))):
      block[random.randrange(b)][random.randrange(b)] = random.choice(others)
    return block
  if style == "random":
    sub = random.sample(palette, random.randint(2, min(3, len(palette))))
    return [[random.choice(sub) for _ in range(b)] for _ in range(b)]
  hs = (b + 1) // 2
  seed = [[random.choice(palette) for _ in range(hs)] for _ in range(hs)]
  return [[seed[min(r, b - 1 - r)][min(c, b - 1 - c)] for c in range(b)]
          for r in range(b)]


def _put_block(q, bi, bj, block, b):
  for r in range(b):
    for c in range(b):
      q[b * bi + r][b * bj + c] = block[r][c]


def _break_transpose(q, palette):
  """Make sure the quadrant is not exactly transpose symmetric."""
  qs = len(q)
  for i in range(qs):
    for j in range(i + 1, qs):
      if q[i][j] != q[j][i]:
        return
  i = random.randrange(qs - 1)
  j = random.randint(i + 1, qs - 1)
  q[i][j] = random.choice([c for c in palette if c != q[i][j]])


def _sample_quadrant(palette, diag, b, offset, qs=QS):
  nb = (qs + offset + b - 1) // b
  big = nb * b
  q = [[0] * big for _ in range(big)]
  for bi in range(nb):
    for bj in range(nb):
      if diag and bj < bi:
        continue
      block = _sample_block(palette, b)
      if diag and bi == bj:
        for r in range(b):
          for c in range(r):
            block[r][c] = block[c][r]
      _put_block(q, bi, bj, block, b)
      if diag and bj > bi:
        _put_block(q, bj, bi, [[block[c][r] for c in range(b)]
                               for r in range(b)], b)
  if diag and nb > 1:
    # Resample some lower blocks so the diagonal cue stays weak.
    lower = [(bi, bj) for bi in range(nb) for bj in range(bi)]
    k = random.randint(1, max(1, min(3, len(lower) // 2)))
    for bi, bj in random.sample(lower, k):
      _put_block(q, bi, bj, _sample_block(palette, b), b)
  quad = [row[offset:offset + qs] for row in q[offset:offset + qs]]
  _break_transpose(quad, palette)
  return quad


def _side(fixed, cap=RANDOM_CAP):
  return fixed if fixed is not None else random.randint(2, cap)


def _sample_mask(full, mask_height, mask_width, size=SIZE):
  """Return ((top, left, h, w), good) for a recoverable mask."""
  qs, axis = (size + 2) // 2, size + 1
  cap = min(RANDOM_CAP, qs - 2)
  for _ in range(200):
    h = _side(mask_height, cap)
    w = _side(mask_width, cap)
    top = random.randint(0, size - h)
    left = random.randint(0, size - w)
    if (_recoverable(top, left, h, w, size) and
        _nontrivial(full, top, left, h, w)):
      return (top, left, h, w), True
  # Constructive fallback: keep the rectangle in columns 2..qs-1, with
  # visible partners in the opposite half; optionally reflect the rectangle.
  rect = None
  for _ in range(50):
    h = _side(mask_height, cap)
    w = _side(mask_width, cap)
    top = random.randint(0, size - h)
    left = random.randint(2, qs - w)
    if random.random() < 0.5:
      left = axis - (left + w - 1)
    rect = (top, left, h, w)
    if _nontrivial(full, top, left, h, w):
      return rect, True
  return rect, False


def _check_palette(palette):
  pal = sorted(set(_as_int(c, "palette colour") for c in palette))
  if len(pal) < 2:
    raise ValueError("palette needs at least two distinct colours")
  for c in pal:
    if c < 0 or c > 9 or c == MASK:
      raise ValueError("palette colours must be 0..9 and not 7")
  return pal


def _parse_quadrant(quadrant, qs=QS):
  rows = []
  for row in quadrant:
    vals = []
    for v in row:
      if isinstance(v, str):
        if len(v) != 1 or v not in "0123456789":
          raise ValueError("quadrant string cells must be single digits")
        vals.append(int(v))
      else:
        vals.append(_as_int(v, "quadrant cell"))
    rows.append(vals)
  if len(rows) != qs or any(len(r) != qs for r in rows):
    raise ValueError("quadrant must be %dx%d" % (qs, qs))
  if any(v < 0 or v > 9 or v == MASK for r in rows for v in r):
    raise ValueError("quadrant colours must be 0..9 and not 7")
  return rows


def _has_reconstruction_cues(full, rect, size):
  """Check latent targets against visible direct or fallback transpose cues."""
  top, left, h, w = rect
  axis = size + 1
  def visible(r, c):
    return 0 <= r < size and 0 <= c < size and not (top <= r < top+h and left <= c < left+w)
  for r in range(top, top+h):
    for c in range(left, left+w):
      direct = [(r,axis-c),(axis-r,c),(axis-r,axis-c)]
      choices = [(y,x) for y,x in direct if visible(y,x)]
      if not choices:
        choices = [(y,x) for y,x in [(c,r),(c,axis-r),(axis-c,r),(axis-c,axis-r)] if visible(y,x)]
      if not choices or any(full[y][x] != full[r][c] for y,x in choices):
        return False
  return True


def generate(quadrant=None, mask=None, palette=None, diag_symmetry=None,
             block_size=None, block_offset=None, mask_height=None,
             mask_width=None, size=None):
  """Build one de493100 example with dimension-aware mirror coordinates.

  Args:
    quadrant: optional (size+2)//2 rows (digit strings or int lists) giving the
      top-left square quadrant of the symmetric mosaic. It cannot be combined
      with palette, diag_symmetry, block_size or block_offset.
    mask: optional (top, left, height, width) of the colour-7 rectangle. With
      an explicit quadrant it may use the verified transpose fallback or be single-coloured
      (fixture replay). With a random quadrant it must be recoverable from
      mirror partners, span at least two mirror orbits unless explicitly 1x1.
      It cannot be combined with mask_height or mask_width.
    palette: optional list of mosaic colours (0..9, never 7, >= 2 colours).
    diag_symmetry: optional bool. If True, the motif-block lattice is
      transpose symmetric except for 1-3 resampled off-diagonal blocks.
    block_size: optional motif block side, 2..6 (random default 3..5).
    block_offset: optional lattice offset, 0..block_size-1.
    mask_height: optional random-mask height, 1..(size+2)//2-2.
    mask_width: optional random-mask width in the same range. Defaults
      sample 2..min(10,(size+2)//2-2); requested 1x1 masks are supported.
    size: even crop side 12..30. With a quadrant, inferred from its length.
      With an explicit mask alone, defaults to 30 to preserve its coordinates.
      Otherwise sampled with larger sizes weighted more heavily, conditional
      on the requested mask dimensions.
  """
  if size is None:
    if quadrant is not None:
      if not isinstance(quadrant, (list, tuple)):
        raise ValueError("quadrant must be a sequence of rows")
      size = 2 * len(quadrant) - 2
    elif mask is not None:
      size = SIZE  # Preserve the original coordinate regime for explicit masks.
    else:
      sides = [_as_int(v, "mask side") for v in (mask_height, mask_width) if v is not None]
      options = [(n,w) for n,w in zip(range(12,31,2), [1,1,1,2,2,3,3,4,4,9])
                 if all(1 <= v <= (n+2)//2-2 for v in sides)]
      if not options:
        raise ValueError("no supported size accommodates the requested mask sides")
      size = random.choices([n for n,w in options], weights=[w for n,w in options])[0]
  size = _as_int(size, "size")
  if size % 2 or not 12 <= size <= 30:
    raise ValueError("size must be an even integer in 12..30")
  qs = (size + 2) // 2
  max_side = qs - 2
  given_q = None
  if quadrant is None:
    if palette is None:
      palette = random.sample(COLOURS, random.randint(4, 6))
    palette = _check_palette(palette)
    if diag_symmetry is None:
      diag_symmetry = random.random() < 0.5
    if not isinstance(diag_symmetry, bool):
      raise ValueError("diag_symmetry must be a bool or None")
    if block_size is None:
      block_size = random.choice([3, 4, 4, 5])
    block_size = _as_int(block_size, "block_size")
    if not 2 <= block_size <= 6:
      raise ValueError("block_size must be in 2..6")
    if block_offset is None:
      block_offset = random.randrange(block_size)
    block_offset = _as_int(block_offset, "block_offset")
    if not 0 <= block_offset < block_size:
      raise ValueError("block_offset must be in 0..block_size-1")
  else:
    if (palette is not None or diag_symmetry is not None or
        block_size is not None or block_offset is not None):
      raise ValueError("palette/diag_symmetry/block_size/block_offset "
                       "conflict with an explicit quadrant")
    given_q = _parse_quadrant(quadrant, qs)

  explicit_rect = None
  if mask is None:
    if mask_height is not None:
      mask_height = _as_int(mask_height, "mask_height")
    if mask_width is not None:
      mask_width = _as_int(mask_width, "mask_width")
    for side in (mask_height, mask_width):
      if side is not None and not 1 <= side <= max_side:
        raise ValueError("mask sides must be in 1..%d" % max_side)
  else:
    if mask_height is not None or mask_width is not None:
      raise ValueError("mask_height/mask_width conflict with explicit mask")
    if len(mask) != 4:
      raise ValueError("mask must be (top, left, height, width)")
    top, left, h, w = (_as_int(v, "mask entry") for v in mask)
    if h < 1 or w < 1 or top < 0 or left < 0:
      raise ValueError("invalid mask rectangle")
    if top + h > size or left + w > size or (h == size and w == size):
      raise ValueError("mask rectangle out of bounds or covers the grid")
    if given_q is None:
      if not _recoverable(top, left, h, w, size):
        raise ValueError("explicit mask with a random quadrant must be "
                         "recoverable from mirror partners")
      if h * w > 1 and _single_orbit(top, left, h, w, size):
        raise ValueError("explicit mask lies in one mirror orbit, so its "
                         "patch is always a single colour")
    explicit_rect = (top, left, h, w)

  replay = given_q is not None and explicit_rect is not None
  full = None
  rect = None
  good = False
  for _ in range(30):
    if given_q is not None:
      q = given_q
    else:
      q = _sample_quadrant(palette, diag_symmetry, block_size, block_offset, qs)
    full = _full_mosaic(q, size)
    if explicit_rect is None:
      rect, good = _sample_mask(full, mask_height, mask_width, size)
    else:
      rect = explicit_rect
      good = _nontrivial(full, *rect)
    if good or given_q is not None:
      break
  if not good and not replay:
    raise ValueError("could not build a mask with a multi-colour hidden "
                     "patch for these parameters")

  top, left, h, w = rect
  if not _has_reconstruction_cues(full, rect, size):
    raise ValueError("explicit mosaic has no valid visible reconstruction cue")
  output = [[full[y][x] for x in range(left, left + w)]
            for y in range(top, top + h)]
  grid_in = [row[:] for row in full]
  for y in range(top, top + h):
    for x in range(left, left + w):
      grid_in[y][x] = MASK
  return {"input": grid_in, "output": output}


def validate():
  """Reconstruct the canonical fixtures from explicit latent quadrants."""
  q1 = ["4338884423826226", "4388884438289666", "8833448838832696",
        "8344448883326629", "5944438869266298", "9554438326668689",
        "4559383326928662", "4495884466696886", "2338622699889999",
        "3883966695899999", "8283269648599999", "2832662984999999",
        "6926688699969998", "2666266899999588", "2692986899994859",
        "6669892669998499"]
  q2 = ["3322899885551331", "1121988952553119", "2213988985253192",
        "2913899858581919", "8381331213319498", "3838112231192889",
        "8383921331919984", "1838221319299929", "8585133132629969",
        "5258311911229946", "5525319263126499", "5558191936139699",
        "1331929984323222", "3119489948231126", "3191988232846312",
        "1929894923483613"]
  q3 = ["3188688688899999", "2383861889982988", "1831816848989898",
        "8223688684889899", "3883313892999898", "8318238899888489",
        "8138283198999548", "3883812398895989", "8848999929885251",
        "8984298882832545", "8998989888295452", "9888989988821525",
        "9299989588682938", "9988845988468288", "9899984864888829",
        "9889898986888882"]
  q4 = ["2929646212661194", "5595466636661199", "9959666432629984",
        "9952264623314998", "9818295911946666", "8911559211999966",
        "1198995999899196", "8189995249481996", "1332119499348838",
        "2623119944488863", "6663998489493688", "6621499893498388",
        "1194699199419984", "1199691999144443", "9989669941993949",
        "4948666614999849"]
  qt = ["2216999944514455", "1163991953151435", "2612919954345341",
        "6312999945545544", "8888223641558444", "8858116144359344",
        "8588361253444934", "8888621255149498", "4554445519198686",
        "4345143583996888", "5135534199398886", "1544554493816868",
        "4155894999881999", "4435439499288391", "5344443982993939",
        "5514444888999981"]
  train = [
      generate(quadrant=q1, mask=(14, 0, 10, 10)),
      generate(quadrant=q2, mask=(0, 21, 7, 5)),
      generate(quadrant=q3, mask=(24, 5, 4, 4)),
      generate(quadrant=q4, mask=(20, 21, 6, 8)),
  ]
  test = [generate(quadrant=qt, mask=(16, 19, 10, 2))]
  return {"train": train, "test": test}
