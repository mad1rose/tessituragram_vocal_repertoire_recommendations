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
  - `all_tessituragrams.json` – **Primary dataset** for the recommendation CLI and for **Experiment 2** (paper: 1,655 vocal lines / 1,419 works). Multi-part works appear as separate lines (`part_id`, `part_name`).
  - `tessituragrams.json` – **Experiment 1** subset (101 solo vocal lines, one per composition), used with the scripts under `previous_paper_and_experiments/previous_experiment_scripts/` for the compact-library protocol.
  - `recommendations.json` – Output of the recommendation CLI (overwritten each run).

- **`experiment/`** – Python scripts for **Experiment 2** (large library: `data/all_tessituragrams.json`).
  - `run_rq1_experiment.py`, `run_rq2_experiment.py`, `run_rq3_experiment.py` – Main experiment entry points for research questions RQ1–RQ3.
  - `run_rq1_baselines.py`, `run_rq2_baselines.py` – Baseline methods for comparison.
  - `run_alpha_sensitivity.py` – Alpha‑sensitivity analysis (same seeds and sampling rules as the main RQ scripts; see `alpha_sensitivity_results.json`).
  - `visualize_rq1.py`, `visualize_rq2.py`, `visualize_rq3.py`, `visualize_baselines.py`, `visualize_alpha_sensitivity.py` – Plotting / visualization of experiment outputs.

- **`experiment_results/`** – **Canonical JSON outputs for Experiment 2** (tables in the paper; large-library protocol).
  - `RQ1_results.json`, `RQ2_results.json`, `RQ3_results.json` – Main experiment outputs.
  - `RQ1_baselines.json`, `RQ2_baselines.json` – Baseline experiment results.
  - `alpha_sensitivity_results.json` – Alpha‑sensitivity runs.

- **`previous_paper_and_experiments/`** – **Experiment 1** scripts (`previous_experiment_scripts/`, e.g. `old_run_rq1_experiment.py`) and **canonical JSON** for the 101-line protocol (`previous_experiment_results/old_*.json`). Use this tree when reproducing compact-library numbers or extending that protocol without changing Experiment 2 outputs.

- **`how_tos/`** – Plain‑text guides that explain **how to run the code in this repo**, written for users with **limited computer science background**.
  - `how_to_create_tessituragrams.txt` – Step‑by‑step instructions to install dependencies and run the tessituragram creation pipeline.
  - `how_to_get_recommendations.txt` – Instructions for running the recommendation CLI (including ensemble type selection and multi-profile entry) and interpreting outputs.
  - `how_to_view_tessituragrams.txt` – Instructions for visualizing tessituragrams and related plots.

- **`songs/mxl_songs/`** – Collection of **MusicXML (`.mxl`) vocal scores** used as input to build tessituragrams and to run experiments.

- **`app.py`** – **Flask web application**. Run `python app.py` and open [http://localhost:5000](http://localhost:5000) to use the interactive web UI for browsing recommendations.

- **`templates/`** – HTML templates for the web UI (Jinja2).

- **`static/`** – CSS, JavaScript, and images for the web UI (includes the interactive piano keyboard component).

- **`requirements.txt`** – Python dependencies (numpy, scipy, matplotlib, music21, nbformat, flask) needed to run the library, web UI, experiments, and visualizations.

### Getting started (quick)

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the web UI** (recommended)
   ```bash
   python app.py
   ```
   Then open **[http://localhost:5000](http://localhost:5000)** in your browser.

   The UI walks you through everything — pick an ensemble type (solo, duet, trio, …), name your singers, set each singer's vocal range / favorite notes / notes to avoid using an interactive piano keyboard, and browse ranked recommendations with visual tessituragram comparisons.

3. **Or use the command-line interface**
   ```bash
   python -m src.run_recommendations
   ```
   The interactive CLI will ask you to pick an ensemble type, then enter one vocal profile per singer (range, favorite notes, avoid notes). Results are printed to the terminal and saved to `data/recommendations.json`.

4. **Create tessituragrams from your own songs** (optional — the repo already includes pre-built data)
   ```bash
   python -m src.main --input-dir songs/mxl_songs --output data/tessituragrams.json
   ```

5. **Visualise recommendations** (CLI results only)
   ```bash
   python -m src.visualize_recommendations
   ```
   Opens the results as a Jupyter notebook with bar-chart comparisons of each song against the ideal profile(s).

6. **Run experiments**
   - Use the scripts in `experiment/` (see the matching how‑to in `how_tos/` for copy‑pasteable commands).

For more detailed, non‑CS‑heavy walkthroughs, open the files in `how_tos/`. They are intended as the primary entry point for new users.