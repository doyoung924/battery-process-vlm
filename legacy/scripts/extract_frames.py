import cv2
import os

# 1. 경로 설정 (사용자 지정 경로 반영)
video_path = '/home/doyoung/battery_vision/data/raw/source/battery_source.mp4'
base_save_path = '/home/doyoung/battery_vision/dataset'

# 2. 구간별 가변 추출 설정 ([시작초, 종료초, 간격(초), 모드])
configs = [
    [71, 238, 2.5, 'train'],   # 양극 일반
    [239, 240, 0.3, 'train'],  # 양극 핵심 진입 (촘촘하게)
    [332, 357, 1.0, 'train'],  # 음극 일반
    [241, 259, 0.5, 'test'],   # 양극 핵심/검사 (격리 검증)
    [358, 379, 0.5, 'test']    # 음극 검사/건조 (격리 검증)
]

def extract():
    # CAP_FFMPEG를 명시하여 소프트웨어 디코딩 강제 시도
    cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print(f"❌ 영상을 찾을 수 없습니다: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30.0
    
    print(f"🎬 영상 FPS: {fps} | 소프트웨어 디코딩 모드로 전환하여 추출을 시작합니다...")

    for start_s, end_s, interval_s, mode in configs:
        save_dir = os.path.join(base_save_path, mode)
        os.makedirs(save_dir, exist_ok=True)
        
        start_f = int(start_s * fps)
        end_f = int(end_s * fps)
        step_f = max(1, int(interval_s * fps)) # ValueError 방지
        
        for f_idx in range(start_f, end_f, step_f):
            cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
            ret, frame = cap.read()
            
            # 디코딩 에러 발생 시 재시도 로직
            if not ret:
                ret, frame = cap.read() 
                if not ret: continue
            
            timestamp = f_idx / fps
            img_name = f"{mode}_{timestamp:.2f}s.jpg"
            cv2.imwrite(os.path.join(save_dir, img_name), frame)
            
    cap.release()
    print(f"✅ 추출 완료! 저장 위치: {base_save_path}")

if __name__ == "__main__":
    extract()