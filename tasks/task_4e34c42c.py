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

"""ARC task 4e34c42c: glue scattered pieces together along shared connectors.

Rule: the input shows several multicoloured pieces on a background. Each piece
is a rectangular fragment of one hidden assembly. Neighbouring fragments
overlap, and the overlap region (a "connector" motif) is identical on both
fragments. The output is that assembly, cropped to its bounding box. It is
built by translating the pieces, never rotating them, until the shared
connectors coincide. A piece that is only a copy of a connector disappears into
its twin.

Scope of the random generator:
  * Half the random scenes use a procedural 2D tree of fresh 3x3 connector
    motifs. A self-avoiding backbone bends in both axes; extra branches can
    attach to interior nodes or previously added branch nodes. Every edge
    becomes a piece containing its two shared endpoint motifs.
  * A latent assembly is built first. It is a horizontal strip of 3-row motifs
    (rings, plus signs, crosses, H/I shapes, checkers, columns ...), with
    optional horizontal bars between the motifs.
  * Optional vertical branches hang above or below width-3 motifs. Each branch
    is a bar plus an end motif.
  * The whole assembly may be transposed.
  * The strip is cut into 2-4 consecutive pieces that share one motif each.
    Each branch is its own piece and contains its attachment motif.
  * An optional duplicate piece is an isolated copy of one motif.
  * Pieces are scattered without rotation and separated by background.
  * A scene is rejected unless every piece is tight and 8-connected. The
    intended placement must beat every alternative matching translation for
    any subset of other fragments, using overlap area then coloured-cell
    count. Inferior partial matches of a repeated connector are permitted.
  * Strips up to 24 cells long are allowed. Lengths above 22 are a synthetic
    extension beyond the fixture outputs.

Requested counts (num_branches, duplicate) are honoured exactly or the scene is
resampled. Out-of-range controls raise ValueError.
Tree scenes are synthetic topological extensions; rotations are never applied
to individual fragments. Random templates in tree mode are generated from
coloured cells, rather than sampled from the strip mode's finite motif catalog.

The original fixtures are rebuilt from explicit latent pieces. Each piece is
given by its grid, its input position and its assembly offset. Both the input
and the output are rendered from these latents.
"""

import random

import common


_MAX_STRIP = 24

_MOTIFS = (
    ("aaa", "aba", "aaa"),
    (".a.", "aba", ".a."),
    ("a.a", ".b.", "a.a"),
    ("a.a", "aba", "a.a"),
    ("aaa", ".b.", "aaa"),
    ("aba", "bab", "aba"),
    ("aaa", "bbb", "aaa"),
    ("a.a", "a.a", "aba"),
    ("aba", "a.a", "a.a"),
    ("aa", "ab", "aa"),
    ("ab", "ab", "ab"),
    ("a", "b", "a"),
    ("a", "a", "a"),
)


def _motif(pattern, palette, bg):
  a, b = random.sample(palette, 2)
  table = {"a": a, "b": b, ".": bg}
  return [[table[ch] for ch in row] for row in pattern]


def _parse(piece):
  if isinstance(piece, str):
    return [[int(ch) for ch in row] for row in piece.split("|")]
  return [list(row) for row in piece]


def _tight_connected(g, bg):
  h, w = len(g), len(g[0])
  cells = [(r, c) for r in range(h) for c in range(w) if g[r][c] != bg]
  if not cells:
    return False
  if not any(v != bg for v in g[0]) or not any(v != bg for v in g[-1]):
    return False
  if not any(row[0] != bg for row in g) or not any(row[-1] != bg for row in g):
    return False
  seen = {cells[0]}
  stack = [cells[0]]
  while stack:
    r, c = stack.pop()
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != bg:
          if (nr, nc) not in seen:
            seen.add((nr, nc))
            stack.append((nr, nc))
  return len(seen) == len(cells)


def _scene(bg, n_motifs, n_branches, duplicate, transpose):
  """Builds the latent assembly and returns (grids, rects, canvas h, canvas w)."""
  palette = [c for c in range(10) if c != bg]
  motifs = [_motif(random.choice(_MOTIFS), palette, bg)
            for _ in range(n_motifs)]
  gaps = [(random.choice((0, 1, 1, 2, 2, 3, 4)), random.choice((1, 1, 1, 0, 2)),
           random.choice(palette)) for _ in range(n_motifs - 1)]
  width = sum(len(m[0]) for m in motifs) + sum(g[0] for g in gaps)
  if width > _MAX_STRIP:
    return None
  strip = [[bg] * width for _ in range(3)]
  mcols = []
  col = 0
  for i, m in enumerate(motifs):
    w = len(m[0])
    mcols.append(col)
    for r in range(3):
      for x in range(w):
        strip[r][col + x] = m[r][x]
    col += w
    if i < n_motifs - 1:
      length, row, colour = gaps[i]
      for x in range(length):
        strip[row][col + x] = colour
      col += length
  n_main = random.randint(2, min(4, n_motifs - 1))
  cuts = [0] + sorted(random.sample(range(1, n_motifs - 1), n_main - 1))
  cuts.append(n_motifs - 1)
  cands = [i for i in range(n_motifs) if len(motifs[i][0]) == 3]
  if len(cands) < n_branches:
    return None  # honour the requested branch count exactly
  random.shuffle(cands)
  branches = []
  for i in cands[:n_branches]:
    end = _motif(random.choice(_MOTIFS), palette, bg)
    ew = len(end[0])
    eoff = random.randint(0, 1) if ew == 2 else (3 - ew) // 2
    branches.append((i, random.choice((-1, 1)), random.randint(1, 3),
                     random.choice(palette), end, eoff))
  up = max([b[2] + 3 for b in branches if b[1] < 0], default=0)
  down = max([b[2] + 3 for b in branches if b[1] > 0], default=0)
  height = up + 3 + down
  canvas = [[bg] * width for _ in range(height)]
  for r in range(3):
    canvas[up + r] = strip[r][:]
  rects = []
  for j in range(n_main):
    c0 = mcols[cuts[j]]
    c1 = mcols[cuts[j + 1]] + len(motifs[cuts[j + 1]][0])
    rects.append((up, c0, 3, c1 - c0))
  dup_cands = [(up, mcols[i], 3, len(motifs[i][0]))
               for i in range(n_motifs) if len(motifs[i][0]) >= 2]
  for i, d, length, colour, end, eoff in branches:
    c0 = mcols[i]
    ew = len(end[0])
    if d < 0:
      for k in range(length):
        canvas[up - 1 - k][c0 + 1] = colour
      er = up - length - 3
      rects.append((er, c0, length + 6, 3))
    else:
      for k in range(length):
        canvas[up + 3 + k][c0 + 1] = colour
      er = up + 3 + length
      rects.append((up, c0, length + 6, 3))
    for r in range(3):
      for x in range(ew):
        canvas[er + r][c0 + eoff + x] = end[r][x]
    if ew >= 2:
      dup_cands.append((er, c0 + eoff, 3, ew))
  if duplicate:
    if not dup_cands:
      return None  # honour the duplicate request exactly
    rects.append(random.choice(dup_cands))
  if transpose:
    canvas = [list(row) for row in zip(*canvas)]
    rects = [(c, r, w, h) for r, c, h, w in rects]
  grids = [[row[c:c + w] for row in canvas[r:r + h]] for r, c, h, w in rects]
  for g in grids:
    if not _tight_connected(g, bg):
      return None
  return grids, rects, len(canvas), len(canvas[0])

def _tree_scene(bg, n_motifs, n_branches, duplicate, transpose):
  """Latent orthogonal tree whose edge pieces overlap at connector nodes."""
  directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
  nodes = [(0, 0)]
  edges = []

  def available(parent):
    y, x = nodes[parent]
    occupied = set(nodes)
    result = []
    for dy, dx in directions:
      q = (y + dy, x + dx)
      neighbors = {(q[0] + a, q[1] + b) for a, b in directions}
      if q not in occupied and neighbors & occupied == {(y, x)}:
        result.append(q)
    return result

  for i in range(1, n_motifs):
    choices = available(i - 1)
    if not choices:
      return None
    nodes.append(random.choice(choices))
    edges.append((i - 1, i))
  for i in range(n_branches):
    # First branch forks the backbone; later ones may continue an earlier
    # branch as well. This permits more than one bend outside the backbone.
    parents = list(range(1, n_motifs - 1)) + list(range(n_motifs, len(nodes)))
    choices = [(p, q) for p in parents for q in available(p)]
    if not choices:
      return None
    parent, q = random.choice(choices)
    edges.append((parent, len(nodes)))
    nodes.append(q)
  pitch = random.choice((5, 6))
  ymin, xmin = min(y for y, x in nodes), min(x for y, x in nodes)
  positions = [((y - ymin) * pitch, (x - xmin) * pitch) for y, x in nodes]
  height = max(y for y, x in positions) + 3
  width = max(x for y, x in positions) + 3
  if height > 30 or width > 30:
    return None
  palette = [c for c in range(10) if c != bg]
  canvas = common.grid(width, height, bg)
  for y, x in positions:
    colours = random.sample(palette, random.randint(2, 4))
    occupied = {(1, 1), (0, random.randrange(3)), (2, random.randrange(3)),
                (random.randrange(3), 0), (random.randrange(3), 2)}
    occupied.update((r, c) for r in range(3) for c in range(3)
                    if random.random() < 0.35)
    for r, c in sorted(occupied):
      canvas[y + r][x + c] = random.choice(colours)
  rects = []
  for a, b in edges:
    ay, ax = positions[a]
    by, bx = positions[b]
    colour = random.choice(palette)
    if ay == by:
      for x in range(min(ax, bx) + 3, max(ax, bx)):
        canvas[ay + 1][x] = colour
    else:
      for y in range(min(ay, by) + 3, max(ay, by)):
        canvas[y][ax + 1] = colour
    rects.append((min(ay, by), min(ax, bx), abs(by - ay) + 3, abs(bx - ax) + 3))
  if duplicate:
    y, x = random.choice(positions)
    rects.append((y, x, 3, 3))
  if transpose:
    canvas = [list(row) for row in zip(*canvas)]
    rects = [(x, y, w, h) for y, x, h, w in rects]
  grids = [[row[x:x + w] for row in canvas[y:y + h]] for y, x, h, w in rects]
  if not all(_tight_connected(g, bg) for g in grids):
    return None
  return grids, rects, len(canvas), len(canvas[0])


def _unique(grids, rects, bg, ch, cw):
  """True placement strictly dominates alternatives for every partial assembly.

  Each alternative's agreeing overlaps are compared with its true overlaps
  against the same other pieces. True overlap must have at least as much area
  AND at least as many coloured cells, pair by pair. A subset consisting only
  of tied pairs must contain fewer than two coloured matches. Therefore every
  legal alternative (>=2 coloured matches) loses to the intended placement,
  regardless of which agreeing pieces have already been assembled.
  """
  n = len(grids)
  for i in range(n):
    p = grids[i]
    hp, wp = len(p), len(p[0])
    true_scores = {}
    ir, ic = rects[i][:2]
    for j in range(n):
      if i == j:
        continue
      jr, jc, jh, jw = rects[j]
      a0, a1 = max(ir, jr), min(ir + hp, jr + jh)
      b0, b1 = max(ic, jc), min(ic + wp, jc + jw)
      if a0 >= a1 or b0 >= b1:
        true_scores[j] = (0, 0)
      else:
        true_scores[j] = ((a1 - a0) * (b1 - b0),
                          sum(p[y - ir][x - ic] != bg
                              for y in range(a0, a1) for x in range(b0, b1)))
    for r in range(-hp + 1, ch):
      for c in range(-wp + 1, cw):
        if (r, c) == (rects[i][0], rects[i][1]):
          continue
        total = 0
        dominated = True
        tied_colours = 0
        for j in range(n):
          if j == i:
            continue
          qr, qc, qh, qw = rects[j]
          a0, a1 = max(r, qr), min(r + hp, qr + qh)
          b0, b1 = max(c, qc), min(c + wp, qc + qw)
          if a0 >= a1 or b0 >= b1:
            continue
          q = grids[j]
          match = True
          coloured = 0
          for y in range(a0, a1):
            prow, qrow = p[y - r], q[y - qr]
            for x in range(b0, b1):
              v = prow[x - c]
              if v != qrow[x - qc]:
                match = False
                break
              if v != bg:
                coloured += 1
            if not match:
              break
          if match:
            total += coloured
            area = (a1 - a0) * (b1 - b0)
            true_area, true_colours = true_scores[j]
            if area > true_area or coloured > true_colours:
              dominated = False
            if (area, coloured) == (true_area, true_colours):
              tied_colours += coloured
        if total >= 2 and (not dominated or tied_colours >= 2):
          return False
  return True


def _pack(grids, width, height):
  """Scatters pieces with at least one background cell between bounding boxes."""
  total = sum((len(g) + 1) * (len(g[0]) + 1) for g in grids)
  maxh = max(len(g) for g in grids)
  maxw = max(len(g[0]) for g in grids)
  if (width is not None and width < maxw) or (
      height is not None and height < maxh):
    return None
  order = sorted(range(len(grids)),
                 key=lambda i: -len(grids[i]) * len(grids[i][0]))
  for _ in range(20):
    wd = width if width else random.randint(max(maxw + 1, 10), 30)
    ht = height if height else random.randint(max(maxh + 1, 10), 30)
    # Keeps coloured cells well below half the grid so bg stays the mode.
    if wd < maxw or ht < maxh or wd * ht < 2.2 * total:
      continue
    pos = [None] * len(grids)
    boxes = []
    ok = True
    for i in order:
      h, w = len(grids[i]), len(grids[i][0])
      found = False
      for _ in range(300):
        r = random.randint(0, ht - h)
        c = random.randint(0, wd - w)
        if all(r + h < br or br + bh < r or c + w < bc or bc + bw < c
               for br, bc, bh, bw in boxes):
          pos[i] = (r, c)
          boxes.append((r, c, h, w))
          found = True
          break
      if not found:
        ok = False
        break
    if ok:
      return wd, ht, pos
  return None


def _render(bg, width, height, placed):
  if not placed:
    raise ValueError("at least one piece is required")
  input_cells = set()
  assembly = {}
  for g, ir, ic, orow, ocol in placed:
    if not g or not g[0] or any(len(row) != len(g[0]) for row in g):
      raise ValueError("piece grids must be nonempty and rectangular")
    if any(c not in range(10) for row in g for c in row):
      raise ValueError("piece colours must lie in 0..9")
    if not _tight_connected(g, bg):
      raise ValueError("pieces must be tight and connected")
    if ir < 0 or ic < 0 or ir + len(g) > height or ic + len(g[0]) > width:
      raise ValueError("input piece outside the grid")
    occupied = {(ir + y, ic + x) for y, row in enumerate(g)
                for x, v in enumerate(row) if v != bg}
    if any((y + dy, x + dx) in input_cells for y, x in occupied
           for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
      raise ValueError("input pieces overlap or touch")
    input_cells.update(occupied)
    for y, row in enumerate(g):
      for x, v in enumerate(row):
        p = (orow + y, ocol + x)
        if p in assembly and assembly[p] != v:
          raise ValueError("assembly overlaps must agree, including background")
        assembly[p] = v
  inp = common.grid(width, height, bg)
  for g, ir, ic, _, _ in placed:
    for y, row in enumerate(g):
      for x, v in enumerate(row):
        if v != bg:
          inp[ir + y][ic + x] = v
  r0 = min(p[3] for p in placed)
  c0 = min(p[4] for p in placed)
  r1 = max(p[3] + len(p[0]) for p in placed)
  c1 = max(p[4] + len(p[0][0]) for p in placed)
  if r1 - r0 > 30 or c1 - c0 > 30:
    raise ValueError("assembled output exceeds 30 cells per side")
  out = common.grid(c1 - c0, r1 - r0, bg)
  for g, _, _, orow, ocol in placed:
    for y, row in enumerate(g):
      for x, v in enumerate(row):
        if v != bg:
          out[orow - r0 + y][ocol - c0 + x] = v
  return {"input": inp, "output": out}


def generate(bg=None, width=None, height=None, pieces=None, num_motifs=None,
             num_branches=None, duplicate=None, transpose=None, layout=None):
  """Returns an input/output pair.

  Args:
    bg: background colour (0..9).
    width: input grid width in columns (1..30).
    height: input grid height in rows (1..30).
    pieces: optional explicit latent pieces. Each entry is
      (grid, input_row, input_col, assembly_row, assembly_col). The grid is
      either a "digits|digits" string or a list of rows. When this is given,
      bg, width and height are required. The random-scene controls must then
      be left as None.
    num_motifs: number of motifs on the main strip (3..6).
    num_branches: exact number of vertical branch pieces (0..2).
    duplicate: whether to add an isolated copy of one motif.
    transpose: whether to transpose the whole assembly.
    layout: 'strip' or 'tree'. None samples the two layouts equally.
      In tree mode num_motifs counts backbone nodes and num_branches counts
      extra branch edges. Each tree edge is one fragment.
  """
  if width is not None and not 1 <= width <= 30:
    raise ValueError("width must be in 1..30")
  if height is not None and not 1 <= height <= 30:
    raise ValueError("height must be in 1..30")
  if bg is not None and not 0 <= bg <= 9:
    raise ValueError("bg must be in 0..9")
  if pieces is not None:
    if bg is None or width is None or height is None:
      raise ValueError("pieces requires bg, width and height")
    if any(v is not None for v in (num_motifs, num_branches, duplicate,
                                   transpose, layout)):
      raise ValueError("pieces cannot be combined with random-scene controls")
    placed = [(_parse(g), ir, ic, orow, ocol)
              for g, ir, ic, orow, ocol in pieces]
    return _render(bg, width, height, placed)
  if num_motifs is not None and not 3 <= num_motifs <= 6:
    raise ValueError("num_motifs must be in 3..6")
  if num_branches is not None and not 0 <= num_branches <= 2:
    raise ValueError("num_branches must be in 0..2")
  if layout not in (None, 'strip', 'tree'):
    raise ValueError("layout must be strip or tree")
  for _ in range(1000):
    b = bg if bg is not None else random.randint(0, 9)
    nm = num_motifs if num_motifs is not None else random.randint(3, 6)
    nb = num_branches if num_branches is not None else random.choice(
        (0, 0, 1, 1, 2))
    dup = duplicate if duplicate is not None else random.random() < 0.5
    tr = transpose if transpose is not None else random.random() < 0.5
    kind = layout if layout is not None else random.choice(('strip', 'tree'))
    scene = (_scene if kind == 'strip' else _tree_scene)(b, nm, nb, dup, tr)
    if scene is None:
      continue
    grids, rects, ch, cw = scene
    if not _unique(grids, rects, b, ch, cw):
      continue
    packed = _pack(grids, width, height)
    if packed is None:
      continue
    wd, ht, pos = packed
    placed = [(grids[i], pos[i][0], pos[i][1], rects[i][0], rects[i][1])
              for i in range(len(grids))]
    return _render(b, wd, ht, placed)
  raise RuntimeError("could not build a valid scene for the given controls")


def validate():
  """Rebuilds the original fixtures from explicit latent pieces."""
  train = [
      generate(bg=8, width=25, height=23, pieces=[
          ("689|611|614|611|689", 11, 20, 0, 0),
          ("9888888888|1188282333|4111222323|1188282333|9888888888",
           6, 6, 0, 2),
          ("333|323|333", 18, 3, 1, 9)]),
      generate(bg=4, width=20, height=30, pieces=[
          ("111|121|111", 3, 1, 1, 0),
          ("1114444444535|1213333333353|1114444444535", 15, 5, 1, 0),
          ("466644|535668|353668|535668|466644", 23, 2, 0, 10),
          ("4441111|8111331|8441441|8111331|4441111", 1, 10, 0, 15)]),
  ]
  test = [
      generate(bg=3, width=20, height=26, pieces=[
          ("66111133|86133888|66111178|33333888", 1, 2, 0, 11),
          ("333366|399968|393366|393333|111333|171333", 1, 12, 0, 6),
          ("444|343|343|111|161", 10, 1, 1, 0),
          ("178|888|373|373|373|222", 10, 9, 2, 16),
          ("111333111|161333171|383333383|383333383|383333383|"
           "388888883|333232333", 18, 9, 4, 0),
          ("32323|34443|44144|34443", 19, 3, 10, 2)]),
      generate(bg=1, width=20, height=20, pieces=[
          ("222|242|222", 1, 7, 0, 7),
          ("322|121|322", 2, 14, 6, 16),
          ("12221|12421|12221|11311|99399|19991|16161", 5, 0, 0, 6),
          ("44416161888|47488888878|44481118888", 7, 9, 6, 3),
          ("888333|878331|888333", 13, 9, 6, 11),
          ("116444|666474|116444", 15, 1, 6, 0)]),
  ]
  return {"train": train, "test": test}
