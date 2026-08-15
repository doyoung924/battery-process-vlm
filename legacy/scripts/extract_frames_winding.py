import cv2
import os

# 설정
video_path = "/home/doyoung/battery_vision/data/raw/winding/Gelon Semi-auto Pouch cell winding machine.mkv"
output_dir = "/home/doyoung/battery_vision/data/raw/winding/winding_frames"
interval_sec = 0.5

# 파일 존재 확인
if not os.path.exists(video_path):
    print(f"❌ 파일을 찾을 수 없습니다: {video_path}")
    print(f"\n현재 폴더의 mkv 파일 목록:")
    folder = os.path.dirname(video_path)
    for f in os.listdir(folder):
        if f.endswith(".mkv"):
            print(f"  - {f}")
    exit()

# 출력 폴더 생성
os.makedirs(output_dir, exist_ok=True)

# 영상 열기
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("❌ 영상을 열 수 없습니다.")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

if fps == 0:
    print("⚠️ FPS 감지 실패 → 기본값 30 사용")
    fps = 30

duration = total_frames / fps
print(f"✅ 파일 확인됨")
print(f"FPS: {fps}")
print(f"총 길이: {duration:.1f}초")
print(f"예상 추출 장수: {int(duration / interval_sec)}장")

# 프레임 추출
interval_frames = int(fps * interval_sec)
frame_idx = 0
saved_count = 0

while True:
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()

    if not ret:
        break

    filename = f"winding_{saved_count:04d}.jpg"
    cv2.imwrite(os.path.join(output_dir, filename), frame)
    saved_count += 1
    frame_idx += interval_frames

cap.release()
print(f"\n✅ 완료! 총 {saved_count}장 → '{output_dir}' 폴더")