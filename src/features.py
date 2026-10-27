"""Feature extraction, one function per feature group.

Every group returns a dict of per clip numbers (frame level features
summarised by mean and std). Column names carry the group prefix so the
groups stay separable later: mfcc_, spec_, rhy_, chroma_.

Run: python -m src.features
"""
import json

import librosa
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tqdm import tqdm

from src import config


def _mean_std(prefix, name, frames):
    """Mean and std over time for a (n_rows, n_frames) or (n_frames,) array."""
    frames = np.atleast_2d(frames)
    out = {}
    for i, row in enumerate(frames):
        tag = f"{name}{i + 1}" if frames.shape[0] > 1 else name
        out[f"{prefix}{tag}_mean"] = float(np.mean(row))
        out[f"{prefix}{tag}_std"] = float(np.std(row))
    return out


def timbral_features(y, sr):
    """MFCC 1 to 20: the overall tone colour of the sound."""
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=config.N_MFCC,
                                n_fft=config.N_FFT, hop_length=config.HOP)
    return _mean_std("mfcc_", "c", mfcc)


def spectral_features(y, sr):
    """Brightness, sharpness and noisiness of the spectrum."""
    S = np.abs(librosa.stft(y, n_fft=config.N_FFT, hop_length=config.HOP))
    out = {}
    out.update(_mean_std("spec_", "centroid",
                         librosa.feature.spectral_centroid(S=S, sr=sr)[0]))
    out.update(_mean_std("spec_", "rolloff",
                         librosa.feature.spectral_rolloff(S=S, sr=sr)[0]))
    out.update(_mean_std("spec_", "bandwidth",
                         librosa.feature.spectral_bandwidth(S=S, sr=sr)[0]))
    out.update(_mean_std("spec_", "zcr",
                         librosa.feature.zero_crossing_rate(
                             y, frame_length=config.N_FFT, hop_length=config.HOP)[0]))
    out.update(_mean_std("spec_", "rms", librosa.feature.rms(S=S)[0]))
    out.update(_mean_std("spec_", "contrast",
                         librosa.feature.spectral_contrast(S=S, sr=sr)))
    return out


def rhythm_features(y, sr):
    """Tempo, beat regularity and how strong the pulse is."""
    hop = config.HOP
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr,
                                           hop_length=hop)
    beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop)
    intervals = np.diff(beat_times)
    duration = len(y) / sr

    tgram = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr,
                                      hop_length=hop)
    # average autocorrelation over time; lag 0 is always 1 so leave it out
    profile = tgram.mean(axis=1)[1:]

    return {
        "rhy_tempo": float(np.atleast_1d(tempo)[0]),
        "rhy_onset_mean": float(onset_env.mean()),
        "rhy_onset_std": float(onset_env.std()),
        "rhy_onset_max": float(onset_env.max()),
        "rhy_beat_interval_mean": float(intervals.mean()) if len(intervals) else 0.0,
        "rhy_beat_interval_std": float(intervals.std()) if len(intervals) else 0.0,
        "rhy_beats_per_sec": len(beats) / duration if duration else 0.0,
        "rhy_tempogram_mean": float(tgram.mean()),
        "rhy_tempogram_std": float(tgram.std()),
        "rhy_tempogram_peak": float(profile.max()),
    }


def chroma_features(y, sr):
    """12 pitch classes: which notes and chords are present."""
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_fft=config.N_FFT,
                                         hop_length=config.HOP)
    return _mean_std("chroma_", "c", chroma)


def extract_from_array(y, sr=config.SR):
    """All four groups for one audio array."""
    feats = {}
    feats.update(timbral_features(y, sr))
    feats.update(spectral_features(y, sr))
    feats.update(rhythm_features(y, sr))
    feats.update(chroma_features(y, sr))
    return feats


def extract_clip(path):
    """Load a clip (first 30 s, 22050 Hz mono) and extract all features."""
    y, sr = librosa.load(path, sr=config.SR, mono=True, duration=config.DURATION)
    return extract_from_array(y, sr)


def _safe_extract(path):
    try:
        row = extract_clip(path)
    except Exception as e:  # unreadable clip, report it instead of crashing
        return path, None, str(e)
    row = {"filename": path.name, "genre": path.parent.name, **row}
    return path, row, None


def main(chunk_size=50):
    files = sorted(config.RAW_DIR.glob("*/*.wav"))
    config.FEATURES_DIR.mkdir(parents=True, exist_ok=True)

    done = set()
    if config.FEATURES_PARTIAL.exists():
        done = set(pd.read_csv(config.FEATURES_PARTIAL, usecols=["filename"])["filename"])
    todo = [f for f in files if f.name not in done]
    print(f"{len(files)} clips found, {len(done)} already done, {len(todo)} to go")

    failed = []
    for start in tqdm(range(0, len(todo), chunk_size), desc="chunks"):
        chunk = todo[start:start + chunk_size]
        results = Parallel(n_jobs=-1)(delayed(_safe_extract)(f) for f in chunk)
        rows = [r for _, r, _ in results if r is not None]
        failed += [{"clip": p.stem, "error": err} for p, r, err in results if r is None]
        if rows:
            pd.DataFrame(rows).to_csv(config.FEATURES_PARTIAL, mode="a", index=False,
                                      header=not config.FEATURES_PARTIAL.exists())

    df = pd.read_csv(config.FEATURES_PARTIAL)
    df = df.drop_duplicates("filename").sort_values("filename").reset_index(drop=True)
    n_nan = int(df.isna().sum().sum())
    if n_nan:
        raise SystemExit(f"{n_nan} NaN values in the feature table, not saving")
    df.to_csv(config.FEATURES_CSV, index=False)
    config.FEATURES_PARTIAL.unlink()

    skipped = []
    if config.SKIPPED_JSON.exists():
        skipped = json.loads(config.SKIPPED_JSON.read_text())
    meta = {
        "librosa_version": librosa.__version__,
        "params": {"sr": config.SR, "duration": config.DURATION, "n_fft": config.N_FFT,
                   "hop_length": config.HOP, "n_mfcc": config.N_MFCC},
        "n_clips": len(df),
        "n_features": {g: int(df.columns.str.startswith(p).sum())
                       for g, p in config.GROUPS.items()},
        "skipped": skipped + failed,
    }
    config.FEATURES_META.write_text(json.dumps(meta, indent=2))
    print(f"Saved {df.shape[0]} rows x {df.shape[1]} columns to {config.FEATURES_CSV}")
    print("Features per group:", meta["n_features"])
    if failed:
        print("Failed:", failed)


if __name__ == "__main__":
    main()
