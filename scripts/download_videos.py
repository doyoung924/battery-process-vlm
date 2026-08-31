"""롱폼 4개 + Shorts 7개를 yt-dlp 로 다운로드한다.

labeling_plan.md 에서 확정한 소스 목록. 각 영상은 mp4 (H264, 1080p 이하)와
info.json (챕터 배열 포함)을 함께 저장한다. Shorts 는 별도 폴더로 분리.

의존: yt-dlp, ffmpeg. `.venv/bin/python scripts/download_videos.py`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RAW_DIR = Path("data/raw_videos")
SHORTS_DIR = RAW_DIR / "shorts"
COOKIES = Path("cookies.txt")  # 있으면 --cookies 옵션 자동 추가 (PO Token 우회)

# (prefix, youtube_id, 메모)
LONGFORM = [
    ("v2_j1jW", "j1jWp9WxGLM", "Zeekr Z Factory (Everything Electric CARS, 10:50)"),
    ("v3_zbBx", "zbBxJLGaoys", "Processlytic 4K (16:32, 챕터 없음)"),
    ("v4_hmhH", "hmhHPvDErhM", "CATL Lightning-Fast (4:17)"),
    ("v5_UHZg", "UHZg5-uk1-k", "How It's Made 2018 (2:19, 12챕터)"),
]

SHORTS = [
    ("s1_Owqn", "OwqnjMAXs6c", "coating slot-die close-up (infinityPV)"),
    ("s2_SNiT", "SNiTgaNbWcc", "slot-die explained (infinityPV)"),
    ("s3_Urld", "Urld0ddZn-w", "calendering (Motoma)"),
    ("s4_by7G", "by7GjvtrfyI", "copper foil slitting (Athena)"),
    ("s5_70fq", "70fq0Pw8RJo", "separator slitting (Xiaowei)"),
    ("s6_rhTC", "rhTC2rNwkuk", "60138 winding (TOB)"),
    ("s7_Ecik", "EcikXB0Lq38", "3종 셀 오버뷰 (lipowergroup)"),
]

# H264/1080p 이하 (OpenCV 호환), avc1 우선
COMMON_ARGS = [
    "-f", "bv*[vcodec^=avc1][height<=1080]+ba/b[vcodec^=avc1][height<=1080]/bv*[height<=1080]+ba/b[height<=1080]",
    "--merge-output-format", "mp4",
    "--write-info-json",
    "--no-progress",
    "--quiet",
    "--no-warnings",
]


def download(prefix: str, ytid: str, memo: str, out_dir: Path, is_short: bool) -> bool:
    out_dir.mkdir(parents=True, exist_ok=True)
    mp4 = out_dir / f"{prefix}.mp4"
    if mp4.exists():
        print(f"→ {prefix} ({memo}) — 이미 있음 skip")
        return True
    url = f"https://www.youtube.com/shorts/{ytid}" if is_short else f"https://www.youtube.com/watch?v={ytid}"
    out_template = str(out_dir / f"{prefix}.%(ext)s")
    print(f"→ {prefix} ({memo})")
    args = list(COMMON_ARGS)
    if COOKIES.exists():
        args += ["--cookies", str(COOKIES)]
    try:
        subprocess.run(
            [".venv/bin/yt-dlp", *args, "-o", out_template, url],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"  실패: {e}")
        return False
    if not mp4.exists():
        print(f"  실패: mp4 없음")
        return False
    info = out_dir / f"{prefix}.info.json"
    size_mb = mp4.stat().st_size / 1024 / 1024
    print(f"  OK: {mp4.name} ({size_mb:.1f}MB) + {'info.json' if info.exists() else 'NO info.json'}")
    return True


def main() -> None:
    print(f"[LONGFORM {len(LONGFORM)}개 → {RAW_DIR}]")
    long_ok = sum(download(p, i, m, RAW_DIR, False) for p, i, m in LONGFORM)
    print()
    print(f"[SHORTS {len(SHORTS)}개 → {SHORTS_DIR}]")
    short_ok = sum(download(p, i, m, SHORTS_DIR, True) for p, i, m in SHORTS)
    print()
    print(f"완료: 롱폼 {long_ok}/{len(LONGFORM)}, Shorts {short_ok}/{len(SHORTS)}")
    if long_ok < len(LONGFORM) or short_ok < len(SHORTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
