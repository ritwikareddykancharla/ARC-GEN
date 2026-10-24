"""Episode evidence for a04b2602 (rings around reds inside green rectangles).

Native rule: every red (2) inside a green (3) rectangle gets a 3x3 blue (1)
ring. Rings overwrite green, black and other reds; the framed reds stay red.
The constructor accepts a scene only when "inside a rectangle" equals "has
>= 2 orthogonal green neighbours".

The gate enumerates a finite, named set of readings, keeps those that
reproduce EVERY demonstration output, and requires every survivor to give the
same defined answer on each query INPUT. Query answers are never read. A pass
rules out only the listed alternatives; it is not an identifiability proof.

Rules (22), evaluated in the native frame (identity palette) after undoing
the episode's colour permutation and D4 transform from metadata only:

* ``native``;
* which reds are framed (native painting): ``select:touch_ge1``,
  ``select:touch_ge3`` (corner reds left unframed), ``select:touch_4``,
  ``select:touch8_ge2``, ``select:all_reds``, ``select:largest_rectangle``
  (undefined on an area tie), ``select:inside_rectangle`` (green components
  merged while their joint box holds only green/red; equal to native on every
  valid scene), and ``select:component_bbox`` (the archived reference
  reading: reds inside the box of one green component). The last differs from
  native only when reds cut a rectangle into several components;
* how rings are painted (native selection): ``paint:spare_reds`` (rings leave
  other reds red), ``paint:spare_green``, ``paint:clip_to_rectangle``,
  ``paint:plus``, ``paint:filled``, and ``paint:sequential_stamp:<order>``
  (ring then centre per red in one scan order, so a later ring covers an
  adjacent framed red) for all eight D4 scan orders.

Witnesses (batch report): about a fifth of random three-demonstration
contexts, legacy and expanded alike, let ``paint:spare_reds``,
``select:touch_ge3`` or ``paint:sequential_stamp:*`` survive and change the
query answer, because no demonstration shows an unframed red under a ring, a
framed corner red, or two adjacent framed reds. The canonical train pairs
refute all three. The set is closed under D4 (scan orders map to scan orders;
the other rules are equivariant), so the verdict does not depend on the
episode orientation. A survivor that is undefined on the query counts as a
distinct answer.
"""

from .augmentation import transformed

TASK_ID = 'a04b2602'
BG, RING, RED, GREEN = 0, 1, 2, 3
ORTHO = ((1, 0), (-1, 0), (0, 1), (0, -1))
AROUND = tuple((dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
ORDERS = {'rc': (0, 1, 1), 'r-c': (0, 1, -1), '-rc': (0, -1, 1), '-r-c': (0, -1, -1),
          'cr': (1, 1, 1), 'c-r': (1, 1, -1), '-cr': (1, -1, 1), '-c-r': (1, -1, -1)}
SELECTIONS = ('touch_ge1', 'touch_ge3', 'touch_4', 'touch8_ge2', 'all_reds',
              'inside_rectangle', 'component_bbox', 'largest_rectangle')
PAINTINGS = ('spare_reds', 'spare_green', 'clip_to_rectangle', 'plus', 'filled') + tuple(
    'sequential_stamp:' + o for o in ORDERS)
RULES = ('native',) + tuple('select:' + s for s in SELECTIONS) + tuple(
    'paint:' + p for p in PAINTINGS)
NATIVE_RULE = RULES[0]


def _missing(message):
    from .colour_evidence import MissingColourEvidence
    return MissingColourEvidence(f'{TASK_ID}: {message}')


def native_frame(g, palette, d4):
    """Undo the episode colour permutation and D4 transform (metadata only)."""
    inverse = {v: k for k, v in enumerate(palette)}
    a = [[inverse[int(c)] for c in row] for row in g]
    a = transformed(a, (-d4) % 4, list(range(10)))
    if d4 >= 4:
        a = [row[::-1] for row in a]
    return a


def _t(g):
    return tuple(tuple(row) for row in g)


class _Scene:
    def __init__(self, g):
        self.g = [list(row) for row in g]
        self.h, self.w = len(g), len(g[0])
        self.reds = [(r, c) for r in range(self.h) for c in range(self.w) if g[r][c] == RED]
        self._boxes = None
        self._components = None

    def at(self, r, c):
        return self.g[r][c] if 0 <= r < self.h and 0 <= c < self.w else None

    def greens(self, r, c, steps=ORTHO):
        return sum(self.at(r + dy, c + dx) == GREEN for dy, dx in steps)

    def components(self):
        if self._components is None:
            label, boxes = {}, []
            for start in ((r, c) for r in range(self.h) for c in range(self.w)):
                if self.at(*start) != GREEN or start in label:
                    continue
                label[start] = len(boxes)
                frontier, box = [start], [start[0], start[1], start[0], start[1]]
                while frontier:
                    r, c = frontier.pop()
                    box = [min(box[0], r), min(box[1], c), max(box[2], r), max(box[3], c)]
                    for dy, dx in ORTHO:
                        n = (r + dy, c + dx)
                        if self.at(*n) == GREEN and n not in label:
                            label[n] = label[start]
                            frontier.append(n)
                boxes.append(tuple(box))
            self._components = boxes
        return self._components

    def _solid(self, box):
        return all(self.g[r][c] in (RED, GREEN) for r in range(box[0], box[2] + 1)
                   for c in range(box[1], box[3] + 1))

    def rectangles(self):
        if self._boxes is None:
            boxes = list(self.components())
            changed = True
            while changed:
                changed = False
                for i in range(len(boxes)):
                    for j in range(i + 1, len(boxes)):
                        a, b = boxes[i], boxes[j]
                        joint = (min(a[0], b[0]), min(a[1], b[1]),
                                 max(a[2], b[2]), max(a[3], b[3]))
                        if self._solid(joint):
                            boxes[i] = joint
                            boxes.pop(j)
                            changed = True
                            break
                    if changed:
                        break
            self._boxes = boxes
        return self._boxes

    @staticmethod
    def _inside(box, p):
        return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]

    def select(self, name):
        reds = self.reds
        if name == 'native':
            return {p for p in reds if self.greens(*p) >= 2}
        if name == 'touch_ge1':
            return {p for p in reds if self.greens(*p) >= 1}
        if name == 'touch_ge3':
            return {p for p in reds if self.greens(*p) >= 3}
        if name == 'touch_4':
            return {p for p in reds if self.greens(*p) == 4}
        if name == 'touch8_ge2':
            return {p for p in reds if self.greens(*p, steps=AROUND) >= 2}
        if name == 'all_reds':
            return set(reds)
        if name == 'inside_rectangle':
            return {p for p in reds if any(self._inside(b, p) for b in self.rectangles())}
        if name == 'component_bbox':
            return {p for p in reds if any(self._inside(b, p) for b in self.components())}
        if name == 'largest_rectangle':
            boxes = self.rectangles()
            if not boxes:
                return None
            areas = [(b[2] - b[0] + 1) * (b[3] - b[1] + 1) for b in boxes]
            if areas.count(max(areas)) != 1:
                return None
            best = boxes[areas.index(max(areas))]
            return {p for p in reds if self._inside(best, p)}
        raise KeyError(name)

    def paint(self, active, name):
        out = [list(row) for row in self.g]
        if name.startswith('sequential_stamp:'):
            axis, s0, s1 = ORDERS[name.split(':', 1)[1]]
            key = (lambda p: (s0 * p[axis], s1 * p[1 - axis]))
            for r, c in sorted(active, key=key):
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if self.at(r + dy, c + dx) is not None:
                            out[r + dy][c + dx] = RING
                out[r][c] = RED
            return out
        steps = ORTHO if name == 'plus' else AROUND
        boxes = self.rectangles() if name == 'clip_to_rectangle' else ()
        for r, c in active:
            if name == 'filled':
                out[r][c] = RING
            for dy, dx in steps:
                y, x = r + dy, c + dx
                if self.at(y, x) is None or ((y, x) in active and name != 'filled'):
                    continue
                if name == 'spare_reds' and self.g[y][x] == RED:
                    continue
                if name == 'spare_green' and self.g[y][x] == GREEN:
                    continue
                if name == 'clip_to_rectangle' and not any(self._inside(b, (y, x)) for b in boxes):
                    continue
                out[y][x] = RING
        return out


def variants(g):
    """Answers of every rule on one native-frame input (None = undefined)."""
    if not g or not g[0] or any(len(row) != len(g[0]) for row in g):
        raise _missing('input is not a rectangular grid')
    scene = _Scene(g)
    native = scene.select('native')
    out = {'native': _t(scene.paint(native, 'native'))}
    for s in SELECTIONS:
        active = scene.select(s)
        out['select:' + s] = None if active is None else _t(scene.paint(active, 'native'))
    for p in PAINTINGS:
        out['paint:' + p] = _t(scene.paint(native, p))
    return out


def surviving_rules(demonstrations, palette=None, d4=0):
    palette = list(range(10)) if palette is None else list(palette)
    alive = set(RULES)
    for demo in demonstrations:
        target = _t(native_frame(demo['output'], palette, d4))
        options = variants(native_frame(demo['input'], palette, d4))
        alive = {name for name in alive if options[name] == target}
    return alive


def candidate_predictions(demonstrations, query_input, palette=None, d4=0):
    """Distinct native-frame query answers (None = undefined) of the survivors."""
    palette = list(range(10)) if palette is None else list(palette)
    options = variants(native_frame(query_input, palette, d4))
    answers = []
    for name in sorted(surviving_rules(demonstrations, palette, d4)):
        if options[name] not in answers:
            answers.append(options[name])
    return answers


def require_rect_ring_evidence(demonstrations, queries, palette=None, d4=0):
    """Raise MissingColourEvidence unless all surviving rules agree per query input."""
    palette = list(range(10)) if palette is None else list(palette)
    alive = surviving_rules(demonstrations, palette, d4)
    if not alive:
        raise _missing('demonstrations fit no candidate rule')
    for query in queries:
        options = variants(native_frame(query['input'], palette, d4))
        answers = {options[name] for name in alive}
        if len(answers) != 1 or None in answers:
            raise _missing('demonstrations leave the query reading ambiguous')
