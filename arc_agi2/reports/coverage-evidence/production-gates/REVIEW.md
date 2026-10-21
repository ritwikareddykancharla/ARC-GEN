# Production evidence-gate review

Prepared for host integration; no live fork files changed and no production job launched.

## What was wrong

`build_million.make_episodes` fixes a query before its 50-attempt demonstration-context search and passes only `{'input': q['input']}` into the evidence gate. That part is correct. Its single `except MissingColourEvidence: continue` was insufficient:

| Family | Existing rejection | Existing production consequence | Proposed action |
|---|---|---|---|
| c6e1b8da | IntrinsicAmbiguity is a MissingColourEvidence subtype | Retries demos for an irreducibly ambiguous query | Typed query rejection; quarantine this input |
| b7955b3c | IntrinsicAmbiguity is plain ValueError | Aborts whole family | Typed query rejection; continue remaining planned queries |
| d5c634a2 | MissingTTallyEvidence has `intrinsic=True` | Flag ignored; retries demos | Adapt intrinsic flag; search-budget reason separate |
| 1b8318e3 | Typed local exceptions; no shared dispatch found | Shared episode gate absent | Add dispatch; shared intrinsic/budget inheritance |
| b1986d4b | Query role parse failure wrapped as MissingColourEvidence | Retries demos despite unparseable query | Query parse rejection typed; unresolved cap/orientation stays context retry |
| df8cc377 | Query role ambiguity and phase-context shortfall flattened | Both retry demos | Role/no-reading typed query rejection; phase shortage retries |
| b230c067 | Intrinsic parse ambiguity flattened | Retries demos | Native parse ambiguity/no-parse typed query rejection |
| e048c9ed, f3e14006 | Gate status raised as plain ValueError | Even normal context shortage aborts family | Raise MissingColourEvidence; preserve all hypothesis checks |

The 1b change preserves the coverage_legend worker's new query-first checks and demo-vs-query classification. An intrinsically ambiguous demonstration raises DockingContextAmbiguity and keeps the query; an intrinsically ambiguous query raises IntrinsicDockingAmbiguity. The proposed patch only changes its imports and base classes.

## Hidden-answer selection issue

`make_record` verifies the emitted program against known query labels. Previously, a failure emptied `pending` and continued the demonstration retry loop. The solver never received the label, but the assembler could choose a different context because the previous context failed the query-answer check. That is answer-informed context selection.

The patch quarantines that entire query after the first post-gate rejection, retains the failed episode, discards every orientation, and never retries it later in the same split. It does not turn mismatches into partial accepted episodes. Unknown exceptions outside the explicit existing verification exception set still propagate.

`demonstrations_disambiguate` intentionally compares labels of D4 variants with identical visible prompts. This is a label-consistency audit, not an input-only evidence gate. Its failure now also quarantines the query instead of searching demonstration contexts using the conflicting labels. Intrinsic identifiability remains determined by task-specific input-only gates.

Motif/legend answer mismatches already raise and abort the family, rather than retry contexts; the patch does not weaken those checks. Labels still legitimately define training completions and allocation strata (output-size relation). No claim is made that the complete dataset-construction process is label-free.

## Counters and saved artifacts

- `intrinsic_query_evidence_rejected`: unique query inputs rejected under the documented input-only hypothesis scope.
- `evidence_search_budget_exhausted`: evidence computation did not finish within its search bound; **not** a proof of intrinsic ambiguity. Conservatively quarantined for investigation, even if a demonstration triggered the budget.
- `post_gate_program_rejected`: program execution/validation/verification failure after the evidence gate, no context retry.
- `augmented_label_conflict`: identical visible augmented prompts have differing labels; no context retry.
- `query_rejections`: query hash, stratum, number of attempts, classification, error, available witness.
- `quarantined_query_count`: rejected query inputs excluded from later query selection in that split.
- `query_context_shortfalls` remains reserved for unresolved context/episode constraints; retry cap unchanged at 50 (1 for stored contexts).
- Program-failure records use `rejections/<split>/<task_id>/<query_input_hash>.json`, preventing the previous one-file-per-family overwrite.

Rejecting intrinsically ambiguous inputs intentionally changes the admitted domain; these inputs remain reported and are not silently replaced until quota is filled. Search-budget and program failures are quarantines for repair, not justified domain exclusions. The strict gates themselves are not weakened or bypassed.

## Evidence about context-retry limits

- b230c067's committed coverage report required **76,957** last-demo draws to resolve **30** deliberately hard repeated-fragment queries (2,565.2 draws/query on average), with zero exhaustion under its larger audit budget. This is not a measured production-50 failure rate, since production redraws three demos from a finite pool. It does establish that assuming 50 random contexts always suffice is unjustified. Prefer input-only evidence-directed context selection from a suitably rich pool; if no such context exists, report a shortage rather than choose easier queries or accept ambiguity.
- Historical b7cb93ac report `query-preserving-assembly-1065-before-selection.json`: 48/82 requested fresh episodes; 34 queries exhausted 50 attempts (1,700 missing-evidence attempts). A subsequent targeted selector improved the small-pool result to 81/82; the remaining one query had no three-demo packing context, rather than too few retries. A later larger/balanced report passes 1,000/1,000. Increasing the cap alone is not the general fix.
- Current ac0c5833/e048c9ed/f3e14006 audits report 163/68/123 total context resamples across 250 accepted episodes respectively. Those are aggregates, not maximum retries, so they do not establish a necessary per-query cap.
- df8cc377: 10 context resamples/250 accepted episodes; no exhausted queries in that audit. e5062a87 review: maximum 3 resamples/query, 0 exhausted.
- No production quotas or retry budgets are increased by this patch.

## Verification

- `test_proposal.py`: **17 passed**. Runs the actual proposed `make_episodes` AST with deterministic local fakes, covering fixed-query context retry, no intrinsic reattempt, query quarantine, complete D4 discard, poisoned query-answer invariance of chosen context, budget separation, explicit cap reporting, real c6/b795 ambiguity witnesses, typed task dispatch, and standalone gate imports.
- `run_portable_tests.py`: **51 passed** across existing c6, b795, docking, d5, e048, f3e and ac0 gate/factory tests against the overlay. No generation jobs or model calls.
- `git apply --check production-gates.patch`: passed against the live fork after the docking worker update.
- `source-hashes.json`: exact pre/post hashes of every proposed file. Check these or `git apply --check` again before applying because other agents may change shared files.

The patch changes exception/control flow and bookkeeping, not generated solver logic or constructor distributions. Parent should refresh changed gate hash evidence/cert metadata according to repository policy; factory/native hashes remain unchanged.
