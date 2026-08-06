# Frozen statistical analysis manifest — TerraRover-Gen

Target journal: *Robotica*  
Frozen date: 2026-08-06  

## Binding analysis decisions

- Primary unit: one environmental scenario/seed, paired RL–heuristic by episode.
- Six primary success comparisons; exact McNemar with Holm correction across the six.
- Individual success-rate intervals: Wilson 95%.
- Paired success-rate difference intervals: reproducible paired BCa bootstrap 95% (100,000 resamples).
- `Complete`: all 100 raw pairs are primary. The historical 37-pair exclusion is sensitivity only.
- Continuous efficiency outcomes are conditional on joint success. `pasos` is omitted as redundant with time.
- `energia_total` is reported only as a cumulative actuation-effort proxy, not physical energy.
- Failure modes are descriptive in the frozen analysis.
- Physical perturbations and anti-stuck variants are secondary/exploratory, with Holm correction within their stated families.

## Frozen primary result

| Terrain | RL | HEU | Δ pp (RL−HEU) | 95% BCa CI Δ | McNemar p | Holm p |
|---|---:|---:|---:|---:|---:|---:|
| V3_F3_02 | 87/100 (87.0%) | 89/100 (89.0%) | -2.0 | [-10.0, +6.0] | 0.814529 | 1 |
| BigRock | 86/100 (86.0%) | 83/100 (83.0%) | +3.0 | [-5.0, +12.0] | 0.647606 | 1 |
| HardTerrain | 95/100 (95.0%) | 90/100 (90.0%) | +5.0 | [-2.0, +13.0] | 0.301758 | 0.905273 |
| BumpyGround | 31/100 (31.0%) | 70/100 (70.0%) | -39.0 | [-50.0, -27.0] | 7.59716e-09 | 4.5583e-08 |
| Complete | 19/100 (19.0%) | 49/100 (49.0%) | -30.0 | [-40.0, -20.0] | 2.27214e-07 | 1.13607e-06 |
| DeepHoles | 17/100 (17.0%) | 42/100 (42.0%) | -25.0 | [-36.0, -14.0] | 4.12576e-05 | 0.00016503 |

After Holm correction, the terrains with detectable RL–heuristic success differences are: BumpyGround, Complete, DeepHoles.

## Complete sensitivity check

- `raw_primary`: n=100, excluded=0, RL=19.0%, HEU=49.0%, Δ=-30.0 pp, McNemar p=2.27214e-07.
- `historical_filtered_sensitivity`: n=63, excluded=37, RL=28.6%, HEU=76.2%, Δ=-47.6 pp, McNemar p=6.93835e-08.

## Physical-robustness family

- RL V3_F3_02: baseline vs sticky: Δ=+11.0 pp; Holm p=0.0078125.
- RL BumpyGround: baseline vs sticky: Δ=-14.0 pp; Holm p=0.0304046.

## Provenance constraints

- RL V3 baseline is the complete audited copy in `Data/raw/RL/HuskyAgent2_metricas_V3_F3_02.csv`; the historical `results/EvaluationResults/RL` counterpart was header-only.
- Every input used by the pipeline is SHA-256 pinned. Any mismatch stops execution.
- Episode-to-seed mapping is explicitly exported because the historical CSVs contain episode number, not seed value.
- Historical OE8/OE9 JSON summaries are not inputs to this pipeline.

## Scope of inference

The 100 evaluation units are environmental scenarios/seeds for one frozen learned policy, not 100 independent training runs. Results therefore quantify evaluation variability conditional on that learned policy and must not be generalized to PPO or reinforcement learning as algorithm classes.
