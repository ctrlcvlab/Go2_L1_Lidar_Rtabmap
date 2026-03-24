#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud2
from geometry_msgs.msg import TransformStamped
import tf2_ros

class OdomTfBroadcaster(Node):
    def __init__(self):
        super().__init__('odom_tf_broadcaster')
        
        # 1. PointCloud2 구독 (로봇이 넘겨주는 Deskewed 점군 - 통신 대역폭 절감 위해 이것만 존재함)
        self.cloud_sub = self.create_subscription(
            PointCloud2,
            '/utlidar/cloud_deskewed',
            self.cloud_callback,
            qos_profile_sensor_data
        )

        # 2. Odometry 구독
        self.odom_sub = self.create_subscription(
            Odometry,
            '/utlidar/robot_odom',
            self.odom_callback,
            qos_profile_sensor_data
        )

        # 동기화된 데이터를 뿌려줄 새 퍼블리셔들 (RELIABLE QoS로 발행 → RTAB-Map 기본 구독과 호환)
        self.cloud_pub = self.create_publisher(
            PointCloud2, 
            '/go2/cloud_synced', 
            10
        )
        
        # [핵심 수정] Odom도 시간 동기화 후 재발행 → RTAB-Map이 이것을 구독
        self.odom_pub = self.create_publisher(
            Odometry,
            '/go2/odom_synced',
            10
        )
        
        # ROS 2 표준 TF 브로드캐스터 초기화
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        
        self.time_offset = None
        self.get_logger().info("Odom TF & Time Sync Relay Node has been started with Offset Sync.")

    def get_synced_stamp(self, original_stamp):
        # 최초 1회: PC 시간과 로봇 시간의 '고정된 시간차(Offset)'를 계산
        if self.time_offset is None:
            now_ns = self.get_clock().now().nanoseconds
            orig_ns = original_stamp.sec * 1000000000 + original_stamp.nanosec
            self.time_offset = now_ns - orig_ns
            
        # 모든 데이터에 동일한 고정 Offset만 더함 (로봇 내부의 Odom과 PointCloud 간 미세한 시간차를 100% 보존)
        orig_ns = original_stamp.sec * 1000000000 + original_stamp.nanosec
        synced_ns = int(orig_ns + self.time_offset)
        return rclpy.time.Time(nanoseconds=synced_ns).to_msg()

    def cloud_callback(self, msg):
        # 고정 오프셋이 적용된 스탬프로 변환
        msg.header.stamp = self.get_synced_stamp(msg.header.stamp)
        self.cloud_pub.publish(msg)

    def odom_callback(self, msg):
        synced_stamp = self.get_synced_stamp(msg.header.stamp)
        
        # 1. TF 브로드캐스트 (odom → base_link)
        t = TransformStamped()
        t.header.stamp = synced_stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        t.transform.rotation = msg.pose.pose.orientation
        self.tf_broadcaster.sendTransform(t)
        
        # 2. 동기화된 Odom 메시지도 재발행 (RTAB-Map용)
        msg.header.stamp = synced_stamp
        self.odom_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = OdomTfBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
