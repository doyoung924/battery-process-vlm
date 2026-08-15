import cv2
import os
import numpy as np

def is_similar(img1_path, img2_path, threshold=0.95):
    """두 이미지가 유사한지 체크 (threshold: 0~1, 높을수록 엄격)"""
    img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
    if img1 is None or img2 is None:
        return False
    img1 = cv2.resize(img1, (64, 64))
    img2 = cv2.resize(img2, (64, 64))
    diff = np.mean(np.abs(img1.astype(float) - img2.astype(float)))
    similarity = 1 - (diff / 255)
    return similarity > threshold

def remove_similar_frames(frames_dir, threshold=0.95):
    files = sorted([
        f for f in os.listdir(frames_dir)
        if f.endswith('.jpg')
    ])
    
    keep = [files[0]]
    removed = 0
    
    for i in range(1, len(files)):
        curr = os.path.join(frames_dir, files[i])
        prev = os.path.join(frames_dir, keep[-1])
        
        if is_similar(prev, curr, threshold):
            os.remove(curr)
            removed += 1
        else:
            keep.append(files[i])
    
    print(f"[{frames_dir}] 제거: {removed}장 → 남은: {len(keep)}장")

classes = ["coating", "slitting", "winding"]

for cls in classes:
    frames_dir = f"data/frames/{cls}"
    remove_similar_frames(frames_dir, threshold=0.95)

print("\n=== 최종 결과 ===")
for cls in classes:
    count = len(os.listdir(f"data/frames/{cls}"))
    print(f"{cls}: {count}장")