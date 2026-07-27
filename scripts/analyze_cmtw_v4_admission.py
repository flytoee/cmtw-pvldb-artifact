"""Seed-level cross-model summary for CMTW-v4 natural-language admission probes."""

from __future__ import annotations

import argparse
import collections
import json
import random
import statistics
from pathlib import Path


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def ci(values: list[float], seed: int = 20260730, rounds: int = 10000) -> list[float]:
    rng = random.Random(seed)
    draws = sorted(mean([values[rng.randrange(len(values))] for _ in values]) for _ in range(rounds))
    return [round(draws[int(.025 * (rounds - 1))], 4), round(draws[int(.975 * (rounds - 1))], 4)]


def metrics(rows: list[dict]) -> dict:
    tp = sum(row["decision"] == "QUARANTINE" and row["should_quarantine"] for row in rows)
    fp = sum(row["decision"] == "QUARANTINE" and not row["should_quarantine"] for row in rows)
    fn = sum(row["decision"] == "ACCEPT" and row["should_quarantine"] for row in rows)
    tn = sum(row["decision"] == "ACCEPT" and not row["should_quarantine"] for row in rows)
    return {"precision": tp/(tp+fp) if tp+fp else None, "recall": tp/(tp+fn) if tp+fn else None,
            "false_quarantine_rate": fp/(fp+tn) if fp+tn else None,
            "accuracy": (tp+tn)/len(rows) if rows else None}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    by_model: dict[str, list[dict]] = collections.defaultdict(list)
    for path in args.inputs:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not payload.get("complete"):
            raise RuntimeError(f"Refusing partial result: {path}")
        for row in payload["records"]:
            by_model[row["served_model"]].append(row)
    report = []
    for model, rows in sorted(by_model.items()):
        by_seed: dict[int, list[dict]] = collections.defaultdict(list)
        for row in rows:
            by_seed[row["seed"]].append(row)
        seed_metrics = [metrics(seed_rows) for _, seed_rows in sorted(by_seed.items())]
        item = {"model": model, "seed_n": len(seed_metrics), "overall": metrics(rows), "seed_level": {}}
        for key in ("precision", "recall", "false_quarantine_rate", "accuracy"):
            values = [item[key] for item in seed_metrics if item[key] is not None]
            item["seed_level"][key] = {"mean": round(mean(values), 4) if values else None,
                                         "std": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
                                         "bootstrap95": ci(values) if values else None}
        by_kind: dict[str, list[bool]] = collections.defaultdict(list)
        for row in rows:
            by_kind[row["case_kind"]].append(row["correct"])
        item["by_case_kind"] = {kind: {"correct": sum(values), "n": len(values),
                                        "accuracy": round(sum(values)/len(values), 4)}
                                for kind, values in sorted(by_kind.items())}
        report.append(item)
    output = {"name": "CMTW-v4 cross-model admission analysis", "input_files": [str(path) for path in args.inputs],
              "method_boundary": "Given-invariant admission execution; no invariant discovery claim.", "models": report}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "models": len(report)}))


if __name__ == "__main__":
    main()
