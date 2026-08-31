"""v1_unlabeled 폴더에서 재라벨링용 프레임을 선별한다.

leak_diagnosis.md 근거 5·6의 결론(라벨을 원본 프레임에서 다시 그린다)에 따라
1920×1080 실사 프레임만 남기고, 인접 프레임의 perceptual hash 유사도로 중복을 제거한다.
polar 요약과 감사용 매니페스트(kept/dropped 모두)를 남긴다.

의존: Pillow, ImageHash. `.venv/bin/python scripts/select_frames.py`.
"""

from __future__ import annotations

import csv
import math
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import imagehash
from PIL import Image

FRAMES_ROOT = Path("data/frames/v1_unlabeled")
OUT_ROOT = Path("data/frames/v1_selected")
MANIFEST = OUT_ROOT / "manifest.csv"

# (source_folder, phash_hamming_threshold) — threshold=None 이면 dedup 건너뜀
CLASS_MAP: dict[str, list[tuple[str, int | None]]] = {
    "coating_die":    [("slot_die", None), ("coating_extra", None)],
    "roll_press":     [("calendering", None)],
    "slitting_knife": [("slitter_knife", 8), ("slitting", None)],
    "winding_core":   [("winding", None), ("numbered_core", 5)],
}
# pHash dedup 후 폴더 총 유지 상한. 시리즈별 kept 비율에 맞춰 균등 간격 stride 샘플링.
MAX_AFTER_DEDUP: dict[str, int] = {
    "numbered_core": 30,  # winding 118 + numbered_core 30 ≈ 목표 150
}
EXCLUDE_PREFIX = "Gemini_Generated_Image"
EXPECTED_SIZE = (1920, 1080)
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
ZONE_IDENTIFIER = ":Zone.Identifier"

# 파일명에서 series 키를 뽑는다. 매칭 실패 시 파일 stem 자체를 사용
# (그 파일은 자기 그룹에 혼자 → dedup 대상에서 자연스레 빠진다)
SERIES_PATTERNS = [
    re.compile(r"^([a-z]+_[a-z])_\d+$"),  # coat_a_0001, ca_a_0001, wi_b_0002 → coat_a
    re.compile(r"^frame_([a-z])\d+$"),    # frame_a0001, frame_e0150 → frame_a
]


@dataclass
class Row:
    source_path: Path
    target_class: str
    series: str
    phash: str
    kept: bool
    drop_reason: str


def series_key(stem: str) -> str:
    for pat in SERIES_PATTERNS:
        m = pat.match(stem)
        if m:
            return m.group(1)
    return f"__solo__:{stem}"


def iter_source_files(folder: Path):
    if not folder.is_dir():
        return
    for p in sorted(folder.iterdir()):
        if p.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if ZONE_IDENTIFIER in p.name:
            continue
        yield p


def process_folder(
    folder: Path, target_class: str, threshold: int | None
) -> list[Row]:
    rows: list[Row] = []
    # series별로 (stem 순 정렬된) 파일 수집
    grouped: dict[str, list[Path]] = defaultdict(list)
    for path in iter_source_files(folder):
        if path.name.startswith(EXCLUDE_PREFIX):
            rows.append(Row(path, target_class, "", "", False, "synthetic"))
            continue
        grouped[series_key(path.stem)].append(path)

    for series, paths in grouped.items():
        kept_hashes: list[tuple[str, imagehash.ImageHash]] = []
        for path in paths:
            try:
                with Image.open(path) as im:
                    if im.size != EXPECTED_SIZE:
                        rows.append(
                            Row(path, target_class, series, "", False, f"resolution:{im.size[0]}x{im.size[1]}")
                        )
                        continue
                    ph = imagehash.phash(im)
            except Exception as e:  # 손상 파일 방어
                rows.append(Row(path, target_class, series, "", False, f"error:{type(e).__name__}"))
                continue

            drop_of = None
            if threshold is not None:
                for prev_name, prev_h in kept_hashes:
                    if ph - prev_h <= threshold:
                        drop_of = prev_name
                        break
            if drop_of is not None:
                rows.append(Row(path, target_class, series, str(ph), False, f"dup_of:{drop_of}"))
            else:
                kept_hashes.append((path.name, ph))
                rows.append(Row(path, target_class, series, str(ph), True, ""))

    cap = MAX_AFTER_DEDUP.get(folder.name)
    if cap is not None:
        apply_stride_cap(rows, cap)
    return rows


def apply_stride_cap(rows: list[Row], target_total: int) -> None:
    """dedup 후 kept 프레임이 target_total 을 넘으면 시리즈별 비율에 맞춰 균등 stride 로 축소."""
    by_series: dict[str, list[Row]] = defaultdict(list)
    for r in rows:
        if r.kept:
            by_series[r.series].append(r)
    kept_total = sum(len(v) for v in by_series.values())
    if kept_total <= target_total:
        return
    for series, series_rows in by_series.items():
        n_series = len(series_rows)
        keep_n = max(1, math.floor(target_total * n_series / kept_total))
        if keep_n >= n_series:
            continue
        # 균등 인덱스: 0, stride, 2*stride, ...
        stride = n_series / keep_n
        keep_idx = {int(i * stride) for i in range(keep_n)}
        for i, r in enumerate(series_rows):
            if i not in keep_idx:
                r.kept = False
                r.drop_reason = f"stride:cap={target_total}"


def copy_kept(rows: list[Row]) -> None:
    for row in rows:
        if not row.kept:
            continue
        dest_dir = OUT_ROOT / row.target_class
        dest_dir.mkdir(parents=True, exist_ok=True)
        # stem 유지, 확장자는 원본 그대로
        shutil.copy2(row.source_path, dest_dir / row.source_path.name)


def write_manifest(rows: list[Row]) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source_path", "target_class", "series", "phash", "kept", "drop_reason"])
        for r in rows:
            w.writerow([str(r.source_path), r.target_class, r.series, r.phash, str(r.kept), r.drop_reason])


def print_summary(rows: list[Row]) -> None:
    by_class = defaultdict(list)
    for r in rows:
        by_class[r.target_class].append(r)

    total_kept = 0
    for cls in CLASS_MAP:
        cls_rows = by_class.get(cls, [])
        kept = sum(1 for r in cls_rows if r.kept)
        dropped = len(cls_rows) - kept
        reasons = Counter(
            r.drop_reason.split(":", 1)[0] for r in cls_rows if not r.kept
        )
        reason_str = ", ".join(f"{k} {v}" for k, v in reasons.most_common())
        print(f"{cls}: kept {kept} / dropped {dropped} ({reason_str or 'none'})")
        total_kept += kept
    print(f"TOTAL kept: {total_kept}")


def main() -> None:
    all_rows: list[Row] = []
    for target_class, sources in CLASS_MAP.items():
        for folder_name, threshold in sources:
            folder = FRAMES_ROOT / folder_name
            all_rows.extend(process_folder(folder, target_class, threshold))

    write_manifest(all_rows)
    copy_kept(all_rows)
    print_summary(all_rows)
    print(f"manifest: {MANIFEST}")
    print(f"copies:   {OUT_ROOT}/<class>/")


if __name__ == "__main__":
    main()
