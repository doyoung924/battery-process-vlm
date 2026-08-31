# 라벨링 계획 — 어느 영상 어느 구간을 어떻게 라벨링할 것인가

작성일 2026-08-19 · 관련 문서 [`leak_diagnosis.md`](leak_diagnosis.md) · [`relabel_progress.md`](relabel_progress.md) · [`../PLAN.md`](../PLAN.md)

> **2026-09-01 개정 요약** — 스크러빙 결과로 test/val 재배정. 아래 원문의 "test = zbBxJLGaoys, val = j1jWp9WxGLM" 은 무효. **현재 확정: test = j1jW (Zeekr, 승격), val = v17_Stjc (VW, 승격), v3_zbBx = 배제** (Subscribe 워터마크 + 4클래스 클로즈업 부족). v10_5AOD 도 배제 (후단 공정만 다룸). 자세한 근거·전체 자료 카탈로그·현행 방침은 `relabel_progress.md` "Phase B 확장" 섹션과 `configs/frame_sources.yaml` 참조.

---

## 목적

`leak_diagnosis.md` 결론 우선순위 2·3(단일 영상 출처 / val 세트 과소)을 해결하려면 영상을 추가하고 **영상 단위로 train/val/test 를 분리**해야 한다. 이 문서는 다음을 확정한다.

1. 어느 영상의 어느 구간을 라벨링에 쓸지
2. 각 프레임에서 4클래스 중 어느 것을 어떻게 라벨링할지 (라벨 기준)
3. train/val/test 를 어느 영상으로 분리할지, test 영상·구간은 무엇인지

---

## 확보 영상 목록

사용자가 확정한 롱폼 4개 + 참고용 Shorts 7개.

### 롱폼 영상 (라벨링 주 소스)

| ID | 채널 | 길이 | 화질 | 챕터 | 촬영지·특징 |
|---|---|---:|---:|---:|---|
| **v1_source** (이미 확보) | Miracle Process | 36:05 | 1080p | 3 | 중국 팩토리 전체 라인. 세로 3구간 (코팅+캘린더+슬리팅 / 와인딩+캡슐 / 조립+테스트) |
| **j1jWp9WxGLM** | Everything Electric CARS | 10:50 | 1920p | **14** | Z Factory (지리자동차 Zeekr) 취재 다큐. 서구 시청자용, 서술형 챕터 |
| **zbBxJLGaoys** | Processlytic | 16:32 | **2160p (4K)** | 0 | 챕터 없음, 4K. Hidden Process — 편집물이라 챕터 부재해도 공정 클로즈업 위주로 추정 |
| **hmhHPvDErhM** | CATL 공식 | 4:17 | 1080p | 4 | 코팅 공정 클로즈업 (Coding=Coating 오타로 추정) |
| **UHZg5-uk1-k** | Lithium Battery Company | 2:19 | 1080p | **12** | 매우 짧지만 챕터 매칭 완벽 (MIXING/COATING/CUTTING/ASSEMBLY/…) |

### Shorts (보조 데이터)

| ID | 클래스 후보 | 길이 | 화질 | 채널 |
|---|---|---:|---:|---|
| OwqnjMAXs6c | coating_die | 56s | 1920p | infinityPV — slot-die 코팅 클로즈업 (연구실 스케일) |
| SNiTgaNbWcc | coating_die | 70s | 1920p | infinityPV — slot-die 설명 |
| Urld0ddZn-w | roll_press | 52s | 1920p | Motoma — 캘린더링 |
| by7GjvtrfyI | slitting_knife | 37s | 1124p | Athena — 구리박 슬리팅 |
| 70fq0Pw8RJo | slitting_knife | 39s | 1920p | Xiaowei — 세퍼레이터 슬리팅 |
| rhTC2rNwkuk | winding_core | 60s | 1280p | TOB — 60138 슈퍼커패시터 와인딩 |
| EcikXB0Lq38 | winding_core+ | 67s | 1920p | lipowergroup — 3종 셀 (실린더/각형/파우치) |

**Shorts 사용 방침:**
- **세로 포맷(9:16) 가능성 큼 → 도메인 시프트 위험.** 다운로드 후 종횡비 확인 필수
- 세로면 학습보다 **테스트 강건성 확인용**으로만 사용 (모델이 세로 프레임에서도 설비를 잡는지)
- 가로면 train 에 소량 추가 (클래스당 3~10 프레임)
- infinityPV·Motoma 는 **연구실/소형 장비**라 팩토리 시각과 다를 수 있음. 라벨링 시 skip 판정 가능

---

## 롱폼 영상별 라벨링 구간 계획

각 영상의 챕터 정보를 근거로 라벨링에 쓸 구간을 아래 확정한다. 다운로드·시각 확인 후 조정.

### v1_source_h264.mp4 (36:05, 이미 확보)

이미 `data/frames/v1_unlabeled/` 에 프레임 분류돼 있고 [`relabel_progress.md`](relabel_progress.md) 에서 345장 선별 완료. **재선별 대상**.

| 구간 | 챕터 | 라벨링 대상 |
|---|---|---|
| 0:34~12:50 | 코팅+캘린더+슬리팅 | coating_die (부족, 재추출 필요), roll_press, slitting_knife |
| 12:50~30:25 | 와인딩+캡슐화 | winding_core |
| 30:25~36:05 | 조립+테스트 | 대상 클래스 밖 → skip |

### j1jWp9WxGLM (10:50, Zeekr Z Factory)

챕터 14개 중 실제 공정 관련:

| 시각 | 챕터 | 라벨링 판정 |
|---|---|---|
| 2:22–3:03 | Cathode room | coating_die 후보 (다운로드 후 확인) |
| 3:03–3:37 | Half a width of a human hair | electrode 필름 클로즈업, 특정 클래스 매칭 어려움 → 확인 후 |
| 4:03–5:49 | **Rolling 2.2 million cells** | roll_press or winding_core (챕터 제목 모호). **가장 중요한 구간** |
| 6:31–7:21 | The Baking Room | 건조로, 대상 클래스 밖 → skip |
| 나머지 | Cell testing, Battery swapping 등 | skip |

**추정 라벨링 구간: 2:22–5:49 (총 3분 27초 → 약 80 프레임 @ 2.5s)**

### zbBxJLGaoys (16:32, 4K, 챕터 없음)

**챕터가 없어 다운로드 후 시각 스크러빙 필요.** 4K 화질이라 클로즈업이 잡히면 최고 데이터가 된다.

**작업 순서:**
1. 다운로드 후 30초 간격 썸네일 그리드 생성 (`scripts/preview_grid.py` 신설 필요)
2. 사람이 그리드 훑어서 각 공정 구간 시각 지정
3. `configs/frame_sources.yaml` 에 수동 챕터 기록

**용도 결정:** **test 영상으로 지정**. 이유는 아래 [테스트 영상 지정] 섹션 참조.

### hmhHPvDErhM (4:17, CATL 공식)

| 시각 | 챕터 | 라벨링 판정 |
|---|---|---|
| 0:00–0:55 | Intro | skip |
| 0:55–1:37 | LightningFast Production | 전체 라인, 원경 → skip 또는 부분 |
| **1:37–3:31** | **Coding Process (=Coating)** | **coating_die 핵심 소스** |
| 3:31–4:17 | Conclusion | skip |

**라벨링 구간: 1:37–3:31 (1분 54초 → 약 45 프레임)**

### UHZg5-uk1-k (2:19, How It's Made)

챕터가 세밀함:

| 시각 | 챕터 | 라벨링 판정 |
|---|---|---|
| 0:07–0:13 | MIXING | 대상 클래스 밖 → skip |
| **0:13–0:41** | **COATING** (28s) | coating_die |
| **0:41–0:51** | **CUTTING** (10s) | slitting_knife (cutting = slitting? 확인) |
| **0:51–1:09** | **ASSEMBLY** (18s) | winding_core (assembly = cell 조립 = winding?) |
| 1:09~ | DRYING/AGING/… | skip |

**라벨링 구간: 0:13–1:09 (56초 → 약 22 프레임)**

**주의:** How It's Made 스타일은 애니메이션/CG 삽입이 많다. 실사 프레임만 골라야 함.

---

## 라벨링 기준 — 무엇을, 어떻게 박스칠 것인가

`leak_diagnosis.md` 근거 6(라벨이 설비 윤곽 아닌 영역을 가리켰다) 를 반영해 다음 규칙을 확정한다.

### 4클래스 정의 및 시각적 판별 기준

| 클래스 | 시각적 정의 | 박스 범위 | 흔한 오라벨 |
|---|---|---|---|
| **coating_die** | 슬러리(검은 액체)를 필름 위에 분사하는 **얇은 슬롯 노즐 헤드**. 옆에서 봤을 때 얇은 사각 |노즐 헤드만. 슬러리·필름 롤은 제외 | 헤드 주변 파이프까지 포함 (X) |
| **roll_press** | 위아래 **두 개 큰 롤러** 사이로 전극 필름이 지나감. 롤러 표면 광택 | 두 롤러 자체 (필름 유입/출구 부분은 제외) | 라인 전체 (X) |
| **slitting_knife** | 축에 나열된 **회전 원반 칼날** (원반 여러 개가 축에 배열) | 칼날 원반들의 축 전체 (한 박스에 여러 원반) | 잘려나온 필름까지 포함 (X) |
| **winding_core** | 전극·세퍼레이터를 감는 **회전 심축**. 감기는 중이면 원통형 롤 형태 | 심축과 감긴 롤 부분 | 지게차·이송장치 (X) |

### 라벨링 절차

1. 프레임을 열어 대상 설비가 명확히 보이는지 확인
2. **없으면 skip** (라벨 없는 프레임 = negative sample). 무리해서 배경만 담기지 않음
3. 있으면 **설비 자체 윤곽에만** 밀착 박스. 여백·주변 인프라 배제
4. 한 프레임에 같은 클래스 여러 개 있으면 각각 박스 (예: 슬리팅 나이프 여러 축)
5. 다른 클래스가 함께 잡히면 함께 라벨링

### 첫 20장 리뷰 원칙

라벨링 20장 완료 시점에 아래를 확인:

- 클래스별 인스턴스 수가 균형 잡히나 (한 클래스가 0이면 프레임 재선별)
- 박스 크기가 이미지의 5~50% 범위인가 (넘으면 라벨 기준 재검토)
- skip 비율이 30% 이하인가 (넘으면 프레임 선별 잘못)

---

## Train / Val / Test 분할 원칙

`leak_diagnosis.md` 결론 3(val 세트 원본 9~16장 문제)과 PLAN §2 Phase 2("영상 단위 분리")를 따른다.

### 원칙

1. **분할은 프레임이 아니라 영상 단위.** 한 영상의 프레임을 여러 split 에 나눠 넣지 않는다
2. **test = 학습에 전혀 쓰이지 않은 영상.** 카메라·조명·설비·촬영자 모두 다른 것이 이상적
3. **val = train 과 겹치지 않는 영상.** test 만큼 엄격하지 않아도 되지만 train 과 분리
4. Shorts 는 세로 포맷이 대부분이라 train 에 소량만 (검증 목적), val·test 에 넣지 않음
5. **각 클래스가 최소 train·test 양쪽에 5+ 인스턴스** — 성능 측정 가능성 확보

### 분할 안 (다운로드 후 확정)

| Split | 영상 | 예상 프레임 | 예상 인스턴스 |
|---|---|---:|---:|
| **train** | v1_source + hmhHPvDErhM + UHZg5-uk1-k + Shorts (선별) | ~400 | ~1,200 |
| **val** | j1jWp9WxGLM | ~80 | ~200 |
| **test** | zbBxJLGaoys (부분) | ~100 | ~250 |
| **합계** | 5개 영상 (+shorts) | ~580 | ~1,650 |

---

## Test 영상 지정 — zbBxJLGaoys 인 이유

| 기준 | zbBxJLGaoys 판정 |
|---|---|
| 학습에 안 쓰였음 | ✅ 신규 |
| 다른 촬영자 | ✅ Processlytic (v1_source Miracle 과 무관) |
| 다른 팩토리 | ✅ 편집물이라 여러 팩토리 소스일 가능성 → 오히려 도메인 다양성 |
| 화질 | ✅ **4K** (판단 근거로 시각 검증 용이) |
| 4클래스 모두 포함 여부 | ⚠️ 챕터 없어 다운로드 후 확인 필요 |
| 길이 여유 | ✅ 16:32 → 부분만 라벨링해도 100+ 프레임 확보 |

### test 라벨링 절차

1. 다운로드 후 60초 간격 썸네일 그리드 생성
2. 각 클래스가 등장하는 구간을 시각 확인 → 클래스당 30초~1분 구간 지정
3. 해당 구간에서 2.5초 간격 프레임 추출 → 라벨링
4. **결정:** test 프레임 라벨링은 Roboflow 에서 사람이 직접 (자동 pseudo-label 금지 — 성능 측정 기준이므로 정답 순수도 필수)
5. 결과: test 프레임 100장, 클래스당 5~15 인스턴스가 목표

### zbBxJLGaoys 로 test 가 안 되는 경우

만약 다운로드 후 확인 결과 4클래스 중 2개 이상이 잘 안 잡히면 → **train/val/test 재배정**:
- 대안 A: j1jWp9WxGLM 을 test 로, zbBxJLGaoys 를 val 로
- 대안 B: v1_source 를 영상 시간 기준으로 3분할 (test = 후반 30% 구간의 프레임)
- 대안 C: 새 영상 확보 (Phase A 재실행)

---

## 클래스 커버 매트릭스 (다운로드 전 예상)

| 클래스 | v1 | j1jW (val) | zbBx (test) | hmhH | UHZg | Shorts |
|---|---|---|---|---|---|---|
| coating_die | ▲ 부족 | ? | ? | ★★ 핵심 | ★ | ★ (2편) |
| roll_press | ★★ 29장 확보 | ★? (rolling 챕터) | ? | ✗ | ✗ | ★ (1편) |
| slitting_knife | ★★ 76장 확보 | ? | ? | ✗ | ★ (cutting) | ★★ (2편) |
| winding_core | ★★ 145장 확보 | ★? (rolling 챕터) | ? | ✗ | ★ (assembly) | ★★ (2편) |

★★ = 주요 소스, ★ = 보조, ▲ = 부족, ? = 미확인, ✗ = 커버 없음

**리스크 hotspot:**
- **coating_die** — v1_source 에서 부족 확인됨. hmhHPvDErhM + UHZg + 코팅 shorts 로 보완해야 함. 그래도 부족하면 j1jW cathode room 구간 활용
- **test set 클래스 커버** — zbBxJLGaoys 에 4클래스 모두 있어야 완전한 성능 측정. 첫 다운로드 시 필수 확인

---

## 다음 실행 순서

1. **Phase B (다운로드)** — `scripts/download_videos.py` 작성 → 롱폼 4개 + Shorts 7개 다운로드
2. **Phase B-후속** — 각 영상 첫 30초 프레임 추출해 실제 화질·종횡비·내용 확인 (특히 Shorts 세로 포맷 여부)
3. **Phase C (챕터 파싱 + 매핑)** — `scripts/list_chapters.py` + zbBxJLGaoys 수동 스크러빙 → `configs/frame_sources.yaml` 확정
4. **Phase D (프레임 추출)** — 위 config 기반 `scripts/extract_frames.py` 실행 → 영상별 `v{N}_unlabeled/<class>_<series>/` 생성
5. **Phase E (통합 선별)** — `scripts/select_frames.py` CLASS_MAP 확장 재실행 → 통합 zip 4개
6. **Phase F (라벨링)**
   - Roboflow 프로젝트: `battery_v2_multi` 4클래스
   - **파일명 prefix 로 영상 태깅** (예: `v2_j1jW_...`, `v3_zbBx_...`) → 나중에 split 자동 분리
   - 첫 20장 라벨링 후 [라벨링 기준] 섹션 리뷰
7. **Phase G (분할 스크립트)** — `scripts/build_splits.py` 작성. 파일명 prefix 로 train/val/test 자동 분할, `data/dataset/v1_relabel/` 생성. leak_diagnosis 결론 5 대로 **분할 간 교집합 0 assert**

---

## 미결 사항 (다운로드 후 결정)

- [ ] j1jW "Rolling 2.2 million cells" 챕터가 roll_press 인지 winding_core 인지
- [ ] zbBxJLGaoys 에 4클래스 모두 나오는지, 각 구간 시각
- [ ] Shorts 종횡비 (세로면 train 제외)
- [ ] hmhHPvDErhM Coding=Coating 인지, 실제 slot-die 잡히는지
- [ ] UHZg CUTTING 이 slitting 인지 notching 인지 (다른 공정이면 매핑 재검토)
