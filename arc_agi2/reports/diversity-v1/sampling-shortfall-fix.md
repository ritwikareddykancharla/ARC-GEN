# Supplement episode-sampling shortfalls: diagnosis and fix

Scope: `arc_agi2/diversity/prepare.py` only. Generators, factories, colour
roles, admission, verified rules and the `REPAIRED` list are unchanged.

## Diagnosis (original 121-family 200/20 run, commit d71ead8, `--seconds 600`)

All eight short families use one original pattern, `uniform/seen`. Each
query therefore needs three other identities of the same input shape in its
own split. Native sources produce one shape with few orbits, and only 1–3 of
these fall in validation. RE-ARC sources spread over hundreds of shapes, so
validation shape bins are sparse. The original reports show two failure
modes, both independent of semantic gates; no episode or shape rejections
were recorded:

| family | old train/val | trials used (of 22,400) | cause |
|---|---|---|---|
| 0962bcdd | 200/18 | 10,304 (support stop) | assembly attempts spent re-drawing used queries |
| 25d8a9c8 | 200/19 | 16,832 (support stop) | same |
| 44f52bb0, a78176bb, 11852cab, d631b094, ed36ccf7 | 200/9, /4, /19, /16, /13 | 22,400 | trial budget, plus the same waste |
| feca6190 | 54/0 | 22,400 | strict source support (see below) |

Queries were drawn uniformly over exact rows, and used identities were
skipped silently. Identities with many exact rows therefore starved rare
ones within the `40 × quota` attempt budget. A simulation with one 300-row
identity plus 20 one-row identities completed 21 queries in only 40 of 200
seeds. The support check ran a quadratic shape scan every 64 accepted trials.

## Fix

* Queries are sampled uniformly by **identity**, then by row. Each identity
  is used at most once per split.
* Each failed attempt is counted against its query identity. After
  `MAX_QUERY_FAILURES = 8` failures the identity is retired, so a
  permanently invalid colour, context or program query cannot consume the
  budget.
* The strict shape gate is unchanged. Unmatched patterns are rejected,
  without cross-shape fallback.
* Pool sampling stops once strict support reaches the quota plus a margin of
  `max(2, ⌈quota/10⌉)`. It may extend to 4× the base trial budget only while
  support remains below the quota, and always within the original 60% time
  share. Every accepted extra proposal passes the unchanged source-specific
  verification gates.
* Feasibility checking is O(rows) for the uniform/seen pattern shared by
  these eight families. Other patterns cache checks by query shape and
  identity. Results match the old check, used as the test oracle.
* Reports add `pool_trials`, `pool_stop` and per-split `query_support`. A
  shortfall records its stop reason and states explicitly that it is an
  observed bounded-pool shortfall, **not** a finite-capacity claim.

## Evidence (laptop, 2 workers, `--train 200 --validation 20 --seconds 600`, seed 2026102401)

| family | before (original) | after | pool stop | val feasible ids |
|---|---|---|---|---|
| 0962bcdd | 200/18, 54.9 s | **200/20**, 21.6 s | support, 11,264 proposals | 25 |
| 44f52bb0 | 200/9, 117.8 s | **200/20**, 52.4 s | support_after_extension, 32,128 proposals | 21 |
| feca6190 | 54/0 | 54/0 (shortfall reported) | trial_budget, 89,600 trials, 35.2 s | 0 |

These timings compare different hosts/worker counts and are not a speed
benchmark. The initial local report counted the terminating support-check
iteration as a trial; the reviewed implementation counts actual proposals,
shown above. This counter correction does not change emitted episodes.

feca6190 observed support: 58 train identities in 5 shape bins, 54 of them
feasible, and one validation identity. This agrees with root's independent
enumeration (54 train / 0 validation). Native feca expansion is owned
separately.

An independent audit of all 494 exported rows found zero violations: global
input split, four distinct canonical and exact inputs, unique query orbits,
strict matched shapes and program re-verification. All 68 tests in the
diversity, profile, finite-input and shape-policy suites pass, including the
10 new tests in `diversity/test_prepare_sampling.py`.

Reviewer checks also passed the four augmentation-context tests and a real
2/2 episode smoke run. Its 2,432 proposals exactly equal accepted pool rows
plus duplicate and rejected proposals, verifying the corrected trial count.

## Unresolved

a78176bb, 25d8a9c8, 11852cab, d631b094 and ed36ccf7 were not re-run
locally; root should run the full after-export. Validation support is close
to quota for some families (44f52bb0 had 21 feasible for 20). Families with
weak validation support may stay short after the time-bounded extension. If
so, the cause will be reported as `bounded_pool_query_support`.
