from ultralytics import YOLO
import cv2

# Eğitilmiş modelini yükle
model = YOLO("/home/salih/Masaüstü/yolo/runs/detect/yolov11_sonuclar/egitim12/weights/best.pt")

# Webcam'i aç
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Hata: Kamera açılmadı!")
    exit()

print("Webcam başlatıldı. Çıkmak için 'q' veya ESC tuşuna bas.")
cv2.namedWindow("Mouse Tespiti", cv2.WINDOW_NORMAL)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Kamera okunamadı!")
        break

    # Nesne tespiti yap
    results = model(frame, verbose=False)
    boxes = results[0].boxes

    mouse_bulundu = False

    if len(boxes) > 0:
        for box in boxes:
            # Koordinatları al
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])

            if conf > 0.5:  # Güven skoru %50'den yüksekse
                mouse_bulundu = True

                # Yeşil kutu çiz
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Kutunun üstüne "Mouse" ve confidence yaz
                etiket = f"Mouse %{int(conf * 100)}"
                cv2.putText(frame, etiket, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Ekranın sol üstüne durum yazısı
    if mouse_bulundu:
        cv2.putText(frame, "Mouse Bulundu!", (20, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    else:
        cv2.putText(frame, "Mouse Bulunamadi", (20, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

    cv2.imshow("Mouse Tespiti", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q") or key == 27:
        break

cap.release()
cv2.destroyAllWindows()