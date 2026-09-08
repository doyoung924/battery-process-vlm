"""pre-extracted 이미지 파일들을 그리드로 렌더링 (스크러빙 용).

preview_grid.py 가 영상 재추출용이라면, 이건 이미 뽑혀 있는 파일을 시각 검토용으로 그리드화.
v1 처럼 pre-extracted 소스의 서브 시리즈(frame_a 등) 재판정 시 사용.

Usage:
    .venv/bin/python scripts/preview_files.py \
        data/frames/v1_unlabeled/slitter_knife/frame_a*.jpg \
        --tag v1_slitter_frameA --cols 8
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CELL_W = 320
CELL_H = 180
PADDING = 4
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_PATHS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def fit_cell(img: Image.Image) -> Image.Image:
    w, h = img.size
    scale = min(CELL_W / w, CELL_H / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (CELL_W, CELL_H), (0, 0, 0))
    canvas.paste(resized, ((CELL_W - nw) // 2, (CELL_H - nh) // 2))
    return canvas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", type=Path, nargs="+")
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--tag", type=str, required=True, help="출력 파일명 슬러그 (예: v1_slitter_frameA)")
    ap.add_argument("--out", type=Path, default=Path("data/scrubbing"))
    args = ap.parse_args()

    files = sorted(args.files)
    if not files:
        raise SystemExit("파일 없음")

    args.out.mkdir(parents=True, exist_ok=True)

    cols = min(args.cols, len(files))
    rows = (len(files) + cols - 1) // cols
    grid_w = cols * CELL_W + (cols + 1) * PADDING
    grid_h = rows * CELL_H + (rows + 1) * PADDING
    grid = Image.new("RGB", (grid_w, grid_h), color=(30, 30, 30))
    draw = ImageDraw.Draw(grid)
    font = load_font(16)

    for idx, path in enumerate(files):
        r, c = divmod(idx, cols)
        x = PADDING + c * (CELL_W + PADDING)
        y = PADDING + r * (CELL_H + PADDING)
        try:
            img = Image.open(path).convert("RGB")
        except Exception:
            continue
        cell = fit_cell(img)
        grid.paste(cell, (x, y))
        label = f"#{idx:03d} {path.stem}"
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0] + 8
        th = bbox[3] - bbox[1] + 4
        draw.rectangle([x, y, x + tw, y + th], fill=(0, 0, 0))
        draw.text((x + 4, y + 2), label, font=font, fill=(255, 255, 255))

    grid_path = args.out / f"{args.tag}_grid.jpg"
    grid.save(grid_path, quality=85)
    print(f"[{args.tag}] {len(files)} files → {grid_path} ({grid_w}x{grid_h})")

    index_path = args.out / f"{args.tag}_index.txt"
    with open(index_path, "w") as f:
        f.write(f"# preview_files grid — {len(files)} files\n\n")
        for i, p in enumerate(files):
            f.write(f"#{i:03d}  {p.name}\n")
    print(f"  → index: {index_path}")


if __name__ == "__main__":
    main()
