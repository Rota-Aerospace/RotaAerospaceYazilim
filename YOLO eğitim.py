from ultralytics import YOLO

# 1. Hazır bir model yükle (n: nano - hızlı, s: small - biraz daha yavaş ama daha iyi)
model = YOLO('yolov8n.pt') 

# 2. Eğitimi başlat
results = model.train(
    data=r"C:\Users\YEY\Desktop\ROTA\UÇAK MEB\SAVASAN IHA.v1i.yolov11\data.yaml", # Oluşturduğun yaml dosyasının yolu
    epochs=100,       # Veri setinin üzerinden kaç kez geçileceği
    imgsz=640,        # Görsel boyutu
    device=0          # Eğer GPU varsa 0, yoksa 'cpu' yazabilirsin
)