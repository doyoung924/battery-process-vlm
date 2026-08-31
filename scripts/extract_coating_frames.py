"""v1_source 영상의 코팅 챕터에서 프레임을 추출한다.

leak_diagnosis.md 근거 5·6에서 재라벨링 방침을 정한 뒤 확인한 결과,
`data/frames/v1_unlabeled/slot_die/` 는 4장뿐이라 coating_die 클래스를 학습시킬 수 없다.
원본 영상 챕터 정보(PLAN.md 2.Phase2)에 따르면 코팅 구간은 0:34에서 시작한다.
캘린더링과 슬리팅이 같은 챕터에 묶여 있으므로 초반 몇 분만 사용한다.

의존: opencv-python-headless. `.venv/bin/python scripts/extract_coating_frames.py`.
"""

from pathlib import Path

import cv2

VIDEO = Path("data/raw_videos/v1_source_h264.mp4")
OUT_DIR = Path("data/frames/v1_unlabeled/coating_extra")
START_SEC = 34        # 0:34 챕터 시작
END_SEC = 270         # 4:30 — 캘린더링 전환 전으로 추정. 시각 확인 후 조정
INTERVAL_SEC = 2.5
EXPECTED_SIZE = (1920, 1080)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(VIDEO))
    if not cap.isOpened():
        raise SystemExit(f"열 수 없음: {VIDEO}")

    saved = 0
    skipped_size = 0
    t = START_SEC
    idx = 0
    while t < END_SEC:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        h, w = frame.shape[:2]
        if (w, h) != EXPECTED_SIZE:
            skipped_size += 1
        else:
            idx += 1
            out = OUT_DIR / f"coat_a_{idx:04d}.jpg"
            cv2.imwrite(str(out), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
            saved += 1
        t += INTERVAL_SEC

    cap.release()
    print(f"saved {saved} frames → {OUT_DIR}")
    print(f"range {START_SEC}s ~ {END_SEC}s, interval {INTERVAL_SEC}s")
    if skipped_size:
        print(f"skipped {skipped_size} frames (해상도 불일치)")


if __name__ == "__main__":
    main()
