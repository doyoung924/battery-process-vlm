"""config-driven 프레임 추출 — configs/frame_sources.yaml 의 chapter 순회.

산출 구조:
    data/frames/v{N}_unlabeled/{series}/v{N}_{series}_{idx:03d}.jpg

원칙:
- split ∈ {train, val, test} 만 처리 (excluded 스킵)
- status: pre-extracted (v1) 스킵 — 이미 data/frames/v1_unlabeled/ 존재
- class: TBD 인 chapter 스킵 (사용자가 라벨 결정 후 재실행)
- skip: true 인 chapter 스킵
- 이미 프레임 있는 폴더 스킵 (재실행 안전, --force 로 재추출)
- shorts 는 대상 아님 (policy: holdout_only, 별도 처리)

Usage:
    .venv/bin/python scripts/extract_frames.py                # 전체
    .venv/bin/python scripts/extract_frames.py --source v17   # 특정 소스
    .venv/bin/python scripts/extract_frames.py --dry-run      # 계획만
    .venv/bin/python scripts/extract_frames.py --force        # 재추출
"""
import argparse
import subprocess
from pathlib import Path

import yaml


def fmt_dur(s: float) -> str:
    s = int(s)
    return f"{s // 60}:{s % 60:02d}"


def extract_chapter(video: Path, start: float, end: float, interval: float,
                    out_dir: Path, prefix: str) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(out_dir / f"{prefix}_%03d.jpg")
    # -ss 를 -i 뒤에 두어 정확한 seek (프레임 정확도 우선, 짧은 chapter 라 속도 무관)
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video),
         "-ss", f"{start}", "-to", f"{end}",
         "-vf", f"fps=1/{interval}", "-q:v", "2", pattern],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed on {video.name} {fmt_dur(start)}-{fmt_dur(end)}:\n{r.stderr[-500:]}")
    return len(list(out_dir.glob(f"{prefix}_*.jpg")))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=Path("configs/frame_sources.yaml"))
    ap.add_argument("--source", type=str, default=None, help="특정 소스 id (예: v17)")
    ap.add_argument("--out-root", type=Path, default=None, help="config extraction.output_root 대신")
    ap.add_argument("--dry-run", action="store_true", help="추출 없이 계획만 출력")
    ap.add_argument("--force", action="store_true", help="기존 프레임 삭제 후 재추출")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    default_interval = cfg["extraction"]["interval_seconds"]
    out_root = args.out_root or Path(cfg["extraction"]["output_root"])

    print(f"config    : {args.config}")
    print(f"interval  : {default_interval}s (default, chapter 별 override 허용)")
    print(f"out_root  : {out_root}")
    print(f"dry_run   : {args.dry_run}   force: {args.force}")
    print()

    total_frames = 0
    total_chapters = 0
    tbd_chapters = []
    skipped_sources = []

    for s in cfg["sources"]:
        sid = s["id"]
        if args.source and sid != args.source:
            continue
        if s["split"] not in ("train", "val", "test"):
            skipped_sources.append(f"{sid} [{s['split']}]")
            continue
        if s.get("status") == "pre-extracted":
            skipped_sources.append(f"{sid} [pre-extracted]")
            continue

        video = Path(s["video"])
        if not video.exists():
            print(f"⚠️  {sid} video not found: {video}")
            continue

        chapters = s.get("chapters", [])
        if not chapters:
            skipped_sources.append(f"{sid} [chapters=[]]")
            continue

        video_out = out_root / f"{sid}_unlabeled"
        print(f"[{sid}] split={s['split']}  {video.name}")

        for ch in chapters:
            cls = ch.get("class")
            series = ch["series"]
            start, end = ch["start"], ch["end"]
            # chapter 별 interval override (미지정 시 default). narrow gold clip 은 짧게, wide 는 default.
            ch_interval = ch.get("interval", default_interval)

            if cls == "TBD":
                tbd_chapters.append(f"{sid}:{series} ({fmt_dur(start)}-{fmt_dur(end)})")
                print(f"  ! skip {series} ({fmt_dur(start)}-{fmt_dur(end)}): class=TBD")
                continue
            if ch.get("skip"):
                print(f"  ! skip {series}: skip=true")
                continue

            series_dir = video_out / series
            prefix = f"{sid}_{series}"
            existing = list(series_dir.glob(f"{prefix}_*.jpg")) if series_dir.exists() else []

            if existing and not args.force:
                print(f"  = {series} ({fmt_dur(start)}-{fmt_dur(end)})  [exists: {len(existing)} frames, skip]")
                total_chapters += 1
                total_frames += len(existing)
                continue

            expected = max(1, int((end - start) / ch_interval))
            interval_note = f"@{ch_interval}s" if ch_interval != default_interval else ""
            if args.dry_run:
                action = "would extract"
                n = expected
                if args.force and existing:
                    action += f" (force, deletes {len(existing)} existing)"
            else:
                if args.force and existing:
                    for f in existing:
                        f.unlink()
                n = extract_chapter(video, start, end, ch_interval, series_dir, prefix)
                action = "extracted"

            print(f"  + {series} ({fmt_dur(start)}-{fmt_dur(end)} {interval_note}) → {series_dir.relative_to(Path.cwd()) if series_dir.is_absolute() else series_dir}  [{action} {n} frames, class={cls}]")
            total_chapters += 1
            total_frames += n

    print()
    print("=== 요약 ===")
    print(f"처리 chapter : {total_chapters}")
    print(f"프레임 합계  : {total_frames}  ({'예상' if args.dry_run else '실제'})")
    if skipped_sources:
        print(f"스킵 소스    : {', '.join(skipped_sources)}")
    if tbd_chapters:
        print(f"TBD chapter  : {', '.join(tbd_chapters)}")
        print("  → configs/frame_sources.yaml 의 class 결정 후 재실행")


if __name__ == "__main__":
    main()
