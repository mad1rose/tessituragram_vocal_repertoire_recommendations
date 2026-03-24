## Tessituragram Vocal Repertoire Recommendations

This repository contains code and data for generating **tessituragrams** from vocal scores and using them to build and evaluate **vocal repertoire recommendation** methods. It includes an **interactive web app** with a piano keyboard interface for musicians to get personalized song recommendations.

### Quick Start — Run the Web App

```bash
pip install -r requirements.txt
python server/app.py
```

Then open **http://localhost:8000** in your browser.

**How to use the app:**

1. **Set your range** — click your lowest note on the piano, then your highest. Keys outside your range dim automatically.
2. **Mark favorites** — switch to Favorites mode and click keys to highlight them green. Click any green key again to un-mark it.
3. **Mark avoids** — switch to Avoid mode and click keys to highlight them red. Click any red key again to un-mark it.
4. **Adjust alpha** — drag the slider to control how harshly avoided notes penalize a song's ranking (0 = ignore, 1 = heavy penalty).
5. **Get Recommendations** — click the button to see your ranked results, 10 per page.
6. **View details** — click any song card to see its tessituragram chart overlaid with your ideal vector.
7. **Edit profile** — click "← Edit Profile" on the results page to go back and change your settings.

---

### Core Use Cases

- **Create tessituragrams** from MusicXML songs.
- **Get personalized song recommendations** via the interactive web app.
- **Run recommendation experiments** (RQ1–RQ3, baselines, alpha-sensitivity).
- **Inspect experiment results** and visualizations.
- **Use step‑by‑step how‑tos** aimed at musicians / teachers with limited CS background.

### Repository Layout

- **`server/`** – FastAPI backend that powers the web app.
  - `app.py` – Entry point. Serves the API and the built React frontend.
  - `api/routes.py` – API endpoints (`/api/recommend`, `/api/song/{filename}`, `/api/library`).
  - `api/schemas.py` – Request/response models.

- **`client/`** – React + TypeScript frontend (built with Vite and Tailwind CSS).
  - `src/pages/` – Profile setup page and results page.
  - `src/components/` – Piano keyboard, alpha slider, song cards, detail modal, charts, pagination.
  - `dist/` – Pre-built frontend assets served by FastAPI (rebuild with `cd client && npm run build`).

- **`src/`** – Core library / CLI code.
  - `main.py` – CLI to **create tessituragrams** from `.mxl` files and write them to `data/tessituragrams.json`.
  - `run_recommendations.py` – CLI to **run recommendation scoring** on an existing tessituragram library.
  - `tessituragram.py` – Tessituragram construction and statistics.
  - `parser.py` – MusicXML parsing and vocal line extraction (uses `music21`).
  - `metadata.py` – Extracts score metadata (composer, title, etc.).
  - `storage.py` – Loading/saving/merging tessituragram JSON and recommendation output.
  - `recommend.py` – Recommendation algorithms and scoring logic.
  - `visualize.py`, `visualize_recommendations.py` – Utilities for plotting / notebook-style visualization (uses `nbformat`).

- **`experiment/`** – Python scripts for **running the experiments** reported in the paper.
  - `run_rq1_experiment.py`, `run_rq2_experiment.py`, `run_rq3_experiment.py` – Main experiment entry points for research questions RQ1–RQ3.
  - `run_rq1_baselines.py`, `run_rq2_baselines.py` – Baseline methods for comparison.
  - `run_alpha_sensitivity.py` – Alpha‑sensitivity analysis experiments.
  - `visualize_rq1.py`, `visualize_rq2.py`, `visualize_rq3.py`, `visualize_baselines.py`, `visualize_alpha_sensitivity.py` – Plotting / visualization of experiment outputs.

- **`experiment_results/`** – **Results of the experiments**.
  - `RQ1_results.json`, `RQ2_results.json`, `RQ3_results.json` – Main experiment outputs.
  - `RQ1_baselines.json`, `RQ2_baselines.json` – Baseline experiment results.
  - `alpha_sensitivity_results.json` – Results for alpha‑sensitivity runs.

- **`how_tos/`** – Plain‑text guides that explain **how to run the code in this repo**, written for users with **limited computer science background**.
  - `how_to_create_tessituragrams.txt` – Step‑by‑step instructions to install dependencies and run the tessituragram creation pipeline.
  - `how_to_get_recommendations.txt` – Instructions for running the recommendation scripts and interpreting outputs.
  - `how_to_view_tessituragrams.txt` – Instructions for visualizing tessituragrams and related plots.

- **`songs/mxl_songs/`** – Collection of **MusicXML (`.mxl`) vocal scores** used as input to build tessituragrams and to run experiments.

- **`requirements.txt`** – Python dependencies (numpy, scipy, matplotlib, music21, nbformat, fastapi, uvicorn).

### Getting Started (detailed)

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Create tessituragrams from the provided songs** (already done if `data/tessituragrams.json` exists)
   ```bash
   python -m src.main --input-dir songs/mxl_songs --output data/tessituragrams.json
   ```
3. **Run the web app**
   ```bash
   python server/app.py
   ```
   Open **http://localhost:8000** in your browser.

4. **Rebuild the frontend** (only needed if you edit files in `client/src/`)
   ```bash
   cd client
   npm install
   npm run build
   ```

5. **Run experiments or visualize results**
   - Use the scripts in `experiment/` (see the matching how‑to in `how_tos/` for copy‑pasteable commands).

For more detailed, non‑CS‑heavy walkthroughs, open the files in `how_tos/`. They are intended as the primary entry point for new users.
