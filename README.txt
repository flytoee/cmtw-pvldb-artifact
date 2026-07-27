CMTW v4 — PVLDB supplemental artifact
=======================================

Purpose
-------
This bundle contains the accepted synthetic inputs, raw JSON results, exact
contract evaluators, local-LM probe runners, analysis scripts, and figure source
tables used by:

  CMTW: Persona-Invariant Integrity and Verifiable Forgetting for
  Companion Memory [Vision]

The artifact is an evidence package, not a new experimental run.  It contains
only original synthetic personas.  No human subjects, cloud API, training,
CUDA/A40/multi-GPU execution, or third-party character data are used.

Claim boundary
--------------
The deterministic oracle checks:

  1. supplied PersonaInvariant admission decisions;
  2. typed valid-time eligibility before ranking;
  3. FORGET-CASCADE closure over recorded derivative edges; and
  4. replayable evidence selection at the answer boundary.

It does not claim neural unlearning, parameter erasure, or discovery/evolution
of PersonaInvariants.  The 2^3 result is a contract-completeness audit: I, C,
and T govern distinct obligations, so their obligation-coverage effects are
additive.  The constructed stale-decoy trace is an existence proof for applying
eligibility before ranking, not a population estimate.

Directory map
-------------
data/
  Accepted synthetic manifests used by the paper.

results/
  Accepted raw and aggregate JSON results.  Failed pilots, partial checkpoints,
  stdout/stderr logs, and excluded development runs are intentionally omitted.

scripts/
  Deterministic contract runner, local LM Studio runners, analysis scripts, and
  figure-generation scripts.

figure-source-data/
  CSV tables behind Figures 3–5.  Versioned intermediate CSVs are retained so
  the final adopted visual encodings can be audited against earlier exports.

docs/
  Pre-registration, feasibility audit, terminology/figure contracts, status,
  and the command-level reproducibility log.

Environment
-----------
Deterministic contract generation and evaluation use Python's standard library.
The figure scripts additionally require numpy and matplotlib.  Local generation
uses the OpenAI-compatible LM Studio endpoint:

  http://127.0.0.1:1234

Exact local model identifiers recorded in the accepted runs:

  mistralai_ministral-3-14b-instruct-2512
  liquid/lfm2-24b-a2b
  llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b
  text-embedding-nomic-embed-text-v1.5

The manuscript uses the neutral label "Llama MoE"; the exact served identifier
is retained here solely for reproducibility.

Minimal deterministic reproduction
----------------------------------
From the artifact root:

  python scripts/run_cmtw_v4_contract_suite.py ^
    --seed-start 20260727 --seeds 20 --personas 8 ^
    --data-output reproduced/cmtw_v4_contract_suite_20seeds_r2.json ^
    --results-output reproduced/e2_e5_contract_suite_20seeds_r2.json

This command performs no model call.  Compare the generated files with:

  data/cmtw_v4_contract_suite_20seeds_r2.json
  results/e2_e5_contract_suite_20seeds_r2.json

Local materialization and embedding reproduction
------------------------------------------------
Start LM Studio at 127.0.0.1:1234 with the recorded Mistral and Nomic models,
then run one request at a time:

  python scripts/run_cmtw_v4_e1_structural_multiseed.py ^
    --seed-start 20260727 --seeds 20 --personas 8 ^
    --endpoint http://127.0.0.1:1234 ^
    --model mistralai_ministral-3-14b-instruct-2512 ^
    --embedding-model text-embedding-nomic-embed-text-v1.5 ^
    --timeout 180 --checkpoint-every 20 ^
    --data-output reproduced/cmtw_v4_e1_structural_20seeds_r1.json ^
    --results-output reproduced/e1_structural_20seeds_mistral_r1.json

Local admission and answer probes
---------------------------------
The exact commands and fixed seeds for all three generators are recorded in:

  docs/reproducibility-log-v4.txt

The probe runners are:

  scripts/run_cmtw_v4_admission_llm.py
  scripts/run_cmtw_v4_llm_stratified.py

Run only one LM Studio model at a time.  The accepted raw results are already
included, so evaluation of the paper does not require model reruns.

Figure provenance
-----------------
Figure 3 answer-level counts:
  results/e1_seed20260726_p8_mistral_batch_r1.json

Figure 3 20-seed reconstruction audit:
  results/e1_structural_20seeds_mistral_r1.json

Figure 4 admission calibration:
  results/e4_admission_20seeds_*.json
  results/e4_admission_3models_analysis_r1.json

Figure 5 contract completeness and generator adherence:
  results/e2_e5_contract_suite_20seeds_r2.json
  results/e2_full_contract_20seeds_*.json
  results/e2_full_contract_3models_analysis_r3.json

Integrity and scope audits
--------------------------
SHA256SUMS.txt lists every file hash relative to this artifact root.

Before release, the authors should run:

  rg -n -i "散兵|scaramouche|wanderer|基尼奇|kinich|杜林|\bdurin\b|洛恩|\blorn\b" ^
    data results scripts figure-source-data

Expected result: zero matches in data, results, scripts, prompts, and figure
source data.

Release note
------------
The synthetic JSON payloads declare CC0 metadata.  A public code license and a
stable public artifact URL remain author-controlled release decisions and must
be selected before upload.  No license or external repository has been invented
by this packaging step.
