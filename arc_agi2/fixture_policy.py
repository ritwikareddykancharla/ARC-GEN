"""Explicit approvals for corrected teaching fixtures; originals stay immutable.

Do not promote every curated packet automatically. An approved task pins both
versions, so new or changed corrections require a fresh review.
"""
import hashlib
import json
from .runtime import reference

APPROVED_CORRECTIONS = {
    '581f7754': {
        'canonical_sha256': '191e4c4ddfd4354e7b4c35388dbeddc19fb760ca52beed8b69d3b9b44c458d8f',
        'teaching_sha256': '52a65032d2925d7a2e9864a17ded1c5fc7ab1af54417768dc984622a168dc187',
        'source': 'https://github.com/arcprize/ARC-AGI-2/pull/52',
        'approval': 'User approved a labelled corrected teaching copy in this project session.',
        'description': 'Eight output cells in demonstration 2; original benchmark data and scores remain unchanged.',
        'changed_cells': [
            {'split':'train','pair':1,'field':'output','row':y,'col':x,'canonical':a,'teaching':b}
            for y,x,a,b in [(3,8,3,8),(3,11,8,3),(4,8,3,8),(4,9,1,3),
                            (4,10,3,1),(4,11,8,3),(5,8,3,8),(5,11,8,3)]
        ],
    },
    'a6f40cea': {
        'canonical_sha256': '190ecfbdad5e3d57ab8f8262bc8f088fd7474896c23225d0275da1d2c76b60e1',
        'teaching_sha256': '02fa6d0273346512cbd6e4ab4d02e75024c788b2080671985f005ac0a946f253',
        'source': 'https://github.com/arcprize/ARC-AGI-2/pull/64',
        'approval': 'User approved the three upstream-backed labelled teaching copies on 2026-10-20; originals and scores remain unchanged.',
        'description': '8 output cells; upstream proposal remains unmerged. e12f9a14 is not included in this approval.',
        'changed_cells': [
            dict(split=split, pair=pair, field='output', row=y, col=x, canonical=a, teaching=b)
            for split,pair,y,x,a,b in [('train', 2, 5, 1, 8, 9), ('train', 2, 5, 2, 9, 8), ('train', 2, 5, 3, 8, 9),
 ('train', 2, 5, 4, 9, 8), ('train', 2, 5, 5, 8, 9), ('train', 2, 5, 6, 9, 8),
 ('train', 2, 5, 7, 8, 9), ('train', 2, 6, 1, 9, 8)]
        ],
    },
    'b74ca5d1': {
        'canonical_sha256': 'deb310c21d0c047427a32197353b8b5baa1290dd46ddd9418821651e88a4bb51',
        'teaching_sha256': '151170dee30f4367c0cf22b17f1ba0fa3547d33cfd74859b5a5336699e730616',
        'source': 'https://github.com/arcprize/ARC-AGI-2/pull/16',
        'approval': 'User approved the three upstream-backed labelled teaching copies on 2026-10-20; originals and scores remain unchanged.',
        'description': '3 output cells; upstream proposal remains unmerged. e12f9a14 is not included in this approval.',
        'changed_cells': [
            dict(split=split, pair=pair, field='output', row=y, col=x, canonical=a, teaching=b)
            for split,pair,y,x,a,b in [('train', 2, 3, 27, 8, 4), ('train', 2, 4, 27, 8, 4), ('test', 1, 13, 15, 4, 6)]
        ],
    },
    'f18ec8cc': {
        'canonical_sha256': 'fc8ce6bdc6ea151735fff7baf9daf16737de59483927de510656fc4263021b18',
        'teaching_sha256': '7da42321e65a82b2d55ea8419893a808a0d1921987d0dfcce636a48afda8f3b8',
        'source': 'https://github.com/arcprize/ARC-AGI-2/pull/37',
        'approval': 'User approved the three upstream-backed labelled teaching copies on 2026-10-20; originals and scores remain unchanged.',
        'description': '52 output cells; upstream proposal remains unmerged. e12f9a14 is not included in this approval.',
        'changed_cells': [
            dict(split=split, pair=pair, field='output', row=y, col=x, canonical=a, teaching=b)
            for split,pair,y,x,a,b in [('train', 0, 0, 0, 9, 7), ('train', 0, 0, 1, 9, 7), ('train', 0, 0, 2, 9, 7),
 ('train', 0, 0, 6, 7, 9), ('train', 0, 0, 7, 7, 9), ('train', 0, 0, 8, 7, 9),
 ('train', 0, 1, 0, 9, 7), ('train', 0, 1, 1, 9, 7), ('train', 0, 1, 2, 9, 7),
 ('train', 0, 1, 6, 7, 9), ('train', 0, 1, 7, 7, 9), ('train', 0, 1, 8, 7, 9),
 ('train', 0, 2, 0, 9, 7), ('train', 0, 2, 1, 9, 7), ('train', 0, 2, 2, 9, 7),
 ('train', 0, 2, 6, 7, 9), ('train', 0, 2, 7, 7, 9), ('train', 0, 2, 8, 7, 9),
 ('train', 0, 3, 0, 9, 7), ('train', 0, 3, 1, 9, 7), ('train', 0, 3, 2, 9, 7),
 ('train', 0, 3, 6, 7, 9), ('train', 0, 3, 7, 7, 9), ('train', 0, 3, 8, 7, 9),
 ('train', 0, 4, 0, 9, 7), ('train', 0, 4, 1, 9, 7), ('train', 0, 4, 2, 9, 7),
 ('train', 0, 4, 6, 7, 9), ('train', 0, 4, 7, 7, 9), ('train', 0, 4, 8, 7, 9),
 ('train', 0, 5, 0, 9, 7), ('train', 0, 5, 1, 9, 7), ('train', 0, 5, 5, 9, 7),
 ('train', 0, 5, 6, 7, 9), ('train', 0, 5, 7, 7, 9), ('train', 0, 5, 8, 7, 9),
 ('train', 0, 6, 0, 9, 7), ('train', 0, 6, 2, 9, 7), ('train', 0, 6, 6, 7, 9),
 ('train', 0, 6, 8, 7, 9), ('train', 0, 7, 0, 9, 7), ('train', 0, 7, 1, 5, 7),
 ('train', 0, 7, 2, 9, 7), ('train', 0, 7, 4, 7, 5), ('train', 0, 7, 6, 7, 9),
 ('train', 0, 7, 8, 7, 9), ('train', 0, 8, 0, 9, 7), ('train', 0, 8, 1, 9, 7),
 ('train', 0, 8, 2, 9, 7), ('train', 0, 8, 6, 7, 9), ('train', 0, 8, 7, 7, 9),
 ('train', 0, 8, 8, 7, 9)]
        ],
    },
    'e12f9a14': {
        'canonical_sha256': 'a1cc429cf5f97fd8dcb45a950adb349efbe656e1df910f345f15fe2f70b7aa9e',
        'teaching_sha256': '93f840ad5d248dd01325d6fda5de589534b81c28a7289f98775d0bf21b1e7355',
        'source': 'arc_agi2/reports/label-reviews/e12f9a14.json',
        'approval': 'User requested corrected training copies and delegated investigation/finalization on 2026-10-20; local review selected the uniform-ray teaching hypothesis.',
        'evidence_status': 'locally_reviewed_hypothesis_not_official_correction',
        'description': 'Add the six-cell yellow ray from the open bottom-right corner in train[2]. Original labels and benchmark scoring remain unchanged; intended-label uncertainty remains explicit.',
        'changed_cells': [
            dict(split='train', pair=2, field='output', row=y, col=x, canonical=8, teaching=4)
            for y,x in [(13,14),(14,15),(15,16),(16,17),(17,18),(18,19)]
        ],
    },
}

# Reviewed additions: benchmark originals remain immutable.
APPROVED_CORRECTIONS.update({'a3f84088': {'canonical_sha256': '8d3777b00a4c5aa3b80c8e313336a6ea07d244669c4ac9eba66679f557f3d132',
              'teaching_sha256': '7e159ee4b32abae2c7b6304d3a7f2b413ec785aabf913a378c1310950c688b69',
              'source': 'https://github.com/fchollet/ARC-AGI/issues/132',
              'approval': 'User requested corrected teaching copies and delegated investigation/finalization '
                          'on 2026-10-20; host reviewed evidence and finalized this explicitly labelled copy '
                          'on 2026-10-21.',
              'evidence_status': 'upstream_reported_locally_reviewed_not_official_correction',
              'description': 'One center cell in train[3] follows the same repeating ring rule. Open '
                             'issue132 supports the discrepancy; no adopted official correction. Canonical '
                             'benchmark data and scoring remain unchanged.',
              'changed_cells': [{'split': 'train',
                                 'pair': 3,
                                 'field': 'output',
                                 'row': 5,
                                 'col': 5,
                                 'canonical': 0,
                                 'teaching': 5}]},
 'd931c21c': {'canonical_sha256': '34200461c67f8bd4dc547fb156a7d8721730e7cf535579d0e3074e00ec81932b',
              'teaching_sha256': 'a7124274c4de361383de34fffdc79a4073af665f68003b03b38474e2dfd52c72',
              'source': 'https://github.com/arcprize/ARC-AGI-2/pull/75',
              'approval': 'User requested corrected teaching copies and delegated investigation/finalization '
                          'on 2026-10-20; host reviewed evidence and finalized this explicitly labelled copy '
                          'on 2026-10-21.',
              'evidence_status': 'upstream_proposed_unmerged_correction',
              'description': 'One extraneous red cell in train[2] removed, exactly matching the unmerged '
                             'PR75 patch. Canonical benchmark data and scoring remain unchanged.',
              'changed_cells': [{'split': 'train',
                                 'pair': 2,
                                 'field': 'output',
                                 'row': 13,
                                 'col': 3,
                                 'canonical': 2,
                                 'teaching': 0}]},
 '963c33f8': {'canonical_sha256': '6fde852adb547efdae404e42f402e6b2dd73f56101e4df3f61a58cc86f9483ca',
              'teaching_sha256': 'affd3a1a8d3eb8325fe6f601646750d47ec23e914e0cb331e430c342a6c7280c',
              'source': 'arc_agi2/reports/label-reviews/963c33f8.json',
              'approval': 'User requested corrected teaching copies and delegated investigation/finalization '
                          'on 2026-10-20; host reviewed evidence and finalized this explicitly labelled copy '
                          'on 2026-10-21.',
              'evidence_status': 'locally_reviewed_native_compatible_hypothesis_not_official_correction',
              'description': 'Six shifted-stick cells in train[2] corrected. Retains floor clearing observed '
                             'in train[1]. Competing eight-cell proposal remains documented; intended-label '
                             'uncertainty is unresolved. Canonical benchmark data and scoring remain '
                             'unchanged.',
              'changed_cells': [{'split': 'train',
                                 'pair': 2,
                                 'field': 'output',
                                 'row': 13,
                                 'col': 11,
                                 'canonical': 7,
                                 'teaching': 9},
                                {'split': 'train',
                                 'pair': 2,
                                 'field': 'output',
                                 'row': 13,
                                 'col': 12,
                                 'canonical': 9,
                                 'teaching': 5},
                                {'split': 'train',
                                 'pair': 2,
                                 'field': 'output',
                                 'row': 14,
                                 'col': 11,
                                 'canonical': 5,
                                 'teaching': 9},
                                {'split': 'train',
                                 'pair': 2,
                                 'field': 'output',
                                 'row': 14,
                                 'col': 12,
                                 'canonical': 9,
                                 'teaching': 5},
                                {'split': 'train',
                                 'pair': 2,
                                 'field': 'output',
                                 'row': 15,
                                 'col': 11,
                                 'canonical': 7,
                                 'teaching': 9},
                                {'split': 'train',
                                 'pair': 2,
                                 'field': 'output',
                                 'row': 15,
                                 'col': 12,
                                 'canonical': 9,
                                 'teaching': 7}]}})

APPROVED_CORRECTIONS.update({'df8cc377': {'added_demonstrations': 1,
              'approval': 'User delegated investigation and finalization of labelled teaching '
                          'copies; host approved context enrichment on 2026-10-21.',
              'canonical_sha256': '18bd3cd2985e28e79fa7d3f6c432d1549083c64a3bd4d4624038b2a2ff85b4a1',
              'changed_cells': [],
              'description': 'One native demonstration resolves checkerboard phase. All original '
                             'pairs unchanged. Original context is ambiguous and is not claimed '
                             'solved. Fresh synthetic episodes require independently sufficient '
                             'demonstrations.',
              'evidence_status': 'locally_reviewed_additional_native_demonstration_not_canonical_solution',
              'kind': 'context_enriched',
              'original_fixture_context_passed': False,
              'source': 'arc_agi2/reports/label-reviews/df8cc377.json',
              'teaching_sha256': '8d6764a7efd5998f1e4a4ef91c60e5757f5cd9c56b8834d9fb77c37435736a60'}})

APPROVED_CORRECTIONS.update({'d753a70b': {'approval': 'User delegated investigation/finalization of labelled teaching copies; '
                          'host finalized audited concentric hypothesis on 2026-10-21.',
              'canonical_sha256': '388e9ae29018272a34b65076f3ae47d3db109f01d18e41b0edeb1af3a5a26b57',
              'changed_cells': [{'canonical': 7,
                                 'col': 4,
                                 'field': 'output',
                                 'pair': 0,
                                 'row': 13,
                                 'split': 'train',
                                 'teaching': 5},
                                {'canonical': 5,
                                 'col': 5,
                                 'field': 'output',
                                 'pair': 0,
                                 'row': 13,
                                 'split': 'train',
                                 'teaching': 7},
                                {'canonical': 7,
                                 'col': 3,
                                 'field': 'output',
                                 'pair': 0,
                                 'row': 14,
                                 'split': 'train',
                                 'teaching': 5},
                                {'canonical': 5,
                                 'col': 4,
                                 'field': 'output',
                                 'pair': 0,
                                 'row': 14,
                                 'split': 'train',
                                 'teaching': 7},
                                {'canonical': 7,
                                 'col': 5,
                                 'field': 'output',
                                 'pair': 0,
                                 'row': 14,
                                 'split': 'train',
                                 'teaching': 5},
                                {'canonical': 5,
                                 'col': 6,
                                 'field': 'output',
                                 'pair': 0,
                                 'row': 14,
                                 'split': 'train',
                                 'teaching': 7},
                                {'canonical': 7,
                                 'col': 2,
                                 'field': 'output',
                                 'pair': 0,
                                 'row': 15,
                                 'split': 'train',
                                 'teaching': 5},
                                {'canonical': 5,
                                 'col': 3,
                                 'field': 'output',
                                 'pair': 0,
                                 'row': 15,
                                 'split': 'train',
                                 'teaching': 7},
                                {'canonical': 7,
                                 'col': 6,
                                 'field': 'output',
                                 'pair': 0,
                                 'row': 15,
                                 'split': 'train',
                                 'teaching': 5},
                                {'canonical': 5,
                                 'col': 7,
                                 'field': 'output',
                                 'pair': 0,
                                 'row': 15,
                                 'split': 'train',
                                 'teaching': 7}],
              'description': 'Uniform concentric radius change matches native random mechanism and '
                             'all other original rings. One canonical boundary ring is translated '
                             'one column. Third-party atlas encodes a special three-cell boundary '
                             'V shift, not an independently established general law; intent '
                             'remains uncertain. This copy deliberately removes the translation '
                             'for teaching and never changes benchmark scoring.',
              'evidence_status': 'locally_reviewed_uncertain_concentric_hypothesis_not_official_correction',
              'original_fixture_context_passed': False,
              'source': 'arc_agi2/reports/label-reviews/d753a70b.json',
              'teaching_sha256': 'a03a9f3f00d34993369efe51ec7f887c184353bec9361e410b13eb5e7054a41a'}})

APPROVED_CORRECTIONS.update({'ba1aa698': {'approval': 'User delegated investigation/finalization of labelled teaching copies; '
                          'host selected audited uniform-motion synthetic teaching hypothesis '
                          'on2026-10-21.',
              'canonical_sha256': '8a8682f21e71f303ce2d7dcd02091df3278e2be978151965590c559536f97fdd',
              'changed_cells': [{'canonical': 2,
                                 'col': 2,
                                 'field': 'output',
                                 'pair': 1,
                                 'row': 11,
                                 'split': 'train',
                                 'teaching': 8},
                                {'canonical': 2,
                                 'col': 3,
                                 'field': 'output',
                                 'pair': 1,
                                 'row': 11,
                                 'split': 'train',
                                 'teaching': 8},
                                {'canonical': 8,
                                 'col': 2,
                                 'field': 'output',
                                 'pair': 1,
                                 'row': 13,
                                 'split': 'train',
                                 'teaching': 2},
                                {'canonical': 8,
                                 'col': 3,
                                 'field': 'output',
                                 'pair': 1,
                                 'row': 13,
                                 'split': 'train',
                                 'teaching': 2}],
              'description': 'Four train[1] output cells follow the unchanged native uniform '
                             'motion mechanism. Original intent remains uncertain: fitted residual '
                             'alternatives remain documented. Original benchmark labels/scoring '
                             'and query answers stay unchanged.',
              'evidence_status': 'locally_reviewed_uncertain_uniform_motion_hypothesis_not_official_correction',
              'original_fixture_context_passed': False,
              'source': 'arc_agi2/reports/label-reviews/ba1aa698.json',
              'teaching_sha256': 'de83dfb0e6a16a2c13e4d0a3d3241a82a7353df7e97a056e154411976ed5a8d0'}})

def digest(task):
    return hashlib.sha256(json.dumps(task,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def fixture_basis(tid, packet=None):
    """Return the reviewed validation basis, with an explicit correction label."""
    approval=APPROVED_CORRECTIONS.get(tid)
    if approval is None:
        return {'fixture':'canonical','corrected':False}
    packet=reference(tid) if packet is None else packet
    if digest(packet['canonical'])!=approval['canonical_sha256'] or digest(packet['teaching_fixture'])!=approval['teaching_sha256']:
        raise ValueError('Approved fixture hashes changed for '+tid)
    return {'fixture':'teaching_fixture','corrected':True,**approval}
