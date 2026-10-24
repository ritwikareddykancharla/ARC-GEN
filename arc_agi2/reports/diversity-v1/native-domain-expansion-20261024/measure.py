"""Measure 1,000 fresh samples per family: baseline constructor vs current.

Run from the repository root:
  PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-domain-expansion-20261024/measure.py
The baseline is each task source at BASELINE (loaded with `git show`).
Statistics describe samples, not guarantees about every episode.
"""
import hashlib
import json
import random
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path

import numpy as np

BASELINE = 'cf79bbcdbccb62f6af3f04c5b4933159ef175fc7'
FAMILIES = ['31adaf00', '84db8fc4', 'ce039d91', '137f0df0', 'd282b262', 'a406ac07', 'f45f5ca7']
N = 1000
OUT = Path(__file__).with_name('measurements.json')


def load(tid, revision=None):
    path = f'tasks/task_{tid}.py'
    text = (subprocess.check_output(['git', 'show', f'{revision}:{path}'], text=True)
            if revision else Path(path).read_text())
    mod = types.ModuleType(f'm_{tid}_{revision or "cur"}')
    exec(compile(text, path, 'exec'), mod.__dict__)
    return mod


def comps(a, keep):
    """4-connected components of cells where keep(a) is True."""
    h, w = a.shape
    mask = keep(a)
    seen = np.zeros_like(mask)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                todo, cells = [(y, x)], []
                while todo:
                    cy, cx = todo.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            todo.append((ny, nx))
                out.append(cells)
    return out


def boxes(cells):
    ys = [y for y, _ in cells]; xs = [x for _, x in cells]
    return max(ys) - min(ys) + 1, max(xs) - min(xs) + 1


def stamped_squares(a):
    g = a.copy(); h, w = g.shape; sizes = []
    for s in range(min(h, w), 1, -1):
        for y in range(h - s + 1):
            for x in range(w - s + 1):
                if (g[y:y + s, x:x + s] == 0).all():
                    g[y:y + s, x:x + s] = 1; sizes.append(s)
    return sizes


def specific(tid, a, b):
    if tid == '31adaf00':
        s = stamped_squares(a)
        return {'filled_squares': len(s), 'square_sizes': s}
    if tid == '84db8fc4':
        return {'enclosed_regions': len(comps(b, lambda g: g == 5)),
                'border_regions': len(comps(b, lambda g: g == 2))}
    if tid == 'ce039d91':
        return {'grey_pixels': int((a == 5).sum()), 'mirrored_pixels': int((b == 1).sum())}
    if tid == '137f0df0':
        c = comps(a, lambda g: g == 5)
        rows = len({min(y for y, _ in k) for k in c}); cols = len({min(x for _, x in k) for k in c})
        return {'blocks': len(c), 'block_shapes': sorted({boxes(k) for k in c}), 'lattice': [rows, cols]}
    if tid == 'd282b262':
        c = comps(a, lambda g: g != 0)
        shapes = [boxes(k) for k in c]
        return {'boxes': len(c), 'box_shapes': shapes, 'nonsquare_boxes': sum(h != w for h, w in shapes)}
    if tid == 'a406ac07':
        bottom = list(a[-1]); right = list(a[:, -1])
        runs = [bottom.count(c) for c in dict.fromkeys(bottom)] + [right.count(c) for c in dict.fromkeys(right)]
        return {'colours': len(set(bottom)), 'run_lengths': runs}
    if tid == 'f45f5ca7':
        return {'rows': a.shape[0]}
    return {}


def summary(values):
    return {'min': min(values), 'max': max(values), 'mean': round(float(np.mean(values)), 3),
            'distinct': len(set(values))}


def measure(tid, mod):
    shapes, aspects, colours, extra = Counter(), [], Counter(), []
    for i in range(N):
        random.seed(int(hashlib.sha256(f'native-domain-20261024:{tid}:{i}'.encode()).hexdigest()[:12], 16))
        p = mod.generate()
        a, b = np.array(p['input']), np.array(p['output'])
        h, w = a.shape
        shapes[(h, w)] += 1
        aspects.append(round(max(h, w) / min(h, w), 3))
        colours[len(np.unique(a))] += 1
        extra.append(specific(tid, a, b))
    hs = [h for (h, _), n in shapes.items() for _ in range(n)]
    ws = [w for (_, w), n in shapes.items() for _ in range(n)]
    rect = sum(n for (h, w), n in shapes.items() if h != w)
    result = {
        'samples': N, 'distinct_shapes': len(shapes),
        'shapes_with_at_least_4_samples': sum(n >= 4 for n in shapes.values()),
        'height': summary(hs), 'width': summary(ws),
        'rectangular_rate': rect / N,
        'large_rate': sum(n for (h, w), n in shapes.items() if max(h, w) > 20) / N,
        'aspect_ratio': summary(aspects),
        'input_colour_count_hist': {str(k): v for k, v in sorted(colours.items())},
    }
    keys = extra[0].keys()
    for k in keys:
        vals = [e[k] for e in extra]
        if isinstance(vals[0], list):
            if vals[0] and isinstance(vals[0][0], (list, tuple)):
                flat = [tuple(v) for vs in vals for v in vs]
                result[k] = {'distinct': len(set(flat)), 'most_common': [[list(s), n] for s, n in Counter(flat).most_common(12)]}
            else:
                flat = [v for vs in vals for v in vs]
                result[k] = {'hist': {str(x): n for x, n in sorted(Counter(flat).items())}}
        else:
            result[k] = summary(vals)
            result[k]['hist'] = {str(x): n for x, n in sorted(Counter(vals).items())}
    return result


def main():
    audit_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    report = {'baseline_revision': BASELINE, 'samples_per_family': N,
              'seed_scheme': 'sha256(native-domain-20261024:<id>:<i>)[:12]', 'families': {}}
    for tid in FAMILIES:
        entry = {'baseline': measure(tid, load(tid, BASELINE)), 'current': measure(tid, load(tid))}
        entry['baseline']['source_sha256'] = hashlib.sha256(subprocess.check_output(
            ['git', 'show', f'{BASELINE}:tasks/task_{tid}.py'])).hexdigest()
        entry['current']['source_sha256'] = hashlib.sha256(
            Path(f'tasks/task_{tid}.py').read_bytes()).hexdigest()
        if audit_dir:
            audit = json.loads((audit_dir / f'{tid}.json').read_text())['native']['input']
            entry['audit_20261024_128_samples'] = {k: audit[k] for k in (
                'shapes', 'height', 'width', 'rectangular_rate', 'colour_count_hist',
                'nonmodal_monochrome_components')}
        report['families'][tid] = entry
        print(tid, entry['baseline']['distinct_shapes'], '->', entry['current']['distinct_shapes'], flush=True)
    OUT.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
