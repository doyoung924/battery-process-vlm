"""라벨링 카드 렌더링 — GOOD/BAD 두 프레임 대비 (2026-09-11 라운드 4).

이전 render_label_example.py 는 GOOD/BAD 가 같은 프레임이라 "크게 치지 마라" 하나만
가르쳤다. 이 스크립트는 다른 프레임에서 고른 혼동 대상을 그림으로 보여준다.

레이아웃 (위→아래):
    [클래스 제목]
    [GOOD 이미지, 초록 테두리, 스펙대로 친 박스 1개, 한 줄 설명]
    [BAD  이미지, 빨강 테두리, 한 줄 설명(왜 안 되는지)]
    [공통 스펙 3줄]

Usage:
    .venv/bin/python scripts/render_label_card.py \\
        --class-name electrode_roll \\
        --title "ELECTRODE_ROLL" \\
        --good data/frames/v3_selected/electrode_roll/v17_v17_er_a_0005.jpg \\
        --good-box 900,15,1920,470 \\
        --good-text "감긴 롤 외곽 밀착. 이송 웹은 포함 안 함" \\
        --bad  /tmp/vinspect/v17_bad_electrode.jpg \\
        --bad-text  "감긴 전극 없음: 빈 심축·이송 롤러만 → 스킵" \\
        --out data/labeling_cards/electrode_roll_card.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_PATHS = [
    "/home/doyoung/.local/share/fonts/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
GREEN = (46, 204, 113)
RED = (231, 76, 60)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY_BG = (28, 28, 32)
GRAY_TXT = (200, 200, 205)

LONG_SIDE = 600            # 셀 긴 변
BORDER = 6                 # GOOD/BAD 테두리 두께
GOOD_BOX_WIDTH = 4         # GOOD 박스 두께
LABEL_BAR_H = 40           # 라벨 바 높이
TITLE_H = 56
FOOTER_H = 96
PAD = 12                   # 이미지 주위 여백

SPEC_LINES = [
    "박스 = 물체 외곽 밀착 · 웹/레터박스/자막 제외",
    "면적 3% 미만 스킵 · 절반 이상 가려지면 스킵",
    "판단이 3초 이상 걸리면 스킵",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_PATHS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def scale_to_long_side(img: Image.Image, long_side: int) -> Image.Image:
    w, h = img.size
    if w >= h:
        new_w = long_side
        new_h = int(round(h * long_side / w))
    else:
        new_h = long_side
        new_w = int(round(w * long_side / h))
    return img.resize((new_w, new_h), Image.LANCZOS)


def scale_box(box: tuple[int, int, int, int], src: tuple[int, int],
              dst: tuple[int, int]) -> tuple[int, int, int, int]:
    sw, sh = src
    dw, dh = dst
    sx = dw / sw
    sy = dh / sh
    x1, y1, x2, y2 = box
    return (int(round(x1 * sx)), int(round(y1 * sy)),
            int(round(x2 * sx)), int(round(y2 * sy)))


def parse_box(spec: str) -> tuple[int, int, int, int]:
    return tuple(int(v) for v in spec.split(","))  # type: ignore[return-value]


def render_panel(src_path: Path, long_side: int, border_color: tuple[int, int, int],
                 label_text: str, good_box: tuple[int, int, int, int] | None) -> Image.Image:
    """이미지 + 테두리 + 라벨 바(하단). GOOD 이면 good_box 표시."""
    orig = Image.open(src_path).convert("RGB")
    orig_size = orig.size
    scaled = scale_to_long_side(orig, long_side)
    w, h = scaled.size

    if good_box:
        draw = ImageDraw.Draw(scaled)
        gx = scale_box(good_box, orig_size, (w, h))
        draw.rectangle(gx, outline=GREEN, width=GOOD_BOX_WIDTH)

    # 라벨 바
    font = load_font(18)
    label_bar = Image.new("RGB", (w, LABEL_BAR_H), color=border_color)
    ld = ImageDraw.Draw(label_bar)
    ld.text((14, (LABEL_BAR_H - 22) // 2), label_text, font=font, fill=WHITE)

    # 이미지 + 라벨 바 결합 후 테두리
    inner = Image.new("RGB", (w, h + LABEL_BAR_H), color=BLACK)
    inner.paste(scaled, (0, 0))
    inner.paste(label_bar, (0, h))

    panel = Image.new("RGB", (w + 2 * BORDER, h + LABEL_BAR_H + 2 * BORDER),
                       color=border_color)
    panel.paste(inner, (BORDER, BORDER))
    return panel


def render_title(text: str, width: int) -> Image.Image:
    bar = Image.new("RGB", (width, TITLE_H), color=BLACK)
    d = ImageDraw.Draw(bar)
    font = load_font(28)
    d.text((16, (TITLE_H - 34) // 2), text, font=font, fill=WHITE)
    return bar


def render_footer(width: int) -> Image.Image:
    bar = Image.new("RGB", (width, FOOTER_H), color=GRAY_BG)
    d = ImageDraw.Draw(bar)
    font = load_font(16)
    line_h = 26
    total_h = line_h * len(SPEC_LINES)
    y0 = (FOOTER_H - total_h) // 2
    for i, line in enumerate(SPEC_LINES):
        d.text((16, y0 + i * line_h), line, font=font, fill=GRAY_TXT)
    return bar


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--class-name", required=True)
    ap.add_argument("--title", required=True, help="상단 표시 제목")
    ap.add_argument("--good", type=Path, required=True)
    ap.add_argument("--good-box", required=True, help="원본 좌표 x1,y1,x2,y2 (스펙대로 친 박스)")
    ap.add_argument("--good-text", required=True)
    ap.add_argument("--bad", type=Path, required=True)
    ap.add_argument("--bad-text", required=True)
    ap.add_argument("--long-side", type=int, default=LONG_SIDE)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    good_box = parse_box(args.good_box)

    good_panel = render_panel(args.good, args.long_side, GREEN,
                              f"GOOD  ·  {args.good_text}", good_box)
    bad_panel = render_panel(args.bad, args.long_side, RED,
                             f"BAD  ·  {args.bad_text}", None)

    inner_w = max(good_panel.width, bad_panel.width)
    total_w = inner_w + 2 * PAD
    title_bar = render_title(args.title, total_w)
    footer_bar = render_footer(total_w)

    total_h = title_bar.height + PAD + good_panel.height + PAD + bad_panel.height + PAD + footer_bar.height
    card = Image.new("RGB", (total_w, total_h), color=BLACK)

    y = 0
    card.paste(title_bar, (0, y)); y += title_bar.height + PAD
    gx = (total_w - good_panel.width) // 2
    card.paste(good_panel, (gx, y)); y += good_panel.height + PAD
    bx = (total_w - bad_panel.width) // 2
    card.paste(bad_panel, (bx, y)); y += bad_panel.height + PAD
    card.paste(footer_bar, (0, y))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    card.save(args.out, "PNG")
    print(f"saved: {args.out}  ({card.width}x{card.height})")


if __name__ == "__main__":
    main()
