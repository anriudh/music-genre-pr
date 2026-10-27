"""Download GTZAN from a Hugging Face parquet mirror and write it out as wav files.

The mirror (sanchit-gandhi/gtzan) stores the original audio bytes, so we decode
them ourselves, resample to 22050 Hz mono and save one wav per clip under
data/raw/genres/<genre>/. Clips that fail to decode are skipped and logged.

Run: python -m src.download
"""
import io
import json
import re
from collections import Counter
from pathlib import Path

import librosa
import numpy as np
import pyarrow.parquet as pq
import soundfile as sf
from huggingface_hub import snapshot_download
from tqdm import tqdm

from src import config

REPO_ID = "sanchit-gandhi/gtzan"
CACHE_DIR = config.ROOT / "data" / "raw" / "hf_cache"


def clip_name(path_str):
    """Turn the mirror's file path into the usual 'blues.00000' style name."""
    m = re.search(r"([a-z]+)\.(\d{5})", path_str or "")
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    return None


def decode_audio(audio_bytes):
    """Decode raw audio bytes to a 22050 Hz mono float32 array."""
    y, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=True)
    y = y.mean(axis=1)
    if sr != config.SR:
        y = librosa.resample(y, orig_sr=sr, target_sr=config.SR)
    if y.size == 0 or not np.isfinite(y).all():
        raise ValueError("empty or non finite audio")
    return y


def main():
    local = snapshot_download(REPO_ID, repo_type="dataset", cache_dir=CACHE_DIR,
                              allow_patterns=["data/*.parquet"])
    shards = sorted((Path(local) / "data").glob("*.parquet"))
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)

    written, skipped = Counter(), []
    for shard in shards:
        table = pq.read_table(shard)
        rows = table.to_pylist()
        for row in tqdm(rows, desc=shard.name):
            genre = config.GENRES[row["genre"]]
            name = clip_name(row.get("file") or row["audio"].get("path"))
            if name is None:
                name = f"{genre}.unknown{sum(written.values()):04d}"
            out = config.RAW_DIR / genre / f"{name}.wav"
            if out.exists():
                written[genre] += 1
                continue
            try:
                y = decode_audio(row["audio"]["bytes"])
            except Exception as e:  # corrupted clip, log it and move on
                skipped.append({"clip": name, "error": str(e)})
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            sf.write(out, y, config.SR)
            written[genre] += 1

    # clips that the mirror never had (jazz.00054 is the usual one)
    for g in config.GENRES:
        for i in range(100):
            name = f"{g}.{i:05d}"
            if not (config.RAW_DIR / g / f"{name}.wav").exists() and \
                    name not in {s["clip"] for s in skipped}:
                skipped.append({"clip": name, "error": "missing from mirror"})

    print("\nClips per genre:")
    for g in config.GENRES:
        print(f"  {g:10s} {written[g]}")
    print(f"  total      {sum(written.values())}")
    if skipped:
        print("Skipped:", [s["clip"] for s in skipped])
    config.SKIPPED_JSON.write_text(json.dumps(skipped, indent=2))


if __name__ == "__main__":
    main()
