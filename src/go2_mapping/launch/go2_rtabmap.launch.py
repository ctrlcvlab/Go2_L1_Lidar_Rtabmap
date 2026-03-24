import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # RTAB-Map 코어 맵핑 노드 (SLAM)
        Node(
            package='rtabmap_slam', 
            executable='rtabmap', 
            name='rtabmap',
            output='screen',
            arguments=['-d'],                    # [추가] 실행 시 기존에 저장된 데이터베이스(이전 지도)를 삭제하고 새 맵핑 시작
            parameters=[{
                'frame_id': 'base_link',
                'odom_frame_id': 'odom',             # Go2가 넘겨주는 Odom 프레임을 기준축으로 사용
                'map_frame_id': 'map',
                'subscribe_depth': False,
                'subscribe_rgb': False,
                'subscribe_scan_cloud': True,        # 3D 라이다 포인트 클라우드 입력 활성화
                'approx_sync': True,                 # 센서 데이터 시간축 자동 동기화
                'topic_queue_size': 50,              # 입력 버퍼를 키워 타임스탬프 유실 방지
                'sync_queue_size': 50,               # 튜닝: 로봇과 PC의 지연(Delay) 대비 동기화 큐 확장
                'wait_for_transform': 0.5,           # TF 지연 허용치를 0.5초로 넉넉하게 확장
                
                # (외부 Odometry(odom 토픽)를 사용하므로 내부 odom 계산 노드는 애초에 실행하지 않음)
                
                # --- 지도 업데이트 주기 및 해상도 최적화 ---
                'Rtabmap/DetectionRate': '3',        # 초당 맵핑 처리 횟수. (기본 1Hz를 3~5Hz로 올려 뚝뚝 끊김 개선)
                
                # --- ICP 기반의 루프 클로저 설정 (라이다 특화) ---
                'Reg/Strategy': '1',                 # 정합 알고리즘: 0=Visual, 1=ICP (라이다 전용), 2=Visual+ICP
                'RGBD/NeighborLinkRefining': 'false', # [핵심] 외부 Odom(Point-LIO)을 신뢰하므로 ICP로 재보정 비활성화
                'ICP/VoxelSize': '0.1',              # ICP 계산 속도를 높이기 위한 복셀 크기 (10cm)
                'ICP/MaxCorrespondenceDistance': '0.15',
                'ICP/PointToPlane': 'true',          # 평면 기하학을 활용해 더 단단하게 스캔 매칭
                
                # --- 3D 데이터를 2D 장애물 지도(Grid Map)로 누르기 ---
                'Grid/FromDepth': 'false',           # Depth 카메라가 아니므로 False
                'Grid/RangeMin': '0.3',              # 30cm 이내의 노이즈/내 몸통 점들 무시
                'Grid/RangeMax': '10.0',             # 10m 이내 데이터만 확실하게 지도로 투영
                'Grid/CellSize': '0.05',             # 2D 맵 한 칸(해상도)의 크기: 5cm (안정성 우선)
                'Grid/3D': 'false',                  # 최종 결과물은 2D Occupancy Grid Map 발행
                'Grid/MaxObstacleHeight': '1.0',     # 로봇 중심선 위로 1m 이하 점군을 장애물로 인식
                'Grid/MaxGroundHeight': '0.15',      # Go2 다리 높이 고려 15cm 이하는 바닥으로 필터링
            }],
            remappings=[
                ('odom', '/go2/odom_synced'),
                ('scan_cloud', '/go2/cloud_synced')
            ]
        ),
        
        # RTAB-Map 전용 3D 뷰어 노드 (어떻게 꿰매지는지 3D로 보기 위함)
        Node(
            package='rtabmap_viz', 
            executable='rtabmap_viz', 
            name='rtabmap_viz',
            output='screen',
            parameters=[{
                'frame_id': 'base_link',
                'odom_frame_id': 'odom',
                'subscribe_scan_cloud': True,
                'approx_sync': True,
                'topic_queue_size': 50,
                'sync_queue_size': 50,
            }],
            remappings=[
                ('odom', '/go2/odom_synced'),
                ('scan_cloud', '/go2/cloud_synced')
            ]
        )
    ])
