"""Finite competitor readings for a04b2602 (native frame, native colours).

Native rule: every red (2) inside a green (3) rectangle gets a 3x3 blue (1)
ring. Rings overwrite green, black and the other reds; the framed reds stay
red. The constructor only accepts scenes where "inside a rectangle" equals
"has >= 2 orthogonal green neighbours".

Each competitor is a deterministic function of ONE input grid. It returns an
output grid, or None when it is undefined on that input. None never fits a
demonstration and counts as its own query answer. Selection functions read
demonstration pairs and the query INPUT only.

Families of readings:
* which reds are framed: neighbour-count thresholds (>= 1, >= 3, == 4, 8-way
  >= 2), all reds, reds of the largest rectangle only, and the archived
  component-bounding-box reading;
* how a ring is painted: rings that spare other reds, spare green, are clipped
  to the rectangle, form a plus instead of a square, are stamped one at a
  time in a scan order (so a later ring covers an earlier framed red; all
  eight D4 scan orders are listed, which keeps the set closed under D4), or
  fill the centre too.
"""

STEPS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
STEPS8 = tuple((dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)


def _size(g):
    return len(g), len(g[0])


def _count(g, r, c, steps, colour=3):
    h, w = _size(g)
    return sum(0 <= r + dy < h and 0 <= c + dx < w and g[r + dy][c + dx] == colour
               for dy, dx in steps)


def _reds(g):
    return [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 2]


def _components(g, colour=3):
    h, w = _size(g)
    seen, out = set(), []
    for y in range(h):
        for x in range(w):
            if g[y][x] != colour or (y, x) in seen:
                continue
            seen.add((y, x))
            stack, cells = [(y, x)], []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in STEPS4:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and g[ny][nx] == colour and (ny, nx) not in seen:
                        seen.add((ny, nx))
                        stack.append((ny, nx))
            out.append(cells)
    return out


def _bbox(cells):
    ys = [y for y, _ in cells]
    xs = [x for _, x in cells]
    return min(ys), min(xs), max(ys), max(xs)


def rectangles(g):
    """Green components merged while the joint box holds only green/red."""
    def solid(b):
        return all(g[r][c] in (2, 3) for r in range(b[0], b[2] + 1) for c in range(b[1], b[3] + 1))
    boxes = [_bbox(c) for c in _components(g)]
    merged = True
    while merged:
        merged = False
        for i in range(len(boxes)):
            for j in range(i):
                a, b = boxes[i], boxes[j]
                joint = (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))
                if solid(joint):
                    boxes[j] = joint
                    del boxes[i]
                    merged = True
                    break
            if merged:
                break
    return boxes


def _in(box, r, c):
    return box[0] <= r <= box[2] and box[1] <= c <= box[3]


# ---------------------------------------------------------------- selection
def sel_native(g):
    return {p for p in _reds(g) if _count(g, *p, STEPS4) >= 2}


def sel_touch_ge1(g):
    return {p for p in _reds(g) if _count(g, *p, STEPS4) >= 1}


def sel_touch_ge3(g):
    return {p for p in _reds(g) if _count(g, *p, STEPS4) >= 3}


def sel_touch_4(g):
    return {p for p in _reds(g) if _count(g, *p, STEPS4) == 4}


def sel_touch8_ge2(g):
    return {p for p in _reds(g) if _count(g, *p, STEPS8) >= 2}


def sel_all(g):
    return set(_reds(g))


def sel_inside(g):
    boxes = rectangles(g)
    return {p for p in _reds(g) if any(_in(b, *p) for b in boxes)}


def sel_component_bbox(g):
    """The archived reference reading."""
    boxes = [_bbox(c) for c in _components(g)]
    return {p for p in _reds(g) if any(_in(b, *p) for b in boxes)}


def sel_largest(g):
    boxes = rectangles(g)
    if not boxes:
        return None
    areas = [(b[2] - b[0] + 1) * (b[3] - b[1] + 1) for b in boxes]
    if areas.count(max(areas)) != 1:
        return None
    b = boxes[areas.index(max(areas))]
    return {p for p in _reds(g) if _in(b, *p)}


# ---------------------------------------------------------------- painting
def paint_native(g, active):
    h, w = _size(g)
    out = [list(r) for r in g]
    for r, c in active:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                y, x = r + dy, c + dx
                if 0 <= y < h and 0 <= x < w and (y, x) not in active:
                    out[y][x] = 1
    return out


def _paint_where(g, active, allowed):
    h, w = _size(g)
    out = [list(r) for r in g]
    for r, c in active:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                y, x = r + dy, c + dx
                if 0 <= y < h and 0 <= x < w and (y, x) not in active and allowed(y, x):
                    out[y][x] = 1
    return out


def paint_spare_reds(g, active):
    return _paint_where(g, active, lambda y, x: g[y][x] != 2)


def paint_spare_green(g, active):
    return _paint_where(g, active, lambda y, x: g[y][x] != 3)


def paint_clip_rect(g, active):
    boxes = rectangles(g)
    return _paint_where(g, active, lambda y, x: any(_in(b, y, x) for b in boxes))


def paint_plus(g, active):
    h, w = _size(g)
    out = [list(r) for r in g]
    for r, c in active:
        for dy, dx in STEPS4:
            y, x = r + dy, c + dx
            if 0 <= y < h and 0 <= x < w and (y, x) not in active:
                out[y][x] = 1
    return out


# The eight scan orders induced by D4 (row-major, mirrored, column-major, ...).
SCAN_ORDERS = {"rc": lambda p: (p[0], p[1]), "r-c": lambda p: (p[0], -p[1]),
               "-rc": lambda p: (-p[0], p[1]), "-r-c": lambda p: (-p[0], -p[1]),
               "cr": lambda p: (p[1], p[0]), "c-r": lambda p: (p[1], -p[0]),
               "-cr": lambda p: (-p[1], p[0]), "-c-r": lambda p: (-p[1], -p[0])}


def paint_sequential(g, active, order="rc"):
    """Stamp ring then centre per red in one scan order; later rings win."""
    h, w = _size(g)
    out = [list(r) for r in g]
    for r, c in sorted(active, key=SCAN_ORDERS[order]):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                y, x = r + dy, c + dx
                if 0 <= y < h and 0 <= x < w:
                    out[y][x] = 1
        out[r][c] = 2
    return out


def paint_filled(g, active):
    h, w = _size(g)
    out = [list(r) for r in g]
    for r, c in active:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                y, x = r + dy, c + dx
                if 0 <= y < h and 0 <= x < w:
                    out[y][x] = 1
    return out


SELECTORS = {"native": sel_native, "touch_ge1": sel_touch_ge1, "touch_ge3": sel_touch_ge3,
             "touch_4": sel_touch_4, "touch8_ge2": sel_touch8_ge2, "all_reds": sel_all,
             "inside_rectangle": sel_inside, "component_bbox": sel_component_bbox,
             "largest_rectangle": sel_largest}
PAINTERS = {"spare_reds": paint_spare_reds, "spare_green": paint_spare_green,
            "clip_to_rectangle": paint_clip_rect, "plus": paint_plus,
            "filled": paint_filled}
PAINTERS.update({"sequential_stamp:" + o: (lambda g, a, o=o: paint_sequential(g, a, o))
                 for o in SCAN_ORDERS})


def _rule(select, paint):
    def run(g):
        active = select(g)
        return None if active is None else paint(g, active)
    return run


RULES = {"native": _rule(sel_native, paint_native)}
for _name, _sel in SELECTORS.items():
    if _name != "native":
        RULES["select:" + _name] = _rule(_sel, paint_native)
for _name, _paint in PAINTERS.items():
    RULES["paint:" + _name] = _rule(sel_native, _paint)


def _key(g):
    return None if g is None else tuple(map(tuple, g))


def surviving(demos, rules=RULES):
    return [n for n, f in rules.items()
            if all(_key(f(d["input"])) == _key(d["output"]) for d in demos)]


def candidate_predictions(demos, query_input, rules=RULES):
    answers = []
    for n in surviving(demos, rules):
        a = _key(rules[n](query_input))
        if a not in answers:
            answers.append(a)
    return answers


def ambiguous(demos, query_input, rules=RULES):
    return len(candidate_predictions(demos, query_input, rules)) != 1


def separating(demos, query_input, rules=RULES):
    """Surviving rules whose query answer differs from the native reading's."""
    native = _key(rules["native"](query_input))
    return sorted(n for n in surviving(demos, rules) if _key(rules[n](query_input)) != native)
