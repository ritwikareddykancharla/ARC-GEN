"""Input-only evidence for 1b8318e3 pixel docking.

Independent from the emitted factory: a pairwise ordering tournament and
transitive closure enumerate possible hidden native pixel orders. The factory
uses winner branching with cycle checks. No constructor, expected query grid,
D4 selector, or emitted-program helper is used here.

Labels prune demonstration consistency only. Query outputs are never read.
Native clamp ambiguity is intrinsic; ambiguity or disagreement from the
alternative king rule is insufficient demonstration context on native-unique inputs. A caller may redraw the
context in the latter case while retaining the query.
"""
from .colour_evidence import MissingColourEvidence, IntrinsicQueryEvidence, EvidenceSearchBudget

class IntrinsicDockingAmbiguity(IntrinsicQueryEvidence):
    """The native clamp mechanism has several outputs for the same input."""

class DockingContextAmbiguity(MissingColourEvidence):
    """Demonstrations leave incompatible query predictions across rules."""

class DockingSearchBudget(EvidenceSearchBudget):
    """Uniqueness was not established within the enumeration budget."""

REACH = 4


def scene(grid):
    """Visible scene -> native generate() arguments (pixel order arbitrary)."""
    n = len(grid)
    if not n or any(len(r) != n for r in grid):
        raise ValueError('docking scenes must be nonempty and square')
    brows, bcols, prows, pcols, pcolors = [], [], [], [], []
    for r in range(n):
        for c in range(n):
            v = grid[r][c]
            if v == 5:
                if (r == 0 or grid[r - 1][c] != 5) and (c == 0 or grid[r][c - 1] != 5):
                    brows.append(r)
                    bcols.append(c)
            elif v != 0:
                prows.append(r)
                pcols.append(c)
                pcolors.append(v)
    wall = {(r, c) for r in range(n) for c in range(n) if grid[r][c] == 5}
    covered = set()
    for r, c in zip(brows, bcols):
        block = {(r + dy, c + dx) for dy in (0, 1) for dx in (0, 1)}
        if not block <= wall or block & covered:
            raise ValueError('box must be one complete separated 2x2 block')
        covered.update(block)
    if covered != wall or not covered or not prows:
        raise ValueError('missing or malformed box/pixel scene')
    return n, brows, bcols, prows, pcols, pcolors


def site_native(prow, pcol, brow, bcol, occupied):
    r, c = prow, pcol
    if pcol < bcol: c = bcol - 1
    if prow < brow: r = brow - 1
    if pcol > bcol + 1: c = bcol + 2
    if prow > brow + 1: r = brow + 2
    return None if (r, c) in occupied else (r, c)


def site_king(prow, pcol, brow, bcol, occupied):
    """Alternative 'king-move approach' reading (fits canonical train 1)."""
    r, c = prow, pcol
    if pcol < bcol: c = bcol - 1
    if prow < brow: r = brow - 1
    if pcol > bcol + 1: c = bcol + 2
    if prow > brow + 1: r = brow + 2
    dr, dc = abs(prow - r), abs(pcol - c)
    if dr and dc and dr != dc:
        if dr > dc:
            alt = (r, bcol if c < bcol else bcol + 1)
        else:
            alt = (brow if r < brow else brow + 1, c)
        if alt not in occupied:
            return alt
    return None if (r, c) in occupied else (r, c)


class Budget(Exception):
    pass


def enumerate_outputs(args, site=site_native, check_label=None, limit=None, budget=300000):
    """Return list of (output_grid, total_order) for every realisable outcome."""
    size, brows, bcols, prows, pcols, pcolors = args
    n = len(prows)
    found = {}
    count = [0]

    def closure_add(less, a, b):
        # add a<b and close transitively; less is a list of sets (successors)
        new = [set(s) for s in less]
        preds = [x for x in range(n) if a in new[x]] + [a]
        succs = list(new[b]) + [b]
        for x in preds:
            new[x].update(succs)
        return new

    def draw_output(orows, ocols):
        out = [[0] * size for _ in range(size)]
        for br, bc in zip(brows, bcols):
            for i in range(2):
                for j in range(2):
                    out[br + i][bc + j] = 5
        for orow, ocol, col in zip(orows, ocols, pcolors):
            if out[orow][ocol] != 0:
                return None
            out[orow][ocol] = col
        return out

    def topo(less):
        rank = sorted(range(n), key=lambda x: -len(less[x]))
        return rank  # x before y whenever y in less[x] (|succ(x)| > |succ(y)|)

    def step(orows, ocols, less):
        count[0] += 1
        if count[0] > budget:
            raise Budget()
        if limit is not None and len(found) >= limit:
            return
        occupied = set(zip(orows, ocols))
        matches = []
        for p in range(n):
            if orows[p] != -1:
                continue
            min_dist, min_list = None, []
            for brow, bcol in zip(brows, bcols):
                s = site(prows[p], pcols[p], brow, bcol, occupied)
                if s is None:
                    continue
                dist = abs(s[0] - prows[p]) + abs(s[1] - pcols[p])
                if dist > REACH:
                    continue
                if min_dist is not None and min_dist < dist:
                    continue
                if min_dist is not None and min_dist > dist:
                    min_list = []
                min_dist, min_list = dist, min_list + [(dist, p, s)]
            if len(min_list) == 1:
                matches.append(min_list[0])
        if not matches:
            if -1 in orows:
                return
            out = draw_output(orows, ocols)
            if out is None:
                return
            if check_label is not None and out != check_label:
                return
            key = tuple(map(tuple, out))
            if key not in found:
                found[key] = (out, topo(less))
            return
        by_site = {}
        for dist, p, s in matches:
            by_site.setdefault(s, []).append((dist, p))
        sites = sorted(by_site)
        decide(orows, ocols, less, sites, by_site, 0)

    def decide(orows, ocols, less, sites, by_site, k):
        if k == len(sites):
            step(orows, ocols, less)
            return
        s = sites[k]
        lst = by_site[s]
        dmin = min(d for d, _ in lst)
        tied = [p for d, p in lst if d == dmin]
        tournament(orows, ocols, less, sites, by_site, k, s, tied, tied[0], 1)

    def tournament(orows, ocols, less, sites, by_site, k, s, tied, champ, j):
        if j == len(tied):
            if check_label is not None and check_label[s[0]][s[1]] != pcolors[champ]:
                return
            o_r, o_c = list(orows), list(ocols)
            o_r[champ], o_c[champ] = s
            decide(o_r, o_c, less, sites, by_site, k + 1)
            return
        q = tied[j]
        if q in less[champ]:
            tournament(orows, ocols, less, sites, by_site, k, s, tied, champ, j + 1)
        elif champ in less[q]:
            tournament(orows, ocols, less, sites, by_site, k, s, tied, q, j + 1)
        else:
            tournament(orows, ocols, closure_add(less, champ, q), sites, by_site, k, s, tied, champ, j + 1)
            tournament(orows, ocols, closure_add(less, q, champ), sites, by_site, k, s, tied, q, j + 1)

    step([-1] * n, [-1] * n, [set() for _ in range(n)])
    return list(found.values())



RULES = {'clamp': site_native, 'king': site_king}


def _normalizer(palette):
    palette = list(range(10)) if palette is None else list(palette)
    if len(palette) != 10 or set(palette) != set(range(10)):
        raise ValueError('palette must be a permutation of ten ARC colours')
    inverse = {value: index for index, value in enumerate(palette)}
    def normalize(grid):
        if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
            raise ValueError('invalid grid height')
        width = len(grid[0])
        if not 1 <= width <= 30 or any(len(row) != width for row in grid):
            raise ValueError('invalid rectangular grid')
        if any(type(value) is not int or value not in inverse for row in grid for value in row):
            raise ValueError('invalid ARC cell')
        return [[inverse[value] for value in row] for row in grid]
    return normalize


def _enumerate(args, rule, label=None, limit=2):
    try:
        return enumerate_outputs(args, site=RULES[rule], check_label=label, limit=limit)
    except Budget as exc:
        raise DockingSearchBudget('1b8318e3: docking uniqueness search budget exhausted') from exc



def _require_native(args, role, index):
    outcomes = _enumerate(args, 'clamp')
    if len(outcomes) > 1:
        if role == 'demonstration':
            raise DockingContextAmbiguity(
                f'1b8318e3: intrinsically ambiguous demonstration at index {index}; retain query, redraw context')
        raise IntrinsicDockingAmbiguity(
            f'1b8318e3: intrinsic native {role} ambiguity at index {index}')
    if not outcomes:
        raise ValueError(f'no complete native docking of {role} index {index}')


def require_native_input(grid, palette=None):
    """Check the documented native unique-output domain using input only."""
    try:
        _require_native(scene(_normalizer(palette)(grid)), 'input', 0)
    except MissingColourEvidence:
        raise
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        raise MissingColourEvidence('1b8318e3: '+str(exc)) from exc

def assess_evidence(demonstrations, queries, palette=None):
    """Return evidence diagnostics or raise a classified evidence exception.

    queries contains dictionaries; only q['input'] is accessed. After fitting
    rule hypotheses to the demonstrations, both demo inputs and query inputs
    must yield a single agreed output without label-pruning their enumeration.
    This prevents a demonstration label from concealing intrinsic ambiguity.
    A native-ambiguous demo is a context failure: redraw demos, keep the query.
    Native query ambiguity is checked first and rejects that query itself.
    """
    if not demonstrations:
        raise MissingColourEvidence('1b8318e3: missing demonstrations')
    try:
        normalize = _normalizer(palette)
        # Query validity comes first: bad demos must never hide an intrinsically
        # ambiguous query and cause repeated context redraws.
        query_args = [scene(normalize(q['input'])) for q in queries]
        for index, args in enumerate(query_args):
            _require_native(args, 'query', index)
        demo_args = []
        survivors = set(RULES)
        for pair in demonstrations:
            gi, go = normalize(pair['input']), normalize(pair['output'])
            if len(gi) != len(go) or len(gi[0]) != len(go[0]):
                raise ValueError('demonstration changes dimensions')
            args = scene(gi)
            _require_native(args, 'demonstration', len(demo_args))
            demo_args.append(args)
            survivors = {rule for rule in survivors if _enumerate(args, rule, go, 1)}
        if not survivors:
            raise ValueError('no docking rule explains all demonstration outputs')
        for role, scenes in (('demonstration', demo_args), ('query', query_args)):
            for index, args in enumerate(scenes):
                answers = set()
                for rule in sorted(survivors):
                    outcomes = _enumerate(args, rule)
                    if len(outcomes) > 1:
                        raise DockingContextAmbiguity(
                            f'1b8318e3: surviving {rule} has multiple {role} outputs at index {index}')
                    answers.update(tuple(map(tuple, out)) for out, _order in outcomes)
                if len(answers) > 1:
                    raise DockingContextAmbiguity(
                        f'1b8318e3: demonstration context does not determine {role} index {index}')
                if not answers:
                    raise ValueError(f'no complete docking of {role} index {index}')
        return {'surviving_rules': sorted(survivors), 'demonstrations_checked': len(demo_args),
                'queries_checked': len(query_args), 'query_labels_read': False}
    except MissingColourEvidence:
        raise
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        raise MissingColourEvidence('1b8318e3: '+str(exc)) from exc


def require_evidence(demonstrations, queries, palette=None):
    assess_evidence(demonstrations, queries, palette)
