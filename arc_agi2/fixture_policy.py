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
