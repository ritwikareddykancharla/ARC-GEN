"""Batch-7 review probe, read-only. Run from the worktree root with PYTHONPATH=.

Usage: fixture_stats_batch7.py [N] [SEED] [--timing]

Prints the measurements quoted in the batch-7 semantic reviews. Nothing is
written. Constructors are only called. Their latent canonical arguments are
captured by wrapping the module's generate() while validate() runs; the
wrapper is removed afterwards. Certified programs come from the production
lookups (certified_factory_source / certified_source, d4 = 0, identity
palette), which return None unless every recorded hash is current. Every
section reseeds from SEED plus a fixed offset, so the output (without
--timing) is byte-identical between runs.

Sections
  S. self-tests of the derived checkers used in section A, on native draws
     (every native case must pass) and on hand-made negatives (must fail).
  A. canonical fixtures against native sampler guards, for all 32 families:
     the captured latent canonical parameters (or the canonical grids) are
     compared with the ranges and grammar of the random path. "UNREACHABLE"
     means a canonical input violates a constraint that the random path
     always enforces; it does not mean the fixture is wrong.
  B. N seeded native draws per family (985ae207: N_SLOW draws, each bounded
     by a per-draw deadline): valid/timeout/error counts, unique inputs,
     distinct shapes, the largest same-shape group, agreement of
     runtime.verification_solver (the check prepare.py applies to every
     native pair) and of the certified program, the canonical episode shape
     profile, and family-specific statistics.
  C. certified programs and archived verifiers on widened scenes: the
     constructor is driven through its explicit-parameter path past its
     literal caps and its output is the reference. A pass is evidence of
     program support, not a certificate or a statement of intended scope.
  D. exact finite native domains where the domain is small enough to count.
  --timing: per-draw wall time (not reproducible; excluded from comparisons).
"""
import collections
import itertools
import math
import random
import statistics
import sys
import time

sys.path.insert(0, '.')
import common  # noqa: E402
from arc_agi2 import runtime  # noqa: E402
from arc_agi2.direct_certificates import (certified_factory_source,  # noqa: E402
                                          certified_source)
from arc_agi2.episode_shape_policy import profile_from_task  # noqa: E402

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
N = int(ARGS[0]) if ARGS else 200
SEED = int(ARGS[1]) if len(ARGS) > 1 else 0
TIMING = '--timing' in sys.argv
ID = list(range(10))
N_SLOW = 12          # native draws for 985ae207 (whole-scene rejection sampler)
SLOW_LIMIT = 20      # seconds per 985ae207 draw
DRAW_LIMIT = 10      # seconds per draw for every other family
C_N = 100            # widened scenes per family in section C

IDS = ['817e6c09', 'c1990cce', '98c475bf', '456873bc', '458e3a53', '470c91de',
       '52fd389e', '5783df64', '5ecac7f7', '758abdf0', '762cd429', '7d7772cc',
       '8fbca751', '981add89', '985ae207', 'c8b7cc0f', 'df9fd884', 'e9ac8c9e',
       'ef26cbf6', '17b866bd', '1e5d6875', '25e02866', '2601afb7', '2e65ae53',
       '42a15761', '48131b3c', '5751f35e', '7491f3cf', '963c33f8', '973e499e',
       '9968a131', '9ddd00f0']


def section(offset):
  random.seed(SEED * 1000 + offset)


def mod(tid):
  return __import__(f'tasks.task_{tid}', fromlist=['generate'])


def canon(tid):
  c = runtime.reference(tid)['canonical']
  return c['train'] + c['test']


def key(g):
  return tuple(map(tuple, g))


def captured(tid):
  """kwargs of every generate() call made by validate(), in order."""
  m = mod(tid)
  orig = m.generate
  calls = []

  def wrap(*a, **k):
    assert not a, 'positional generate() arguments are not expected'
    calls.append(dict(k))
    return orig(*a, **k)

  m.generate = wrap
  try:
    m.validate()
  finally:
    m.generate = orig
  return calls


def program(tid):
  src = certified_factory_source(tid, 0, ID)
  kind = 'direct_factory'
  if src is None:
    src = certified_source(tid)
    kind = 'direct_certificate'
  if src is None:
    return None, 'none'
  ns = {}
  exec(src, ns)
  return (lambda g, demos=(): [list(map(int, r)) for r in ns['solve'](list(demos), g)]), kind


def adj8(a, b):
  return max(abs(a[0] - b[0]), abs(a[1] - b[1])) <= 1


def comps(cells, eight=True):
  cells = set(cells)
  out = []
  nb = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a or b) and (eight or not (a and b))]
  while cells:
    s = cells.pop()
    st, comp = [s], [s]
    while st:
      r, c = st.pop()
      for a, b in nb:
        q = (r + a, c + b)
        if q in cells:
          cells.remove(q)
          st.append(q)
          comp.append(q)
    out.append(sorted(comp))
  return out


def show(tid, msg):
  print(f'  {tid}: {msg}')


def verdict(tid, results):
  """results: list of (label, [violations])."""
  bad = [(lab, v) for lab, v in results if v]
  if not bad:
    show(tid, f'all {len(results)} canonical pairs inside the random path')
    return
  show(tid, f'UNREACHABLE {len(bad)}/{len(results)} canonical pairs')
  for lab, v in bad:
    print(f'      {lab}: ' + '; '.join(v))


def labels(tid):
  c = runtime.reference(tid)['canonical']
  return [f'train[{i}]' for i in range(len(c['train']))] + [f'test[{i}]' for i in range(len(c['test']))]


# ------------------------------------------------------------- derived checkers

def _gale_ryser(r, s):
  """A 0/1 matrix with row sums r and column sums s exists."""
  if sum(r) != sum(s):
    return False
  rs = sorted(r, reverse=True)
  for k in range(1, len(rs) + 1):
    if sum(rs[:k]) > sum(min(x, k) for x in s):
      return False
  return True


def _flow_feasible(n, cells, r2, s2):
  """Nonnegative integers on `cells` with row sums r2 and column sums s2."""
  if sum(r2) != sum(s2):
    return False
  total = sum(r2)
  if total == 0:
    return True
  # Max flow: source -> rows (r2), rows -> cols (cells, inf), cols -> sink (s2).
  size = 2 * n + 2
  src, snk = 2 * n, 2 * n + 1
  cap = [[0] * size for _ in range(size)]
  for i in range(n):
    cap[src][i] = r2[i]
    cap[n + i][snk] = s2[i]
  for r, c in cells:
    cap[r][n + c] = total
  flow = 0
  while True:
    prev = [-1] * size
    prev[src] = src
    queue = [src]
    while queue and prev[snk] < 0:
      u = queue.pop(0)
      for v in range(size):
        if prev[v] < 0 and cap[u][v] > 0:
          prev[v] = u
          queue.append(v)
    if prev[snk] < 0:
      break
    aug, v = total, snk
    while v != src:
      aug = min(aug, cap[prev[v]][v])
      v = prev[v]
    v = snk
    while v != src:
      cap[prev[v]][v] -= aug
      cap[v][prev[v]] += aug
      v = prev[v]
    flow += aug
  return flow == total


def conway_reachable(cells, n, tries=5):
  """Exact test: common.conway_sprite(n, n, tries) can return this cell set.

  conway_sprite deletes at most `tries` cells from the full n x n grid
  (never the last cell of a row or column), then shuffles the row list and
  the column list independently. The result is a pairing of the row and
  column multisets of a 0/1 matrix S (|S| >= n*n - tries, every row and
  column non-empty). A distinct-cell set T is reachable iff positive
  multiplicities on T exist whose row/column sums are the margins of such
  an S. Margins are enumerated; feasibility is Gale-Ryser plus a max flow.
  """
  cells = set(cells)
  if not cells or any(not (0 <= r < n and 0 <= c < n) for r, c in cells):
    return False
  rc = [sum(1 for r, _ in cells if r == i) for i in range(n)]
  cc = [sum(1 for _, c in cells if c == j) for j in range(n)]
  if min(rc) == 0 or min(cc) == 0:
    return False
  lo = n * n - tries
  rows_opts = [range(rc[i], n + 1) for i in range(n)]
  cols_opts = [range(cc[j], n + 1) for j in range(n)]
  cols_by_sum = collections.defaultdict(list)
  for s in itertools.product(*cols_opts):
    cols_by_sum[sum(s)].append(s)
  for r in itertools.product(*rows_opts):
    e = sum(r)
    if e < lo:
      continue
    for s in cols_by_sum.get(e, []):
      if not _gale_ryser(r, s):
        continue
      if _flow_feasible(n, cells, [r[i] - rc[i] for i in range(n)],
                        [s[j] - cc[j] for j in range(n)]):
        return True
  return False


def mask_cells(colors, n):
  return {(i // n, i % n) for i, v in enumerate(colors) if v}


def margins(cells, n):
  return ([sum(1 for r, _ in cells if r == i) for i in range(n)],
          [sum(1 for _, c in cells if c == j) for j in range(n)])


def group_cells(k, g):
  return {(r, c) for r, c, gg in zip(k['rows'], k['cols'], k['groups']) if gg == g}


def wall_grammar_7491(n):
  """Every wall the 7491f3cf random path can draw at panel size n."""
  walls = set()

  def variants(cells):
    out = set()
    for xp in (0, 1):
      for fl in (0, 1):
        cs = cells
        if xp:
          cs = {(c, r) for r, c in cs}
        if fl:
          cs = {(r, n - 1 - c) for r, c in cs}
        out.add(frozenset(cs))
    return out

  for k in range(1, n - 1):
    walls |= variants({(k, c) for c in range(n)})
  walls |= variants({(i, i) for i in range(n)})
  for r in range(1, n - 1):
    for c in range(1, n - 1):
      for rows in (range(0, r + 1), range(r, n)):
        for cols in (range(0, c + 1), range(c, n)):
          walls |= variants({(i, c) for i in rows} | {(r, j) for j in cols})

  def paths(row, col, acc):
    if row == n:
      yield set(acc)
      return
    for d in (-1, 0, 1):
      if 0 <= col + d < n:
        yield from paths(row + 1, col + d, acc + [(row, col + d)])

  for col in range(n):
    for p in paths(1, col, [(0, col)]):
      walls |= variants(p)
  return walls


def _panel_reasons_5ecac7f7(g, size, c0, ws):
  """Guard violations of one panel split into pieces of widths ws."""
  allowed = {0, 1, 2, 3, 4, 5, 8, 9}
  wmax = 2 if size == 5 else 3
  why, colours, start = [], [], c0
  for idx, w in enumerate(ws):
    if w > wmax:
      why.append(f'piece {idx} width {w} > {wmax} (line 33)')
    cells = [(r, c - start) for r in range(size) for c in range(start, start + w) if g[r][c] != 7]
    vals = {g[r][start + c] for r, c in cells}
    if len(vals) != 1:
      why.append(f'piece {idx} has colours {sorted(vals)} (one colour per piece, line 60)')
    elif not vals <= allowed:
      why.append(f'piece {idx} colour {sorted(vals)} outside [0,1,2,3,4,5,8,9] (line 53)')
    if not 1 <= len(cells) <= size * w - 1:
      why.append(f'piece {idx} fills {len(cells)}/{size * w} cells (never full, line 64)')
    cols = {c for _, c in cells}
    if idx == 0 and w - 1 not in cols:
      why.append('piece 0 misses its last column (line 66)')
    if idx == 1 and len(cols) != w:
      why.append('piece 1 misses a column (line 67)')
    if idx == 2 and 0 not in cols:
      why.append('piece 2 misses its first column (line 68)')
    if cells and not common.connected(sorted(cells)):
      why.append(f'piece {idx} not 4-connected (line 69)')
    colours.append(sorted(vals)[0] if len(vals) == 1 else None)
    start += w
  if colours[0] is not None and colours[1] is not None and colours[2] is not None and \
      (colours[0] == colours[1] or colours[1] == colours[2]):
    why.append('adjacent pieces share a colour (line 54)')
  return why


def nearest_miss_5ecac7f7(g, size):
  """Per panel: the width triple with the fewest guard violations, and those violations."""
  out = []
  for p in range(3):
    c0 = p * (size + 1)
    best = None
    for ws in itertools.product(range(1, size - 1), repeat=3):
      if sum(ws) != size:
        continue
      why = _panel_reasons_5ecac7f7(g, size, c0, ws)
      if best is None or len(why) < len(best[1]):
        best = (ws, why)
    out.append(best)
  return out


def subfigures_5ecac7f7(g, size, color_map):
  """Width triples per panel that the 5ecac7f7 random path could have drawn.

  Returns the list of 9-width assignments consistent with every per-piece
  guard (monochrome, allowed colour, not full, 4-connected, column cover,
  adjacent colours distinct) and with the canonical colour map.
  """
  wmax = 2 if size == 5 else 3
  panels = []
  for p in range(3):
    c0 = p * (size + 1)
    opts = [ws for ws in itertools.product(range(1, wmax + 1), repeat=3)
            if sum(ws) == size and not _panel_reasons_5ecac7f7(g, size, c0, ws)]
    panels.append(opts)
  out = []
  for a in panels[0]:
    for b in panels[1]:
      for c in panels[2]:
        w = list(a) + list(b) + list(c)
        if w[0] + w[4] + w[8] != size:
          continue
        cm = [x for x in range(w[0])]
        cm += [size + 1 + w[3] + x for x in range(w[4])]
        cm += [2 * (size + 1) + w[6] + w[7] + x for x in range(w[8])]
        if cm == list(color_map):
          out.append(w)
  return out


def radii_5751(g):
  size = len(g)
  half = size // 2
  radii = [0] * half
  for row in range(size):
    for col in range(size):
      r = (half - 1 - row) if row < half else (row - half)
      c = (half - 1 - col) if col < half else (col - half)
      if g[row][col]:
        radii[max(r, c)] = g[row][col]
  return radii


def thue_grammar_7d77(thues, size):
  """thues, up to trailing -1 entries, is a sequence the 7d7772cc hue loop can emit.

  Trailing -1 entries draw nothing (line 67), so a sequence that differs only
  by them gives the same grids; up to two are appended before testing.
  """
  return any(_thue_exact(list(thues) + [-1] * pad, size) for pad in range(3))


def _thue_exact(thues, size):
  spacing = 1 if size == 16 else 0
  i, col = 0, 1
  while True:
    if i >= len(thues) or thues[i] == -1:
      return False
    i += 1
    col += 1
    if col + 1 >= size:
      break
    if spacing:
      if i >= len(thues) or thues[i] != -1:
        return False
      i += 1
      col += 1
    if col + 1 >= size:
      break
    if i < len(thues) and thues[i] == -1:
      i += 1
      col += 1
    if col + 1 >= size:
      break
  return i == len(thues)


# =================================================== S. checker self-tests
print('== S. self-tests of derived checkers (native draws must pass, negatives must fail)')
section(1)
for n in (3, 4):
  draws = [set(zip(*common.conway_sprite(n, n))) for _ in range(300)]
  ok = sum(conway_reachable(d, n) for d in draws)
  neg = [{(r, c) for r in range(1, n) for c in range(n)},            # misses row 0
         {(r, c) for r in range(n) for c in range(n - 1)}]           # misses last column
  print(f'  conway_reachable n={n}: native {ok}/300 accepted; '
        f'row/column-missing negatives accepted {sum(conway_reachable(x, n) for x in neg)}/2')
# Low tail: native sprites with few distinct cells need repeated pairings, which is
# where an over-strict checker would first reject a reachable set.
section(6)
tail = [set(zip(*common.conway_sprite(4, 4))) for _ in range(20000)]
low = [t for t in tail if len(t) <= 6] + [t for t in tail if len(t) == 7][:200]
print(f'  conway_reachable n=4 low tail: native sprites with <= 7 distinct cells '
      f'{sum(conway_reachable(t, 4) for t in low)}/{len(low)} accepted')
walls5 = wall_grammar_7491(5)
section(2)
m7491 = mod('7491f3cf')
wall_hits = 0
for _ in range(200):
  wall_hits += frozenset(m7491._sample_line(5)) in walls5
print(f'  7491f3cf wall grammar (n=5, {len(walls5)} walls): native _sample_line {wall_hits}/200 recognised')
section(3)
m5e = mod('5ecac7f7')
dec_ok = 0
for _ in range(200):
  p = m5e.generate()
  g = p['input']
  size = len(g)
  # recover the colour map from the native output (first column match per output column)
  cm = []
  for c in range(size):
    col = [p['output'][r][c] for r in range(size)]
    cands = [x for x in range(len(g[0])) if [g[r][x] for r in range(size)] == col]
    cm.append(cands)
  ok = False
  for choice in itertools.product(*cm):
    if subfigures_5ecac7f7(g, size, choice):
      ok = True
      break
  dec_ok += ok
print(f'  5ecac7f7 sub-figure decoder: native {dec_ok}/200 decoded inside the guards')
section(4)
m57 = mod('5751f35e')
rad_ok = 0
for _ in range(200):
  p = m57.generate()
  r = radii_5751(p['input'])
  runs = [len(list(gr)) for _, gr in itertools.groupby(r)]
  rad_ok += len(runs) == 3 and all(1 <= x <= 3 for x in runs)
print(f'  5751f35e ring inference: native {rad_ok}/200 give 3 runs of length 1..3')
section(5)
m7d = mod('7d7772cc')
gram_ok = 0
orig = m7d.generate
for _ in range(200):
  # Draw natively, then replay the constructor's draws (lines 29-59, same order and RNG
  # state) to recover the latent hues, and check the explicit path reproduces the pair.
  st = random.getstate()
  p = orig()
  random.setstate(st)
  spacing = common.randint(0, 1)
  size = 8 * (spacing + 1)
  mrow = common.randint(1, size // 2)
  lrow = common.randint(mrow + 1, size - 3)
  colors = common.shuffle(list(range(10)))
  tcolor = colors.pop()
  bcolor = tcolor if common.randint(0, 2) else colors.pop()
  fcolor = colors.pop()
  num_colors = common.randint(3, 5)
  while len(colors) > num_colors:
    colors.pop()
  while True:
    col, thues, bhues, sames = 1, [], [], []
    while True:
      thues.append(common.choice(colors))
      bhues.append(thues[-1] if common.randint(0, 1) else common.choice(colors))
      sames.append(thues[-1] == bhues[-1])
      col += 1
      if col + 1 >= size:
        break
      if spacing:
        thues.append(-1)
        bhues.append(-1)
        col += 1
      if col + 1 >= size:
        break
      if common.randint(0, 9) == 0:
        thues.append(-1)
        bhues.append(-1)
        col += 1
      if col + 1 >= size:
        break
    if True in sames and False in sames:
      break
  flip, xpose = common.randint(0, 1), common.randint(0, 1)
  replay = orig(size=size, tcolor=tcolor, bcolor=bcolor, fcolor=fcolor, lrow=lrow, mrow=mrow,
                flip=flip, xpose=xpose, thues=thues, bhues=bhues)
  gram_ok += replay == p and thue_grammar_7d77(thues, size)
print(f'  7d7772cc hue grammar: {gram_ok}/200 native draws replayed exactly and accepted')


# ======================================================== A. canonical guards
print()
print('== A. canonical fixtures against native guards')
section(10)
CAP = {tid: captured(tid) for tid in IDS}


def a_817(k, i):
  v = []
  w, rows, cols = k['width'], k['rows'], k['cols']
  if not 5 <= w <= 17:
    v.append(f'width {w} outside 5..17 (line 30)')
  if cols[0] not in (0, 1):
    v.append(f'first column {cols[0]} outside 0..1 (line 32)')
  if any(not 0 <= r <= 5 for r in rows):
    v.append('row outside 0..5')
  last = 2
  for j in range(1, len(cols)):
    sp = cols[j] - cols[j - 1]
    if not (1 if last > 1 else 2) <= sp <= 3:
      v.append(f'spacing {sp} after {last} (line 38)')
    pr, r = rows[j - 1], rows[j]
    if r == pr or (sp == 2 and abs(r - pr) <= 1) or (sp == 1 and abs(r - pr) <= 2):
      v.append(f'block {j} row {r} after {pr} at spacing {sp} (lines 43-45)')
    last = sp
  if cols[-1] + 2 != w:
    v.append('last block does not end at the right wall (line 47)')
  return v


def a_c19(k, i):
  w = k['width']
  return [] if w % 2 == 1 and 5 <= w <= 29 else [f'width {w}']


def a_98c(k, i):
  m = mod('98c475bf')
  v = []
  if not 12 <= k['height'] <= 30:
    v.append('height')
  mk = k['markers']
  if len(mk) not in m.SAMPLED_COUNTS:
    v.append(f'{len(mk)} markers not in the sampled counts {sorted(set(m.SAMPLED_COUNTS))}')
  cols = [c for _, c in mk]
  if len(set(cols)) != len(cols) or k['line_color'] in cols or k['border'] in cols + [k['line_color']]:
    v.append('colour roles collide')
  iv = []
  for r, c in mk:
    a, b = m._footprint(r, c)
    if a < 0 or b >= k['height'] or not m._separated(a, b, iv):
      v.append('marker motifs not separated / do not fit')
    iv.append((a, b))
  if m._covers_marker(k['line_row'], k['line_color'], mk):
    v.append('input motif covers a marker row')
  return v


def a_456(k, i):
  v = []
  n = k['size']
  if n not in (3, 4):
    v.append(f'size {n} outside 3..4 (line 31)')
  cells = mask_cells(k['colors'], n)
  if not conway_reachable(cells, n):
    rr, cc = margins(cells, n)
    v.append(f'{len(cells)}-cell sprite (row counts {rr}, column counts {cc}) not reachable by '
             f'conway_sprite({n},{n}) (common.py 120-145)')
  return v


def a_458(k, i):
  v = []
  cs = k['cell_size']
  copies = 10 - cs
  if not 3 <= cs <= 6:
    v.append('cell size')
  if not (2 <= k['width'] <= 3 and 2 <= k['height'] <= 3):
    v.append('output size outside 2..3 (line 41)')
  if not (0 <= k['brow'] <= copies - k['height'] and 0 <= k['bcol'] <= copies - k['width']):
    v.append('block position')
  if not 0 <= k['offset'] <= 10:
    v.append('offset')
  p = k['pattern']
  if len(p) != 6 or len(set(p)) != 6 or k['line_color'] in p:
    v.append('pattern')
  if k['line_color'] in k['colors']:
    v.append('a cell uses the line colour')
  return v


def a_470(k, i):
  v = []
  n = len(k['wides'])
  if k['size'] not in (10, 11):
    v.append(f'size {k["size"]} outside 10..11')
  if not 2 <= n <= 4:
    v.append('box count')
  if any(not 2 <= x <= 5 for x in k['wides'] + k['talls']):
    v.append('box side outside 2..5')
  cs = k['colors']
  if len(set(cs)) != len(cs) or any(c in (0, 7, 8) for c in cs):
    v.append('colours not distinct non-7/8 (line 65)')
  return v


def a_52f(k, i):
  v = []
  n = len(k['wides'])
  counts = [k['pboxes'].count(b) for b in range(n)]
  size = k['size']
  if (n, size) not in ((2, 25), (3, 29)):
    v.append(f'{n} boxes on {size}x{size} (lines 37-38 tie 2->25, 3->29)')
  cs = k['colors']
  if len(set(cs)) != n or any(c not in (1, 2, 3, 6, 8) for c in cs):
    v.append('colours')
  if len(set(counts)) != n or any(not 1 <= c <= 4 for c in counts):
    v.append(f'pixel counts {counts}: native samples distinct counts from 1..4 (line 42)')
  for name in ('wides', 'talls'):
    xs = k[name]
    if len(set(xs)) != n or any(not 3 <= x <= 10 for x in xs):
      v.append(f'{name} {xs}: native samples distinct values from 3..10 (lines 43-44)')
  order = sorted(range(n), key=lambda b: counts[b])
  for name in ('wides', 'talls'):
    xs = [k[name][b] for b in order]
    if xs != sorted(xs) or len(set(xs)) != n:
      v.append(f'{name} not co-sorted with pixel counts (lines 42-45 zip sorted lists)')
  ex = []
  for b in range(n):
    c = counts[b]
    ex.append((k['brows'][b] - c, k['bcols'][b] - c, k['wides'][b] + 2 * c, k['talls'][b] + 2 * c))
  if any(r < 0 or c < 0 or r + t > size or c + w > size for r, c, w, t in ex):
    v.append('expanded box leaves the canvas')
  if common.overlaps([e[0] for e in ex], [e[1] for e in ex], [e[2] for e in ex], [e[3] for e in ex], 1):
    v.append('expanded boxes overlap')
  for b in range(n):
    px = [(r, c) for r, c, pb in zip(k['prows'], k['pcols'], k['pboxes']) if pb == b]
    if any(not (1 <= r <= k['talls'][b] - 2 and 1 <= c <= k['wides'][b] - 2) for r, c in px):
      v.append('pixel on box edge')
    if any(adj8(a, bb) for a, bb in itertools.combinations(px, 2)):
      v.append('pixels 8-adjacent')
  return v


def a_578(k, i):
  v = []
  size = k['size']
  if size not in (6, 9):
    v.append('size')
  base = size // 3
  for j, (r, c) in enumerate(zip(k['rows'], k['cols'])):
    if not (base * (j // 3) <= r < base * (j // 3 + 1) and base * (j % 3) <= c < base * (j % 3 + 1)):
      v.append(f'pixel {j} outside its block')
  if sorted(k['colors']) != list(range(1, 10)):
    v.append('colours not a permutation of 1..9')
  return v


def a_5ec(k, i):
  g = canon('5ecac7f7')[i]['input']
  size = k['size']
  v = []
  if size not in (5, 6):
    v.append('size')
  sols = subfigures_5ecac7f7(g, size, k['color_map'])
  if not sols:
    cm = k['color_map']
    wmax = 2 if size == 5 else 3
    picked = [sum(1 for x in cm if p * (size + 1) <= x < p * (size + 1) + size) for p in range(3)]
    if max(picked) > wmax:
      v.append(f'colour map takes piece widths {picked}; size {size} caps widths at {wmax} (line 33)')
    for p, (ws, why) in enumerate(nearest_miss_5ecac7f7(g, size)):
      if why:
        v.append(f'panel {p} nearest split {list(ws)}: ' + ', '.join(why))
    if not v:
      v.append('every panel splits inside the guards, but no split matches the colour map')
  return v


def a_758(k, i):
  ls = k['lengths']
  v = []
  if len(ls) != 16 or any(x not in (0, 1, 2) for x in ls):
    v.append('lengths')
  if any(a and b for a, b in zip(ls, ls[1:])):
    v.append('consecutive stubs')
  return v


def a_762(k, i):
  return [] if k['copies'] in (3, 4) and all(1 <= c <= 9 for c in k['colors']) else ['copies/colours']


def a_7d7(k, i):
  v = []
  size = k['size']
  if size not in (8, 16):
    v.append('size')
  if not 1 <= k['mrow'] <= size // 2 or not k['mrow'] + 1 <= k['lrow'] <= size - 3:
    v.append('rows')
  hues = [h for h in k['thues'] + k['bhues'] if h != -1]
  if k['fcolor'] in (k['tcolor'], k['bcolor']) or set(hues) & {k['tcolor'], k['bcolor'], k['fcolor']}:
    v.append('colour roles collide')
  if len(set(hues)) > 5:
    v.append('more than 5 hues')
  if not thue_grammar_7d77(k['thues'], size) or [h == -1 for h in k['thues']] != [h == -1 for h in k['bhues']]:
    v.append('hue sequence outside the loop grammar')
  sames = [a == b for a, b in zip(k['thues'], k['bhues']) if a != -1]
  if not (True in sames and False in sames):
    v.append('needs both same and different hue pairs')
  return v


def a_8fb(k, i):
  v = []
  n = len(k['brows'])
  if (k['width'], k['height']) == (7, 7):
    if n != 1 or not (1 <= k['brows'][0] <= 2 and 1 <= k['bcols'][0] <= 2):
      v.append('7x7 layout')
  elif (k['width'], k['height']) == (12, 8):
    lattice = {(0, 0), (0, 4), (0, 8), (4, 0), (4, 4), (4, 8)}
    pos = list(zip(k['brows'], k['bcols']))
    if n != 3:
      v.append(f'{n} boxes on 12x8: native always samples 3 lattice cells (line 43)')
    if not set(pos) <= lattice or len(set(pos)) != n:
      v.append('box positions off the lattice')
  else:
    v.append('canvas')
  for g in range(n):
    cells = group_cells(k, g)
    if not conway_reachable(cells, 4):
      rr, cc = margins(cells, 4)
      v.append(f'sprite {g} ({len(cells)} cells, row counts {rr}, column counts {cc}) not reachable '
               f'by conway_sprite(4,4) (common.py 120-145)')
  return v


def a_981(k, i):
  v = []
  size, n = k['size'], len(k['wides'])
  if size not in (20, 30) or not ((size == 20 and 1 <= n <= 3) or (size == 30 and 4 <= n <= 6)):
    v.append(f'{n} boxes on {size}')
  for w, t, r, c in zip(k['wides'], k['talls'], k['brows'], k['bcols']):
    if not (5 <= w <= size - 10 and 5 <= t <= size - 10):
      v.append(f'box {w}x{t} outside 5..{size - 10}')
    if not (1 <= r <= size - t - 1 and 0 <= c <= size - w):
      v.append('box position')
  bg = k['bgcolor']
  if bg in k['bcolors'] or bg in k['pcolors']:
    v.append('background reused')
  pc = k['pcols']
  if not 2 <= pc[0] <= 5 or any(not 3 <= b - a <= 7 for a, b in zip(pc, pc[1:])) or pc[-1] >= size - 1 \
      or pc[-1] + 7 < size - 1:
    v.append(f'marker columns {pc} outside the start 2..5 / step 3..7 walk (lines 60-63)')
  return v


def a_985(k, i):
  v = []
  size, nb, npx = k['size'], len(k['wides']), len(k['prows'])
  if (size == 20 and nb not in (2, 3)) or (size == 25 and nb != 4) or size not in (20, 25):
    v.append(f'{nb} boxes on {size}')
  if npx not in (nb, nb + 1):
    v.append('pixel count')
  for w, t in zip(k['wides'], k['talls']):
    s, l = min(w, t), max(w, t)
    if not (2 <= s <= 4 and 5 <= l <= 18):
      v.append(f'box {w}x{t} outside short 2..4 / long 5..18')
  if any(not 2 <= x <= size - 3 for x in k['prows'] + k['pcols']):
    v.append('pixel position')
  if set(k['pcolors']) != set(k['bcolors']):
    v.append('pixel colours do not cover the boxes')
  if k['fcolor'] == 8 or len(set(k['bcolors'])) != nb or set(k['bcolors']) & {8, k['fcolor']}:
    v.append('colours')
  rows = k['brows'] + [r - 1 for r in k['prows']]
  cols = k['bcols'] + [c - 1 for c in k['pcols']]
  if common.overlaps(rows, cols, k['wides'] + [3] * npx, k['talls'] + [3] * npx, 1):
    v.append('boxes/frames closer than one cell')
  return v


def a_c8b(k, i):
  v = []
  size = k['size']
  if size not in (7, 9):
    v.append('size')
  if not 4 <= k['wide'] <= size - 2:
    v.append(f'rectangle width {k["wide"]} outside 4..{size - 2} (line 56)')
  if not 4 <= k['tall'] <= size - 2:
    v.append(f'rectangle height {k["tall"]} outside 4..{size - 2} (line 56)')
  if k['color'] == 1:
    v.append('colour')
  g = canon('c8b7cc0f')[i]['input']
  cnt = sum(g[r][c] == k['color'] for r in range(k['brow'] + 1, k['brow'] + k['tall'] - 1)
            for c in range(k['bcol'] + 1, k['bcol'] + k['wide'] - 1))
  if not 3 <= cnt <= 6:
    v.append(f'count {cnt}')
  return v


def a_df9(k, i):
  v = []
  wide = k['wide']
  size = 7 + wide
  if wide not in (1, 2):
    v.append('wide')
  if not 1 <= k['brow'] <= size - 6:
    v.append('brow')
  b = k['bcols']
  if any(not 0 <= x <= size - 2 - wide for x in b) or not b[0] + wide + 2 < b[1]:
    v.append('portal columns')
  cs = k['colors']
  hues = {c for c in cs if c}
  if len(hues) != 1 or hues & {4, 7}:
    v.append('colour')
  zeros = {j for j, c in enumerate(cs) if not c}
  ok = zeros in ([set(), {0}, {0, 1}] if wide == 1 else
                 [z | t for z in (set(), {4}, {5}) for t in (set(), {0}, {1}, {0, 1})])
  if not ok:
    v.append(f'cut-off cells {sorted(zeros)}')
  return v


def a_e9a(k, i):
  v = []
  size, ws = k['size'], k['widths']
  if not ((size == 10 and len(ws) == 1 and ws[0] in (2, 4, 6)) or (size == 15 and ws == [6, 2, 4])):
    v.append(f'size {size} widths {ws}')
  for w, r, c in zip(ws, k['rows'], k['cols']):
    if not (1 <= r <= size - w - 1 and 1 <= c <= size - w - 1):
      v.append('box position')
  if common.overlaps(k['rows'], k['cols'], ws, ws, 3):
    v.append('boxes closer than 3')
  for j in range(len(ws)):
    cs = [k['tops'][j], k['uppers'][j], k['lowers'][j], k['bottoms'][j]]
    if len(set(cs)) != 4 or 5 in cs or 0 in cs:
      v.append('corner colours')
  return v


def a_ef2(k, i):
  v = []
  cs = k['colors']
  if len(set(cs)) != 3 or set(cs) & {0, 1, 4}:
    v.append('colours')
  for g in range(3):
    cells = group_cells(k, g)
    if not conway_reachable(cells, 3):
      rows = sorted({r for r, _ in cells})
      cols = sorted({c for _, c in cells})
      v.append(f'sprite {g} covers rows {rows} cols {cols}: conway_sprite(3,3) always covers '
               f'every row and column (common.py 136-141)')
  return v


def a_17b(k, i):
  v = []
  w, h = k['width'], k['height']
  if w not in (3, 4) or h not in (3, 4) or w * h > 12:
    v.append('lattice')
  cs = k['colors']
  extra = sorted(set(cs) - {0, 1, 4, 8})
  if extra:
    v.append(f'cell colour(s) {extra} outside the native list [0,1,4,8] (line 34)')
  if len(set(cs)) < 3:
    v.append('fewer than 3 colours')
  return v


def a_1e5(k, i):
  v = []
  size, n = k['size'], len(k['brows'])
  if size not in (8, 12, 16):
    v.append('size')
  if n not in (size * size // 16, size * size // 16 - 1):
    v.append(f'{n} boxes on {size}')
  if any(not 0 <= x <= size - 2 for x in k['brows'] + k['bcols']):
    v.append('position')
  if common.overlaps(k['brows'], k['bcols'], [2] * n, [2] * n, 1):
    def cells(j):
      a, b, ang = k['brows'][j], k['bcols'][j], k['angles'][j]
      return {(a + dr, b + dc) for q, (dr, dc) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))) if q != ang}
    for x, y in itertools.combinations(range(n), 2):
      if common.overlaps([k['brows'][x], k['brows'][y]], [k['bcols'][x], k['bcols'][y]], [2, 2], [2, 2], 1):
        touch = any(adj8(p, q) for p in cells(x) for q in cells(y))
        v.append(f'2x2 frames at {(k["brows"][x], k["bcols"][x])} and {(k["brows"][y], k["bcols"][y])} '
                 f'have no gap (line 41 needs one); the drawn L cells {"touch" if touch else "do not touch"}')
  if any(c not in (2, 5) for c in k['colors']):
    v.append('colour')
  return v


def a_25e(k, i):
  v = []
  L, size, nb = k['length'], k['size'], len(k['bcolors'])
  if not (4 <= L <= 6 and size == 2 * L + 6 and nb == L - 2):
    v.append(f'L={L} size={size} boxes={nb}')
  if k['icolor'] == k['ocolor'] or len(set(k['bcolors'])) != nb or set(k['bcolors']) & {k['icolor'], k['ocolor']}:
    v.append('colours')
  if any(not 1 <= x <= size - L - 1 for x in k['brows'] + k['bcols']):
    v.append('box position')
  if common.overlaps(k['brows'], k['bcols'], [L] * nb, [L] * nb, 1):
    v.append('boxes closer than 1')
  cs = k['colors']
  cells = {c: [(j // L, j % L) for j, x in enumerate(cs) if x == c] for c in set(cs)}
  if set(cs) != set(k['bcolors']) | {k['ocolor']}:
    v.append('colour set')
  for c in k['bcolors']:
    if any(not (1 <= r <= L - 2 and 1 <= cc <= L - 2) for r, cc in cells.get(c, [])):
      v.append('stroke cell on the border (lines 48-50 keep strokes interior)')
    if c in cells and not common.connected(cells[c]):
      v.append('colour not 4-connected')
  # sufficient condition for the stroke loop to stop exactly here: one colour lies on a
  # single straight interior segment, so it can be the final stroke.
  def straight(px):
    rs = {r for r, _ in px}
    cc = {c for _, c in px}
    return (len(rs) == 1 and max(cc) - min(cc) + 1 == len(px)) or \
           (len(cc) == 1 and max(rs) - min(rs) + 1 == len(px))
  if not any(straight(cells[c]) for c in k['bcolors'] if c in cells):
    v.append('no colour can be the final stroke (sufficient check only)')
  return v


def a_260(k, i):
  v = []
  n = len(k['lengths'])
  if not 3 <= n <= 5 or any(not 1 <= x <= 2 * n for x in k['lengths']):
    v.append('lines/lengths')
  if len(set(k['colors'])) != n or 7 in k['colors']:
    v.append('colours')
  return v


def a_2e6(k, i):
  v = []
  size, n = k['size'], len(k['wides'])
  if (size, n) not in ((16, 3), (22, 4), (28, 5)):
    v.append(f'{n} boxes on {size}x{size} (line 30 ties size 10+6b to b+2 boxes)')
  for w, t, r, c, hm, vm in zip(k['wides'], k['talls'], k['brows'], k['bcols'], k['hmids'], k['vmids']):
    if not (5 <= w <= size // 2 and 5 <= t <= size // 2):
      v.append(f'box {w}x{t} outside 5..{size // 2} (lines 32-33)')
    if not (1 <= r <= size - t - 1 and 1 <= c <= size - w - 1):
      v.append('box position')
    if not (2 <= hm <= t - 3 and 2 <= vm <= w - 3):
      v.append('divider position')
  if common.overlaps(k['brows'], k['bcols'], k['wides'], k['talls'], 1):
    v.append('boxes closer than 1')
  if len(set(k['idxs'])) < 2 or any(not 0 <= x < n for x in k['idxs']):
    v.append('idxs')
  cs = k['colors'] + [k['bcolor']]
  if len(set(cs)) != 5 or 0 in cs:
    v.append('colours')
  return v


def a_42a(k, i):
  s = k['size']
  cols = [sum(k['vals'][s * j:s * (j + 1)]) for j in range(s)]
  return [] if 3 <= s <= 5 and sorted(cols) == list(range(1, s + 1)) else [f'size {s} counts {cols}']


def a_481(k, i):
  s, t = k['size'], sum(k['colors'])
  return [] if 2 <= s <= 4 and s <= t <= s * s - s and 1 <= k['hue'] <= 9 else ['size/density']


def a_575(k, i):
  v = []
  size = k['size']
  g = canon('5751f35e')[i]['input']
  r = radii_5751(g)
  runs = [(c, len(list(gr))) for c, gr in itertools.groupby(r)]
  if not 8 <= size <= 12 or size % 2:
    v.append('size')
  if len(runs) != 3 or len({c for c, _ in runs}) != 3 or any(not 1 <= x <= 3 for _, x in runs):
    v.append(f'rings {runs}')
  half = size // 2
  for row in range(size):
    for col in range(size):
      rr = (half - 1 - row) if row < half else (row - half)
      cc = (half - 1 - col) if col < half else (col - half)
      if g[row][col] not in (0, r[max(rr, cc)]):
        v.append('foreign colour inside a ring')
        break
  return v


def a_749(k, i):
  v = []
  n = len(k['pattern2'])
  if n != 5:
    v.append('panel size')
  if frozenset(map(tuple, k['line'])) not in wall_grammar_7491(n):
    v.append('wall outside the straight/diagonal/ell/path grammar')
  # patterns: the 'random' kind (line 212) reaches every set; validate() runs the
  # all_fixed path, which raises on any violated scene guard.
  return v


def a_963(k, i):
  v = []
  size = k['size']
  if not 14 <= size <= 16 or not 0 <= k['bcol'] <= size - 3 or sum(k['blues']) == 0:
    v.append('size/bcol/blues')
  if set(k['colors']) - {5, 7}:
    v.append('colours')
  if k.get('extras'):
    v.append(f'extras={k["extras"]}: the random path never sets the shifted-stick offset '
             f'(line 52); see fixture_policy 963c33f8 teaching copy')
  return v


def a_973(k, i):
  s = k['size']
  cs = k['colors']
  ok = 3 <= s <= 5 and 0 not in cs and 2 <= len(set(cs)) <= 3
  return [] if ok else ['size/colours']


def a_996(k, i):
  s, L = k['size'], k['length']
  ok = 4 <= s <= 6 and 3 <= L <= s and 0 <= k['row'] <= s - L and 0 <= k['col'] <= s - 3 \
      and len(set(k['colors'])) == 2 and 7 not in k['colors']
  return [] if ok else ['parameters']


def a_9dd(k, i):
  L = k['length']
  t = sum(k['shown'])
  return [] if 2 <= L <= 4 and abs(t - L * L // 2) <= 1 and 1 <= k['color'] <= 9 else ['length/shown']


ACHECK = {'817e6c09': a_817, 'c1990cce': a_c19, '98c475bf': a_98c, '456873bc': a_456,
          '458e3a53': a_458, '470c91de': a_470, '52fd389e': a_52f, '5783df64': a_578,
          '5ecac7f7': a_5ec, '758abdf0': a_758, '762cd429': a_762, '7d7772cc': a_7d7,
          '8fbca751': a_8fb, '981add89': a_981, '985ae207': a_985, 'c8b7cc0f': a_c8b,
          'df9fd884': a_df9, 'e9ac8c9e': a_e9a, 'ef26cbf6': a_ef2, '17b866bd': a_17b,
          '1e5d6875': a_1e5, '25e02866': a_25e, '2601afb7': a_260, '2e65ae53': a_2e6,
          '42a15761': a_42a, '48131b3c': a_481, '5751f35e': a_575, '7491f3cf': a_749,
          '963c33f8': a_963, '973e499e': a_973, '9968a131': a_996, '9ddd00f0': a_9dd}

for tid in IDS:
  cal = CAP[tid]
  verdict(tid, [(lab, ACHECK[tid](k, i)) for i, (lab, k) in enumerate(zip(labels(tid), cal))])

# extra canonical facts quoted in the reviews
k = CAP['52fd389e']
print('  52fd389e latent (counts, wides, talls): ' + str([
    ([kk['pboxes'].count(b) for b in range(len(kk['wides']))], kk['wides'], kk['talls']) for kk in k]))
print('  c8b7cc0f latent (size, wide, tall): ' + str([(kk['size'], kk['wide'], kk['tall']) for kk in CAP['c8b7cc0f']]))
print('  456873bc / 8fbca751 / ef26cbf6 canonical sprite cell counts: ' + str((
    [len(mask_cells(kk['colors'], kk['size'])) for kk in CAP['456873bc']],
    [[len(group_cells(kk, g)) for g in range(len(kk['brows']))] for kk in CAP['8fbca751']],
    [[len(group_cells(kk, g)) for g in range(3)] for kk in CAP['ef26cbf6']])))


# ======================================================== B. native draws
print()
print(f'== B. {N} seeded native draws per family (985ae207: {N_SLOW}, {SLOW_LIMIT}s deadline each)')


def stat_conway(n, cnt):
  section(900 + n)
  ds = collections.Counter(len(set(zip(*common.conway_sprite(n, n)))) for _ in range(cnt))
  return dict(sorted(ds.items()))


def stat_52f(pairs):
  boxes = collections.Counter()
  for p in pairs:
    g = p['input']
    boxes[len(comps({(r, c) for r in range(len(g)) for c in range(len(g)) if g[r][c] == 4}))] += 1
  return f'box_counts={dict(sorted(boxes.items()))}'


def stat_8fb(pairs):
  shapes = collections.Counter()
  for p in pairs:
    g, o = p['input'], p['output']
    shapes[(len(g), len(g[0]), sum(row.count(2) for row in o) > 0)] += 1
  boxes = collections.Counter()
  for p in pairs:
    g = p['input']
    if len(g[0]) == 12:
      occ = {(r // 4, c // 4) for r in range(8) for c in range(12) if g[r][c] == 8}
      boxes[len(occ)] += 1
  return f'12x8_occupied_lattice_cells={dict(sorted(boxes.items()))}'


def stat_5ec(pairs):
  return f'size6={sum(len(p["input"]) == 6 for p in pairs)}/{len(pairs)}'


def stat_c8b(pairs):
  cnt = collections.Counter(sum(v != 0 for row in p['output'] for v in row) for p in pairs)
  return f'output_counts={dict(sorted(cnt.items()))}'


def stat_17b(pairs):
  cols = collections.Counter()
  for p in pairs:
    g = p['input']
    cols.update({g[r][c] for r in range(0, len(g) - 1, 5) for c in range(0, len(g[0]) - 1, 5)})
  return f'cell_colours_seen={sorted(cols)}'


def stat_2e6(pairs):
  return 'sizes=' + str(dict(sorted(collections.Counter(len(p['input']) for p in pairs).items())))


def _disagrees(tid, p):
  try:
    return runtime.grid(runtime.call(runtime.verification_solver(tid), p['input'], seconds=5)) != p['output']
  except Exception:  # noqa: BLE001
    return True


def stat_575(pairs):
  """Verifier disagreements split by an inner ring of colour 0 (line 52 samples 0..9)."""
  split = collections.Counter()
  for p in pairs:
    o = p['output']
    half = len(o) // 2
    radii = [o[half - 1 - k][half - 1 - k] for k in range(half)]
    inner_zero = any(x == 0 for x in radii[:-1])
    split[(inner_zero, _disagrees('5751f35e', p))] += 1
  return ('inner_zero_ring/disagree: ' + ', '.join(f'{a}/{b}={c}' for (a, b), c in sorted(split.items())))


def far_edge_overshoot_985(g):
  """Some tile's final copy (constructor lines 53-75) sticks out past its bar's far edge."""
  h = len(g)
  tiles = []
  for y in range(1, h - 1):
    for x in range(1, h - 1):
      ring = {g[y + a][x + b] for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b}
      if len(ring) == 1 and g[y][x] not in ring and 8 not in ring:
        tiles.append((y, x, g[y][x]))
  centres = {(y, x) for y, x, _ in tiles}
  for y, x, c in tiles:
    dy = dx = 0
    pts = [(a, b) for a in range(h) for b in range(h) if g[a][b] == c and (a, b) not in centres]
    a0, b0 = min(p[0] for p in pts), min(p[1] for p in pts)
    a1, b1 = max(p[0] for p in pts), max(p[1] for p in pts)
    while True:
      if y < a0:
        dy, dx = 3, 0
      elif y > a1:
        dy, dx = -3, 0
      elif x < b0:
        dy, dx = 0, 3
      elif x > b1:
        dy, dx = 0, -3
      else:
        break
      y, x = y + dy, x + dx
    if (dy > 0 and y + 1 > a1) or (dy < 0 and y - 1 < a0) or (dx > 0 and x + 1 > b1) or (dx < 0 and x - 1 < b0):
      return True
  return False


def stat_985(pairs):
  """Verifier disagreements split by a far-edge overshoot (archived verifier line 'nx + 2 <= bx1')."""
  split = collections.Counter()
  for p in pairs:
    split[(far_edge_overshoot_985(p['input']), _disagrees('985ae207', p))] += 1
  return ('far_edge_overshoot/disagree: ' + ', '.join(f'{a}/{b}={c}' for (a, b), c in sorted(split.items())))


print('  985ae207 canonical far-edge overshoot (train..test): ' +
      str([far_edge_overshoot_985(q['input']) for q in canon('985ae207')]))


EXTRA = {'52fd389e': stat_52f, '8fbca751': stat_8fb, '5ecac7f7': stat_5ec, 'c8b7cc0f': stat_c8b,
         '17b866bd': stat_17b, '2e65ae53': stat_2e6, '5751f35e': stat_575, '985ae207': stat_985}

NATIVE = {}
for off, tid in enumerate(IDS):
  section(100 + off)
  m = mod(tid)
  check = runtime.verification_solver(tid)
  prog, kind = program(tid)
  n_draw = N_SLOW if tid == '985ae207' else N
  limit = SLOW_LIMIT if tid == '985ae207' else DRAW_LIMIT
  pairs, errors, timeouts = [], 0, 0
  for j in range(n_draw):
    if tid == '985ae207':
      # A draw cut off by the deadline leaves the RNG in a timing-dependent state, so
      # every slow draw gets its own seed. Only draws near the deadline can still vary.
      random.seed(SEED * 1000 + 100 + off + 7919 * (j + 1))
    try:
      p = runtime.call(m.generate, seconds=limit)
      if p['input'] is None:
        errors += 1
      else:
        pairs.append(p)
    except TimeoutError:
      timeouts += 1
    except Exception:  # noqa: BLE001
      errors += 1
  NATIVE[tid] = pairs
  ver = prg = 0
  gate_txt = ''
  if tid == '98c475bf':
    # The program reads motifs from demonstrations: pair each query with the next three
    # native draws as demonstrations, as an episode would, and apply the production gate.
    from arc_agi2.colour_evidence import require_colour_evidence
    gated = passed = 0
    for j, p in enumerate(pairs):
      demos = [pairs[(j + d) % len(pairs)] for d in (1, 2, 3)]
      try:
        require_colour_evidence('98c475bf', demos, [p], ID)
      except Exception:  # noqa: BLE001
        gated += 1
        continue
      try:
        passed += runtime.call(prog, p['input'], demos, seconds=5) == p['output']
      except Exception:  # noqa: BLE001
        pass
    gate_txt = f' gate_rejected_3demo_episodes={gated}/{len(pairs)} program_on_gated={passed}/{len(pairs) - gated}'
  for p in pairs:
    try:
      ver += runtime.grid(runtime.call(check, p['input'], seconds=5)) == p['output']
    except Exception:  # noqa: BLE001
      pass
    if prog is not None and tid != '98c475bf':
      try:
        prg += runtime.call(prog, p['input'], seconds=5) == p['output']
      except Exception:  # noqa: BLE001
        pass
  shapes = collections.Counter((len(p['input']), len(p['input'][0])) for p in pairs)
  uniq = len({key(p['input']) for p in pairs})
  prof = profile_from_task(runtime.reference(tid)['canonical'])['patterns']
  pats = sorted({(x['demo_input_shapes'], x['query_input_shape']) for x in prof})
  extra = EXTRA[tid](pairs) if tid in EXTRA else ''
  prog_txt = 'see gate' if tid == '98c475bf' else f'{prg}/{len(pairs)}'
  print(f'  {tid}: valid={len(pairs)}/{n_draw} timeouts={timeouts} errors={errors} unique={uniq} '
        f'shapes={len(shapes)} max_same_shape={max(shapes.values()) if shapes else 0} '
        f'verifier={ver}/{len(pairs)} program[{kind}]={prog_txt}{gate_txt} '
        f'canonical_profile={pats} {extra}'.rstrip())

print(f'  conway_sprite(3,3) distinct-cell counts over 20000 draws: {stat_conway(3, 20000)}')
print(f'  conway_sprite(4,4) distinct-cell counts over 20000 draws: {stat_conway(4, 20000)}')


# ======================================================== C. widened scenes
print()
print(f'== C. certified programs and archived verifiers on widened scenes ({C_N} per family; '
      'constructor output is the reference)')


def run_c(tid, maker, note, reference=None):
  m = mod(tid)
  prog, kind = program(tid)
  check = runtime.verification_solver(tid)
  ok_p = ok_v = made = fail = 0
  shapes = set()
  first_bad = None
  for _ in range(C_N):
    p = None
    for _try in range(300):
      kw = maker()
      if kw is None:
        continue
      try:
        p = runtime.call(reference or m.generate, seconds=5, **kw)
      except Exception:  # noqa: BLE001
        p = None
      if p is not None and p.get('input') is not None:
        break
      p = None
    if p is None:
      fail += 1
      continue
    made += 1
    shapes.add((len(p['input']), len(p['input'][0])))
    try:
      good = runtime.call(prog, p['input'], seconds=5) == p['output']
    except Exception:  # noqa: BLE001
      good = False
    ok_p += good
    if not good and first_bad is None:
      first_bad = {k: v for k, v in kw.items() if not isinstance(v, list) or len(v) <= 12}
    try:
      ok_v += runtime.grid(runtime.call(check, p['input'], seconds=5)) == p['output']
    except Exception:  # noqa: BLE001
      pass
  msg = (f'{note}: scenes={made} (unbuildable {fail}) shapes={len(shapes)} '
         f'program[{kind}]={ok_p}/{made} archived_verifier={ok_v}/{made}')
  if first_bad is not None:
    msg += f' first_program_mismatch={first_bad}'
  show(tid, msg)


def r(a, b):
  return random.randint(a, b)


def c_817():
  w = r(5, 30)
  col, rows, cols, last = r(0, 3), [], [], 2
  row = r(0, 5)
  while col + 1 < w:
    cols.append(col)
    rows.append(row)
    sp = r(1 if last > 1 else 2, 5)
    last = sp
    col += sp
    for _ in range(50):
      row = r(0, 5)
      if row == rows[-1]:
        continue
      if sp == 2 and abs(row - rows[-1]) <= 1:
        continue
      if sp == 1 and abs(row - rows[-1]) <= 2:
        continue
      break
    else:
      return None
  if len(cols) < 2:
    return None
  return {'width': w, 'rows': rows, 'cols': cols}


def c_456():
  n = random.choice([2, 5])
  rows, cols = common.conway_sprite(n, n)
  colors = [0] * (n * n)
  for a, b in zip(rows, cols):
    colors[a * n + b] = 1
  return {'size': n, 'line': r(0, n - 1), 'xpose': r(0, 1), 'colors': colors}


def c_458():
  cs = r(3, 6)
  copies = 10 - cs
  w, h = r(1, min(copies, 6)), r(1, min(copies, 6))
  if w < 2 and h < 2:
    return None
  lc = random.randint(1, 9)
  pat = [x for x in random.sample(range(10), 10) if x != lc][:6]
  colors = [c if c != lc else 0 for c in (random.randint(1, 9) for _ in range(w * h))]
  return {'cell_size': cs, 'line_color': lc, 'width': w, 'height': h, 'brow': r(0, copies - h),
          'bcol': r(0, copies - w), 'flop': r(0, 1), 'offset': r(0, 10), 'pattern': pat, 'colors': colors}


def c_470():
  size = r(6, 30)
  n = r(1, 6)
  wides = [r(2, 6) for _ in range(n)]
  talls = [r(2, 6) for _ in range(n)]
  if any(x > size - 1 for x in wides + talls):
    return None
  return {'size': size, 'wides': wides, 'talls': talls,
          'brows': [r(0, size - t) for t in talls], 'bcols': [r(0, size - w) for w in wides],
          'colors': random.sample([c for c in range(1, 10) if c not in (7, 8)], n),
          'angles': [r(0, 3) for _ in range(n)]}


def c_52f():
  size = r(12, 30)
  n = r(1, 4)
  counts = [r(1, 6) for _ in range(n)]
  wides = [r(3, 10) for _ in range(n)]
  talls = [r(3, 10) for _ in range(n)]
  ex_w = [w + 2 * c for w, c in zip(wides, counts)]
  ex_t = [t + 2 * c for t, c in zip(talls, counts)]
  if any(x > size for x in ex_w + ex_t):
    return None
  brows = [r(0, size - t) for t in ex_t]
  bcols = [r(0, size - w) for w in ex_w]
  if common.overlaps(brows, bcols, ex_w, ex_t, 1):
    return None
  prows, pcols, pboxes = [], [], []
  for b, (c, w, t) in enumerate(zip(counts, wides, talls)):
    coords = [(a, bb) for a in range(1, t - 1) for bb in range(1, w - 1)]
    if len(coords) < c:
      return None
    coords = random.sample(coords, c)
    rr, cc = zip(*coords)
    if common.overlaps(rr, cc, [1] * c, [1] * c, 1):
      return None
    prows += rr
    pcols += cc
    pboxes += [b] * c
  return {'size': size, 'wides': wides, 'talls': talls,
          'brows': [x + c for x, c in zip(brows, counts)], 'bcols': [x + c for x, c in zip(bcols, counts)],
          'colors': random.sample([1, 2, 3, 5, 6, 7, 8, 9], n), 'prows': list(prows),
          'pcols': list(pcols), 'pboxes': pboxes}


def c_578():
  base = random.choice([1, 4, 5, 6, 7, 8, 9, 10])
  rows, cols = [], []
  for j in range(9):
    rows.append(base * (j // 3) + r(0, base - 1))
    cols.append(base * (j % 3) + r(0, base - 1))
  return {'size': 3 * base, 'rows': rows, 'cols': cols, 'colors': random.sample(range(1, 10), 9)}


def c_5ec():
  size = r(5, 9)
  wmax = size - 2
  for _ in range(2000):
    widths = [r(1, wmax) for _ in range(9)]
    if sum(widths[0:3]) == size and sum(widths[3:6]) == size and sum(widths[6:9]) == size \
        and widths[0] + widths[4] + widths[8] == size:
      break
  else:
    return None
  color_map = [c for c in range(widths[0])]
  color_map += [size + 1 + widths[3] + c for c in range(widths[4])]
  color_map += [2 * (size + 1) + widths[6] + widths[7] + c for c in range(widths[8])]
  subsets = []
  for _ in range(3):
    while True:
      s = random.choices([0, 1, 2, 3, 4, 5, 8, 9], k=3)
      if s[0] != s[1] and s[1] != s[2]:
        break
    subsets += s
  wide = 3 * size + 2
  grid = common.grid(wide, size, 7)
  col = -1
  for index, (width, color) in enumerate(zip(widths, subsets)):
    if index % 3 == 0:
      col += 1
    for _try in range(500):
      coords = [(a, b) for a in range(size) for b in range(width)]
      coords = random.sample(coords, r(1, len(coords) - 1))
      columns = {b for _, b in coords}
      if index % 3 == 0 and width - 1 not in columns:
        continue
      if index % 3 == 1 and len(columns) != width:
        continue
      if index % 3 == 2 and 0 not in columns:
        continue
      if common.connected(coords):
        break
    else:
      return None
    for a, b in coords:
      grid[a][col + b] = color
    col += width
  for a in range(size):
    grid[a][2 * size + 1] = grid[a][size] = 6
  return {'size': size, 'color_map': color_map, 'colors': common.flatten(grid)}


def c_7d7():
  size = r(6, 30)
  spacing = r(0, 1)
  mrow = r(1, size // 2)
  if mrow + 1 > size - 3:
    return None
  lrow = r(mrow + 1, size - 3)
  colors = random.sample(range(10), 10)
  t = colors.pop()
  b = t if r(0, 2) else colors.pop()
  f = colors.pop()
  colors = colors[:r(3, 5)]
  col, th, bh = 1, [], []
  while True:
    th.append(random.choice(colors))
    bh.append(th[-1] if r(0, 1) else random.choice(colors))
    col += 1
    if col + 1 >= size:
      break
    if spacing:
      th.append(-1)
      bh.append(-1)
      col += 1
    if col + 1 >= size:
      break
    if r(0, 9) == 0:
      th.append(-1)
      bh.append(-1)
      col += 1
    if col + 1 >= size:
      break
  return {'size': size, 'tcolor': t, 'bcolor': b, 'fcolor': f, 'lrow': lrow, 'mrow': mrow,
          'flip': r(0, 1), 'xpose': r(0, 1), 'thues': th, 'bhues': bh}


def c_8fb():
  a, b = r(1, 7), r(1, 7)
  cells = [(i * 4, j * 4) for i in range(a) for j in range(b)]
  n = r(1, min(6, len(cells)))
  pos = random.sample(cells, n)
  rows, cols, groups = [], [], []
  for g in range(n):
    pr, pc = common.conway_sprite(4, 4)
    rows += pr
    cols += pc
    groups += [g] * len(pr)
  return {'width': 4 * b, 'height': 4 * a, 'brows': [p[0] for p in pos], 'bcols': [p[1] for p in pos],
          'rows': rows, 'cols': cols, 'groups': groups}


def c_981():
  size = r(12, 30)
  n = r(1, 6)
  bg = random.randint(1, 9)
  wides = [r(3, size - 4) for _ in range(n)]
  talls = [r(3, size - 4) for _ in range(n)]
  pcol, pcols = r(1, 5), []
  while pcol < size - 1:
    pcols.append(pcol)
    pcol += r(2, 7)
  return {'size': size, 'wides': wides, 'talls': talls,
          'brows': [r(1, size - t - 1) for t in talls], 'bcols': [r(0, size - w) for w in wides],
          'bcolors': [random.choice([c for c in range(1, 10) if c != bg]) for _ in range(n)],
          'pcols': pcols, 'pcolors': [random.choice([c for c in range(1, 10) if c != bg]) for _ in pcols],
          'bgcolor': bg}


def ref_c8b(size, rows, cols, wide, tall, brow, bcol, color):
  """c8b7cc0f lines 36-47 without the count 3..6 rejection (line 44)."""
  grid, output = common.grid(size, size), common.grid(3, 3)
  for a, b in zip(rows, cols):
    grid[a][b] = color
  common.hollow_rect(grid, wide, tall, brow, bcol, 1)
  count = sum(grid[a][b] == color for a in range(brow + 1, brow + tall - 1)
              for b in range(bcol + 1, bcol + wide - 1))
  if not 1 <= count <= 9:
    return None
  for j in range(count):
    output[j // 3][j % 3] = color
  return {'input': grid, 'output': output}


def c_c8b():
  size = r(6, 20)
  prob = random.choice([0.05, 0.1, 0.2])
  px = common.random_pixels(size, size, prob)
  wide, tall = r(3, size), r(3, size)
  return {'size': size, 'rows': [p[0] for p in px], 'cols': [p[1] for p in px], 'wide': wide,
          'tall': tall, 'brow': r(0, size - tall), 'bcol': r(0, size - wide),
          'color': random.choice([c for c in range(2, 10)])}


def ref_df9(size, wide, flop, brow, bcols, colors):
  """df9fd884 lines 51-70 with the size literal (7 + wide, line 50) lifted to a parameter."""
  grid, output = common.grids(size, size, 7)
  for g in (grid, output):
    g[0][bcols[0]] = g[0][bcols[0] + wide + 1] = 4
    for j in range(wide):
      g[0][bcols[0] + j + 1] = 4
    g[1][bcols[0]] = g[1][bcols[0] + wide + 1] = 4
    g[size - 1][bcols[1]] = g[size - 1][bcols[1] + wide + 1] = 4
    for j in range(wide):
      g[size - 1][bcols[1] + j + 1] = 4
    g[size - 2][bcols[1]] = g[size - 2][bcols[1] + wide + 1] = 4
  for j, color in enumerate(colors):
    if not color:
      continue
    grid[brow + j // wide][bcols[1] + 1 + j % wide] = color
    output[size - 3 + j // wide][bcols[0] + 1 + j % wide] = color
  if flop:
    grid, output = common.flop(grid), common.flop(output)
  return {'input': grid, 'output': output}


def c_df9():
  wide = r(1, 4)
  size = r(7 + wide, 30)
  bcols = [r(0, size - 2 - wide) for _ in range(2)]
  if not bcols[0] + wide + 2 < bcols[1]:
    return None
  c = random.choice([x for x in range(1, 10) if x not in (4, 7)])
  colors = [c] * (wide * 3)
  for j in range(wide * 2):        # top cells may be cut off, as on lines 40-48
    if r(0, 3) == 0:
      colors[j] = 0
  if not any(colors[2 * wide:]):
    return None
  return {'size': size, 'wide': wide, 'flop': r(0, 1), 'brow': r(1, size - 6), 'bcols': bcols,
          'colors': colors}


def c_e9a():
  size = r(8, 30)
  n = r(1, 5)
  widths = [2 * r(1, 4) for _ in range(n)]
  if any(w > size - 2 for w in widths):
    return None
  rows = [r(1, size - w - 1) for w in widths]
  cols = [r(1, size - w - 1) for w in widths]
  if common.overlaps(rows, cols, widths, widths, 3):
    return None
  cs = [random.sample([c for c in range(1, 10) if c != 5], 4) for _ in widths]
  return {'size': size, 'widths': widths, 'rows': rows, 'cols': cols, 'tops': [c[0] for c in cs],
          'uppers': [c[1] for c in cs], 'lowers': [c[2] for c in cs], 'bottoms': [c[3] for c in cs]}


def c_ef2():
  rows, cols, groups = [], [], []
  for g in range(3):
    cells = [(a, b) for a in range(3) for b in range(3) if random.random() < 0.5]
    if not cells:
      return None
    rows += [a for a, _ in cells]
    cols += [b for _, b in cells]
    groups += [g] * len(cells)
  return {'rows': rows, 'cols': cols, 'groups': groups,
          'colors': random.sample([c for c in range(2, 10) if c != 4], 3), 'flip': r(0, 1), 'xpose': r(0, 1)}


def c_17b():
  w, h = r(1, 5), r(1, 5)
  return {'width': w, 'height': h, 'colors': [random.choice(range(10)) for _ in range(w * h)]}


def c_1e5():
  size = r(5, 30)
  n = r(1, max(1, size * size // 16))
  brows, bcols = [], []
  for a, b in random.sample([(x, y) for x in range(size - 1) for y in range(size - 1)], (size - 1) ** 2):
    if common.overlaps(brows + [a], bcols + [b], [2] * (len(brows) + 1), [2] * (len(brows) + 1), 1):
      continue
    brows.append(a)
    bcols.append(b)
    if len(brows) == n:
      break
  n = len(brows)
  return {'size': size, 'brows': brows, 'bcols': bcols, 'angles': [r(0, 3) for _ in range(n)],
          'colors': [random.choice([2, 5]) for _ in range(n)]}


def c_25e():
  L = r(3, 9)
  nb = r(1, min(5, max(1, L - 2)))
  size = r(L + 2, 30)
  icolor = random.randint(1, 9)
  ocolor = random.choice([c for c in range(1, 10) if c != icolor])
  bcolors = random.sample([c for c in range(1, 10) if c not in (icolor, ocolor)], nb)
  brows = [r(1, size - L - 1) for _ in range(nb)]
  bcols = [r(1, size - L - 1) for _ in range(nb)]
  if common.overlaps(brows, bcols, [L] * nb, [L] * nb, 1):
    return None
  colors = [ocolor] * (L * L)
  for _ in range(400):
    slen = r(1, L - 2)
    soff = r(1, L - slen - 1)
    spos = r(1, L - 2)
    sdir = r(0, 1)
    sc = random.choice(bcolors + [ocolor])
    for val in range(soff, soff + slen):
      if sdir:
        colors[val * L + spos] = sc
      else:
        colors[spos * L + val] = sc
    if len(set(colors)) != nb + 1:
      continue
    if all(common.connected([(a, b) for a in range(L) for b in range(L) if colors[a * L + b] == bc])
           for bc in bcolors):
      return {'size': size, 'length': L, 'icolor': icolor, 'ocolor': ocolor, 'brows': brows,
              'bcols': bcols, 'bcolors': bcolors, 'colors': colors}
  return None


def c_260():
  n = r(2, 9)
  return {'lengths': [r(1, 2 * n) for _ in range(n)],
          'colors': random.sample([0, 1, 2, 3, 4, 5, 6, 8, 9], n)}


def c_2e6():
  size = r(12, 30)
  n = r(1, 6)
  wides = [r(5, size - 2) for _ in range(n)]
  talls = [r(5, size - 2) for _ in range(n)]
  brows = [r(1, size - t - 1) for t in talls]
  bcols = [r(1, size - w - 1) for w in wides]
  if common.overlaps(brows, bcols, wides, talls, 1):
    return None
  idxs = [r(0, n - 1) for _ in range(4)]
  colors = random.sample(range(1, 10), 5)
  return {'size': size, 'wides': wides, 'talls': talls, 'brows': brows, 'bcols': bcols,
          'hmids': [r(2, t - 3) for t in talls], 'vmids': [r(2, w - 3) for w in wides],
          'idxs': idxs, 'colors': colors[:4], 'bcolor': colors[4]}


def c_42a():
  s = random.choice([2, 6, 7])
  vals = []
  for order in random.sample(range(1, s + 1), s):
    idxs = random.sample(range(s), order)
    vals += [1 if j in idxs else 0 for j in range(s)]
  return {'size': s, 'vals': vals}


def c_481():
  s = r(5, 15)
  t = r(1, s * s - 1)
  on = set(random.sample(range(s * s), t))
  return {'size': s, 'hue': random.randint(1, 9), 'colors': [1 if j in on else 0 for j in range(s * s)]}


def c_575():
  k = r(2, 4)
  lengths = [r(1, 4) for _ in range(k)]
  size = 2 * sum(lengths)
  if not 4 <= size <= 30:
    return None
  half = size // 2
  colors = random.sample(range(10), k)
  radii = [c for c, ln in zip(colors, lengths) for _ in range(ln)]
  slate = common.grid(size, size)
  for a in range(size):
    for b in range(size):
      rr = (half - 1 - a) if a < half else (a - half)
      cc = (half - 1 - b) if b < half else (b - half)
      slate[a][b] = radii[max(rr, cc)]
  for a, b in common.random_pixels(size, size):
    slate[a][b] = 0
  flat = common.flatten(slate)
  if radii_5751(slate) != radii:
    return None
  return {'size': size, 'colors': flat}


def c_963():
  size = r(8, 30)
  blues = [r(0, 1) for _ in range(3)]
  if not any(blues):
    return None
  return {'size': size, 'bcol': r(0, size - 3), 'blues': blues,
          'colors': [7 if r(0, 15) else 5 for _ in range(size * size)]}


def c_973():
  s = random.choice([2, 3, 4, 5])
  k = r(2, min(4, s * s))
  hues = random.sample(range(1, 10), k)
  colors = [random.choice(hues) for _ in range(s * s)]
  if len(set(colors)) != k:
    return None
  return {'size': s, 'colors': colors}


def c_996():
  s = r(7, 30)
  L = r(3, s)
  return {'size': s, 'row': r(0, s - L), 'col': r(0, s - 3), 'length': L,
          'colors': random.sample([0, 1, 2, 3, 4, 5, 6, 8, 9], 2)}


def c_9dd():
  shown = [r(0, 1) for _ in range(25)]
  if not any(shown):
    return None
  return {'length': 5, 'color': random.randint(1, 9), 'shown': shown}


ref_ok = sum(ref_df9(7 + kk['wide'], **kk) == mod('df9fd884').generate(**kk) for kk in CAP['df9fd884'])
ref_ok2 = sum(ref_c8b(**kk) == mod('c8b7cc0f').generate(**kk) for kk in CAP['c8b7cc0f'])
section(299)
nat_ok = 0
for _ in range(100):
  kk = None
  st = random.getstate()
  p = mod('c8b7cc0f').generate()
  random.setstate(st)
  # replay lines 49-60 to recover the latent arguments, then compare with the lifted reference
  size = 7 if common.randint(0, 1) else 9
  color = common.random_color(exclude=[1])
  while True:
    rows, cols = [], []
    for pixel in common.random_pixels(size, size, 0.1):
      rows, cols = rows + [pixel[0]], cols + [pixel[1]]
    wide, tall = common.randint(4, size - 2), common.randint(4, size - 2)
    brow = common.randint(0, size - tall)
    bcol = common.randint(0, size - wide)
    q = ref_c8b(size, rows, cols, wide, tall, brow, bcol, color)
    if q is not None and 3 <= sum(v != 0 for row in q['output'] for v in row) <= 6:
      break
  nat_ok += q == p
print(f'  reference self-tests: ref_df9 equals generate on {ref_ok}/{len(CAP["df9fd884"])} canonical '
      f'parameter sets; ref_c8b equals generate on {ref_ok2}/{len(CAP["c8b7cc0f"])} canonical sets and '
      f'{nat_ok}/100 replayed native draws')
section(300)
run_c('817e6c09', c_817, 'width 5..30, start 0..3, gaps up to 4 columns, ending anywhere (height literal 7 kept)')
section(301)
run_c('c1990cce', lambda: {'width': 3}, 'width 3 (the only odd width outside 5..29 that fits)')
section(302)
run_c('456873bc', c_456, 'sprite sizes 2 and 5 (5x5 and 29x29 canvases)')
section(303)
run_c('458e3a53', c_458, 'output blocks 1..6 x 1..6 (native 2..3)')
section(304)
run_c('470c91de', c_470, 'canvas 6..30, 1..6 boxes of side 2..6')
section(305)
run_c('52fd389e', c_52f, 'canvas 12..30, 1..4 boxes, counts 1..6 (repeats allowed, not co-sorted), any non-4 colour')
section(306)
run_c('5783df64', c_578, 'block size 1 and 4..10 (3x3 to 30x30)')
section(307)
run_c('5ecac7f7', c_5ec, 'panel size 5..9, piece widths 1..size-2')
section(308)
run_c('762cd429', lambda: {'copies': 2, 'colors': [random.randint(1, 9) for _ in range(4)]},
      'NEGATIVE CONTROL copies 2 on the 16x30 canvas (line 32 maps copies != 3 to width 30); '
      'not a rule instance, because the canvas width fixes the copy count; failure expected')
section(309)
run_c('7d7772cc', c_7d7, 'canvas 6..30, spacing independent of size')
section(310)
run_c('8fbca751', c_8fb, 'lattices of 1..7 x 1..7 cells with 1..6 occupied cells')
section(311)
run_c('981add89', c_981, 'canvas 12..30, 1..6 boxes of side 3..size-4, marker steps 2..7')
section(312)
run_c('c8b7cc0f', c_c8b, 'canvas 6..20, rectangle sides 3..size, counts 1..9',
      reference=ref_c8b)
section(313)
run_c('df9fd884', c_df9, 'portal width 1..4, canvas 8..30 independent of the portal (size literal lifted)',
      reference=ref_df9)
section(314)
run_c('e9ac8c9e', c_e9a, 'canvas 8..30, 1..5 boxes of even side 2..8')
section(315)
run_c('ef26cbf6', c_ef2, 'any non-empty 3x3 masks (rows/columns may be empty)')
section(316)
run_c('17b866bd', c_17b, 'lattices 1..5 x 1..5, any cell colour 0..9')
section(317)
run_c('1e5d6875', c_1e5, 'canvas 5..30, sparse to dense boxes')
section(318)
run_c('25e02866', c_25e, 'square side 3..9, 1..5 boxes, canvas side..30 independent of the square')
section(319)
run_c('2601afb7', c_260, '2..9 lines (5x5 to 19x19)')
section(320)
run_c('2e65ae53', c_2e6, 'canvas 12..30, 1..6 boxes of side 5..size-2')
section(321)
run_c('42a15761', c_42a, 'column counts 2, 6 and 7')
section(322)
run_c('48131b3c', c_481, 'sizes 5..15, any density')
section(323)
run_c('5751f35e', c_575, '2..4 rings of width 1..4 (4..30)')
section(324)
run_c('963c33f8', c_963, 'canvas 8..30')
section(325)
run_c('973e499e', c_973, 'size 2..5 with 2..4 colours')
section(326)
run_c('9968a131', c_996, 'canvas 7..30')
section(327)
run_c('9ddd00f0', c_9dd, 'block side 5 (29x29), any shown subset')
print('  not run: 98c475bf (demonstration-read motifs; width literal), 758abdf0 (canvas literal '
      'without a parameter), 7491f3cf (already at the 4n+5 <= 30 cap), 985ae207 (rejection cost)')


# ======================================================== D. exact finite domains
print()
print('== D. exact finite native domains')


def count_817_width(w):
  """Distinct native (rows, cols) walks at width w: DP over (column, last spacing, row).

  A block at column w-2 always ends the walk (every spacing leaves the loop at
  line 35) and satisfies line 47, so it counts once; a walk that leaves the
  loop from any other column is rejected by line 47.
  """
  memo = {}

  def ways(col, last, row):
    if (col, last, row) in memo:
      return memo[(col, last, row)]
    if col + 2 == w:
      return 1
    res = 0
    for sp in range(1 if last > 1 else 2, 4):
      nc = col + sp
      if nc + 1 >= w:
        continue
      for nr in range(6):
        if nr == row or (sp == 2 and abs(nr - row) <= 1) or (sp == 1 and abs(nr - row) <= 2):
          continue
        res += ways(nc, sp, nr)
    memo[(col, last, row)] = res
    return res

  return sum(ways(c0, 2, r0) for c0 in (0, 1) for r0 in range(6))


def brute_817_width(w):
  """Literal enumeration of lines 31-47 at width w, as distinct rendered inputs."""
  m = mod('817e6c09')
  out = set()

  def rec(col, row, last, rows, cols):
    rows, cols = rows + [row], cols + [col]
    for sp in range(1 if last > 1 else 2, 4):
      nc = col + sp
      if not nc + 1 < w:
        if cols[-1] + 2 == w:
          out.add((tuple(rows), tuple(cols)))
        continue
      for nr in range(6):
        if nr == rows[-1] or (sp == 2 and abs(nr - rows[-1]) <= 1) or (sp == 1 and abs(nr - rows[-1]) <= 2):
          continue
        rec(nc, nr, sp, rows, cols)

  for c0 in (0, 1):
    for r0 in range(6):
      rec(c0, r0, 2, [], [])
  return len({key(m.generate(width=w, rows=list(a), cols=list(b))['input']) for a, b in out})


def count_817():
  checks = [(w, count_817_width(w), brute_817_width(w)) for w in range(5, 12)]
  agree = sum(a == b for _, a, b in checks)
  return sum(count_817_width(w) for w in range(5, 18)), agree, len(checks)


def count_758():
  m = mod('758abdf0')
  seqs = []

  def rec(acc):
    if len(acc) == 16:
      seqs.append(list(acc))
      return
    for x in ((0,) if acc and acc[-1] else (0, 1, 2)):
      rec(acc + [x])

  rec([])
  grids = set()
  for s in seqs:
    for f in (0, 1):
      for x in (0, 1):
        grids.add(key(m.generate(lengths=s, flip=f, xpose=x)['input']))
  return len(seqs), len(grids)


def count_996():
  m = mod('9968a131')
  out = set()
  pal = [0, 1, 2, 3, 4, 5, 6, 8, 9]
  for s in range(4, 7):
    for L in range(3, s + 1):
      for row in range(0, s - L + 1):
        for col in range(0, s - 2):
          for a, b in itertools.permutations(pal, 2):
            out.add(key(m.generate(size=s, row=row, col=col, length=L, colors=[a, b])['input']))
  return len(out)


def count_9dd():
  total = 0
  for L in range(2, 5):
    total += 9 * sum(math.comb(L * L, t) for t in range(L * L + 1) if abs(t - L * L // 2) <= 1)
  return total


def count_481():
  return 9 * sum(sum(math.comb(s * s, t) for t in range(s, s * s - s + 1)) for s in range(2, 5))


def count_42a():
  return sum(math.factorial(s) * math.prod(math.comb(s, k) for k in range(1, s + 1)) for s in range(3, 6))


print(f'  c1990cce: 13 inputs (odd widths 5..29), certificate finite_default_domain exhaustive 13')
print(f'  762cd429: {2 * 9 ** 4} inputs (2 canvases x 9^4 seed colourings)')
print(f'  9ddd00f0: {count_9dd()} inputs (L 2..4, |shown - L^2//2| <= 1, 9 colours)')
print(f'  48131b3c: {count_481()} inputs (sizes 2..4, density size..size^2-size, 9 hues)')
print(f'  42a15761: {count_42a()} inputs (sizes 3..5, distinct column counts)')
print(f'  9968a131: {count_996()} inputs (enumerated through the explicit path)')
n817, agree817, total817 = count_817()
print(f'  817e6c09: {n817} inputs (DP over the native column/row walk; DP equals literal brute-force '
      f'enumeration of rendered inputs at {agree817}/{total817} widths 5..11)')
seqs, grids = count_758()
print(f'  758abdf0: {seqs} stub sequences, {grids} distinct inputs over flip/xpose')


# ======================================================== timing
if TIMING:
  print()
  print('== timing (not reproducible)')
  for tid in IDS:
    m = mod(tid)
    n_draw = 6 if tid == '985ae207' else 30
    limit = SLOW_LIMIT if tid == '985ae207' else DRAW_LIMIT
    ts, to = [], 0
    for _ in range(n_draw):
      t0 = time.perf_counter()
      try:
        runtime.call(m.generate, seconds=limit)
        ts.append(time.perf_counter() - t0)
      except TimeoutError:
        to += 1
    if ts:
      print(f'  {tid}: n={len(ts)} timeouts={to} median={statistics.median(ts) * 1000:.1f}ms '
            f'max={max(ts) * 1000:.1f}ms')
    else:
      print(f'  {tid}: n=0 timeouts={to}')
