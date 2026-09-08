"""라벨링 기준 예시 이미지 생성 — GOOD/BAD 대비 렌더링.

기존 experiments/labeling_examples/*.jpg 포맷 재현:
    - 상단 반절: 원본 프레임 + 녹색 GOOD 박스 + "GOOD: OK: ..." 하단 텍스트
    - 하단 반절: 같은 프레임 + 빨간 BAD 박스 + "BAD: NG: ..." 하단 텍스트
    - 좌상단: 클래스 제목 (상단) / "WRONG" (하단)

Usage:
    .venv/bin/python scripts/render_label_example.py \\
        --src data/frames/v8_unlabeled/wi_RQM4/v8_wi_RQM4_002.jpg \\
        --title WINDING_CORE \\
        --good-box 300,150,700,450 --good-text "OK: winding station (심축+tangency)" \\
        --bad-box 0,0,-1,-1 --bad-text "NG: entire jelly roll (post-winding)" \\
        --out experiments/labeling_examples/winding_core.jpg
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_PATHS = [
    # 한글 우선 (CJK 지원 필수)
    "/home/doyoung/.local/share/fonts/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
GREEN = (46, 204, 113)
RED = (231, 76, 60)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_PATHS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def parse_box(spec: str, w: int, h: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = [int(v) for v in spec.split(",")]
    if x2 < 0:
        x2 = w + x2 + 1
    if y2 < 0:
        y2 = h + y2 + 1
    return x1, y1, x2, y2


def draw_labeled(img: Image.Image, box: tuple[int, int, int, int],
                 color: tuple[int, int, int], top_label: str, bottom_label: str,
                 tag_text: str) -> None:
    draw = ImageDraw.Draw(img)
    font_box = load_font(20)
    font_top = load_font(28)
    font_bot = load_font(22)

    draw.rectangle(box, outline=color, width=4)

    tw, th = draw.textbbox((0, 0), top_label, font=font_box)[2:]
    draw.rectangle([box[0], box[1] - th - 6, box[0] + tw + 8, box[1]], fill=color)
    draw.text((box[0] + 4, box[1] - th - 4), top_label, font=font_box, fill=WHITE)

    tw2, th2 = draw.textbbox((0, 0), tag_text, font=font_top)[2:]
    draw.rectangle([0, 0, tw2 + 16, th2 + 12], fill=BLACK)
    draw.text((8, 4), tag_text, font=font_top, fill=WHITE)

    tw3, th3 = draw.textbbox((0, 0), bottom_label, font=font_bot)[2:]
    y_bot = img.height - th3 - 12
    draw.rectangle([0, y_bot, tw3 + 16, img.height], fill=color)
    draw.text((8, y_bot + 4), bottom_label, font=font_bot, fill=WHITE)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, required=True, help="원본 프레임")
    ap.add_argument("--title", required=True, help="상단 클래스 제목 (예: WINDING_CORE)")
    ap.add_argument("--good-box", required=True, help="GOOD 박스 x1,y1,x2,y2 (음수 = 이미지 크기에서 뺀 값)")
    ap.add_argument("--good-text", required=True, help="GOOD 하단 라벨 (OK: ...)")
    ap.add_argument("--bad-box", default="5,5,-6,-6", help="BAD 박스 x1,y1,x2,y2 (기본 전체 안쪽 5px)")
    ap.add_argument("--bad-text", required=True, help="BAD 하단 라벨 (NG: ...)")
    ap.add_argument("--good-class", default=None, help="GOOD 박스 위 태그 (기본 title 소문자)")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    good_class = args.good_class or args.title.lower()

    src = Image.open(args.src).convert("RGB")
    w, h = src.size

    good_box = parse_box(args.good_box, w, h)
    bad_box = parse_box(args.bad_box, w, h)

    top = src.copy()
    draw_labeled(top, good_box, GREEN, good_class, f"GOOD: {args.good_text}", args.title)

    bot = src.copy()
    draw_labeled(bot, bad_box, RED, "WRONG", f"BAD: {args.bad_text}", "WRONG")

    out = Image.new("RGB", (w, h * 2), color=BLACK)
    out.paste(top, (0, 0))
    out.paste(bot, (0, h))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.save(args.out, quality=90)
    print(f"saved: {args.out}  ({w}x{h * 2})")


if __name__ == "__main__":
    main()
