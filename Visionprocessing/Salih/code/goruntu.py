from ultralytics import YOLO

# Model seç: yolo11n / yolo11s / yolo11m / yolo11l / yolo11x
model = YOLO("yolo11n.pt")

model.train(
    data = "/home/salih/Masaüstü/yolov5/yolov2.yaml",
    epochs  = 100,
    imgsz   = 640,
    batch   = 16,
    device  = 0,       # GPU
    project = "yolov11_sonuclar",
    name    = "egitim1",
)