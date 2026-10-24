"""Root-authorized context-aware certificate adapter for 98c475bf.

Why not arc_agi2.diversity.recertify: the standard harness draws four
independent default pairs per episode. After the width expansion those pairs
usually have different canvas widths, and even at one width a query marker
colour is often never demonstrated. The factory (correctly) refuses both, so
the standard harness fails. Its real failure is kept separately as
standard-recertify-98c475bf.json. This adapter is a dedicated harness, not an
edit to the shared one.

Method (fixed-query, compatible-context):
  * QUERIES fresh default queries are drawn once under fixed seeds and never
    replaced or dropped. A query whose bounded context search fails is
    listed and fails the certificate.
  * Only demonstrations are resampled: three generate(height=H, width=W)
    pairs at the query's own canvas shape, matching prepare's uniform/seen
    shape policy for this family. At most MAX_CONTEXTS contexts per query.
  * A context is accepted only by the production evidence gate,
    require_colour_evidence -> line_motif_evidence, run on the transformed
    demonstrations and the query INPUT under all eight D4 transforms with a
    seeded palette. Verdicts must agree across D4. The gate never sees the
    query label. A context is also rejected (and counted) if its three
    demonstration inputs and the query are not four distinct D4/palette
    orbits.
  * After acceptance, as soundness checks that never select a context: the
    gate's own prediction and the factory program (program_targets.verify:
    every demonstration and the query) must be exact under all eight D4
    transforms; motif_context (the native target) must be exact at d4 = 0.
    Any mismatch fails the certificate immediately.
  * The archived verifier (runtime.verification_solver) independently checks
    the label of every drawn pair: every query and every demonstration in
    every accepted or rejected context.
  * 16 canonical fixture variants (8 D4 x 2 palettes): gate, gate prediction
    and factory exact; validate() must replay the canonical fixtures.
  * Cross-width negative control on the first CROSS_WIDTH queries:
    demonstrations at another width must be refused by gate and factory.

Count definitions are written into the certificate. fresh_pairs_checked
counts fixed fresh QUERIES only; accepted demonstrations, rejected-context
draws and demo pair checks are separate fields.

Run from the worktree root:
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-routing-motif-20261025/certify_98c475bf.py [--write]
--write, only if passed, writes the merged record to
arc_agi2/direct_factories/98c475bf.json and its identical native-certificates
mirror (required by test_pipeline.native_recertification). The standard
harness failure stays in standard-recertify-98c475bf.json here.
Supplementary small-domain audits reuse audit_domain() (see context_audit.py).
"""
import hashlib
import importlib
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

from arc_agi2.augmentation import transformed
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.direct_factories import task_98c475bf as factory
from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.line_motif_evidence import solve_visible_motifs
from arc_agi2.motif_context import solve_demonstrated_motifs
from arc_agi2.program_targets import audit_target, verify
from arc_agi2.runtime import BASE, call, grid, reference, verification_basis, verification_solver

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import history  # noqa: E402

TID = "98c475bf"
METHOD = "fixed-query-same-shape-context-line-motif-gate"
METHOD_VERSION = 1
QUERIES = 1000
MAX_CONTEXTS = 64
CROSS_WIDTH = 20
FIXTURE_PALETTES = (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5])
PINNED = {
    "adapter": HERE / "certify_98c475bf.py",
    "history_helper": HERE / "history.py",
    "constructor": BASE.parent / "tasks" / "task_98c475bf.py",
    "factory": BASE / "direct_factories" / "task_98c475bf.py",
    "gate_line_motif_evidence": BASE / "line_motif_evidence.py",
    "gate_dispatch_colour_evidence": BASE / "colour_evidence.py",
    "native_target_motif_context": BASE / "motif_context.py",
    "checker_dispatch_verified_rules": BASE / "verified_rules.py",
    "checker_archived_reference": BASE / "references" / "98c475bf.json",
    "program_targets": BASE / "program_targets.py",
    "augmentation": BASE / "augmentation.py",
    "runtime": BASE / "runtime.py",
    "helpers": BASE / "helpers.py",
    "prepare_input_orbit": BASE / "diversity" / "prepare.py",
    "direct_certificates_qualifies": BASE / "direct_certificates.py",
    "common": BASE.parent / "common.py",
}
COUNT_DEFINITIONS = {
    "fresh_pairs_checked": "fixed fresh default queries with verified labels (one pair each); "
                           "demonstrations are counted separately",
    "augmented_pair_checks": "query pairs verified exactly by the factory program under 8 D4 each",
    "augmented_demo_pair_checks": "demonstration pairs verified exactly by the factory under 8 D4 "
                                  "inside accepted episodes",
    "accepted_demo_pairs": "demonstrations in accepted contexts (3 per accepted query)",
    "context_retries": "contexts rejected before the accepted one, summed over queries",
    "rejected_context_draws": "all rejected contexts, by reason",
    "demo_pair_draws": "all demonstration pairs drawn, accepted or rejected",
    "pair_labels_verified": "every drawn pair (queries, all demonstrations in accepted and "
                            "rejected contexts, and cross-width control demonstrations) whose "
                            "label the archived verifier reproduced; any disagreement aborts",
    "unique_base_inputs": "distinct raw query inputs",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def seed_of(*parts):
    return int(sha(":".join(map(str, ("routing-motif-98c475bf",) + parts)).encode())[:12], 16)


def episode(pairs, d4, palette):
    four = [{k: transformed(p[k], d4, palette) for k in ("input", "output")} for p in pairs]
    return {"train": four[:-1], "test": [{"input": four[-1]["input"]}],
            "solutions": [four[-1]["output"]]}


class Harness:
    def __init__(self):
        self.module = importlib.import_module("tasks.task_" + TID)
        self.checker = verification_solver(TID)
        self.labels = 0

    def draw(self, **kw):
        p = call(self.module.generate, seconds=3, **kw)
        p = {k: grid(p[k]) for k in ("input", "output")}
        if grid(call(self.checker, p["input"])) != p["output"]:
            raise AssertionError("Archived verifier disagrees with constructor label")
        self.labels += 1
        return p


def gate_verdicts(demos, query, palette):
    """Gate on demonstrations and the query input only, for every D4."""
    verdicts, reasons = [], Counter()
    for d4 in range(8):
        ep = episode(demos + [query], d4, palette)
        try:
            require_colour_evidence(TID, ep["train"], ep["test"], palette, d4)
            verdicts.append(True)
        except MissingColourEvidence as exc:
            verdicts.append(False)
            reasons[str(exc)] += 1
    return verdicts, reasons


def soundness(demos, query, palette):
    """Checks after acceptance; any failure is a certificate failure."""
    for d4 in range(8):
        ep = episode(demos + [query], d4, palette)
        if solve_visible_motifs(ep["train"], ep["test"][0]["input"], palette[0]) != ep["solutions"][0]:
            raise AssertionError("Gate prediction disagrees with the label")
        src = factory.build_program(d4, palette)
        audit_target(TID, src)
        verify(src, ep, seconds=3)
    if solve_demonstrated_motifs(demos, query["input"]) != query["output"]:
        raise AssertionError("Native motif_context target disagrees with the label")


def audit_domain(query_kwargs, queries, tag, harness=None, cross_width=0):
    """Fixed-query compatible-context audit; returns a report dict."""
    h = harness or Harness()
    report = {"query_kwargs": query_kwargs, "queries_requested": queries, "queries_accepted": 0,
              "queries_failed": [], "max_contexts_per_query": MAX_CONTEXTS,
              "context_retries": 0, "context_retry_histogram": Counter(),
              "rejected_context_draws": Counter(), "gate_rejection_messages": Counter(),
              "sampler_rejections": [], "d4_inconsistent_contexts": 0,
              "demo_pair_draws": 0, "accepted_demo_pairs": 0,
              "augmented_pair_checks": 0, "augmented_demo_pair_checks": 0,
              "query_widths": Counter(), "query_heights": Counter(), "query_shapes": set(),
              "query_marker_counts": Counter(), "accepted_by_width": Counter(),
              "retries_by_width": Counter(), "native_target_checks": 0,
              "duplicate_query_orbits": 0}
    raw, orbits, episodes = set(), Counter(), set()
    cross = {"pairs": 0, "gate_refused": 0, "factory_raised": 0}
    for q in range(queries):
        random.seed(seed_of(tag, "query", q))
        query = h.draw(**query_kwargs)
        qh, qw = len(query["input"]), len(query["input"][0])
        qorbit = input_orbit(query["input"])
        raw.add(json.dumps(query["input"]))
        orbits[qorbit] += 1
        report["query_widths"][qw] += 1
        report["query_heights"][qh] += 1
        report["query_shapes"].add((qh, qw))
        markers = sum(1 for row in query["input"] if row[1] != 0 and row[1] == row[-2]
                      and all(v == 0 for v in row[2:-2]))
        report["query_marker_counts"][markers] += 1
        palette = list(range(10))
        random.Random(seed_of(tag, "palette", q)).shuffle(palette)
        accepted = None
        for attempt in range(MAX_CONTEXTS):
            random.seed(seed_of(tag, "context", q, attempt))
            try:
                demos = [h.draw(height=qh, width=qw) for _ in range(3)]
            except (ValueError, RuntimeError) as exc:
                report["sampler_rejections"].append({"query": q, "attempt": attempt, "error": repr(exc)})
                report["rejected_context_draws"]["sampler_exhausted"] += 1
                continue
            report["demo_pair_draws"] += 3
            ids = [input_orbit(d["input"]) for d in demos] + [qorbit]
            if len(set(ids)) != 4:
                report["rejected_context_draws"]["duplicate_identity"] += 1
                continue
            verdicts, reasons = gate_verdicts(demos, query, palette)
            if len(set(verdicts)) != 1:
                report["d4_inconsistent_contexts"] += 1
                raise AssertionError(f"Gate verdict depends on D4 for query {q}")
            if not verdicts[0]:
                report["rejected_context_draws"]["gate_missing_evidence"] += 1
                report["gate_rejection_messages"].update(reasons)
                continue
            accepted = (demos, attempt, ids)
            break
        if accepted is None:
            report["queries_failed"].append({"query": q, "seed": seed_of(tag, "query", q),
                                             "shape": [qh, qw]})
            continue
        demos, attempt, ids = accepted
        soundness(demos, query, palette)
        key = (ids[-1], tuple(sorted(ids[:3])))
        if key in episodes:
            raise AssertionError("Duplicate episode identity")
        episodes.add(key)
        report["native_target_checks"] += 1
        report["queries_accepted"] += 1
        report["context_retries"] += attempt
        report["context_retry_histogram"][attempt] += 1
        report["accepted_by_width"][qw] += 1
        report["retries_by_width"][qw] += attempt
        report["accepted_demo_pairs"] += 3
        report["augmented_pair_checks"] += 8
        report["augmented_demo_pair_checks"] += 24
        if q < cross_width:
            other = qw + 4 if qw + 4 <= h.module.MAX_WIDTH else qw - 4
            random.seed(seed_of(tag, "cross", q))
            wrong = [h.draw(height=qh, width=other) for _ in range(3)]
            cross["pairs"] += 1
            verdicts, _ = gate_verdicts(wrong, query, palette)
            cross["gate_refused"] += not any(verdicts)
            # The factory must refuse (raise), not merely answer wrongly.
            ep = episode(wrong + [query], 0, palette)
            namespace = {}
            exec(factory.build_program(0, palette), namespace)
            try:
                call(namespace["solve"], ep["train"], ep["test"][0]["input"], seconds=3)
            except ValueError:
                cross["factory_raised"] += 1
    report["unique_query_raw_inputs"] = len(raw)
    report["unique_query_orbits"] = len(orbits)
    report["duplicate_query_orbits"] = sum(n - 1 for n in orbits.values())
    report["distinct_episode_identities"] = len(episodes)
    report["query_shapes"] = len(report["query_shapes"])
    if cross_width:
        report["cross_width_negative_control"] = cross
    for k, v in list(report.items()):
        if isinstance(v, Counter):
            report[k] = {str(a): b for a, b in sorted(v.items(), key=lambda kv: str(kv[0]))}
    return report


def fixture_variants(harness):
    fixture = reference(TID)["canonical"]
    replay = harness.module.validate()
    if replay["train"] != fixture["train"] or replay["test"] != fixture["test"]:
        raise AssertionError("Original fixture replay changed")
    pairs = fixture["train"] + fixture["test"]
    for p in pairs:
        if grid(call(harness.checker, p["input"])) != p["output"]:
            raise AssertionError("Archived verifier disagrees with a canonical label")
    checked = 0
    for palette in FIXTURE_PALETTES:
        for d4 in range(8):
            ep = episode(pairs, d4, palette)
            require_colour_evidence(TID, ep["train"], ep["test"], palette, d4)
            if solve_visible_motifs(ep["train"], ep["test"][0]["input"], palette[0]) != ep["solutions"][0]:
                raise AssertionError("Gate prediction disagrees on a fixture variant")
            src = factory.build_program(d4, palette)
            audit_target(TID, src)
            verify(src, ep)
            checked += 1
    return checked


SCOPE = (
    "Default sampler of tasks/task_98c475bf.py: width 18..30 drawn per scene, height 12..30, "
    "fixed five-colour motif table at absolute x from the left border. Supported only for "
    "episodes whose demonstrations share the query's width (here: the query's full canvas "
    "shape, as prepare's uniform/seen policy requires) and demonstrate every query marker "
    "colour; the line_motif_evidence gate and the factory refuse other contexts. Novel-width "
    "or cross-width anchoring is not claimed.")
PROVENANCE = (
    "Measured fields written by the root-authorized dedicated adapter "
    "arc_agi2/reports/diversity-v1/native-routing-motif-20261025/certify_98c475bf.py "
    "(method fixed-query-same-shape-context-line-motif-gate v1; hashes in source_sha256). The "
    "standard arc_agi2.diversity.recertify harness fails for this family by construction; its "
    "real failure report is kept as standard-recertify-98c475bf.json in the same directory. "
    "provenance and draft_notes are carried verbatim from the record at 99def42.")


def certify(write=False):
    started = time.monotonic()
    harness = Harness()
    report = {
        "task_id": TID, "passed": False, "method": METHOD, "method_version": METHOD_VERSION,
        "constructor_sha256": sha(PINNED["constructor"].read_bytes()),
        "factory_sha256": sha(PINNED["factory"].read_bytes()),
        "factory_version": 1, "adapter_sha256": sha(PINNED["adapter"].read_bytes()),
        "source_sha256": {k: sha(p.read_bytes()) for k, p in PINNED.items()},
        "evidence_gate": "arc_agi2.colour_evidence.require_colour_evidence -> "
                         "arc_agi2.line_motif_evidence.require_line_motif_evidence",
        "pair_verifier": verification_basis(TID),
        "native_target": "arc_agi2.motif_context.solve_demonstrated_motifs (d4 = 0)",
        "requires_per_episode_verification": True,
        "count_definitions": COUNT_DEFINITIONS,
        "fresh_pairs_checked": 0, "augmented_pair_checks": 0, "fixture_variants_checked": 0,
        "sampler_rejections": [],
    }
    try:
        report["fixture_variants_checked"] = fixture_variants(harness)
        domain = audit_domain({}, QUERIES, "default", harness, cross_width=CROSS_WIDTH)
        report.update(domain)
        del report["query_kwargs"]
        report["pair_labels_verified"] = harness.labels
        report["fresh_pairs_checked"] = domain["queries_accepted"]
        report["unique_base_inputs"] = domain["unique_query_raw_inputs"]
        if domain["queries_failed"]:
            raise AssertionError("Queries exhausted the bounded context budget")
        cross = domain["cross_width_negative_control"]
        if cross["gate_refused"] != cross["pairs"] or cross["factory_raised"] != cross["pairs"]:
            raise AssertionError("A cross-width context was not refused")
        if report["fresh_pairs_checked"] < QUERIES or report["fixture_variants_checked"] != 16:
            raise AssertionError("Insufficient verified checks")
        report.update(passed=True, fixture_basis="canonical")
    except Exception as exc:  # noqa: BLE001 - recorded in the certificate
        report["error"] = repr(exc)
        report["pair_labels_verified"] = harness.labels
    report["seconds"] = round(time.monotonic() - started, 2)
    (HERE / "certificate-98c475bf.json").write_text(json.dumps(report, indent=2) + "\n")
    if write and report["passed"]:
        history.write_record(TID, history.merge(TID, report, SCOPE, PROVENANCE))
    return report


if __name__ == "__main__":
    r = certify(write="--write" in sys.argv)
    keep = ("passed", "error", "fresh_pairs_checked", "augmented_pair_checks",
            "augmented_demo_pair_checks", "fixture_variants_checked", "queries_failed",
            "context_retries", "rejected_context_draws", "unique_base_inputs",
            "pair_labels_verified", "cross_width_negative_control", "seconds")
    print(json.dumps({k: r.get(k) for k in keep}, indent=1))
