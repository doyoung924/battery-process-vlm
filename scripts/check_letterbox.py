"""박스가 레터박스(검은 여백) 영역을 얼마나 포함하는지 잰다.

데이터셋 이미지는 전부 640x640 이지만 원본은 16:9 영상 프레임이라
위아래에 검은 여백이 들어가 있다. 여백에는 아무 정보도 없으므로,
박스가 여백을 크게 포함한다면 그 박스는 설비 윤곽이 아니라
"설비가 있는 넓은 영역"을 가리키고 있다는 뜻이다.

clip_boxes.py 로 이미지 경계를 벗어난 부분을 잘라내도 이 문제는 남는다.
여백은 이미지 안쪽이기 때문이다. 재라벨링이 필요한지 판단하는 근거다.
"""

import argparse
import os
import statistics
from collections import Counter
from pathlib import Path

from PIL import Image

ZONE_IDENTIFIER = ":Zone.Identifier"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}

# 행 평균 밝기가 이 값 이하이면 레터박스 여백으로 본다
DARK_THRESHOLD = 12
# 박스 면적의 이 비율 이상이 여백이면 "여백을 크게 포함"으로 센다
PADDING_HEAVY = 0.20


def read_class_names(dataset: Path) -> list[str]:
    path = dataset / "data.yaml"
    if not path.exists():
        return []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("names:"):
            body = line.partition(":")[2].strip().strip("[]")
            return [n.strip().strip("'\"") for n in body.split(",") if n.strip()]
    return []


def content_band(image: Image.Image) -> tuple[float, float]:
    """세로 방향 콘텐츠 구간을 정규화 좌표 (top, bottom) 로 돌려준다."""
    gray = image.convert("L")
    width, height = gray.size
    # 각 행의 평균 밝기 — 폭 1로 리사이즈하면 행 평균이 된다
    column = gray.resize((1, height))
    rows = [column.getpixel((0, y)) for y in range(height)]

    top = 0
    while top < height and rows[top] <= DARK_THRESHOLD:
        top += 1
    bottom = height - 1
    while bottom > top and rows[bottom] <= DARK_THRESHOLD:
        bottom -= 1

    return top / height, (bottom + 1) / height


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    args = parser.parse_args()

    dataset = Path(args.data)
    names = read_class_names(dataset)

    padding_fractions = []
    heavy = Counter()
    total_boxes = 0
    band_heights = []
    images_with_band = 0
    images_total = 0

    for split in ("train", "valid", "test"):
        images_dir = dataset / split / "images"
        labels_dir = dataset / split / "labels"
        if not labels_dir.is_dir():
            continue

        for directory, _, filenames in os.walk(images_dir, followlinks=True):
            for filename in sorted(filenames):
                if ZONE_IDENTIFIER in filename:
                    continue
                image_path = Path(directory) / filename
                if image_path.suffix.lower() not in IMAGE_SUFFIXES:
                    continue

                label_path = labels_dir / (image_path.stem + ".txt")
                if not label_path.exists():
                    continue

                with Image.open(image_path) as image:
                    top, bottom = content_band(image)

                images_total += 1
                band = bottom - top
                band_heights.append(band)
                if band < 0.98:
                    images_with_band += 1

                for line in label_path.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines():
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    try:
                        cls = int(float(parts[0]))
                        _, cy, _, h = (
                            float(parts[1]), float(parts[2]),
                            float(parts[3]), float(parts[4]),
                        )
                    except ValueError:
                        continue

                    total_boxes += 1
                    y1, y2 = cy - h / 2, cy + h / 2
                    inside = max(0.0, min(y2, bottom) - max(y1, top))
                    fraction = 1 - (inside / h) if h > 0 else 0.0
                    padding_fractions.append(fraction)
                    if fraction >= PADDING_HEAVY:
                        heavy[cls] += 1

    def name_of(cls: int) -> str:
        return names[cls] if cls < len(names) else f"class_{cls}"

    print(f"이미지 {images_total}장 / 박스 {total_boxes}개\n")

    if band_heights:
        median_band = statistics.median(band_heights)
        print(f"[레터박스] 여백이 있는 이미지 {images_with_band}장 "
              f"({100 * images_with_band / max(1, images_total):.0f}%)")
        print(f"  콘텐츠 세로 구간 중앙값 {median_band:.0%} "
              f"— 나머지 {1 - median_band:.0%}는 검은 여백이다\n")

    if padding_fractions:
        padding_fractions.sort()
        def pct(p):
            return padding_fractions[min(len(padding_fractions) - 1,
                                         int(p / 100 * (len(padding_fractions) - 1)))]
        print("[박스 면적 중 여백이 차지하는 비율]")
        print(f"  p50 {pct(50):.0%} / p75 {pct(75):.0%} / p90 {pct(90):.0%} / p95 {pct(95):.0%}")

    count = sum(heavy.values())
    print(f"\n[여백을 {PADDING_HEAVY:.0%} 이상 포함하는 박스] {count}개 "
          f"({100 * count / max(1, total_boxes):.1f}%)")
    for cls, n in heavy.most_common():
        print(f"    {name_of(cls):<18} {n}")
    if not heavy:
        print("    없음")


if __name__ == "__main__":
    main()
