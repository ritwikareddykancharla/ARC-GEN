# Native batch I (2026-10-25): 18447a8d and b4a43f3b

Base `96be803`. The review (`native-domain-review-20261024`, commit 517bd83) was treated as
evidence, not authority, and every figure here was re-measured.

**Not a production export.** Neither ID is admitted or registered, and `admission.json` pins
`verified_rules.py` and `colour_evidence.py`, which this batch changes. Root still has to
rebuild admission, register the families and run the production 1000 train / 20 validation
export. Admission, prepare, policies and registries were not modified or monkeypatched.

## Commits

| Commit | Scope |
|---|---|
| `c9260a5` | pre-gate witnesses archived on base sources (`pre-gate-witnesses-96be803.json`) |
| `c9af69f` | constructors and old-vs-new explicit-path equivalence |
| `37cde2c` | `verified_rules`: b4a43f3b geometric separator checker (b4 only) |
| `865d919` | b4 uniform-count scatter maps; mask docstring |
| `5efcfea` | `native_i_evidence.py` gates and two-ID dispatch; tests; priority ablation |
| (final) | certificates, profile-honouring context audit, coverage, family tests, this README |

Shared-source hashes:
- `verified_rules.py`: a54743d7 → 3a3425ae.
- `colour_evidence.py`: 6789d3d8 → dbb4f883.
- `native_i_evidence.py`: new, b297b9cc.

**Integration dependency.** Earlier batches (D/E) pin `colour_evidence.py` and/or
`verified_rules.py` in their audit reports, and F/G/H may touch the same files. These pins
describe this branch only, not the merged tree. Global hash and audit refresh belongs to root's
final integration. No old hash strings were hand-edited.

Measured on this branch: 8 pin tests fail, and the other 86 D/E tests pass.
- Failing: `test_native_batch_d.py::test_certificates_bind_current_bytes` for 195ba7dc,
  281123b4, 31d5ba1a and 34b99a2b, and the same test in `test_native_batch_e.py` for 0c786b71,
  e0fb7511, f0df5ff0 and f3cdc58f.
- Cause: their `context-audit.json` pins `colour_evidence` 6789d3d8; those audits pin
  `verified_rules` a54743d7 too.
- These are pin failures only. The new dispatch returns early for 18447a8d/b4a43f3b and touches
  no other ID, and the only `verified_rules` change is a new b4 entry.
- Root's integration rerun of those audit scripts on the merged tree clears them.

## Domains (rules, roles, canonical JSON and factories unchanged)

| ID | Before | After (default) | Explicit |
|---|---|---|---|
| 18447a8d | 3..4 bands; unbounded while-True loop; canonical train[1] (2 bands) unreachable | 2..7 bands (uniform), new `num_bands`; distinct lock profiles sampled directly (matching is unique iff profiles differ), so no rejection loop; keys shuffled | complete `lefts/rights/colors`: old code verbatim |
| b4a43f3b | 13x6 only; exactly 3 axis segments; canonical train[1] (4 segments) unreachable; unbounded sprite loop | map: 1..8 segments + 0..2 free cells (2/3), or a uniform-count scatter of 1..area cells (1/3); motif scale 1..3 (map width 3s); map height 1..10; motif masks enumerated (full 3x3 span, 8-connected, 3..9 cells; helper reached 4..9); colours {1,2,3,6} | complete `colors+pattern` without `scale`/`map_height`: old 13x6 code verbatim |

**Width and total stay fixed for 18447a8d.** Width 11, total 5, 3-row bands and background
7 / lock 8 are unchanged, since no fixture varies them.

**Why scale and map height can vary for b4a43f3b.** The archived checker and the factory both
derive the factor from the top block (`top // 3`). A fixed factor of 2 is not even defined at
scales 1 and 3. Mixed-scale contexts are gated by fixed-factor extraction competitors. The
motif is never padded or cropped.

**Explicit-path legacy labels** (`legacy-equivalence.json`, 3000 random complete explicit
inputs per ID against the base sources, deliberately outside the default palette and domain):
- 0 mismatches.
- 18447a8d: 1348 valid and identical; 1652 cases where the old code returned None, crashed or
  left ARC bounds now raise `ValueError`.
- b4a43f3b: 2750 identical; 250 old crashes now raise `ValueError`.
- These legacy scenes are labelled but outside the certified default domain: repeated or
  0/7 key colours, 0 or 1 bands, colour-5 or all-0 motifs, empty maps.
- Partial arguments are kept, or raise; they are never silently ignored.

## Shared checker (b4 only)

The archived solver takes the first unique full uniform row as the separator. Two legal cases
break it:
- the scale-1 motif `111/202/030`, where it returns a 0x9 grid;
- legacy colour-5 motif rows.

`separated_motif_stamp` reads the documented geometry instead: a W x W s-fold motif square,
row W all 5, and every non-0 map cell marked. Results (`verifier-evidence-b4a43f3b.json`,
final bytes):

| Set | Reviewed | Archived |
|---|---|---|
| fixtures | 10/10 | – |
| old 1000 draws | 1000/1000 | 1000 |
| new 1000 draws | 1000/1000 | 998 |
| adversarial | 14/14 | 10 |

The factory passes 8 D4 x 2 palettes on all 12 palette[5]-unique adversarial scenes. The
earlier scale-1 colour restriction was removed on review: those motifs are valid content.

## Evidence gates (`native_i_evidence.py`, via `require_colour_evidence` → `make_record`)

The gates are bounded and named. They keep the competitors that reproduce every demo and
require one defined query answer. Answers are never read. Verdicts are D4-covariant because
both directions of each family are included. This is not an identifiability proof.

- **18447a8d.** Complement matching (native) vs same_band, reverse, cyclic shifts 1..6,
  area-only matching, and raw visible colour_ascending/descending.
  - The raw numeric orders are palette-dependent by design. Seed 9 with two bands is ambiguous
    under the identity palette and accepted under `[3,9,0,7,2,8,1,6,4,5]`; this is documented
    and tested, not a bug.
  - All-orders colour priority is a report-scoped ablation (`priority_ablation.py`). On 250
    paired fixed 2-band same-shape queries, with the same demo sequences and a 64-attempt bound:

    | Family | Accepted | Retries | Max retry |
    |---|---|---|---|
    | natural | 250/250 | 167 | 18 |
    | all orders | 249/250 | 1874 | 59 |

    Brute force over all orders agrees on 300/300 cases. All-orders would also reject the
    original ARC task: its demos fit 1<9<2<3<6<4, and query colour 5 is unseen.
- **b4a43f3b.** The product of five components, evaluated separably and cross-checked by
  brute force:
  - extraction: to 3x3, or a fixed factor 1..3;
  - motif D4;
  - fill: native, zeros as map colour, or silhouette;
  - map D4;
  - selector: marked, unmarked or all.

Both supervisor witnesses are accepted by `make_record` at the base (16/16) and rejected after
the gate (0/16; `post-gate-witnesses.json`). Canonical and teaching fixtures are accepted in
all 24 D4 x palette variants. Each named competitor has a constructor-built witness test.

## Certificates

Run with the unmodified `recertify.check` via `recertify_runner.py` (2 workers):
- 1000 fresh / 8000 D4 / 16 fixture variants;
- 0 sampler rejections;
- 1000 unique inputs.

Provenance and `draft_notes` were merged back from 96be803, with
`previous_constructor_sha256` and `previous_domain_limitations` added.

| ID | constructor (prev → new) | factory |
|---|---|---|
| 18447a8d | 616d77de → 8b26a6e3 | 63b5acbc |
| b4a43f3b | 62217bdc → a2df6bff | ad0f0f59 |

## Fixed-query context audit (`context_audit.py`, `context-audit.json`)

What the audit does:
- 250 fixed queries per run, never dropped.
- Demos honour the canonical `profile_from_task` pattern, checked with `describe`:
  - 18447a8d is mixed/seen: one demo at the query's band count, two at other counts;
  - b4a43f3b is uniform/seen: all demos at the query's scale and height.
- All four inputs have distinct `prepare.input_orbit` identities.
- Every demo comes from the query's `input_split`, with at most 400 draws per slot.
- At most 64 contexts per query. `make_record` runs on all 8 D4 under a seeded palette, and
  the gate's unique prediction must equal the label.
- Labels are checked by `verification_solver`.

| Run | accepted | retries (max) | query split train/val | demo draws / slots (train; val) |
|---|---|---|---|---|
| 18447a8d default | 250/250 | 3 (1) | 242/8 | 768/735; 598/24 |
| 18447a8d 2 bands | 250/250 | 1 (1) | 243/7 | 773/732; 457/21 |
| b4a43f3b default | 250/250 | 1 (1) | 235/15 | 738/708; 989/45 |
| b4a43f3b 5x3 (s=1, h=1) | 250/250 | 51 (8) | 239/11 | 929/870; 734/33 |

- **Calls.** Each run made 2000 `make_record` calls.
- **Draw cost.** Split-matched demos cost about 20–25 draws per validation slot and about 1.05
  per train slot.
- **Split scope.** Validation queries are only the ~1/20 hash fraction of these fixed queries,
  not a 20-episode quota.
- **Same-shape stress.** The same-shape 2-band ablation above is a stress report only: the
  production profile for 18447a8d is mixed, which explains the much lower retries here.

## Coverage (1000 draws, same seeds; `batch-i-evidence.json`)

| ID | input shapes before → after | before → after |
|---|---|---|
| 18447a8d | 2 → 6 | bands {3,4} → 2..7 (154–177 each); distinct orbits 999 → 1000; keys all moved 353 → 410 |
| b4a43f3b | 1 → 30 | scale 2 → 1/2/3 (347/317/336); map height 6 → 1..10; map occupancy 0.08–0.47 → 0.02–1.00 (70 full maps); motif cells 4..6 → 3..9 |

0 checker disagreements before and after.

**Capacity, 18447a8d at 2 bands** (the smallest random corner):
- 8064 layouts;
- 4080 distinct `input_orbit` identities;
- 3892 train / 188 validation by `input_split`.

This matches the supervisor's enumeration. Other band counts and b4 shapes are far larger.

## Limits and outstanding

- **Production export.** It is root-owned. The 1000 train / 20 validation distinct-orbit export
  still needs admission, registration, a prepare run and a merged-tree hash refresh. No quota
  is claimed here.
- **Factory domain.** The b4 factory locates palette[5]. Legacy explicit colour-5 motifs are
  outside its domain, as they were before, and are not sampled by default.
- **Gate scope.** The gates rule out the listed alternatives only. Same-shape 2-band contexts
  for 18447a8d need resampling (about 12% first-context acceptance in the stress run). The
  production mixed profile needs very little.
- **Process note.** Two supervisor-rejected tool calls were nonetheless applied on disk:
  - a scratch probe edit (`/tmp`, 2000-draw/2-palette probe);
  - the alias/orbit-motif test-helper edit.

  Both were kept deliberately. The probe matches what is reported, and the test edit is the
  intended fix.

## Tests

| File | Covers |
|---|---|
| `diversity/test_native_batch_i.py` (25) | fixtures; random domains; explicit and legacy paths; boundary shapes via checker + factory on 8 D4 x 2 palettes; timing; certificate, audit and equivalence hash binding |
| `test_native_i_evidence.py` (38) | each competitor's witness; documented seed-9 palette dependence; D4 covariance; b4 palette invariance; brute-force cross-checks; fixtures; `make_record` dispatch; runtime bound |
| `diversity/test_b4_verifier.py` (16) | checker registration, fixtures, counterexample, adversarial cases, raising, evidence pins |
