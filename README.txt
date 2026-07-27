CMTW v4 — PVLDB supplemental artifact (release 1.1)
=====================================================

Purpose
-------
This bundle contains the frozen, paper-used synthetic inputs, raw JSON results, exact
contract evaluators, local-LM probe runners, analysis scripts, and figure source
tables used by:

  CMTW: A Data-Management Workload for Persona Integrity and Verifiable
  Forgetting in Companion Memory [Vision]

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

LICENSE.txt
  MIT license for the Python source code.

DATA-LICENSE.txt
  CC0-1.0 dedication notice for the original synthetic data and result tables.

CITATION.cff
  Citation metadata for this artifact.

Environment
-----------
Deterministic contract generation and evaluation use Python's standard library.
The figure scripts additionally require numpy and matplotlib.  The release was
packaging-tested with Python 3.12.10, numpy 2.4.6, and matplotlib 3.10.8; these
versions are pinned in requirements.txt.  Local generation uses the
OpenAI-compatible LM Studio endpoint:

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
From the artifact root, run this single-line command in PowerShell, cmd.exe,
Bash, or another shell:

  python scripts/run_cmtw_v4_contract_suite.py --seed-start 20260727 --seeds 20 --personas 8 --data-output reproduced/cmtw_v4_contract_suite_20seeds_r2.json --results-output reproduced/e2_e5_contract_suite_20seeds_r2.json

This command performs no model call.  Compare the generated files with:

  data/cmtw_v4_contract_suite_20seeds_r2.json
  results/e2_e5_contract_suite_20seeds_r2.json

Local materialization and embedding reproduction
-------------------------------------------------
Start LM Studio at 127.0.0.1:1234 with the recorded Mistral and Nomic models,
then run one request at a time.  The following command is deliberately kept on
one line so it is shell-independent:

  python scripts/run_cmtw_v4_e1_structural_multiseed.py --seed-start 20260727 --seeds 20 --personas 8 --endpoint http://127.0.0.1:1234 --model mistralai_ministral-3-14b-instruct-2512 --embedding-model text-embedding-nomic-embed-text-v1.5 --timeout 180 --checkpoint-every 20 --data-output reproduced/cmtw_v4_e1_structural_20seeds_r1.json --results-output reproduced/e1_structural_20seeds_mistral_r1.json

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

Figure reproduction from frozen files
-------------------------------------
Install only the plotting dependencies, then regenerate the paper figures:

  python -m pip install -r requirements.txt
  python scripts/plot_cmtw_v5_figures.py
  python scripts/plot_cmtw_v7_figure_adoptions.py

These commands perform no inference, data generation, or statistical
re-estimation.  They read results/ and figure-source-data/ and write vector PDF
and SVG files, plus inspection rasters, under reproduced/figures/.  The first
script also exports recomputed CSV tables under
reproduced/figure-source-data/.

Integrity and scope audits
--------------------------
SHA256SUMS.txt lists every file hash relative to this artifact root.

The release audit uses this exact-name scan:

  rg -n -i -w -e scaramouche -e wanderer -e kinich -e durin -e lorn data results scripts figure-source-data
  rg -n -e 散兵 -e 基尼奇 -e 杜林 -e 洛恩 data results scripts figure-source-data

Expected result: zero matches in data, results, scripts, prompts, and figure
source data.

Release note
------------
Python source code is released under MIT; original synthetic data and result
tables are released under CC0-1.0.  The immutable submission snapshot is:

  https://github.com/flytoee-rgb/cmtw-pvldb-artifact/releases/tag/v1.1-pvldb-submission

Historical workspace paths recorded in docs/reproducibility-log-v4.txt are
preserved verbatim.  The packaged mapping is results/v4/ -> results/ and
docs/paper/figures/v4/source-data/ -> figure-source-data/.
