"""챕터 없는 롱폼의 시각 스크러빙용 썸네일 그리드 생성.

지정 간격으로 프레임을 뽑아 하나의 그리드 이미지로 합치고, 각 셀에 타임코드를
오버레이한다. 스크러빙 절차:

    1. 이 스크립트로 그리드 생성
    2. 이미지 뷰어에서 그리드 열고 클래스 구간을 시각 지정 (예: "#03~#07 = coating_die")
    3. configs/frame_sources.yaml 의 해당 소스 chapters 필드에 반영

Usage:
    .venv/bin/python scripts/preview_grid.py data/raw_videos/v17_Stjc.mp4 --interval 5
    .venv/bin/python scripts/preview_grid.py data/raw_videos/v10_5AOD.mp4 --interval 20
    .venv/bin/python scripts/preview_grid.py data/raw_videos/v3_zbBx.mp4  --interval 60
    # chapter 스코프 (TBD chapter 판정용):
    .venv/bin/python scripts/preview_grid.py data/raw_videos/v2_j1jW.mp4 --start 243 --end 349 --interval 5 --tag rp_j1jW
"""
import argparse
import subprocess
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont


CELL_W = 320
CELL_H = 180
PADDING = 4
CHAPTER_LABEL_H = 26
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
]


def probe_duration(video: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(video)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def probe_resolution(video: Path) -> tuple[int, int]:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "csv=s=x:p=0", str(video)],
        capture_output=True, text=True, check=True,
    )
    w, h = r.stdout.strip().split("x")
    return int(w), int(h)


def extract_frame(video: Path, second: float, out: Path, cw: int, ch: int) -> None:
    scale = (
        f"scale={cw}:{ch}:force_original_aspect_ratio=decrease,"
        f"pad={cw}:{ch}:(ow-iw)/2:(oh-ih)/2:color=black"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{second}", "-i", str(video),
         "-frames:v", "1", "-vf", scale, "-q:v", "3", str(out)],
        capture_output=True, check=True,
    )


def load_chapters(video_id: str, yaml_path: Path) -> list[dict]:
    if not yaml_path.exists():
        return []
    cfg = yaml.safe_load(yaml_path.read_text())
    for src in cfg.get("sources", []) or []:
        if src.get("id") == video_id:
            return src.get("chapters", []) or []
    return []


def chapter_label_at(s: float, chapters: list[dict]) -> str | None:
    for ch in chapters:
        if ch.get("start", 0) <= s < ch.get("end", 0):
            cls = ch.get("class") or ch.get("series") or "?"
            return f"[skip] {cls}" if ch.get("skip") else cls
    return None


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_PATHS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def fmt_ts(s: float) -> str:
    s = int(s)
    return f"{s // 60}:{s % 60:02d}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("--interval", type=float, default=60.0,
                    help="샘플링 간격 (초). 기본 60. 짧은 영상은 5~20 권장")
    ap.add_argument("--cols", type=int, default=6, help="그리드 컬럼 수 (기본 6)")
    ap.add_argument("--out", type=Path, default=Path("data/scrubbing"))
    ap.add_argument("--start", type=float, default=None, help="시작 초. 기본 0 (전체)")
    ap.add_argument("--end",   type=float, default=None, help="끝 초. 기본 영상 끝")
    ap.add_argument("--frames", type=int, default=None,
                    help="정확한 프레임 개수. 지정 시 end = start + frames*interval (영상 duration 상한)")
    ap.add_argument("--tag",   type=str,   default=None, help="출력 파일명에 붙일 태그 (예: rp_j1jW)")
    ap.add_argument("--name",  type=str,   default=None, help="출력 파일명 (예: v1_overview.png). 확장자로 포맷 결정")
    ap.add_argument("--cell-max", type=int, default=None,
                    help="셀 긴 변 픽셀 (aspect ratio 유지). 미지정 시 320x180 letterbox pad")
    ap.add_argument("--show-chapters", action="store_true",
                    help="configs/frame_sources.yaml 의 챕터명을 각 셀 아래에 표기")
    ap.add_argument("--chapters-yaml", type=Path, default=Path("configs/frame_sources.yaml"))
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    # v10_5AOD.mp4 → "v10", v1_source_h264.mp4 → "v1"
    video_id = args.video.stem.split("_", 1)[0]
    slug = f"{video_id}_{args.tag}" if args.tag else video_id

    dur = probe_duration(args.video)
    start = args.start if args.start is not None else 0.0
    if args.frames is not None:
        end = min(start + args.frames * args.interval, dur)
    else:
        end = args.end if args.end is not None else dur

    if args.cell_max:
        vw, vh = probe_resolution(args.video)
        if vw >= vh:
            cell_w = args.cell_max
            cell_h = max(2, round(args.cell_max * vh / vw))
        else:
            cell_h = args.cell_max
            cell_w = max(2, round(args.cell_max * vw / vh))
        # yuv420p 는 짝수 dim 필요 (홀수면 pad 필터 실패)
        if cell_w % 2:
            cell_w += 1
        if cell_h % 2:
            cell_h += 1
    else:
        cell_w, cell_h = CELL_W, CELL_H

    chapters = load_chapters(video_id, args.chapters_yaml) if args.show_chapters else []
    row_h = cell_h + (CHAPTER_LABEL_H if args.show_chapters else 0)

    seconds = []
    t = start
    while t < end:
        seconds.append(round(t, 1))
        t += args.interval

    scope = f"{fmt_ts(start)}-{fmt_ts(end)}" if (args.start is not None or args.end is not None or args.frames is not None) else f"0-{fmt_ts(dur)}"
    print(f"[{slug}] {args.video.name}  scope={scope}  interval={args.interval}s  cells={len(seconds)}  cell={cell_w}x{cell_h}")

    tmp_dir = args.out / f"_tmp_{slug}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for i, s in enumerate(seconds):
        out = tmp_dir / f"{i:03d}.jpg"
        extract_frame(args.video, s, out, cell_w, cell_h)
        frames.append((s, out))

    cols = min(args.cols, len(frames))
    rows = (len(frames) + cols - 1) // cols
    grid_w = cols * cell_w + (cols + 1) * PADDING
    grid_h = rows * row_h + (rows + 1) * PADDING
    grid = Image.new("RGB", (grid_w, grid_h), color=(30, 30, 30))
    draw = ImageDraw.Draw(grid)
    ts_font_size = 20 if cell_w >= 320 else 14
    ch_font_size = 16 if cell_w >= 320 else 12
    ts_font = load_font(ts_font_size)
    ch_font = load_font(ch_font_size)

    for idx, (s, path) in enumerate(frames):
        r, c = divmod(idx, cols)
        x = PADDING + c * (cell_w + PADDING)
        y = PADDING + r * (row_h + PADDING)
        img = Image.open(path).convert("RGB")
        grid.paste(img, (x, y))
        label = f"#{idx:02d} {fmt_ts(s)}"
        bbox = draw.textbbox((0, 0), label, font=ts_font)
        tw = bbox[2] - bbox[0] + 8
        th = bbox[3] - bbox[1] + 4
        draw.rectangle([x, y, x + tw, y + th], fill=(0, 0, 0))
        draw.text((x + 4, y + 2), label, font=ts_font, fill=(255, 255, 255))

        if args.show_chapters:
            ch_y = y + cell_h
            ch_label = chapter_label_at(s, chapters) or "—"
            skipped = ch_label.startswith("[skip]")
            bg = (60, 30, 30) if skipped else (30, 30, 60)
            fg = (240, 180, 180) if skipped else (220, 220, 255)
            draw.rectangle([x, ch_y, x + cell_w, ch_y + CHAPTER_LABEL_H], fill=bg)
            draw.text((x + 4, ch_y + 4), ch_label, font=ch_font, fill=fg)

    if args.name:
        grid_path = args.out / args.name
    else:
        grid_path = args.out / f"{slug}_grid.jpg"
    if grid_path.suffix.lower() in (".jpg", ".jpeg"):
        grid.save(grid_path, quality=85)
    else:
        grid.save(grid_path)
    print(f"  → grid : {grid_path}  ({grid_w}x{grid_h})")

    index_path = args.out / f"{grid_path.stem}_index.txt"
    with open(index_path, "w") as f:
        f.write(f"# {args.video.name}\n")
        f.write(f"# scope = {scope} (duration {fmt_ts(dur)}), interval = {args.interval}s, cells = {len(seconds)}\n")
        f.write(f"# 스크러빙 후 configs/frame_sources.yaml 의 {video_id} chapters 채우기\n\n")
        for i, s in enumerate(seconds):
            ch = chapter_label_at(s, chapters) if args.show_chapters else ""
            ch_col = f"  {ch}" if ch else ""
            f.write(f"#{i:02d}  {fmt_ts(s):>6s}  ({s:6.1f}s){ch_col}\n")
    print(f"  → index: {index_path}")

    for _, p in frames:
        p.unlink()
    tmp_dir.rmdir()


if __name__ == "__main__":
    main()
