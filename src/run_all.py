"""Run the whole pipeline: download, features, ablation, plots.

Steps whose output already exists are skipped, so after a fresh clone this
goes straight to the ablation using the committed features.csv.

Run: python -m src.run_all
"""
from src import ablation, config, plots


def main():
    if config.FEATURES_CSV.exists():
        print("features.csv found, skipping download and feature extraction")
    else:
        from src import download, features
        if len(list(config.RAW_DIR.glob("*/*.wav"))) >= 999:
            print("raw audio found, skipping download")
        else:
            download.main()
        features.main()
    ablation.main()
    plots.main()


if __name__ == "__main__":
    main()
