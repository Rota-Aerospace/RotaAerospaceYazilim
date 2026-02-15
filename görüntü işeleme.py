import cv2
import numpy as np
from ultralytics import YOLO

# Load YOLO model
model = YOLO('yolov8n-pose.pt')

# Open webcam
cap = cv2.VideoCapture(0)

# Make OpenCV window resizable
win_name = 'Hand Detection'
cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)

# Rectangle size as fraction of frame (width, height)
rect_w_ratio = 0.25
rect_h_ratio = 0.35

def draw_persistent_rect(frame, w_ratio, h_ratio):
    h, w = frame.shape[:2]
    rw = int(w * w_ratio)
    rh = int(h * h_ratio)
    cx, cy = w // 2, h // 2
    x1, y1 = cx - rw // 2, cy - rh // 2
    x2, y2 = cx + rw // 2, cy + rh // 2
    # Rectangle (blue) and center point (red)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 100, 0), 2)
    cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
    return (x1, y1, x2, y2), (cx, cy)

print("Klavye: '+' veya '-' ile dikdörtgeni büyüt/küçült, 'q' çıkış")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run YOLO pose detection
    results = model(frame)

    # Draw persistent rectangle and center
    (rx1, ry1, rx2, ry2), (rcx, rcy) = draw_persistent_rect(frame, rect_w_ratio, rect_h_ratio)

    # Try to get hand keypoints (if model returned poses)
    hand_found = False
    hand_pos = None
    try:
        if results and results[0].keypoints is not None:
            keypoints = results[0].keypoints.xy[0]
            # choose a hand keypoint if available (use left-wrist index 9 if present)
            if len(keypoints) > 9:
                kp = keypoints[9]
                x, y = int(kp[0]), int(kp[1])
                hand_found = True
                hand_pos = (x, y)
            elif len(keypoints) > 7:
                kp = keypoints[7]
                x, y = int(kp[0]), int(kp[1])
                hand_found = True
                hand_pos = (x, y)
    except Exception:
        hand_found = False

    # If hand detected, draw it and compute distance to rect center if inside
    if hand_found and hand_pos is not None:
        hx, hy = hand_pos
        cv2.circle(frame, (hx, hy), 6, (0, 255, 0), -1)
        # Check if hand is inside the persistent rectangle
        if rx1 <= hx <= rx2 and ry1 <= hy <= ry2:
            dist = np.linalg.norm(np.array([hx, hy]) - np.array([rcx, rcy]))
            cv2.line(frame, (hx, hy), (rcx, rcy), (0, 255, 0), 1)
            cv2.putText(frame, f'Uzaklik: {dist:.1f}px', (hx + 10, hy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, 'El dikdortgenin disinda', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
    else:
        cv2.putText(frame, 'El algilanamadi', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

    # Instructions and current rectangle size
    cv2.putText(frame, f'Dik. boyut: {int(rect_w_ratio*100)}% x {int(rect_h_ratio*100)}%', (10, frame.shape[0]-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    cv2.imshow(win_name, frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('+') or key == ord('='):
        rect_w_ratio = min(0.9, rect_w_ratio + 0.02)
        rect_h_ratio = min(0.9, rect_h_ratio + 0.02)
    elif key == ord('-') or key == ord('_'):
        rect_w_ratio = max(0.05, rect_w_ratio - 0.02)
        rect_h_ratio = max(0.05, rect_h_ratio - 0.02)

cap.release()
cv2.destroyAllWindows()