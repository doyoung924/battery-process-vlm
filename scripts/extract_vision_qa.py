"""finetuning.ipynb 셀 안에 인라인 코드로만 존재하는 SFT 학습 쌍을 JSON으로 회수한다.

노트북 셀에는 vision_qa / additional / additional2 ... 형태로 리스트 리터럴이
하드코딩되어 있고, 실행 결과물인 vision_qa.json 은 RunPod 워크스페이스에만 있었다.
노트북이 유실되면 복구 불가능한 자산이므로 리포지토리로 옮긴다.

리스트 리터럴만 ast 로 파싱한다 (노트북 코드를 실행하지 않는다).
"""

import argparse
import ast
import json
from pathlib import Path

# 회수 대상 변수명 접두사 — vision_qa, additional, additional2, additional3 ...
TARGET_PREFIXES = ("vision_qa", "additional")


def iter_code_cells(notebook: dict):
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        yield source


def extract_lists(source: str) -> list[dict]:
    """셀 소스에서 대상 변수에 할당된 리스트 리터럴을 뽑는다."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if not any(n.startswith(TARGET_PREFIXES) for n in names):
            continue
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            continue
        try:
            value = ast.literal_eval(node.value)
        except ValueError:
            continue
        found.extend(v for v in value if isinstance(v, dict))
    return found


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--notebook", default="legacy/llm/finetuning.ipynb")
    parser.add_argument("--out", default="data/sft/vision_qa.json")
    args = parser.parse_args()

    notebook = json.loads(Path(args.notebook).read_text(encoding="utf-8"))

    pairs: list[dict] = []
    for source in iter_code_cells(notebook):
        pairs.extend(extract_lists(source))

    # instruction + input 조합이 같으면 중복으로 본다 (셀마다 리스트를 재정의하며 누적한 흔적이 있다)
    seen = set()
    unique = []
    for pair in pairs:
        key = (pair.get("instruction", ""), pair.get("input", ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(pair)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(unique, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with_input = sum(1 for p in unique if p.get("input"))
    print(f"추출 {len(pairs)}쌍 → 중복 제거 후 {len(unique)}쌍")
    print(f"  탐지 결과(input) 포함: {with_input}쌍 / 텍스트 전용: {len(unique) - with_input}쌍")
    print(f"  저장: {out_path}")


if __name__ == "__main__":
    main()
