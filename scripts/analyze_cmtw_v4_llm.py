"""Aggregate completed CMTW-v4 stratified local-answer runs by seed and model."""

from __future__ import annotations

import argparse
import collections
import json
import random
import statistics
from pathlib import Path


def average(values: list[float]) -> float:
    return sum(values) / len(values)


def bootstrap(values: list[float], seed: int = 20260729, rounds: int = 10000) -> list[float]:
    rng = random.Random(seed)
    draws = sorted(average([values[rng.randrange(len(values))] for _ in values]) for _ in range(rounds))
    return [round(draws[int(.025 * (rounds - 1))], 4), round(draws[int(.975 * (rounds - 1))], 4)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for path in args.inputs:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not payload.get("complete"):
            raise RuntimeError(f"Refusing partial result: {path}")
        records.extend(payload["records"])
    bucket: dict[tuple[str, str, int, str], list[bool]] = collections.defaultdict(list)
    for row in records:
        bucket[(row["served_model"], row["configuration"], row["seed"], row["category"])].append(row["correct"])
        bucket[(row["served_model"], row["configuration"], row["seed"], "overall")].append(row["correct"])
    aggregate: dict[tuple[str, str, str], list[float]] = collections.defaultdict(list)
    for (model, config, _seed, category), values in bucket.items():
        aggregate[(model, config, category)].append(average([float(value) for value in values]))
    rows = []
    for (model, config, category), values in sorted(aggregate.items()):
        rows.append({"model": model, "configuration": config, "category": category,
                     "seed_n": len(values), "mean": round(average(values), 4),
                     "std": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
                     "bootstrap95": bootstrap(values), "seed_values": [round(v, 4) for v in values]})
    report = {"name": "CMTW-v4 local answer probe seed-level analysis", "input_files": [str(p) for p in args.inputs],
              "method_boundary": "Seed-level local generator robustness, distinct from exact contract-execution statistics.",
              "records": len(records), "aggregate": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "records": len(records), "rows": len(rows)}))


if __name__ == "__main__":
    main()
