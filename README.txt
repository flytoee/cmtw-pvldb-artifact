CMTW reproducibility artifacts: ICDE DEFT and historical PVLDB
=============================================================

CURRENT ICDE ARTIFACT (2026-10-10)
---------------------------------
Paper: CMTW: Lifecycle-Sound Data Management for Long-Lived Companion Memory
Release: https://github.com/flytoee/cmtw-pvldb-artifact/releases/tag/v2.0-icde-deft
Download: https://github.com/flytoee/cmtw-pvldb-artifact/releases/download/v2.0-icde-deft/cmtw-icde-deft-artifact.zip

For the new ICDE experiments, download the named ZIP above. It contains the
frozen v6 synthetic inputs, pre-policy labels, raw local model responses,
strong conventional database comparator, scope-epoch prototype, held-out
admission tests, equal-fallback deletion tests, genuine summary/embedding
fixtures, learned query-withdrawal concurrency traces, executed source
snapshots, plots, command logs, SHA-256 manifests, and manuscript sources.
The v7 paper in the ZIP is an availability-only revision; no experiment or
scientific claim was changed for this release. AI-use disclosure awaits a
separate author-approved manuscript update.

ZIP size: 5,421,554 bytes
ZIP SHA-256: 068950a391af0c064b48e6c18f4b9c1cf9a6d9cc2945c7eaef583a8754099587
The ZIP contains 1,719 files and a per-file SHA256-MANIFEST.json.
Code: existing MIT license. Original synthetic data/results: existing CC0
dedication. No model weights, borrowed paper PDFs or real participant data.

The repository file tree below remains the historical PVLDB artifact.
GitHub's automatic Source code ZIP/tar.gz downloads snapshot that legacy tree;
they are NOT the new ICDE evidence package. Use cmtw-icde-deft-artifact.zip.
Do not pool the new GLM/Nomic experiment results with old model results.

HISTORICAL PVLDB ARTIFACT - documentation below retained
-------------------------------------------------------
Release: https://github.com/flytoee/cmtw-pvldb-artifact/releases/tag/v1.4-pvldb-submission

CMTW PVLDB supplemental artifact
================================

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

paper-figures/
  Exact adopted submission files for Figures 3–5.  Figure 4 is distributed as
  its adopted vector PDF plus its self-contained HTML/SVG source in scripts/.

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
The historical figure scripts additionally require numpy and matplotlib; these
versions are pinned in requirements.txt.  The adopted submission figures use
R 4.5.3 and the packages listed in R-packages.txt, plus Chrome or Edge for the
self-contained Figure 4 HTML.  Local generation uses the
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
The exact adopted files are under paper-figures/.  Regenerate their current
visual encodings from frozen CSVs and self-contained source with:

The adopted outputs use stable submission names:

  paper-figures/cmtw-fig3-recorded-view-repair.*
  paper-figures/cmtw-fig4-lifecycle-correctness.pdf
  paper-figures/cmtw-fig5-contract-portability.*

  Rscript scripts/build_cmtw_fig3_submission.R
  powershell -ExecutionPolicy Bypass -File scripts/render_cmtw_fig4_submission.ps1
  Rscript scripts/build_cmtw_fig5_submission.R

These commands perform no inference, data generation, or statistical
re-estimation.  They write to reproduced/paper-figures/.  R-generated SVG, PNG,
and TIFF files reproduce byte-for-byte in the audited environment; PDF metadata
contains a render timestamp, so PDF byte hashes may differ although rendered
content is identical.  The Figure 4 audit renders adopted and reproduced PDFs at
150 dpi and obtains identical raster SHA-256 values; its source is
scripts/fig4_submission.html.

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
tables are released under CC0-1.0.  The public artifact repository is:

  https://github.com/flytoee/cmtw-pvldb-artifact

Historical workspace paths recorded in docs/reproducibility-log-v4.txt are
preserved verbatim.  The packaged mapping is results/v4/ -> results/ and
docs/paper/figures/v4/source-data/ -> figure-source-data/.
