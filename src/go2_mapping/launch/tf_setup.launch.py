import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Odom -> Base_link TF Broadcaster Node
        Node(
            package='go2_mapping',
            executable='odom_tf_broadcaster',
            name='odom_tf_broadcaster',
            output='screen'
        ),
        # Static TF: base_link -> utlidar_lidar
        # 참고: Go2 라이다(L1)의 실제 장착 위치에 맞게 x, y, z 거리를 튜닝해야 합니다. (기본값 임시 설정)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_lidar_tf',
            arguments=['0.15', '0', '0.14', '0', '0', '0', 'base_link', 'utlidar_lidar']
        )
    ])
