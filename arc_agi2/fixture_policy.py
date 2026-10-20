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
