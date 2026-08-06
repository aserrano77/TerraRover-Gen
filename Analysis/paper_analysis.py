#!/usr/bin/env python3
"""Reproducible statistical pipeline for the TerraRover-Gen Robotica paper.

All paper-facing numbers are regenerated from the immutable CSV sources named
and hashed in analysis_manifest.json. Historical OE8/OE9 JSON outputs are never
loaded. The script fails closed if an input hash, schema, episode sequence, or
pairing invariant changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import scipy
from scipy import stats


HERE = Path(__file__).resolve().parent
DEFAULT_MANIFEST = HERE / "analysis_manifest.json"
DEFAULT_PROJECT_ROOT = HERE.parent
DEFAULT_OUTPUT_DIR = HERE.parent / "Results" / "tables"
REQUIRED_COLUMNS = [
    "episodio",
    "resultado",
    "pasos",
    "tiempo_s",
    "distancia_final_m",
    "energia_total",
    "tasa_exito_acum",
]
PRIMARY_TERRAINS = [
    "V3_F3_02",
    "BigRock",
    "HardTerrain",
    "BumpyGround",
    "Complete",
    "DeepHoles",
]
FAILURE_ORDER = ["SUCCESS", "STUCK", "FALL", "COLLISION", "SPIN", "COLLISION_STAY"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_file(project_root: Path, spec: dict) -> Path:
    path = project_root / spec["path"]
    if not path.is_file():
        raise FileNotFoundError(f"Missing manifest input: {path}")
    actual = sha256_file(path)
    if actual != spec["sha256"]:
        raise RuntimeError(
            f"SHA-256 mismatch for {spec['path']}: expected {spec['sha256']}, got {actual}"
        )
    return path


def load_csv(project_root: Path, spec: dict, expected_n: int = 100) -> pd.DataFrame:
    path = verify_file(project_root, spec)
    df = pd.read_csv(path, sep=";")
    if list(df.columns) != REQUIRED_COLUMNS:
        raise RuntimeError(f"Unexpected schema in {spec['path']}: {list(df.columns)}")
    if len(df) != expected_n:
        raise RuntimeError(f"Expected {expected_n} rows in {spec['path']}, found {len(df)}")
    if df["episodio"].tolist() != list(range(1, expected_n + 1)):
        raise RuntimeError(f"Episodes are not exactly 1..{expected_n} in {spec['path']}")
    if df["episodio"].duplicated().any():
        raise RuntimeError(f"Duplicate episode identifiers in {spec['path']}")
    if df[REQUIRED_COLUMNS[1:]].isna().any().any():
        raise RuntimeError(f"Missing values in required columns of {spec['path']}")
    observed = set(df["resultado"].astype(str))
    unknown = observed - set(FAILURE_ORDER)
    if unknown:
        raise RuntimeError(f"Unknown terminal result(s) in {spec['path']}: {sorted(unknown)}")
    return df.set_index("episodio", drop=False)


def validate_csv_internal_consistency(df: pd.DataFrame, label: str) -> None:
    success = (df["resultado"] == "SUCCESS").astype(int)
    expected_acc = success.cumsum() / np.arange(1, len(df) + 1)
    if not np.allclose(df["tasa_exito_acum"].to_numpy(float), expected_acc, atol=5.1e-4):
        raise RuntimeError(f"Cumulative success rate is inconsistent in {label}")
    success_distance = df.loc[df["resultado"] == "SUCCESS", "distancia_final_m"]
    if (success_distance > 2.01).any():
        raise RuntimeError(f"SUCCESS beyond 2.01 m detected in {label}")
    if not np.allclose(df["tiempo_s"], df["pasos"] * 0.01, atol=0.011, rtol=0):
        raise RuntimeError(f"tiempo_s is not consistent with pasos*0.01 in {label}")


def align_pair(a: pd.DataFrame, b: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not a.index.equals(b.index):
        raise RuntimeError("Paired data do not have identical episode indices")
    return a, b


def wilson_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    if n <= 0:
        return (math.nan, math.nan)
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return center - half, center + half


def exact_mcnemar(x: np.ndarray, y: np.ndarray) -> dict:
    x = np.asarray(x, dtype=bool)
    y = np.asarray(y, dtype=bool)
    both_success = int(np.sum(x & y))
    y_only = int(np.sum(~x & y))
    x_only = int(np.sum(x & ~y))
    both_failure = int(np.sum(~x & ~y))
    discordant = y_only + x_only
    p = 1.0 if discordant == 0 else float(
        stats.binomtest(min(y_only, x_only), discordant, p=0.5, alternative="two-sided").pvalue
    )
    return {
        "both_success": both_success,
        "heuristic_only_success": y_only,
        "rl_only_success": x_only,
        "both_failure": both_failure,
        "discordant_pairs": discordant,
        "p": p,
    }


def holm_adjust(pvalues: Iterable[float]) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(list(pvalues), dtype=float)
    m = len(p)
    order = np.argsort(p, kind="mergesort")
    adjusted_sorted = np.empty(m, dtype=float)
    running = 0.0
    for rank, idx in enumerate(order):
        candidate = (m - rank) * p[idx]
        running = max(running, candidate)
        adjusted_sorted[rank] = min(1.0, running)
    adjusted = np.empty(m, dtype=float)
    for rank, idx in enumerate(order):
        adjusted[idx] = adjusted_sorted[rank]
    return adjusted, adjusted < 0.05


def paired_bca_diff_ci(
    x: np.ndarray,
    y: np.ndarray,
    *,
    seed: int,
    n_resamples: int,
    confidence: float = 0.95,
) -> tuple[float, float, float]:
    """Return difference and paired BCa CI for mean(x-y), in proportion units."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.shape != y.shape:
        raise RuntimeError("Paired bootstrap inputs have different shapes")

    def statistic(a: np.ndarray, b: np.ndarray, axis: int = -1) -> np.ndarray:
        return np.mean(a - b, axis=axis)

    result = stats.bootstrap(
        (x, y),
        statistic,
        vectorized=True,
        paired=True,
        n_resamples=n_resamples,
        batch=10000,
        confidence_level=confidence,
        method="BCa",
        rng=np.random.default_rng(seed),
    )
    return float(np.mean(x - y)), float(result.confidence_interval.low), float(result.confidence_interval.high)


def quartiles(values: np.ndarray) -> tuple[float, float, float]:
    q1, median, q3 = np.quantile(np.asarray(values, dtype=float), [0.25, 0.5, 0.75])
    return float(q1), float(median), float(q3)


def matched_rank_biserial(x: np.ndarray, y: np.ndarray) -> float:
    """Matched-pairs rank-biserial correlation for differences x-y, excluding zeros."""
    d = np.asarray(x, dtype=float) - np.asarray(y, dtype=float)
    d = d[d != 0]
    if len(d) == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(d), method="average")
    pos = float(ranks[d > 0].sum())
    neg = float(ranks[d < 0].sum())
    total = pos + neg
    return (pos - neg) / total if total else 0.0


def load_primary(manifest: dict, project_root: Path) -> dict[str, tuple[pd.DataFrame, pd.DataFrame]]:
    pairs = {}
    for terrain in PRIMARY_TERRAINS:
        spec = manifest["primary_datasets"][terrain]
        rl = load_csv(project_root, spec["rl"])
        heu = load_csv(project_root, spec["heuristic"])
        validate_csv_internal_consistency(rl, f"{terrain}/RL")
        validate_csv_internal_consistency(heu, f"{terrain}/HEU")
        pairs[terrain] = align_pair(rl, heu)
    return pairs


def primary_results(manifest: dict, pairs: dict) -> pd.DataFrame:
    design = manifest["design"]
    rows = []
    for i, terrain in enumerate(PRIMARY_TERRAINS):
        rl, heu = pairs[terrain]
        sr = (rl["resultado"] == "SUCCESS").to_numpy()
        sh = (heu["resultado"] == "SUCCESS").to_numpy()
        n = len(sr)
        nr, nh = int(sr.sum()), int(sh.sum())
        rl_ci = wilson_ci(nr, n)
        heu_ci = wilson_ci(nh, n)
        diff, dlo, dhi = paired_bca_diff_ci(
            sr,
            sh,
            seed=int(design["paired_difference_bootstrap_seed"]) + i,
            n_resamples=int(design["paired_difference_bootstrap_resamples"]),
        )
        mc = exact_mcnemar(sr, sh)
        rows.append({
            "terrain": terrain,
            "n_pairs": n,
            "rl_success_n": nr,
            "rl_success_pct": nr / n * 100,
            "rl_wilson95_low_pct": rl_ci[0] * 100,
            "rl_wilson95_high_pct": rl_ci[1] * 100,
            "heuristic_success_n": nh,
            "heuristic_success_pct": nh / n * 100,
            "heuristic_wilson95_low_pct": heu_ci[0] * 100,
            "heuristic_wilson95_high_pct": heu_ci[1] * 100,
            "diff_rl_minus_heuristic_pp": diff * 100,
            "diff_bca95_low_pp": dlo * 100,
            "diff_bca95_high_pp": dhi * 100,
            "both_success_n": mc["both_success"],
            "heuristic_only_success_n": mc["heuristic_only_success"],
            "rl_only_success_n": mc["rl_only_success"],
            "both_failure_n": mc["both_failure"],
            "discordant_pairs_n": mc["discordant_pairs"],
            "mcnemar_exact_p": mc["p"],
        })
    out = pd.DataFrame(rows)
    out["mcnemar_holm_p"] , reject = holm_adjust(out["mcnemar_exact_p"])
    out["mcnemar_holm_reject_0_05"] = reject
    return out


def failure_results(pairs: dict) -> pd.DataFrame:
    rows = []
    for terrain in PRIMARY_TERRAINS:
        rl, heu = pairs[terrain]
        for system, df in [("RL", rl), ("HEU", heu)]:
            counts = df["resultado"].value_counts()
            row = {"terrain": terrain, "system": system, "n": len(df)}
            for result in FAILURE_ORDER:
                n = int(counts.get(result, 0))
                row[f"{result.lower()}_n"] = n
                row[f"{result.lower()}_pct"] = n / len(df) * 100
            rows.append(row)
    return pd.DataFrame(rows)


def continuous_results(manifest: dict, pairs: dict) -> pd.DataFrame:
    rows = []
    labels = manifest["design"]["continuous_outcome_labels"]
    for terrain in PRIMARY_TERRAINS:
        rl, heu = pairs[terrain]
        both = (rl["resultado"] == "SUCCESS") & (heu["resultado"] == "SUCCESS")
        for outcome in manifest["design"]["continuous_outcomes"]:
            x = rl.loc[both, outcome].to_numpy(float)
            y = heu.loc[both, outcome].to_numpy(float)
            q1x, medx, q3x = quartiles(x)
            q1y, medy, q3y = quartiles(y)
            if np.allclose(x, y):
                statistic, p = 0.0, 1.0
            else:
                w = stats.wilcoxon(x, y, zero_method="wilcox", alternative="two-sided", method="auto")
                statistic, p = float(w.statistic), float(w.pvalue)
            rows.append({
                "terrain": terrain,
                "outcome": outcome,
                "outcome_label": labels[outcome],
                "n_both_success": len(x),
                "rl_median": medx,
                "rl_q1": q1x,
                "rl_q3": q3x,
                "heuristic_median": medy,
                "heuristic_q1": q1y,
                "heuristic_q3": q3y,
                "median_paired_diff_rl_minus_heuristic": float(np.median(x - y)),
                "wilcoxon_statistic": statistic,
                "wilcoxon_p": p,
                "rank_biserial_rl_minus_heuristic": matched_rank_biserial(x, y),
            })
    out = pd.DataFrame(rows)
    out["wilcoxon_holm_p_within_outcome"] = np.nan
    out["wilcoxon_holm_reject_0_05"] = False
    for outcome in manifest["design"]["continuous_outcomes"]:
        mask = out["outcome"] == outcome
        adj, reject = holm_adjust(out.loc[mask, "wilcoxon_p"])
        out.loc[mask, "wilcoxon_holm_p_within_outcome"] = adj
        out.loc[mask, "wilcoxon_holm_reject_0_05"] = reject
    return out


def variant_comparison(
    baseline: pd.DataFrame,
    variant: pd.DataFrame,
    *,
    family: str,
    comparison: str,
    system: str,
    terrain: str,
    variant_name: str,
) -> dict:
    baseline, variant = align_pair(baseline, variant)
    sb = (baseline["resultado"] == "SUCCESS").to_numpy()
    sv = (variant["resultado"] == "SUCCESS").to_numpy()
    mc = exact_mcnemar(sb, sv)
    n = len(sb)
    nb, nv = int(sb.sum()), int(sv.sum())
    return {
        "family": family,
        "comparison": comparison,
        "system": system,
        "terrain": terrain,
        "variant": variant_name,
        "n_pairs": n,
        "baseline_success_n": nb,
        "baseline_success_pct": round(nb / n * 100, 12),
        "variant_success_n": nv,
        "variant_success_pct": round(nv / n * 100, 12),
        "diff_variant_minus_baseline_pp": round((nv - nb) / n * 100, 12),
        "mcnemar_exact_p": mc["p"],
        "both_success_n": mc["both_success"],
        "baseline_only_success_n": mc["rl_only_success"],
        "variant_only_success_n": mc["heuristic_only_success"],
        "both_failure_n": mc["both_failure"],
    }


def secondary_results(manifest: dict, project_root: Path, pairs: dict) -> pd.DataFrame:
    rows = []
    phys = manifest["physical_robustness_datasets"]
    for system in ["RL", "HEU"]:
        for terrain, key_terrain in [("V3_F3_02", "V3"), ("BumpyGround", "BumpyGround")]:
            baseline = pairs[terrain][0 if system == "RL" else 1]
            for variant, label in [("sticky", "high-friction material configuration"), ("fl2000", "force-limit 2000")]:
                spec = phys[f"{system}_{key_terrain}_{variant}"]
                df = load_csv(project_root, spec)
                validate_csv_internal_consistency(df, f"{system}/{terrain}/{variant}")
                rows.append(variant_comparison(
                    baseline, df,
                    family="physical_robustness_8",
                    comparison=f"{system} {terrain}: baseline vs {variant}",
                    system=system,
                    terrain=terrain,
                    variant_name=label,
                ))

    anti = manifest["anti_stuck_datasets"]
    for key, spec in anti.items():
        terrain = spec["baseline_terrain"]
        baseline = pairs[terrain][0]
        df = load_csv(project_root, spec)
        validate_csv_internal_consistency(df, f"RL/{key}")
        rows.append(variant_comparison(
            baseline, df,
            family="anti_stuck_2",
            comparison=f"RL {terrain}: baseline vs {key}",
            system="RL",
            terrain=terrain,
            variant_name=key,
        ))

    out = pd.DataFrame(rows)
    out["mcnemar_holm_p_within_family"] = np.nan
    out["mcnemar_holm_reject_0_05"] = False
    for family in out["family"].unique():
        mask = out["family"] == family
        adj, reject = holm_adjust(out.loc[mask, "mcnemar_exact_p"])
        out.loc[mask, "mcnemar_holm_p_within_family"] = adj
        out.loc[mask, "mcnemar_holm_reject_0_05"] = reject
    return out


def complete_sensitivity(pairs: dict) -> pd.DataFrame:
    rl, heu = pairs["Complete"]
    rl_bad = (rl["resultado"] == "FALL") & (rl["pasos"] <= 50)
    heu_bad = (heu["resultado"] == "FALL") & (heu["pasos"] <= 50)
    excluded = rl_bad | heu_bad
    rows = []
    for label, keep in [("raw_primary", ~pd.Series(False, index=rl.index)), ("historical_filtered_sensitivity", ~excluded)]:
        r, h = rl.loc[keep], heu.loc[keep]
        sr = (r["resultado"] == "SUCCESS").to_numpy()
        sh = (h["resultado"] == "SUCCESS").to_numpy()
        mc = exact_mcnemar(sr, sh)
        n = len(r)
        nr, nh = int(sr.sum()), int(sh.sum())
        rows.append({
            "analysis": label,
            "n_pairs": n,
            "excluded_pairs": len(rl) - n,
            "rl_success_n": nr,
            "rl_success_pct": nr / n * 100,
            "heuristic_success_n": nh,
            "heuristic_success_pct": nh / n * 100,
            "diff_rl_minus_heuristic_pp": (nr - nh) / n * 100,
            "mcnemar_exact_p": mc["p"],
        })
    return pd.DataFrame(rows)


def seed_mapping(manifest: dict) -> pd.DataFrame:
    seeds = manifest["seed_provenance"]["episode_seeds"]
    if len(seeds) != 100 or len(set(seeds)) != 100:
        raise RuntimeError("Manifest must contain exactly 100 unique episode seeds")
    return pd.DataFrame({"episodio": range(1, 101), "episode_seed": seeds})


def write_markdown_summary(
    path: Path,
    manifest: dict,
    primary: pd.DataFrame,
    secondary: pd.DataFrame,
    sensitivity: pd.DataFrame,
) -> None:
    sig = primary.loc[primary["mcnemar_holm_reject_0_05"], "terrain"].tolist()
    phys_sig = secondary.loc[
        (secondary["family"] == "physical_robustness_8") & secondary["mcnemar_holm_reject_0_05"],
        ["comparison", "diff_variant_minus_baseline_pp", "mcnemar_holm_p_within_family"],
    ]
    lines = [
        "# Frozen statistical analysis manifest — TerraRover-Gen",
        "",
        f"Target journal: *{manifest['paper_target']}*  ",
        f"Frozen date: {manifest['analysis_frozen_date']}  ",
        "",
        "## Binding analysis decisions",
        "",
        "- Primary unit: one environmental scenario/seed, paired RL–heuristic by episode.",
        "- Six primary success comparisons; exact McNemar with Holm correction across the six.",
        "- Individual success-rate intervals: Wilson 95%.",
        "- Paired success-rate difference intervals: reproducible paired BCa bootstrap 95% (100,000 resamples).",
        "- `Complete`: all 100 raw pairs are primary. The historical 37-pair exclusion is sensitivity only.",
        "- Continuous efficiency outcomes are conditional on joint success. `pasos` is omitted as redundant with time.",
        "- `energia_total` is reported only as a cumulative actuation-effort proxy, not physical energy.",
        "- Failure modes are descriptive in the frozen analysis.",
        "- Physical perturbations and anti-stuck variants are secondary/exploratory, with Holm correction within their stated families.",
        "",
        "## Frozen primary result",
        "",
        "| Terrain | RL | HEU | Δ pp (RL−HEU) | 95% BCa CI Δ | McNemar p | Holm p |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in primary.iterrows():
        lines.append(
            f"| {r.terrain} | {int(r.rl_success_n)}/100 ({r.rl_success_pct:.1f}%) | "
            f"{int(r.heuristic_success_n)}/100 ({r.heuristic_success_pct:.1f}%) | "
            f"{r.diff_rl_minus_heuristic_pp:+.1f} | "
            f"[{r.diff_bca95_low_pp:+.1f}, {r.diff_bca95_high_pp:+.1f}] | "
            f"{r.mcnemar_exact_p:.6g} | {r.mcnemar_holm_p:.6g} |"
        )
    lines.extend([
        "",
        f"After Holm correction, the terrains with detectable RL–heuristic success differences are: {', '.join(sig)}.",
        "",
        "## Complete sensitivity check",
        "",
    ])
    for _, r in sensitivity.iterrows():
        lines.append(
            f"- `{r.analysis}`: n={int(r.n_pairs)}, excluded={int(r.excluded_pairs)}, "
            f"RL={r.rl_success_pct:.1f}%, HEU={r.heuristic_success_pct:.1f}%, "
            f"Δ={r.diff_rl_minus_heuristic_pp:+.1f} pp, McNemar p={r.mcnemar_exact_p:.6g}."
        )
    lines.extend(["", "## Physical-robustness family", ""])
    if len(phys_sig):
        for _, r in phys_sig.iterrows():
            lines.append(
                f"- {r.comparison}: Δ={r.diff_variant_minus_baseline_pp:+.1f} pp; "
                f"Holm p={r.mcnemar_holm_p_within_family:.6g}."
            )
    else:
        lines.append("- No physical-robustness comparison remains detectable after Holm correction.")
    lines.extend([
        "",
        "## Provenance constraints",
        "",
        "- RL V3 baseline is the complete audited copy in `Data/raw/RL/HuskyAgent2_metricas_V3_F3_02.csv`; the historical `results/EvaluationResults/RL` counterpart was header-only.",
        "- Every input used by the pipeline is SHA-256 pinned. Any mismatch stops execution.",
        "- Episode-to-seed mapping is explicitly exported because the historical CSVs contain episode number, not seed value.",
        "- Historical OE8/OE9 JSON summaries are not inputs to this pipeline.",
        "",
        "## Scope of inference",
        "",
        "The 100 evaluation units are environmental scenarios/seeds for one frozen learned policy, not 100 independent training runs. Results therefore quantify evaluation variability conditional on that learned policy and must not be generalized to PPO or reinforcement learning as algorithm classes.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=DEFAULT_PROJECT_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    project_root = args.project_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Pin the seed source itself, then validate all data files as they are loaded.
    seed_spec = {
        "path": manifest["seed_provenance"]["source_path"],
        "sha256": manifest["seed_provenance"]["source_sha256"],
    }
    verify_file(project_root, seed_spec)
    for spec in manifest["seed_provenance"].get("corroborating_sources", []):
        verify_file(project_root, spec)

    pairs = load_primary(manifest, project_root)
    primary = primary_results(manifest, pairs)
    failures = failure_results(pairs)
    continuous = continuous_results(manifest, pairs)
    secondary = secondary_results(manifest, project_root, pairs)
    sensitivity = complete_sensitivity(pairs)
    seeds = seed_mapping(manifest)

    outputs = {
        "paper_results_primary.csv": primary,
        "paper_results_failure_modes.csv": failures,
        "paper_results_continuous.csv": continuous,
        "paper_results_secondary.csv": secondary,
        "paper_results_complete_sensitivity.csv": sensitivity,
        "episode_seed_mapping.csv": seeds,
    }
    for name, df in outputs.items():
        # Preserve full precision in source tables; round only for paper presentation.
        df.to_csv(output_dir / name, index=False)

    provenance = {
        "manifest_sha256": sha256_file(args.manifest.resolve()),
        "project_root": str(project_root),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "outputs_sha256": {name: sha256_file(output_dir / name) for name in outputs},
    }
    (output_dir / "run_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    write_markdown_summary(output_dir / "analysis_manifest.md", manifest, primary, secondary, sensitivity)

    print("TerraRover-Gen paper analysis completed successfully.")
    print(f"Outputs: {output_dir}")
    print(primary[[
        "terrain", "rl_success_pct", "heuristic_success_pct", "diff_rl_minus_heuristic_pp",
        "diff_bca95_low_pp", "diff_bca95_high_pp", "mcnemar_exact_p", "mcnemar_holm_p"
    ]].to_string(index=False))


if __name__ == "__main__":
    main()
