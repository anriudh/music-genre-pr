# HANDOFF 2026-10-27 16:47 | claude/blissful-carson-741n9o@ec64f8c | paused: manual
Resume protocol: read this file and nothing else, then open only the files under Load.
Do not scan the repo, re-read the old conversation, or re-derive what is listed here.
If HEAD is not ec64f8c, run `git log --oneline ec64f8c..HEAD` first. Start at Not done 1.
Delete this file once Not done is finished.

## Goal
Build the GTZAN feature group ablation project from PROJECT_BRIEF.md, all 6 phases, pushed to GitHub. All 6 phases are built and pushed; only follow-ups that need the user are left.

## Done (verified)
- Phase 1, env and layout: py3.12 `.venv`, pinned `requirements.txt` installed and imported cleanly (9a9d230)
- Phase 2, data: `src/download.py` pulls the HF mirror `sanchit-gandhi/gtzan` (parquet, raw audio) into `data/raw/genres/<genre>/*.wav`, 22050 Hz mono, 999 clips. jazz.00054 is not in the mirror and is logged as "missing from mirror" (d8d2ec0)
- Phase 3, features: `src/features.py` produces 98 features (40 mfcc_, 24 spec_, 10 rhy_, 24 chroma_). 999 rows, no NaN. Resume tested by killing the run at 600 clips and rerunning. CSV and meta committed (87f5f88)
- Phase 4, models and ablation: `src/train.py`, `src/ablation.py`, `src/plots.py`. 18 nested CV runs. SVM All 80.1%, RF All 76.4%, holdout 83.0%. 4 figures checked visually, results CSVs and `models/best_model.joblib` (0.7 MB, SVM C=10 gamma=0.01) committed (f9ad7dc)
- Phase 5, demo: `predict.py` tested on metal.00010.wav (metal 98.6%), a synthetic WAV and MP3, and a 10 s MP3 (032349d, b3ba0a2)
- Phase 6: `src/run_all.py` plus the full README (results table, figures, interpretation, limitations, Windows setup). `python -m src.run_all` reran and reproduced results, model and figures with zero git diff (ec64f8c)
- Branch is pushed and in sync with origin

## Not done
1. Nothing left from the brief. Remaining items need the user:
2. User runs `predict.py` on Windows for the live demo. Not tested on Windows from here.
3. Merge `claude/blissful-carson-741n9o` into `main` (no PR opened; only do it if the user asks).
4. At project end, remove CLAUDE.md, HANDOFF.md and PROJECT_BRIEF.md from the repo (user decision, see Decisions).

## Decisions
- CLAUDE.md, HANDOFF.md and PROJECT_BRIEF.md stay tracked until the project ends, so the handoff works across cloud sessions. Do not gitignore them now.
- predict.py does not pad short files with silence, because padding skews the mean/std features. Short files are used whole.
- Heatmap and confusion matrix use the better combined classifier (SVM).
- Combined 80.1% is slightly above the brief's 65 to 80% range. The README limitations explain it (GTZAN artist and duplicate leakage in random splits).

## Dead ends
- huggingface.co was 403 by proxy policy at session start. The user allowed it in the environment network settings, and it worked in the same session. Kaggle is still blocked; it is not needed.

## Gotchas
- `data/raw/` (wavs plus hf_cache, about 2.6 GB) is not committed. A fresh clone does not need it: features.csv and the model are committed.
- The ablation takes about 7 min on 4 cores.
- CLAUDE.md says no AI attribution trailers in commits and no em dashes anywhere.

## Load
- README.md: current results and run instructions, if the user asks about results or the demo.

## Verify
- `git log --oneline -1` -> `ec64f8c Add run_all and full README`
- `python predict.py data/raw/genres/metal/metal.00010.wav` -> `Predicted genre: METAL` (needs raw data, which exists only in this container)
