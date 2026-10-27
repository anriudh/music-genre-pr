# Project Brief: Music Genre Pattern Recognition via Feature Ablation

Read this whole file before doing anything. Start in **plan mode**, produce a phased plan, and wait for my approval before writing code or touching git. Deadline is tight, so keep the plan lean and do not add scope beyond what is written here.

## Environment (read first, this is where blockers will come from)

- You are running in a **Claude Code cloud session** (Linux container), not on my machine. My own machine is **Windows**, which only matters for the README run instructions and the live demo.
- **Network is restricted.** Package registries (PyPI) and GitHub are normally reachable. Most other sites (Kaggle, dataset hosts, university mirrors) may be blocked by the proxy. There is **no Kaggle API key** and I do not want to set one up.
- **Do this before planning anything else:** run a quick reachability check (for example `curl -sSI` against `https://huggingface.co`, `https://www.kaggle.com`, `https://pypi.org`, `https://github.com`) and report what is reachable. If something fails, read `/root/.ccr/README.md` and check `curl -sS "$HTTPS_PROXY/__agentproxy/status"` instead of retrying with other tools. Never disable TLS verification or unset the proxy variables.
- **Dataset access plan, in order:**
  1. If Hugging Face is reachable, find a GTZAN mirror on the Hub that stores the audio directly (parquet or wav files, not a loading script that downloads from the original marsyas site, which is usually dead). Download with `huggingface_hub` and decode to wav locally. Verify 10 genres, about 100 clips each.
  2. If Hugging Face is blocked, check whether a GitHub-hosted copy of GTZAN is reachable (GitHub is allowlisted).
  3. If both fail, **stop and tell me plainly**. Do not spend time trying other workarounds. I will upload the data myself.
- **Session storage is temporary.** Anything not pushed to GitHub can be lost. So: commit and push after every phase, and commit `data/features/features.csv` (it is small) so feature extraction never has to be redone. Raw audio is never committed.
- **Long jobs:** feature extraction over ~1000 clips takes a while. Run it in the foreground (not as a detached background process, those get killed), parallelise with `joblib`, and make it resumable (write partial results so a rerun skips clips already done).
- **No ffmpeg or apt installs needed.** Use `soundfile` (its wheels bundle libsndfile with MP3 support) plus `librosa` for loading. This also keeps the demo working on Windows without installing ffmpeg. If `apt-get` is needed for anything, assume it may be blocked and find a pip-only route.
- **Python env:** create a `venv` at `.venv` in the project root and install everything into it with pinned versions in `requirements.txt`. No global installs. Pick package versions that also install cleanly on Windows with Python 3.11 or 3.12 (avoid anything needing a C compiler on Windows).

## GitHub

- Repo name: your choice, short and descriptive (something like `music-genre-pr`). **Public.** My GitHub user is `anriudh`.
- Try creating it with the preinstalled `gh` CLI (`gh repo create anriudh/<name> --public`). If that fails because of permissions or the session's GitHub access, **stop and tell me the exact name**; I will create the empty repo myself and add it to the session, then you continue.
- `.gitignore`: `.venv/`, `data/raw/`, `__pycache__/`, `.ipynb_checkpoints/`, any downloaded archives and HF cache.
- Commit messages: plain, short, human. No em dashes.

## Context

- Course: Pattern Recognition (PR), B.Tech CSE (Data Science), 7th semester. Solo project, graded.
- It will be presented to the whole class with a PPT (not part of this build). Every figure must be presentation ready: readable labels, sensible titles, saved as PNG at 300 dpi.
- This must read as a **Pattern Recognition study, not an ML tutorial**. GTZAN genre classification is a common student project. What makes ours different is the central question:

  > Which categories of audio features actually carry the information that separates music genres, and why does that match musical intuition?

  The headline result is the **feature group ablation**, not a single accuracy number.

## Scope

### Dataset
- GTZAN: 1000 clips, 10 genres (blues, classical, country, disco, hiphop, jazz, metal, pop, reggae, rock), 30 s each.
- Use raw audio only. Do not use any precomputed feature CSVs that come with a mirror; we extract our own.
- `jazz.00054` is corrupted in most copies. Loading must skip unreadable files and log what was skipped.
- Resample everything to 22050 Hz mono.

### Feature extraction (librosa)
Extract per frame, aggregate per clip (mean and std). Keep the four groups separate in code and in the saved table using column prefixes `mfcc_`, `spec_`, `rhy_`, `chroma_`.

| Group | Features | What it captures |
|---|---|---|
| Timbral | MFCC 1 to 20 (mean, std) | Tone colour / texture |
| Spectral | Spectral centroid, rolloff, bandwidth, contrast, zero crossing rate, RMS | Brightness, sharpness, noisiness |
| Rhythm | Tempo, onset strength stats, beat interval stats, tempogram summary | Groove and pacing |
| Chroma | 12 bin chroma (STFT), mean and std | Harmonic / pitch class content |

Save to `data/features/features.csv` plus a small `features_meta.json` (librosa version, parameters, skipped files).

### Classifiers
- SVM (RBF) and Random Forest. Skip KNN, no time.
- Scaling inside an sklearn `Pipeline` so nothing leaks across folds.
- **Stratified 5 fold CV** (mean and std) for all reported numbers, plus one stratified held out split for the confusion matrix.
- Light tuning only: a small grid (for SVM, C and gamma; for RF, n_estimators and max_depth), nested inside the training folds. Fixed random seeds everywhere.

### Core analysis: feature group ablation
For each classifier, train and evaluate on:
1. Timbral only
2. Spectral only
3. Rhythm only
4. Chroma only
5. All combined
6. All minus one group (four runs, cheap and shows each group's added value)

Outputs:
- `figures/ablation_accuracy.png`: CV accuracy with error bars per feature set, per classifier.
- `figures/per_genre_f1_heatmap.png`: rows = feature groups, columns = genres. This is the key figure for the musical interpretation.
- `figures/rf_importance_by_group.png`: Random Forest importances summed per group.
- `figures/confusion_matrix.png`: best combined model (supporting figure only).
- `results/ablation_results.csv`: every run's numbers.

### Demo script
`predict.py <audio_file>`: loads any WAV or MP3, takes the middle 30 s, extracts the same features, loads the saved best model (`models/best_model.joblib`, committed if under ~20 MB), prints the predicted genre with class probabilities, and saves a mel spectrogram PNG next to the input. Test it in the cloud on a GTZAN clip and on a short synthetic or converted non GTZAN file. I will run it myself on Windows for the live demo.

### Out of scope
Deep learning or pretrained embeddings, a confusion pair deep dive section, the PPT, any web UI, KNN.

## Project layout

```
<repo>/
  data/
    raw/              # ignored
    features/         # features.csv, features_meta.json (committed)
  models/             # best_model.joblib
  src/
    config.py         # paths, seeds, librosa params
    download.py
    features.py       # one function per feature group
    train.py
    ablation.py
    plots.py
  predict.py
  results/
  figures/
  requirements.txt
  README.md
  .gitignore
```

One command per phase (for example `python -m src.features`), plus a `run_all` entry point.

## Phases

1. **Env check and setup**: reachability check, venv, requirements, layout, git init, GitHub repo, first push. Exit: deps install in a fresh venv, repo exists and has the initial commit.
2. **Data**: get GTZAN via the access plan above, verify counts per genre. Exit: 999 or 1000 readable clips across 10 genres. Push.
3. **Features**: resumable, parallel extraction. Exit: one row per clip, prefixed columns, no NaNs. Commit the CSV. Push.
4. **Models and ablation**: baseline on all features, then every ablation run, results CSV and all four figures. Exit: combined accuracy roughly in the 65 to 80% range (flag anything far outside), all figures exist. Push.
5. **Demo**: `predict.py` working, model saved. Exit: tested on a GTZAN and a non GTZAN file. Push.
6. **README and wrap up**: project question, Windows setup commands (`py -3.12 -m venv .venv`, `.venv\Scripts\activate`, `pip install -r requirements.txt`), how to run each phase and the demo, results table, embedded figures, a short plain interpretation of what the ablation shows, and known limitations (GTZAN has duplicate tracks and repeated artists, so random splits can inflate scores). Final push.

## Writing style

README, comments, docstrings, and commit messages: plain and human, like a student explaining their own work. No em dashes anywhere, no filler, no hype words.

## Questions for me

Only ask if genuinely blocked (dataset unreachable, repo creation fails). Everything else in this file is decided.
