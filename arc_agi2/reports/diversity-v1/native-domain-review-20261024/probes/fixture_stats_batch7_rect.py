"""Batch-7 rectangular-dimension probe for 7491f3cf and 973e499e. Read-only.

Run from the worktree root with PYTHONPATH=.

Usage: fixture_stats_batch7_rect.py [N] [SEED]

Both constructors draw square shapes only: 7491f3cf uses N x N panels (lines
61-62, 370) and 973e499e an s x s input (line 29). This probe builds
rectangular scenes outside the constructors. Each scene is checked against an
independent reference relation, then against the certified program from the
production lookup (d4 = 0, identity palette) and the archived verifier
(runtime.verification_solver). A pass is evidence of program support for the
hypothesis. It is not a certificate and does not show that the original task
intends rectangles.

Sections
  S. self-tests: on square shapes, each rectangular builder reproduces the
     constructor exactly.
  A. 7491f3cf: four H x W panels (W 3..6 so that 4W+5 <= 30, H 3..12 with
     H != W unless noted). The constructor's own wall kinds (row/column
     line, ell, monotone path, staircase diagonal) and pattern kinds are
     restated for rectangles, and every scene guard is kept. Acceptance
     rates, including the wall-evidence guard, are reported per aspect.
  B. 973e499e: H x W inputs with H, W independently in 2..5 and 2..4 colours.
     Reference: output[bi*H + r][bj*W + c] = in[r][c] if in[r][c] == in[bi][bj],
     otherwise 0.
Every section reseeds from SEED plus a fixed offset, so output is
byte-identical between runs.
"""
import collections
import random
import sys

sys.path.insert(0, '.')
from arc_agi2 import runtime  # noqa: E402
from arc_agi2.direct_certificates import certified_factory_source  # noqa: E402

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
N = int(ARGS[0]) if ARGS else 300
SEED = int(ARGS[1]) if len(ARGS) > 1 else 0
ID = list(range(10))


def section(offset):
  random.seed(SEED * 1000 + offset)


def mod(tid):
  return __import__(f'tasks.task_{tid}', fromlist=['generate'])


def program(tid):
  src = certified_factory_source(tid, 0, ID)
  ns = {}
  exec(src, ns)
  return lambda g, demos=(): [list(map(int, r)) for r in ns['solve'](list(demos), g)]


def agree(fn, g, want):
  try:
    return runtime.grid(runtime.call(fn, g, seconds=5)) == want
  except Exception:  # noqa: BLE001
    return False


# ------------------------------------------------------------------ 7491f3cf
def regions(h, w, wall):
  seen, regs = set(), []
  for r in range(h):
    for c in range(w):
      if (r, c) in wall or (r, c) in seen:
        continue
      seen.add((r, c))
      stack, reg = [(r, c)], set()
      while stack:
        y, x = stack.pop()
        reg.add((y, x))
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
          q = (y + dy, x + dx)
          if 0 <= q[0] < h and 0 <= q[1] < w and q not in wall and q not in seen:
            seen.add(q)
            stack.append(q)
      regs.append(reg)
  return regs


def connected8(cells):
  cells = set(cells)
  start = next(iter(cells))
  seen, stack = {start}, [start]
  while stack:
    y, x = stack.pop()
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        q = (y + dy, x + dx)
        if q in cells and q not in seen:
          seen.add(q)
          stack.append(q)
  return len(seen) == len(cells)


def near(cell, wall):
  return any((cell[0] + dy, cell[1] + dx) in wall for dy in (-1, 0, 1) for dx in (-1, 0, 1))


def sample_wall(h, w):
  """Rectangular restatement of _sample_line (lines 139-163); returns (kind, cells)."""
  kind = random.choices(['straight', 'diagonal', 'ell', 'path'], weights=[2, 1, 3, 4])[0]
  if kind == 'straight':
    if random.random() < 0.5:
      k = random.randint(1, h - 2)
      cells = {(k, c) for c in range(w)}
    else:
      k = random.randint(1, w - 2)
      cells = {(r, k) for r in range(h)}
  elif kind == 'diagonal':
    # staircase from corner to corner: one cell per row on the long axis
    if h >= w:
      cells = {(r, (r * (w - 1)) // max(1, h - 1)) for r in range(h)}
    else:
      cells = {((c * (h - 1)) // max(1, w - 1), c) for c in range(w)}
  elif kind == 'ell':
    r = random.randint(1, h - 2)
    c = random.randint(1, w - 2)
    rows = range(0, r + 1) if random.random() < 0.5 else range(r, h)
    cols = range(0, c + 1) if random.random() < 0.5 else range(c, w)
    cells = {(i, c) for i in rows} | {(r, j) for j in cols}
  else:
    if random.random() < 0.5:
      col = random.randint(0, w - 1)
      cells = {(0, col)}
      for row in range(1, h):
        col += random.choice([d for d in (-1, 0, 1) if 0 <= col + d < w])
        cells.add((row, col))
    else:
      row = random.randint(0, h - 1)
      cells = {(row, 0)}
      for col in range(1, w):
        row += random.choice([d for d in (-1, 0, 1) if 0 <= row + d < h])
        cells.add((row, col))
  if random.random() < 0.5:
    cells = {(r, w - 1 - c) for r, c in cells}
  if random.random() < 0.5:
    cells = {(h - 1 - r, c) for r, c in cells}
  return kind, cells


def sample_pattern(h, w):
  """Rectangular restatement of _sample_pattern (lines 173-212)."""
  kind = random.choice(['x', 'plus', 'checker', 'blocks', 'ells', 'stripes', 'ring', 'diamond',
                        'sym', 'sym', 'random'])
  allc = [(r, c) for r in range(h) for c in range(w)]

  def mirror(cells):
    out = set()
    for r, c in cells:
      out |= {(r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c)}
    return out

  if kind == 'x':
    return {(r, c) for r, c in allc if c == (r * (w - 1)) // max(1, h - 1) or
            c == w - 1 - (r * (w - 1)) // max(1, h - 1)}
  if kind == 'plus':
    r0, c0 = random.randint(1, h - 2), random.randint(1, w - 2)
    return {(r0, j) for j in range(w)} | {(i, c0) for i in range(h)}
  if kind == 'checker':
    ph = random.randint(0, 1)
    return {(r, c) for r, c in allc if (r + c) % 2 == ph}
  if kind == 'blocks':
    corners = [(0, 0), (0, w - 2), (h - 2, 0), (h - 2, w - 2)]
    out = set()
    for r0, c0 in random.sample(corners, random.randint(1, 4)):
      out |= {(r0 + a, c0 + b) for a in (0, 1) for b in (0, 1)}
    return out
  if kind == 'ells':
    return mirror({(0, 0), (0, 1), (1, 0)})
  if kind == 'stripes':
    step = random.choice([2, 3])
    ph = random.randint(0, step - 1)
    if random.random() < 0.5:
      return {(r, c) for r, c in allc if r % step == ph}
    return {(r, c) for r, c in allc if c % step == ph}
  if kind == 'ring':
    return {(r, c) for r, c in allc if r in (0, h - 1) or c in (0, w - 1)}
  if kind == 'diamond':
    mr, mc = h // 2, w // 2
    k = random.randint(1, max(1, min(mr, mc)))
    return {(r, c) for r, c in allc if abs(r - mr) + abs(c - mc) == k}
  if kind == 'sym':
    return mirror({(r, c) for r in range((h + 1) // 2) for c in range((w + 1) // 2) if random.random() < 0.4})
  return {cell for cell in allc if random.random() < 0.3}


def route(h, w, wall, dreg, p2, p3, c2, c3, bg):
  """Constructor lines 355-363 restated for an H x W panel."""
  res = {}
  for r in range(h):
    for c in range(w):
      if (r, c) in wall:
        res[(r, c)] = c2 if (r, c) in p2 else (c3 if (r, c) in p3 else bg)
      elif (r, c) in dreg:
        res[(r, c)] = c2 if (r, c) in p2 else bg
      else:
        res[(r, c)] = c3 if (r, c) in p3 else bg
  return res


def render(h, w, cols, wall, dot, p2, p3, res):
  f, bg, lc, c2, c3 = cols
  grid = [[f] * (4 * w + 5) for _ in range(h + 2)]
  offs = [1 + k * (w + 1) for k in range(4)]
  for k in range(4):
    for r in range(h):
      for c in range(w):
        grid[1 + r][offs[k] + c] = bg
  for r, c in wall | {dot}:
    grid[1 + r][offs[0] + c] = lc
  for r, c in p2:
    grid[1 + r][offs[1] + c] = c2
  for r, c in p3:
    grid[1 + r][offs[2] + c] = c3
  out = [row[:] for row in grid]
  for (r, c), v in res.items():
    out[1 + r][offs[3] + c] = v
  return {'input': grid, 'output': out}


def build_7491(h, w, require_wall, stats):
  """One scene with every constructor guard (lines 297-369); None after 400 tries."""
  for _ in range(400):
    stats['tries'] += 1
    cols = random.sample(range(10), 5)
    f, bg, lc, c2, c3 = cols
    kind, wall = sample_wall(h, w)
    if len(wall) < 2 or not connected8(wall):
      stats['wall_bad'] += 1
      continue
    regs = regions(h, w, wall)
    if len(regs) != 2 or min(len(x) for x in regs) < 2:
      stats['wall_bad'] += 1
      continue
    options = [sorted(c for c in reg if not near(c, wall)) for reg in regs]
    options = [o for o in options if o]
    if not options:
      stats['no_dot'] += 1
      continue
    dot = random.choice(random.choice(options))
    dreg = regs[0] if dot in regs[0] else regs[1]
    other = regs[1] if dreg is regs[0] else regs[0]
    p2, p3 = sample_pattern(h, w), sample_pattern(h, w)
    lim = h * w - 1
    if not (3 <= len(p2) <= lim and 3 <= len(p3) <= lim) or p2 == p3:
      stats['pattern_bad'] += 1
      continue
    if not (dreg & p2) or not (other & p3):
      stats['region_unshown'] += 1
      continue
    if require_wall and (not (wall & p2 & p3) or not (wall & (p3 - p2))):
      stats['wall_evidence'] += 1
      continue
    if 3 * h * w - (len(wall) + 1) - len(p2) - len(p3) <= max(len(wall) + 1, len(p2), len(p3)):
      stats['fill_dominance'] += 1
      continue
    res = route(h, w, wall, dreg, p2, p3, c2, c3, bg)
    ov2 = {q: c2 if q in p2 else c3 if q in p3 else bg for q in res}
    ov3 = {q: c3 if q in p3 else c2 if q in p2 else bg for q in res}
    if res == ov2 or res == ov3:
      stats['overlay_equal'] += 1
      continue
    stats['accepted'] += 1
    stats['kind_' + kind] += 1
    return render(h, w, cols, wall, dot, p2, p3, res), (cols, wall, dot, p2, p3)
  return None, None


# ================================================================ S. self-tests
print('== S. self-tests (square shapes reproduce the constructor)')
section(1)
m7 = mod('7491f3cf')
ok = 0
for _ in range(100):
  n = random.choice([4, 5, 6])
  st = collections.Counter()
  scene, lat = build_7491(n, n, False, st)
  cols, wall, dot, p2, p3 = lat
  pat = lambda p: [''.join('#' if (r, c) in p else '.' for c in range(n)) for r in range(n)]  # noqa: E731
  try:
    ref = m7.generate(frame=cols[0], background=cols[1], line_color=cols[2], color2=cols[3], color3=cols[4],
                      line=sorted(wall), dot=dot, pattern2=pat(p2), pattern3=pat(p3), panel_size=n,
                      wall_evidence=False)
    ok += ref == scene
  except ValueError:
    pass
print(f'  7491f3cf: rectangular builder at H = W equals generate(**explicit) on {ok}/100 scenes')
section(2)
m9 = mod('973e499e')


def ref_973(g):
  h, w = len(g), len(g[0])
  out = [[0] * (w * w) for _ in range(h * h)]
  for bi in range(h):
    for bj in range(w):
      for r in range(h):
        for c in range(w):
          if g[r][c] == g[bi][bj]:
            out[bi * h + r][bj * w + c] = g[r][c]
  return out


ok = sum(ref_973(p['input']) == p['output'] for p in (m9.generate() for _ in range(200)))
print(f'  973e499e: independent relation equals the constructor on {ok}/200 native draws')
canon_ok = sum(ref_973(p['input']) == p['output'] for p in
               runtime.reference('973e499e')['canonical']['train'] + runtime.reference('973e499e')['canonical']['test'])
print(f'  973e499e: independent relation equals {canon_ok}/5 canonical pairs')

# ================================================================ A. 7491f3cf
print()
print(f'== A. 7491f3cf rectangular panels ({N} scenes per aspect class)')
section(10)
prog7 = program('7491f3cf')
ver7 = runtime.verification_solver('7491f3cf')
for label, shapes in (('tall H > W', [(h, w) for w in range(3, 7) for h in range(w + 1, 13)]),
                      ('wide H < W', [(h, w) for w in range(4, 7) for h in range(3, w)]),
                      ('square H = W 4..6 (control, constructor range)', [(n, n) for n in range(4, 7)]),
                      ('square 3x3 (outside constructor range, reported not filtered)', [(3, 3)])):
  st = collections.Counter()
  made = pa = va = 0
  dims = set()
  first_bad = None
  for j in range(N):
    h, w = random.choice(shapes)
    scene, lat = build_7491(h, w, j % 2 == 0, st)
    if scene is None:
      continue
    made += 1
    dims.add((h, w))
    good = agree(prog7, scene['input'], scene['output'])
    pa += good
    va += agree(ver7, scene['input'], scene['output'])
    if not good and first_bad is None:
      first_bad = (h, w)
  rej = {k: v for k, v in sorted(st.items()) if k not in ('tries', 'accepted') and not k.startswith('kind_')}
  kinds = {k[5:]: v for k, v in sorted(st.items()) if k.startswith('kind_')}
  print(f'  {label}: scenes={made}/{N} panel_shapes={len(dims)} program={pa}/{made} archived_verifier={va}/{made} '
        f'acceptance={st["accepted"]}/{st["tries"]} rejections={rej} wall_kinds={kinds}'
        + (f' first_program_mismatch_shape={first_bad}' if first_bad else ''))
# evidence guard feasibility per panel shape (wall evidence required on every try)
section(11)
feas = []
for h, w in [(3, 6), (8, 3), (10, 5), (12, 6), (28, 6), (20, 4)]:
  st = collections.Counter()
  got = sum(build_7491(h, w, True, st)[0] is not None for _ in range(40))
  feas.append(f'{h}x{w}:{got}/40 (tries {st["tries"]})')
print('  wall-evidence scenes buildable within 400 tries: ' + ', '.join(feas))
section(12)
st = collections.Counter()
big, made, pa = [(28, 6), (25, 5), (20, 6)], 0, 0
for _ in range(60):
  h, w = random.choice(big)
  scene, _ = build_7491(h, w, False, st)
  if scene is None:
    continue
  made += 1
  pa += agree(prog7, scene['input'], scene['output'])
print(f'  extreme tall panels (canvas up to 30x29): scenes={made}/60 program={pa}/{made}')

# ================================================================ B. 973e499e
print()
print(f'== B. 973e499e rectangular inputs ({N} scenes; H, W independent in 2..5)')
section(20)
prog9 = program('973e499e')
ver9 = runtime.verification_solver('973e499e')
by = collections.defaultdict(lambda: [0, 0, 0])
for _ in range(N):
  h, w = random.randint(2, 5), random.randint(2, 5)
  k = random.randint(2, min(4, h * w))
  hues = random.sample(range(1, 10), k)
  while True:
    g = [[random.choice(hues) for _ in range(w)] for _ in range(h)]
    if len({v for row in g for v in row}) == k:
      break
  want = ref_973(g)
  cls = 'square' if h == w else 'rectangular'
  by[cls][0] += 1
  by[cls][1] += agree(prog9, g, want)
  by[cls][2] += agree(ver9, g, want)
for cls in ('rectangular', 'square'):
  n_, p_, v_ = by[cls]
  print(f'  {cls}: scenes={n_} program={p_}/{n_} archived_verifier={v_}/{n_}')
print('  output sizes reached: H^2 x W^2 from 4x4 to 25x25, all <= 30')
