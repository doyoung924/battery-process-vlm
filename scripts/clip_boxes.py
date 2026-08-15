"""라벨 박스를 이미지 경계 [0,1] 로 클리핑한 데이터셋을 만든다.

check_boxes.py 로 박스의 35.4%가 경계를 벗어난 것을 확인했다. 이것이
단순 좌표 버그인지, 라벨 기준 자체가 잘못된 것인지를 가르기 위한 실험이다.

클리핑 후 다시 그려서 (visualize_labels.py) 박스가 설비를 제대로 감싸면
좌표 버그였던 것이고, 여전히 화면 전체를 덮으면 라벨 기준의 문제다.

원본은 건드리지 않고 --out 에 새 데이터셋을 만든다.
"""

import argparse
import shutil
import statistics
from collections import Counter
from pathlib import Path

ZONE_IDENTIFIER = ":Zone.Identifier"

# 클리핑 후 이 면적 미만으로 남으면 박스로서 의미가 없어 버린다
MIN_AREA = 0.0005
# 원래 면적의 이 비율 미만만 남으면 "대부분이 이미지 밖이었다"고 본다
MOSTLY_OUTSIDE = 0.5


def read_class_names(dataset: Path) -> list[str]:
    path = dataset / "data.yaml"
    if not path.exists():
        return []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("names:"):
            body = line.partition(":")[2].strip().strip("[]")
            return [n.strip().strip("'\"") for n in body.split(",") if n.strip()]
    return []


def clip(cx: float, cy: float, w: float, h: float):
    """(cx, cy, w, h) → 경계로 자른 (cx, cy, w, h). 잘라낸 뒤 면적이 0 이면 None."""
    x1, y1 = cx - w / 2, cy - h / 2
    x2, y2 = cx + w / 2, cy + h / 2

    x1, y1 = max(0.0, x1), max(0.0, y1)
    x2, y2 = min(1.0, x2), min(1.0, y2)

    if x2 <= x1 or y2 <= y1:
        return None
    return (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    source = Path(args.data)
    target = Path(args.out)
    names = read_class_names(source)

    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    if (source / "data.yaml").exists():
        shutil.copy2(source / "data.yaml", target / "data.yaml")

    total = 0
    clipped = 0
    dropped = Counter()
    mostly_outside = Counter()
    retained_fractions = []

    for split in ("train", "valid", "test"):
        src_images = source / split / "images"
        src_labels = source / split / "labels"
        if not src_labels.is_dir():
            continue

        dst_images = target / split / "images"
        dst_labels = target / split / "labels"
        dst_labels.mkdir(parents=True, exist_ok=True)

        # 이미지는 심볼릭 링크로 연결한다 (수백 MB 복제를 피한다)
        if src_images.is_dir() and not dst_images.exists():
            dst_images.symlink_to(src_images.resolve(), target_is_directory=True)

        for path in sorted(src_labels.iterdir()):
            if path.suffix != ".txt" or ZONE_IDENTIFIER in path.name:
                continue

            lines = []
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                parts = line.split()
                if len(parts) < 5:
                    continue
                try:
                    cls = int(float(parts[0]))
                    cx, cy, w, h = (float(v) for v in parts[1:5])
                except ValueError:
                    continue

                total += 1
                original_area = w * h
                result = clip(cx, cy, w, h)

                if result is None:
                    dropped[cls] += 1
                    continue

                ncx, ncy, nw, nh = result
                new_area = nw * nh

                if abs(new_area - original_area) > 1e-9:
                    clipped += 1
                    fraction = new_area / original_area if original_area > 0 else 0.0
                    retained_fractions.append(fraction)
                    if fraction < MOSTLY_OUTSIDE:
                        mostly_outside[cls] += 1

                if new_area < MIN_AREA:
                    dropped[cls] += 1
                    continue

                lines.append(f"{cls} {ncx:.6f} {ncy:.6f} {nw:.6f} {nh:.6f}")

            (dst_labels / path.name).write_text("\n".join(lines) + "\n", encoding="utf-8")

    def name_of(cls: int) -> str:
        return names[cls] if cls < len(names) else f"class_{cls}"

    print(f"원본 {source} → {target}\n")
    print(f"전체 박스 {total}개")
    print(f"  클리핑됨   {clipped}개 ({100 * clipped / max(1, total):.1f}%)")
    print(f"  삭제됨     {sum(dropped.values())}개 (클리핑 후 면적 소멸)")

    if retained_fractions:
        retained_fractions.sort()
        median = statistics.median(retained_fractions)
        print(f"\n[클리핑된 박스가 남긴 면적 비율]")
        print(f"  중앙값 {median:.2f} — 원래 면적의 {median:.0%} 만 이미지 안에 있었다")
        print(f"  최소 {retained_fractions[0]:.2f} / 최대 {retained_fractions[-1]:.2f}")

    count = sum(mostly_outside.values())
    print(f"\n[절반 이상이 이미지 밖이었던 박스] {count}개 "
          f"({100 * count / max(1, total):.1f}%)")
    for cls, n in mostly_outside.most_common():
        print(f"    {name_of(cls):<18} {n}")
    if not mostly_outside:
        print("    없음")

    if dropped:
        print(f"\n[삭제된 박스]")
        for cls, n in dropped.most_common():
            print(f"    {name_of(cls):<18} {n}")


if __name__ == "__main__":
    main()
