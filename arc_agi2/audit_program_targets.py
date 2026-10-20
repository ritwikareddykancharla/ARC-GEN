"""Audit every native target on its approved fixtures; no training or publishing."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
from .runtime import BASE, reference
from .fixture_policy import fixture_basis
from .program_targets import compile_target, audit_target, verify


def check(task_id):
    result = {'task_id': task_id, 'passed': False}
    stage = 'compile'
    try:
        source, basis = compile_target(task_id)
        result.update(basis=basis, program_sha256=hashlib.sha256(source.encode()).hexdigest())
        stage = 'source_audit'
        audit_target(task_id, source)
        stage = 'fixture_execution'
        packet = reference(task_id)
        fb = fixture_basis(task_id)
        task = packet[fb['fixture']]
        ep = {'train': task['train'],
              'test': [{'input': p['input']} for p in task['test']],
              'solutions': [p['output'] for p in task['test']]}
        result['verification'] = verify(source, ep)
        result.update(passed=True, fixture=fb['fixture'], corrected=fb['corrected'])
    except Exception as exc:
        result.update(stage=stage, error=type(exc).__name__ + ': ' + str(exc)[:800])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    ids = sorted(r['task_id'] for r in json.loads((BASE/'reference_index.json').read_text())['tasks'])
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(check, tid) for tid in ids]
        for future in as_completed(futures):
            rows.append(future.result())
            if len(rows) % 100 == 0:
                print(json.dumps({'checked': len(rows), 'passed': sum(r['passed'] for r in rows)}), flush=True)
    rows.sort(key=lambda r: r['task_id'])
    report = {
        'scope': 'Native orientation/palette; approved supplied fixtures only. Fresh generated episodes and direct augmented variants require separate verification.',
        'total': len(rows), 'passed': sum(r['passed'] for r in rows),
        'failures_by_stage': dict(Counter(r['stage'] for r in rows if not r['passed'])),
        'tasks': rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='tasks'}), flush=True)


if __name__ == '__main__':
    main()
