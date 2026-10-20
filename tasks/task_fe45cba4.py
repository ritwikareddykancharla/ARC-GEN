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

"""ARC-GEN style generator for task fe45cba4 (plug the piece into its socket).

Rule: sockets sit against the right edge of the grid. A socket is a
rectangle whose top row, bottom row and right column are solid. A notch is
cut from its interior and opens to the left. Some sockets have a loose piece
of the same colour lying further left. The piece is a full-height spine
column with the notch shape attached to its right. In the output, each piece
is erased and translated so that it fills the notch. Its spine becomes a new
column just left of the socket, so the result is a solid rectangle one column
wider than the socket. The moving object is always the leftmost member of a
same-colour pair, and the socket never moves. Unpaired sockets stay unchanged
and act as distractors (like the lone 2 block in train pair 2 and the 9 block
in the test).

Scope: by default, random scenes have 8..20 rows (at least 4k-1 for k
sockets) and 8..20 columns. Explicit height 7..30 and width 8..30 are
synthetic extensions. There are 2..4 right-anchored sockets, each in its own
horizontal band, with blank rows between bands. Each socket is 3..6 tall
(3..7 on grids taller than 20) and 3..(W-2)//2 wide (at most 7, or 8 on
grids wider than 20). Notches grow from the socket's left column and are
often mirrored top to bottom. About a quarter of notches are the whole
interior (the C-shaped socket of the train pairs). A mirrored notch may form
two separate bays (a synthetic extension). Every bay touches the left column,
so the piece stays connected through its spine. At least one socket is
paired. Pieces are packed into disjoint row slots. Their start column is
usually 0..3, as in the fixtures, but on wide grids it can lie further right
(a synthetic extension). Background separates each piece from every other
object (no 8-neighbour contact). No piece cell lies inside any socket's
bounding box or in the column just left of it, so a piece never looks as if
it were already plugged into a foreign socket. The vertical offset between a
piece and its socket varies freely and is often non-zero. Socket colours are
distinct and differ from the background. The background defaults to 7, as in
every example. Every piece has exactly one translation that lands only on
background and completes a rectangle with its socket. The background is
strictly the most frequent colour.

Boundary note: height=7 forces two 3-tall sockets in rows 0..2 and 4..6, and
width=8 forces every socket to be 3 wide. These extreme sizes are nearly
fixed templates where only the notch and the colours vary.

Not supported: sockets anchored to other edges, pieces that are not left of
their socket, same-colour decoys, more than one piece per socket, pieces
side by side in the same rows.
"""

import random

import common

_BG = 7
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _as_int(x, name):
  """Return x as a plain int; reject bools, floats and other non-ints."""
  if isinstance(x, bool) or not isinstance(x, int):
    raise ValueError('%s must be an integer' % name)
  return int(x)


def _as_seq(x, name):
  """Return x as a list, raising ValueError for non-sequences."""
  if isinstance(x, (str, bytes)):
    raise ValueError('%s must be a sequence' % name)
  try:
    return list(x)
  except TypeError:
    raise ValueError('%s must be a sequence' % name) from None


def _components(cells):
  """Return the 4-connected components of a set of cells."""
  todo = set(cells)
  comps = []
  while todo:
    start = todo.pop()
    comp = {start}
    stack = [start]
    while stack:
      r, c = stack.pop()
      for dr, dc in _DIRS:
        n = (r + dr, c + dc)
        if n in todo:
          todo.remove(n)
          comp.add(n)
          stack.append(n)
    comps.append(comp)
  return comps


def _connected(cells):
  return len(_components(cells)) <= 1


def _make_notch(h, w, symmetric, full=False):
  """Random notch inside interior rows 1..h-2 and cols 0..w-2 (relative).

  With full=True the notch is the whole interior, which leaves a C-shaped
  socket (as in both canonical train pairs).
  """
  interior = {(r, c) for r in range(1, h - 1) for c in range(w - 1)}
  if full:
    return sorted(interior)
  whole = {(r, c) for r in range(h) for c in range(w)}
  cap = max(1, (len(interior) * 3) // 5)
  target = random.randint(1, cap)
  notch = set()

  def add(cells):
    trial = notch | cells
    if _connected(whole - trial):
      notch.update(cells)

  seed_r = random.randint(1, h - 2)
  first = {(seed_r, 0)}
  if symmetric:
    first.add((h - 1 - seed_r, 0))
  add(first)
  for _ in range(4 * len(interior) + 20):
    if len(notch) >= target:
      break
    frontier = sorted({(r + dr, c + dc) for (r, c) in notch for dr, dc in _DIRS
                       if (r + dr, c + dc) in interior
                       and (r + dr, c + dc) not in notch})
    if not frontier:
      break
    cell = random.choice(frontier)
    cells = {cell}
    if symmetric:
      cells.add((h - 1 - cell[0], cell[1]))
    add(cells)
  return sorted(notch)


def _notch_ok(h, w, notch):
  """Notch is non-empty, lies in the interior, keeps the socket connected,
  and each of its bays touches the socket's left column."""
  if h < 3 or w < 2:
    return False
  ns = set(notch)
  if not ns:
    return False
  for r, c in ns:
    if not (1 <= r <= h - 2 and 0 <= c <= w - 2):
      return False
  whole = {(r, c) for r in range(h) for c in range(w)}
  if not _connected(whole - ns):
    return False
  for comp in _components(ns):
    if not any(c == 0 for _, c in comp):
      return False
  return True


def _piece_cells(h, notch, pr, pc):
  cells = [(pr + i, pc) for i in range(h)]
  cells += [(pr + dr, pc + 1 + dc) for dr, dc in notch]
  return cells


def _socket_cells(width, r0, h, w, notch):
  c0 = width - w
  ns = set(notch)
  return [(r0 + r, c0 + c) for r in range(h) for c in range(w)
          if (r, c) not in ns]


def _socket_zones(width, sockets):
  """Every socket's bounding box plus the column just left of it.

  For a paired socket this is exactly its target rectangle. Keeping pieces
  out of all zones also stops a piece from sitting in a foreign socket's
  mouth.
  """
  zone = set()
  for r0, h, w, _, _ in sockets:
    for rr in range(r0, r0 + h):
      for cc in range(max(0, width - w - 1), width):
        zone.add((rr, cc))
  return zone


def _gap_ok(cells, hgt, wid, occupied, forbidden):
  """In bounds, outside socket zones, not 8-adjacent to other objects."""
  for r, c in cells:
    if not (0 <= r < hgt and 0 <= c < wid) or (r, c) in forbidden:
      return False
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        if (r + dr, c + dc) in occupied:
          return False
  return True


def _render(height, width, bg, sockets, pieces):
  inp = common.grid(width, height, bg)
  out = common.grid(width, height, bg)
  if len(inp) != height or any(len(row) != width for row in inp):
    raise RuntimeError('unexpected grid orientation')
  for r0, h, w, col, notch in sockets:
    if col == bg:
      raise ValueError('socket colour equals background')
    for r, c in _socket_cells(width, r0, h, w, notch):
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError('socket out of bounds')
      inp[r][c] = col
      out[r][c] = col
  for idx, pr, pc in pieces:
    r0, h, w, col, notch = sockets[idx]
    if width - w - 1 < 0:
      raise ValueError('no room for the spine column')
    for r, c in _piece_cells(h, notch, pr, pc):
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError('piece out of bounds')
      inp[r][c] = col
    for r in range(r0, r0 + h):
      for c in range(width - w - 1, width):
        out[r][c] = col
  return inp, out


def _unique_fit(inp, bg, piece, sock, move):
  """True iff `move` is the only translation completing a rectangle."""
  hh, ww = len(inp), len(inp[0])
  pset, sset = set(piece), set(sock)
  found = []
  for dy in range(-hh, hh):
    for dx in range(-ww, ww):
      if dy == 0 and dx == 0:
        continue
      new = []
      ok = True
      for r, c in piece:
        nr, nc = r + dy, c + dx
        if (not (0 <= nr < hh and 0 <= nc < ww) or (nr, nc) in sset or
            (inp[nr][nc] != bg and (nr, nc) not in pset)):
          ok = False
          break
        new.append((nr, nc))
      if not ok:
        continue
      union = sset | set(new)
      rs = [r for r, _ in union]
      cs = [c for _, c in union]
      area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
      if len(union) == area:
        found.append((dy, dx))
        if len(found) > 1:
          return False
  return found == [move]


def _bg_dominant(inp, bg):
  counts = {}
  for row in inp:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  nbg = counts.get(bg, 0)
  return all(v == bg or n < nbg for v, n in counts.items())


def _scene_ok(inp, bg, sockets, pieces, width):
  if not _bg_dominant(inp, bg):
    return False
  for idx, pr, pc in pieces:
    r0, h, w, _, notch = sockets[idx]
    move = (r0 - pr, width - w - 1 - pc)
    if not _unique_fit(inp, bg, _piece_cells(h, notch, pr, pc),
                       _socket_cells(width, r0, h, w, notch), move):
      return False
  return True


def _check_explicit(height, width, bg, sockets, pieces):
  """Validate explicit latent parameters and return normalised copies."""
  if not (1 <= height <= 30 and 1 <= width <= 30):
    raise ValueError('height and width must be 1..30')
  norm = []
  colours = set()
  for s in _as_seq(sockets, 'sockets'):
    fields = _as_seq(s, 'socket')
    if len(fields) != 5:
      raise ValueError('socket must be (top_row, h, w, colour, notch)')
    r0 = _as_int(fields[0], 'socket top_row')
    h = _as_int(fields[1], 'socket h')
    w = _as_int(fields[2], 'socket w')
    col = _as_int(fields[3], 'socket colour')
    # Bounds first, so huge sizes fail fast before any h*w work.
    if r0 < 0 or h < 3 or w < 2 or r0 + h > height or w > width:
      raise ValueError('socket out of bounds or too small')
    if not 0 <= col <= 9 or col == bg:
      raise ValueError('socket colour must be 0..9 and differ from background')
    if col in colours:
      raise ValueError('socket colours must be distinct')
    colours.add(col)
    raw = _as_seq(fields[4], 'notch')
    if len(raw) > h * w:
      raise ValueError('notch has too many cells')
    cells = set()
    for cell in raw:
      pair = _as_seq(cell, 'notch cell')
      if len(pair) != 2:
        raise ValueError('notch cells must be (dr, dc) pairs')
      cells.add((_as_int(pair[0], 'notch row'), _as_int(pair[1], 'notch col')))
    notch = sorted(cells)
    if not _notch_ok(h, w, notch):
      raise ValueError('invalid notch')
    norm.append((r0, h, w, col, notch))
  spans = sorted((r0, r0 + h - 1) for r0, h, _, _, _ in norm)
  for (_, e1), (s2, _) in zip(spans, spans[1:]):
    if s2 <= e1 + 1:
      raise ValueError('sockets need a blank row between them')
  normp = []
  seen = set()
  for p in _as_seq(pieces, 'pieces'):
    fields = _as_seq(p, 'piece')
    if len(fields) != 3:
      raise ValueError('piece must be (socket_index, spine_top_row, spine_col)')
    idx = _as_int(fields[0], 'piece socket_index')
    pr = _as_int(fields[1], 'piece spine_top_row')
    pc = _as_int(fields[2], 'piece spine_col')
    if not 0 <= idx < len(norm):
      raise ValueError('bad socket index')
    if idx in seen:
      raise ValueError('at most one piece per socket')
    seen.add(idx)
    if norm[idx][2] + 1 > width:
      raise ValueError('no room for the spine column')
    normp.append((idx, pr, pc))
  forbidden = _socket_zones(width, norm)
  occupied = set()
  for r0, h, w, _, notch in norm:
    occupied.update(_socket_cells(width, r0, h, w, notch))
  for idx, pr, pc in normp:
    r0, h, w, _, notch = norm[idx]
    if pc >= width - w:
      raise ValueError('piece must start left of its socket')
    cells = _piece_cells(h, notch, pr, pc)
    if not _gap_ok(cells, height, width, occupied, forbidden):
      raise ValueError('piece out of bounds, inside a socket zone, or '
                       'touching another object')
    occupied.update(cells)
  return norm, normp


def _random_scene(bg, height, width, num_sockets, num_pieces):
  for _ in range(500):
    if num_sockets is not None:
      k = num_sockets
    else:
      cap = 4 if height is None else min(4, (height + 1) // 4)
      choices = [c for c in (2, 2, 2, 3, 3, 4) if c <= cap]
      if num_pieces is not None:
        choices = [c for c in choices if c >= num_pieces]
      k = random.choice(choices)
    if height is not None:
      hgt = height
    else:
      hgt = random.randint(max(8, 4 * k - 1), 20)
    if width is not None:
      wid = width
    elif random.random() < 0.5:
      wid = max(8, hgt)
    else:
      wid = random.randint(8, 20)
    hmax = 6 if hgt <= 20 else 7
    hs = [random.randint(3, hmax) for _ in range(k)]
    while sum(hs) + k - 1 > hgt:
      i = random.choice([j for j in range(k) if hs[j] > 3])
      hs[i] -= 1
    need = sum(hs) + k - 1
    wmax = min(8 if wid > 20 else 7, (wid - 2) // 2)
    ws = [random.randint(3, wmax) for _ in range(k)]
    slots = [0] * (k + 1)
    for _ in range(hgt - need):
      slots[random.randrange(k + 1)] += 1
    rows = []
    r = slots[0]
    for i in range(k):
      rows.append(r)
      r += hs[i] + 1 + slots[i + 1]
    colours = random.sample([c for c in range(10) if c != bg], k)
    sockets = []
    for i in range(k):
      notch = _make_notch(hs[i], ws[i], random.random() < 0.7,
                          random.random() < 0.25)
      sockets.append((rows[i], hs[i], ws[i], colours[i], notch))
    if num_pieces is not None:
      npair = num_pieces
    else:
      npair = random.randint(1, k - 1) if random.random() < 0.8 else k
    paired = random.sample(range(k), npair)
    occupied = set()
    for r0, h, w, col, notch in sockets:
      occupied.update(_socket_cells(wid, r0, h, w, notch))
    # Every socket zone (paired targets and unpaired mouths) is off limits.
    forbidden = _socket_zones(wid, sockets)
    # Pack the pieces into disjoint row slots (random order, random slack).
    slack = hgt - sum(hs[i] for i in paired) - (npair - 1)
    gaps = [0] * (npair + 1)
    for _ in range(slack):
      gaps[random.randrange(npair + 1)] += 1
    pieces = []
    pr = gaps[0]
    ok = True
    for j, idx in enumerate(paired):
      r0, h, w, col, notch = sockets[idx]
      # Spine column: mostly near the left edge (as in the fixtures), but on
      # wide grids sometimes further right, keeping a gap to the target.
      max_pc = max(0, wid - 2 * w - 2)
      lo = min(3, max_pc)
      options = []
      for _ in range(6):
        if random.random() < 0.6:
          options.append(random.randint(0, lo))
        else:
          options.append(random.randint(0, max_pc))
      placed = False
      for pc in options + [0, 1, 2, 3]:
        if pc >= wid - w:
          continue
        cells = _piece_cells(h, notch, pr, pc)
        if _gap_ok(cells, hgt, wid, occupied, forbidden):
          occupied.update(cells)
          pieces.append((idx, pr, pc))
          placed = True
          break
      if not placed:
        ok = False
        break
      pr += h + 1 + gaps[j + 1]
    if not ok:
      continue
    inp, out = _render(hgt, wid, bg, sockets, pieces)
    if _scene_ok(inp, bg, sockets, pieces, wid):
      return inp, out
  raise RuntimeError('failed to build scene')


def generate(height=None, width=None, background=None, sockets=None,
             pieces=None, num_sockets=None, num_pieces=None):
  """Build one input/output pair.

  Args:
    height: grid rows. For random scenes this is optional. The default
      samples 8..20, and explicit values 7..30 are accepted. Required (1..30)
      when sockets are given.
    width: grid columns. For random scenes this is optional. The default
      samples 8..20, and explicit values 8..30 are accepted. Required (1..30)
      when sockets are given.
    background: background colour, 0..9 (default 7).
    sockets: list of (top_row, h, w, colour, notch). Each socket is anchored
      to the right edge, with h >= 3 and w >= 2. notch is a list of (dr, dc)
      cells cut from the socket's bounding box, relative to its top-left
      corner. The cells must lie in rows 1..h-2 and cols 0..w-2, and every
      notch bay must touch column 0. Sockets must be separated by blank rows,
      and their colours must be distinct. At least one socket is required.
    pieces: list of (socket_index, spine_top_row, spine_col), giving where
      each loose piece (spine plus notch shape) lies in the input. Each socket
      can have at most one piece, and at least one piece is required. A piece
      must be separated from every other object and must not enter any
      socket's bounding box or the column just left of it. Only valid
      together with sockets. Invalid or ambiguous explicit scenes raise
      ValueError.
    num_sockets: random scenes only; number of sockets (2..4).
    num_pieces: random scenes only; number of paired sockets (1..num_sockets).
  """
  bg = _BG if background is None else _as_int(background, 'background')
  if not 0 <= bg <= 9:
    raise ValueError('background must be 0..9')
  if height is not None:
    height = _as_int(height, 'height')
  if width is not None:
    width = _as_int(width, 'width')
  if num_sockets is not None:
    num_sockets = _as_int(num_sockets, 'num_sockets')
  if num_pieces is not None:
    num_pieces = _as_int(num_pieces, 'num_pieces')
  if sockets is not None:
    if height is None or width is None:
      raise ValueError('explicit sockets need height and width')
    if num_sockets is not None or num_pieces is not None:
      raise ValueError('num_sockets/num_pieces apply to random scenes only')
    sockets = _as_seq(sockets, 'sockets')
    if not sockets:
      raise ValueError('explicit scenes need at least one socket')
    if pieces is None:
      raise ValueError('explicit scenes need at least one piece')
    pieces = _as_seq(pieces, 'pieces')
    if not pieces:
      raise ValueError('explicit scenes need at least one piece')
    norm, normp = _check_explicit(height, width, bg, sockets, pieces)
    inp, out = _render(height, width, bg, norm, normp)
    if not _scene_ok(inp, bg, norm, normp, width):
      raise ValueError('explicit scene is ambiguous or background not dominant')
    return {'input': inp, 'output': out}
  if pieces is not None:
    raise ValueError('pieces require explicit sockets')
  if height is not None and not 7 <= height <= 30:
    raise ValueError('height must be 7..30')
  if width is not None and not 8 <= width <= 30:
    raise ValueError('width must be 8..30')
  if num_sockets is not None:
    if not 2 <= num_sockets <= 4:
      raise ValueError('num_sockets must be 2..4')
    if height is not None and 4 * num_sockets - 1 > height:
      raise ValueError('height too small for num_sockets')
  if num_pieces is not None:
    kmax = 4 if num_sockets is None else num_sockets
    if height is not None and num_sockets is None:
      kmax = min(kmax, (height + 1) // 4)
    if not 1 <= num_pieces <= kmax:
      raise ValueError('num_pieces must be 1..num_sockets')
  inp, out = _random_scene(bg, height, width, num_sockets, num_pieces)
  return {'input': inp, 'output': out}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  sock9 = [(1, 0)]
  sock2 = [(1, 0), (1, 1), (2, 0), (2, 1)]
  train = [
      generate(height=8, width=8,
               sockets=[(0, 3, 3, 9, sock9), (4, 4, 3, 2, sock2)],
               pieces=[(1, 2, 0)]),
      generate(height=8, width=8,
               sockets=[(0, 3, 3, 9, sock9), (4, 4, 3, 2, sock2)],
               pieces=[(0, 1, 0)]),
  ]
  test = [
      generate(height=16, width=16,
               sockets=[(0, 5, 6, 9, [(1, 0), (2, 0), (2, 1), (3, 0)]),
                        (8, 5, 6, 8, [(1, 0), (1, 2), (2, 0), (2, 1), (2, 2),
                                      (2, 3), (3, 0), (3, 2)])],
               pieces=[(1, 5, 0)]),
  ]
  return {'train': train, 'test': test}
