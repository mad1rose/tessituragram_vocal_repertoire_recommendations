# Experiment 1 replication (101-line library)

These scripts reproduce **Experiment 1** from the CADSCOM paper: `data/tessituragrams.json` (101 vocal lines, one per composition), **N_QUERIES = 50**, query seed **42**, and **i.i.d.** bootstrap CIs on query-level (or baseline-level) outcomes. Query sampling is uniform over **eligible lines**; with at most one line per composition in this library, that coincides with uniform sampling over compositions. They do **not** import `experiment/run_rq1_experiment.py` or `experiment/run_rq2_experiment.py`, which implement **Experiment 2** (1,655 lines, cluster bootstrap).

## Run from the repository root

```text
python previous_paper_and_experiments/previous_experiment_scripts/old_run_rq1_experiment.py
python previous_paper_and_experiments/previous_experiment_scripts/old_run_rq1_baselines.py
python previous_paper_and_experiments/previous_experiment_scripts/old_run_rq2_experiment.py
python previous_paper_and_experiments/previous_experiment_scripts/old_run_rq2_baselines.py
python previous_paper_and_experiments/previous_experiment_scripts/old_run_rq3_experiment.py
python previous_paper_and_experiments/previous_experiment_scripts/old_run_alpha_sensitivity.py
```

## Outputs

JSON is written under `previous_paper_and_experiments/previous_experiment_results/`:

| File | Contents |
|------|----------|
| `old_RQ1_results.json` | RQ1 self-retrieval (full model, α = 0.5) |
| `old_RQ1_baselines.json` | RQ1 null / cosine-only / full + paired contrasts + \|C\| summaries |
| `old_RQ2_results.json` | RQ2 stability (5 baselines) |
| `old_RQ2_baselines.json` | RQ2 baselines |
| `old_RQ3_results.json` | RQ3 implementation checks (25 profiles) |
| `old_alpha_sensitivity_results.json` | RQ1 + RQ2 across α |

Shared constants and query selection live in `previous_experiment_scripts/exp1_common.py`.

## Experiment 2

Large-library experiments and Table 2 (right column) / Table 4 (right column) use `experiment/run_*.py` and `experiment_results/*.json`.
