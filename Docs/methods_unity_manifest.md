# Frozen Unity/Methods manifest — TerraRover-Gen

Target journal: *Robotica*  
Frozen date: 2026-08-06  
Scope: methodological parameters verified directly from the archived Unity project and run metadata. This file supersedes contradictory descriptive values in the TFG where explicitly noted below.

## 1. Software and physics stack

| Item | Frozen value | Evidence / interpretation |
|---|---|---|
| Unity Editor | `6000.3.6f1` (`bbb010bdb8a3`) | `ProjectSettings/ProjectVersion.txt` |
| Unity ML-Agents C# package | `4.0.1` | Unity timer metadata (`com.unity.ml-agents_version`) |
| Python | `3.10.12` (Anaconda, 64-bit Windows) | final `HuskyV3_F3_02/run_logs/timers.json` |
| ML-Agents Python trainer | `1.2.0.dev0` | final run timer/training-status metadata |
| `mlagents_envs` | `1.2.0.dev0` | final run timer metadata |
| PyTorch | `2.5.1+cu121` | final run timer/training-status metadata |
| NumPy | `1.23.5` | final run timer metadata |
| Fixed timestep | nominal `0.01 s` (~100 Hz) | Unity serializes `1411199 / 141120000 = 0.0099999929 s` |
| Physics solver | TGS (`m_SolverType: 1`) | `ProjectSettings/DynamicsManager.asset` |
| Solver iterations | 20 position, 1 velocity | `DynamicsManager.asset` |
| Gravity | `(0, -9.81, 0) m/s^2` | `DynamicsManager.asset` |

Do **not** write simply “ML-Agents 4.0” in the paper: the Unity C# package and Python trainer use different version identifiers in the preserved run metadata (`4.0.1` and `1.2.0.dev0`, respectively).

## 2. RL policy input and control cadence

### Manual/vector observations

`HuskyAgent2.CollectObservations()` contributes 16 scalar values per observation step:

| Block | Values | Dim. | Normalization / frame |
|---|---|---:|---|
| Chassis orientation | `transform.up` | 3 | world-axis components |
| Chassis heading | `transform.forward` | 3 | world-axis components |
| Linear velocity | local `baseLink.linearVelocity` | 3 | divided by `maxLinearSpeed=1.5`, magnitude clamped to 1 |
| Angular velocity | local `baseLink.angularVelocity` | 3 | divided by `maxAngularSpeed=2`, magnitude clamped to 1 |
| Target direction | normalized direction to target, transformed to local frame | 3 | unit direction |
| Target distance | Euclidean distance / 100 | 1 | clamped to `[0,1]` |
| **Total** | | **16** | |

`BehaviorParameters` serializes `VectorObservationSize=16` and `NumStackedVectorObservations=3`, so the effective stacked vector component is **48 scalars**.

Important wording correction: `transform.up` and `transform.forward` themselves are world-axis vectors, not local-frame/invariant representations. The local velocity and target-direction terms are explicitly transformed into the rover frame.

### RayPerception sensors used by RL

Both sensor GameObjects are active in `Environment.prefab`, and `BehaviorParameters.m_UseChildSensors=1`.

| Parameter | FrontalVision | FloorVision |
|---|---:|---:|
| Sensor GameObject | `Sensor_LidarFrontal` | `Sensor_LidarFloor` |
| Detectable tag | `Obstacle` | `Terrain` |
| Rays per direction | 7 | 7 |
| Total rays | 15 | 15 |
| Max ray degrees | 70° each side (140° total) | 70° each side (140° total) |
| Sphere-cast radius | 0.25 m | 0.05 m |
| Ray length | 8 m | 4 m |
| Observation stacks | 1 | 1 |
| Local position | `(0, 0.33, 0.492)` | `(0, 0.33, 0.37)` |
| Local rotation | 0° | +30° about X |

Under ML-Agents 4.0, a ray sensor contributes
`ObservationStacks × (1 + 2 × RaysPerDirection) × (NumDetectableTags + 2)` values. With one detectable tag, each of these sensors therefore contributes `1 × 15 × 3 = 45` scalars. The two ray sensors contribute **90 scalars** in total. Together with the 48 stacked vector scalars, the RL policy receives **138 observation scalars per decision**, exposed as three observation streams (stacked vector + frontal ray sensor + floor ray sensor).

The three values associated with each ray are not merely a binary hit and distance: they comprise the one-hot detectable-tag slot (one tag here), a miss/hit-anything indicator, and the normalized hit distance. This follows the ML-Agents 4.0 ray-observation specification: <https://docs.unity3d.com/Packages/com.unity.ml-agents@4.0/manual/Learning-Environment-Design-Agents.html>.

### RL control cadence

The RL agent has two continuous actions (linear-motion and turning commands). `DecisionRequester` is serialised as `DecisionPeriod=5` and `TakeActionsBetweenDecisions=1`. With the ~0.01 s physics step, the network therefore produces a new action every **0.05 s (~20 Hz)** and Unity holds/reapplies actions between decisions.

## 3. Heuristic controller: actual information used

The TFG statement that the heuristic “receives the same 48-dimensional vector and both LiDAR sensors” is **not supported by the implementation and must not be repeated in the paper**.

`HuskyHeuristic` executes explicit rules from:

- target heading error computed from rover pose and target position in the horizontal plane;
- chassis tilt `1 - transform.up.y`, used to reduce speed on slopes;
- 15 manually issued frontal `Physics.SphereCast` queries with the same frontal geometry as the RL `FrontalVision` sensor: 7 rays per side + central ray, ±70°, radius 0.25 m, length 8 m, `Obstacle` tag filtering;
- internal reorientation/hysteresis state.

The heuristic prefab does contain `Sensor_LidarFrontal` and `Sensor_LidarFloor` components, but both GameObjects are serialised **inactive** (`m_IsActive: 0`). The heuristic logic does not consume the RL 16/48-dimensional observation vector and does not use the floor `RayPerception` sensor for control.

The commonality that can safely be claimed is narrower: both controllers operate the same Husky/ArticulationBody platform and use the same target/scenario generation; the heuristic reproduces the **frontal obstacle-sensing geometry** in its own `SphereCast` routine. Their policy inputs are not identical.

### Heuristic control cadence

`HuskyHeuristic.FixedUpdate()` recomputes its command every physics step, i.e. **~100 Hz**, whereas RL decisions are ~20 Hz. This is a real implementation asymmetry and should be disclosed as a threat to strict controller parity.

## 4. Evaluation seeds and paired scenarios

The seed list is reproducible from code rather than merely copied from a scene:

```text
masterSeed = 12345
rng = new System.Random(masterSeed)
for i = 0..99:
    seed[i] = rng.Next(1, 1000000)
```

The resulting 100-element list is unique. It begins:

```text
66747, 70160, 774765, 511139, 797490, 827308, 165959, 736130, 260217, 506005, ...
```

and ends:

```text
..., 935319, 553248, 271016, 391649, 293502, 111369, 254993, 463381, 615514
```

The list regenerated from the `System.Random` algorithm matches the serialised list element-for-element. `SampleScene.unity` preserves two complete identical 100-seed lists, one on the RL prefab instance and one on the heuristic prefab instance. `EvaluationRL.unity` preserves another complete copy of the same list. The frozen statistical pipeline maps episode `1..100` to this sequence.

For each episode, `TerrainGenerator4.GenerateTerrain(currentSeed)` calls `UnityEngine.Random.InitState(currentSeed)` before generating height-field offsets and obstacle placement. The subsequent rover yaw and target position are drawn from the same reset Unity RNG stream. Thus, for the same terrain configuration and seed, both controller implementations follow the same deterministic scenario-generation sequence (terrain/obstacles, initial yaw, and target placement).

Traceability limitation: the historical CSVs record `episodio` rather than the literal seed value. The episode→seed mapping therefore requires the archived project/manifest; it is not self-contained in each CSV.

## 5. Effective episode-termination conditions

There is **no fixed episode step limit** in the preserved RL prefab (`MaxStep=0`) and no separate time-out condition in either controller. Effective terminal outcomes are:

| Outcome | Effective implementation | RL | Heuristic |
|---|---|---|---|
| `SUCCESS` | Euclidean rover→target distance `<= 2.0 m` | yes | yes |
| `FALL` | `transform.up.y < 0.2` **or** rover Y < terrain origin Y − 5 m | yes | yes |
| `SPIN` | checked every 100 physics steps; net displacement < 0.5 m and net rotation >=45°; 3 consecutive spin checks | yes | yes |
| `STUCK` | checked every 100 physics steps; net displacement < 0.5 m and net rotation <45°; 5 consecutive stuck checks | yes | yes |
| `COLLISION` | `OnCollisionEnter` with a GameObject tagged `Obstacle` | yes | yes |
| `COLLISION_STAY` | `OnCollisionStay` with `Obstacle` | no | yes |

At the frozen timestep, the anti-stuck check interval is ~**1 s**, not ~2 s. Consecutive `SPIN` and `STUCK` thresholds therefore correspond nominally to ~3 s and ~5 s of their respective condition, although a counter resets when the other movement category occurs.

### Critical correction: unused serialized anti-stuck fields

Both prefabs serialise `stuckRadiusThreshold=0.05`, and the RL script even retains a default `0.1`; however, **the terminal code never reads `stuckRadiusThreshold`**. Both controllers instead use the hard-coded comparison `netDistanceMoved >= 0.5f`. Likewise the RL field `minSpinAngle=2` is not used in the terminal classification; the implemented angle threshold is hard-coded at 45°.

Therefore Methods must report **0.5 m displacement / 45° rotation**, not the TFG's “0.05 m” anti-stuck criterion. The historical narrative that lowering `stuckRadiusThreshold` from 0.1 to 0.05 changed the final anti-stuck classifier is not supported by this archived implementation.

The heuristic has an additional `OnCollisionStay` fallback not present in RL. No `COLLISION_STAY` outcome appears in the six primary datasets, so this asymmetry is observable in code but did not create a recorded outcome category in the primary results.

## 6. Corrections that are binding for the paper

The following TFG formulations are superseded:

1. **Do not say “identical observations” or “same 48-dimensional vector”.** RL and heuristic use different control inputs; only the platform, scenario generation, and frontal obstacle-sensing geometry are common.
2. **Do not say anti-stuck checks occur every ~2 s / 50 Hz.** Physics is ~100 Hz and checks occur every 100 physics steps (~1 s).
3. **Do not describe the implemented stuck threshold as 0.05 m.** The executed code uses 0.5 m; the 0.05 field is dead configuration.
4. **Do not say `COLLISION` necessarily includes terrain boundaries.** The code terminates collision episodes on objects tagged `Obstacle`; boundary behavior should not be broadened without separate evidence.
5. **Do not imply equal control update rates.** RL decisions are ~20 Hz; heuristic commands are recomputed ~100 Hz.
6. **Do not conflate ML-Agents package versions.** Preserve C# package `4.0.1` versus Python trainer `1.2.0.dev0`.
7. **Do not describe each RL ray as a two-value observation.** With one detectable tag, ML-Agents emits three values per ray; the two 15-ray sensors contribute 90 scalars, making the full RL observation 138 scalars per decision (48 stacked vector + 90 ray).

## 7. Configuration/provenance caveats to carry into Methods or Threats to Validity

- The current project snapshot is not a one-click reconstruction of every historical perturbation: some source values reflect later sensitivity runs (e.g. heuristic motor `forceLimit=2000` while the RL script currently uses 1000). Baseline physical parameters should therefore be tied to dataset/run provenance rather than inferred from the final source snapshot alone.
- `Packages/manifest.json` references ML-Agents and URDF Importer through local Windows paths. The exact ML-Agents C# version is nevertheless recoverable from Unity timer metadata; the exact URDF Importer revision is not recoverable from the package manifest alone.
- The paired-seed design is strongly supported by the common serialized lists and deterministic generation code, but seed values were not written into the historical CSV rows.
- Evaluation variability is conditional on one frozen trained policy; it is not variability across independent PPO training runs (already frozen in the statistical manifest).

## 8. Paper-ready minimum statement (for later Methods drafting)

> Experiments were conducted in Unity 6000.3.6f1 with the Unity ML-Agents C# package 4.0.1 and a 0.01-s physics timestep (approximately 100 Hz). The frozen RL policy was trained with the ML-Agents Python trainer 1.2.0.dev0 under Python 3.10.12 and PyTorch 2.5.1+cu121. The RL controller combined a 16-variable vector observation stacked over three decision instants (48 scalars) with two 15-ray perception sensors (45 scalars each), for 138 observation scalars per decision: a frontal obstacle sensor (±70°, 8 m, 0.25-m sphere-cast radius) and a downward-oriented terrain sensor (±70°, 4 m, 0.05-m radius). RL actions were updated every five physics steps (~20 Hz). The deterministic heuristic operated on the same rover and paired procedurally generated scenarios, using target heading, chassis tilt, and a manually reproduced 15-ray frontal obstacle geometry; it recomputed commands at each physics step (~100 Hz). Evaluation used 100 seeds generated from `System.Random(12345)` and applied in the same order to both controllers. Episodes terminated on success (target distance ≤2 m), fall/rollover, obstacle collision, or repeated no-progress/spin conditions evaluated at 100-step intervals.

This paragraph is a factual seed for Methods, not final journal prose; the controller-cadence and observation asymmetries should also be discussed explicitly under threats to validity.

## 9. Evidence hashes

SHA-256 values for the inspected archived files:

```text
ProjectSettings/ProjectVersion.txt              591d7239c0288ad3ed6c5631840a838f99726c79d92f2fa840f77db8490d448d
ProjectSettings/TimeManager.asset               a319a2254c2ea1c6f8723890e9f4ce16b272290fb398187e717e4465de87a0ab
ProjectSettings/DynamicsManager.asset           4929a465b74ee9e41ef0ae3ea49628e53f09eb611d9371589bb7e754a0c04d4d
Assets/Scripts/Agent/HuskyAgent2.cs             1d45b14f1a845ff71149a97bedf68fbfa99fa0013c0393061889f152fbb8e385
Assets/Scripts/Agent/HuskyHeuristic.cs          bb94664d406bf63076e13f9889b2a61cdac1e972528616fe7635bbda68c8b32b
Assets/Scripts/Terrain/TerrainGenerator4.cs     fc2dcecff84648673fa94bb39fafcd46e29b2c0ba41e8e993bb405211d90d28c
Assets/Prefabs/Environment.prefab               0e3e3b0774915767872b45b4907f9ad5fc2d4bcd4d8101ad2be77cd5d014ccf8
Assets/Prefabs/Heuristic.prefab                 8e42eb431bfbcfbbe711f1689230aeb11a6b5b77de79e9f15c8919763837554f
Assets/Scenes/SampleScene.unity                  d9f0eaf4d82f2f654dbf1f7e2c2dc62875a54070a3ac8b88f365548c97b4b1a8
Assets/Scenes/EvaluationRL.unity                 e1f40edb90fffc63219a196e3690e197d66f7f3b13ba945ebe53769b62932c18
Assets/ML-Agents/Timers/EvaluationRL_timers.json e35de8c4c192b1a9e8d8536016080350afc96a446faa98bd1f96a0d59d6356ff
paper_analysis/output/episode_seed_mapping.csv   304e75d1c5b19ec4acbdd4c7436403f7ace4320bceeda1824c725dfe0cb70250
```
