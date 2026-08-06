# Reproducibility notes

## Scope

This package supports the evaluation claims of the TerraRover-Gen manuscript. The 100 units per terrain are environmental scenarios generated from predetermined seeds and evaluated with one frozen PPO policy; they are not independent PPO training runs.

## Data provenance

The historical evaluation CSVs record `episodio` rather than the literal procedural seed. `Data/episode_seed_mapping.csv` makes the mapping explicit. The sequence is generated from the original master seed 12345 and is also serialized in the archived Unity evaluation scenes.

The RL baseline file for `V3_F3_02` in the historical `results/EvaluationResults/RL` directory contained only a header. The complete authoritative copy recovered from `Scripts_Analysis/OE9` is published as `Data/raw/RL/HuskyAgent2_metricas_V3_F3_02.csv`; its SHA-256 is pinned in `Analysis/analysis_manifest.json`.

The frozen pipeline treats all 100 `Complete` pairs as primary. The older outcome-dependent 63-pair version is retained only as a sensitivity calculation derived by the pipeline and is not a separate raw dataset.

## Unity snapshot boundary

The public Unity snapshot is cleaned from the archived development project. It excludes `ZDeprecated`, recovery material, scene-execution timer dumps under `Assets/ML-Agents`, obsolete PPO models, training-event histories, and intermediate checkpoints. The compact final-run `timers.json` retained under `Models/` is kept only for training-environment provenance.

Two non-experimental identifiers were removed from the public snapshot: the disabled Unity cloud project/organization identifiers in `ProjectSettings.asset`, and the development-machine prefix from the archived ML-Agents command line in `Models/HuskyV3_F3_02/timers.json`. Package versions, trainer arguments, training metadata, scenes, controllers, terrain definitions, and experiment data are otherwise preserved for the reproducibility scope described here.

The final development snapshot contains some serialized values left over from later perturbation experiments. It is therefore not a one-click historical reconstruction of every baseline and perturbation run simultaneously. Dataset-to-configuration provenance is represented by the frozen CSVs, model/configuration artifacts, scene/code snapshot, and audit documents rather than by assuming that the final Inspector values correspond to every historical run.

## Controller-comparison boundary

The heuristic is a non-learning reference controller under common seeded physical scenarios, not a perfectly interface-matched control condition. It has different state access and a different update frequency from PPO. The published results must not be interpreted as isolating “RL versus rules” as the sole causal difference.

## Statistical regeneration

`Analysis/paper_analysis.py` uses `Analysis/analysis_manifest.json` as the source of truth for:

- primary and secondary datasets;
- SHA-256 input hashes;
- paired episode indexing;
- exact McNemar tests and Holm correction;
- paired BCa bootstrap confidence intervals;
- joint-success continuous-outcome analyses;
- secondary physical-robustness and anti-stuck analyses.

Run from the repository root:

```bash
python Analysis/paper_analysis.py
```

The command fails closed if a raw input does not match its frozen hash or expected schema.
