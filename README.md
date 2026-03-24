## Tessituragram Vocal Repertoire Recommendations

This repository contains code and data for generating **tessituragrams** from vocal scores and using them to build and evaluate **vocal repertoire recommendation** methods.

The core use cases are:
- **Create tessituragrams** from MusicXML songs.
- **Get personalised song recommendations** for solo singers, duets, trios, and larger ensembles.
- **Run recommendation experiments** (RQ1–RQ3, baselines, alpha-sensitivity).
- **Inspect experiment results** and visualizations.
- **Use step‑by‑step how‑tos** aimed at musicians / teachers with limited CS background.

### Repository layout

- **`src/`** – Core library / CLI code.
  - `main.py` – CLI to **create tessituragrams** from `.mxl` files and write them to `data/tessituragrams.json`.
  - `run_recommendations.py` – Interactive CLI to **get song recommendations**. Supports solos and multi-part songs (duets, trios, etc.). For multi-part songs the user enters one vocal profile per singer and the system finds the optimal assignment of singers to vocal lines using the Hungarian algorithm.
  - `tessituragram.py` – Tessituragram construction and statistics.
  - `parser.py` – MusicXML parsing and vocal line extraction (uses `music21`).
  - `metadata.py` – Extracts score metadata (composer, title, etc.).
  - `storage.py` – Loading/saving/merging tessituragram JSON and recommendation output. Includes helpers for ensemble-type discovery, filtering, and part flattening.
  - `recommend.py` – Recommendation algorithms and scoring logic, including single-profile scoring (solo path) and multi-profile optimal assignment (multi-part path).
  - `visualize.py` – Generates a Jupyter notebook with raw tessituragram histograms (supports both single-part and multi-part formats).
  - `visualize_recommendations.py` – Generates a Jupyter notebook with recommendation charts: each song's normalised tessituragram overlaid with the matched profile's ideal vector.

- **`data/`** – Data files.
  - `all_tessituragrams.json` – **Primary dataset** used by the recommendation CLI. Contains tessituragrams for all songs, including songs with multiple voice parts (each part stored separately with its own `part_id` and `part_name`).
  - `tessituragrams.json` – Older single-part dataset used by the experiment scripts.
  - `recommendations.json` – Output of the recommendation CLI (overwritten each run).

- **`experiment/`** – Python scripts for **running the experiments** reported in the paper.
  - `run_rq1_experiment.py`, `run_rq2_experiment.py`, `run_rq3_experiment.py` – Main experiment entry points for research questions RQ1–RQ3.
  - `run_rq1_baselines.py`, `run_rq2_baselines.py` – Baseline methods for comparison.
  - `run_alpha_sensitivity.py` – Alpha‑sensitivity analysis experiments.
  - `visualize_rq1.py`, `visualize_rq2.py`, `visualize_rq3.py`, `visualize_baselines.py`, `visualize_alpha_sensitivity.py` – Plotting / visualization of experiment outputs.
  - *Note:* experiment scripts use the older `data/tessituragrams.json` for reproducibility.

- **`experiment_results/`** – **Results of the experiments**.
  - `RQ1_results.json`, `RQ2_results.json`, `RQ3_results.json` – Main experiment outputs.
  - `RQ1_baselines.json`, `RQ2_baselines.json` – Baseline experiment results.
  - `alpha_sensitivity_results.json` – Results for alpha‑sensitivity runs.

- **`how_tos/`** – Plain‑text guides that explain **how to run the code in this repo**, written for users with **limited computer science background**.
  - `how_to_create_tessituragrams.txt` – Step‑by‑step instructions to install dependencies and run the tessituragram creation pipeline.
  - `how_to_get_recommendations.txt` – Instructions for running the recommendation CLI (including ensemble type selection and multi-profile entry) and interpreting outputs.
  - `how_to_view_tessituragrams.txt` – Instructions for visualizing tessituragrams and related plots.

- **`songs/mxl_songs/`** – Collection of **MusicXML (`.mxl`) vocal scores** used as input to build tessituragrams and to run experiments.

- **`requirements.txt`** – Python dependencies (numpy, scipy, matplotlib, music21, nbformat) needed to run the library, experiments, and visualizations.

### Getting started (quick)

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Create tessituragrams from the provided songs**
   ```bash
   python -m src.main --input-dir songs/mxl_songs --output data/tessituragrams.json
   ```
3. **Get song recommendations**
   ```bash
   python -m src.run_recommendations
   ```
   The interactive CLI will ask you to pick an ensemble type (solo, duet, trio, …), then enter one vocal profile per singer (range, favorite notes, avoid notes). Results are printed to the terminal and saved to `data/recommendations.json`.
4. **Visualise recommendations**
   ```bash
   python -m src.visualize_recommendations
   ```
   Opens the results as a Jupyter notebook with bar-chart comparisons of each song against the ideal profile(s).
5. **Run experiments**
   - Use the scripts in `experiment/` (see the matching how‑to in `how_tos/` for copy‑pasteable commands).

For more detailed, non‑CS‑heavy walkthroughs, open the files in `how_tos/`. They are intended as the primary entry point for new users.