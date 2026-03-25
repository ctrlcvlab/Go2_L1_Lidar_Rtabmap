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
        # 공개 Go2 URDF 예시들이 공통적으로 가리키는 전방/하방 장착 위치를 초기값으로 사용한다.
        # 참고: 정확한 공장 extrinsic은 공개 문서에서 확인되지 않아, 실기 RViz/맵 품질 기준 검증은 여전히 필요하다.
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_lidar_tf',
            arguments=['0.29515', '0', '-0.06597', '0', '-0.2', '0', 'base_link', 'utlidar_lidar']
        )
    ])
