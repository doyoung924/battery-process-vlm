"""YOLO 데이터셋을 진단한다 — 무엇이 학습을 막고 있는지 수치로 특정한다.

출력 항목과 그 판단 근거:
  · 클래스별 인스턴스 수    → 학습이 성립하는 수량인가 (실무 기준 클래스당 100~150)
  · 박스 면적 비율 분포     → 소형 객체 비중. imgsz 를 올려야 하는지 결정
  · 박스 종횡비 분포        → 극단적 종횡비는 바운딩박스로 표현하기 부적합한 클래스 신호
  · 이미지당 박스 수 / IoU  → 밀집·중첩 정도. SAHI 타일링과 NMS 설정 근거
  · 합성 이미지 비중        → Gemini 생성 이미지는 실제 영상에 일반화되지 않는다
"""

import argparse
import statistics
from collections import Counter, defaultdict
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
ZONE_IDENTIFIER = ":Zone.Identifier"
SYNTHETIC_PREFIX = "Gemini_Generated_Image"

# 소형 객체 기준 — 이미지 면적 대비 비율
TINY_AREA = 0.01   # 1% 미만
SMALL_AREA = 0.05  # 5% 미만


def read_class_names(dataset: Path) -> list[str]:
    """data.yaml 의 names 리스트를 파싱한다 (PyYAML 의존을 피한다)."""
    path = dataset / "data.yaml"
    if not path.exists():
        return []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("names:"):
            continue
        body = line.partition(":")[2].strip().strip("[]")
        return [n.strip().strip("'\"") for n in body.split(",") if n.strip()]
    return []


def iter_label_files(dataset: Path):
    for split in ("train", "valid", "test"):
        labels = dataset / split / "labels"
        if not labels.is_dir():
            continue
        for path in sorted(labels.iterdir()):
            if path.suffix == ".txt" and ZONE_IDENTIFIER not in path.name:
                yield split, path


def parse_boxes(path: Path) -> list[tuple[int, float, float, float, float]]:
    """YOLO 라벨 한 파일 → [(cls, cx, cy, w, h), ...]"""
    boxes = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            cls = int(float(parts[0]))
            cx, cy, w, h = (float(v) for v in parts[1:5])
        except ValueError:
            continue
        boxes.append((cls, cx, cy, w, h))
    return boxes


def iou(a: tuple, b: tuple) -> float:
    """정규화 좌표 (cx, cy, w, h) 두 박스의 IoU."""
    def corners(box):
        _, cx, cy, w, h = box
        return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2

    ax1, ay1, ax2, ay2 = corners(a)
    bx1, by1, bx2, by2 = corners(b)

    ix = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    iy = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = ix * iy
    if inter <= 0:
        return 0.0
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union > 0 else 0.0


def percentiles(values: list[float], points=(5, 25, 50, 75, 95)) -> dict[int, float]:
    if not values:
        return {p: 0.0 for p in points}
    ordered = sorted(values)
    out = {}
    for p in points:
        idx = min(len(ordered) - 1, int(round(p / 100 * (len(ordered) - 1))))
        out[p] = ordered[idx]
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="YOLO 데이터셋 루트 (data.yaml 이 있는 곳)")
    args = parser.parse_args()

    dataset = Path(args.data)
    names = read_class_names(dataset)

    instances = Counter()
    areas = defaultdict(list)
    ratios = defaultdict(list)
    boxes_per_image = []
    overlaps = []
    split_counts = Counter()

    for split, label_path in iter_label_files(dataset):
        boxes = parse_boxes(label_path)
        split_counts[split] += 1
        boxes_per_image.append(len(boxes))

        for cls, _, _, w, h in boxes:
            instances[cls] += 1
            areas[cls].append(w * h)
            ratios[cls].append(w / h if h > 0 else 0.0)

        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                value = iou(boxes[i], boxes[j])
                if value > 0:
                    overlaps.append(value)

    # ---- 이미지 구성 ----
    print("=" * 74)
    print(f"데이터셋: {dataset}")
    print("=" * 74)

    image_files = []
    for split in ("train", "valid", "test"):
        images = dataset / split / "images"
        if not images.is_dir():
            continue
        image_files += [
            p.name
            for p in images.iterdir()
            if p.is_file()
            and ZONE_IDENTIFIER not in p.name
            and p.suffix.lower() in IMAGE_SUFFIXES
        ]

    synthetic = sum(1 for n in image_files if n.startswith(SYNTHETIC_PREFIX))
    print(f"\n[이미지] 전체 {len(image_files)}장 "
          f"(train {split_counts['train']} / valid {split_counts['valid']} / test {split_counts['test']} 라벨)")
    if image_files:
        print(f"  합성(Gemini) {synthetic}장 ({100*synthetic/len(image_files):.0f}%) / "
              f"실사 {len(image_files)-synthetic}장")

    # ---- 클래스별 인스턴스 ----
    total = sum(instances.values())
    print(f"\n[클래스별 인스턴스] 총 {total}개")
    print(f"  {'클래스':<20} {'개수':>6} {'비중':>7} {'중앙면적':>9} {'종횡비':>7}  판정")
    for cls in sorted(instances, key=lambda c: -instances[c]):
        name = names[cls] if cls < len(names) else f"class_{cls}"
        count = instances[cls]
        median_area = statistics.median(areas[cls]) if areas[cls] else 0.0
        median_ratio = statistics.median(ratios[cls]) if ratios[cls] else 0.0

        if count < 30:
            verdict = "학습 불가 — 인스턴스 부족"
        elif count < 100:
            verdict = "부족 — 100개 이상 필요"
        elif median_ratio > 5 or median_ratio < 0.2:
            verdict = "박스 부적합 의심 — 극단적 종횡비"
        else:
            verdict = "양호"

        print(f"  {name:<20} {count:>6} {100*count/total:>6.1f}% "
              f"{median_area:>9.4f} {median_ratio:>7.2f}  {verdict}")

    # ---- 박스 크기 ----
    all_areas = [a for values in areas.values() for a in values]
    pct = percentiles(all_areas)
    tiny = sum(1 for a in all_areas if a < TINY_AREA)
    small = sum(1 for a in all_areas if a < SMALL_AREA)
    print(f"\n[박스 면적 비율] p5 {pct[5]:.4f} / p25 {pct[25]:.4f} / "
          f"p50 {pct[50]:.4f} / p75 {pct[75]:.4f} / p95 {pct[95]:.4f}")
    print(f"  1% 미만(초소형) {tiny}개 ({100*tiny/max(1,len(all_areas)):.0f}%) / "
          f"5% 미만(소형) {small}개 ({100*small/max(1,len(all_areas)):.0f}%)")
    if all_areas and small / len(all_areas) > 0.5:
        print("  → 소형 객체가 과반. imgsz 상향(1280)과 SAHI 타일링이 필요하다.")

    # ---- 밀집도 ----
    mean_boxes = statistics.mean(boxes_per_image) if boxes_per_image else 0
    empty = sum(1 for n in boxes_per_image if n == 0)
    print(f"\n[밀집도] 이미지당 박스 평균 {mean_boxes:.1f}개 / "
          f"최대 {max(boxes_per_image, default=0)}개 / 빈 라벨 {empty}장")
    if overlaps:
        opct = percentiles(overlaps)
        high = sum(1 for v in overlaps if v > 0.5)
        print(f"  겹치는 박스쌍 {len(overlaps)}개 — IoU p50 {opct[50]:.2f} / p95 {opct[95]:.2f}")
        print(f"  IoU 0.5 초과 {high}쌍", end="")
        print(" → 표준 NMS 에서 정답 박스가 삭제될 수 있다. Soft-NMS 검토."
              if high else "")
    else:
        print("  겹치는 박스 없음 → NMS 설정은 기본값으로 충분하다.")


if __name__ == "__main__":
    main()
