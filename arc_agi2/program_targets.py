"""Standalone SFT program targets built from reviewed, saved solver sources.

Targets receive demonstrations and query INPUT only. Expected query outputs are
used by the offline verifier, never to construct a target. This is a trusted
archived-code tool, not a security sandbox for arbitrary model submissions.
"""
import ast
import hashlib
import inspect
import json
import symtable
from functools import lru_cache
from pathlib import Path

import numpy as np
from . import helpers
from .runtime import BASE, call, grid, reference
from .verified_rules import VERIFIERS


class TargetError(ValueError):
    pass


class Clean(ast.NodeTransformer):
    def generic_visit(self, node):
        node = super().generic_visit(node)
        # A block containing only a tracing call still needs a valid suite
        # after emit() is removed (e.g. `if drew: emit(...)`).
        if isinstance(getattr(node, 'body', None), list) and not node.body and not isinstance(node, ast.Module):
            node.body = [ast.Pass()]
        return node

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'emit':
            return None
        return self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module == 'runtime':
            if any(alias.name != 'grid' for alias in node.names):
                raise TargetError('Unbundled runtime dependency')
            return [ast.Assign(targets=[ast.Name(id=alias.asname or alias.name,
                                                 ctx=ast.Store())],
                               value=ast.Name(id='_check_grid', ctx=ast.Load()))
                    for alias in node.names]
        return node


def clean(source):
    tree = Clean().visit(ast.parse(source))
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + '\n'


def globals_used(source):
    root = symtable.symtable(source, '<solver>', 'exec')
    used = set()
    def walk(table):
        for symbol in table.get_symbols():
            if symbol.is_referenced() and symbol.is_global():
                used.add(symbol.get_name())
        for child in table.get_children():
            walk(child)
    walk(root)
    return used


GRID_CHECK = '''def _check_grid(value):
    a = np.asarray(value)
    if a.ndim != 2 or any(n < 1 or n > 30 for n in a.shape) or not np.issubdtype(a.dtype, np.integer) or np.any(a < 0) or np.any(a > 9):
        raise ValueError("Expected a rectangular integer grid with colours 0..9")
    return a.astype(int).tolist()
'''


def bundle(source):
    source = clean(source)
    selected = {}
    pending = globals_used(source)
    defined = set(symtable.symtable(source, '<solver>', 'exec').get_identifiers())
    # A name referenced globally is not necessarily defined by the module.
    table = symtable.symtable(source, '<solver>', 'exec')
    defined = {s.get_name() for s in table.get_symbols() if s.is_assigned() or s.is_imported() or s.is_namespace()}
    while pending:
        name = min(pending)
        pending.remove(name)
        if name in defined or name in selected:
            continue
        obj = getattr(helpers, name, None)
        if inspect.isfunction(obj) and obj.__module__ == helpers.__name__:
            text = clean(inspect.getsource(obj))
            selected[name] = text
            pending.update(globals_used(text))
    # The preloaded helper module exports these imports as well as its functions.
    header = 'import numpy as np\nfrom collections import Counter, deque\nfrom itertools import pairwise, permutations\n'
    if 'emit' in globals_used(source):
        header += 'def emit(*args, **kwargs):\n    pass\n'
    return header + GRID_CHECK + '\n'.join(selected.values()) + '\n' + source


@lru_cache(maxsize=2048)
def native_program(task_id):
    if task_id == '269e22fb':
        from . import contextual
        text = inspect.getsource(contextual)
        tree = ast.parse(text)
        tree.body = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and getattr(n, 'name', '') != 'verify_shared_picture_episode']
        source = ast.unparse(tree).replace('grid(', '_check_grid(')
        source += '\ndef _native_solve(demonstrations, query):\n    return solve_shared_picture(demonstrations, query)\n'
        basis = 'demonstration_conditioned_shared_picture'
    elif task_id == '98c475bf':
        from . import motif_context
        tree = ast.parse(inspect.getsource(motif_context))
        tree.body = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        source = ast.unparse(tree).replace('grid(', '_check_grid(')
        source += '\ndef _native_solve(demonstrations, query):\n    return solve_demonstrated_motifs(demonstrations, query)\n'
        basis = 'demonstration_conditioned_motifs'
    elif task_id == 'd6542281':
        from . import joint_fragments
        source = inspect.getsource(joint_fragments)
        source += '\ndef _native_solve(demonstrations, query):\n    return transform(query)\n'
        basis = 'reviewed_joint_fragment_exact_cover'
    elif task_id in VERIFIERS:
        f = VERIFIERS[task_id]
        source = inspect.getsource(f)
        source += '\ndef _native_solve(demonstrations, query):\n    return ' + f.__name__ + '(query)\n'
        basis = 'reviewed_verifier_override'
    else:
        source = reference(task_id)['code']
        argument = 'np.asarray(query)' if task_id in ('0d87d2a6', 'c1d99e64') else 'query'
        source += '\ndef _native_solve(demonstrations, query):\n    return transform(' + argument + ')\n'
        basis = 'saved_teacher_transform'
    return bundle(source), basis


WRAPPER = '''
def _episode_forward(a):
    a = [list(row) for row in a]
    if _D4 >= 4:
        a = [row[::-1] for row in a]
    for _ in range(_D4 % 4):
        a = [list(row) for row in zip(*a[::-1])]
    return [[_PALETTE[int(c)] for c in row] for row in a]

def _episode_inverse(a):
    inv = [_PALETTE.index(c) for c in range(10)]
    a = [[inv[int(c)] for c in row] for row in a]
    for _ in range((-_D4) % 4):
        a = [list(row) for row in zip(*a[::-1])]
    if _D4 >= 4:
        a = [row[::-1] for row in a]
    return a

def solve(demonstrations, grid):
    native_demos = [{k: _episode_inverse(p[k]) for k in ('input', 'output')} for p in demonstrations]
    result = _native_solve(native_demos, _episode_inverse(grid))
    return _check_grid(_episode_forward(_check_grid(result)))
'''


def reference_target(task_id, d4=0, palette=None):
    """Only family identity and augmentation metadata enter target construction."""
    palette = list(range(10)) if palette is None else list(palette)
    if type(d4) is not int or d4 not in range(8) or sorted(palette) != list(range(10)):
        raise TargetError('Invalid episode augmentation')
    native, basis = native_program(task_id)
    source = native + '\n_D4 = ' + repr(d4) + '\n_PALETTE = ' + repr(palette) + '\n' + WRAPPER
    # Standalone compilation in a fresh namespace; no preloaded project helpers.
    compile(source, '<standalone-target>', 'exec')
    return source, basis


def compile_target(task_id, d4=0, palette=None):
    """Produce direct-coordinate code; missing rewrites cannot fall back to wrappers."""
    palette = list(range(10)) if palette is None else list(palette)
    if type(d4) is not int or d4 not in range(8) or sorted(palette) != list(range(10)):
        raise TargetError('Invalid episode augmentation')
    from .direct_programs import direct_source
    source = direct_source(task_id, d4, palette)
    if source is not None:
        return source, 'reviewed_direct_coordinate_rewrite'
    if d4 == 0 and palette == list(range(10)):
        source, basis = native_program(task_id)
        class Entry(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                if node.name == '_native_solve':node.name = 'solve'
                return self.generic_visit(node)
        tree = Entry().visit(ast.parse(source));ast.fix_missing_locations(tree)
        return ast.unparse(tree)+'\n', basis
    raise TargetError('Direct augmented program rewrite required; wrapper targets disabled')


@lru_cache(maxsize=2048)
def forbidden_fixture_literals(task_id):
    """Flag literal copies of this task's original grids in a saved program."""
    r = reference(task_id)
    values = set()
    for version in ('canonical', 'teaching_fixture'):
        for split in ('train', 'test'):
            for p in r[version][split]:
                for field in ('input', 'output'):
                    a = p[field]
                    if sum(map(len, a)) >= 9:
                        values.add(json.dumps(a, separators=(',', ':')))
    return values


@lru_cache(maxsize=2048)
def audit_target(task_id, source):
    tree = ast.parse(source)
    allowed = {'numpy', 'collections', 'math', 'itertools', 'functools', 'heapq', 'copy', 'statistics', 'operator', 'typing', 'bisect', 'fractions'}
    forbidden = {'open', 'exec', 'eval', 'compile', '__import__', 'globals', 'locals', 'input', 'breakpoint'}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            if any(a.name.split('.')[0] not in allowed for a in n.names):
                raise TargetError('Unsupported import')
        if isinstance(n, ast.ImportFrom):
            if n.level or not n.module or n.module.split('.')[0] not in allowed:
                raise TargetError('Project or unsupported import')
        if isinstance(n, ast.Name) and n.id in forbidden:
            raise TargetError('Unsupported executable operation: ' + n.id)
        if isinstance(n, ast.Attribute) and (n.attr.startswith('__') or n.attr in {'load','save','loadtxt','savetxt','fromfile','tofile','memmap','system','popen'}):
            raise TargetError('Unsupported attribute: '+n.attr)
        if isinstance(n, (ast.List, ast.Tuple)):
            try:
                value = ast.literal_eval(n)
                key = json.dumps(value, separators=(',', ':'))
            except (ValueError, TypeError, SyntaxError):
                continue
            if key in forbidden_fixture_literals(task_id):
                raise TargetError('Literal original grid in program; contextual repair required')


def verify(source, episode, seconds=3):
    """Fresh module state for EACH input. Labels never enter solver namespace."""
    tests = episode['test']; answers = episode['solutions']
    if not episode['train'] or not tests or len(tests) != len(answers):
        raise TargetError('Incomplete episode')
    targets = [(p['input'], p['output']) for p in episode['train']]
    targets += [(p['input'], a) for p, a in zip(tests, answers)]
    code = compile(source, '<standalone-target>', 'exec')
    results = []
    for query, expected in targets:
        namespace = {'__name__': 'standalone_target'}
        call(exec, code, namespace, seconds=seconds)
        # JSON copying prevents a solver mutating evaluator fixtures.
        demos = json.loads(json.dumps(episode['train']))
        query_copy = json.loads(json.dumps(query))
        actual = grid(call(namespace['solve'], demos, query_copy, seconds=seconds))
        results.append(actual == grid(expected))
    if not all(results):
        raise TargetError('Program not exact: ' + json.dumps(results))
    return {'demo_pairs_exact': len(episode['train']), 'query_pairs_exact': len(tests), 'all_exact': True}


def make_record(episode, source_repo='', source_revision=''):
    task_id = episode['task_id']
    from .colour_evidence import require_colour_evidence
    require_colour_evidence(task_id, episode['train'], episode['test'],
                            episode.get('color_permutation'),
                            episode.get('d4_transform', 0))
    if task_id == '00dbd492':
        # Older ARC-GEN samples at size 7 could contain zero boxes. Exact
        # execution alone accepts these vacuous examples. Check all demos and
        # queries, including palette-augmented copies, before target export.
        inputs = [p['input'] for p in episode['train'] + episode['test']]
        if any(len({c for row in inp for c in row}) < 2 for inp in inputs):
            raise TargetError('00dbd492: background-only input has no box to fill')
    source, basis = compile_target(task_id, episode.get('d4_transform', 0), episode.get('color_permutation'))
    audit_target(task_id, source)
    checked = verify(source, episode)
    challenge = {'train': episode['train'], 'test': episode['test']}
    prompt = ('Infer the shared rule from the demonstrations. Return a standalone Python program defining '
              'solve(demonstrations, grid), then the output grids for every test input. '
              'Use a python code block followed by a json code block with key outputs. '
              'Include required helpers; Python standard-library modules and NumPy are allowed.\n' + json.dumps(challenge, separators=(',', ':')))
    output_json = json.dumps({'outputs': episode['solutions']}, separators=(',', ':'))
    completion = '```python\n' + source.rstrip() + '\n```\n\n```json\n' + output_json + '\n```'
    from .fixture_policy import fixture_basis
    fb = fixture_basis(task_id)
    from .synthetic_variants import variant_provenance
    variant = variant_provenance(task_id)
    return dict(episode_id=episode['episode_id'], source_episode_id=episode['episode_id'],
                task_id=task_id, mode='PROGRAM_AND_GRID', prompt=prompt, completion=completion,
                program=source, output_json=output_json,
                messages=[{'role':'user','content':prompt},{'role':'assistant','content':completion}],
                program_sha256=hashlib.sha256(source.encode()).hexdigest(), solver_basis=basis,
                d4_transform=episode.get('d4_transform',0), color_permutation=episode.get('color_permutation',list(range(10))),
                source_repo=source_repo, source_revision=source_revision,
                synthetic_variant=variant,
                fixture_basis=fb['fixture'], correction_evidence_status=fb.get('evidence_status','reviewed_upstream_proposal' if fb['corrected'] else 'canonical'),
                verification=checked, train=episode['train'], test=episode['test'], solutions=episode['solutions'])
