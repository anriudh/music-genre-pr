"""Predict the genre of any WAV or MP3 file with the saved model.

Takes the middle 30 seconds of the file, extracts the same features used in
training, prints the predicted genre with class probabilities and saves a mel
spectrogram PNG next to the input file.

Usage: python predict.py path/to/song.mp3
"""
import argparse
import sys
from pathlib import Path

import joblib
import librosa
import librosa.display
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import config
from src.features import extract_from_array


def middle_30s(y, sr):
    """Middle 30 s of the signal, zero padded if the file is shorter."""
    n = int(config.DURATION * sr)
    if len(y) >= n:
        start = (len(y) - n) // 2
        return y[start:start + n]
    return np.pad(y, (0, n - len(y)))


def save_mel(y, sr, out_path, title):
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=config.N_FFT,
                                         hop_length=config.HOP, n_mels=128)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    img = librosa.display.specshow(librosa.power_to_db(mel, ref=np.max), sr=sr,
                                   hop_length=config.HOP, x_axis="time",
                                   y_axis="mel", ax=ax, cmap="magma")
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    ax.set_title(title)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Predict the genre of an audio file.")
    parser.add_argument("audio", type=Path, help="WAV or MP3 file")
    args = parser.parse_args()
    if not args.audio.exists():
        sys.exit(f"File not found: {args.audio}")

    bundle = joblib.load(config.BEST_MODEL)
    y, sr = librosa.load(args.audio, sr=config.SR, mono=True)
    if len(y) < config.DURATION * sr:
        print(f"Note: file is {len(y) / sr:.1f} s long, padding to 30 s")
    y = middle_30s(y, sr)

    feats = pd.DataFrame([extract_from_array(y, sr)])[bundle["features"]]
    probs = bundle["model"].predict_proba(feats)[0]
    order = np.argsort(probs)[::-1]
    best = bundle["classes"][order[0]]

    print(f"\nFile: {args.audio.name}")
    print(f"Predicted genre: {best.upper()}  ({probs[order[0]]:.1%})\n")
    for i in order:
        bar = "#" * int(round(probs[i] * 40))
        print(f"  {bundle['classes'][i]:10s} {probs[i]:6.1%}  {bar}")

    out = args.audio.with_name(f"{args.audio.stem}_mel.png")
    save_mel(y, sr, out, f"{args.audio.name}: predicted {best} ({probs[order[0]]:.0%})")
    print(f"\nMel spectrogram saved to {out}")


if __name__ == "__main__":
    main()
