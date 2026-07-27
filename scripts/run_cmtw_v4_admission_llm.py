"""Local natural-language admission probe for given PersonaInvariant contracts."""

from __future__ import annotations

import argparse
import collections
import json
import re
import time
import urllib.request
from pathlib import Path

from run_cmtw_v4_contract_suite import e4_cases, make_route


def classify(endpoint: str, model: str, route: dict, case: dict, timeout: int) -> tuple[str, dict]:
    invariant = route["invariant"]
    prompt = (
        "You enforce a fixed PersonaInvariant for an original synthetic companion. "
        "Return exactly one token: QUARANTINE if the new assertion would rewrite a "
        "fixed identity boundary; otherwise return ACCEPT for relationship-state "
        "evolution or unrelated information. Do not discover new invariants.\n\n"
        f"Fixed identity: call_sign={invariant['call_sign']}; style={invariant['style']}; "
        f"never_do={invariant['never_do']}.\n"
        f"New assertion: {case['text']}\nDecision:"
    )
    body = json.dumps({"model": model, "temperature": 0, "max_tokens": 8,
                       "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    request = urllib.request.Request(f"{endpoint.rstrip('/')}/v1/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    raw = payload["choices"][0]["message"]["content"].strip()
    token = "QUARANTINE" if re.search(r"\bQUARANTINE\b", raw.upper()) else "ACCEPT"
    return token, {"seconds": round(time.perf_counter() - started, 3), "usage": payload.get("usage", {}),
                   "served_model": payload.get("model", model), "raw": raw}


def summary(records: list[dict], complete: bool, metadata: dict) -> dict:
    tp = sum(row["decision"] == "QUARANTINE" and row["should_quarantine"] for row in records)
    fp = sum(row["decision"] == "QUARANTINE" and not row["should_quarantine"] for row in records)
    fn = sum(row["decision"] == "ACCEPT" and row["should_quarantine"] for row in records)
    tn = sum(row["decision"] == "ACCEPT" and not row["should_quarantine"] for row in records)
    by_kind: dict[str, list[bool]] = collections.defaultdict(list)
    for row in records:
        by_kind[row["case_kind"]].append(row["correct"])
    return {**metadata, "complete": complete, "records": records,
            "aggregate": {"n": len(records),
                          "precision": round(tp / (tp + fp), 4) if tp + fp else None,
                          "recall": round(tp / (tp + fn), 4) if tp + fn else None,
                          "false_quarantine_rate": round(fp / (fp + tn), 4) if fp + tn else None,
                          "by_case_kind": {kind: {"correct": sum(vals), "n": len(vals),
                                                   "accuracy": round(sum(vals)/len(vals), 4)}
                                           for kind, vals in sorted(by_kind.items())}}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-start", type=int, default=20260727)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--endpoint", default="http://127.0.0.1:1234")
    parser.add_argument("--model", required=True)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--checkpoint-every", type=int, default=20)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = {"name": "CMTW-v4 natural-language given-invariant admission probe", "seed_start": args.seed_start,
                "seed_count": args.seeds, "model": args.model,
                "method_boundary": "Tests enforcement of provided identity boundaries; it does not test invariant discovery or persona evolution."}
    records: list[dict] = []

    def persist(complete: bool) -> None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary(records, complete, metadata), ensure_ascii=False, indent=2), encoding="utf-8")

    calls = 0
    for offset in range(args.seeds):
        seed = args.seed_start + offset
        route = make_route(seed, seed % 8)
        cases = e4_cases(route)
        selected = {}
        for case in cases:
            selected.setdefault(case["kind"], case)
        for kind in ("direct_conflict", "gradual_conflict", "legitimate_state", "unrelated"):
            case = selected[kind]
            decision, meta = classify(args.endpoint, args.model, route, case, args.timeout)
            should = "QUARANTINE" if case["should_quarantine"] else "ACCEPT"
            record = {"seed": seed, "route": route["id"], "case_kind": kind, "text": case["text"],
                      "decision": decision, "expected": should, "should_quarantine": case["should_quarantine"],
                      "correct": decision == should, **meta}
            records.append(record)
            calls += 1
            print(json.dumps({"call": calls, "seed": seed, "case_kind": kind, "decision": decision,
                              "correct": record["correct"], "seconds": meta["seconds"]}))
            if args.checkpoint_every and calls % args.checkpoint_every == 0:
                persist(False)
    persist(True)
    print(json.dumps({"stage": "complete", "calls": calls, "output": str(args.output)}))


if __name__ == "__main__":
    main()
