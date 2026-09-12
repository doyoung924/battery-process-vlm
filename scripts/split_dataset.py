"""Roboflow export 를 라운드4 배정표에 맞춰 train/val/test 로 재분배한다.

배정 규칙은 docs/labeling_spec_v1.md 의 "분할 배정" 절과 1:1 대응한다.
Roboflow 의 auto-split 은 프레임 단위라 시간·소스 경계를 무시하고 근접
프레임을 다른 split 으로 흘려보내 실질적 누수를 만든다. 이 스크립트는
그 배정을 폐기하고 매니페스트의 series/timecode 로 다시 배정한다.

electrode_roll  : 소스 단위 (v1→train, v4→val, v17→test)
pouch_cell_tray : v1 26:00~28:30 train / 28:30~29:15 val / 29:15~30:00 test
prismatic_cell  : v10 0:00~3:30 train / 3:30~4:30 val / 4:30~5:25 test
mixing_tank     : 보류 → _holdout/ 에 보관, split 에 넣지 않는다
"""

import argparse
import csv
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROBOFLOW_SUFFIX = re.compile(r"_(png|jpg|jpeg)\.rf\.[0-9a-f]+$", re.IGNORECASE)
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
ZONE_IDENTIFIER = ":Zone.Identifier"

# (start_sec, end_sec_exclusive, split). 끝값은 배타적으로 다룬다.
POUCH_TIME_SPLIT = [
    (1560.0, 1710.0, "train"),   # 26:00 ~ 28:30
    (1710.0, 1755.0, "val"),     # 28:30 ~ 29:15
    (1755.0, 1800.0, "test"),    # 29:15 ~ 30:00
]
PRISMATIC_TIME_SPLIT = [
    (0.0,   210.0, "train"),     # 0:00 ~ 3:30
    (210.0, 270.0, "val"),       # 3:30 ~ 4:30
    (270.0, 325.0, "test"),      # 4:30 ~ 5:25
]
ELECTRODE_ROLL_SPLIT = {
    "v1_er_a": "train", "v1_er_b": "train", "v1_er_c": "train",
    "v4_er_a": "val",
    "v17_er_a": "test",
}

SPLITS = ("train", "val", "test")


def is_image(name: str) -> bool:
    return ZONE_IDENTIFIER not in name and Path(name).suffix.lower() in IMAGE_SUFFIXES


def strip_roboflow_suffix(stem: str) -> str:
    """`v1_v1_er_a_0004_jpg.rf.HASH` → `v1_v1_er_a_0004`.

    증강본은 hash 만 다르고 base 는 공유하므로 base 를 배정 단위로 쓴다.
    """
    return ROBOFLOW_SUFFIX.sub("", stem)


def load_manifest(path: Path) -> dict[str, dict]:
    """매니페스트를 base stem 키로 인덱싱한다.

    매니페스트 filename 은 `<class>/v1_v1_er_a_0004.jpg` 형식. Roboflow export
    는 클래스 폴더 정보를 잃고 flat 하게 되므로 stem 만으로 조회 가능해야 한다.
    """
    index: dict[str, dict] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stem = Path(row["filename"]).stem
            index[stem] = {
                "class": row["class"],
                "series": row["series"],
                "timecode_seconds": float(row["timecode_seconds"]),
            }
    return index


def assign_split(cls: str, series: str, timecode: float) -> tuple[str, str]:
    """(split, reason) 을 돌려준다. split 이 None 이면 배정 불가."""
    if cls == "electrode_roll":
        split = ELECTRODE_ROLL_SPLIT.get(series)
        if split is None:
            return (None, f"electrode_roll 인데 배정표에 없는 series: {series}")
        return (split, f"electrode_roll series={series}")
    if cls == "pouch_cell_tray":
        for start, end, split in POUCH_TIME_SPLIT:
            if start <= timecode < end:
                return (split, f"pouch {timecode:.0f}s in [{start:.0f},{end:.0f})")
        return (None, f"pouch_cell_tray 인데 배정 구간 밖: {timecode:.0f}s")
    if cls == "prismatic_cell_tray":
        for start, end, split in PRISMATIC_TIME_SPLIT:
            if start <= timecode < end:
                return (split, f"prismatic {timecode:.0f}s in [{start:.0f},{end:.0f})")
        return (None, f"prismatic_cell_tray 인데 배정 구간 밖: {timecode:.0f}s")
    if cls == "mixing_tank":
        return ("_holdout", "mixing_tank 보류")
    return (None, f"알 수 없는 클래스: {cls}")


def iter_input_images(root: Path):
    """Roboflow export 하위 이미지 전부. 이미 분할되어 있어도 무시하고 다 훑는다."""
    for images_dir in root.rglob("images"):
        if not images_dir.is_dir():
            continue
        for p in images_dir.iterdir():
            if p.is_file() and is_image(p.name):
                yield p


def label_path_for(image_path: Path) -> Path:
    return image_path.parent.parent / "labels" / (image_path.stem + ".txt")


def count_boxes(label_file: Path) -> Counter:
    """YOLO 라벨 파일의 클래스 인덱스별 박스 수."""
    counts: Counter = Counter()
    if not label_file.exists():
        return counts
    for line in label_file.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if not parts:
            continue
        try:
            counts[int(parts[0])] += 1
        except ValueError:
            continue
    return counts


def read_class_names(root: Path) -> list[str]:
    """Roboflow data.yaml 의 names 리스트."""
    yaml = root / "data.yaml"
    if not yaml.exists():
        return []
    for line in yaml.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("names:"):
            body = line.partition(":")[2].strip().strip("[]")
            return [n.strip().strip("'\"") for n in body.split(",") if n.strip()]
    return []


def format_table(rows: list[list[str]]) -> str:
    """왼쪽 정렬 헤더 + 오른쪽 정렬 숫자 표."""
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    out = []
    for i, row in enumerate(rows):
        cells = []
        for j, cell in enumerate(row):
            justify = str.ljust if j == 0 else str.rjust
            cells.append(justify(str(cell), widths[j]))
        out.append("  ".join(cells))
        if i == 0:
            out.append("  ".join("-" * w for w in widths))
    return "\n".join(out)


def plan(input_root: Path, manifest: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    """(배정 성공 리스트, 누락/오류 리스트)."""
    assigned: list[dict] = []
    unresolved: list[dict] = []
    for img in iter_input_images(input_root):
        base = strip_roboflow_suffix(img.stem)
        info = manifest.get(base)
        if info is None:
            unresolved.append({"image": img, "reason": f"매니페스트에 없음: base={base}"})
            continue
        split, reason = assign_split(info["class"], info["series"], info["timecode_seconds"])
        record = {
            "image": img,
            "label": label_path_for(img),
            "base": base,
            "class": info["class"],
            "series": info["series"],
            "timecode": info["timecode_seconds"],
            "split": split,
            "reason": reason,
        }
        if split is None:
            unresolved.append(record)
        else:
            assigned.append(record)
    return assigned, unresolved


def check_leakage(assigned: list[dict]) -> dict[str, set[str]]:
    """같은 base 가 여러 split 에 걸쳐 있는지 검사한다.

    배정 로직이 base 단위로 결정론적이라 원칙적으로 발생 불가하지만, 매니페스트
    중복 항목·경계값 오류를 잡는 안전망으로 실행 후 검증한다.
    """
    per_base: dict[str, set[str]] = defaultdict(set)
    for r in assigned:
        per_base[r["base"]].add(r["split"])
    return {base: splits for base, splits in per_base.items() if len(splits) > 1}


def emit_summary(assigned: list[dict], class_names: list[str]) -> None:
    # split × 이미지 base 수 (증강본 접기 전 원본 기준)
    by_split_bases: dict[str, set[str]] = defaultdict(set)
    by_split_files: Counter = Counter()
    by_split_class_bases: dict[tuple[str, str], set[str]] = defaultdict(set)
    by_split_class_boxes: Counter = Counter()

    for r in assigned:
        by_split_bases[r["split"]].add(r["base"])
        by_split_files[r["split"]] += 1
        by_split_class_bases[(r["split"], r["class"])].add(r["base"])
        for cls_idx, n in count_boxes(r["label"]).items():
            name = class_names[cls_idx] if 0 <= cls_idx < len(class_names) else f"cls{cls_idx}"
            by_split_class_boxes[(r["split"], name)] += n

    print("\n[이미지 수] split × 클래스 (원본 base 기준, 증강본 접음)")
    classes = sorted({c for _, c in by_split_class_bases})
    rows = [["class", *SPLITS, "_holdout", "total"]]
    for c in classes:
        row = [c]
        total = 0
        for sp in SPLITS + ("_holdout",):
            n = len(by_split_class_bases.get((sp, c), set()))
            row.append(n)
            total += n
        row.append(total)
        rows.append(row)
    footer = ["TOTAL"]
    for sp in SPLITS + ("_holdout",):
        footer.append(len(by_split_bases.get(sp, set())))
    footer.append(sum(len(v) for v in by_split_bases.values()))
    rows.append(footer)
    print(format_table(rows))

    print("\n[박스 수] split × 클래스 (증강본 포함, 라벨 파일 line 합)")
    box_classes = sorted({c for _, c in by_split_class_boxes})
    rows = [["class", *SPLITS, "_holdout", "total"]]
    for c in box_classes:
        row = [c]
        total = 0
        for sp in SPLITS + ("_holdout",):
            n = by_split_class_boxes.get((sp, c), 0)
            row.append(n)
            total += n
        row.append(total)
        rows.append(row)
    rows.append([
        "TOTAL",
        *[sum(by_split_class_boxes.get((sp, c), 0) for c in box_classes) for sp in SPLITS + ("_holdout",)],
        sum(by_split_class_boxes.values()),
    ])
    print(format_table(rows))

    print("\n[파일 수] split (증강본 포함)")
    for sp in SPLITS + ("_holdout",):
        print(f"  {sp:<10} {by_split_files.get(sp, 0):>6}")


def write_data_yaml(output_root: Path, class_names: list[str]) -> None:
    names_str = "[" + ", ".join(f"'{n}'" for n in class_names) + "]"
    body = (
        "train: ../train/images\n"
        "val: ../val/images\n"
        "test: ../test/images\n"
        "\n"
        f"nc: {len(class_names)}\n"
        f"names: {names_str}\n"
    )
    (output_root / "data.yaml").write_text(body, encoding="utf-8")


def execute(assigned: list[dict], output_root: Path, class_names: list[str], move: bool) -> None:
    for sp in SPLITS + ("_holdout",):
        (output_root / sp / "images").mkdir(parents=True, exist_ok=True)
        (output_root / sp / "labels").mkdir(parents=True, exist_ok=True)
    for r in assigned:
        dst_img = output_root / r["split"] / "images" / r["image"].name
        dst_lbl = output_root / r["split"] / "labels" / r["label"].name
        op = shutil.move if move else shutil.copy2
        op(str(r["image"]), str(dst_img))
        if r["label"].exists():
            op(str(r["label"]), str(dst_lbl))
    write_data_yaml(output_root, class_names)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, type=Path, help="Roboflow export 루트 (data.yaml 포함)")
    parser.add_argument("--output", type=Path, help="재분배 결과 루트. 미지정시 <input>_split")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/frames/v3_selected/manifest.csv"),
        help="v3_selected/manifest.csv 경로",
    )
    parser.add_argument("--dry-run", action="store_true", help="파일 이동/복사 없이 계획과 검증만 출력")
    parser.add_argument("--move", action="store_true", help="복사 대신 이동")
    args = parser.parse_args()

    if not args.input.is_dir():
        sys.exit(f"입력 경로 없음: {args.input}")
    if not args.manifest.is_file():
        sys.exit(f"매니페스트 없음: {args.manifest}")

    output_root = args.output or args.input.with_name(args.input.name + "_split")
    if not args.dry_run and output_root.exists() and any(output_root.iterdir()):
        sys.exit(f"출력 경로가 비어 있지 않음: {output_root}. 지우고 다시 실행하라.")

    manifest = load_manifest(args.manifest)
    class_names = read_class_names(args.input)
    print(f"입력: {args.input}")
    print(f"출력: {output_root}{'  (dry-run)' if args.dry_run else ''}")
    print(f"매니페스트 항목: {len(manifest)}")
    print(f"data.yaml classes: {class_names or '(없음)'}")

    assigned, unresolved = plan(args.input, manifest)
    print(f"\n배정 성공: {len(assigned)}장")
    print(f"배정 불가: {len(unresolved)}장")

    if unresolved:
        print("\n[배정 불가 상세]")
        for r in unresolved[:20]:
            print(f"  {r.get('image').name}: {r['reason']}")
        if len(unresolved) > 20:
            print(f"  ... 외 {len(unresolved) - 20}건")

    emit_summary(assigned, class_names)

    leaks = check_leakage(assigned)
    if leaks:
        print("\n[누수 감지] 같은 base 가 여러 split 에 배정됨:")
        for base, splits in list(leaks.items())[:20]:
            print(f"  {base}: {sorted(splits)}")
        sys.exit(f"누수 {len(leaks)}건. 매니페스트 중복 또는 경계값을 확인하라.")
    else:
        print("\n[누수 없음] 같은 base 가 여러 split 에 나뉜 사례 없음.")

    if args.dry_run:
        print("\ndry-run 종료. 실제 배포하려면 --dry-run 을 빼고 다시 실행하라.")
        return

    execute(assigned, output_root, class_names, args.move)
    print(f"\n완료. {'이동' if args.move else '복사'} → {output_root}")


if __name__ == "__main__":
    main()
