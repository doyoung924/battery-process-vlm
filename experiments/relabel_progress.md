# Phase 1 재라벨링 — 진행 상황

작성일 2026-08-16, 갱신 2026-08-27 · 관련 문서 [`leak_diagnosis.md`](leak_diagnosis.md) · [`labeling_plan.md`](labeling_plan.md) · [`../PLAN.md`](../PLAN.md)

---

## 현재 상태 (2026-09-01)

**단계:** Phase B 확장 **다운로드 완료**. 총 롱폼 18개(v1~v18) + Shorts 11개(s3, s6, s8~s16) 확보. `configs/frame_sources.yaml` 확장 및 챕터 매핑 착수 대기.

**주요 발견:**
- **Xiaowei New Energy 채널 편중** — 신규 대부분이 Xiaowei (v7, v10, s8, s9, s11~s15). 기존 s5 포함 총 9개. 도메인 다양성 축 좁아짐 (Xiaowei = 중국 파일럿/연구실 스케일)
- **v10_5AOD ⭐** — 5분 26초 Xiaowei 각형 셀 롱폼. 이번 최대 자산
- **v7_EUOo** — Xiaowei "가로 1080p 30초" (shorts 아님) → train 가능
- **URL 미결 해결 (2026-09-01)** — v18 = `E-s6AZaNUaw` (OCELL CCD Slitting), s10 = `ElCZ2XQkk18` (RUIAN LOYAL slitting shorts). 전 자료 원본 URL 확정
- **Xiaowei 편중 방침 확정 (2026-09-01)** — "선별적 파일럿 편입 + 팩토리 스케일 우선". 클래스당 pilot 30% 상한. 아래 [방침 결정 이력] 참조
- **`configs/frame_sources.yaml` 확장 (2026-09-01)** — 롱폼 18 + shorts 11 정의. `policy` 섹션 명시
- **스크러빙 도구 신설 + 3영상 실행 (2026-09-01)** — `scripts/preview_grid.py`. v17/v10/v3 그리드 → 아래 [스크러빙 결과] 참조
- **train/val/test 재배정 (2026-09-01)** — 스크러빙 결과 v3, v10 배제 → **test = v2_j1jW 승격, val = v17_Stjc 승격, v3 = excluded**. Xiaowei train 편입은 사실상 0
- **Phase D 착수 (2026-09-02)** — `scripts/extract_frames.py` 신설, config `chapters` 순회 프레임 추출 완료. 신규 177 프레임 (v1_unlabeled 1104 별도)

**다음:**
1. v2 `rp_j1jW` chapter TBD 결정 — test 로 승격됐으니 우선. 스크러빙 or 라벨링 시 시각 확인
2. `scripts/select_frames.py` 확장 — 여러 영상 통합 + pilot 30% 상한 assert
3. Roboflow 프로젝트 `battery_v2_multi` 개설 + 통합 zip 업로드 + 라벨링 시작

**이전 Phase B 결과 (2026-08-27):** 롱폼 5개(v1~v5) + Shorts 7개 확보. 이후 Shorts 정리로 s3, s6 만 남음.

---

## Phase B 확장 — 다운로드 완료 (2026-09-01)

사용자가 초기 9개 후보 프로브 후 자체 확장해 총 신규 13 롱폼 + 9 shorts 다운로드. 프로브 스크립트: `/tmp/probe_candidates.py`, `/tmp/probe_new.py`. 파일 실측 스크립트: `/tmp/probe_files.sh`.

### 전체 자료 카탈로그 (2026-09-01 시점)

**롱폼 (18개):**

| 파일 | 원본 ID | 채널 | 실측 길이 | 실측 해상도 | 클래스 후보 | 판정 |
|---|---|---|---:|---|---|---|
| v1_source | (Miracle Process) | 중국 팩토리 | 36:06 | 1920x1080 @ 50 | 3구간 (coat+cal+slit / wind / assy) | 기존 train 주력 |
| v2_j1jW | j1jWp9WxGLM | Everything Electric | 10:50 | 1920x960 @ 25 | Zeekr, rolling 챕터 | 기존 val |
| v3_zbBx | zbBxJLGaoys | Processlytic | 16:32 | **3840x2160 @ 60** | 4K test, 챕터 없음 | 기존 test |
| v4_hmhH | hmhHPvDErhM | CATL 공식 | 4:17 | 1920x1080 @ 25 | coating_die (핵심) | 기존 train |
| v5_UHZg | UHZg5-uk1-k | Lithium Battery Co | 2:19 | 1920x1080 @ 30 | coat+cut+assy 챕터 | 기존 train |
| v6_zCRF | zCRFZrBMt_Y | HAONENG | 1:32 | **626x360** | calendaring+slitting 통합 라인 | ⚠️ **360p 원본** |
| v7_EUOo | EUOo2rqtUqY | **Xiaowei** | 0:30 | **1920x1080 @ 60** | winding_core (phone battery) | ✅ **가로 → train 가능** |
| v8_RQM4 | RQM43Xah3bg | Gelon | 0:35 | 1920x1080 | winding_core (pouch, 반자동) | ✅ 도메인 다양성 |
| v9_9ang | 9angWnJ0k4Q | TOB NEW ENERGY | 0:52 | **640x360** | winding_core (pouch+cylindrical 반자동) | ⚠️ **360p 원본** |
| v10_5AOD | 5AODl1KRP3U | **Xiaowei** | **5:26** | 1920x1080 | **각형 셀 전체 자동 라인 (4클래스 커버 가능성)** | ⭐ **최대 자산** |
| v11_SOBJ | SOBJXa3sUvA | MIN LI | 0:16 | 854x480 | coating | ⚠️ 480p |
| v12_UQ91 | UQ91MAQN7Kk | AME | 1:13 | 1920x1080 | slitting_knife | ✅ 보조 |
| v13_5Ev5 | 5Ev5yUGGF1k | AVEnergy | 0:27 | 1920x1080 | slitting_knife | △ slitting 중복 |
| v14_h4xp | h4x-pFgMKR8 | Gloflux | 0:05 | 1920x1080 | slitting_knife | ❌ 5초, 실사용 어려움 |
| v15_zbHP | zbHPiLUpue8 | Gloflux | 0:06 | 1920x1080 | slitting_knife | ❌ 6초, v14 동채널 |
| v16_11rQ | 11rQ12-VGuw | PPCELL | 0:58 | 1280x720 | winding_core (실린더) | ✅ 필수 |
| v17_Stjc | Stjcse7Bcqk | AutoMotoTV (VW) | 1:00 | 1920x1080 @ 25 | slitting + calendering | ⭐ 필수 (VW Salzgitter, 유럽) |
| v18_Es6A | E-s6AZaNUaw | Michael Haiqing Zhong | 0:23 | 1280x720 @ 25 | **slitting_knife** (OCELL CCD Display Electrode Slitting Machine) | ✅ 확정 |

**Shorts (11개) — 전량 세로:**

| 파일 | 원본 ID | 채널 | 길이 | 클래스 | 방침 |
|---|---|---|---:|---|---|
| s3_Urld | Urld0ddZn-w | Motoma | 0:52 | roll_press | 홀드아웃 (기존) |
| s6_rhTC | rhTC2rNwkuk | TOB | 1:00 | winding_core | 홀드아웃 (기존) |
| s8_W5EY | W5EY-tmwXvE | **Xiaowei** | 0:25 | slitting_knife | 홀드아웃 |
| s9_r0Yj | r0Yjpkrs9kY | **Xiaowei** | 0:20 | slitting_knife | 홀드아웃 |
| s10_ElCZ | ElCZ2XQkk18 | RUIAN LOYAL MACHINERY | 0:14 | slitting_knife (제조사 홍보) | 홀드아웃 |
| s11_aGPs | aGPsYNlPUDQ | **Xiaowei** | 0:20 | **coating_die** | 홀드아웃 |
| s12_Q791 | Q791fmLizKw | **Xiaowei** | 0:19 | **coating_die** | 홀드아웃 |
| s13_Yjlc | Yjl_c3fb5I0 | **Xiaowei** | 0:31 | roll_press | 홀드아웃 |
| s14_jbgH | jbgHp1sblFY | **Xiaowei** | 0:15 | roll_press | 홀드아웃 |
| s15_jXyP | jXyPImQEsGo | **Xiaowei** | 0:24 | winding_core | 홀드아웃 |
| s16_PJAA | PJAAGzOhcdM | LG에너지솔루션 | 0:50 | winding_core (실린더) | 홀드아웃 (한국 팩토리 → 데모 가치) |

### 신규 자료 판정 종합

**⭐ 자산 우위 3개:**
- v10_5AOD — Xiaowei 각형 셀 5:26 롱폼. 시각 스크러빙 후 4클래스 커버 가능성. v3(test) 다음으로 긴 신규
- v17_Stjc — VW Salzgitter 유럽 팩토리, slitting+calendering. 도메인 다양성 축 확장
- v7_EUOo — Xiaowei 채널의 "가로 1080p" 롱폼(shorts URL 아님). train 후보

**신규 도메인 축:**
- **유럽 팩토리** — v17 (VW Salzgitter)
- **한국 팩토리** — s16 (LG엔솔)
- **각형 셀 (prismatic)** — v10, v13(slitting 대상 추정)
- **파일럿/연구실 스케일** — Xiaowei 계열 다수

### Xiaowei 편중 리스크 (신규 이슈)

신규 자료 대부분(v7 + v10 + s8 + s9 + s11~s15) + 기존 s5 = **총 9개가 Xiaowei New Energy**. Xiaowei = 중국 이차전지 장비 제조사, **연구실/파일럿 라인 스케일**(팩토리 아님). Xiaowei 프레임에 편중된 train set 은 팩토리 스케일 일반화 실패 위험. 

**대응 필요:** train/val/test 배분 시 채널 축을 명시적으로 고려. Xiaowei 프레임 train 비율 상한(예: 클래스당 30% 이하) 검토.

### 클래스 커버 재평가

- **coating_die** — v11(짧고 480p) + s11/s12(Xiaowei 세로 홀드아웃). **여전히 train용 부족.** hmhH + UHZg + v1 재스크러빙 전략 유효
- **roll_press** — v6(360p 통합 라인) + v10(예상) + v17(VW) + s13/s14(홀드아웃). v1(29장) 유지. 다양성 크게 확대
- **slitting_knife** — v6 + v12 + v13 + v17 + v18 + s8/s9/s10 추가. 이미 76장+, **중복 위험 관리 필요** (pHash Hamming dedup 강화)
- **winding_core** — v7 + v8 + v9 + v10(예상) + v16 + s15/s16 추가. 도메인 다양성 크게 확대 (Xiaowei phone/prismatic + Gelon pouch + TOB pouch/cyl + PPCELL cyl + LG cyl)

### URL 재확인 결과 (2026-09-01)

- ✅ **v18_Es6A = `E-s6AZaNUaw`** (마지막 소문자 w, 이전 프로브는 대문자 W로 오타). 채널: Michael Haiqing Zhong, 제목: "OCELL CCD Display Electrode Slitting Machine". 파일 첫 프레임에서 관찰된 "초음속(超音速) Vision Inspection UI" 는 이 영상의 CCD 디스플레이 시스템과 일치
- ✅ **s10_ElCZ = `ElCZ2XQkk18`**. 채널: RUIAN LOYAL MACHINERY, 제목: "Lithium battery pole pieces slitting machine". 중국 장비 제조사 홍보 shorts

### 방침 결정 이력 (2026-09-01)

**결정:** "선별적 파일럿 편입 + 팩토리 스케일 우선"

**근거:** test 도메인 정합이 객체 탐지 성능에 가장 크게 기여. 파일럿(연구실/파일럿 라인) 프레임은 클로즈업·단순 배경 편중이라 팩토리 test 에서 recall 저하 위험.

**구현:**
- 클래스당 pilot 프레임 30% 상한, Xiaowei 채널 프레임 20% 상한
- `configs/frame_sources.yaml` `policy` 섹션에 명시
- `scripts/select_frames.py` 에서 클래스별 카운트 후 assert (구현 예정)

**Train 구성 결과 (스크러빙 후, 2026-09-01 최종):**
- factory 3: v1_source, v4_hmhH, v5_UHZg
- pilot 4 (선별): v8_RQM4 (Gelon pouch), v12_UQ91 (AME slitting), v16_11rQ (PPCELL 실린더), v18_Es6A (OCELL CCD)
- **Xiaowei train 편입 0** (v7 편중 위험으로 배제 + v10 스크러빙 후 배제)
- excluded 9: v3, v6, v7, v9, v10, v11, v13, v14, v15

### 스크러빙 결과 (2026-09-01) — `data/scrubbing/`

`scripts/preview_grid.py` 로 v17/v10/v3 그리드 생성 후 시각 확인.

**v17_Stjc (VW, 60s @ 5s = 12셀) — ✅ 사용 확정**
- #00-#02 (0:00-0:10): 인트로/원경 → skip
- #03-#07 (0:15-0:35): calendering 원반 롤러 두 개 클로즈업 → **roll_press**
- #08-#11 (0:40-0:55): 슬리팅 축 + 잘린 필름 → **slitting_knife**
- `configs/frame_sources.yaml` v17 chapters 채워짐
- **val 로 승격** (원래 train → val, j1jW 재배정으로)

**v10_5AOD (Xiaowei 각형, 5:26 @ 10s = 33셀) — ❌ 배제**
- 전 구간 assembly/robot arm/트레이/케이싱/완제품 정렬
- "Prismatic Cell Production" 은 후단 공정(셀 조립) 만 다룸, 앞단(전극) 없음
- 4클래스 매칭 불가 → excluded
- 부가 효과: Xiaowei train 편입 0 자동 해소

**v3_zbBx (Processlytic 4K, 16:32 @ 30s = 34셀) — ❌ 배제 + test 재배정**
- 문제 1: Subscribe 워터마크 전 프레임 상시 (일부 상단 큰 배너)
- 문제 2: 편집 트랜지션 지대 (~8:30~11:30) 흰 프레임 다수
- 문제 3: **4클래스 클로즈업 심각히 부족** — coating/slitting 전무, roll/winding 불명확
- 대부분 라인 원경 + mixing + 자동화 창고 + assembly + packaging
- test 원칙(클래스당 5+ 인스턴스) 위배 → **excluded**

### train/val/test 재배정 (2026-09-01)

v3 배제로 test 공백 → 재배정:

| Split | 이전 | 이후 | 근거 |
|---|---|---|---|
| test | v3_zbBx | **v2_j1jW (Zeekr, 10:50)** | val → test 승격. 4클래스 커버 확인됨(coating_die 챕터 있음), 팩토리 다큐 |
| val | v2_j1jW | **v17_Stjc (VW, 60s)** | train → val 승격. 60s 짧지만 val 로는 감수. 유럽 팩토리 → 도메인 다양성 |
| train | v17 포함 | v17 제외 | v17 val 이동으로 팩토리 train = v1, v4, v5 (3개) |
| excluded | (기존 배제) | v3, v10 추가 | 스크러빙 결과 반영 |

**리스크:** val 이 60s 로 짧아 하이퍼파라미터 튜닝 시 val 지표 노이즈 큼. 라벨링 후 클래스별 인스턴스 5개 이상 확보 되는지 확인 필요.

### 미결 사항 (재개 시점 체크리스트)

- [ ] `scripts/extract_frames.py` 신설 — config `chapters` 순회하며 ffmpeg 로 프레임 추출
- [ ] `scripts/select_frames.py` 확장 — 다중 영상 통합 + policy.scale_cap 상한 assert
- [ ] v2 [243, 349] 'Rolling' 챕터 시각 확인 (test 승격으로 우선순위 상승)
- [ ] 라벨링 20장 시점에 클래스별 pilot 비율 실측 → 상한(30%) 조정 여부 결정
- [ ] val (v17) 프레임 확보량 검증 — 12장으로 클래스별 5+ 인스턴스 나오는지

---

## 요약

1차 시도 실패 원인은 3층: (1) 라벨 기준 문제, (2) 단일 영상 출처, (3) 합성 이미지 의존. `leak_diagnosis.md` 참조.

**계획 진화:**
- 초기(2026-08-16): v1_source 단일 영상에서 345장 선별 → Roboflow 업로드 준비 완료
- 재검토(2026-08-19): 단일 영상 문제 미해결 자각. 통합 배치 전략으로 전환 → 롱폼 3개 + Shorts 여러 개 추가 확보 계획
- 다운로드 시도(2026-08-19~21): 성공 5, 실패 6. YouTube 인증 문제

---

## 완료된 작업

### 1. 진단 (완료, 2026-08-15)
- `experiments/leak_diagnosis.md` — 근거 1~6, 재라벨링이 최상위 우선순위임을 수치로 특정
- 진단 스크립트: `scripts/analyze_dataset.py`, `check_boxes.py`, `check_letterbox.py`, `clip_boxes.py`, `visualize_labels.py`, `check_leakage.py`, `collect_runs.py`

### 2. 프레임 선별 파이프라인 (완료, 2026-08-16)
| 스크립트 | 역할 |
|---|---|
| `scripts/extract_coating_frames.py` | v1_source_h264.mp4 의 `0:34~4:30` 구간을 2.5초 간격 샘플링 → coating_extra/ 95장 |
| `scripts/select_frames.py` | 폴더별 Gemini 제외 + 해상도 필터 + series pHash Hamming dedup + stride 캡 → class 폴더 복사 + manifest.csv |

`.venv/` 에 `Pillow`, `ImageHash`, `opencv-python-headless`, `yt-dlp`, `bgutil-ytdlp-pot-provider` 설치됨.

### 3. v1_source 단일 영상 기반 선별 (완료, 2026-08-16 — 나중에 재선별 예정)

| 목표 클래스 | 프레임 | 소스 |
|---|---:|---|
| coating_die | 95 | slot_die 실사 2 + coating_extra 93 |
| roll_press | 29 | calendering 전량 |
| slitting_knife | 76 | slitter_knife (pHash 8) + slitting 실사 |
| winding_core | 145 | winding 118 + numbered_core (pHash 5 + stride cap 30) 27 |
| **합계** | **345** | |

산출물: `data/frames/v1_selected/{class}/`, `manifest.csv`, class zip 4개.

**주의:** 통합 배치 전략 확정 후 이 결과는 **재선별 예정**. 현재는 유지 (Phase E 에서 CLASS_MAP 확장하여 재실행할 때 재생성됨).

### 4. 라벨링 계획 확정 (완료, 2026-08-19)
- `experiments/labeling_plan.md` — 어느 영상 어느 구간을 어떻게 라벨링할지, 4클래스 시각적 정의, train/val/test 영상 분리 원칙, test 영상 지정 근거
- 확정 사항:
  - train = v1_source + hmhH + UHZg + shorts
  - val = j1jWp9WxGLM (Zeekr Z Factory)
  - test = zbBxJLGaoys (4K 16분)

### 5. 신규 영상 후보 조사 (완료, 2026-08-19)
- 롱폼 후보 11개 프로브 → 4개 선택 (j1jW, zbBx, hmhH, UHZg)
- Shorts 후보 7개 프로브 → 4클래스 커버 확인

### 6. 다운로드 스크립트 (완료, 2026-08-19)
- `scripts/download_videos.py` — WSL 용 yt-dlp 래퍼
- `scripts/download_on_windows.ps1` — Windows PowerShell 용 (cookies-from-browser 사용)

### 7. 전량 다운로드 완료 (2026-08-27)

이전 부분 다운로드는 초기화 후 cobalt.tools 로 재확보.

**롱폼 5개** (`data/raw_videos/`):

| 파일 | 크기 | 해상도 | 길이 | 비고 |
|---|---:|---|---:|---|
| v1_source_h264.mp4 | 443M | 1920x1080 @ 50 | 36:06 | Miracle Process (train) |
| v2_j1jW.mp4 | 122M | 1920x960 @ 25 | 10:50 | Zeekr (val) — 종횡비 2:1 |
| v3_zbBx.mp4 | 1.7G | **3840x2160 @ 60** | 16:32 | Processlytic 4K (test) |
| v4_hmhH.mp4 | 73M | 1920x1080 @ 25 | 4:17 | CATL (train) |
| v5_UHZg.mp4 | 33M | 1920x1080 @ 30 | 2:19 | How It's Made (train) |

**Shorts 7개** (`data/raw_videos/shorts/`) — **전량 세로 480p 확인**:

| 파일 | 크기 | 해상도 | 길이 | 클래스 |
|---|---:|---|---:|---|
| s1_Owqn.mp4 | 3.6M | 480x854 | 55.7s | coating_die |
| s2_SNiT.mp4 | 5.0M | 480x854 | 69.7s | coating_die |
| s3_Urld.mp4 | 3.9M | 480x854 | 52.3s | roll_press |
| s4_by7G.mp4 | 2.9M | 480x756 | 36.8s | slitting_knife |
| s5_70fq.mp4 | 5.3M | 480x854 | 39.1s | slitting_knife |
| s6_rhTC.mp4 | 5.7M | 480x854 | 60.0s | winding_core |
| s7_Ecik.mp4 | 5.1M | 480x854 | 67.4s | winding_core+ |

**Shorts 방침 확정 (2026-08-27):** 전량 세로 480p → **train 제외**. `labeling_plan.md` 리스크 예측 그대로. 필요 시 강건성 평가용으로만 별도 홀드아웃.

---

## 재개 지점 — 다음에 여기서 시작

### ✅ Phase C — 챕터 매핑 config 완료 (2026-08-27)

산출물: `configs/frame_sources.yaml`
- 롱폼 5개 + Shorts 7개 소스 정의
- 각 챕터에 class·series·note (미결 사항은 `class: TBD` 로 명시)
- `open_questions` 섹션에 다운로드 후 확인해야 할 5개 항목 (labeling_plan 미결 사항과 동기화)
- v1_source 는 `status: pre-extracted` (기존 v1_unlabeled 재사용)
- Shorts 는 `policy: holdout_only` (train 제외 방침 반영)

### Step 1. Phase D — 일반화 프레임 추출 스크립트

`scripts/extract_frames.py` (신규) — config 기반, 여러 영상·챕터 iterate → `data/frames/v{N}_unlabeled/<class>_<series>/*.jpg`

기존 `extract_coating_frames.py` 로직을 config-driven 으로 확장. YAML 파싱 → chapter 별 ffmpeg/cv2 로 2.5초 간격 프레임 추출 → 폴더별 저장.

### Step 2. zbBxJLGaoys 시각 스크러빙

4K 16분 챕터 없음. `scripts/preview_grid.py` (신규) 로 60초 간격 썸네일 그리드 생성 → 사용자가 각 클래스 등장 구간 시각 지정 → yaml 업데이트.

### Step 3. Phase E — 통합 선별 재실행

`scripts/select_frames.py` 의 `CLASS_MAP` 을 여러 영상으로 확장 → 재실행 → 통합 zip 4개.

### Step 4. Phase F — Roboflow 업로드 + 라벨링

Roboflow 프로젝트 `battery_v2_multi` 생성 → 통합 zip 업로드 → 라벨링 착수. 파일명 prefix (v1/v2/v3/…) 로 나중에 train/val/test 자동 분할.

---

## 리스크와 유의점 (변경 없음)

| 리스크 | 대응 |
|---|---|
| coating_die 인스턴스 부족 | hmhH + UHZg + coating shorts 로 보완 |
| slitting_knife 프레임 부적합 | 라벨링 시 skip 판정, 부족하면 slitting shorts 로 보완 |
| j1jW "Rolling" 챕터 모호 | 다운로드 후 시각 확인 필수 (roll_press vs winding_core) |
| zbBx 4클래스 커버 미확인 | 스크러빙 후 부족하면 val/test 재배정 |
| Shorts 세로 포맷 가능성 | 다운로드 후 종횡비 확인, 세로면 train 제외 |
| v15_raw 삭제 금지 | README 비교용, `data/dataset/v15_raw/` 보존 |

---

## YouTube 다운로드 지식 (재시도 시 참고)

- **WSL 에서는 안 됨.** Node 18(unsupported), Deno 미설치, quickjs 는 sudo 필요, PoT 서버 미실행
- **Windows 에서도 yt-dlp.exe 단독으론 안 됨.** JS runtime 필요
- **성공 경로:**
  1. `--cookies-from-browser chrome` (Chrome 종료 상태에서, 유튜브 로그인된 프로필)
  2. Deno 설치 (`winget install DenoLand.Deno`)
  3. 낮은 화질(format 22 = 720p mp4 combined) 은 시그니처 없이 되는 경우 있음
- **가장 확실한 우회:** cobalt.tools 웹 다운로더 (JS runtime·auth 필요 없음)

---

## 관련 파일 인덱스

**계획·진단 문서:**
- `experiments/leak_diagnosis.md` — 실패 원인 진단
- `experiments/labeling_plan.md` — 영상별 라벨링 구간 + train/val/test 분리
- `experiments/relabel_progress.md` — 이 문서 (진행 상황)

**스크립트:**
- `scripts/extract_coating_frames.py` — v1_source 코팅 챕터 프레임 추출
- `scripts/select_frames.py` — 필터·dedup·stride 선별
- `scripts/download_videos.py` — WSL yt-dlp (실패)
- `scripts/download_on_windows.ps1` — Windows PowerShell 다운로드
- **미작성:** `scripts/extract_frames.py` (일반화), `scripts/preview_grid.py` (스크러빙용)

**데이터:**
- `data/raw_videos/v1_source_h264.mp4` — Miracle Process (443M)
- `data/raw_videos/v{2..5}_*.mp4` — Zeekr / Processlytic 4K / CATL / How It's Made
- `data/raw_videos/shorts/s{1..7}_*.mp4` — 전량 세로 480p, train 제외 방침
- `data/frames/v1_unlabeled/` — v1_source 프레임 (10개 폴더 1,040장)
- `data/frames/v1_selected/` — v1 단독 선별 결과 (재선별 예정)
- `data/dataset/v15_raw/` — 폐기 예정 라벨 (보존)

**설정:**
- `cookies.txt` — YouTube 인증 (개인정보, `.gitignore` 되어 있음)
- `.venv/` — Python 3.12 가상환경
