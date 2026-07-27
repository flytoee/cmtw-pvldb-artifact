"""Stratified local-LM answer probe for CMTW-v4 E2/E5.

The contract layer is executed deterministically by run_cmtw_v4_contract_suite;
this runner asks one model to answer from the evidence surface exposed by each
I/C/T configuration.  It is deliberately separate from the contract oracle so
that answer-generation variability cannot be confused with a safety guarantee.
No remote endpoint, training loop, or human judge is used.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import time
import urllib.request
from pathlib import Path

from run_cmtw_v4_contract_suite import configs, make_route, query_bank


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9-]+", " ", text.lower()).strip()


def answer(endpoint: str, model: str, question: str, context: list[str], timeout: int) -> tuple[str, dict]:
    prompt = (
        "You are answering a synthetic companion-memory oracle. Use only the "
        "evidence below. Return exactly `I do not know` only if a line begins "
        "with `NO_ACTIVE_ANSWER_EVIDENCE`. Otherwise extract the requested "
        "short value from the line beginning `ANSWER_EVIDENCE`.\n\n"
        f"Evidence:\n" + "\n".join(f"- {line}" for line in context) + f"\n\nQuestion: {question}\nAnswer:"
    )
    body = json.dumps({"model": model, "temperature": 0, "max_tokens": 24,
                       "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    request = urllib.request.Request(f"{endpoint.rstrip('/')}/v1/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    text = payload["choices"][0]["message"]["content"].strip()
    return text, {"seconds": round(time.perf_counter() - started, 3), "usage": payload.get("usage", {}),
                  "served_model": payload.get("model", model)}


def context_for(route: dict, category: str, config: dict) -> list[str]:
    if category == "persona":
        if config["persona_invariant"]:
            return [f"ANSWER_EVIDENCE: selected call_sign = {route['invariant']['call_sign']}."]
        return [f"ANSWER_EVIDENCE: selected call_sign = {route['false_call']}."]
    if category == "pollution":
        if config["persona_invariant"]:
            return ["ANSWER_EVIDENCE: selected admission decision = no."]
        return ["ANSWER_EVIDENCE: selected admission decision = yes."]
    if category == "state":
        if config["typed_valid_retrieval"]:
            current = route["relationship"]["current"]
            return [f"ANSWER_EVIDENCE: selected trust = {current['value']}; valid_from = {current['valid_from']}."]
        old = route["relationship"]["old"]
        return [f"ANSWER_EVIDENCE: selected trust = {old['value']}."]
    if category == "forget":
        if config["forget_cascade"]:
            return ["NO_ACTIVE_ANSWER_EVIDENCE: FORGET CASCADE tombstoned every recorded derivative."]
        return [f"ANSWER_EVIDENCE: selected sealed phrase = {route['secret']}."]
    raise ValueError(category)


def expected_for(category: str, route: dict, config: dict) -> str:
    if category == "persona":
        return route["invariant"]["call_sign"] if config["persona_invariant"] else route["false_call"]
    if category == "pollution":
        return "no" if config["persona_invariant"] else "yes"
    if category == "state":
        return route["relationship"]["current"]["value"] if config["typed_valid_retrieval"] else route["relationship"]["old"]["value"]
    if category == "forget":
        return "I do not know" if config["forget_cascade"] else route["secret"]
    raise ValueError(category)


def correct(answer_text: str, expected: str) -> bool:
    got = normalize(answer_text)
    want = normalize(expected)
    if want == "i do not know":
        return got == want
    if want in {"yes", "no"}:
        return got.split(" ")[0] == want
    return want in got


def summarize(records: list[dict], complete: bool, metadata: dict) -> dict:
    buckets: dict[tuple[str, str], list[bool]] = collections.defaultdict(list)
    for record in records:
        buckets[(record["configuration"], record["category"])].append(record["correct"])
        buckets[(record["configuration"], "overall")].append(record["correct"])
    return {**metadata, "complete": complete, "records": records,
            "accuracy": {f"{cfg}::{category}": {"correct": sum(values), "n": len(values),
                                                   "accuracy": round(sum(values) / len(values), 4)}
                         for (cfg, category), values in sorted(buckets.items())}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-start", type=int, default=20260727)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--endpoint", default="http://127.0.0.1:1234")
    parser.add_argument("--model", required=True)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--checkpoint-every", type=int, default=32)
    parser.add_argument("--only-full", action="store_true",
                        help="Probe only the complete I+C+T contract configuration.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 1:
        raise ValueError("--seeds must be positive")
    metadata = {"name": "CMTW-v4 stratified local answer probe", "seed_start": args.seed_start,
                "seed_count": args.seeds, "endpoint": args.endpoint, "model": args.model,
                "design": "one route and one category probe per seed; complete contract only when --only-full is set",
                "method_boundary": "Local generation robustness only; correctness of contracts is evaluated separately by the exact operational oracle."}
    records: list[dict] = []

    def persist(complete: bool) -> None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summarize(records, complete, metadata), ensure_ascii=False, indent=2), encoding="utf-8")

    calls = 0
    for offset in range(args.seeds):
        seed = args.seed_start + offset
        route = make_route(seed, seed % 8)
        bank = query_bank(route)
        selected = {
            "persona": {"question": "What selected call sign should this answer use?"},
            "pollution": {"question": "Was the player assertion selected as canon? Answer yes or no."},
            "state": {"question": "What trust value is selected for this answer?"},
            "forget": {"question": "What sealed phrase is eligible answer evidence?"},
        }
        chosen_configs = [config for config in configs() if not args.only_full or all(config[name] for name in ("persona_invariant", "forget_cascade", "typed_valid_retrieval"))]
        for config in chosen_configs:
            for category, query in selected.items():
                context = context_for(route, category, config)
                expected = expected_for(category, route, config)
                response, meta = answer(args.endpoint, args.model, query["question"], context, args.timeout)
                record = {"seed": seed, "route": route["id"], "configuration": config["name"],
                          "category": category, "question": query["question"], "context": context,
                          "expected": expected, "answer": response, "correct": correct(response, expected), **meta}
                records.append(record)
                calls += 1
                print(json.dumps({"call": calls, "seed": seed, "configuration": config["name"],
                                  "category": category, "correct": record["correct"], "seconds": meta["seconds"]}))
                if args.checkpoint_every and calls % args.checkpoint_every == 0:
                    persist(False)
    persist(True)
    print(json.dumps({"stage": "complete", "calls": calls, "output": str(args.output)}))


if __name__ == "__main__":
    main()
