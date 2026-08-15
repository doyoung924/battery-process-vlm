from ultralytics import YOLO

# 모델 로드 (YOLOv8n = 가장 가벼운 버전, 데이터 적을때 적합)
model = YOLO("yolov8n.pt")

# 학습
results = model.train(
    data="/home/doyoung/battery_vision/data/battey_vsion_dataset/data.yaml",
    epochs=100,
    imgsz=640,
    batch=16,
    name="battery_process_v1",
    project="/home/doyoung/battery_vision/runs",
    patience=20,       # 20 epoch 동안 성능 개선 없으면 조기 종료
    save=True,
    plots=True,        # 학습 결과 그래프 저장
)

print("학습 완료!")
print(f"최고 mAP50: {results.results_dict['metrics/mAP50(B)']}")