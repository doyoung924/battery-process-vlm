"""config 기반 다중 영상 프레임 선별 — configs/frame_sources.yaml 순회.

전 소스가 chapter 기반 (2026-09-08 밤 라운드 2 이후):
    폴더명이 series (coat_hmhH, v1_ccs 등). config chapter 의 class 필드 참조.

산출:
    data/frames/v2_selected/{split}/{class}/{source_id}_{stem}.jpg
    data/frames/v2_selected/manifest.csv

이력:
    2026-08-16 초판 — v1 단독 선별 (v1_selected/)
    2026-09-02 개정 — config 기반 다중 영상, split 인식, pilot 상한 assert
    2026-09-08 밤 라운드 2 — v1 pre-extracted 폐기, chapter 기반 통일
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import imagehash
import yaml
from PIL import Image

CONFIG_DEFAULT = Path("configs/frame_sources.yaml")
FRAMES_ROOT = Path("data/frames")
OUT_ROOT_DEFAULT = Path("data/frames/v2_selected")

# v1 pre-extracted 방식 폐기 (2026-09-08 밤 라운드 2).
# 기존 클래스별 폴더는 data/frames/v1_unlabeled/_archive_pre_chapter/ 로 백업.
# v1 도 이제 chapter 기반 (v1_ccs, v1_we) → 아래 V1_CLASS_MAP 은 dead code.
# 재도입 필요 시 참고용으로 남김.
_V1_CLASS_MAP_LEGACY: dict[str, tuple[str, int | None, int | None]] = {
    "slot_die":       ("coating_die",    None, None),
    "calendering":    ("roll_press",     None, None),
    "slitter_knife":  ("slitting_knife",  8,   None),
    "slitting":       ("slitting_knife", None, None),
    "winding":        ("winding_core",   None, None),
    "numbered_core":  ("winding_core",     5,    30),
}

# v2+ series pHash dedup threshold.
# 정밀 스크러빙 + narrow chapter + 촘촘 interval 방침(2026-09-08 밤 라운드 2) 이후
# 시리즈 기본 dedup 활성화 (dense 추출로 근중복 프레임 증가 대응).
# 값 클수록 aggressive (더 많이 dedup). 정적 카메라 배터리 공정 영상은 8~10 권장.
SERIES_DEFAULT_THRESHOLD = 8
# 시리즈별 오버라이드 (더 완화하고 싶은 동적 클립 등).
SERIES_THRESHOLDS: dict[str, int] = {}

EXCLUDE_PREFIX = "Gemini_Generated_Image"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
ZONE_IDENTIFIER = ":Zone.Identifier"

# v1 파일명 시리즈 키 (pre-extracted 방식 폐기로 dead code — archive 참조 시 재활성).
_V1_SERIES_PATTERNS_LEGACY = [
    re.compile(r"^([a-z]+_[a-z])_\d+$"),   # coat_a_0001 → coat_a
    re.compile(r"^frame_([a-z])\d+$"),     # frame_a0001 → frame_a
]


@dataclass
class SourceItem:
    source_id: str
    split: str
    scale: str
    channel_pool: str
    target_class: str
    folder: Path
    threshold: int | None
    stride_cap: int | None


@dataclass
class Row:
    source_id: str
    split: str
    scale: str
    channel_pool: str
    source_path: Path
    target_class: str
    series: str
    phash: str
    kept: bool
    drop_reason: str


def iter_source_files(folder: Path):
    if not folder.is_dir():
        return
    for p in sorted(folder.iterdir()):
        if p.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if ZONE_IDENTIFIER in p.name:
            continue
        yield p


def build_source_items(cfg: dict) -> list[SourceItem]:
    items: list[SourceItem] = []
    for s in cfg["sources"]:
        sid = s["id"]
        if s["split"] not in ("train", "val", "test"):
            continue
        scale = s.get("scale", "unknown")
        pool = s.get("channel_pool", "unknown")

        v_root = FRAMES_ROOT / f"{sid}_unlabeled"
        for ch in s.get("chapters", []):
            if ch.get("skip") or ch.get("class") in (None, "TBD"):
                continue
            series = ch["series"]
            folder = v_root / series
            # 시리즈별 override → 없으면 기본값. dense 추출 시 근중복 자동 필터.
            thresh = SERIES_THRESHOLDS.get(series, SERIES_DEFAULT_THRESHOLD)
            items.append(SourceItem(sid, s["split"], scale, pool, ch["class"], folder, thresh, None))
    return items


def process_item(item: SourceItem) -> list[Row]:
    rows: list[Row] = []
    if not item.folder.is_dir():
        return rows

    grouped: dict[str, list[Path]] = defaultdict(list)
    for path in iter_source_files(item.folder):
        if path.name.startswith(EXCLUDE_PREFIX):
            rows.append(Row(item.source_id, item.split, item.scale, item.channel_pool,
                            path, item.target_class, "", "", False, "synthetic"))
            continue
        # 전 소스 chapter 기반 통일 (2026-09-08 밤 라운드 2): 폴더 자체가 series
        key = item.folder.name
        grouped[key].append(path)

    for series, paths in grouped.items():
        kept_hashes: list[tuple[str, imagehash.ImageHash]] = []
        for path in paths:
            try:
                with Image.open(path) as im:
                    ph = imagehash.phash(im)
            except Exception as e:
                rows.append(Row(item.source_id, item.split, item.scale, item.channel_pool,
                                path, item.target_class, series, "", False, f"error:{type(e).__name__}"))
                continue

            drop_of = None
            if item.threshold is not None:
                for prev_name, prev_h in kept_hashes:
                    if ph - prev_h <= item.threshold:
                        drop_of = prev_name
                        break
            if drop_of:
                rows.append(Row(item.source_id, item.split, item.scale, item.channel_pool,
                                path, item.target_class, series, str(ph), False, f"dup_of:{drop_of}"))
            else:
                kept_hashes.append((path.name, ph))
                rows.append(Row(item.source_id, item.split, item.scale, item.channel_pool,
                                path, item.target_class, series, str(ph), True, ""))

    if item.stride_cap:
        apply_stride_cap(rows, item.stride_cap)
    return rows


def apply_stride_cap(rows: list[Row], target_total: int) -> None:
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
        stride = n_series / keep_n
        keep_idx = {int(i * stride) for i in range(keep_n)}
        for i, r in enumerate(series_rows):
            if i not in keep_idx:
                r.kept = False
                r.drop_reason = f"stride:cap={target_total}"


def copy_kept(rows: list[Row], out_root: Path) -> None:
    for r in rows:
        if not r.kept:
            continue
        dest_dir = out_root / r.split / r.target_class
        dest_dir.mkdir(parents=True, exist_ok=True)
        # source_id prefix 강제 (Roboflow split 자동 인식 목적)
        dest_name = r.source_path.name
        if not dest_name.startswith(f"{r.source_id}_"):
            dest_name = f"{r.source_id}_{dest_name}"
        shutil.copy2(r.source_path, dest_dir / dest_name)


def write_manifest(rows: list[Row], out_root: Path) -> Path:
    out_root.mkdir(parents=True, exist_ok=True)
    manifest = out_root / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source_id", "split", "scale", "channel_pool",
                    "source_path", "target_class", "series", "phash",
                    "kept", "drop_reason"])
        for r in rows:
            w.writerow([r.source_id, r.split, r.scale, r.channel_pool,
                        str(r.source_path), r.target_class, r.series, r.phash,
                        str(r.kept), r.drop_reason])
    return manifest


def print_summary(rows: list[Row], pilot_ratio_max: float, xiaowei_ratio_max: float) -> list[str]:
    stats = defaultdict(lambda: defaultdict(int))
    for r in rows:
        if r.kept:
            stats[r.split][r.target_class] += 1

    all_classes = sorted({c for d in stats.values() for c in d})
    print("\n=== split × class 카운트 (kept) ===")
    header = f"{'split':6s} " + " ".join(f"{c:>15s}" for c in all_classes) + f"  {'total':>7s}"
    print(header)
    for split in ["train", "val", "test"]:
        line = f"{split:6s} "
        total = 0
        for c in all_classes:
            n = stats[split].get(c, 0)
            line += f"{n:15d} "
            total += n
        print(line + f"  {total:7d}")

    # train pilot / xiaowei 비율 assert
    print(f"\n=== train: 클래스별 스케일·채널 비율 (상한 pilot {pilot_ratio_max:.0%} / xiaowei {xiaowei_ratio_max:.0%}) ===")
    scale_stats = defaultdict(lambda: defaultdict(int))   # cls → scale → count
    pool_stats  = defaultdict(lambda: defaultdict(int))   # cls → channel_pool → count
    for r in rows:
        if r.kept and r.split == "train":
            scale_stats[r.target_class][r.scale] += 1
            pool_stats[r.target_class][r.channel_pool] += 1

    warnings: list[str] = []
    for cls in sorted(scale_stats):
        factory = scale_stats[cls].get("factory", 0)
        pilot   = scale_stats[cls].get("pilot", 0)
        xiaowei = pool_stats[cls].get("xiaowei", 0)
        other_p = pool_stats[cls].get("other_pilot", 0)
        total = factory + pilot
        if total == 0:
            continue
        p_ratio = pilot / total
        x_ratio = xiaowei / total
        flag = ""
        if p_ratio > pilot_ratio_max:
            flag += "  ⚠️ pilot 초과"
            warnings.append(f"{cls}: pilot {p_ratio:.1%} > {pilot_ratio_max:.0%}")
        if x_ratio > xiaowei_ratio_max:
            flag += "  ⚠️ xiaowei 초과"
            warnings.append(f"{cls}: xiaowei {x_ratio:.1%} > {xiaowei_ratio_max:.0%}")
        print(f"  {cls:16s}  factory={factory:4d}  pilot={pilot:4d}"
              f"  (xiaowei={xiaowei:3d}, other_pilot={other_p:3d})"
              f"  pilot_ratio={p_ratio:.1%}{flag}")

    return warnings


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=CONFIG_DEFAULT)
    ap.add_argument("--out-root", type=Path, default=OUT_ROOT_DEFAULT)
    ap.add_argument("--force", action="store_true", help="기존 출력 폴더 삭제 후 재생성")
    ap.add_argument("--dry-run", action="store_true", help="계산만 (파일 복사 안 함)")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    policy = cfg.get("policy", {})
    pilot_ratio_max = policy.get("scale_cap", {}).get("pilot_ratio_max", 0.30)
    xiaowei_ratio_max = policy.get("channel_cap", {}).get("xiaowei_ratio_max", 0.20)

    print(f"config    : {args.config}")
    print(f"out_root  : {args.out_root}")
    print(f"policy    : pilot ≤ {pilot_ratio_max:.0%}, xiaowei ≤ {xiaowei_ratio_max:.0%}")
    print(f"dry_run={args.dry_run}  force={args.force}")

    if args.out_root.exists() and any(args.out_root.iterdir()):
        if not args.force and not args.dry_run:
            raise SystemExit(f"❌ {args.out_root} 이미 존재 (비어있지 않음). --force 로 재생성 or 수동 삭제")
        if args.force and not args.dry_run:
            print(f"🗑  {args.out_root} 삭제 후 재생성 (--force)")
            shutil.rmtree(args.out_root)

    items = build_source_items(cfg)
    print(f"\n처리 대상 items: {len(items)}")

    all_rows: list[Row] = []
    for item in items:
        rows = process_item(item)
        all_rows.extend(rows)

    if not args.dry_run:
        write_manifest(all_rows, args.out_root)
        copy_kept(all_rows, args.out_root)

    warnings = print_summary(all_rows, pilot_ratio_max, xiaowei_ratio_max)

    if not args.dry_run:
        print(f"\nmanifest: {args.out_root / 'manifest.csv'}")
        print(f"copies:   {args.out_root}/<split>/<class>/")

    if warnings:
        print("\n⚠️  상한 초과 항목:")
        for w in warnings:
            print(f"  - {w}")
        print("   대응: factory 소스 추가 / pilot stride cap 강화 / Xiaowei 소스 배제")


if __name__ == "__main__":
    main()
