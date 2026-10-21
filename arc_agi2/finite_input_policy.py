"""Audited exceptions for native families with very few D4/palette input orbits.

This module does not change generation or launch jobs. A caller must apply the
same identity to eligibility, demonstration selection, and final uniqueness.
Four exact-distinct inputs remain mandatory: three demonstrations and a query.

A canonical orbit reserved for train is reserved globally, never per family.
Previously published pool rows/reports must be re-split and recounted, and any
validation episode containing a reserved orbit must be removed or rebuilt.
Include POLICY_SIGNATURE in pool and episode cache signatures when integrating.
No independent unseen-orbit validation is claimed for a single-orbit family.

Audit: main repo outputs/research/arcgen-program-grid-launch/pool-audit/findings.md
Pinned HF dataset revision: 5a2f7abfd90ea205bc4e5e777efba353d1550a25.
The a85d4709 with-replacement column sampler is a documented follow-up only;
this policy does not modify its generator or enlarge any native support.
"""
import hashlib
import json
import re
from types import MappingProxyType

VERSION = 'finite-input-policy-v1'
AUDIT_DATASET_REVISION = '5a2f7abfd90ea205bc4e5e777efba353d1550a25'

FAMILY_PROVENANCE = {'0d3d703e': {'mechanism': 'Fixed colour substitution on three distinct stripes. Palette '
                           'canonicalization removes the very colour identities being learned.',
              'native_source': 'tasks/task_0d3d703e.py',
              'native_source_sha256': '415c3ef4385b4d64d93dec67f339de4d12eeeae09a4f4593ec30d5ad7a52e431',
              'native_support_note': '8P3 = 336 native default inputs; all observed. Keep query-colour '
                                     'demonstration evidence.'},
 '27a28665': {'mechanism': 'Demonstrated mask-to-output legend; the same mask in a different ink colour '
                           'can supply necessary evidence.',
              'native_source': 'tasks/task_27a28665.py',
              'native_source_sha256': 'ea370ba360ef2eb8e26b75bfb5593698509f78bcf59151466a809a6626d5494b',
              'native_support_note': 'Existing builder exception. Exact input uniqueness and the query '
                                     'legend-key evidence check remain mandatory.'},
 '3979b1a8': {'mechanism': 'Expand a fixed three-colour cross/corner motif into its larger patterned '
                           'construction.',
              'native_source': 'tasks/task_3979b1a8.py',
              'native_source_sha256': '433e97395ef5bb002c56cc40b77ed02147d7a2e7def2f78ae3f631b6ed0f6517',
              'native_support_note': '9P3 = 504 native default inputs; all observed.'},
 '4522001f': {'mechanism': 'A three-cell green quadrant marker determines two large diagonal green '
                           'blocks.',
              'native_source': 'tasks/task_4522001f.py',
              'native_source_sha256': 'd422664dc7ca47d2f37d90c407b926652e09a24ceaa166a99a473104b2689212',
              'native_support_note': 'Exactly four default quadrant cases. Four exact-distinct inputs '
                                     'suffice for three demonstrations and a query. Do not inflate by '
                                     'demo-order permutations.'},
 '66e6c45b': {'mechanism': 'Move the four distinct colours in the central 2×2 block to the '
                           'corresponding outer corners.',
              'native_source': 'tasks/task_66e6c45b.py',
              'native_source_sha256': 'b1cc1e42aa38c777553b8f5ec6646911d4617b2d8c25a6f7765196bbc7e33481',
              'native_support_note': '9P4 = 3,024 native default inputs; 1,200 sampled. Single palette '
                                     'orbit does not mean only one exact example.'},
 '833966f4': {'mechanism': 'Swap the first two and last two elements of a five-colour column, keeping '
                           'the middle element.',
              'native_source': 'tasks/task_833966f4.py',
              'native_source_sha256': 'f80959bd5426733f1fdc240632a601e56ad41bb3287efb84ba422eb6e12ab288',
              'native_support_note': '10P5 = 30,240 native default inputs; 1,200 sampled, all currently '
                                     'validation. Needs global orbit reservation, not family-only split '
                                     'override.'},
 '8b28cd80': {'mechanism': 'A single coloured pixel locates the origin of a clipped expanding '
                           'rectangular spiral.',
              'native_source': 'tasks/task_8b28cd80.py',
              'native_source_sha256': 'c67eab8e7ee3c99830364fab9cdfa8d4bcef3a250c9a0b01816994e1f4d7b0f9',
              'native_support_note': 'Nine positions × nine colours = 81 native inputs. Three geometric '
                                     'orbits (corner, edge, centre), all currently training.'},
 '93b581b8': {'mechanism': 'Copy colours of a 2×2 block into four diagonally offset 2×2 blocks, '
                           'clipping at boundaries.',
              'native_source': 'tasks/task_93b581b8.py',
              'native_source_sha256': '149cad5f55e7576e3141cf0d0a838cc5f8e642572f1aab35ce558a48252b9879',
              'native_support_note': 'Nine anchors × 9P4 = 27,216 default inputs, but only three D4 '
                                     'anchor orbits. 1,200 sampled.'},
 '94414823': {'mechanism': 'Two outside colour markers determine the alternating 2×2 coloured tiles '
                           'inside a grey frame.',
              'native_source': 'tasks/task_94414823.py',
              'native_source_sha256': 'd4c881e833258ea3a81fc6b578b97400675ba6c5803fbc977870383c197ec405',
              'native_support_note': '8P2 colours × four orientations = 224 native default inputs; all '
                                     'observed.'},
 'a85d4709': {'mechanism': 'Each grey pixel’s column selects the colour filling its entire row.',
              'native_source': 'tasks/task_a85d4709.py',
              'native_source_sha256': '679472699877cc13233c3c4cedded2e28c83e6debd9b29bcd1f8dc44211731f2',
              'native_support_note': 'Default shuffle gives only 3! = 6 layouts. Native '
                                     'generate(cols=...) and canonical fixtures also support repeated '
                                     'columns, giving 3^3 = 27 layouts: default-sampler coverage is '
                                     'unnecessarily restricted.'},
 'bda2d7a6': {'mechanism': 'Cyclically shift the colours of concentric square rings.',
              'native_source': 'tasks/task_bda2d7a6.py',
              'native_source_sha256': '2903b625f23383cf37a347087a97136a168e58868bc8f28ed6709b424e98901a',
              'native_support_note': 'Two sizes × 10P3 = 1,440 native default inputs; 1,200 sampled. '
                                     'The two sizes become two palette/D4 input orbits.'},
 'ca8de6ea': {'mechanism': 'Compress/remap the five colour roles of a symmetric diagonal motif into a '
                           '3×3 pattern.',
              'native_source': 'tasks/task_ca8de6ea.py',
              'native_source_sha256': '97956be7d75541d1dc634dab84905176d3418e57fadda7302b1add3d3763edb8',
              'native_support_note': '9P5 = 15,120 native default inputs; 1,200 sampled, all one '
                                     'palette/D4 orbit.'}}

FINITE_INPUT_TASK_IDS = frozenset(FAMILY_PROVENANCE)
# Only this audited one-orbit family had every available input assigned to val.
# feca6190 also contains this input orbit: reservation MUST be global.
GLOBAL_TRAIN_ORBITS = frozenset({
    '728f2830dc356b54d2a72152929d7c96085bfd0585626d52890ce1aec18409c3',
})

POLICY_SIGNATURE = hashlib.sha256(json.dumps({
    'version': VERSION,
    'families': FAMILY_PROVENANCE,
    'global_train_orbits': sorted(GLOBAL_TRAIN_ORBITS),
    'minimum_exact_inputs': 4,
}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
# Expose provenance read-only, including each nested family record.
FAMILY_PROVENANCE = MappingProxyType({
    tid: MappingProxyType(record) for tid, record in FAMILY_PROVENANCE.items()
})


def identity_key(task_id):
    """Identity used for WITHIN-episode distinctness, never for split assignment."""
    return 'input_hash' if task_id in FINITE_INPUT_TASK_IDS else 'canonical_input_hash'


def minimum_class_requirement(task_id):
    """Minimum classes of identity_key(task_id): three demos plus one query."""
    return 4


def input_split(canonical_hash):
    """Globally consistent canonical split, with one explicit train reservation.

    There is deliberately no task_id argument: the same canonical input cannot
    be training in one family and validation in another. Other finite-family
    hashes retain their original split.
    """
    if not isinstance(canonical_hash, str) or not re.fullmatch(r'[0-9a-f]{64}', canonical_hash):
        raise ValueError('canonical_hash must be a lowercase SHA-256 hex digest')
    if canonical_hash in GLOBAL_TRAIN_ORBITS:
        return 'train'
    return 'validation' if int(canonical_hash[:8], 16) % 20 == 0 else 'train'


def _count(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f'{field} must be a nonnegative integer')
    return value


def capacity_basis(report, split):
    """Return eligible SUPPORT, not an episode quota or augmented row count.

    Native pool rows are exact-input deduplicated, so summing their per-stratum
    counts gives exact distinct split inputs. Finite families use that support;
    ordinary families use canonical support. Fewer than four selected identity
    classes gives zero. Contextual-episode quotas remain the caller's concern.

    Reports must reflect the current input_split policy. In particular, an old
    all-validation 833966f4 report is NOT silently converted into train counts.
    """
    if split not in ('train', 'validation'):
        raise ValueError('split must be train or validation')
    task_id = report['task_id']
    if task_id in FINITE_INPUT_TASK_IDS:
        strata = report[split + '_strata']
        support = sum(_count(n, split + '_strata.' + str(k)) for k, n in strata.items())
    else:
        support = _count(report[split + '_canonical'], split + '_canonical')
    return support if support >= minimum_class_requirement(task_id) else 0
