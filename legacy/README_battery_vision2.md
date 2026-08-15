# 🔋 Battery Vision AI
### 배터리 제조 공정 실시간 관제 시스템

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-FF6B35?style=flat)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Oracle](https://img.shields.io/badge/Oracle_DB-F80000?style=flat&logo=oracle&logoColor=white)
![Roboflow](https://img.shields.io/badge/Roboflow-7B2FFF?style=flat)
![Status](https://img.shields.io/badge/Status-Phase_1_진행중-yellow?style=flat)

> 컴퓨터 비전(YOLOv8)으로 배터리 제조 공정을 자동 인식하고, 실시간으로 공정 상태를 관제하는 AI 시스템입니다.  
> 재료공학 전공 지식을 활용한 도메인 특화 설계가 핵심 차별점입니다.

---

## 📌 프로젝트 소개

### 배경 및 문제 인식

배터리 제조 현장의 공정 모니터링은 현재 대부분 **작업자 육안 확인** 또는 **단순 센서 기반**에 의존합니다.
스마트팩토리 전환이 가속화되는 환경에서, 영상 기반 AI를 통한 공정 자동 인식 및 실시간 관제 시스템의 필요성이 커지고 있습니다.

### 프로젝트 목표

- 배터리 제조 영상에서 현재 진행 중인 **공정을 자동으로 인식**
- 공정별 상태를 **실시간 관제 화면(대시보드)** 으로 시각화
- **단일 통합 모델** 구조로 VLM + AI 에이전트 파이프라인 확장 대응
- 재료공학 도메인 지식 기반의 **공정 클래스 설계**로 인식 정확도 차별화

### 차별점

| 일반 비전 AI 프로젝트 | Battery Vision AI |
|---|---|
| 범용 객체 감지 | **배터리 공정 특화** 클래스 설계 |
| 단순 분류 모델 | YOLO → VLM → Agent **단계적 파이프라인** |
| 임의 데이터셋 | **재료공학 지식** 기반 공정 구간 선별 |
| 감지만 수행 | 감지 + 관제 + 이력 관리 **통합 시스템** |

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                     입력층                           │
│   카메라(RTSP)  ──  영상 파일(MP4)  ──  ffmpeg       │
└───────────────────────┬─────────────────────────────┘
                        │ 프레임 추출 / H.264 변환
┌───────────────────────▼─────────────────────────────┐
│                처리층 (Phase 1)                      │
│         YOLOv8n ── 공정 인식 (4 classes)             │
│         VLM     ── 자연어 설명 생성 (Phase 2)         │
└───────────────────────┬─────────────────────────────┘
                        │ 인식 결과
┌───────────────────────▼─────────────────────────────┐
│                     저장층                           │
│      Oracle DB ── 파일 스토리지 ── 운영 로그          │
└───────────────────────┬─────────────────────────────┘
                        │ REST API
┌───────────────────────▼─────────────────────────────┐
│                    서비스층                          │
│         FastAPI ── AI Agent (Phase 3)                │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                     표현층                           │
│         관제 대시보드 ── 이력 조회 화면               │
└─────────────────────────────────────────────────────┘
```

---

## 🔬 인식 대상 공정

재료공학 전공 지식을 바탕으로 배터리 제조의 핵심 4개 공정을 클래스로 정의했습니다.

| 클래스 | 공정명 | 설명 |
|:---:|---|---|
| `Coating` | 코팅 | 집전체(Foil)에 활물질 슬러리를 균일하게 도포하는 공정 |
| `Calendering` | 캘린더링 | 코팅된 전극을 고압 롤러로 압착하여 밀도/두께를 조정하는 공정 |
| `Slitting` | 슬리팅 | 전극 시트를 셀 규격에 맞는 폭으로 정밀 절단하는 공정 |
| `Winding` | 와인딩 | 양극재·분리막·음극재를 감아 젤리롤(Jelly Roll)을 형성하는 공정 |

> **도메인 지식 적용 사례**: Coating과 Calendering은 시각적으로 유사하여 오분류가 잦습니다.
> 재료공학 지식을 바탕으로 공정별 핵심 시각 특징(Slot Die 노즐, Press Roller 등)을 기준으로
> 학습 데이터 구간을 세밀하게 선별하여 오분류를 최소화했습니다.

---

## ⚙️ 기술 스택

| 분류 | 기술 |
|---|---|
| **AI 모델** | YOLOv8n (Ultralytics) |
| **학습 환경** | Google Colab (Tesla T4 GPU) |
| **데이터 관리** | Roboflow (라벨링 · 증강 · 버전 관리) |
| **영상 처리** | ffmpeg (AV1 → H.264 변환, 프레임 추출) |
| **백엔드** | FastAPI (Python 3.10+) |
| **데이터베이스** | Oracle DB (SQL Developer) |
| **이미지 증강** | Gemini (합성 학습 데이터 생성) |
| **개발 환경** | WSL Ubuntu, VS Code |

---

## 🚀 주요 기능 및 구현 현황

### Phase 1 — 공정 인식 + 실시간 관제 (진행중)

- [x] YOLOv8n 단일 모델로 4개 공정 클래스 인식
- [x] 신뢰도 임계값(conf=0.5) 기반 결과 필터링
- [x] 바운딩박스 + 클래스명 + 신뢰도 오버레이
- [x] AV1 코덱 소스 영상 H.264 변환 처리
- [x] Roboflow 기반 학습 데이터셋 구축
- [ ] FastAPI REST API 서버 구축
- [ ] 실시간 관제 대시보드
- [ ] Oracle DB 인식 결과 저장 및 이력 조회

### Phase 2 — VLM 자연어 설명 (예정)

- [ ] YOLOv8 + VLM 파이프라인 연동
- [ ] 공정 상태 자연어 설명 생성
- [ ] 대시보드 설명 표시 UI

### Phase 3 — AI 에이전트 자동화 (예정)

- [ ] 공정 상태 기반 자동 대응 시나리오
- [ ] 다중 공정 라인 자율 관제

---

## 📊 학습 결과

> 학습 환경: Google Colab Tesla T4 GPU | 모델: YOLOv8n | imgsz=512

| 버전 | mAP@0.5 | Precision | Recall | 특이사항 |
|:---:|:---:|:---:|:---:|---|
| battery_v2 | - | - | - | 초기 4클래스 학습 |
| battery_v3 | - | - | - | 데이터 증강 적용 |
| battery_v4 | - | - | - | 클래스 혼동 개선 |
| battery_v4-2 | - | - | - | Winding 구간 정제 |

> 수치는 학습 완료 후 업데이트 예정

---

## 📁 프로젝트 문서

설계 단계별 산출물을 체계적으로 정리했습니다.

| 문서 | 설명 | 링크 |
|---|---|---|
| 요구사항 정의서 (RD) | 비즈니스 관점 고수준 요구사항 | [docs/01_requirements/](docs/01_requirements/) |
| 요구사항 명세서 (SRS) | 기능/비기능 요구사항 상세 명세 (Excel) | [docs/01_requirements/](docs/01_requirements/) |
| ERD + DDL | DB 스키마 설계 (Oracle) | [docs/02_database/](docs/02_database/) |
| ERD 설계 근거 | 컬럼별 타입 선택 이유 및 대안 검토 | [docs/02_database/](docs/02_database/) |
| 시스템 아키텍처 설계서 | 레이어 구성, 데이터 흐름, 기술 스택 | [docs/03_architecture/](docs/03_architecture/) |

---

## 🛠️ 설치 및 실행

### 환경 요구사항

```
Python 3.10+
CUDA 지원 GPU (권장)
ffmpeg
Oracle DB (SQL Developer)
```

### 설치

```bash
git clone https://github.com/YOUR_USERNAME/battery_vision.git
cd battery_vision

pip install ultralytics
pip install fastapi uvicorn
pip install -r requirements.txt
```

### 영상 전처리 (AV1 → H.264)

```bash
ffmpeg -i input.mp4 -c:v libx264 output.mp4
```

### 공정 인식 실행

```bash
python3 src/detect.py --source output.mp4 --weights models/best.pt --conf 0.5
```

### DB 스키마 적용 (Oracle)

SQL Developer에서 `docs/02_database/battery_vision_ERD_oracle.sql` 실행 (F5)

---

## 📂 프로젝트 구조

```
battery_vision/
├── README.md
├── docs/
│   ├── 01_requirements/
│   │   ├── battery_vision_RD.docx
│   │   └── battery_vision_SRS.xlsx
│   ├── 02_database/
│   │   ├── battery_vision_ERD.sql
│   │   ├── battery_vision_ERD_oracle.sql
│   │   ├── battery_vision_ERD_annotated.sql
│   │   └── battery_vision_ERD_rationale.docx
│   └── 03_architecture/
│       └── battery_vision_architecture.docx
├── src/
│   └── detect.py
├── models/
│   └── best.pt
├── notebooks/
│   └── battery_vision_train.ipynb
└── data/
    └── raw/frames/
```

---

## 🗺️ 로드맵

```
2025
 ├── Phase 1  공정 인식 + 실시간 관제  ◀ 현재
 ├── Phase 2  VLM 자연어 설명 연동
 └── Phase 3  AI 에이전트 자동화
```

---

## 👤 개발자

**도영**
- 전공: 재료공학
- 관심 분야: 제조 AI, 컴퓨터 비전, 스마트팩토리
- GitHub: [@YOUR_USERNAME](https://github.com/YOUR_USERNAME)

> 재료공학 도메인 지식과 AI 기술을 결합하여  
> 실제 배터리 제조 현장에 적용 가능한 비전 시스템을 목표로 개발 중입니다.
