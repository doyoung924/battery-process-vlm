from ultralytics import YOLO
import cv2

# 학습된 best.pt 모델 로드
model = YOLO("/home/doyoung/battery_vision/runs/battery_process_v1/weights/best.pt")

# 데모 영상 경로
video_path = "/home/doyoung/battery_vision/data/raw/demo/demo_final_1080p.mp4"
output_path = "/home/doyoung/battery_vision/data/raw/demo/demo_result.mp4"

# 영상에 모델 적용
results = model.predict(
    source=video_path,
    save=True,
    project="/home/doyoung/battery_vision/data/raw/demo",
    name="result",
    conf=0.3,
    iou=0.5,
    show_labels=True,
    show_conf=True,
    line_width=2,
    stream=True,    # ← 이거 추가!
)

for r in results:
    pass

print("✅ 완료! 결과 영상 저장됨")