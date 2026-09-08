# Phase 1 재라벨링 — 진행 상황

작성일 2026-08-16, 갱신 2026-08-27 · 관련 문서 [`leak_diagnosis.md`](leak_diagnosis.md) · [`labeling_plan.md`](labeling_plan.md) · [`../PLAN.md`](../PLAN.md)

---

## 현재 상태 (2026-09-08 밤 — 라운드 3: 라벨 정의 재정립)

**단계:** winding_core 실무 CV 관점 재정의 → v16 excluded, 라벨 예시 2개 재작성 (winding_core / coating_die), `labeling_plan.md` 정의 표 갱신. `select_frames --force` + zip 재실행 대기.

### 2026-09-08 밤 — 라운드 3: winding_core 실무 CV 재정의 + 라벨 예시 재작성

**계기:** 사용자 지적 "winding_core = 전극+분리막이 감기는 걸 해야 하는 것 아닌가?"
- 기존 정의 (`labeling_plan.md`): "심축과 감긴 롤 부분" — 실제 winding action 없는 프레임까지 포함
- 실무 산업 CV / QC 관점으론 정의가 좁아야 이상감지·QC 신호로 유효

**4클래스 재정의 (실무 QC 관점):**
| 클래스 | 재정의 | QC 시나리오 |
|---|---|---|
| coating_die | slot die head + slurry 접점 (head → foil tangency) | 슬러리 유량 이상, 코팅 두께 편차, head 오염 |
| roll_press | 압연 롤 쌍 + nip point | 롤 압력 편차, 필름 두께 QC, 롤 마모 |
| slitting_knife | 원반 나이프 어셈블리 (blades array + 축) | 슬리팅 폭, 나이프 마모 |
| winding_core | **winding station** — 심축 + tangency + 이송 필름 | jelly roll 결함, 필름 얼라인먼트, 감기 속도 |

**소스 재판정 (winding_core 기준):**
| 소스 | 판정 | 근거 |
|---|---|---|
| v8_RQM4 (val) | ✅ 유지 | `v8_winding_check_grid.jpg` — 심축+필름 감기 tangency 명확 (pouch 라 표시됐으나 실제는 심축 winding) |
| v9_9ang (train) | ✅ 유지 | `v9_winding_check_grid.jpg` — 반자동 심축 winding, tangency 관찰됨 |
| **v16_11rQ** | ❌ **excluded** | `v16_winding_check_grid.jpg` — 라인 원경/셀 이송/판넬 위주, tangency 부재. post-winding assembly 성격 |
| v1_we (신규 대구간) | Roboflow 판정 | 사용자가 winding station 프레임만 kept |

**라벨 예시 재작성:**
- `experiments/labeling_examples/winding_core.jpg` — v8_wi_RQM4_008.jpg 기반. GOOD 박스 = 검은 원반(심축) + 좌측 은색 필름 이송 tangency. BAD = 전체 프레임
- `experiments/labeling_examples/coating_die.jpg` — s2_coat_SNiT_022.jpg 기반. GOOD 박스 = slot die head + 슬러리 튜브 + head → foil 접선 (분홍색 coated foil 상단부). BAD = 감긴 coated roll + 자막
- 생성 도구: `scripts/render_label_example.py` (신설, PIL, CJK 폰트 지원)

**부작용:** winding_core val 이 v8 단독 (14장) 이 됨. 통계적 최소 (5+/클래스) 는 충족.

---

## 이전 상태 (2026-09-08 밤 — 잡동사니 소각 3소스 완료)

**단계:** 3개 잡동사니 소스(v1_coat_a, v4_hmhH, v1_frame_a) 소각 완료. `v2_selected_all.zip` 재빌드(49M, 470장). Roboflow 미라벨 정리 대기.

### 2026-09-08 밤 — 잡동사니 소각 3소스 실행 (chapter 좁힘 라운드 1)

**계기:** 소스별 매칭율 진단(직전 섹션) 결과 반영. 사용자 결정 "전체 소각".

**재스크러빙 결과:**

| 소스 | 스크러빙 | 판정 |
|---|---|---|
| v1_coat_a (`coating_extra/coat_a_*`) | `preview_grid --start 34 --end 270 --interval 5` (48셀) | slurry tank / 필름 이송 / 원경 / 게이지 위주, gold 후보 ~10셀도 실은 calendering 성격 (roll_press). 이미 `calendering/` 폴더로 커버 → **전체 소각** |
| v4_coat_hmhH (chapter 97~211s) | `preview_grid --start 97 --end 211 --interval 3` (38셀) | 자막·presenter·CG·원경 위주. gold 3~4셀뿐 (#03~#04 1:46~1:49, #10 2:07, #21 2:40). CATL 홍보 특성 → **chapter 완전 skip + split=excluded** |
| v1_frame_a (`slitter_knife/frame_a*` 72장) | `preview_files` (신규 스크립트, 파일 그리드) | 작업자 손 + 필름 이송 위주, gold ~9셀. `frame_b` 42장(21장 kept) 로 slitting 커버 → **전체 소각** |

**적용 (파일 이동 + 코드/config 갱신):**

1. `data/frames/v1_unlabeled/coating_extra/` → `_excluded_coating_extra/` (95장 rename)
2. `data/frames/v1_unlabeled/slitter_knife/frame_a*.jpg` → `_excluded_frame_a/` (72장)
3. `data/frames/v1_unlabeled/numbered_core/frame_a*.jpg` → `_excluded_frame_a/` (87장, stride cap 으로 3장만 kept 였음)
4. `scripts/select_frames.py` `V1_CLASS_MAP` 에서 `coating_extra` 키 삭제
5. `configs/frame_sources.yaml`:
   - v4 `split: train → excluded`, chapter `skip: true` + `excluded_reason` 갱신
   - v1 `reference_chapters` 하단에 소각 이력 주석
6. `scripts/preview_files.py` 신설 (pre-extracted 파일 시리즈 그리드용, preview_grid 와 상보)

**재선별 결과 (2026-09-08 밤):**

| split | coating_die | roll_press | slitting_knife | winding_core | total |
|---|---:|---:|---:|---:|---:|
| train | 122 (−141) | 43 | 80 (−44) | 170 (+3) | **415 (−182, 소각 30.5%)** |
| val | 0 | 0 | 0 | 21 | **21** |
| test | 16 | 10 | 8 | 0 | **34** |
| **all** | **138** | **53** | **88** | **191** | **470** |

- coating_die 감축 상세: v1_coat_a 95 + v4_coat_hmhH 46 = 141장 소각
- slitting_knife 감축: v1_frame_a (slitter_knife 폴더 kept 44장) 소각
- winding_core 소폭 증가: numbered_core frame_a 소각으로 stride cap 재계산, 다른 시리즈에서 여유 확보
- **정책 warning** (assert 아님, class_exceptions 로 완화됨): coating_die pilot 89.3% (factory 자원이 v5 UHZg 11장 + v1 slot_die 2장 = 13장뿐). v4 배제 직접 여파. 재도입 필요 시 매우 좁은 서브 chapter 로만.

**산출물:**
- `data/frames/v2_zip_stage/v2_selected_all.zip` (49M, 470장) — 76M 643장에서 감축
- 기존 3-split zip 및 `v2_selected_new_20260908.zip` 은 정리(삭제)됨

**Roboflow 정리 가이드 (사용자 액션):**
- 소각된 소스는 **미라벨 프레임만** 삭제. 이미 라벨된 것은 유지 (재분류 판정이 gold 인 경우 있음, 예: coat_a → roll_press 5장)
- 파일명 prefix 필터로 batch 삭제:
  - `v1_coat_a_*` (미라벨 84장)
  - `v4_coat_hmhH_*` (미라벨 43장)
  - `v1_frame_a*` (미라벨 45장)
- 다음 export 시 라벨된 16장은 정상 회수, 로컬 소재 없어도 annotation 유지

**다음 액션 후보:**
- (a) 매칭율 미지 소스 진행 리뷰 (v1_wi_b/c/e/f/g/h/i, v5_*, v18_*)
- (b) v12_sl_UQ91 (17.2%) 재스크러빙 검토 — 초반 매칭율이라 확정 이름
- (c) 라벨링 진행 (신규 zip 업로드 → 400+장 라벨링)

### 2026-09-08 밤 — 소스별 실 매칭율 진단 (chapter 좁힘 준비)

**계기:** 사용자가 "기존 영상에서 좋은 이미지들이 많은데 select_frames 가 뽑은 게 클래스 관계없는 이미지 훨씬 많다" 지적. Roboflow 미라벨 프레임 대다수 skip 감이라고 관찰.

**진단 실행:** v2_selected/train 업로드 프레임 수 vs Roboflow export 라벨된 프레임 수 소스별 비교. 라벨된 = 실 매칭 확실 (empty label 0).

**결과 (소스별 실 매칭율):**

⚠️ **잡동사니 소스 (매칭율 20% 미만):**

| 소스 | 업로드 | 라벨 | 매칭율 | 낭비 프레임 |
|---|---:|---:|---:|---:|
| v1_frame_a | 47 | 2 | **4.3%** | ~45 |
| v4_coat_hmhH | 46 | 3 | **6.5%** | ~43 |
| v1_frame_c | 15 | 1 | **6.7%** | ~14 |
| v1_coat_a | 95 | 11 | **11.6%** | ~84 |
| v12_sl_UQ91 | 29 | 5 | **17.2%** (초반) | ~24 |
| **소계** | **232** | **22** | | **~210장 낭비** (v2_selected/train 597의 35%) |

✅ **Gold 소스 (매칭율 70%+ 검증됨):**
- v1_wi_d 100% (12/12), v1_ca_c 70.6% (12/17), v1_ca_b 66.7%
- s3_rp_Urld 100%, s14_rp_jbgH 100%, s1_coat_Owqn 54.5%

△ **진행 중 (판정 이름):** v20_coat_WQiE 46%, s19_coat_VG2C 44%, s2_coat_SNiT 36%, v1_ca_a 33%

🕐 **미시작 (매칭율 미지):** v1_wi_b/c/e/f/g/h/i (106장), v1_sl_a/b (10장), v1_frame_b/d/e (30장), v5_coat/sl/wi (22장), v9/s20 신규 (32장), v18_sl_Es6A (9장)

**원인 특정:**
- v1_source `coating_extra` 폴더 (95장) — 이름-실물 불일치. 실제로 mixing/이송/원경 다수, 실 slot die 극소수
- v1_source `frame_a/b/c/d/e` 시리즈 — 정체불명 잡동사니 폴더 (extract_coating_frames.py 로 뽑은 원 소스 확인 필요)
- v4 CATL — chapter 97~211초 통짜, 실 slot die 극소수 (presenter/원경/자막 다수)
- v12 slitting — chapter 0~73초 통짜, 초반 라벨링이라 확정 이르나 낮음

**다음 액션 (재개 시점 명령):**

1. **잡동사니 소각 진행** (권장) — v1_coat_a + v4_hmhH + v1_frame_a 3개 재스크러빙 → chapter/V1_CLASS_MAP 좁힘 → select_frames --force. 예상 삭감 ~170장
2. 또는 철저 소각 — 매칭율 낮은/미지 소스 모두 재스크러빙 (30~60분)
3. 또는 무손실 subset — 라벨된 112장 유지 + 미라벨 소스만 chapter 재검토 (스크립트 확장)

**재시작 명령 예시:**
- "잡동사니 소각 이어서 하자"
- "v1_coat_a, v4_hmhH, v1_frame_a 재스크러빙 시작"
- "매칭율 낮은 3개 소스 chapter 좁힘"

### 2026-09-08 밤 — 신규 6소스 편입 + 파이프라인 재빌드

### 2026-09-08 밤 — 신규 6소스 편입 + 파이프라인 재빌드

**계기:** 2026-09-08 저녁 D 방향 신규 다운로드 완료 (8개 후보). 스크러빙·챕터 판정 후 6개 편입 확정.

**신규 다운로드 8개 판정 (사양 및 스크러빙 결과):**

| 소스 | 사양 | 판정 | 편입 결과 |
|---|---|---|---|
| **s1_Owqn** (OCP TOB 재) | 55.7s 480x854 | ✅ Gold #11~#25 head 다각도 | chapter `{22,50,coating_die}` |
| **s2_SNiT** (OCP 재) | 69.7s 480x854 | ✅ Gold+ #02~#27 head 매우 풍부 | chapter `{5,68,coating_die}` |
| **s19_VG2C** (infinityPV) | 41s 480x854 | ✅ Gold 전 구간 head 다각도 | chapter `{0,40,coating_die}` |
| **s20_TLPi** (infinityPV) | 45.4s 480x854 | ✅ Gold+ head 조립 튜토리얼 | chapter `{0,44,coating_die}` |
| **v9_9ang** (TOB, 배제→편입) | 52s 640x360 | ✅ #03~#19 심축 반자동 winding | chapter `{4,40,winding_core}` |
| **v20_WQiE** (infinityPV 롱폼) | 104s 1080p | ✅ 좋음 head 산발적 | chapter `{3,100,coating_die}` |
| v19_3gUI (CATL 다큐) | 190s 1080p | ⏳ 보류 촘촘 재스크러빙 필요 | 배제 |
| v21_Id4k (Dürr 홍보) | 160s 1080p | ❌ 전 구간 CG/애니메이션 | 배제 |
| v22_Yq41 (한국어 견학) | 950s 1080p | ⏳ 보류 구간별 스크러빙 필요 | 배제 (한국 팩토리 첫 소스, 다음 라운드 최우선) |

**정책 완화:**
- `policy.scale_cap.class_exceptions.coating_die: null` 신규 (roll_press 예외 이어서 두 번째)
- shorts 4개 편입으로 pilot 상한 급상승 예상 → 예외 명시

**파이프라인 재빌드 결과 (2026-09-08 밤):**

| split | coating_die | roll_press | slitting_knife | winding_core | total |
|---|---:|---:|---:|---:|---:|
| train | **263** (154+109) | 43 | 124 | **167** (153+14) | **597** |
| val | 0 | 0 | 0 | 21 | **21** |
| test | 16 | 10 | 8 | 0 | **34** |

- 전체 652장 프레임 → 유니크 643장 (파일명 충돌 hash suffix rename)
- coating_die 순증 +109 (168 → 277 프레임, +65%): v20(39) + s2(25) + s20(18) + s19(16) + s1(11)
- winding_core 순증 +14: v9(14)

**산출물:**
- `data/frames/v2_zip_stage/v2_selected_all.zip` (76M, 643장) — 전체 스냅샷 갱신
- `data/frames/v2_zip_stage/v2_selected_new_20260908.zip` (7.9M, 123장) — **신규 배치 업로드용**
- 기존 3-split zip · v2_selected_all(구) 은 rollback 대비 유지

**112장 시점 라벨 품질 재검증 (신규 소스 대표 11장 렌더링):** 우수
- 신규 소스 모두 원칙 준수, 재라벨링 불필요
- 재분류 판정 정확: v20 → rp 2건, s19 → rp 2건, s1 → rp 1건 (사용자 도메인 지식 반영)
- 세로 shorts letterbox 좌우 검정 완벽 무시
- 자막·로고·판넬·다이얼 게이지 배제 우수

**신규 소스 진행 상황 (112장 시점):**
- v20 WQiE: 20/39 (51%) — coating_die 18 + rp 재분류 2
- s2 SNiT: 9/25 (36%) — coating_die 9
- s19 VG2C: 7/16 (44%) — coating_die 5 + rp 재분류 2
- s1 Owqn: 6/11 (55%) — coating_die 5 + rp 재분류 1
- s20 TLPi: 0/18 미시작
- v9 wi_9ang: 0/14 미시작

**클래스별 인스턴스 (112장 시점):**
- roll_press 61 (임계 50+ 달성) ✅
- coating_die 46 (임계 근접)
- winding_core 13 (v1 winding + v9 진행 필요)
- slitting_knife 10 (v12/v17/v18 나머지 진행 필요)

### 2026-09-08 저녁 — 72장 시점 리뷰 + 소재 부족 대안 진단

**Roboflow export (`battery_v2_multi.yolov8`) 실측:**

| 클래스 | 인스턴스 | 프레임 | 프레임당 |
|---|---:|---:|---:|
| roll_press | 56 | 47 | 1.19 |
| winding_core | 13 | 13 | 1.00 |
| slitting_knife | 10 | 10 | 1.00 |
| coating_die | 9 | 9 | 1.00 |
| **합계** | **88** | 72 | - |

**소스별:** v1(45) + s3(11 완주) + v17(5) + v12(5) + v4(3) + s14(3 완주). empty label 0장.

**소스 × 클래스 매트릭스 — 통합 라벨링 방침 효과 검증:**
- v1_coat_a 대량 재분류: `coating_die → roll_press` 5장 (파일명은 coat, 실물은 calendering)
- v1_frame_a/c 시리즈: rp/sl/wi 로 분산 재분류
- **v1_source 는 사실 coating_die 소스가 아니라 roll_press 소스** (아래 v1 재스크러빙 결과 참조)

**바운딩 박스 품질 검증 (개별 렌더링 6장):** 매우 우수
- 원칙 "설비 자체의 윤곽에 밀착" 준수 확인
- 배경·자막·완제품 배제 잘 됨
- 다중 인스턴스 (s3_rp_Urld_008 3 boxes, s14_rp_jbgH_001 2 boxes) 개별 박스 처리 우수
- 이름-실물 재분류 판정 정확
- **재라벨링 필요 없음**. `data/scrubbing/label_samples/` 에 검증 이미지 13장 보관 (gitignored)

**소재 부족 대안 A/B/C 스크러빙 결과 (사용자 지시: 촘촘히 프레임 단위 판정):**

| 대안 | 소스 | 판정 | 순증 |
|---|---|---|---:|
| A-1 | s11_aGPs (Xiaowei coating 20s) | ❌ 원경/판넬/필름 이송, slot die head 없음 | 0 |
| A-2 | s12_Q791 (Xiaowei coating 19s) | ❌ 원경/판넬/필름, slot die head 없음 | 0 |
| A-3 | s15_jXyP (Xiaowei winding 23s) | ❌ 완제품 셀 이송, 심축 없음 | 0 |
| A-4 | s16_PJAA (LG엔솔 winding 50s) | ❌ 하단 절반 광고 배너 + 원경 | 0 |
| B-1 | v9_9ang (TOB winding, 360p 52s) | ✅ **편입** — 심축 클로즈업 명확 (#03~#19) | winding_core +14 |
| B-2 | v11_SOBJ (MIN LI coating, 480p 16s) | ❌ 매칭 애매 + rp 는 이미 충분 | 0 |
| C | v1_source 34~274s 재스크러빙 | ❌ slot die head 부재 확정, calendering 위주 | 0 |

**핵심 교훈:**
- **셀 홍보 shorts (Xiaowei/LG엔솔) = 완제품·원경 위주** → 실 공정 클로즈업 부족. Motoma(s3) 처럼 "공정 설명" 목적 shorts 만 유효
- **v1_source = calendering 위주 영상** — coating 챕터도 실 slot die 는 실사 4장(slot_die 폴더) 뿐. 나머지는 슬러리 탱크·롤·이송·모니터 UI
- **coating_die 는 기존 자원 완전 고갈** → 신규 다운로드 없이는 60~90 인스턴스가 최종

**결정:** v9 편입 진행 (winding_core +14) + D 신규 다운로드 (사용자 진행)

**v9 편입은 config 갱신 대기** — 신규 다운로드분과 함께 한 번에 파이프라인 재실행 예정

### 2026-09-08 저녁 — coating_die 신규 다운로드 후보 (D 방향)

WebSearch 결과. 사용자가 직접 다운로드 예정.

**🔴 최우선: 기존 카탈로그 재다운로드 (이전 삭제됨)**

| 예정 파일 | URL | 사양 | 비고 |
|---|---|---|---|
| s1_Owqn | https://www.youtube.com/shorts/OwqnjMAXs6c | 55.7s 480x854 | TOB "Electrode Coating — Slot-die" |
| s2_SNiT | https://www.youtube.com/shorts/SNiTgaNbWcc | 69.7s 480x854 | "What is Slot-die Coating?" |

s1+s2 재확보만으로 예상 +49장 (2.5s interval).

**🟡 Gold 후보: infinityPV slot-die head shorts (연구실 스케일)**

| URL | 콘텐츠 |
|---|---|
| https://www.youtube.com/shorts/VG2Cult1d74 | "Slot-die Heads Explained in 42 seconds" — head 다각도 클로즈업 |
| https://www.youtube.com/shorts/TLPir94Do0c | "How to Assemble a Slot-die Head" — 어셈블리 부품 |

리스크: infinityPV = 연구실 slot-die 제조사, test 4K와 스케일 갭.

**🟢 롱폼 (팩토리 스케일)**

| URL | 채널 |
|---|---|
| https://www.youtube.com/watch?v=-3gUI3QeqHg | CATL "Inside CATL's Battery Coating Lab: Why Precision Matters" |
| https://www.youtube.com/watch?v=WQiEStr4GRM | "Slot-die Coating for Battery Electrodes Explained" |
| https://www.youtube.com/watch?v=Id4kUbf8Hm8 | "Lithium-ion battery electrode manufacturing for gigafactories" (2022) |
| https://www.youtube.com/watch?v=Yq41X98CwIg | 한국어 "이차전지 리튬이온 배터리 어떻게 만드나? 공장 견학" |

**다음 액션 (다운로드 후):**
1. `data/raw_videos/` 배치
2. `preview_grid.py` 스크러빙 → 클로즈업 구간 판정
3. `configs/frame_sources.yaml` chapters 갱신 (+ v9 편입 병합)
4. `extract_frames.py` → `select_frames.py --force`
5. `v2_selected_all.zip` 재빌드
6. Roboflow 신규 배치 업로드 (기존 프로젝트에 추가, Auto Split OFF 유지)

### 2026-09-08 roll_press 보강 — shorts s3/s14 편입

**계기:** 사용자가 클래스 카운트 재확인 시 roll_press 39장(train 29 단독 v1) 심각 부족 지적. 1차 실패 "단일 영상 출처" 우선순위 3 회귀 리스크.

**스크러빙 결과 (기존 다운로드 자원 재검토):**

| 소스 | 판정 | 순증 프레임 |
|---|---|---:|
| v6_zCRF (HAONENG 1:32) | #00 만 roll_press. 이후 slitting 위주 | ~3~5장 |
| v5_UHZg | #06 "DRYING THE ELECTRODE" 롤러 — 도메인 오분류 리스크 | 0~3장 |
| v4_hmhH (CATL) | presenter + 라인 원경 위주 | 0장 |
| v10_5AOD (Xiaowei) | 전 구간 assembly. 배제 재확인 | 0장 |
| s3_Urld (Motoma "Calendering") ⭐ | #03~#17 (0:06~0:34) 롤러 클로즈업 gold | **11장** |
| s13_Yjlc (Xiaowei) | 세로 기기 원경 위주 → 라벨 기준 위배 | 0장 (배제) |
| s14_jbgH (Xiaowei) | #04~#07 롤러 축 클로즈업 marginal | 3장 |

**결정:** shorts s3, s14 만 `sources` 로 편입 (train). 방침 완화 근거는 아래.
- s3 chapter: `{start: 6, end: 34, class: roll_press, series: rp_Urld}` — Motoma calendering 명시적 주제
- s14 chapter: `{start: 3, end: 10, class: roll_press, series: rp_jbgH}` — 라벨링 시 원경 프레임 skip 예상
- v6, v13, v10 등은 배제 유지 (v6 는 slitting 자원 충분해 편입 이득 없음)

**정책 완화:**
- `policy.scale_cap.class_exceptions: {roll_press: null}` — roll_press 만 pilot 30% 상한 예외
- `shorts.policy: holdout_only_by_default` — 기본 홀드아웃, s3/s14 예외 편입
- select_frames.py warning 은 그대로 (초과 사실 기록), assert 안 함

**세로 shorts 편입 리스크 (감수):**
- 원본 480x854 세로 → 학습 시 letterbox pad (정보 손실)
- Xiaowei (s14) 편중 상한 위배 소지 (roll_press 43장 중 xiaowei 3장 = 6.9% → 20% 상한 내)
- Motoma / Xiaowei 파일럿 스케일 → factory test 정합성 저하 가능성. 인정하고 진행

**신규 선별 결과 (2026-09-08):**

| split | coating_die | roll_press | slitting_knife | winding_core | total |
|---|---:|---:|---:|---:|---:|
| train | 154 | **43** (29+14) | 124 | 153 | **474** |
| val | 0 | 0 | 0 | 21 | **21** |
| test | 16 | 10 | 8 | 0 | **34** |

**roll_press train 소스:** v1(29 factory) + s3(11 other_pilot Motoma) + s14(3 xiaowei) — 소스 3개로 단일 소스 문제 완화. 여전히 다른 클래스 대비 적으나 순증 48% (29→43).

**통합 zip 재빌드:** `v2_selected_all.zip` (68M, 520장). 파일명 충돌 6장 hash suffix rename.

### 2026-09-08 방침 전환 — 통합 라벨링 + 사후 영상 단위 분할

**계기:** 사용자가 v2_selected {train,val,test} 실물 재확인 시 이름-실물 불일치 다수 지적 (예: 슬러리탱크가 `coating_die` 폴더). 원인은 v1_source `coating_extra` 챕터(0:34~4:30) 통짜 샘플링 — mixing·이송·슬러리 프레임이 coating_die 로 태깅됨. `manifest.csv` 상 v1 coating_die 152장 중 상당수가 이 구간에서 옴.

**결정:** Roboflow 배치를 하나로 통합, 라벨링 시 skip 자유롭게, 분할은 라벨링 완료 후 파일명 `source_id` prefix 로 사후 처리.

- **Roboflow 업로드:** `data/frames/v2_zip_stage/v2_selected_all.zip` (67M, 506장) 단일 배치. Auto Split **반드시 OFF**
- **라벨 기준 일관성 확보:** 원래 `labeling_plan.md` 목표. split 별 배치는 이 목표에 부작용 (배치 간 판정 드리프트)
- **사후 분할 원칙:** 영상 단위 유지 (leak_diagnosis.md 우선순위 3 준수). 프레임 랜덤 분할 금지 (1차 mAP 0.995 데이터 누수 재현 리스크)
- **사후 분할 스크립트:** `scripts/split_by_source.py` (미작성, 라벨링 완료 후 작성). 파일명 first-token (`v1_`, `v2_`, `v8_`, `v16_`, `v17_`) 로 영상 매핑, YOLO/COCO annotation 을 train/val/test 로 재분배
- **val 재배정 재검토:** 라벨링 후 살아남은 인스턴스 수 기준. 어제(2026-09-07) v8 train→val / v16 chapter 30~48s 좁힘은 유지 (winding_core 클로즈업 확보는 여전히 유효)

**통합 zip 구성 (2026-09-08 갱신):**
- 3개 split 을 클래스 폴더로 flatten (split 계층 제거, 클래스 계층 유지)
- 파일명 충돌 6장은 content hash suffix 로 rename (v1_frame_a0001/a0039/b0001 이 slitting_knife·winding_core 양쪽 존재)
- 총 520장 (전체 유니크): coating_die 168 / roll_press **53** / slitting_knife 126 / winding_core 173
- roll_press 는 shorts s3/s14 편입 후 확대 (아래 2026-09-08 roll_press 보강 섹션 참조)

**기존 3개 split zip 유지:** `v2_selected_{train,val,test}.zip` — rollback 대비 (통합 방침 실패 시 복원용)

### 2026-09-07 val 재구성 (A+C 결정)

**계기:** 사용자가 val 폴더(v16_11rQ 23장) 실물 확인 시 "라벨링 할 만한 게 없다" 지적. `preview_grid.py --interval 2` 로 v16 30셀 재스크러빙한 결과 대부분이 라인 원경·DELL 제어판·완제품 실린더 이송이고 winding_core 클로즈업은 30~48s 구간(~7장)뿐 확인.

**원인:** 2026-09-02 test/val 재배정 때 v16 스크러빙을 생략하고 `chapters: [{start: 0, end: 58, class: winding_core}]` 통짜로 잡은 것. caveat 에 "실린더 winding 이 가장 명확 매칭" 라고 낙관 추정만 적혀 있었음.

**대응:** 옵션 A(v8 train→val 이동) + 옵션 C(v16 chapter 30~48s 좁힘) 조합
- v8_RQM4 split: `train` → `val`. 14장 (Gelon pouch 반자동 winding, 1080p)
- v16_11rQ chapters: `0~58s` → `30~48s`. 7장 (심축 회전 구간). caveat 갱신
- train winding_core: 167 → 153 (v8 이동)

**신규 선별 결과 (2026-09-07):**

| split | coating_die | roll_press | slitting_knife | winding_core | total |
|---|---:|---:|---:|---:|---:|
| train | 154 | 29 | 124 | 153 | **460** |
| val | 0 | 0 | 0 | 21 (v8×14+v16×7) | **21** |
| test | 16 | 10 | 8 | 0 | **34** |

**train pilot 비율:** slitting **30.6%** ⚠️ 여전 (v8·v16 이동은 winding 만 영향). 라벨링 20장 리뷰 시 재검토 대상.

**zip 재빌드:** `data/frames/v2_zip_stage/v2_selected_{train,val,test}.zip` (67M / 3.4M / 5.6M).

### 이전 상태 (2026-09-01 시점 기록, 참고)

Phase B 확장 다운로드 완료. 총 롱폼 18개(v1~v18) + Shorts 11개(s3, s6, s8~s16).

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
- **v2 rp_j1jW/hair_j1jW 스크러빙 (2026-09-02)** — `preview_grid.py --start/--end/--tag` 옵션 추가 후 chapter-scoped 그리드 생성. 판정: **두 chapter 모두 4클래스 매칭 없음** (완제품 로고 + jumbo electrode roll + 셀 assembly 위주). `skip: true` 처리
- **test/val 재구성 (2026-09-02)** — v2 winding_core 커버 부재 확인 → **test = v2(coat) + v17(rp+sl)** 통합, **val = v16(wi)** 승격. **test winding_core 는 없음 accepted** (train 학습은 v1+v8+v16=182장으로 충분)
- **`scripts/select_frames.py` 확장 완료 (2026-09-02)** — config 기반 다중 영상 통합, split 인식, pilot/xiaowei 상한 assert. 산출: `data/frames/v2_selected/{split}/{class}/{source_id}_{stem}.{ext}` (531 프레임 = train 474 + val 23 + test 34). 매니페스트 1201행

**2026-09-02 선별 (구):** train 474 / val 23(v16만) / test 34 → 2026-09-07 재구성으로 대체 (위 참조)

**다음:**
1. Roboflow 프로젝트 `battery_v2_multi` 개설 (4클래스) → `data/frames/v2_zip_stage/v2_selected_all.zip` 단일 배치 업로드 (**Auto Split OFF 필수**)
2. 라벨링 20장 시점 리뷰 (박스 크기 5~50%, skip 비율, 이름-실물 매칭 실측)
3. 전량 라벨링 완료 후 `scripts/split_by_source.py` 작성 → 파일명 source_id 기반 영상 단위 train/val/test 재분배

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
