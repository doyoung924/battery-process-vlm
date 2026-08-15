"""1차 시도의 학습 run 이력을 하나의 CSV로 회수한다.

experiments/legacy_runs/ 에는 ultralytics 가 남긴 run 디렉터리가 흩어져 있다.
각 run 의 results.csv(에폭별 지표) + args.yaml(하이퍼파라미터)을 합쳐
"어떤 설정으로 무엇을 얻었는가" 표를 만든다.

이 표가 진단의 출발점이다. mAP50 이 0.99대인 run 과 0.5~0.7 대인 run 이
갈리는데, 그 차이가 모델이 아니라 **데이터 분할 방식**에서 온다는 것이 가설이다.
따라서 data 경로도 함께 기록해 추적할 수 있게 한다.
"""

import argparse
import csv
from pathlib import Path

# results.csv 헤더는 ultralytics 버전에 따라 공백이 붙는 경우가 있다
METRIC_COLUMNS = {
    "mAP50": "metrics/mAP50(B)",
    "mAP50_95": "metrics/mAP50-95(B)",
    "precision": "metrics/precision(B)",
    "recall": "metrics/recall(B)",
}

ARG_KEYS = ("model", "data", "epochs", "batch", "imgsz", "optimizer", "lr0", "patience")

FIELDNAMES = [
    "run",
    "model",
    "imgsz",
    "epochs_planned",
    "epochs_run",
    "batch",
    "lr0",
    "patience",
    "mAP50",
    "mAP50_95",
    "precision",
    "recall",
    "train_seconds",
    "data",
]


def read_args(run_dir: Path) -> dict:
    """args.yaml 을 얕게 파싱한다 (PyYAML 의존을 피한다 — 최상위 key: value 뿐이다)."""
    path = run_dir / "args.yaml"
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith((" ", "#")) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        if key in ARG_KEYS:
            out[key] = value.strip()
    return out


def read_results(run_dir: Path) -> tuple[dict, int, str]:
    """마지막 에폭의 지표를 반환한다. (지표, 실제 에폭 수, 누적 학습시간)"""
    path = run_dir / "results.csv"
    with path.open(encoding="utf-8", errors="replace", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return {}, 0, ""

    # 헤더에 선행 공백이 붙는 버전이 있어 정규화한다
    last = {(k or "").strip(): (v or "").strip() for k, v in rows[-1].items()}
    metrics = {name: last.get(col, "") for name, col in METRIC_COLUMNS.items()}
    return metrics, len(rows), last.get("time", "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", default="experiments/legacy_runs")
    parser.add_argument("--out", default="experiments/history.csv")
    args = parser.parse_args()

    runs_root = Path(args.runs)
    records = []
    skipped = []

    for run_dir in sorted(p for p in runs_root.iterdir() if p.is_dir()):
        if not (run_dir / "results.csv").exists():
            skipped.append(run_dir.name)
            continue

        metrics, epochs_run, train_seconds = read_results(run_dir)
        cfg = read_args(run_dir)

        model = cfg.get("model", "")
        records.append(
            {
                "run": run_dir.name,
                "model": Path(model).name if model else "",
                "imgsz": cfg.get("imgsz", ""),
                "epochs_planned": cfg.get("epochs", ""),
                "epochs_run": epochs_run,
                "batch": cfg.get("batch", ""),
                "lr0": cfg.get("lr0", ""),
                "patience": cfg.get("patience", ""),
                "train_seconds": train_seconds,
                "data": cfg.get("data", ""),
                **metrics,
            }
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)

    print(f"run {len(records)}개 수집 → {out_path}")
    if skipped:
        print(f"results.csv 없어 제외: {len(skipped)}개 ({', '.join(skipped[:5])}...)")

    print()
    header = f"{'run':<26} {'mAP50':>7} {'mAP50-95':>9} {'imgsz':>6} {'ep':>4}  data"
    print(header)
    print("-" * len(header))
    for r in sorted(records, key=lambda x: -_as_float(x["mAP50"])):
        data_dir = Path(r["data"]).parent.name if r["data"] else ""
        print(
            f"{r['run']:<26} {_fmt(r['mAP50']):>7} {_fmt(r['mAP50_95']):>9} "
            f"{r['imgsz']:>6} {r['epochs_run']:>4}  {data_dir}"
        )


def _as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return -1.0


def _fmt(value: str) -> str:
    f = _as_float(value)
    return f"{f:.3f}" if f >= 0 else "-"


if __name__ == "__main__":
    main()
