# Written by Muhammed Ali Kaya - 01.04.2026
# High Performance: Multithreading + Zero Delay Telemetry

import numpy as np
import cv2
import asyncio
import sys
import torch
import threading
from mavsdk import System
from mavsdk.telemetry import LandedState
from ultralytics import YOLO

# Sistem kütüphaneleri (BUNU SİLMİŞTİM, GERİ KOYDUK!)
sys.path.append('/usr/lib/python3/dist-packages')
from gz.transport13 import Node
from gz.msgs10.image_pb2 import Image

# --- MODEL YÜKLEME ---
model_path = "/home/muhammed/yolo_proje/runs/detect/yolov11_sonuclar/egitim/weights/best.pt"
model = YOLO(model_path)
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Model {device} üzerinde. CUDA: {torch.cuda.is_available()}")

# --- GLOBAL DEĞİŞKENLER ---
current_frame = None
frame_lock = threading.Lock()

# Telemetri gecikmesini önlemek için anlık verileri tutacağımız sözlük
telem_data = {"lat": 0.0, "lon": 0.0, "rel_alt": 0.0}

# --- ARKA PLAN GÖRÜNTÜ İŞLEME (THREAD) ---
def vision_worker():
    global current_frame, frame_lock
    prev_time = 0
    
    while True:
        with frame_lock:
            if current_frame is None:
                continue
            frame = current_frame.copy()
        
        # YOLO Tahmini (Hız için imgsz=320)
        results = model.predict(frame, conf=0.4, verbose=False, imgsz=320, device=device)
        annotated_frame = results[0].plot()
        
        # FPS Hesapla
        new_time = cv2.getTickCount()
        freq = cv2.getTickFrequency()
        fps = freq / (new_time - prev_time) if prev_time > 0 else 0
        prev_time = new_time

        cv2.putText(annotated_frame, f"Vision FPS: {int(fps)}", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow("VTOL Kamera (Optimized)", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# --- GAZEMO KAMERA CALLBACK ---
def camera_callback(msg):
    global current_frame, frame_lock
    try:
        img_data = np.frombuffer(msg.data, dtype=np.uint8)
        raw_frame = img_data.reshape((msg.height, msg.width, 3))
        frame = cv2.cvtColor(raw_frame, cv2.COLOR_RGB2BGR)
        
        with frame_lock:
            current_frame = frame
    except:
        pass

# --- ANLIK TELEMETRİ GÜNCELLEYİCİ (GECİKMEYİ ÇÖZEN KISIM) ---
async def observe_telemetry(drone):
    """Bu fonksiyon arka planda MAVSDK kuyruğunu sürekli boşaltıp güncel veriyi yazar"""
    global telem_data
    async for pos in drone.telemetry.position():
        telem_data["lat"] = pos.latitude_deg
        telem_data["lon"] = pos.longitude_deg
        telem_data["rel_alt"] = pos.relative_altitude_m

# --- DRONE GÖREVİ (ASYNC) ---
async def run_mission(drone):
    global telem_data

    # Arka planda telemetriyi sürekli tazeleyen görevi başlat
    asyncio.create_task(observe_telemetry(drone))

    print("İHA'ya bağlanılıyor...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("İHA bağlandı!")
            break

    print("Hazırlıklar tamamlanıyor...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_armable:
            print("Sistem Hazır!")
            break
        await asyncio.sleep(1)

    print("-- Arming")
    await drone.action.arm()
    
    print("-- Takeoff (80m)")
    await drone.action.set_takeoff_altitude(80.0)
    await drone.action.takeoff()

    # İrtifa Takibi (Artık Gecikmesiz!)
    print("-- İrtifa Takibi Başladı...")
    while telem_data["rel_alt"] < 78.0:
        # Eski paketleri beklemek yerine direkt güncel değişkenden okuyoruz
        print(f"Anlık İrtifa: {telem_data['rel_alt']:.2f} m", end="\r")
        await asyncio.sleep(0.1)
    
    print(f"\n[HEDEF] 80m ulaşıldı.")

    # Waypoint Navigasyonu
    OFFSET = 0.000009 
    current_lat = telem_data["lat"]
    current_lon = telem_data["lon"]

    waypoints = [(current_lat + 100*OFFSET, current_lon + 100*OFFSET),
                 (current_lat + 100*OFFSET, current_lon - 100*OFFSET)]

    for lat, lon in waypoints:
        print(f"--> Waypoint gidiliyor: {lat}, {lon}")
        await drone.action.goto_location(lat, lon, 80, 0)
        await asyncio.sleep(15)

    print("-- RTL Yapılıyor...")
    await drone.action.return_to_launch()

async def main():
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")

    # 1. Kamerayı Dinle
    gz_node = Node()
    gz_node.subscribe(Image, "/vtol_camera/image", camera_callback)

    # 2. Görüntü İşlemeyi Ayrı Bir Thread'de Başlat (FPS'i Kurtaran Hamle)
    t = threading.Thread(target=vision_worker, daemon=True)
    t.start()

    # 3. Ana Görevi Çalıştır
    await run_mission(drone)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nKapatılıyor...")
    finally:
        cv2.destroyAllWindows()