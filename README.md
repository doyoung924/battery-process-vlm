# battery-process-vlm

이차전지 제조 영상에서 프레임을 직접 추출·라벨링해 만드는 **공정 구간 검출용 데이터셋 재구축 프로젝트**. 1차 시도(9클래스, 합성 이미지 포함)의 mAP50 0.995 실사 실패를 원인 진단하고, 클래스·분할·소스·라벨 기준을 전면 재설계한 라운드 4가 현재 상태다. **라운드 4 라벨링이 진행 중이며 4클래스 학습은 아직 시작하지 않았다.**

## 1. 문제

1차 시도 총 19회 학습(`experiments/history.csv`)에서 mAP50 0.995가 8회 반복 기록됐다.

| 실행 | 데이터셋 | mAP50 | mAP50-95 |
|---|---|---:|---:|
| battery_v4-2 | v16i (Colab) | 0.995 | 0.946 |
| coating_v2 / v3 / v4 / v5-2 | coating 계열 | 0.995 | 0.638–0.671 |
| slitting_v1 / v2 / v3-2 | v1i~v3i | 0.995 | 0.593–0.613 |

미학습 실사 영상에 적용하면 성능이 무너졌다. 지표와 실체의 괴리 원인을 특정하기 위해 진단을 수행했다.

## 2. 진단

첫 가설은 train/val 프레임 누수였으나, base 파일명 대조 결과 **누수 0건**으로 반증됐다. Roboflow 분할 자체는 깨끗했고 문제는 분할되는 데이터의 성질에 있었다. 원인은 우선순위 순으로 다음 네 가지다.

1. **라벨 기준이 설비 윤곽이 아닌 "설비가 있는 영역"을 가리킴** — 박스 30%가 검은 여백을 20% 이상 포함. 모델이 화면 대부분을 덮는 큰 박스 하나를 예측하는 장면 분류 수준으로 학습됨.
2. **실사 프레임 단일 출처** — 전부 `battery_source.mp4` 하나. 어떻게 분할해도 카메라·조명·설비가 동일해 미학습 영상 성능을 원리적으로 측정 불가.
3. **val 세트 원본 9~16장** — 클래스당 3~5장으로 이미지 1장 차이가 mAP 0.99↔0.90을 뒤집는다. `v15_raw`(runpod_v12 학습)는 val 0장이라 학습셋 자체가 val로 채점됨.
4. **학습 데이터의 36~72%가 Gemini 생성 합성 이미지** — 실사보다 조명·구도가 균일해 "더 쉬운 문제"가 됨.

`experiments/leak_diagnosis.md` §근거 5의 "경계 이탈 35%"는 §근거 6의 클리핑 실험에서 자체 반증됐다. 클리핑 후에도 박스 면적이 원본의 84%로 유지돼 좌표 버그가 아닌 라벨 기준 문제로 확정됐다. 상세는 [`experiments/leak_diagnosis.md`](experiments/leak_diagnosis.md) 참조.

## 3. 재설계

| 진단 항목 | 처방 |
|---|---|
| 라벨 기준 | 1920×1080 원본에서 재라벨링, 기존 640×640 레터박스 데이터셋 폐기 |
| 단일 소스 | 실사 영상 1편 → 4편(v1/v4/v10/v17)로 확장 |
| val 과소 | 영상 단위 분할 도입 |
| 합성 이미지 | 학습에서 전면 배제 |
| 클래스 부적합 | 9클래스 → 4클래스 축소 |

**철회한 계획:** `imgsz=1280` · SAHI 타일링은 재라벨링 데이터 분석에서 박스 면적 중앙값이 이미지의 24%로 확인돼 소형 객체 문제 자체가 없음이 드러났으므로 폐기했다.

## 4. 현재 데이터

### 영상 소스 (`configs/frame_sources.yaml`)

| id | 채널 | 길이 | 해상도 | 판정 |
|---|---|---:|---|---|
| v1 | Miracle Process | 36:06 | 1920×1080 | 사용 |
| v4 | CATL | 4:17 | 1920×1080 | 사용 |
| v10 | Xiaowei New Energy | 5:26 | 1920×1080 | 사용 |
| v17 | AutoMotoTV — VW Salzgitter | 1:00 | 1920×1080 | 사용 |
| v5 | How It's Made | 2:19 | 1920×1080 | 제외 — 감긴 electrode_roll 정면 클로즈업 부재 |
| v15 | Wei-Hang Automation | 0:06 | 1920×1080 | 제외 — 슬리팅 원반·판넬만 등장 |

`extract_frames_v3.py` 로 1s 간격 샘플링 + pHash Hamming dedup 적용.

### 프레임 수 (`data/frames/v3_selected/manifest.csv`, 671장)

| 클래스 | 프레임 수 |
|---|---:|
| electrode_roll | 212 |
| prismatic_cell_tray | 206 |
| pouch_cell_tray | 195 |
| mixing_tank | 58 |

라벨링 완료 장수는 Roboflow 프로젝트 안 상태이므로 저장소에서 확인 불가.

### train/val/test 배정 (`docs/labeling_spec_v1.md`)

| 클래스 | train | val | test |
|---|---|---|---|
| electrode_roll | v1_er_a/b/c (79장) | v4_er_a (10장) | v17_er_a (16장) |
| pouch_cell_tray | v1 26:00–28:30 | v1 28:30–29:15 | v1 29:15–30:00 |
| prismatic_cell_tray | v10 0:00–3:30 | v10 3:30–4:30 | v10 4:30–5:25 |
| mixing_tank | 보류 | 보류 | 보류 |

electrode_roll 만 공장 3곳(Miracle Process / CATL / VW)의 영상 단위 분할이 성립한다.

## 5. 클래스 정의

`docs/labeling_spec_v1.md` (동결). 각 클래스는 단일 물체로 정의하고 판별 질문에 예/아니오로 답할 수 있어야 한다.

| 클래스 | 판별 질문 |
|---|---|
| electrode_roll | 원통에 감긴 전극이 보이는가 (검은 코팅면 + 구리/알루미늄 스트라이프) |
| prismatic_cell_tray | 같은 모양 각형 셀이 2개 이상 나란한가 |
| pouch_cell_tray | 트레이 위에 파우치가 2개 이상 있는가 |
| mixing_tank | 원통형 탱크 몸체가 보이는가 |

**선정 기준 3가지:**

1. 바운딩박스로 표현 가능한가 (면·필름 형태 제외)
2. 형태만으로 다른 클래스와 구분되는가
3. 공정 구간을 특정하는 데 기여하는가

**라운드 4에서 탈락한 후보** (`docs/labeling_spec_v1.md` §제외 결정 기록):

| 후보 | 탈락 사유 |
|---|---|
| roll_press | v1 36분에 압연 공정 장면 부재. 타 소스에서 압연 롤과 이송 롤의 시각적 구분 불가 |
| slitting_knife | v1/v12/v13 전수 확인 결과 원형 날 식별 프레임 총 8장. 최소 다양성 미달 |
| thickness_gauge | 실체가 분석용 전자저울로 확인. 면적 분포 20배 편차로 내용물 혼입 발견. 80박스 폐기 |
| coating_die | v1 근거 구간 얇음. v20(infinityPV)은 실험실 장비로 외형 상이해 동일 클래스 불가. 51박스 폐기 |

이전 라운드의 4클래스 라벨 181박스는 부정확한 챕터 정의 위에서 작업된 것으로 전량 폐기했다.

## 6. 알려진 한계

- **단일 소스 3클래스** — `pouch_cell_tray` / `prismatic_cell_tray` / `mixing_tank` 는 각각 단일 영상(v1, v10, v1)에서만 나온다. 시간 구간으로 분할했으나 카메라·조명·설비가 동일하므로 미학습 영상에서의 일반화는 측정 불가. 시간대가 다르면 대상 개체·각도가 달라지지만 프레임 누수와는 구분된다.
- **mixing_tank 보류** — 58장으로 부족해 이번 라운드에서 split 배정을 보류했다. 실질적으로 3클래스 학습으로 시작.
- **라운드 4 학습 미착수** — YOLO 학습 스크립트가 저장소에 없다. `runpod/` 폴더는 비어 있다.
- **VLM 파이프라인 미착수** — 시계열 집계·Claude 리포트·소형 VLM 증류·Streamlit 데모 전부 미착수. 프로젝트 이름의 "vlm" 부분은 계획 단계에 머물러 있다.
- **라벨링 완료 장수 미확인** — Roboflow 프로젝트 상태이며 저장소 파일로 검증 불가.
- **1차 학습(19회, `experiments/history.csv`)의 mAP50 0.99대 지표는 참고 불가** — val이 학습셋이거나(v15_raw), val 원본 9~16장이거나, 학습 데이터의 36~72%가 합성 이미지였다.
- **낡은 문서와의 클래스·규모 표기 불일치** — `PLAN.md` 와 `experiments/status_20260911.md` 는 라운드 3 이하 클래스(coating_die / roll_press / slitting_knife / winding_core)를 표기한다. 정본은 §8 문서 안내 참조.

## 7. 재현 방법

1. `scripts/download_videos.py` (WSL 인증 문제 시 `scripts/download_on_windows.ps1`) 로 v1/v4/v10/v17 을 `data/raw_videos/` 에 확보
2. `scripts/extract_frames_v3.py` 실행 → `configs/frame_sources.yaml` 순회, `data/frames/v3_selected/<class>/` 와 `manifest.csv` 생성 (1s 간격, pHash Hamming dedup)
3. `data/frames/v3_selected/` 를 Roboflow 프로젝트에 업로드해 4클래스로 라벨링 (외부 도구)
4. Roboflow 에서 YOLO 형식 export 다운로드
5. `scripts/split_dataset.py` 로 Roboflow export 를 `manifest.csv` 의 series/timecode 기준으로 train/val/test 재분배. mixing_tank 는 `_holdout/` 로 격리

**YOLO 학습 스크립트는 저장소에 없다.** `runpod/` 폴더는 비어 있으며, 라운드 4 학습은 시작되지 않았다.

## 8. 문서 안내

**정본 (라운드 4 기준, 이 README는 이 다섯 개만 근거로 삼는다):**

- `docs/labeling_spec_v1.md` — 클래스 정의·박스 규칙·스킵 기준·분할 배정 (동결)
- `configs/frame_sources.yaml` — 사용/배제 소스와 챕터 구간
- `experiments/leak_diagnosis.md` — 1차 실패 진단
- `experiments/history.csv` — 1차 19회 실험 기록
- `data/frames/v3_selected/manifest.csv` — 현재 프레임 목록

**낡은 문서 (참고용, 클래스명·규모 재사용 금지):**

- `PLAN.md` — 7단계 로드맵 원안. 클래스 후보(coating_die / roll_press / slitting_knife / winding_core / web_roll)는 라운드 3 이전.
- `experiments/status_20260911.md` — 라운드 3 시점 브리핑. 4클래스 표기가 현행과 다르다.
- `PROJECT_SUMMARY.md` — 자소서용 서사. "600~800장" 은 원안 목표치이며 실측이 아니다.
- `experiments/labeling_plan.md`, `experiments/relabel_progress.md` — 라운드 2/3 이력 아카이브.
- `docs/labeling_spec_v2_notes.md` — v1 동결 후 개선안 임시 보관.
