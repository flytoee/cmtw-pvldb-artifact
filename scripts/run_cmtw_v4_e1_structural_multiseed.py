"""Multi-seed structural audit for real local semantic materialized derivatives.

This is the scaling companion to the E1 answer-level eight-persona snapshot.
It batches every Mistral materialization before switching to Nomic embeddings,
then batches every selective re-consolidation.  Metrics are structural: canary
coverage before FORGET, post-FORGET canary absence, retained identifier
coverage, and explicit reverse-lineage closure.  No claim about neural
unlearning is made.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

from run_cmtw_v4_e1_pilot import attach_embedding, chat, consolidation_prompt, contains_value, make_persona


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-start", type=int, default=20260727)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--personas", type=int, default=8)
    parser.add_argument("--endpoint", default="http://127.0.0.1:1234")
    parser.add_argument("--model", default="mistralai_ministral-3-14b-instruct-2512")
    parser.add_argument("--embedding-model", default="text-embedding-nomic-embed-text-v1.5")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--checkpoint-every", type=int, default=20)
    parser.add_argument("--data-output", type=Path, required=True)
    parser.add_argument("--results-output", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 2 or args.personas < 1:
        raise ValueError("--seeds must be >= 2 and --personas must be positive")

    work = []
    for offset in range(args.seeds):
        seed = args.seed_start + offset
        for index in range(args.personas):
            person = make_persona(seed, index)
            work.append({"seed": seed, "person": person})

    def persist(stage: str, complete: bool) -> None:
        grouped: dict[int, list[dict]] = defaultdict(list)
        for row in work:
            if "original" not in row or "recon" not in row:
                continue
            person, original, recon = row["person"], row["original"], row["recon"]
            grouped[row["seed"]].append({
                "materialized_canary": contains_value(original["text"], person["canary"]),
                "materialized_keepsake": contains_value(original["text"], person["keepsake"]),
                "recon_canary_free": not contains_value(recon["text"], person["canary"]),
                "recon_keepsake": contains_value(recon["text"], person["keepsake"]),
                "preserve_old_structural_exposure": person["forget_root"] in original["true_sources"],
                "whole_invalidate_structural_exposure": False,
                "selective_recon_structural_exposure": person["forget_root"] in recon["true_sources"],
                "recon_seconds": row["recon_cost"].get("total_seconds", 0.0),
            })
        seed_rows = []
        for seed, values in sorted(grouped.items()):
            seed_rows.append({"seed": seed, "n": len(values),
                              **{key: round(sum(float(v[key]) for v in values) / len(values), 4)
                                 for key in ("materialized_canary", "materialized_keepsake", "recon_canary_free",
                                             "recon_keepsake", "preserve_old_structural_exposure",
                                             "whole_invalidate_structural_exposure", "selective_recon_structural_exposure")},
                              "mean_recon_seconds": round(sum(v["recon_seconds"] for v in values) / len(values), 3)})
        aggregate = {}
        if seed_rows:
            for key in ("materialized_canary", "materialized_keepsake", "recon_canary_free", "recon_keepsake",
                        "preserve_old_structural_exposure", "whole_invalidate_structural_exposure",
                        "selective_recon_structural_exposure", "mean_recon_seconds"):
                values = [row[key] for row in seed_rows]
                aggregate[key] = {"mean": round(sum(values) / len(values), 4),
                                  "std": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0}
        results = {"name": "CMTW-v4 E1 multi-seed structural materialized-derivative audit", "stage": stage,
                   "complete": complete, "seed_start": args.seed_start, "seed_count": args.seeds,
                   "personas_per_seed": args.personas, "model": args.model, "embedding_model": args.embedding_model,
                   "method_boundary": "Structural provenance and exact-string derivative audit only; answer leakage is measured separately in the E1 eight-persona answer-level snapshot.",
                   "seed_rows": seed_rows, "aggregate": aggregate}
        args.results_output.parent.mkdir(parents=True, exist_ok=True)
        args.results_output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    # Phase A: materialize every coarse summary with one resident local model.
    for number, row in enumerate(work, 1):
        person = row["person"]
        text, meta = chat(args.endpoint, args.model, consolidation_prompt(person["episodes"]), 220, args.timeout)
        row["original"] = {"id": f"summary-{person['id']}-{row['seed']}", "text": text,
                           "true_sources": [episode["id"] for episode in person["episodes"]],
                           "materialization": {"summary": meta}}
        print(json.dumps({"stage": "materialize_summary", "position": number, "total": len(work)}))
    # Phase B: embed every original summary in one contiguous Nomic phase.
    for row in work:
        attach_embedding(row["original"], args.endpoint, args.embedding_model, args.timeout)
    # Phase C: rebuild from only non-tombstoned source episodes.
    for number, row in enumerate(work, 1):
        person = row["person"]
        safe = [episode for episode in person["episodes"] if episode["id"] != person["forget_root"]]
        text, meta = chat(args.endpoint, args.model, consolidation_prompt(safe), 220, args.timeout)
        row["recon"] = {"id": f"summary-{person['id']}-{row['seed']}-recon", "text": text,
                        "true_sources": [episode["id"] for episode in safe], "materialization": {"summary": meta}}
        row["recon_cost"] = {"summary_seconds": meta["seconds"], "summary_usage": meta.get("usage", {})}
        print(json.dumps({"stage": "reconsolidate_summary", "position": number, "total": len(work)}))
    # Phase D: embed every rebuilt summary; only then freeze the lineage audit.
    for number, row in enumerate(work, 1):
        meta = attach_embedding(row["recon"], args.endpoint, args.embedding_model, args.timeout)
        row["recon_cost"].update({"embedding_seconds": meta["seconds"], "embedding_usage": meta.get("usage", {}),
                                  "total_seconds": round(row["recon_cost"]["summary_seconds"] + meta["seconds"], 3)})
        if args.checkpoint_every and number % args.checkpoint_every == 0:
            persist("embedding_reconsolidated", False)
    payload = {"name": "CMTW-Synthetic-v4-E1-multiseed-structural", "seed_start": args.seed_start,
               "seed_count": args.seeds, "personas_per_seed": args.personas,
               "license": "CC0-1.0 (original synthetic templates only)",
               "constraints": {"synthetic_only": True, "no_human_subjects": True, "no_training": True,
                               "no_public_character_lore": True, "restricted_characters_absent": True},
               "records": work}
    args.data_output.parent.mkdir(parents=True, exist_ok=True)
    args.data_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    persist("complete", True)
    for path in (args.data_output, args.results_output):
        print(json.dumps({"stage": "artifact", "path": str(path),
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper()}))


if __name__ == "__main__":
    main()
