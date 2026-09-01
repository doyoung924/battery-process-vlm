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

from PIL import Image, ImageDraw, ImageFont


CELL_W = 320
CELL_H = 180
PADDING = 4
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


def extract_frame(video: Path, second: float, out: Path) -> None:
    scale = (
        f"scale={CELL_W}:{CELL_H}:force_original_aspect_ratio=decrease,"
        f"pad={CELL_W}:{CELL_H}:(ow-iw)/2:(oh-ih)/2:color=black"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{second}", "-i", str(video),
         "-frames:v", "1", "-vf", scale, "-q:v", "3", str(out)],
        capture_output=True, check=True,
    )


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
    ap.add_argument("--tag",   type=str,   default=None, help="출력 파일명에 붙일 태그 (예: rp_j1jW)")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    # v10_5AOD.mp4 → "v10"
    video_id = args.video.stem.split("_", 1)[0]
    slug = f"{video_id}_{args.tag}" if args.tag else video_id

    dur = probe_duration(args.video)
    start = args.start if args.start is not None else 0.0
    end = args.end if args.end is not None else dur
    seconds = []
    t = start
    while t < end:
        seconds.append(round(t, 1))
        t += args.interval

    scope = f"{fmt_ts(start)}-{fmt_ts(end)}" if (args.start is not None or args.end is not None) else f"0-{fmt_ts(dur)}"
    print(f"[{slug}] {args.video.name}  scope={scope}  interval={args.interval}s  cells={len(seconds)}")

    tmp_dir = args.out / f"_tmp_{slug}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for i, s in enumerate(seconds):
        out = tmp_dir / f"{i:03d}.jpg"
        extract_frame(args.video, s, out)
        frames.append((s, out))

    cols = min(args.cols, len(frames))
    rows = (len(frames) + cols - 1) // cols
    grid_w = cols * CELL_W + (cols + 1) * PADDING
    grid_h = rows * CELL_H + (rows + 1) * PADDING
    grid = Image.new("RGB", (grid_w, grid_h), color=(30, 30, 30))
    draw = ImageDraw.Draw(grid)
    font = load_font(20)

    for idx, (s, path) in enumerate(frames):
        r, c = divmod(idx, cols)
        x = PADDING + c * (CELL_W + PADDING)
        y = PADDING + r * (CELL_H + PADDING)
        img = Image.open(path).convert("RGB")
        grid.paste(img, (x, y))
        label = f"#{idx:02d} {fmt_ts(s)}"
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0] + 8
        th = bbox[3] - bbox[1] + 4
        draw.rectangle([x, y, x + tw, y + th], fill=(0, 0, 0))
        draw.text((x + 4, y + 2), label, font=font, fill=(255, 255, 255))

    grid_path = args.out / f"{slug}_grid.jpg"
    grid.save(grid_path, quality=85)
    print(f"  → grid : {grid_path}  ({grid_w}x{grid_h})")

    index_path = args.out / f"{slug}_index.txt"
    with open(index_path, "w") as f:
        f.write(f"# {args.video.name}\n")
        f.write(f"# scope = {scope} (duration {fmt_ts(dur)}), interval = {args.interval}s, cells = {len(seconds)}\n")
        f.write(f"# 스크러빙 후 configs/frame_sources.yaml 의 {video_id} chapters 채우기\n\n")
        for i, s in enumerate(seconds):
            f.write(f"#{i:02d}  {fmt_ts(s):>6s}  ({s:6.1f}s)\n")
    print(f"  → index: {index_path}")

    for _, p in frames:
        p.unlink()
    tmp_dir.rmdir()


if __name__ == "__main__":
    main()
