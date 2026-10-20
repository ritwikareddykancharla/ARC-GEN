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

"""Generator for ARC task 83eb0a57 (assemble pieces onto the largest slab).

Rule: the input is a background colour holding several solid rectangular
pieces. The largest piece (the host) has a fill colour and some visible
"key" cells. Every smaller piece uses two colours: a key colour and a hidden
colour. Inside the host, only a piece's key cells are visible; its hidden
cells show the host fill. The output is the host, cropped. Each smaller
piece is then pasted onto it, from largest to smallest bounding-box area, at
the offset where its key cells line up. Alignment is scored over canvas cells
whose colour belongs to the piece: +1 when the colours agree and -1 when
they disagree. Cells of foreign colours are ignored.

Scope (random mode): the grid size is sampled from 18..30 per side, with
30x30 favoured, or it is supplied by the caller. The host is 5..15 by 5..17
cells, capped by the grid size. The colours are sampled, and there are 1-4
pasted pieces of up to 9x9 cells. Key patterns come in four styles: blocks,
lines, a ring outline, or a single key cell inside a hidden frame (like the
8-ring of train pair 3). Key colours may be shared between pieces, which
creates competing distractor key groups. Occasionally a piece's hidden
colour equals another piece's key colour, or equals the host fill (so the
fill cells count in that piece's score instead of being ignored).

An optional nested mode places a small piece inside a larger pasted piece,
as in train pair 3. In that mode the larger piece carries extra distractor
key blocks of the same colour. An optional decoy mode requires that a naive
solver (matches only, no -1 penalty, first maximum in raster order) picks a
wrong offset for at least one piece. This makes the mismatch penalty matter.

Random mode excludes partially overlapping paste footprints (non-nested pieces
keep a one-cell gap inside the host) and more than four pasted pieces. Explicit
mode permits additional pieces and overlapping footprints when all input
rectangles are separated and each successive placement is uniquely justified.
Both modes require two colours per pasted piece. Single-piece random scenes
have no host-only distractor keys outside the piece footprint.

The output is built from the latent paste offsets. A local implementation
of the scoring rule is used only to reject scenes whose intended offset is
not the unique best offset. Explicit scenes go through the same check.
Grid sizes other than 30x30, and hosts or pieces larger than the fixtures,
are synthetic extensions.
"""

import random

import common


def _is_int(v):
  """True for genuine ints (bools and floats are rejected)."""
  return type(v) is int


def _is_colour(v):
  return _is_int(v) and 0 <= v <= 9


def _pattern(h, w, hidden, key):
  """Random two-colour piece pattern with at least one key and one hidden cell."""
  for _ in range(60):
    pat = [[hidden] * w for _ in range(h)]
    style = random.choice(["blocks", "blocks", "lines", "ring"])
    if style == "blocks":
      for _ in range(random.randint(1, 3)):
        bh = random.randint(1, min(2, h))
        bw = random.randint(1, min(2, w))
        r = random.randint(0, h - bh)
        c = random.randint(0, w - bw)
        for y in range(r, r + bh):
          for x in range(c, c + bw):
            pat[y][x] = key
    elif style == "lines":
      if random.random() < 0.5:
        for y in range(h):
          if random.random() < 0.4:
            pat[y] = [key] * w
      else:
        for x in range(w):
          if random.random() < 0.4:
            for y in range(h):
              pat[y][x] = key
    else:
      if h < 3 or w < 3:
        continue
      rh = random.randint(3, h)
      rw = random.randint(3, w)
      r = random.randint(0, h - rh)
      c = random.randint(0, w - rw)
      for y in range(r, r + rh):
        for x in range(c, c + rw):
          if y in (r, r + rh - 1) or x in (c, c + rw - 1):
            pat[y][x] = key
    n = sum(1 for row in pat for v in row if v == key)
    if 0 < n < h * w:
      return pat
  pat = [[hidden] * w for _ in range(h)]
  pat[random.randrange(h)][random.randrange(w)] = key
  return pat


def _single_key(h, w, hidden, key):
  """One interior key cell inside a hidden frame (like pair 3's 8-ring)."""
  pat = [[hidden] * w for _ in range(h)]
  pat[random.randint(1, h - 2)][random.randint(1, w - 2)] = key
  return pat


def _choices(canvas, pat):
  """Return (all best offsets under the +1/-1 rule, naive raster-first offset).

  The naive solver counts only matching cells and applies no penalty. It is
  an ablation used to measure whether the mismatch penalty matters.
  """
  hh, ww = len(canvas), len(canvas[0])
  h, w = len(pat), len(pat[0])
  cols = set(v for row in pat for v in row)
  best, where = None, []
  nbest, nwhere = None, None
  for oy in range(hh - h + 1):
    for ox in range(ww - w + 1):
      s = 0
      m = 0
      for y in range(h):
        crow = canvas[oy + y]
        prow = pat[y]
        for x in range(w):
          v = crow[ox + x]
          if v in cols:
            if v == prow[x]:
              s += 1
              m += 1
            else:
              s -= 1
      if best is None or s > best:
        best, where = s, [(oy, ox)]
      elif s == best:
        where.append((oy, ox))
      if nbest is None or m > nbest:
        nbest, nwhere = m, (oy, ox)
  return where, nwhere


def _free(boxes, r, c, h, w):
  """True if box (r, c, h, w) keeps a one-cell gap from every box in boxes."""
  for (br, bc, bh, bw) in boxes:
    if r - 1 < br + bh and br < r + h + 1 and c - 1 < bc + bw and bc < c + w + 1:
      return False
  return True


def _area(pat):
  return len(pat) * len(pat[0])


def _assemble(fill, hh, hw, latent):
  """Build host canvas and output from latent (pattern, key, dy, dx) pieces.

  Returns (host, output, unique, naive_fail). unique is True when every
  latent offset is the unique best offset at its paste step. naive_fail is
  True when the no-penalty solver would pick a different offset at some step.
  """
  order = sorted(latent, key=lambda p: -_area(p[0]))
  canvas = [[fill] * hw for _ in range(hh)]
  for (pat, key, dy, dx) in order:
    for y, row in enumerate(pat):
      for x, v in enumerate(row):
        if v == key:
          canvas[dy + y][dx + x] = key
  hostg = [row[:] for row in canvas]
  unique = True
  naive_fail = False
  for (pat, key, dy, dx) in order:
    where, nwhere = _choices(canvas, pat)
    if where != [(dy, dx)]:
      unique = False
    if nwhere != (dy, dx):
      naive_fail = True
    for y, row in enumerate(pat):
      for x, v in enumerate(row):
        canvas[dy + y][dx + x] = v
  return hostg, canvas, unique, naive_fail


def _build(size, bg, host, pieces):
  """Render the input grid and assembled output from latent parameters."""
  height, width = size
  top, left, hh, hw, fill = host
  latent = [(p[2], p[3], p[4], p[5]) for p in pieces]
  hostg, out, unique, naive_fail = _assemble(fill, hh, hw, latent)
  grid = common.grid(width, height, bg)
  for y in range(hh):
    for x in range(hw):
      grid[top + y][left + x] = hostg[y][x]
  for (r, c, pat, _, _, _) in pieces:
    for y, row in enumerate(pat):
      for x, v in enumerate(row):
        grid[r + y][c + x] = v
  return grid, out, unique, naive_fail


def _bg_dominant(grid, b):
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  nb = counts.get(b, 0)
  return all(counts[c] < nb for c in counts if c != b)


def _check_size(size):
  if (not isinstance(size, (list, tuple)) or len(size) != 2 or
      not all(_is_int(v) for v in size)):
    raise ValueError("size must be a pair of ints (height, width)")


def _check_explicit(size, bg, host, pieces):
  """Reject malformed explicit scenes instead of silently rendering them."""
  _check_size(size)
  height, width = size
  if not (1 <= height <= 30 and 1 <= width <= 30):
    raise ValueError("size out of range")
  if not _is_colour(bg):
    raise ValueError("bg must be an int colour 0..9")
  if not isinstance(host, (list, tuple)) or len(host) != 5:
    raise ValueError("host must be (top, left, height, width, fill)")
  top, left, hh, hw, fill = host
  if not all(_is_int(v) for v in (top, left, hh, hw)) or hh < 1 or hw < 1:
    raise ValueError("host geometry must be positive ints")
  if not _is_colour(fill) or fill == bg:
    raise ValueError("host fill must be a colour differing from background")
  if top < 0 or left < 0 or top + hh > height or left + hw > width:
    raise ValueError("host out of bounds")
  if not isinstance(pieces, (list, tuple)) or not pieces:
    raise ValueError("at least one piece is required")
  boxes = [(top, left, hh, hw)]
  areas = []
  for piece in pieces:
    if not isinstance(piece, (list, tuple)) or len(piece) != 6:
      raise ValueError("piece must be (row, col, pattern, key, dy, dx)")
    r, c, pat, key, dy, dx = piece
    if not all(_is_int(v) for v in (r, c, dy, dx)):
      raise ValueError("piece positions and offsets must be ints")
    if (not isinstance(pat, (list, tuple)) or not pat
        or any(not isinstance(row, (list, tuple)) or not row for row in pat)):
      raise ValueError("pattern must be non-empty rows of colours")
    h, w = len(pat), len(pat[0])
    if any(len(row) != w for row in pat):
      raise ValueError("pattern must be rectangular")
    if any(not _is_colour(v) or v == bg for row in pat for v in row):
      raise ValueError("pattern colours must be non-background colours")
    cols = set(v for row in pat for v in row)
    if not _is_colour(key) or len(cols) != 2 or key not in cols:
      raise ValueError("pattern must use exactly the key and one hidden colour")
    if key == fill:
      raise ValueError("key must differ from the host fill")
    if r < 0 or c < 0 or r + h > height or c + w > width:
      raise ValueError("piece out of bounds")
    if dy < 0 or dx < 0 or dy + h > hh or dx + w > hw:
      raise ValueError("paste offset out of host bounds")
    if not _free(boxes, r, c, h, w):
      raise ValueError("pieces must not touch or overlap in the input")
    boxes.append((r, c, h, w))
    areas.append(h * w)
  if len(set(areas)) != len(areas) or max(areas) >= hh * hw:
    raise ValueError("piece areas must be distinct and below the host area")
  grid, _, unique, _ = _build(size, bg, host, pieces)
  if not unique:
    raise ValueError("a paste offset is not the unique best alignment")
  if not _bg_dominant(grid, bg):
    raise ValueError("bg must be the strictly most frequent colour")


def _random_scene(size, bg, num_pieces, nested, decoy):
  """Sample a fresh valid scene; returns (size, bg, host, pieces)."""
  # Keep the sampled count through retries; resampling it inside this loop
  # systematically favours easy-to-pack one-piece scenes.
  n = num_pieces if num_pieces is not None else random.choice(
      [1, 2, 2, 3, 3, 4])
  for _ in range(1000):
    if size is None:
      if random.random() < 0.4:
        height, width = 30, 30
      else:
        height, width = random.randint(18, 30), random.randint(18, 30)
    else:
      height, width = size
    b = bg if bg is not None else random.randint(0, 9)
    fill = random.choice([c for c in range(10) if c != b])
    pool = [c for c in range(10) if c not in (b, fill)]
    random.shuffle(pool)
    keys_used = []
    if decoy is None:
      want_decoy = n >= 2 and random.random() < 0.4
    else:
      want_decoy = decoy
    if nested is None:
      nest = n >= 2 and random.random() < (0.7 if want_decoy else 0.3)
    else:
      nest = nested
    share = 0.7 if want_decoy else 0.5

    def take():
      return pool.pop() if pool else None

    def pick_key():
      if keys_used and (random.random() < share or not pool):
        return random.choice(keys_used)
      k = take()
      if k is not None:
        keys_used.append(k)
      return k

    def pick_hidden(key):
      # Hidden colour equal to the host fill makes fill cells count in the
      # score; the uniqueness check below keeps such scenes unambiguous.
      if random.random() < 0.1:
        return fill
      others = [k for k in keys_used if k != key]
      if others and random.random() < 0.15:
        return random.choice(others)
      return take()

    lo = 6 if nest else 5
    hh_max = min(15, height - 6)
    hw_max = min(17, width - 6)
    if hh_max < lo or hw_max < lo:
      continue
    hh = random.randint(lo, hh_max)
    hw = random.randint(lo, hw_max)
    latent = []
    boxes = []
    if nest:
      key = pick_key()
      hid_big = take()
      hid_small = take()
      if key is None or hid_big is None or hid_small is None:
        continue
      bh = random.randint(5, min(9, hh - 1))
      bw = random.randint(5, min(9, hw - 1))
      sh = random.randint(2, min(4, bh - 2))
      sw = random.randint(2, min(4, bw - 2))
      sy = random.randint(0, bh - sh)
      sx = random.randint(0, bw - sw)
      if sh >= 3 and sw >= 3 and random.random() < (0.7 if want_decoy else 0.4):
        small = _single_key(sh, sw, hid_small, key)
      else:
        small = _pattern(sh, sw, hid_small, key)
      big = [[hid_big] * bw for _ in range(bh)]
      for y in range(sh):
        for x in range(sw):
          if small[y][x] == key:
            big[sy + y][sx + x] = key
      for _ in range(random.randint(1, 3)):
        for _ in range(30):
          if want_decoy and random.random() < 0.6:
            dh, dw = 2, 2
          else:
            dh = random.randint(1, 2)
            dw = random.randint(1, 2)
          r = random.randint(0, bh - dh)
          c = random.randint(0, bw - dw)
          if r + dh <= sy or r >= sy + sh or c + dw <= sx or c >= sx + sw:
            for y in range(r, r + dh):
              for x in range(c, c + dw):
                big[y][x] = key
            break
      if not any(v == hid_big for row in big for v in row):
        continue
      dy = random.randint(0, hh - bh)
      dx = random.randint(0, hw - bw)
      latent.append((big, key, dy, dx))
      latent.append((small, key, dy + sy, dx + sx))
      boxes.append((dy, dx, bh, bw))
      n_extra = n - 2
    else:
      n_extra = n
    for _ in range(n_extra):
      for _ in range(60):
        h = random.randint(2, min(9, hh - 2))
        w = random.randint(2, min(9, hw - 2))
        r = random.randint(0, hh - h)
        c = random.randint(0, hw - w)
        if _free(boxes, r, c, h, w):
          break
      else:
        break
      key = pick_key()
      if key is None:
        break
      hid = pick_hidden(key)
      if hid is None:
        break
      if h >= 3 and w >= 3 and random.random() < (0.4 if want_decoy else 0.15):
        pat = _single_key(h, w, hid, key)
      else:
        pat = _pattern(h, w, hid, key)
      latent.append((pat, key, r, c))
      boxes.append((r, c, h, w))
    if len(latent) != n:
      continue
    areas = [_area(p[0]) for p in latent]
    if len(set(areas)) != len(areas) or max(areas) >= hh * hw:
      continue
    # Ambiguity invariant: each paste must be the unique best alignment.
    _, _, unique, naive_fail = _assemble(fill, hh, hw, latent)
    if not unique:
      continue
    if want_decoy and not naive_fail:
      continue
    dims = [(hh, hw)] + [(len(p[0]), len(p[0][0])) for p in latent]
    placed = []
    for (h, w) in dims:
      for _ in range(400):
        r = random.randint(0, height - h)
        c = random.randint(0, width - w)
        if _free(placed, r, c, h, w):
          placed.append((r, c, h, w))
          break
      else:
        break
    if len(placed) != len(dims):
      continue
    host = (placed[0][0], placed[0][1], hh, hw, fill)
    pieces = [(placed[i + 1][0], placed[i + 1][1], p[0], p[1], p[2], p[3])
              for i, p in enumerate(latent)]
    grid, _, _, _ = _build((height, width), b, host, pieces)
    if not _bg_dominant(grid, b):
      continue
    return (height, width), b, host, pieces
  raise RuntimeError("could not construct a valid scene")


def generate(size=None, bg=None, host=None, pieces=None, num_pieces=None,
             nested=None, decoy=None):
  """Generate one input/output pair.

  Args:
    size: (height, width) ints of the input grid. In random mode each side
      must be 18..30; random if None. In explicit mode it defaults to
      (30, 30) and may be 1..30 per side.
    bg: background colour, int 0..9. Random if None in random mode; required
      in explicit mode.
    host: (top, left, height, width, fill) of the largest slab in the input.
      Must be given together with pieces (explicit mode).
    pieces: list of (row, col, pattern, key, dy, dx). (row, col) is the
      piece's input position, pattern is its full two-colour grid, key is
      its key colour (visible inside the host), and (dy, dx) is its paste
      offset relative to the host. Each offset must be the unique best
      alignment at its paste step, or ValueError is raised.
    num_pieces: int number of pasted pieces (1..4) in random mode; in
      explicit mode it must equal len(pieces) if given.
    nested: random mode only; None or bool. True forces a small piece nested
      inside a larger pasted piece (needs at least 2 pieces), False forbids
      it.
    decoy: random mode only; None or bool. True requires the no-penalty
      naive solver to misplace at least one piece (needs at least 2 pieces),
      False removes that requirement. None samples it.
  """
  if nested is not None and type(nested) is not bool:
    raise ValueError("nested must be None or a bool")
  if decoy is not None and type(decoy) is not bool:
    raise ValueError("decoy must be None or a bool")
  if num_pieces is not None and not _is_int(num_pieces):
    raise ValueError("num_pieces must be an int")
  if bg is not None and not _is_colour(bg):
    raise ValueError("bg must be an int colour 0..9")
  if size is not None:
    _check_size(size)
    size = (size[0], size[1])
  if (host is None) != (pieces is None):
    raise ValueError("host and pieces must be supplied together")
  if host is not None:
    if nested is not None or decoy is not None:
      raise ValueError("nested and decoy are random-mode controls")
    if not isinstance(pieces, (list, tuple)) or not pieces:
      raise ValueError("at least one piece is required")
    if num_pieces is not None and num_pieces != len(pieces):
      raise ValueError("num_pieces disagrees with explicit pieces")
    if bg is None:
      raise ValueError("explicit scenes require bg")
    if size is None:
      size = (30, 30)
    _check_explicit(size, bg, host, pieces)
  else:
    if size is not None and not (18 <= size[0] <= 30 and 18 <= size[1] <= 30):
      raise ValueError("random-mode size must be 18..30 per side")
    if num_pieces is not None and not 1 <= num_pieces <= 4:
      raise ValueError("num_pieces must be 1..4")
    if (nested or decoy) and num_pieces is not None and num_pieces < 2:
      raise ValueError("nested and decoy modes need at least two pieces")
    if (nested or decoy) and num_pieces is None:
      num_pieces = random.randint(2, 4)
    size, bg, host, pieces = _random_scene(size, bg, num_pieces, nested, decoy)
  grid, out, _, _ = _build(size, bg, host, pieces)
  return {"input": grid, "output": out}


def validate():
  """Reconstruct the canonical ARC pairs from explicit latent parameters."""
  p2 = [[1] * 9,
        [1, 2, 2, 1, 1, 1, 2, 2, 1],
        [1, 2, 2, 1, 1, 1, 2, 2, 1],
        [1] * 9,
        [1] * 9,
        [1, 2, 2, 1, 1, 1, 2, 2, 1],
        [1, 2, 2, 1, 1, 1, 2, 2, 1],
        [1] * 9]
  p3 = [[2] * 7,
        [2, 1, 1, 2, 2, 2, 2],
        [2, 1, 1, 2, 2, 2, 2],
        [2] * 7,
        [2] * 7,
        [2, 2, 2, 2, 1, 2, 2],
        [2] * 7,
        [2] * 7]
  train = [
      generate(size=(30, 30), bg=8, host=(2, 15, 9, 5, 1),
               pieces=[(16, 5, [[3, 3, 3], [2, 2, 2], [3, 3, 3]], 3, 1, 1)]),
      generate(size=(30, 30), bg=4, host=(15, 8, 12, 16, 3),
               pieces=[(3, 2, p2, 2, 2, 2)]),
      generate(size=(30, 30), bg=3, host=(16, 5, 13, 15, 4),
               pieces=[(5, 4, p3, 1, 1, 1),
                       (8, 18, [[8, 8, 8], [8, 1, 8], [8, 8, 8]], 1, 5, 4)]),
  ]
  test = [
      generate(size=(30, 30), bg=1, host=(1, 1, 10, 10, 8),
               pieces=[(15, 6, [[2, 2, 2, 3], [2, 3, 2, 3], [2, 2, 2, 3],
                                [3, 3, 3, 3]], 2, 1, 1),
                       (22, 19, [[4, 4, 4, 4], [4, 2, 2, 4], [4, 4, 4, 4]],
                        2, 6, 3)]),
  ]
  return {"train": train, "test": test}
