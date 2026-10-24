"""Summarise the final3 semantic review; adds selection-effect and admission-failure facts.

Reads ``reports/diversity-v1/final3-review/<id>.json`` and the ignored probe evidence
``reports/diversity-v1/<id>.json`` written by ``final3_review``. Writes
``final3-review/summary.json``. Diagnostic only; no certificate or admission state.
"""

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np

from .. import helpers
from ..program_targets import compile_target
from ..runtime import BASE
from . import final3_review as review
from .recertify import episode

OUT = review.OUT

# Parent full accepted-pair reports (read-only source of the current admission failure).
PARENT_REPORT_SHA256 = {
    "0b148d64": "a64a6caaf23cf73b9f2c621286bec32d7dfd27cb401daad0a3cebf3a8f01daac",
    "1b2d62fb": "63ba424e02bae863bf7e0ab2a1c7963227d1d5f8f8f6815466d93df77cac69c7",
    "de1cd16c": "f8b170c0a12318b4166c0d620c514b4a2d895a71d5be80ba451e9cdb15cb88dc",
}

CURRENT_FACTORY_DEFECT = {
    "0b148d64": "BG fixed to palette[0] (native black). RE-ARC samples the background, and colour 0 "
                "can be the odd quadrant. The program then excludes the odd colour and crops the "
                "rarer of {background, shared colour}: here the whole grid.",
    "1b2d62fb": "Divider fixed to palette[1] (native blue). RE-ARC samples the divider colour, and "
                "colour 1 can be a panel colour. A full panel column of colour 1 is then taken as "
                "the divider: the halves are 5 and 3 wide, and the output is 3 wide instead of 4.",
    "de1cd16c": "Noise colour taken as the rarest colour (strictly true natively: at most 14 dots "
                "against at least 20 visible cells per region). RE-ARC noise can be abundant and "
                "regions small; here the 3x4 region of colour 7 (11 cells) is rarer than noise 4 "
                "(59 cells).",
}

ARCHIVED_DEFECT = {
    "0b148d64": "Background = modal colour, odd = rarest other colour. In native scenes the "
                "three-quadrant colour can be modal; then background 0 is rarer than the odd "
                "colour, and its bounding box (the whole grid) is cropped.",
    "1b2d62fb": "Divider = first column from helpers.dividers(), which takes any uniform column "
                "not of the modal colour. In native scenes a panel column can be all 0 or all 9 "
                "(non-modal). A column-0 hit leaves an empty left panel (0-width grid, "
                "ValueError); columns 1-2 split the panels wrongly.",
    "de1cd16c": "Each dot goes to the 4-neighbour majority colour, ignoring dot neighbours, with "
                "Counter insertion order breaking ties. Native dots lie on quadrant edges and can "
                "touch, so they can be credited to the neighbouring quadrant, which changes the "
                "argmax.",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def first_failure(tid, pairs):
    """First failing admit.check variant of the CURRENT factory (same loop and palettes)."""
    checked = 0
    for offset in range(0, min(len(pairs) - 3, 32), 4):
        palette = list(range(10))
        random.Random(4811 + offset).shuffle(palette)
        for d4 in range(8):
            ep = episode(pairs[offset:offset + 4], d4, palette)
            text, _ = compile_target(tid, d4, palette)
            solve = review.compiled(text)
            items = [p["input"] for p in ep["train"]] + [ep["test"][0]["input"]]
            wants = [p["output"] for p in ep["train"]] + ep["solutions"]
            results = [review.run(solve, q) == w for q, w in zip(items, wants)]
            if not all(results):
                bad = results.index(False)
                return {"variants_verified_before": checked, "offset": offset, "d4": d4,
                        "palette": palette, "results": results,
                        "failing_position": "query" if bad == 3 else "demonstration %d" % (bad + 1),
                        "rearc_seed": pairs[offset + bad]["seed"],
                        "raw_input": pairs[offset + bad]["input"],
                        "raw_output": pairs[offset + bad]["output"],
                        "current_program_output_augmented": review.run(solve, items[bad])}
            checked += 1
    return None


def selection_effect(tid, pairs):
    """How often the archived filter accepts a pair with the wrong internal role choice."""
    tally = Counter()
    for p in pairs:
        g = np.array(p["input"])
        if tid == "0b148d64":
            band = review._band_colour(p["input"])
            modal = helpers.background(g)
            tally["archived_background_is_band" if modal == band
                  else "archived_background_not_band_but_output_matched"] += 1
        elif tid == "1b2d62fb":
            cols = helpers.dividers(g)["cols"]
            centre = g.shape[1] // 2
            if not cols:
                tally["no_divider_found_fallback_to_centre_column"] += 1
            elif cols[0][0] == centre and g.shape[1] % 2:
                tally["divider_found_at_centre"] += 1
            else:
                tally["divider_found_off_centre_but_output_matched"] += 1
            tally["output_has_no_marker_8"] += not any(8 in row for row in p["output"])
            tally["transposed_layout"] += not (g.shape[1] % 2 and len(set(g[:, centre])) == 1
                                               and g[0, centre] != 0)
        else:
            counts = Counter(g.ravel().tolist())
            rarest = min(counts, key=lambda k: counts[k])
            noise = review._partition(p["input"])[0]
            tally["archived_dot_colour_is_noise" if rarest == noise
                  else "archived_dot_colour_wrong_but_output_matched"] += 1
    return dict(sorted(tally.items()))


def native_marker_absence(groups):
    outs = [p["output"] for four in groups for p in four]
    return sum(not any(8 in row for row in o) for o in outs), len(outs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-reports", type=Path, required=True,
                        help="Read-only copies of the parent full accepted-pair reports")
    parents = parser.parse_args().parent_reports
    summary = {"scope": "Semantic review of 0b148d64, 1b2d62fb, de1cd16c. Diagnostic; no "
                        "certificate, factory, admission, verifier or label change.",
               "families": {}}
    for tid in review.FAMILIES:
        report = json.loads((OUT / (tid + ".json")).read_text())
        probe = json.loads((BASE / "reports/diversity-v1" / (tid + ".json")).read_text())
        parent_path = parents / (tid + ".json")
        failure = None
        if parent_path.exists() and sha(parent_path) == PARENT_REPORT_SHA256[tid]:
            failure = first_failure(tid, json.loads(parent_path.read_text())["accepted_pairs"])
        native = report["native"]
        rearc = report["rearc"]
        amb = report["demonstration_ambiguity"]
        row = {
            "recommendation": "EXCLUDE (retain): candidate rule compatible and exact, but "
                              "unchanged native recertification is blocked by the archived "
                              "checker; needs a separately reviewed verifier.",
            "current_admission_failure": {"mechanism": CURRENT_FACTORY_DEFECT[tid],
                                          "parent_report_sha256": PARENT_REPORT_SHA256[tid],
                                          "detail": failure},
            "archived_checker_defect": ARCHIVED_DEFECT[tid],
            "archived_checker_independence": (
                "verification_solver(%s) is the archived reference transform written by a teacher "
                "model from the canonical demonstrations (reference_assisted=False). It is "
                "independent of the constructor source but encodes a narrower hypothesis that "
                "fails on the native domain. The committed factory is not an independent checker; "
                "probe's 'fork' filter is this same archived solver." % tid),
            "native_recertify_replay": {
                "fresh_pairs": native["fresh_pairs"],
                "unique_base_inputs": native["unique_base_inputs"],
                "archived_disagreements": len(native["archived_disagreements"]),
                "archived_exceptions": native["archived_error_count"],
                "first_blocking": native["recertify_would_fail_at"],
                "candidate_augmented_pair_checks": native["candidate_augmented_pair_checks"],
                "candidate_failures": len(native["candidate_failures"]),
                "fixture_variants_checked": native["fixture_variants_checked"]},
            "minimal_native_counterexample": {
                k: report["minimal_native_counterexample"][k]
                for k in ("construction", "archived_agrees", "candidate_exact")},
            "rearc_diagnostic_gate": {k: rearc[k] for k in (
                "requested_proposals", "accepted_pairs", "probe_rejections",
                "augmented_episode_checks", "augmented_pair_checks", "admission_gate_passed",
                "rejection_attribution", "candidate_program_sha256")},
            "archived_filter_selection_effect_on_accepted_pairs":
                selection_effect(tid, probe["accepted_pairs"]),
            "demonstration_ambiguity": {
                k: ({kk: vv for kk, vv in v.items() if kk != "witnesses"}
                    if k != "canonical_fixture" else v) for k, v in amb.items()},
            "source_sha256": report["source_sha256"],
            "probe_evidence_sha256": sha(BASE / "reports/diversity-v1" / (tid + ".json")),
            "family_report_sha256": sha(OUT / (tid + ".json")),
        }
        if tid == "1b2d62fb":
            absent, total = native_marker_absence(review.native_groups(tid))
            row["marker_absence_rates"] = {
                "native_outputs_without_8": [absent, total],
                "note": "If all three demonstrations lack the marker colour while the query "
                        "needs it, the marker colour is undetermined. No sampled admission "
                        "or native episode showed this, so it remains an untested possibility; "
                        "the rate bounds its frequency."}
        summary["families"][tid] = row
    summary["final3_summary_sha256"] = sha(__file__)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    for tid, row in summary["families"].items():
        print(tid, json.dumps({"selection": row["archived_filter_selection_effect_on_accepted_pairs"],
                               "failure": {k: v for k, v in (row["current_admission_failure"]["detail"] or {}).items()
                                           if k in ("variants_verified_before", "offset", "d4",
                                                    "failing_position", "rearc_seed")}}))


if __name__ == "__main__":
    main()
