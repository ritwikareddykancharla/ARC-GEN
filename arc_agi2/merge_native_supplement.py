"""Merge verified native expansions into a completed repair, without publishing.

Creates a new immutable staging directory. Existing source and repair artifacts
are retained; no running builder's directories may be passed as destinations.
"""
import argparse
from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import shutil

from . import repair_episode_shortfalls as r


def copy_artifact(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Unlink before replacement: other staged snapshots may share this inode.
    destination.unlink(missing_ok=True)
    if source.suffix in ('.tar', '.arrow', '.parquet'):
        try:
            os.link(source, destination)
            return
        except OSError:
            pass
    shutil.copy2(source, destination)


def merge(snapshot, recovery, supplement, destination, builder):
    snapshot, recovery, supplement, destination = map(Path, (snapshot, recovery, supplement, destination))
    if destination.exists():
        raise ValueError('Destination must be new; preserve previous work')
    if any(parent.resolve() == destination.resolve() or parent.resolve() in destination.resolve().parents
           for parent in (snapshot, recovery, supplement)):
        raise ValueError('Destination must be outside all input directories')
    manifest = r.read(recovery / 'manifest.json')
    plan = r.read(recovery / 'repair-report.json')
    build = r.read(supplement / 'supplement-build.json')
    if manifest['status'] not in r.TERMINAL or not plan.get('publishable'):
        raise ValueError('Recovery must be terminal and publishable')
    if not build.get('complete'):
        raise ValueError('Supplement has not completed')
    revision = plan['source_dataset_revision']
    if build['source_dataset_revision'] != revision:
        raise ValueError('Supplement was built against a different dataset revision')
    original_reports = r.load_reports(snapshot)
    reports = {**original_reports, **r.load_reports(recovery)}
    previous_reports = deepcopy(reports)
    r.verify_source_counts(manifest, reports)
    allocation = r.read(recovery / 'allocation.json')
    replacements = {}
    audit = {}
    for tid, evidence in sorted(build['families'].items()):
        r.safe_path(tid)
        if tid not in allocation['train_by_family']:
            raise ValueError('Supplement family absent from original allocation: ' + tid)
        ep_path = supplement / 'episode_reports' / (tid + '.json')
        pool_path = supplement / 'pools' / (tid + '.parquet')
        pool_report_path = supplement / 'pool_reports' / (tid + '.json')
        for path, key in ((ep_path, 'episode_report_sha256'),
                          (pool_path, 'pool_sha256'), (pool_report_path, 'pool_report_sha256')):
            if r.sha256(path) != evidence[key]:
                raise ValueError('Supplement hash mismatch: ' + str(path))
        if evidence['prior_pool_sha256'] != r.read(snapshot / 'pool_reports' / (tid + '.json'))['sha256']:
            raise ValueError('Supplement prior pool does not match pinned snapshot')
        candidate = r.read(ep_path)
        if candidate['task_id'] != tid or set(candidate['splits']) != set(r.SPLITS):
            raise ValueError('Supplement must contain both splits for the named family')
        provenance = r.validate_pool(supplement, tid, manifest, revision)
        pool_report = provenance['source_pool_report']
        rows = builder.pq.read_table(pool_path).to_pylist()
        migrated, _, migration = builder.repartition_pool(rows, pool_report)
        if migrated != rows or migration['requires_episode_rebuild']:
            raise ValueError('Supplement does not follow the global split policy')
        r.verify_artifacts(supplement, candidate)
        if not r.nonregressing(reports.get(tid, {}), candidate):
            raise ValueError('Supplement would lose existing verified episodes: ' + tid)
        for split in r.SPLITS:
            quota = evidence['quotas'][split]
            if any(type(n) is not int or n < 0 for n in quota.values()):
                raise ValueError('Invalid supplemental allocation')
            if candidate['splits'][split]['fresh_episodes'] != sum(quota.values()):
                raise ValueError('Supplement does not fulfill its stated quota')
            if split == 'train' and sum(quota.values()) > builder.POLICY['planned_dataset']['fresh_episodes_per_family']:
                raise ValueError('Supplement exceeds fresh family ceiling')
            if split == 'validation' and sum(quota.values()) != sum(allocation[split+'_by_family'].get(tid, {}).values()):
                raise ValueError('Supplement changes validation quota')
            allocation[split + '_by_family'][tid] = quota
        candidate['native_expansion_provenance'] = {
            'source_dataset_revision': revision, 'source_commit': build['source_commit'],
            'original_pool_sha256': evidence['prior_pool_sha256'],
            'pool_sha256': evidence['pool_sha256'],
            'pool_report_sha256': evidence['pool_report_sha256'],
            'unmodified_episode_report_sha256': evidence['episode_report_sha256'],
            'split_reaudit': migration,
        }
        replacements[tid] = candidate
        audit[tid] = deepcopy(candidate['native_expansion_provenance'])
    reports.update(replacements)
    previous_manifest = deepcopy(manifest)
    manifest.update(r.totals(reports))
    for split in r.SPLITS:
        quota_map = allocation[split + '_by_family']
        actual = Counter()
        for quota in quota_map.values():
            actual.update(quota)
        used = {tid: sum(q.values()) for tid, q in quota_map.items()}
        stats = allocation[split]
        stats.update(allocated=sum(used.values()), actual=dict(actual), family_allocated=used)
        stats['allocation_shortfall'] = stats['requested'] - stats['allocated']
        if stats['allocation_shortfall'] < 0:
            raise ValueError('Merged allocation exceeds requested dataset size')
        # Recompute capacities from actual admitted pools, keeping the old
        # allocation audit as history rather than leaving stale live fields.
        for tid in replacements:
            pool = r.read(supplement / 'pool_reports' / (tid + '.json'))
            _, capacity = builder.allocate([pool], split, stats['requested'], stats['desired'])
            stats.setdefault('family_capacity', {})[tid] = capacity['family_capacity'].get(tid, 0)
        if split == 'train':
            ceiling = builder.POLICY['planned_dataset']['fresh_episodes_per_family']
            stats['family_capacity_shortfall'] = {t: ceiling-c for t, c in stats['family_capacity'].items() if c < ceiling}
        stats['family_unused_capacity'] = {t: c-used.get(t, 0) for t, c in stats['family_capacity'].items() if c > used.get(t, 0)}
        desired = stats['desired']
        stats['shortfall_by_stratum'] = {k: n-actual[k] for k, n in desired.items() if n > actual[k]}
        stats['histogram_surplus_by_stratum'] = {k: n-desired.get(k, 0) for k, n in actual.items() if n > desired.get(k, 0)}
        manifest[split + '_fresh_shortfall'] = max(0, manifest['target_'+split+'_fresh_episodes']-manifest[split+'_fresh_episodes'])
    manifest['status'] = 'complete_with_shortfall' if manifest.get('errors') or any(manifest[s+'_fresh_shortfall'] for s in r.SPLITS) else 'complete'
    manifest.setdefault('native_expansion_history', []).append({'source_commit': build['source_commit'], 'families': audit})
    allocation['native_expansion_audit'] = audit
    plan['accepted_families'] = sorted(set(plan['accepted_families']) | set(replacements))
    plan['native_expansions'] = audit
    plan['remaining_shortfalls'] = r.selection(manifest, allocation, reports)
    old_manifest = r.read(snapshot / 'manifest.json')
    old_files = {p for split in r.SPLITS for p in old_manifest['episode_files'][split]}
    new_files = {p for split in r.SPLITS for p in manifest['episode_files'][split]}
    plan['delete_files'] = sorted(old_files-new_files)
    # All validation above happens before creating the destination.
    destination.mkdir(parents=True)
    for source in sorted(recovery.rglob('*')):
        rel = source.relative_to(recovery)
        if source.is_file() and 'work' not in rel.parts:
            copy_artifact(source, destination / rel)
    replaced_files = {p for tid in replacements for split in r.SPLITS
                      for p in previous_reports.get(tid, {}).get('splits', {}).get(split, {}).get('files', [])}
    for path in replaced_files:
        (destination / r.safe_path(path)).unlink(missing_ok=True)
    for tid, report in replacements.items():
        files = [f'pools/{tid}.parquet', f'pool_reports/{tid}.json']
        files += [p for split in report['splits'].values() for p in split['files']]
        for path in files:
            copy_artifact(supplement / r.safe_path(path), destination / path)
        r.write(destination / 'episode_reports' / (tid + '.json'), report)
    r.write(destination / 'manifest.json', manifest)
    r.write(destination / 'allocation.json', allocation)
    r.write(destination / 'repair-report.json', plan)
    r.write(destination / 'size-audit.json', r.size_audit(reports, manifest))
    r.write(destination / 'native-expansion-audit.json', {'families': audit, 'original_recovery_manifest_sha256': r.sha256(recovery/'manifest.json'), 'supplement_build_sha256': r.sha256(supplement/'supplement-build.json')})
    from .visual_card import card
    (destination / 'README.md').write_text(card(manifest) + '\nNative dimension expansions and their original pool hashes are recorded in [the expansion audit](native-expansion-audit.json).\n')
    r.verify_source_counts(manifest, reports)
    return {'families': sorted(replacements), 'before_fresh': previous_manifest['train_fresh_episodes'],
            'after_fresh': manifest['train_fresh_episodes'], 'published': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('snapshot', 'recovery', 'supplement', 'destination'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    from . import build_million as builder
    import json
    print(json.dumps(merge(**vars(args), builder=builder)), flush=True)


if __name__ == '__main__':
    main()
