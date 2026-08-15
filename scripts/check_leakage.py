"""1차 시도 데이터셋의 train/val 누수를 정량화한다.

Roboflow export 파일명은 `{원본이름}_{ext}.rf.{hash}.jpg` 형태다.
증강 파생본은 원본 이름(base)을 공유하므로, base 가 train 과 valid 양쪽에
나타나면 같은 사진의 변형으로 채점한 것이 된다.

이 스크립트가 답하는 질문:
  1) val 세트의 원본 이미지가 몇 장인가 (증강본을 접으면)
  2) 그중 몇 장이 train 에도 있는가 (누수 비율)
"""

import argparse
import re
from pathlib import Path

# 예: -2026-06-09-135038_png.rf.280468930296401ea780e72a8730cfd0.jpg
ROBOFLOW_SUFFIX = re.compile(r"_(png|jpg|jpeg)\.rf\.[0-9a-f]+\.(jpg|png)$", re.IGNORECASE)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}

# Windows 에서 복사되며 딸려온 NTFS 대체 데이터 스트림.
# 이미지와 1:1 로 존재해 세지 않으면 장수가 정확히 두 배로 부풀려진다.
ZONE_IDENTIFIER = ":Zone.Identifier"

# Gemini 로 생성한 합성 공정 이미지의 파일명 접두사
SYNTHETIC_PREFIX = "Gemini_Generated_Image"


def is_image(name: str) -> bool:
    return ZONE_IDENTIFIER not in name and Path(name).suffix.lower() in IMAGE_SUFFIXES


def base_names(split_dir: Path) -> tuple[set[str], int]:
    """(원본 이름 집합, 이미지 파일 개수)"""
    images = split_dir / "images"
    if not images.is_dir():
        return set(), 0
    files = [p.name for p in images.iterdir() if p.is_file() and is_image(p.name)]
    return {ROBOFLOW_SUFFIX.sub("", n) for n in files}, len(files)


def report(dataset: Path) -> dict | None:
    train, n_train = base_names(dataset / "train")
    valid, n_valid = base_names(dataset / "valid")
    if not n_train and not n_valid:
        return None

    overlap = train & valid
    leak_pct = 100 * len(overlap) / len(valid) if valid else 0.0

    # Gemini 로 생성한 합성 이미지 비중. 실제 공정 영상 프레임이 아니므로
    # 이 비중이 높을수록 미학습 영상에 대한 일반화를 기대할 수 없다.
    all_bases = train | valid
    synthetic = sum(1 for b in all_bases if b.startswith(SYNTHETIC_PREFIX))
    synth_pct = 100 * synthetic / len(all_bases) if all_bases else 0.0

    return {
        "dataset": dataset.name,
        "train_files": n_train,
        "train_unique": len(train),
        "valid_files": n_valid,
        "valid_unique": len(valid),
        "overlap": len(overlap),
        "leak_pct": leak_pct,
        "synth_pct": synth_pct,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", help="데이터셋 디렉터리 또는 그 부모 디렉터리")
    args = parser.parse_args()

    candidates: list[Path] = []
    for raw in args.roots:
        root = Path(raw)
        if (root / "train").is_dir() or (root / "valid").is_dir():
            candidates.append(root)
        else:
            candidates.extend(sorted(p for p in root.iterdir() if p.is_dir()))

    rows = [r for r in (report(c) for c in candidates) if r]

    header = (
        f"{'dataset':<38} {'train':>14} {'valid':>13} {'중복':>5} {'합성비중':>8}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        train_cell = f"{r['train_files']}장/{r['train_unique']}원본"
        valid_cell = f"{r['valid_files']}장/{r['valid_unique']}원본"
        print(
            f"{r['dataset']:<38} {train_cell:>14} {valid_cell:>13} "
            f"{r['overlap']:>5} {r['synth_pct']:>7.0f}%"
        )

    print()
    leaking = [r for r in rows if r["overlap"]]
    if leaking:
        print(f"직접 누수: {len(leaking)}/{len(rows)}개 데이터셋에서 "
              f"val 원본이 train 에도 존재한다.")
    else:
        print("직접 누수(같은 원본이 train·val 양쪽)는 없다.")

    tiny = [r for r in rows if 0 < r["valid_unique"] < 20]
    if tiny:
        print(f"val 원본 20장 미만: {len(tiny)}개 데이터셋 "
              f"→ mAP 의 신뢰구간이 지표로 쓸 수 없을 만큼 넓다.")

    synthetic_heavy = [r for r in rows if r["synth_pct"] >= 30]
    if synthetic_heavy:
        print(f"합성 이미지 30% 이상: {len(synthetic_heavy)}개 데이터셋 "
              f"→ 실제 영상 프레임에 대한 일반화를 기대할 수 없다.")


if __name__ == "__main__":
    main()
