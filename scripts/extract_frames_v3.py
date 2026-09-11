"""라운드 4 전용 프레임 추출 — configs/frame_sources.yaml (재작성판) 순회.

동작:
- extraction.interval_seconds 간격으로 각 chapter 를 ffmpeg 로 임시 폴더에 추출
- pHash(Hamming ≤ THRESHOLD) 로 chapter 내 dedup
- 살아남은 프레임을 data/frames/<output.subdir>/<class>/ 로 이동
- data/frames/<output.subdir>/manifest.csv 에 (filename, source_id, series, class, chapter_start, chapter_end, timecode_seconds) 기록

기존 data/frames/v{N}_unlabeled/ 는 건드리지 않는다.
excluded_reason 이 있거나 chapters 가 비었으면 소스 스킵.

Usage:
    .venv/bin/python scripts/extract_frames_v3.py
    .venv/bin/python scripts/extract_frames_v3.py --dry-run
    .venv/bin/python scripts/extract_frames_v3.py --force   # 기존 v3_selected 폴더 비우고 재추출
"""
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import imagehash
import yaml
from PIL import Image

PHASH_THRESHOLD = 8   # Hamming 거리 임계 (select_frames.py SERIES_DEFAULT_THRESHOLD 와 통일)


def fmt_dur(s: float) -> str:
    s = int(s)
    return f"{s // 60}:{s % 60:02d}"


def ffmpeg_extract(video: Path, start: float, end: float, interval: float,
                   out_dir: Path, prefix: str) -> list[Path]:
    """chapter 를 임시 폴더에 fps=1/interval 로 추출. 반환: 정렬된 프레임 경로."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(out_dir / f"{prefix}_%04d.jpg")
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video),
         "-ss", f"{start}", "-to", f"{end}",
         "-vf", f"fps=1/{interval}", "-q:v", "2", pattern],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed on {video.name} {fmt_dur(start)}-{fmt_dur(end)}:\n{r.stderr[-500:]}")
    return sorted(out_dir.glob(f"{prefix}_*.jpg"))


def dedup_phash(frames: list[Path], threshold: int = PHASH_THRESHOLD) -> tuple[list[Path], int]:
    """pHash 로 chapter 내 근중복 제거. 반환: (살아남은 프레임, 제거 수)."""
    kept: list[tuple[Path, imagehash.ImageHash]] = []
    dropped = 0
    for path in frames:
        try:
            with Image.open(path) as im:
                ph = imagehash.phash(im)
        except Exception as e:
            print(f"    ⚠️  hash error {path.name}: {type(e).__name__}: {e}")
            continue
        if any((ph - h) <= threshold for _, h in kept):
            dropped += 1
            continue
        kept.append((path, ph))
    return [p for p, _ in kept], dropped


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=Path("configs/frame_sources.yaml"))
    ap.add_argument("--dry-run", action="store_true", help="추출 없이 계획만 출력")
    ap.add_argument("--force", action="store_true", help="기존 v3_selected 클래스 폴더 비우고 재추출")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    interval = float(cfg["extraction"]["interval_seconds"])
    frames_root = Path(cfg["extraction"]["output_root"])
    subdir = cfg["output"]["subdir"]
    out_root = frames_root / subdir

    print(f"config    : {args.config}")
    print(f"interval  : {interval}s   pHash threshold: {PHASH_THRESHOLD}")
    print(f"out_root  : {out_root}")
    print(f"dry_run   : {args.dry_run}   force: {args.force}")
    print()

    if args.force and out_root.exists():
        print(f"[force] removing {out_root}")
        if not args.dry_run:
            shutil.rmtree(out_root)

    class_counts: Counter[str] = Counter()
    manifest_rows: list[dict] = []
    skipped = []

    for s in cfg["sources"]:
        sid = s["id"]
        if s.get("excluded_reason") or not s.get("chapters"):
            skipped.append(f"{sid} [excluded/empty]")
            continue
        video = Path(s["video"])
        if not video.exists():
            print(f"⚠️  {sid} video not found: {video}")
            continue
        print(f"[{sid}] {video.name}")

        for ch in s["chapters"]:
            cls = ch["class"]
            series = ch["series"]
            start = float(ch["start"])
            end = float(ch["end"])
            ch_interval = float(ch.get("interval", interval))
            span = fmt_dur(start) + "-" + fmt_dur(end)

            if args.dry_run:
                expected = max(1, int((end - start) / ch_interval))
                print(f"  + would extract {series} ({span} @{ch_interval}s) → ~{expected} frames [class={cls}]")
                class_counts[cls] += expected
                continue

            with tempfile.TemporaryDirectory(prefix=f"v3_{sid}_{series}_") as tmp:
                tmp_dir = Path(tmp)
                prefix = f"{sid}_{series}"
                try:
                    raw = ffmpeg_extract(video, start, end, ch_interval, tmp_dir, prefix)
                except RuntimeError as e:
                    print(f"  ! {series}: {e}")
                    continue

                kept, dropped = dedup_phash(raw)
                dest_dir = out_root / cls
                dest_dir.mkdir(parents=True, exist_ok=True)

                for idx, src in enumerate(kept):
                    # ffmpeg 는 chapter start 를 0 으로 삼아 순번을 매김.
                    # 따라서 원본 프레임 인덱스 → 원본 영상 타임코드 = start + (idx * ch_interval)
                    # (dedup 은 dropping 이므로 raw 의 원 위치를 유지하지 않음. src 파일명에서 원 인덱스 파싱)
                    raw_idx = int(src.stem.rsplit("_", 1)[-1]) - 1
                    timecode = start + raw_idx * ch_interval
                    dest_name = f"{sid}_{series}_{idx:04d}.jpg"
                    dest = dest_dir / dest_name
                    shutil.move(str(src), str(dest))
                    manifest_rows.append({
                        "filename": str(dest.relative_to(out_root)),
                        "source_id": sid,
                        "series": series,
                        "class": cls,
                        "chapter_start": start,
                        "chapter_end": end,
                        "timecode_seconds": round(timecode, 2),
                        "timecode_hms": fmt_dur(timecode),
                    })
                    class_counts[cls] += 1

                print(f"  + {series} ({span} @{ch_interval}s) class={cls}"
                      f"  raw={len(raw)}  kept={len(kept)}  dedup_dropped={dropped}")

    if not args.dry_run and manifest_rows:
        out_root.mkdir(parents=True, exist_ok=True)
        manifest_path = out_root / "manifest.csv"
        with manifest_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()))
            w.writeheader()
            w.writerows(manifest_rows)
        print(f"\nmanifest  : {manifest_path}  ({len(manifest_rows)} rows)")

    print("\n=== 클래스별 프레임 수 ===")
    target = 100
    for cls in sorted(class_counts):
        n = class_counts[cls]
        flag = "  ⚠️ <100" if n < target and not args.dry_run else ""
        print(f"  {cls:<20} {n:>4}{flag}")

    if skipped:
        print(f"\n스킵 소스   : {', '.join(skipped)}")


if __name__ == "__main__":
    main()
