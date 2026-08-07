# Public repository preparation audit

Audit date: 2026-08-07

## Source archive

The repository snapshot was derived from the archived `TerraRover_Sim-master.zip` development snapshot together with the frozen paper-analysis artifacts produced on 2026-08-06.

The source archive contained approximately 421 MB of uncompressed `Assets` content and 372 MB of uncompressed training/result history. Most of that material is not required to inspect or reproduce the paper's evaluation claims.

## Included

- current non-deprecated Unity assets, scenes, prefabs, terrain definitions, controllers, and project settings;
- the evaluated `HuskyV3_F3_02` ONNX policy and final-run trainer metadata;
- the exact raw CSV inputs named in the frozen analysis manifest;
- the explicit 100-episode seed mapping;
- the frozen statistical pipeline and its manifest of SHA-256 inputs;
- frozen paper tables/figures and scripts for regenerating quantitative outputs;
- methods/statistical audit records.

## Excluded

- `Assets/ZDeprecated` and nested deprecated-script folders;
- `_Recovery` material;
- obsolete PPO models `V3_F1_02` and `V3_F2_02` from the active-model folder;
- historical training runs and intermediate checkpoints not used by the paper;
- TensorBoard event histories;
- scene-execution timer dumps;
- demonstration-only `pruebaVideo1` CSVs;
- empty/superseded evaluation CSVs, including the header-only historical RL `V3_F3_02` copy;
- Plastic SCM workspace metadata;
- Unity cloud project/organization identifiers;
- machine-specific absolute package paths.

## Dependency normalization

The archived Unity package manifest referenced ML-Agents and URDF Importer through absolute paths on the development computer. The repository replaces those paths with:

- `com.unity.ml-agents`: `4.0.1`;
- `com.unity.robotics.urdf-importer`: official Git URL pinned to `v0.5.2`.

The archived `packages-lock.json` is not published because it encoded the two stale local package sources. Unity should regenerate the lock file from the normalized manifest on first open.

## Integrity checks

- The final ONNX policy in the Unity project, archived run output, and publication copy were byte-identical before cleanup.
- The frozen analysis pipeline completed successfully using the reorganized public raw-data tree and hash-pinned inputs.
- All six generated paper-table CSVs, including the episode-to-seed mapping, were byte-identical to the frozen manuscript inputs.
- Regenerated PNG Figures 2 and 3 were byte-identical to the figures used in the manuscript candidate.
- No API keys, access tokens, private keys, or non-empty password fields were detected by the final text-pattern scan.

## Publication status

- GitHub repository: `https://github.com/aserrano77/TerraRover-Gen`.
- Original TerraRover-Gen source code: MIT License.
- Project-owned data, documentation, figures, frozen-model artifacts, and other non-software research materials: CC BY 4.0.
- Clearpath Husky description assets: original BSD 3-Clause terms retained; see `THIRD_PARTY_NOTICES.md`.
- Remaining step: after the paper release is frozen, archive that release in Zenodo and insert the resulting DOI into the manuscript Data Availability Statement and citation metadata.
