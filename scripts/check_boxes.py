"""라벨 박스의 기하학적 이상을 센다.

시각화에서 박스가 이미지 경계(레터박스 패딩 포함) 밖으로 뻗어나가고
같은 영역에 중복 박스가 쌓이는 것이 보였다. 눈으로 본 것을 수치로 확정한다.

  · 경계 이탈  — 정규화 좌표가 [0,1] 을 벗어난 박스. 증강 후 클리핑 실패 신호
  · 거대 박스  — 이미지의 60% 이상을 덮는 박스. 위치 정보가 없다는 뜻
  · 중복 박스  — 같은 클래스끼리 IoU 0.7 초과. 라벨러가 같은 대상을 여러 번 그림
"""

import argparse
from collections import Counter
from pathlib import Path

ZONE_IDENTIFIER = ":Zone.Identifier"
OUT_OF_BOUNDS_TOLERANCE = 0.005  # 부동소수 오차 허용
HUGE_AREA = 0.60
DUPLICATE_IOU = 0.70


def read_class_names(dataset: Path) -> list[str]:
    path = dataset / "data.yaml"
    if not path.exists():
        return []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("names:"):
            body = line.partition(":")[2].strip().strip("[]")
            return [n.strip().strip("'\"") for n in body.split(",") if n.strip()]
    return []


def corners(box):
    _, cx, cy, w, h = box
    return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2


def iou(a, b) -> float:
    ax1, ay1, ax2, ay2 = corners(a)
    bx1, by1, bx2, by2 = corners(b)
    ix = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    iy = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = ix * iy
    if inter <= 0:
        return 0.0
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union > 0 else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    args = parser.parse_args()

    dataset = Path(args.data)
    names = read_class_names(dataset)

    total = 0
    out_of_bounds = Counter()
    huge = Counter()
    duplicates = Counter()
    extreme_ratio = Counter()
    files_with_oob = 0

    for split in ("train", "valid", "test"):
        labels = dataset / split / "labels"
        if not labels.is_dir():
            continue
        for path in sorted(labels.iterdir()):
            if path.suffix != ".txt" or ZONE_IDENTIFIER in path.name:
                continue

            boxes = []
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                parts = line.split()
                if len(parts) < 5:
                    continue
                try:
                    boxes.append((int(float(parts[0])), *(float(v) for v in parts[1:5])))
                except ValueError:
                    continue

            file_has_oob = False
            for box in boxes:
                total += 1
                cls = box[0]
                x1, y1, x2, y2 = corners(box)

                if (x1 < -OUT_OF_BOUNDS_TOLERANCE or y1 < -OUT_OF_BOUNDS_TOLERANCE
                        or x2 > 1 + OUT_OF_BOUNDS_TOLERANCE
                        or y2 > 1 + OUT_OF_BOUNDS_TOLERANCE):
                    out_of_bounds[cls] += 1
                    file_has_oob = True

                if box[3] * box[4] >= HUGE_AREA:
                    huge[cls] += 1

                ratio = box[3] / box[4] if box[4] > 0 else 0.0
                if ratio > 4 or ratio < 0.25:
                    extreme_ratio[cls] += 1

            if file_has_oob:
                files_with_oob += 1

            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    if boxes[i][0] == boxes[j][0] and iou(boxes[i], boxes[j]) > DUPLICATE_IOU:
                        duplicates[boxes[i][0]] += 1

    def name_of(cls: int) -> str:
        return names[cls] if cls < len(names) else f"class_{cls}"

    print(f"전체 박스 {total}개\n")

    def section(title: str, counter: Counter, note: str) -> None:
        count = sum(counter.values())
        print(f"[{title}] {count}개 ({100 * count / max(1, total):.1f}%) — {note}")
        for cls, n in counter.most_common():
            print(f"    {name_of(cls):<18} {n}")
        if not counter:
            print("    없음")
        print()

    section("경계 이탈", out_of_bounds,
            "정규화 좌표가 [0,1] 밖. 증강 후 클리핑되지 않았다")
    print(f"    → 영향받은 이미지 {files_with_oob}장\n")
    section("거대 박스", huge, f"이미지의 {HUGE_AREA:.0%} 이상을 덮는다")
    section("중복 박스쌍", duplicates,
            f"같은 클래스끼리 IoU {DUPLICATE_IOU} 초과")
    section("극단 종횡비", extreme_ratio, "4:1 보다 길쭉하거나 납작하다")


if __name__ == "__main__":
    main()
