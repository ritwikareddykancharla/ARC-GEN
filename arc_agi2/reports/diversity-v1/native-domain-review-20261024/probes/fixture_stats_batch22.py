"""Batch-22 review probe, read-only. Run from the worktree root with PYTHONPATH=.

Usage: fixture_stats_batch22.py [N] [SEED] [--timing]

Prints the measurements quoted in the batch-22 semantic reviews. Nothing is
written. Constructors are only called. Their latent fixture arguments are
captured by wrapping the module's generate() while validate() runs; the
wrapper is removed afterwards. Certified programs come from the production
lookups (certified_factory_source / certified_source, d4 = 0, identity
palette), which return None unless every recorded hash is current. Every
section reseeds from SEED plus a fixed offset, so the output (without
--timing) is byte-identical between runs.

Sections
  A. canonical fixtures against native sampler guards, for all 32 families:
     the latent canonical parameters (or the canonical grids) are compared
     with the ranges and grammar of the random path. "UNREACHABLE" means a
     canonical input violates a constraint that the random path always
     enforces; it does not mean the fixture is wrong.
  B. N seeded native draws per family: unique inputs, distinct shapes, the
     largest same-shape group, agreement of runtime.verification_solver (the
     check prepare.py applies to every native pair) and of the certified
     program, the canonical episode shape profile, and family-specific
     statistics.
  C. program support past literal caps: constructors driven through their own
     explicit or widened parameter paths, compared with the certified program.
     A pass is evidence of program support, not a certificate.
  --timing: per-draw wall time (not reproducible; excluded from comparisons).
"""
import collections
import itertools
import json
import random
import statistics
import sys
import time

sys.path.insert(0, '.')
import common  # noqa: E402,F401
from arc_agi2 import runtime  # noqa: E402
from arc_agi2.direct_certificates import (certified_factory_source,  # noqa: E402
                                          certified_source)
from arc_agi2.episode_shape_policy import profile_from_task  # noqa: E402

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
N = int(ARGS[0]) if ARGS else 200
SEED = int(ARGS[1]) if len(ARGS) > 1 else 0
TIMING = '--timing' in sys.argv
ID = list(range(10))

IDS = ['4b6b68e5', '50f325b5', '7bb29440', 'a2d730bd', 'c6141b15', 'd6542281',
       'e12f9a14', '269e22fb', '2b9ef948', '5dbc8537', '79369cc6', '7acdf6d3',
       '80a900e0', 'c9680e90', 'cb2d8a2c', 'e4888269', '1a6449f1', '28a6681f',
       '396d80d7', '446ef5d2', '5545f144', '5b692c0f', '64efde09', '825aa9e9',
       '9720b24f', 'bf32578f', 'd4c90558', 'dfadab01', '247ef758', '31f7f899',
       '963f59bc', 'a04b2602']


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
  """(args, kwargs) of every generate() call made by validate(), in order."""
  m = mod(tid)
  orig = m.generate
  calls = []

  def wrap(*a, **k):
    calls.append((a, k))
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


def bbox(cells):
  rs = [r for r, _ in cells]
  cs = [c for _, c in cells]
  return min(rs), min(cs), max(rs), max(cs)


def show(tid, msg):
  print(f'  {tid}: {msg}')


# ======================================================== A. canonical guards
print('== A. canonical fixtures against native guards')
section(1)

# 4b6b68e5: outline count and outline boxes (native: n >= 2 when both sides
# >= 12, box sides <= 11, at most 2 corner notches + 1 side bite).
rows = []
for n, p in enumerate(canon('4b6b68e5')):
  g = p['input']
  by = collections.defaultdict(set)
  for r, row in enumerate(g):
    for c, v in enumerate(row):
      if v:
        by[v].add((r, c))
  walls = [comp for col in by for comp in comps(by[col], eight=False) if len(comp) >= 2]
  boxes = [(b[2] - b[0] + 1, b[3] - b[1] + 1) for b in map(bbox, walls)]
  rows.append(f'pair{n} {len(g)}x{len(g[0])} outlines={len(walls)} boxes={sorted(boxes)}')
show('4b6b68e5', '; '.join(rows))
show('4b6b68e5', 'native n>=max(min(2,cap),1) with cap=min(6,W*H//70)>=2 for W,H>=12 (lines 287-292); '
     'box side <= 11 (line 185)')

# 50f325b5: all-green placements in canonical inputs vs painted copies.
m = mod('50f325b5')
rows = []
for n, p in enumerate(canon('50f325b5')):
  g, o = p['input'], p['output']
  t = [(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] == 8]
  var = m._variants(t)
  pl = m._all_placements(g, var)
  painted = {(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] == 3 and o[r][c] == 8}
  extra = [sorted(x) for x in pl if not x <= painted]
  over = [e for e in extra if set(e) & painted]
  mirror = []
  unm = set()
  cur = list(t)
  for _ in range(4):
    cur = [(c, -r) for r, c in cur]
    unm.add(m._normalize(cur))
  for e in over:
    mirror.append(m._normalize(e) not in unm)
  rows.append(f'pair{n} placements={len(pl)} painted_cells={len(painted)} unpainted_overlapping={len(over)} '
              f'unpainted_is_mirror={mirror}')
show('50f325b5', '; '.join(rows))

# 7bb29440: special-cell adjacency per rectangle (native: sep = no 8-adjacency;
# free = at least one forced 4-adjacent pair; run3 = straight run).
calls = captured('7bb29440')
rows = []
for n, (a, k) in enumerate(calls):
  kinds = []
  for top, left, h, w, sp in k['rects']:
    cells = {(r, c) for r, c, _ in sp}
    four = any((r + a2, c + b2) in cells for r, c in cells for a2, b2 in ((0, 1), (1, 0)))
    diag = any((r + a2, c + b2) in cells for r, c in cells for a2, b2 in ((1, 1), (1, -1)))
    kinds.append('4adj' if four else ('DIAG-ONLY' if diag else 'sep'))
  rows.append(f'pair{n} {kinds}')
show('7bb29440', '; '.join(rows))

# a2d730bd: canonical latent parameters against the random ranges.
calls = captured('a2d730bd')
rows = []
for n, (a, k) in enumerate(calls):
  W, H = k['width'], k['height']
  nb = len(k['wides'])
  area_ok = (nb == 1) if W * H < 250 else ((nb in (1, 2)) if W * H < 500 else nb in (2, 3))
  ok = area_ok
  for w, t in zip(k['wides'], k['talls']):
    tall = t > w
    short, long_ = (w, t) if tall else (t, w)
    lim = (H if tall else W) - 4
    ok &= 2 <= short <= 4 and 7 <= long_ <= min(11, lim)
  rows.append(f'pair{n} {W}x{H} boxes={nb} sizes={list(zip(k["wides"], k["talls"]))} in_native_ranges={ok}')
show('a2d730bd', '; '.join(rows))

# c6141b15: canonical centre sets among the enumerated structured layouts.
m = mod('c6141b15')
rows = []
for n, (a, k) in enumerate(captured('c6141b15')):
  info = m._info(m.SHAPES[k['shape']])
  cs = k['centres']
  r0 = min(r for r, _ in cs)
  c0 = min(c for _, c in cs)
  rel = tuple(sorted((r - r0, c - c0) for r, c in cs))
  hit = [lay for lay in m.STRUCTURED
         if any(tuple(sorted(f[1])) == rel for f in m._structured_candidates(info.cells, lay))]
  rows.append(f'pair{n} {k["shape"]} layout={hit} dir_in_random_set={tuple(k["line_dir"]) in m.UNIT_DIRECTIONS[:4]}')
show('c6141b15', '; '.join(rows))

# d6542281: template boxes, cell and colour counts, fragment component sizes.
m = mod('d6542281')
rows = []
for n, (a, k) in enumerate(captured('d6542281')):
  ts = [m._parse(p) for _, _, p in k['templates']]
  dims = [m._dims(t) for t in ts]
  ok = all(h <= 5 and w <= 5 and 3 <= len(t) <= 12 and 2 <= len(set(t.values())) <= 4
           for t, (h, w) in zip(ts, dims))
  frag = []
  for ti, _, _, vis in k['stamps']:
    for comp in m._components({p: ts[ti][p] for p in map(tuple, vis)}):
      frag.append(len(comp))
  rows.append(f'pair{n} templates={len(ts)} dims={dims} ok={ok} fragment_sizes={sorted(frag)} '
              f'sites={collections.Counter(s[0] for s in k["stamps"])}')
show('d6542281', '; '.join(rows))

# e12f9a14: canonical/teaching scenes through the native cleanliness flags.
m = mod('e12f9a14')
rows = []
for n, (a, k) in enumerate(captured('e12f9a14')):
  seeds = m._normalise_seeds(k['width'], k['height'], k['background'], k['frame_color'], k['seeds'])
  g = m._build_grid(k['width'], k['height'], k['background'], k['frame_color'], seeds)
  _, info = m._simulate(g, k['background'], seeds, k['height'], k['width'])
  cap = max(1, min(5, k['width'] * k['height'] // 80))
  rows.append(f'pair{n} seeds={len(seeds)} cap={cap} flags={[f for f in m.FLAGS if info[f]]}')
show('e12f9a14', '; '.join(rows))

# 2b9ef948: canonical turn lists against the random grammar.
rows = []
for n, (a, k) in enumerate(captured('2b9ef948')):
  t = list(k['turns'])
  body = t[1:] if abs(t[0]) == 1 else t
  ok = 1 <= len(body) <= 3 and all(2 <= abs(x) <= 6 for x in body)
  rows.append(f'pair{n} turns={t} in_grammar={ok}')
show('2b9ef948', '; '.join(rows))

# 5dbc8537: piece dimensions, areas and counts (native: sides <= 6, area <= 24,
# at most 14 pieces without num_pieces).
rows = []
for n, (a, k) in enumerate(captured('5dbc8537')):
  ps = k['pieces']
  dims = [(len(p), len(p[0])) for p, _, _ in ps]
  bad = [d for d in dims if max(d) > 6 or d[0] * d[1] > 24]
  rows.append(f'pair{n} pieces={len(ps)} over_cap={bad}{" COUNT>14" if len(ps) > 14 else ""}')
show('5dbc8537', '; '.join(rows))

# 7acdf6d3: cups and fill partition.
rows = []
for n, (a, k) in enumerate(captured('7acdf6d3')):
  pieces = sorted(len(c) for c in comps(set(map(tuple, k['fill']))))
  rows.append(f'pair{n} cups={[(c[0], c[3], c[4]) for c in k["cups"]]} fill_pieces={pieces}')
show('7acdf6d3', '; '.join(rows) + ' (native: sizes 1..4; pieces [n<=6] | all 1 | runs of 1..3)')

# 80a900e0: badge count, segment counts, minimum side for the badge count.
m = mod('80a900e0')
rows = []
for n, (a, k) in enumerate(captured('80a900e0')):
  pats = k['patterns']
  rows.append(f'pair{n} {k["height"]}x{k["width"]} badges={len(pats)} segs={[len(p[3]) for p in pats]} '
              f'min_side={m.MIN_SIDE[len(pats)]}')
show('80a900e0', '; '.join(rows))

# c9680e90: object count and chain lengths against the grown engine.
rows = []
for n, (a, k) in enumerate(captured('c9680e90')):
  h, w = k['height'], k['width']
  d = (h - 1) // 2
  objs = k['objects']
  rows.append(f'pair{n} {h}x{w} objects={len(objs)} grown_max={max(1, min(8, d * w // 6))} '
              f'chains={sorted(len(c) for _, c in objs)}')
show('c9680e90', '; '.join(rows) + ' (native chain max 6)')

# cb2d8a2c: bars, ones, widths.
rows = []
for n, (a, k) in enumerate(captured('cb2d8a2c')):
  direction, length, width, seed, bars = a
  rows.append(f'pair{n} {direction} L={length} W={width} bars={len(bars)} ones={[b[3] for b in bars]} '
              f'max_bars={(length - 1) // 4}')
show('cb2d8a2c', '; '.join(rows) + ' (native ones <= 4, width >= 7)')

# e4888269: isolated pixels, shapes and shape sizes (native: >= 3 pixels;
# 2..5 shapes without a divider, 0..2 with one; shapes <= 7x7 / 10 cells).
rows = []
for n, (a, k) in enumerate(captured('e4888269')):
  shapes = k.get('shapes') or []
  sizes = sorted(sum(c1 - c0 + 1 for _, c0, c1 in runs) for _, runs in shapes)
  rows.append(f'pair{n} divider={k["divider"] is not None} pixels={len(k["pixels"] or [])} '
              f'shapes={len(shapes)} shape_cells={sizes} legend_rows={len(k["legend"])}')
show('e4888269', '; '.join(rows))

# 1a6449f1: cropped interior of the largest frame (native interior <= 8).
rows = []
for n, (a, k) in enumerate(captured('1a6449f1')):
  rows.append(f'pair{n} interior={k["tall"]}x{k["wide"]} frame={k["tall"] + 2}x{k["wide"] + 2}')
show('1a6449f1', '; '.join(rows) + ' (native frame sides 5..10, interior <= 8)')

# 28a6681f: water components, floating solids, solid column heights.
def terrain_stats(terr):
  """Bottom-anchored column heights and the solids that are not columns."""
  h, w = len(terr), len(terr[0])
  col_h, column = [], set()
  for c in range(w):
    hh = 0
    while hh < h and terr[h - 1 - hh][c]:
      column.add((h - 1 - hh, c))
      hh += 1
    col_h.append(hh)
  solid = {(r, c) for r in range(h) for c in range(w) if terr[r][c]}
  loose = comps(solid - column)
  widths = sorted({n2 for cc in loose for n2 in collections.Counter(r for r, _ in cc).values()})
  return col_h, loose, widths


rows = []
for n, (a, k) in enumerate(captured('28a6681f')):
  terr = [[int(ch) for ch in r] for r in k['terrain']]
  h = len(terr)
  water = comps({tuple(x) for x in k['water']}, eight=False)
  col_h, loose, widths = terrain_stats(terr)
  rows.append(f'pair{n} water_components={len(water)} non_column_solids={len(loose)} '
              f'their_row_widths={widths} max_column={max(col_h)} (native pillar <= {h - 3})')
show('28a6681f', '; '.join(rows))
section(3)
m = mod('28a6681f')
cnt, wid, wat, tallest = collections.Counter(), set(), collections.Counter(), 0
for _ in range(300):
  p = m.generate()
  terr = [[v if v != 1 else 0 for v in row] for row in p['input']]
  col_h, loose, widths = terrain_stats(terr)
  cnt[len(loose)] += 1
  wid |= set(widths)
  tallest = max(tallest, max(col_h) - (len(terr) - 3))
  wat[len(comps({(r, c) for r, row in enumerate(p['input']) for c, v in enumerate(row) if v == 1},
                eight=False))] += 1
show('28a6681f', f'self-test on 300 native inputs: non_column_solids={dict(sorted(cnt.items()))} '
     f'row_widths={sorted(wid)} water_components={dict(sorted(wat.items()))} '
     f'max(column - (h-3))={tallest}')

# 396d80d7: figure size, symmetry and inner box (fixtures are compact lattices).
rows = []
for n, p in enumerate(canon('396d80d7')):
  g = p['input']
  cells = {(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] != 7}
  b = bbox(cells)
  lr = cells == {(r, b[1] + b[3] - c) for r, c in cells}
  ud = cells == {(b[0] + b[2] - r, c) for r, c in cells}
  rows.append(f'pair{n} fig={b[2] - b[0] + 1}x{b[3] - b[1] + 1} lr={lr} ud={ud} components8={len(comps(cells))}')
show('396d80d7', '; '.join(rows))

# 446ef5d2: accent components against the decorate() kinds, piece shapes.
def accent_kind(cells, ih, iw):
  r0, c0, r1, c1 = bbox(cells)
  sh, sw = r1 - r0 + 1, c1 - c0 + 1
  s = set(cells)
  if sh == 1 or sw == 1:
    return 'bar' if len(s) == sh * sw else 'X'
  ring = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
          if r in (r0, r1) or c in (c0, c1)}
  if s == ring and sh >= 3 and sw >= 3:
    return 'ring'
  holes = sh * sw - len(s)
  if sh <= 4 and sw <= 6 and holes <= max(1, sh * sw // 4) and (holes == 0 or (sh >= 2 and sw >= 2)):
    return 'block'
  return f'X({sh}x{sw},holes={holes})'


rows = []
for n, (a, k) in enumerate(captured('446ef5d2')):
  rect = [[int(ch) for ch in r] for r in k['rect_rows']]
  h, w = len(rect), len(rect[0])
  frame = rect[0][0]
  kinds = []
  for col in sorted({v for r in rect for v in r} - {frame}):
    for comp in comps({(r, c) for r in range(h) for c in range(w) if rect[r][c] == col}):
      kinds.append(accent_kind(comp, h - 2, w - 2))
  labs = [list(r) for r in k['labels']]
  groups = collections.defaultdict(list)
  for r, row in enumerate(labs):
    for c, v in enumerate(row):
      groups[v].append((r, c))
  rect_pieces = sum(len(v) == (bbox(v)[2] - bbox(v)[0] + 1) * (bbox(v)[3] - bbox(v)[1] + 1)
                    for v in groups.values())
  rows.append(f'pair{n} rect={h}x{w} accents={kinds} pieces={len(groups)} rectangular_pieces={rect_pieces}')
show('446ef5d2', '; '.join(rows) + ' (X = not a native ring/block/bar)')
section(4)
m = mod('446ef5d2')
kinds = collections.Counter()
for _ in range(300):
  h, w = random.randint(4, 12), random.randint(4, 20)
  rect, _ = m._decorate(h, w, 1, [2, 3, 4])
  for col in (2, 3, 4):
    for comp in comps({(r, c) for r in range(h) for c in range(w) if rect[r][c] == col}):
      kinds['X' if accent_kind(comp, h - 2, w - 2).startswith('X') else 'native-kind'] += 1
show('446ef5d2', f'classifier self-test on 300 native rectangles: {dict(sorted(kinds.items()))}')
rect_pieces = all_pieces = 0
for _ in range(300):
  h, w = random.randint(4, 12), random.randint(4, 20)
  k = random.randint(3, max(3, min(10, h * w // 8)))
  groups = collections.defaultdict(list)
  for r, row in enumerate(m._partition(h, w, k)):
    for c, v in enumerate(row):
      groups[v].append((r, c))
  for v in groups.values():
    b = bbox(v)
    all_pieces += 1
    rect_pieces += len(v) == (b[2] - b[0] + 1) * (b[3] - b[1] + 1)
show('446ef5d2', f'native _partition: rectangular pieces {rect_pieces}/{all_pieces} '
     f'(canonical: 4/4, 4/4, 8/10, 6/6)')

# 5545f144: dot spacing and shown-shape halo guards of the random path.
m = mod('5545f144')
rows = []
for n, (a, k) in enumerate(captured('5545f144')):
  path = [tuple(q) for q in k['path']]
  sh = k['shape']
  tip, d = tuple(k['tip']), tuple(k['direction'])
  spaced = all(max(abs(p[0] - q[0]), abs(p[1] - q[1])) > 1 for p, q in itertools.combinations(path, 2))
  dirs = m._directions(tip, path)
  halo_ok = not (set(path) & m._halo(m._place(sh, tip, d)))
  for i in range(1, len(path)):
    halo = m._halo(m._place(sh, path[i - 1], dirs[i - 1]))
    halo_ok &= not any(q in halo for q in path[i:])
  hi = max(2, min(12, k['height'] * k['width'] // 10))
  depth = -min(a2 for a2, _ in sh)
  hw = max(abs(b2) for _, b2 in sh)
  rows.append(f'pair{n} eats={len(path)} (<= {hi}) panels={k["num_panels"]} spaced={spaced} halo={halo_ok} '
              f'shape_depth={depth} half_width={hw}')
show('5545f144', '; '.join(rows))

# 5b692c0f: per shape: along-axis length (<= 9), intact-half extent (<= 5) and
# the forced cell next to the axis in every row of the intact half.
rows = []
for n, (a, k) in enumerate(captured('5b692c0f')):
  parts = []
  for s in k['shapes']:
    cells = {}
    for r, row in enumerate(s['rows']):
      for c, ch in enumerate(row):
        if ch != '0':
          cells[(s['top'] + r, s['left'] + c)] = int(ch)
    v, ax, side = s['vertical'], s['axis'], s['side']
    along = sorted({p[0] if v else p[1] for p in cells})
    main = [col for col in cells.values() if col != 4][0]
    gaps = [y for y in range(along[0], along[-1] + 1)
            if cells.get((y, ax + side) if v else (ax + side, y)) != main]
    ext = max(abs((p[1] if v else p[0]) - ax) for p, col in cells.items()
              if ((p[1] if v else p[0]) - ax) * side > 0)
    parts.append(f'len={len(along)} intact_ext={ext} missing_next_to_axis={len(gaps)}')
  rows.append(f'pair{n} [' + ' | '.join(parts) + ']')
show('5b692c0f', '; '.join(rows))
section(5)
m = mod('5b692c0f')
worst_len = worst_ext = missing_total = shapes_seen = 0
for _ in range(300):
  _, _, specs = m._random_scene(None, None, None)
  for cells, v, ax, side in specs:
    shapes_seen += 1
    along = sorted({p[0] if v else p[1] for p in cells})
    main = [col for col in cells.values() if col != 4][0]
    missing_total += sum(cells.get((y, ax + side) if v else (ax + side, y)) != main
                         for y in range(along[0], along[-1] + 1))
    worst_len = max(worst_len, len(along))
    worst_ext = max(worst_ext, max(abs((p[1] if v else p[0]) - ax) for p in cells
                                   if ((p[1] if v else p[0]) - ax) * side > 0))
show('5b692c0f', f'self-test on {shapes_seen} native shapes: max len={worst_len} max intact_ext={worst_ext} '
     f'missing_next_to_axis total={missing_total}')

# 64efde09: lengths, marker indices, device and marker counts, sizes.
rows = []
for n, (a, k) in enumerate(captured('64efde09')):
  L = len(k['far'])
  idx = [x[1] for x in k['markers']]
  rows.append(f'pair{n} {k["height"]}x{k["width"]} L={L} devices={len(k["devices"])} markers={len(idx)} '
              f'indices_in_1..L-2={all(1 <= i <= L - 2 for i in idx)}')
show('64efde09', '; '.join(rows))

# 825aa9e9: canonical skylines against the five ground styles.
def styles(hts, h):
  w = len(hts)
  cap = max(1, h - 4)
  out = []
  vals = set(hts)
  if (len(vals - {0}) == 1 and hts.count(0) <= 1 and max(hts) in range(1, min(2, cap) + 1)):
    out.append('flat')
  if all(0 <= x <= cap for x in hts) and all(abs(a2 - b2) <= 1 for a2, b2 in zip(hts, hts[1:])):
    out.append('skyline')
  for period in (4, 5, 6):
    for off in range(period):
      for base in (0, 1):
        if hts == [h if (c - off) % period == 0 else base for c in range(w)]:
          out.append('pillars')
  for lo in (0, 1):
    for hi in range(lo + 1, min(cap, lo + 2) + 1):
      for phase in (0, 1):
        alt = [hi if (c + phase) % 2 == 0 else lo for c in range(w)]
        if hts == alt or any(hts == alt[:a2] + [lo] * (w - a2) for a2 in range(w)):
          out.append('stubs')
  if len(vals) == 2:
    for wall in range(1, max(1, h - 2) + 1):
      for floor in range(0, min(wall - 1, cap) + 1):
        if vals == {wall, floor}:
          idx = [c for c in range(w) if hts[c] == floor]
          if idx == list(range(idx[0], idx[-1] + 1)) and idx[0] <= w - 3 and idx[-1] >= idx[0] + 1:
            out.append('pocket')
  return sorted(set(out))


rows = []
for n, (a, k) in enumerate(captured('825aa9e9')):
  w, h, hts = a[0], a[1], list(a[2])
  rows.append(f'pair{n} h={h} heights={hts} styles={styles(hts, h) or "NONE"}')
show('825aa9e9', '; '.join(rows))

# 9720b24f: grid and container boxes; container outlines against the
# octagon / thickening / gap geometry of _build_container (exhaustive over
# corner cuts; thickening and gap are matched as runs on one side each).
m = mod('9720b24f')


def outline_reachable(cells):
  r0, c0, r1, c1 = bbox(cells)
  h, w = r1 - r0 + 1, c1 - c0 + 1
  if not (m._MIN_BOX <= h <= m._MAX_BOX and m._MIN_BOX <= w <= m._MAX_BOX):
    return False
  target = {(r - r0, c - c0) for r, c in cells}
  top = min(h, w) // 2 + 1
  for ks in itertools.product(range(top + 1), repeat=4):
    tl, tr, br, bl = ks
    if not (tl + tr <= w - 1 and bl + br <= w - 1 and tl + bl <= h - 1 and tr + br <= h - 1):
      continue
    verts = [(0, tl), (0, w - 1 - tr), (tr, w - 1), (h - 1 - br, w - 1),
             (h - 1, w - 1 - br), (h - 1, bl), (h - 1 - bl, 0), (tl, 0)]
    segs = [m._line(*verts[i], *verts[(i + 1) % 8]) for i in range(8)]
    base = set().union(*map(set, segs))
    extra, missing = target - base, base - target
    # Thickening: one straight side shifted inward (looser than the native
    # contiguous-run rule, so a False here is conservative).
    thick_opts = [None] if not extra else [
        i for i, (dr, dc) in m._INWARD.items()
        if extra <= {(r + dr, c + dc) for r, c in segs[i]}]
    for thick in thick_opts:
      if not missing:
        return True
      for j in range(8):
        if j == thick or len(segs[j]) < 3:
          continue
        mid = segs[j][1:-1]
        if missing <= set(mid):
          idx = sorted(mid.index(p) for p in missing)
          if idx == list(range(idx[0], idx[-1] + 1)):
            return True
  return False


rows = []
for n, (a, k) in enumerate(captured('9720b24f')):
  res = [outline_reachable([tuple(p) for p in cells]) for _, cells in k['containers']]
  boxes = [(lambda b: (b[2] - b[0] + 1, b[3] - b[1] + 1))(bbox([tuple(p) for p in c])) for _, c in k['containers']]
  rows.append(f'pair{n} grid={k["height"]}x{k["width"]} container_boxes={boxes} outline_reachable={res} '
              f'loose={len(k["loose"])}')
show('9720b24f', '; '.join(rows) + ' (native grid >= 7, boxes 4..11)')
section(2)
acc = tot = 0
for _ in range(300):
  w, h = m._pick_dims(None, None, random.randint(1, 3))
  cons, _, _ = m._random_scene(w, h, random.randint(1, min(3, m._cap(w, h))))
  for _, cells in cons:
    tot += 1
    acc += outline_reachable(cells)
show('9720b24f', f'checker self-test: accepts {acc}/{tot} native containers')

# d4c90558: frame thickness and interior size (native: thickness 1..3,
# interior 3..8 x 3..9, grey count <= 12).
rows = []
for n, (a, k) in enumerate(captured('d4c90558')):
  parts = []
  for col, r0, c0, r1, c1, (t, b, l, r), greys in k['frames']:
    ih, iw = r1 - r0 + 1 - t - b, c1 - c0 + 1 - l - r
    bad = max(t, b, l, r) > 3 or not (3 <= ih <= 8 and 3 <= iw <= 9) or len(greys) > 12
    parts.append(f'{col}:thick={(t, b, l, r)} interior={ih}x{iw}{" OUT" if bad else ""}')
  rows.append(f'pair{n} [' + ', '.join(parts) + ']')
show('d4c90558', '; '.join(rows))

# dfadab01: lattice steps and legend.
rows = []
for n, (a, k) in enumerate(captured('dfadab01')):
  rs = sorted({r for r, _, _ in k['markers']})
  cs = sorted({c for _, c, _ in k['markers']})
  rows.append(f'pair{n} {k["height"]}x{k["width"]} legend={k["legend"]} row_gaps={[b - a2 for a2, b in zip(rs, rs[1:])]} '
              f'col_gaps={[b - a2 for a2, b in zip(cs, cs[1:])]} markers={len(k["markers"])}')
show('dfadab01', '; '.join(rows))

# 247ef758: legend gaps/overlaps, top/bottom marker consistency, corners.
rows = []
for n, (a, k) in enumerate(captured('247ef758')):
  mots = sorted(k['motifs'], key=lambda x: x[1])
  gaps = [mots[i + 1][1] - (mots[i][1] + len(mots[i][3])) for i in range(len(mots) - 1)]
  fw = k['frame_width']
  corner = [o for o in list(k['top_marks']) + list(k['bottom_marks']) if o in (0, fw - 1)]
  tb = collections.defaultdict(lambda: [set(), set()])
  for o, col in k['top_marks'].items():
    tb[col][0].add(o)
  for o, col in k['bottom_marks'].items():
    tb[col][1].add(o)
  mism = sorted(col for col, (t, b) in tb.items() if t != b and t and b)
  rows.append(f'pair{n} legend_gaps={gaps} corner_marks={corner} top_bottom_mismatch_colours={mism}')
show('247ef758', '; '.join(rows) + ' (native gaps 0..1, no corner marks, matched or one-sided columns)')
section(6)
m = mod('247ef758')
gap_set, corners, mism = set(), 0, 0
for _ in range(300):
  k = m._sample_scene()
  mots = sorted(k['motifs'], key=lambda x: x[1])
  gap_set |= {mots[i + 1][1] - (mots[i][1] + len(mots[i][3])) for i in range(len(mots) - 1)}
  fw = k['frame_width']
  corners += sum(o in (0, fw - 1) for o in list(k['top_marks']) + list(k['bottom_marks']))
  tb = collections.defaultdict(lambda: [set(), set()])
  for o, col in k['top_marks'].items():
    tb[col][0].add(o)
  for o, col in k['bottom_marks'].items():
    tb[col][1].add(o)
  mism += any(t != b and t and b for t, b in tb.values())
show('247ef758', f'self-test on 300 native scenes: legend gaps={sorted(gap_set)} corner marks={corners} '
     f'scenes with top/bottom column mismatch={mism}')

# 31f7f899: bar count, widths, leftover and extent margins.
rows = []
for n, (a, k) in enumerate(captured('31f7f899')):
  bars, h, lr = k['bars'], k['height'], k['line_row']
  widths = [b[1] for b in bars]
  ok = (3 <= len(bars) <= 6 and all(x in (1, 2, 3) for x in widths)
        and k['width'] - sum(widths) >= 2
        and all(lr - b[3] <= lr - 1 and b[4] - lr <= h - 2 - lr for b in bars))
  rows.append(f'pair{n} bars={len(bars)} widths={widths} in_native_ranges={ok}')
show('31f7f899', '; '.join(rows))

# 963f59bc: shape box, symmetry, marker sides.
m = mod('963f59bc')
rows = []
for n, (a, k) in enumerate(captured('963f59bc')):
  shp = [tuple(p) for p in k['shape']]
  b = bbox(shp)
  sym = m._sym_lr(shp) or m._sym_ud(shp) or m._sym_rot(shp)
  sides = []
  for r, c, _ in k['markers']:
    if b[0] <= r <= b[2]:
      sides.append('right' if c > b[3] else 'left')
    else:
      sides.append('down' if r > b[2] else 'up')
  s = set(shp)

  def walk(lines, cell_of):
    # One cell per line, consecutive cells differing by at most 1 across.
    reach = {x for x in range(-1, 40) if cell_of(lines[0], x) in s}
    for ln in lines[1:]:
      reach = {x for x in range(-1, 40) if cell_of(ln, x) in s
               and any(abs(x - y) <= 1 for y in reach)}
    return bool(reach)

  walks = (walk(list(range(b[0], b[2] + 1)), lambda r, c: (r, c)) and
           walk(list(range(b[1], b[3] + 1)), lambda c, r: (r, c)))
  rows.append(f'pair{n} box={b[2] - b[0] + 1}x{b[3] - b[1] + 1} symmetric={sym} sides={sides} '
              f'king_walks={walks}')
show('963f59bc', '; '.join(rows) + ' (random shapes start from a row walk and a column walk)')

# bf32578f: canonical offsets reachable by _sample_shape.
rows = []
for n, (a, k) in enumerate(captured('bf32578f')):
  offs, cap = k['offsets'], k['cap']
  steps = [b - a2 for a2, b in zip(offs, offs[1:])]
  rows.append(f'pair{n} offsets={offs} cap={cap} d={offs[-1]} steps={steps} '
              f'reachable={offs[0] == 0 and (cap > 0 or offs[-1] >= 1)}')
show('bf32578f', '; '.join(rows))

# a04b2602: separation of the green boxes (native: overlaps(..., 2) is false).
rows = []
for n, p in enumerate(canon('a04b2602')):
  g = p['input']
  greens = {(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] == 3}
  boxes = [bbox(cc) for cc in comps(greens) if len(cc) > 4]
  gaps = []
  for x, y in itertools.combinations(boxes, 2):
    rg = max(y[0] - x[2], x[0] - y[2]) - 1
    cg = max(y[1] - x[3], x[1] - y[3]) - 1
    gaps.append(max(rg, cg))
  rows.append(f'pair{n} boxes={len(boxes)} min_gap={min(gaps) if gaps else None}')
show('a04b2602', '; '.join(rows) + ' (native needs gap >= 2)')

# 79369cc6: blocked near-copies present in the canonical inputs.
m = mod('79369cc6')
rows = []
for n, (a, k) in enumerate(captured('79369cc6')):
  ex, bl = m._scan(k['background'], k['motif'], k['motif_row'], k['motif_col'])
  rows.append(f'pair{n} exact={len(ex)} blocked={len(bl)} copies={len(k["copies"])}')
show('79369cc6', '; '.join(rows) + ' (motif always 3x3)')

# 269e22fb: canonical crops come from one fixed 20x20 picture.
rows = []
for n, (a, k) in enumerate(captured('269e22fb')):
  rows.append(f'pair{n} crop={k["height"]}x{k["width"]}@({k["row"]},{k["col"]})')
show('269e22fb', '; '.join(rows) + ' (random path never uses the canonical picture)')


# ======================================================== B. native draws
print()
print(f'== B. {N} seeded native draws per family')


def stat_396(pairs):
  one = 0
  for p in pairs:
    g = p['input']
    cells = {(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] != 7}
    one += len(comps(cells)) == 1
  return f'figure_one_8component={one}/{len(pairs)}'


def stat_4b6(pairs):
  cnt = collections.Counter()
  for p in pairs:
    g = p['input']
    by = collections.defaultdict(set)
    for r, row in enumerate(g):
      for c, v in enumerate(row):
        if v:
          by[v].add((r, c))
    cnt[sum(1 for col in by for comp in comps(by[col], eight=False) if len(comp) >= 2)] += 1
  return f'outline_counts={dict(sorted(cnt.items()))}'


def stat_7bb(pairs):
  kinds = collections.Counter()
  for p in pairs:
    g = p['input']
    nonzero = {(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c]}
    for rect in comps(nonzero):
      s = {q for q in rect if g[q[0]][q[1]] in (4, 6)}
      four = any((r + a2, c + b2) in s for r, c in s for a2, b2 in ((0, 1), (1, 0)))
      diag = any((r + a2, c + b2) in s for r, c in s for a2, b2 in ((1, 1), (1, -1)))
      kinds['4adj' if four else ('DIAG-ONLY' if diag else 'sep')] += 1
  return f'rect_special_adjacency={dict(sorted(kinds.items()))}'


def stat_50f(pairs):
  m2 = mod('50f325b5')
  over = 0
  for p in pairs:
    g, o = p['input'], p['output']
    t = [(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] == 8]
    painted = {(r, c) for r in range(len(g)) for c in range(len(g[0])) if o[r][c] == 8 and g[r][c] == 3}
    over += any(not x <= painted for x in m2._all_placements(g, m2._variants(t)))
  return f'scenes_with_unpainted_placement={over}'


def stat_793(pairs):
  def share(g):
    return sum(row.count(6) for row in g) / (len(g) * len(g[0]))
  nat = sorted(share(p['input']) for p in pairs)
  can = [round(share(p['input']), 3) for p in canon('79369cc6')]
  return (f'six_share native median={statistics.median(nat):.3f} range={nat[0]:.3f}..{nat[-1]:.3f} '
          f'canonical={can}')


EXTRA = {'396d80d7': stat_396, '4b6b68e5': stat_4b6, '7bb29440': stat_7bb, '50f325b5': stat_50f,
         '79369cc6': stat_793}

for off, tid in enumerate(IDS):
  section(100 + off)
  m = mod(tid)
  check = runtime.verification_solver(tid)
  prog, kind = program(tid)
  pairs, errors = [], 0
  for _ in range(N):
    try:
      pairs.append(m.generate())
    except Exception:  # noqa: BLE001
      errors += 1
  ver = prg = 0
  for p in pairs:
    try:
      ver += runtime.grid(runtime.call(check, p['input'], seconds=5)) == p['output']
    except Exception:  # noqa: BLE001
      pass
    if prog is not None and tid != '269e22fb':
      try:
        prg += runtime.call(prog, p['input'], seconds=5) == p['output']
      except Exception:  # noqa: BLE001
        pass
  shapes = collections.Counter((len(p['input']), len(p['input'][0])) for p in pairs)
  uniq = len({key(p['input']) for p in pairs})
  prof = profile_from_task(runtime.reference(tid)['canonical'])['patterns']
  pats = sorted({(x['demo_input_shapes'], x['query_input_shape']) for x in prof})
  extra = EXTRA[tid](pairs) if tid in EXTRA else ''
  prog_txt = 'n/a (episode-conditioned)' if tid == '269e22fb' else f'{prg}/{len(pairs)}'
  print(f'  {tid}: valid={len(pairs)}/{N} unique={uniq} shapes={len(shapes)} '
        f'max_same_shape={max(shapes.values())} verifier={ver}/{len(pairs)} program[{kind}]={prog_txt} '
        f'canonical_profile={pats} {extra}'.rstrip())

# 269e22fb is episode-shared: check the documented contextual verifier.
section(199)
from arc_agi2.contextual import verify_shared_picture_episode  # noqa: E402
m = mod('269e22fb')
ok = 0
for _ in range(min(N, 50)):
  ep = m.generate_episode()
  try:
    verify_shared_picture_episode(ep)
    ok += 1
  except Exception:  # noqa: BLE001
    pass
print(f'  269e22fb: generate_episode + contextual verifier: {ok}/{min(N, 50)} episodes')


# ======================================================== C. past literal caps
print()
print('== C. certified programs past native literal caps (constructor as reference)')


def compare(tid, make, count):
  prog, kind = program(tid)
  okc = tot = 0
  shapes = set()
  for _ in range(count * 6):
    if tot >= count:
      break
    try:
      p = make()
    except Exception:  # noqa: BLE001
      continue
    tot += 1
    shapes.add((len(p['input']), len(p['input'][0])))
    try:
      okc += prog(p['input']) == p['output']
    except Exception:  # noqa: BLE001
      pass
  return f'{okc}/{tot} [{kind}] shapes={len(shapes)}'


# a2d730bd: boxes with long side 12..20 on large canvases.
section(301)
m = mod('a2d730bd')


def a2d():
  W, H = random.randint(24, 30), random.randint(24, 30)
  d = random.randint(0, 1)
  long_ = random.randint(12, min(20, (H if d else W) - 4))
  short = random.randint(2, 4)
  wide, tall = (short, long_) if d else (long_, short)
  brow = random.randint(2, H - tall - 2)
  bcol = random.randint(2, W - wide - 2)
  col = random.randint(1, 9)
  bg = random.choice([c for c in range(1, 10) if c != col])
  n = random.randint(1, 3)
  if d:
    prows = random.sample(range(brow + 1, brow + tall - 1), n)
    pcols = random.sample(list(range(1, bcol - 2)) + list(range(bcol + wide + 2, W - 1)), n)
  else:
    prows = random.sample(list(range(1, brow - 2)) + list(range(brow + tall + 2, H - 1)), n)
    pcols = random.sample(range(bcol + 1, bcol + wide - 1), n)
  p = m.generate(width=W, height=H, bgcolor=bg, wides=[wide], talls=[tall], brows=[brow],
                 bcols=[bcol], bcolors=[col], prows=prows, pcols=pcols, pcolors=[col] * n)
  if p['input'] is None:
    raise ValueError
  return p


print(f'  a2d730bd long side 12..20: {compare("a2d730bd", a2d, 200)}')

# 2b9ef948: segment lengths 7..10.
section(302)
m = mod('2b9ef948')


def b9e():
  W, H = random.randint(20, 30), random.randint(20, 30)
  turns = [1 if random.randint(0, 1) else -1] if random.randint(0, 1) else []
  turns += [random.choice((1, -1)) * random.randint(7, 10) for _ in range(random.randint(1, 3))]
  p = m.generate(width=W, height=H, color=random.choice([1, 2, 3, 6, 7, 8, 9]),
                 brow=random.randint(2, H - 3), bcol=random.randint(2, W - 3),
                 prow=random.randint(1, H - 2), pcol=random.randint(1, W - 2), turns=turns)
  if p['input'] is None:
    raise ValueError
  return p


print(f'  2b9ef948 segments 7..10: {compare("2b9ef948", b9e, 200)}')

# 7acdf6d3: cup sizes 5..6 through a widened shape table.
section(303)
m = mod('7acdf6d3')
saved = m._SHAPES
m._SHAPES = ([('V', k, 0) for k in range(1, 7)] +
             [('U', w, h) for w in range(1, 7) for h in range(1, 7)])
try:
  print(f'  7acdf6d3 cup sizes 1..6 (table widened in-process): '
        f'{compare("7acdf6d3", lambda: m.generate(width=random.randint(18, 30), height=random.randint(18, 30)), 200)}')
finally:
  m._SHAPES = saved

# cb2d8a2c: up to 6 ones per bar through a widened cap.
section(304)
m = mod('cb2d8a2c')
saved = m._MAX_ONES
m._MAX_ONES = 6
try:
  print(f'  cb2d8a2c ones 1..6 (cap widened in-process): '
        f'{compare("cb2d8a2c", lambda: m.generate(width=random.randint(16, 30)), 200)}')
finally:
  m._MAX_ONES = saved

# 963f59bc: shape boxes 6..8 (explicit control).
section(305)
m = mod('963f59bc')
print(f'  963f59bc boxes 6..8: '
      f'{compare("963f59bc", lambda: m.generate(box_height=random.randint(6, 8), box_width=random.randint(6, 8)), 200)}')

# c9680e90: chains up to 12 (explicit control).
section(306)
m = mod('c9680e90')
print(f'  c9680e90 chains <= 12: '
      f'{compare("c9680e90", lambda: m.generate(max_chain_length=12), 200)}')

# 5545f144: 13..20 eats (explicit control).
section(307)
m = mod('5545f144')
print(f'  5545f144 eats 13..20: '
      f'{compare("5545f144", lambda: m.generate(num_eats=random.randint(13, 20), height=30, width=30, num_panels=1), 100)}')

# 64efde09: device lengths 11..14 (explicit template length).
section(308)
m = mod('64efde09')


def d64():
  L = random.randint(11, 14)
  a2, b2, e = random.sample([c for c in range(10) if c != 8], 3)
  return m.generate(width=30, height=30, far=[a2, a2] + [b2] * (L - 3) + [e])


print(f'  64efde09 device length 11..14: {compare("64efde09", d64, 200)}')

# 31f7f899: 7..9 bars.
section(309)
m = mod('31f7f899')


def f31():
  W = random.randint(20, 30)
  H = random.randint(9, 30)
  lr = random.randint(2, H - 3)
  n = random.randint(7, 9)
  xs = sorted(random.sample(range(0, W, 2), n))
  bars, by_len = [], {}
  for x in xs:
    for _ in range(30):
      t, b = lr - random.randint(0, lr - 1), lr + random.randint(0, H - 2 - lr)
      L = b - t
      if by_len.get(L, (t, b)) == (t, b):
        by_len[L] = (t, b)
        bars.append((x, 1, random.choice([0, 1, 2, 3, 4, 5, 7, 9]), t, b))
        break
  if len(bars) != n or W - n < n + 1:
    raise ValueError
  return m.generate(width=W, height=H, line_row=lr, bars=bars, vertical=False)


print(f'  31f7f899 7..9 bars: {compare("31f7f899", f31, 200)}')


# ======================================================== timing (optional)
if TIMING:
  print()
  print(f'== timing over {N} draws (wall clock, not reproducible)')
  for off, tid in enumerate(IDS):
    section(400 + off)
    m = mod(tid)
    ts = []
    for _ in range(N):
      t0 = time.perf_counter()
      try:
        m.generate()
      except Exception:  # noqa: BLE001
        pass
      ts.append(time.perf_counter() - t0)
    print(f'  {tid}: median={statistics.median(ts) * 1000:.1f}ms max={max(ts) * 1000:.0f}ms '
          f'over_2s={sum(t > 2 for t in ts)}')
