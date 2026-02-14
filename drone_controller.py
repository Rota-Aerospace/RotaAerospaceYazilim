#!/usr/bin/env python3
"""
MAVROS ile Gazebo'da Drone Kontrolü
PX4 otopilotu ile simüle edilmiş drone uçuşu
"""

import rospy
import math
from geometry_msgs.msg import PoseStamped, TwistStamped
from mavros_msgs.msg import State, PositionTarget
from mavros_msgs.srv import CommandBool, SetMode, CommandTOL
from sensor_msgs.msg import Imu
import time

class DroneController:
    def __init__(self):
        # Node başlat
        rospy.init_node('drone_controller', anonymous=True)
        
        # Değişkenler
        self.current_state = State()
        self.current_pose = PoseStamped()
        self.target_pose = PoseStamped()
        self.imu_data = Imu()
        
        # Yayınlayıcılar ve Abone Olanlar
        self.state_sub = rospy.Subscriber("/mavros/state", State, self.state_callback)
        self.local_pose_sub = rospy.Subscriber("/mavros/local_position/pose", PoseStamped, self.pose_callback)
        self.imu_sub = rospy.Subscriber("/mavros/imu/data", Imu, self.imu_callback)
        
        # Local position setpoint yayıncısı
        self.local_setpoint_pub = rospy.Publisher("/mavros/setpoint_position/local", PoseStamped, queue_size=10)
        self.velocity_pub = rospy.Publisher("/mavros/setpoint_velocity/cmd_vel", TwistStamped, queue_size=10)
        
        # MAVROS servisleri
        self.arming_client = rospy.ServiceProxy("/mavros/cmd/arming", CommandBool)
        self.set_mode_client = rospy.ServiceProxy("/mavros/set_mode", SetMode)
        self.takeoff_client = rospy.ServiceProxy("/mavros/cmd/takeoff", CommandTOL)
        self.land_client = rospy.ServiceProxy("/mavros/cmd/land", CommandTOL)
        
        # Başlangıç durumu
        self.ready_to_fly = False
        
        rospy.loginfo("Drone Controller başladı!")
    
    def state_callback(self, msg):
        """Drone durumunu al"""
        self.current_state = msg
        
    def pose_callback(self, msg):
        """Mevcut pozisyonu al"""
        self.current_pose = msg
    
    def imu_callback(self, msg):
        """IMU verilerini al"""
        self.imu_data = msg
    
    def wait_for_connection(self, timeout=10):
        """MAVROS bağlantısının kurulmasını bekle"""
        start_time = time.time()
        rate = rospy.Rate(10)
        
        while not self.current_state.connected and (time.time() - start_time) < timeout:
            rate.sleep()
        
        if self.current_state.connected:
            rospy.loginfo("MAVROS bağlantısı kuruldu!")
            return True
        else:
            rospy.logerr("MAVROS bağlantısı başarısız!")
            return False
    
    def set_offboard_mode(self):
        """Offboard modunu ayarla"""
        rate = rospy.Rate(20)
        
        # Offboard modundan önce setpoint göndermek gerekli
        for _ in range(100):
            if self.current_state.mode != "OFFBOARD":
                target = PoseStamped()
                target.header.stamp = rospy.Time.now()
                target.header.frame_id = "map"
                target.pose.position.x = self.current_pose.pose.position.x
                target.pose.position.y = self.current_pose.pose.position.y
                target.pose.position.z = self.current_pose.pose.position.z
                target.pose.orientation.w = 1.0
                
                self.local_setpoint_pub.publish(target)
            
            rate.sleep()
        
        # Modu değiştir
        try:
            response = self.set_mode_client(0, "OFFBOARD")
            if response.mode_sent:
                rospy.loginfo("Offboard modu etkinleştirildi")
                return True
        except rospy.ServiceException as e:
            rospy.logerr(f"Set Mode hata: {e}")
            return False
    
    def arm_drone(self):
        """Droneyi başlat (arm)"""
        try:
            response = self.arming_client(True)
            if response.success:
                rospy.loginfo("Drone başlatıldı (armed)")
                return True
        except rospy.ServiceException as e:
            rospy.logerr(f"Arming hata: {e}")
            return False
    
    def takeoff(self, height=2.0):
        """Kalkış yap"""
        try:
            response = self.takeoff_client(0, 0, 0, 0, height)
            if response.success:
                rospy.loginfo(f"Kalkış başladı - Yükseklik: {height}m")
                return True
        except rospy.ServiceException as e:
            rospy.logerr(f"Takeoff hata: {e}")
            return False
    
    def land(self):
        """İnişe geç"""
        try:
            response = self.land_client(0, 0, 0, 0, 0)
            if response.success:
                rospy.loginfo("İniş başladı")
                return True
        except rospy.ServiceException as e:
            rospy.logerr(f"Land hata: {e}")
            return False
    
    def move_to_position(self, x, y, z, yaw=0):
        """Belirtilen pozisyona git"""
        target = PoseStamped()
        target.header.stamp = rospy.Time.now()
        target.header.frame_id = "map"
        target.pose.position.x = x
        target.pose.position.y = y
        target.pose.position.z = z
        
        # Yaw açısından quaternion hesapla
        yaw_rad = math.radians(yaw)
        target.pose.orientation.z = math.sin(yaw_rad / 2.0)
        target.pose.orientation.w = math.cos(yaw_rad / 2.0)
        
        self.local_setpoint_pub.publish(target)
    
    def fly_square(self, side_length=5.0, height=3.0):
        """Kare şekilde uç"""
        rate = rospy.Rate(30)
        
        waypoints = [
            (0, 0, height, 0),
            (side_length, 0, height, 0),
            (side_length, side_length, height, 0),
            (0, side_length, height, 0),
            (0, 0, height, 0),
        ]
        
        rospy.loginfo("Kare uçuş başladı!")
        
        for i, (x, y, z, yaw) in enumerate(waypoints):
            rospy.loginfo(f"Waypoint {i+1}: ({x}, {y}, {z})")
            
            # Her waypointe 5 saniye kullan
            for _ in range(150):
                self.move_to_position(x, y, z, yaw)
                rate.sleep()
        
        rospy.loginfo("Kare uçuş tamamlandı!")
    
    def fly_circle(self, radius=5.0, height=3.0, duration=30):
        """Daire şekilde uç"""
        rate = rospy.Rate(30)
        start_time = time.time()
        
        rospy.loginfo(f"Daire uçuş başladı! Yarıçap: {radius}m, Yükseklik: {height}m")
        
        while (time.time() - start_time) < duration:
            elapsed = time.time() - start_time
            angle = (elapsed / duration) * 2 * math.pi
            
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            yaw = math.degrees(angle)
            
            self.move_to_position(x, y, height, yaw)
            rate.sleep()
        
        rospy.loginfo("Daire uçuş tamamlandı!")
    
    def hover(self, duration=5.0):
        """Bir yerde dur"""
        rate = rospy.Rate(30)
        start_time = time.time()
        
        rospy.loginfo(f"{duration} saniye hover yapılıyor...")
        
        while (time.time() - start_time) < duration:
            self.move_to_position(
                self.current_pose.pose.position.x,
                self.current_pose.pose.position.y,
                self.current_pose.pose.position.z
            )
            rate.sleep()
    
    def disarm_drone(self):
        """Droneyi kapat (disarm)"""
        try:
            response = self.arming_client(False)
            if response.success:
                rospy.loginfo("Drone kapatıldı (disarmed)")
                return True
        except rospy.ServiceException as e:
            rospy.logerr(f"Disarming hata: {e}")
            return False
    
    def run_mission(self):
        """Misyon çalıştır"""
        # Bağlantı bekle
        if not self.wait_for_connection():
            return
        
        time.sleep(1)
        
        # Offboard moduna geç
        if not self.set_offboard_mode():
            return
        
        time.sleep(1)
        
        # Droneyi başlat
        if not self.arm_drone():
            return
        
        time.sleep(2)
        
        # Kalkış yap
        if not self.takeoff(3.0):
            return
        
        time.sleep(5)
        
        # Daire uç
        self.fly_circle(radius=5.0, height=3.0, duration=30)
        
        # Hover yap
        self.hover(duration=3.0)
        
        # Kare uç
        self.fly_square(side_length=4.0, height=3.0)
        
        # Tekrar hover
        self.hover(duration=2.0)
        
        # İniş
        if not self.land():
            return
        
        time.sleep(5)
        
        # Kapat
        self.disarm_drone()
        
        rospy.loginfo("Misyon tamamlandı!")


def main():
    try:
        controller = DroneController()
        controller.run_mission()
    except rospy.ROSInterruptException:
        rospy.loginfo("Node kapatıldı")


if __name__ == "__main__":
    main()
