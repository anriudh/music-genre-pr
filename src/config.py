"""Paths, seeds and audio parameters shared by every step."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw" / "genres"
FEATURES_DIR = ROOT / "data" / "features"
FEATURES_CSV = FEATURES_DIR / "features.csv"
FEATURES_PARTIAL = FEATURES_DIR / "features_partial.csv"
FEATURES_META = FEATURES_DIR / "features_meta.json"
SKIPPED_JSON = ROOT / "data" / "raw" / "skipped.json"
MODELS_DIR = ROOT / "models"
BEST_MODEL = MODELS_DIR / "best_model.joblib"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"

SEED = 42

# audio
SR = 22050
DURATION = 30.0
N_FFT = 2048
HOP = 512
N_MFCC = 20

GENRES = ["blues", "classical", "country", "disco", "hiphop",
          "jazz", "metal", "pop", "reggae", "rock"]

# column prefix for each feature group
GROUPS = {
    "Timbral": "mfcc_",
    "Spectral": "spec_",
    "Rhythm": "rhy_",
    "Chroma": "chroma_",
}
