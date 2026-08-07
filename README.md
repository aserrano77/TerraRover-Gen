# TerraRover-Gen

Reproducibility package for the manuscript **“TerraRover-Gen: A Controlled Study of Zero-Shot Terrain-Family Generalization for Rover Navigation.”**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21830588.svg)](https://doi.org/10.5281/zenodo.21830588)

The repository characterizes one frozen PPO rover-navigation policy under controlled terrain-family shifts. It is an evaluation package, not a claim of a new reinforcement-learning algorithm or a universal rover benchmark.

## What is included

- `UnityProject/` — cleaned Unity 6000.3.6f1 project snapshot containing the current evaluation/training scenes, terrain families, rover assets, controllers, and project settings.
- `Models/HuskyV3_F3_02/` — frozen PPO policy used in the paper plus archived trainer configuration and provenance metadata.
- `Data/raw/` — the exact episode-level CSV inputs used by the frozen statistical pipeline.
- `Data/episode_seed_mapping.csv` — explicit episode-to-seed mapping for the 100 paired scenarios.
- `Analysis/` — hash-pinned paper analysis and quantitative figure-generation scripts.
- `Results/tables/` — frozen analysis outputs used to construct the manuscript tables.
- `Results/figures/` — manuscript figures. Figures 2 and 3 are regenerated from the frozen analysis outputs; Figure 1 is the archived terrain montage.
- `Docs/` — statistical and Unity/methods audit records plus reproducibility notes.

Historical checkpoints, deprecated source snapshots, editor caches, video-test CSVs, and empty/superseded datasets are intentionally excluded.

## Frozen policy

The evaluated policy is `Models/HuskyV3_F3_02/frozen_policy.onnx`.

SHA-256:

```text
84c305eb489abc4618f61379f2bcd2cf0b7276609da4e3d741aa1f0050ecc032
```

The archived final ONNX in the original training-results directory, the copy assigned to the Unity evaluation project, and this published copy were verified as byte-identical during repository preparation.

## Reproduce the paper analysis

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r Analysis/requirements.txt
python Analysis/paper_analysis.py
python Analysis/paper_figures.py
```

`paper_analysis.py` verifies SHA-256 hashes, schema, episode indices, and pairing invariants before computing results. It regenerates the CSVs in `Results/tables/`. The quantitative figure script then regenerates Figures 2 and 3 in `Results/figures/`.

## Unity environment

- Unity Editor: 6000.3.6f1
- Unity ML-Agents C# package: 4.0.1
- Unity Robotics URDF Importer: v0.5.2

The original project snapshot referenced ML-Agents and URDF Importer through absolute paths on the development computer. For portability, those two manifest entries are normalized here to the corresponding released package/version. The stale original `packages-lock.json` is therefore intentionally not included; Unity should resolve a fresh lock file from `Packages/manifest.json` on first open.

See `Docs/reproducibility.md` for the experimental provenance boundary and known archival limitations.

## Authors

- Carolina Parreño Rodríguez
- Antonio Serrano (corresponding author, aserrano7@ucam.edu)

## License

Original TerraRover-Gen source code is released under the MIT License. Project-owned data, documentation, figures, frozen-model artifacts, and other non-software research materials are released under the Creative Commons Attribution 4.0 International (CC BY 4.0) license. Third-party material remains under its original license; in particular, the Clearpath Husky description assets retain their BSD 3-Clause terms.

See `LICENSE.md` for the scope of each license and `THIRD_PARTY_NOTICES.md` for third-party attribution.
