"""라벨과 예측을 컨택트시트로 그려 눈으로 확인한다.

analyze_dataset.py 는 "박스 면적 중앙값이 이미지의 24%"라는 수치를 냈다.
그 수치만으로는 라벨이 설비 윤곽을 가리키는지, 설비가 있는 영역을 뭉뚱그린
것인지 판단할 수 없다. 실제로 그려봐야 재라벨링 범위를 정할 수 있다.

  --mode gt    데이터셋의 정답 박스를 그린다 (라벨 품질 확인)
  --mode pred  가중치로 추론한 박스를 그린다 (일반화 확인)
"""

import argparse
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
ZONE_IDENTIFIER = ":Zone.Identifier"
SYNTHETIC_PREFIX = "Gemini_Generated_Image"

# 클래스별 색 — 인덱스 순환
PALETTE = [
    "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
    "#911eb4", "#42d4f4", "#f032e6", "#bfef45",
]

CELL = 400  # 컨택트시트 한 칸의 픽셀 크기


def read_class_names(dataset: Path) -> list[str]:
    path = dataset / "data.yaml"
    if not path.exists():
        return []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("names:"):
            body = line.partition(":")[2].strip().strip("[]")
            return [n.strip().strip("'\"") for n in body.split(",") if n.strip()]
    return []


def is_image(path: Path) -> bool:
    return (
        path.is_file()
        and ZONE_IDENTIFIER not in path.name
        and path.suffix.lower() in IMAGE_SUFFIXES
    )


def collect_images(root: Path, synthetic: str) -> list[Path]:
    """synthetic: only | exclude | all

    clip_boxes.py 가 만든 데이터셋은 images/ 가 심볼릭 링크다.
    Path.rglob 은 심볼릭 링크된 디렉터리로 내려가지 않으므로 os.walk 를 쓴다.
    """
    found = []
    for directory, _, filenames in os.walk(root, followlinks=True):
        for filename in filenames:
            path = Path(directory) / filename
            if not is_image(path):
                continue
            is_synth = filename.startswith(SYNTHETIC_PREFIX)
            if synthetic == "only" and not is_synth:
                continue
            if synthetic == "exclude" and is_synth:
                continue
            found.append(path)
    return sorted(found)


def draw_boxes(image: Image.Image, boxes, names: list[str]) -> Image.Image:
    """boxes: [(cls, cx, cy, w, h, label_suffix)] — 정규화 좌표"""
    canvas = image.convert("RGB")
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size

    for cls, cx, cy, w, h, suffix in boxes:
        x1 = (cx - w / 2) * width
        y1 = (cy - h / 2) * height
        x2 = (cx + w / 2) * width
        y2 = (cy + h / 2) * height
        color = PALETTE[cls % len(PALETTE)]

        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        name = names[cls] if cls < len(names) else f"c{cls}"
        text = f"{name}{suffix}"
        # 라벨 배경 — 글자가 배경에 묻히지 않게
        tx, ty = x1 + 2, max(0, y1 - 14)
        draw.rectangle([tx - 2, ty - 1, tx + 7 * len(text), ty + 12], fill=color)
        draw.text((tx, ty), text, fill="white")

    return canvas


def gt_boxes(image_path: Path) -> list:
    """이미지 경로에서 대응하는 YOLO 라벨을 찾아 읽는다."""
    label_path = Path(
        str(image_path).replace("/images/", "/labels/")
    ).with_suffix(".txt")
    if not label_path.exists():
        return []

    boxes = []
    for line in label_path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            cls = int(float(parts[0]))
            cx, cy, w, h = (float(v) for v in parts[1:5])
        except ValueError:
            continue
        boxes.append((cls, cx, cy, w, h, ""))
    return boxes


def contact_sheet(cells: list[Image.Image], columns: int) -> Image.Image:
    rows = (len(cells) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * CELL, rows * CELL), "#1a1a1a")
    for i, cell in enumerate(cells):
        cell = cell.copy()
        cell.thumbnail((CELL - 8, CELL - 8))
        x = (i % columns) * CELL + (CELL - cell.width) // 2
        y = (i // columns) * CELL + (CELL - cell.height) // 2
        sheet.paste(cell, (x, y))
    return sheet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("gt", "pred"), default="gt")
    parser.add_argument("--data", required=True, help="데이터셋 루트 또는 이미지 디렉터리")
    parser.add_argument("--names-from", help="data.yaml 위치 (--data 와 다를 때)")
    parser.add_argument("--weights", help="--mode pred 에 필요")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--synthetic", choices=("only", "exclude", "all"), default="exclude")
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    data_root = Path(args.data)
    names = read_class_names(Path(args.names_from) if args.names_from else data_root)

    candidates = collect_images(data_root, args.synthetic)
    if not candidates:
        raise SystemExit(f"이미지를 찾지 못했다: {data_root} (synthetic={args.synthetic})")

    random.seed(args.seed)
    picked = random.sample(candidates, min(args.count, len(candidates)))

    if args.mode == "pred":
        if not args.weights:
            raise SystemExit("--mode pred 에는 --weights 가 필요하다")
        from ultralytics import YOLO

        model = YOLO(args.weights)
        if not names:
            names = [model.names[i] for i in sorted(model.names)]

    cells = []
    empty = 0
    for path in picked:
        image = Image.open(path)

        if args.mode == "gt":
            boxes = gt_boxes(path)
        else:
            result = model.predict(str(path), conf=args.conf, verbose=False)[0]
            boxes = []
            for box in result.boxes:
                cls = int(box.cls.item())
                cx, cy, w, h = box.xywhn[0].tolist()
                boxes.append((cls, cx, cy, w, h, f" {box.conf.item():.2f}"))

        if not boxes:
            empty += 1
        cells.append(draw_boxes(image, boxes, names))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    contact_sheet(cells, args.columns).save(out_path)

    print(f"{args.mode} 시각화 {len(picked)}장 → {out_path}")
    print(f"  후보 {len(candidates)}장 중 샘플링 (synthetic={args.synthetic})")
    print(f"  박스 없는 이미지 {empty}장")


if __name__ == "__main__":
    main()
