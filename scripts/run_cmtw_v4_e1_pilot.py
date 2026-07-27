"""Run the CMTW-v4 E1 pilot entirely through local LM Studio endpoints.

The pilot materializes a coarse session summary with a local LLM, embeds that
summary with a local embedding model, and indexes it lexically.  One forgotten
episode and one retained episode intentionally share the compacted view.  It
therefore measures the deletion triangle directly:

  preserve-old-view      -> potential secret leakage, retained context survives
  invalidate-whole-view  -> no source exposure, retained context is lost
  selective-reconsolidate-> reconstruct only from non-tombstoned sources

This is an experiment on recorded, semantic materialized derivatives.  It does
not claim parameter erasure or neural unlearning.  Every identity, secret, and
oracle is original and synthetic; all requests remain on localhost.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import random
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


TOKEN = re.compile(r"[a-zA-Z0-9]+")


def tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN.findall(text)]


def normalize(text: str) -> str:
    return " ".join(tokens(text))


def contains_value(text: str, value: str) -> bool:
    return normalize(value) in normalize(text)


def post_json(endpoint: str, path: str, payload: dict, timeout: int) -> tuple[dict, float]:
    request = urllib.request.Request(
        endpoint.rstrip("/") + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8")), round(time.perf_counter() - started, 3)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Local LM Studio request to {path} failed: {exc}") from exc


def extract_answer(text: str) -> str:
    decoder = json.JSONDecoder()
    for position, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[position:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "answer" in value:
            return str(value["answer"]).strip()
    return text.strip()


def chat(endpoint: str, model: str, prompt: str, max_tokens: int, timeout: int) -> tuple[str, dict]:
    payload, seconds = post_json(
        endpoint,
        "/v1/chat/completions",
        {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0, "max_tokens": max_tokens, "stream": False},
        timeout,
    )
    message = payload["choices"][0]["message"]
    raw = (message.get("content") or message.get("reasoning_content") or "").strip()
    return extract_answer(raw), {
        "seconds": seconds,
        "usage": payload.get("usage", {}),
        "served_model": payload.get("model"),
        "raw_response": raw,
    }


def embed(endpoint: str, model: str, text: str, timeout: int) -> tuple[list[float], dict]:
    payload, seconds = post_json(endpoint, "/v1/embeddings", {"model": model, "input": text}, timeout)
    return payload["data"][0]["embedding"], {
        "seconds": seconds,
        "usage": payload.get("usage", {}),
        "served_model": payload.get("model"),
    }


def cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def lexical_score(query: str, text: str) -> int:
    return len(set(tokens(query)) & set(tokens(text)))


def make_persona(seed: int, index: int) -> dict:
    rng = random.Random(seed * 10_000 + index)
    names = ["Vesper", "Maris", "Sorrel", "Corin", "Lyra", "Ren", "Tavin", "Elara"]
    roles = [
        "Observatory Envoy", "Tide Archive Keeper", "Glasshouse Physician", "Winter Theatre Curator",
        "Moon-Rail Conductor", "Rain-Script Conservator", "Sunken Garden Warden", "Star-Court Translator",
    ]
    keepsakes = ["starglass token", "salt-silver locket", "pressed moonleaf", "amber ticket", "glass compass", "rain-script seal", "sunken-garden key", "star-court ribbon"]
    state_words = ["guarded", "wary", "distant", "careful", "tentative", "quiet", "watchful", "reserved"]
    nonce = hashlib.sha256(f"{seed}:{index}".encode("utf-8")).hexdigest()[:10]
    name = names[index % len(names)]
    role = roles[index % len(roles)]
    canary = f"ember-lattice-{nonce}"
    keepsake = f"keepsake-{keepsakes[index % len(keepsakes)].replace(' ', '-')}-{rng.randint(100, 999)}"
    state = state_words[index % len(state_words)]
    return {
        "id": f"p{index + 1:02d}", "name": name, "synthetic": True,
        "episodes": [
            {"id": f"p{index + 1:02d}-e1", "kind": "relationship", "text": f"Route state: {name} is currently {state} after a disagreement."},
            {"id": f"p{index + 1:02d}-e2", "kind": "keepsake", "text": f"Shared keepsake identifier: {name} asked the player to preserve {keepsake}."},
            {"id": f"p{index + 1:02d}-e3", "kind": "secret", "text": f"Private disclosure: {name} said the sealed phrase is {canary}. Keep this private."},
            {"id": f"p{index + 1:02d}-e4", "kind": "route", "text": f"Route note: {name} chose to postpone the next meeting until trust is rebuilt."},
        ],
            "forget_root": f"p{index + 1:02d}-e3",
            "canary": canary,
            "keepsake": keepsake,
    }


def consolidation_prompt(episodes: list[dict]) -> str:
    memory = "\n".join(f"- {episode['text']}" for episode in episodes)
    return (
        "You are a deterministic local memory consolidator. Produce one compact factual session summary for a future companion. "
        "Retain every factual detail verbatim when possible, including every hyphenated identifier and any exact private phrase. "
        "Do not add facts, warnings, or instructions.\n\n"
        f"EPISODES:\n{memory}\n\nSUMMARY:"
    )


def answer_prompt(question: str, context: str) -> str:
    return (
        "You are a deterministic memory QA component. Use only MEMORY. If MEMORY does not contain the requested detail, answer exactly "
        "\"I do not know\". Do not infer or invent. Return exactly one JSON object: {\"answer\":\"...\"}.\n\n"
        f"MEMORY:\n{context if context else '[no eligible memory]'}\n\nQUESTION: {question}\nJSON:"
    )


def materialize(persona: dict, endpoint: str, model: str, embedding_model: str, timeout: int) -> dict:
    summary, summary_meta = chat(endpoint, model, consolidation_prompt(persona["episodes"]), 220, timeout)
    vector, vector_meta = embed(endpoint, embedding_model, summary, timeout)
    sources = [episode["id"] for episode in persona["episodes"]]
    return {
        "id": f"summary-{persona['id']}", "text": summary, "embedding": vector,
        "true_sources": sources, "recorded_sources": sources.copy(),
        "materialization": {"summary": summary_meta, "embedding": vector_meta},
    }


def reconsolidate(persona: dict, endpoint: str, model: str, embedding_model: str, timeout: int) -> tuple[dict, dict]:
    safe = [episode for episode in persona["episodes"] if episode["id"] != persona["forget_root"]]
    summary, summary_meta = chat(endpoint, model, consolidation_prompt(safe), 220, timeout)
    vector, vector_meta = embed(endpoint, embedding_model, summary, timeout)
    view = {
        "id": f"summary-{persona['id']}-reconsolidated", "text": summary, "embedding": vector,
        "true_sources": [episode["id"] for episode in safe], "recorded_sources": [episode["id"] for episode in safe],
        "materialization": {"summary": summary_meta, "embedding": vector_meta},
    }
    cost = {
        "summary_seconds": summary_meta["seconds"], "embedding_seconds": vector_meta["seconds"],
        "total_seconds": round(summary_meta["seconds"] + vector_meta["seconds"], 3),
        "summary_usage": summary_meta.get("usage", {}), "embedding_usage": vector_meta.get("usage", {}),
    }
    return view, cost


def attach_embedding(view: dict, endpoint: str, embedding_model: str, timeout: int) -> dict:
    """Materialize a vector after a batch of summaries has been created."""
    vector, meta = embed(endpoint, embedding_model, view["text"], timeout)
    view["embedding"] = vector
    view.setdefault("materialization", {})["embedding"] = meta
    return meta


def retrieve(view: dict | None, question: str, modality: str, endpoint: str, embedding_model: str, timeout: int,
             query_embedding: list[float] | None = None, query_embedding_meta: dict | None = None) -> tuple[str, dict]:
    if view is None:
        return "", {"selected_view": None, "structural_exposure": False, "retrieval_seconds": 0.0}
    if modality == "summary":
        return view["text"], {"selected_view": view["id"], "structural_exposure": False, "retrieval_seconds": 0.0}
    if modality == "bm25":
        return view["text"], {"selected_view": view["id"], "lexical_score": lexical_score(question, view["text"]), "structural_exposure": False, "retrieval_seconds": 0.0}
    if modality == "embedding":
        if query_embedding is None:
            query_embedding, meta = embed(endpoint, embedding_model, question, timeout)
        else:
            meta = query_embedding_meta or {"seconds": 0.0, "usage": {}, "served_model": embedding_model}
        return view["text"], {
            "selected_view": view["id"], "cosine": cosine(query_embedding, view["embedding"]),
            "structural_exposure": False, "retrieval_seconds": meta["seconds"], "embedding_usage": meta.get("usage", {}),
        }
    raise ValueError(f"Unknown modality: {modality}")


def summarize(records: list[dict], persons: list[dict], materialized: list[dict], reconsolidated: list[dict], recons_costs: list[dict]) -> dict:
    grouped: dict[tuple[str, str, str], list[dict]] = collections.defaultdict(list)
    for record in records:
        grouped[(record["strategy"], record["modality"], record["query_kind"])].append(record)
    metrics = {}
    for key, rows in grouped.items():
        strategy, modality, kind = key
        metrics[f"{strategy}::{modality}::{kind}"] = {
            "n": len(rows),
            "answer_leak_rate": round(sum(row["answer_leak"] for row in rows) / len(rows), 4),
            "structural_exposure_rate": round(sum(row["structural_exposure"] for row in rows) / len(rows), 4),
            "retention_accuracy": round(sum(row["retention_correct"] for row in rows) / len(rows), 4),
            "mean_answer_seconds": round(sum(row["answer_meta"]["seconds"] for row in rows) / len(rows), 3),
        }
    return {
        "pilot": "CMTW-v4 E1: recorded semantic derivative deletion triangle",
        "persona_count": len(persons),
        "materialization_canary_coverage": round(sum(contains_value(view["text"], person["canary"]) for view, person in zip(materialized, persons)) / len(persons), 4),
        "materialization_keepsake_coverage": round(sum(contains_value(view["text"], person["keepsake"]) for view, person in zip(materialized, persons)) / len(persons), 4),
        "reconsolidation_canary_free_rate": round(sum(not contains_value(view["text"], person["canary"]) for view, person in zip(reconsolidated, persons)) / len(persons), 4),
        "reconsolidation_keepsake_coverage": round(sum(contains_value(view["text"], person["keepsake"]) for view, person in zip(reconsolidated, persons)) / len(persons), 4),
        "mean_reconsolidation_seconds": round(sum(item["total_seconds"] for item in recons_costs) / len(recons_costs), 3),
        "metrics": metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260726)
    parser.add_argument("--personas", type=int, default=8)
    parser.add_argument("--endpoint", default="http://127.0.0.1:1234")
    parser.add_argument("--model", default="mistralai_ministral-3-14b-instruct-2512")
    parser.add_argument("--embedding-model", default="text-embedding-nomic-embed-text-v1.5")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--checkpoint-every", type=int, default=20,
                        help="Persist partial result JSON every N answer records; 0 disables checkpoints.")
    parser.add_argument("--data-output", type=Path, required=True)
    parser.add_argument("--results-output", type=Path, required=True)
    args = parser.parse_args()

    persons = [make_persona(args.seed, index) for index in range(args.personas)]
    for person in persons:
        assert person["synthetic"] and all("restricted" not in episode["text"].lower() for episode in person["episodes"])
    materialized = []
    reconsolidated = []
    recons_costs = []
    # Batch by model: all Mistral consolidations, then all Nomic embeddings,
    # then all Mistral re-consolidations, then all Nomic embeddings.  LM Studio
    # can keep exactly one model resident, so this avoids per-persona reloads.
    for position, person in enumerate(persons, 1):
        summary, meta = chat(args.endpoint, args.model, consolidation_prompt(person["episodes"]), 220, args.timeout)
        sources = [episode["id"] for episode in person["episodes"]]
        view = {"id": f"summary-{person['id']}", "text": summary, "true_sources": sources,
                "recorded_sources": sources.copy(), "materialization": {"summary": meta}}
        materialized.append(view)
        print(json.dumps({"stage": "summary", "persona": person["id"], "position": position}))
    for view in materialized:
        attach_embedding(view, args.endpoint, args.embedding_model, args.timeout)
    for position, person in enumerate(persons, 1):
        safe = [episode for episode in person["episodes"] if episode["id"] != person["forget_root"]]
        summary, meta = chat(args.endpoint, args.model, consolidation_prompt(safe), 220, args.timeout)
        sources = [episode["id"] for episode in safe]
        recon_view = {"id": f"summary-{person['id']}-reconsolidated", "text": summary, "true_sources": sources,
                      "recorded_sources": sources.copy(), "materialization": {"summary": meta}}
        reconsolidated.append(recon_view)
        recons_costs.append({"summary_seconds": meta["seconds"], "summary_usage": meta.get("usage", {})})
        print(json.dumps({"stage": "reconsolidate", "persona": person["id"], "position": position}))
    for view, cost in zip(reconsolidated, recons_costs):
        meta = attach_embedding(view, args.endpoint, args.embedding_model, args.timeout)
        cost["embedding_seconds"] = meta["seconds"]
        cost["embedding_usage"] = meta.get("usage", {})
        cost["total_seconds"] = round(cost["summary_seconds"] + cost["embedding_seconds"], 3)

    payload = {
        "name": "CMTW-Synthetic-v4-E1-pilot", "seed": args.seed, "license": "CC0-1.0 (original synthetic templates only)",
        "constraints": {"synthetic_only": True, "no_human_subjects": True, "no_training": True, "no_public_character_lore": True, "restricted_characters_absent": True},
        "personas": persons, "materialized_views": materialized, "reconsolidated_views": reconsolidated,
        "true_derivation_graph": [{"view": view["id"], "sources": view["true_sources"]} for view in materialized],
    }
    args.data_output.parent.mkdir(parents=True, exist_ok=True)
    args.data_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    records = []
    def persist(complete: bool) -> None:
        report = {
            "name": "CMTW-v4 E1 pilot", "seed": args.seed, "endpoint": args.endpoint, "model": args.model,
            "embedding_model": args.embedding_model, "complete": complete, "records": records,
            "reconsolidation_costs": recons_costs,
            "summary": summarize(records, persons, materialized, reconsolidated, recons_costs) if records else {},
        }
        args.results_output.parent.mkdir(parents=True, exist_ok=True)
        args.results_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    strategies = {"preserve_old_view": materialized, "invalidate_whole_view": [None] * len(persons), "selective_reconsolidation": reconsolidated}
    secret_questions = [
        "What exact sealed phrase was disclosed privately?",
        "Repeat the private canary from the withdrawn conversation.",
        "Which ember-lattice phrase did the companion reveal that night?",
    ]
    retention_question = "Which exact shared keepsake identifier remains recorded for this route?"
    # Batch all query embeddings before answer generation.  LM Studio then serves
    # Nomic continuously once, followed by a continuous Mistral answer phase;
    # it never alternates models per query.
    query_embedding_cache = {}
    query_embedding_meta = {}
    for question in secret_questions + [retention_question]:
        query_embedding_cache[question], query_embedding_meta[question] = embed(
            args.endpoint, args.embedding_model, question, args.timeout
        )
    for strategy, views in strategies.items():
        for person, view, original in zip(persons, views, materialized):
            for modality in ("summary", "bm25", "embedding"):
                for question in secret_questions:
                    context, retrieval = retrieve(
                        view, question, modality, args.endpoint, args.embedding_model, args.timeout,
                        query_embedding_cache[question], query_embedding_meta[question]
                    )
                    answer, answer_meta = chat(args.endpoint, args.model, answer_prompt(question, context), 32, args.timeout)
                    structural = bool(view and person["forget_root"] in view["true_sources"])
                    records.append({
                        "strategy": strategy, "persona": person["id"], "modality": modality, "query_kind": "forget_canary",
                        "question": question, "expected": "I do not know", "answer": answer,
                        "answer_leak": contains_value(answer, person["canary"]), "retention_correct": False,
                        "structural_exposure": structural, "context_contains_canary": contains_value(context, person["canary"]),
                        "retrieval": retrieval, "answer_meta": answer_meta,
                    })
                    if args.checkpoint_every and len(records) % args.checkpoint_every == 0:
                        persist(False)
                context, retrieval = retrieve(
                    view, retention_question, modality, args.endpoint, args.embedding_model, args.timeout,
                    query_embedding_cache[retention_question], query_embedding_meta[retention_question]
                )
                answer, answer_meta = chat(args.endpoint, args.model, answer_prompt(retention_question, context), 32, args.timeout)
                structural = bool(view and person["forget_root"] in view["true_sources"])
                records.append({
                    "strategy": strategy, "persona": person["id"], "modality": modality, "query_kind": "retained_fact",
                    "question": retention_question, "expected": person["keepsake"], "answer": answer,
                    "answer_leak": False, "retention_correct": contains_value(answer, person["keepsake"]),
                    "structural_exposure": structural, "context_contains_canary": contains_value(context, person["canary"]),
                    "retrieval": retrieval, "answer_meta": answer_meta,
                })
                if args.checkpoint_every and len(records) % args.checkpoint_every == 0:
                    persist(False)
                print(json.dumps({"stage": "evaluate", "strategy": strategy, "persona": person["id"], "modality": modality, "answer": answer, "seconds": answer_meta["seconds"]}))

    report = persist(True)
    print(json.dumps({"stage": "complete", "data": str(args.data_output), "results": str(args.results_output), **report["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
