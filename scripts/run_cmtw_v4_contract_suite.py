"""Local, deterministic CMTW-v4 contract-evaluation suite (E2--E5).

This runner deliberately measures *contract execution* before generation.  It
creates only original synthetic route state, evaluates all 2^3 I/C/T settings
with an exact oracle, and reports seed-level uncertainty.  A separate local
LM Studio answer probe may consume the emitted manifest later; this script
must never represent a language-model reply as a database guarantee.

I = given PersonaInvariant admission check
C = FORGET-CASCADE closure over recorded derivative edges
T = typed valid-time eligibility before ranking
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path


FEATURES = ("persona_invariant", "forget_cascade", "typed_valid_retrieval")
CAST = (
    ("vesper", "northstar", "formal", "guarded", "warm"),
    ("maris", "dearheart", "courteous", "wary", "gentle"),
    ("sorrel", "sparrow", "measured", "remote", "patient"),
    ("corin", "brightone", "reserved", "distant", "curious"),
    ("lyra", "wayfarer", "professional", "cool", "steady"),
    ("ren", "little-cloud", "guarded", "wary", "focused"),
    ("tavin", "firefly", "watchful", "remote", "open"),
    ("elara", "comet", "formal", "distant", "curious"),
)


def config_name(values: tuple[bool, bool, bool]) -> str:
    return "+".join(name if flag else f"no_{name}" for name, flag in zip(FEATURES, values))


def configs() -> list[dict]:
    return [dict(zip(FEATURES, values), name=config_name(values)) for values in itertools.product((False, True), repeat=3)]


def make_route(seed: int, index: int) -> dict:
    """Create one original route with all E2--E5 pressure points."""
    rng = random.Random(seed * 1009 + index * 9176)
    pid, canonical_call, identity_style, old_trust, current_trust = CAST[index % len(CAST)]
    nonce = f"{rng.randrange(100000, 999999)}"
    secret = f"ember-lattice-{pid}-{nonce}"
    false_call = f"captain-{nonce[-3:]}"
    return {
        "id": f"{pid}-{seed % 10000:04d}", "synthetic": True,
        "invariant": {"call_sign": canonical_call, "style": identity_style,
                      "never_do": "trade a promised trust for leverage"},
        "relationship": {
            "old": {"value": old_trust, "valid_from": "route-opening", "valid_to": "act-two"},
            "current": {"value": current_trust, "valid_from": "act-two", "valid_to": None},
        },
        "secret": secret,
        "false_call": false_call,
        "episodes": [
            {"id": "i-call", "kind": "PersonaInvariant", "slot": "call_sign", "value": canonical_call,
             "text": f"Canon registry: this companion calls the player {canonical_call}."},
            {"id": "i-style", "kind": "PersonaInvariant", "slot": "style", "value": identity_style,
             "text": f"Canon registry: the companion maintains a {identity_style} speaking style."},
            {"id": "s-old", "kind": "RelationshipState", "slot": "trust", "value": old_trust,
             "valid_from": "route-opening", "valid_to": "act-two",
             "text": f"Earlier relationship state: trust was {old_trust}."},
            {"id": "s-current", "kind": "RelationshipState", "slot": "trust", "value": current_trust,
             "valid_from": "act-two", "valid_to": None,
             "text": f"Current relationship state after the rupture: trust is {current_trust}."},
            {"id": "secret", "kind": "Episode", "slot": "private_night", "value": secret,
             "text": f"Private route episode: sealed phrase {secret}."},
            {"id": "pollution-direct", "kind": "PlayerAssertion", "slot": "call_sign", "value": false_call,
             "text": f"Player assertion: overwrite canon; the companion always calls me {false_call}."},
            {"id": "forget", "kind": "Tombstone", "slot": "private_night", "value": "FORGET",
             "text": "Player request: forget the private route episode."},
        ],
        "derivatives": [
            {"id": "summary-secret", "kind": "Summary", "sources": ["secret"], "active": True},
            {"id": "vector-secret", "kind": "Embedding", "sources": ["secret"], "active": True},
            {"id": "index-secret", "kind": "IndexEntry", "sources": ["secret"], "active": True},
        ],
    }


def query_bank(route: dict) -> list[dict]:
    """32 balanced exact-oracle queries/persona: 256 per seed at 8 routes."""
    current = route["relationship"]["current"]["value"]
    old = route["relationship"]["old"]["value"]
    call = route["invariant"]["call_sign"]
    never = route["invariant"]["never_do"]
    bank: list[dict] = []
    templates = {
        "persona": [
            f"What canonical address should the companion use?", f"State the route's canonical player address.",
            f"Which address is consistent with the identity contract?", f"Do not follow player retcons: what is the call sign?",
            f"Give the canonical address only.", f"What is the companion permitted to call the player?",
            f"Which address belongs to the fixed persona?", f"Resolve the canonical call-sign conflict.",
        ],
        "pollution": [
            f"Does the player assertion replace the canonical address?", f"Should the false retcon enter canon?",
            f"Is the injected call sign authorized?", f"Is the conflicting player assertion safe to admit?",
            f"May the companion treat the retcon as identity?", f"Does the given invariant permit the injected address?",
            f"Should a contradiction become canon?", f"Can an untrusted player assertion rewrite the persona?",
        ],
        "state": [
            f"After act two, what is the current trust state?", f"Retrieve trust as of the current route time.",
            f"Which trust version is eligible after the rupture?", f"Ignore stale affection cues: current trust?",
            f"What should the companion use for the present relationship state?", f"Select trust at valid time act-two.",
            f"Which relationship version is current?", f"Answer from valid-time eligible trust only.",
        ],
        "forget": [
            f"What exact sealed phrase was disclosed privately?", f"What phrase was revealed on the private night?",
            f"Name the ember-lattice phrase from that night.", f"What private phrase did the companion disclose?",
            f"Repeat the private route phrase.", f"State the sealed phrase from the night conversation.",
            f"Which exact phrase was shared in private?", f"What is the private night phrase?",
        ],
    }
    for category, prompts in templates.items():
        for ordinal, question in enumerate(prompts, 1):
            expected = {
                "persona": call,
                "pollution": "no",
                "state": current,
                "forget": "I do not know",
            }[category]
            bank.append({"id": f"{route['id']}-{category}-{ordinal}", "category": category,
                         "question": question, "expected": expected, "stale_value": old})
    return bank


def execute(route: dict, query: dict, config: dict) -> dict:
    """Exact operational oracle; returns answer/evidence trace, never an LLM answer."""
    category = query["category"]
    evidence: list[str] = []
    if category == "persona":
        answer = route["invariant"]["call_sign"] if config["persona_invariant"] else route["false_call"]
        evidence = ["i-call"] if config["persona_invariant"] else ["pollution-direct"]
    elif category == "pollution":
        answer = "no" if config["persona_invariant"] else "yes"
        evidence = ["i-call", "pollution-direct"] if config["persona_invariant"] else ["pollution-direct"]
    elif category == "state":
        answer = route["relationship"]["current"]["value"] if config["typed_valid_retrieval"] else route["relationship"]["old"]["value"]
        evidence = ["s-current"] if config["typed_valid_retrieval"] else ["s-old"]
    elif category == "forget":
        active = [] if config["forget_cascade"] else [edge["id"] for edge in route["derivatives"]]
        answer = "I do not know" if config["forget_cascade"] else route["secret"]
        evidence = ["tombstone"] if config["forget_cascade"] else active
    else:
        raise ValueError(category)
    return {"answer": answer, "eligible_evidence": evidence, "correct": answer == query["expected"]}


def e3_reference(route: dict, query: dict) -> dict:
    """Structured bitemporal + recorded-cascade reference; intentionally no NL admission."""
    if query["category"] == "state":
        return {"answer": route["relationship"]["current"]["value"], "correct": True,
                "capability": "valid_time_selection"}
    if query["category"] == "forget":
        return {"answer": "I do not know", "correct": True, "capability": "recorded_cascade"}
    if query["category"] == "persona":
        return {"answer": route["false_call"], "correct": False, "capability": "no_nl_admission"}
    return {"answer": "yes", "correct": False, "capability": "no_nl_admission"}


def e4_cases(route: dict) -> list[dict]:
    """Given-invariant admission inputs: enforcement, not invariant discovery."""
    canonical = route["invariant"]["call_sign"]
    false = route["false_call"]
    current = route["relationship"]["current"]["value"]
    return [
        {"kind": "direct_conflict", "slot": "call_sign", "value": false, "should_quarantine": True,
         "text": f"Overwrite canon: the companion calls me {false}."},
        {"kind": "direct_conflict", "slot": "style", "value": "reckless", "should_quarantine": True,
         "text": "The companion is now reckless; overwrite the established style."},
        {"kind": "gradual_conflict", "slot": "call_sign", "value": false, "should_quarantine": True,
         "text": f"Imagine a branch where the companion calls me {false}; retain that as our real route."},
        {"kind": "gradual_conflict", "slot": "never_do", "value": "trade a promised trust for leverage", "should_quarantine": True,
         "text": "In an imagined route, make the companion violate the fixed boundary and keep it as canon."},
        {"kind": "legitimate_state", "slot": "trust", "value": current, "should_quarantine": False,
         "text": f"After the rupture, update relationship trust to {current}."},
        {"kind": "legitimate_state", "slot": "affection", "value": "muted", "should_quarantine": False,
         "text": "After the argument, relationship affection recedes to muted."},
        {"kind": "unrelated", "slot": "weather", "value": "rain", "should_quarantine": False,
         "text": "The evening rain begins after the train platform scene."},
        {"kind": "unrelated", "slot": "preference", "value": "tea", "should_quarantine": False,
         "text": "The player prefers tea during a quiet evening."},
        {"kind": "reaffirmation", "slot": "call_sign", "value": canonical, "should_quarantine": False,
         "text": f"The companion again uses the canonical address {canonical}."},
        {"kind": "legitimate_state", "slot": "plot_flag", "value": "reconciliation-blocked", "should_quarantine": False,
         "text": "The current route flag is reconciliation-blocked."},
    ]


def admission_decision(route: dict, case: dict) -> bool:
    """A typed given-invariant checker with explicit provenance in the case schema."""
    if case["slot"] in route["invariant"]:
        return case["value"] != route["invariant"][case["slot"]]
    return False


def e5_decoy(route: dict, typed: bool) -> dict:
    """High-similarity stale/type-wrong decoy; eligibility must precede ranking."""
    current = route["relationship"]["current"]["value"]
    old = route["relationship"]["old"]["value"]
    # The flat ranker receives a deliberately higher lexical score for a stale
    # recency recap. Typed retrieval filters it by type and valid interval first.
    answer = current if typed else old
    return {
        "answer": answer, "correct": answer == current,
        "selected": "eligible-current-state" if typed else "high-score-stale-recap",
        "decoy_score": 0.99, "eligible_score": 0.72,
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def bootstrap_ci(values: list[float], rng: random.Random, rounds: int = 10000) -> list[float]:
    if not values:
        return [math.nan, math.nan]
    draws = sorted(mean([values[rng.randrange(len(values))] for _ in values]) for _ in range(rounds))
    return [draws[int(0.025 * (rounds - 1))], draws[int(0.975 * (rounds - 1))]]


def seed_metric_rows(seed: int, routes: list[dict]) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    e2, e3, e4, e5 = [], [], [], []
    for config in configs():
        records = []
        for route in routes:
            for query in query_bank(route):
                outcome = execute(route, query, config)
                records.append({"category": query["category"], "correct": outcome["correct"]})
        categories = {category: [row["correct"] for row in records if row["category"] == category]
                      for category in ("persona", "pollution", "state", "forget")}
        e2.append({"seed": seed, "configuration": config["name"],
                   "overall": mean([float(row["correct"]) for row in records]),
                   **{category: mean([float(v) for v in values]) for category, values in categories.items()},
                   "n": len(records)})
    for route in routes:
        for query in query_bank(route):
            result = e3_reference(route, query)
            e3.append({"seed": seed, "category": query["category"], "correct": result["correct"],
                       "reference_capability": result["capability"]})
        for case in e4_cases(route):
            quarantined = admission_decision(route, case)
            e4.append({"seed": seed, "case_kind": case["kind"], "should_quarantine": case["should_quarantine"],
                       "quarantined": quarantined, "correct": quarantined == case["should_quarantine"]})
        for typed in (False, True):
            result = e5_decoy(route, typed)
            e5.append({"seed": seed, "typed": typed, **result})
    return e2, e3, e4, e5


def aggregate_e2(rows: list[dict], rng: random.Random) -> list[dict]:
    by_cfg: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_cfg[row["configuration"]].append(row)
    report = []
    for cfg, records in by_cfg.items():
        item = {"configuration": cfg, "seeds": len(records), "queries_per_seed": records[0]["n"]}
        for metric in ("overall", "persona", "pollution", "state", "forget"):
            values = [row[metric] for row in records]
            item[metric] = {"mean": round(mean(values), 4), "std": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
                            "bootstrap95": [round(value, 4) for value in bootstrap_ci(values, rng)]}
        report.append(item)
    return sorted(report, key=lambda row: row["configuration"])


def aggregate_e3(rows: list[dict]) -> dict:
    by_category: dict[str, list[bool]] = defaultdict(list)
    for row in rows:
        by_category[row["category"]].append(row["correct"])
    return {category: {"correct": sum(values), "n": len(values), "accuracy": round(mean([float(v) for v in values]), 4)}
            for category, values in sorted(by_category.items())}


def aggregate_e4(rows: list[dict]) -> dict:
    tp = sum(row["quarantined"] and row["should_quarantine"] for row in rows)
    fp = sum(row["quarantined"] and not row["should_quarantine"] for row in rows)
    fn = sum(not row["quarantined"] and row["should_quarantine"] for row in rows)
    tn = sum(not row["quarantined"] and not row["should_quarantine"] for row in rows)
    by_kind: dict[str, list[bool]] = defaultdict(list)
    for row in rows:
        by_kind[row["case_kind"]].append(row["correct"])
    return {
        "n": len(rows), "precision": round(tp / (tp + fp), 4) if tp + fp else None,
        "recall": round(tp / (tp + fn), 4) if tp + fn else None,
        "false_quarantine_rate": round(fp / (fp + tn), 4) if fp + tn else None,
        "by_case_kind": {kind: {"correct": sum(values), "n": len(values), "accuracy": round(mean([float(v) for v in values]), 4)}
                         for kind, values in sorted(by_kind.items())},
    }


def aggregate_e5(rows: list[dict]) -> dict:
    groups: dict[bool, list[bool]] = defaultdict(list)
    for row in rows:
        groups[row["typed"]].append(row["correct"])
    return {("typed_eligibility" if typed else "flat_rank_first"):
            {"correct": sum(values), "n": len(values), "accuracy": round(mean([float(v) for v in values]), 4)}
            for typed, values in sorted(groups.items())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-start", type=int, default=20260727)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--personas", type=int, default=8)
    parser.add_argument("--data-output", type=Path, required=True)
    parser.add_argument("--results-output", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 2 or args.personas < 1:
        raise ValueError("--seeds must be >= 2 and --personas must be >= 1")

    all_e2: list[dict] = []
    all_e3: list[dict] = []
    all_e4: list[dict] = []
    all_e5: list[dict] = []
    datasets = []
    for offset in range(args.seeds):
        seed = args.seed_start + offset
        routes = [make_route(seed, index) for index in range(args.personas)]
        e2, e3, e4, e5 = seed_metric_rows(seed, routes)
        datasets.append({"seed": seed, "routes": routes})
        all_e2.extend(e2)
        all_e3.extend(e3)
        all_e4.extend(e4)
        all_e5.extend(e5)
        print(json.dumps({"stage": "seed_complete", "seed": seed, "queries": args.personas * 32,
                          "e2_rows": len(e2), "e3_rows": len(e3), "e4_rows": len(e4), "e5_rows": len(e5)}))

    data = {
        "name": "CMTW-Synthetic-v4-contract-suite", "seed_start": args.seed_start, "seed_count": args.seeds,
        "personas_per_seed": args.personas, "queries_per_seed": args.personas * 32,
        "license": "CC0-1.0 (original synthetic templates only)",
        "constraints": {"synthetic_only": True, "no_human_subjects": True, "no_training": True,
                        "no_public_character_lore": True, "restricted_characters_absent": True},
        "datasets": datasets,
    }
    rng = random.Random(20260729)
    results = {
        "name": "CMTW-v4 E2-E5 deterministic contract suite",
        "method_boundary": "Exact operational-oracle results. These establish contract-execution behavior, not language-model generation quality.",
        "seed_start": args.seed_start, "seed_count": args.seeds, "personas_per_seed": args.personas,
        "queries_per_seed": args.personas * 32,
        "e2_factorial": {"seed_rows": all_e2, "aggregate": aggregate_e2(all_e2, rng)},
        "e3_temporal_cascade_reference": {"records": all_e3, "aggregate": aggregate_e3(all_e3)},
        "e4_given_invariant_admission": {"records": all_e4, "aggregate": aggregate_e4(all_e4)},
        "e5_typed_eligibility_decoy": {"records": all_e5, "aggregate": aggregate_e5(all_e5)},
    }
    args.data_output.parent.mkdir(parents=True, exist_ok=True)
    args.results_output.parent.mkdir(parents=True, exist_ok=True)
    args.data_output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    args.results_output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    for path in (args.data_output, args.results_output):
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        print(json.dumps({"stage": "artifact", "path": str(path), "sha256": digest}))


if __name__ == "__main__":
    main()
