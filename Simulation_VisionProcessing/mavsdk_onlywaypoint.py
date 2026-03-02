import asyncio
import sys
from mavsdk import System

sys.path.append('/usr/lib/python3/dist-packages')


telem_data = {"lat": 0.0, "lon": 0.0, "rel_alt": 0.0}

async def telemetry(drone):
    global telem_data
    async for position in drone.telemetry.position():
        telem_data["lat"] = position.latitude_deg
        telem_data["lon"] = position.longitude_deg
        telem_data["rel_alt"] = position.relative_altitude_m


async def mission(drone):
    global telem_data

    # Asenkron görevler için ayrı bir thread başlat
    asyncio.create_task(telemetry(drone))

    print("Drone'a bağlanılıyor...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone bağlandı")
            break
    
    print("Hazırlıklar yapılıyor...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_armable:
            print("Sistem hazır!")
            break
        await asyncio.sleep(1)

    print("--Arming") 
    await drone.action.arm()

    print("--Takeoff (80m)")  
    await drone.action.set_takeoff_altitude(80.0)
    await drone.action.takeoff()

    print("--İrtifa Takibi Başladı")
    while telem_data["rel_alt"] < 78.0:
        print(f"Anlık İrtifa: {telem_data['rel_alt']:.2f} m", end="\r")
        await asyncio.sleep(0.1)


    print(f"\n[HEDEF] 80m'ye ulaşıldı.") 

    offset = 0.000009
    current_lat = telem_data["lat"]
    current_lon = telem_data["lon"]

    waypoints = [(current_lat + 200*offset, current_lon + 200*offset)
                 ,(current_lat + 200*offset, current_lon - 200*offset)]
    
    for lat, lon in waypoints:
        print(f"--> Waypointlere gidiliyor: {lat}, {lon}")
        await drone.action.goto_location(lat, lon, 50, 0)
        await asyncio.sleep(15)

    print("--RTL Yapılıyor...")    
    await drone.action.return_to_launch()
    


async def main():
    drone = System()
    await drone.connect(system_address="udp://:14540")
    await mission(drone)

if __name__ == "__main__":
    try:
        asyncio.run(main())    
    except KeyboardInterrupt:
        print("Görev iptal edildi.")    



