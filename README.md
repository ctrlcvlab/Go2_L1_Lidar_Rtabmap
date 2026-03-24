# Go2 LiDAR RTAB-Map SLAM

## 🎯 Overview
Go2 LiDAR RTAB-Map SLAM 프로젝트는 Unitree Go2 로봇의 4D LiDAR와 Point-LIO를 이용해 생성된 내부 Odometry를 기반으로, 외부 PC(ROS 2) 환경에서 실시간 3D 환경 맵핑을 수행하는 프레임워크입니다.
이 파이프라인은 로봇에서 스트리밍되는 `cloud_deskewed` 3D 포인트 클라우드 데이터와 `robot_odom` 간의 동기화 및 맵 잔상(Ghosting) 문제를 해결하기 위한 구조를 적용하였으며, 안정적인 전역 3D Pointcloud Map 및 2D Grid Map 생성을 목표로 합니다.

## 📑 Table of Contents
- [🎯 Overview](#-overview)
- [🗺️ Project Roadmap](#️-project-roadmap)
- [🛠️ Prerequisites](#️-prerequisites)
- [📦 Dependencies](#-dependencies)
- [⚙️ Installation & Setup](#️-installation--setup)
- [📂 Project Structure](#-project-structure)
- [🏗️ Modules](#️-modules)
  - [1. Data Synchronization & TF Setup](#1-data-synchronization--tf-setup)
  - [2. 3D SLAM (RTAB-Map)](#2-3d-slam-rtab-map)

## 🗺️ Project Roadmap
이 프로젝트는 Go2 로봇의 SLAM 및 Navigation 성능을 극대화하기 위해 다음과 같은 단계적인 접근을 취합니다.
- **Phase 1: 3D SLAM & Localization (현재 단계)**
  - Unitree Go2의 4D LiDAR 데이터와 내부 Point-LIO 오도메트리 파이프라인과의 연동
  - 실시간 Point cloud 맵핑 및 RTAB-Map 파라미터 최적화(ICP 활용 단일화)
  - `deskewed` 데이터와 odom 시각 불일치 현상에 따른 맵 번짐(Ghosting) 문제 완화
- **Phase 2: Autonomous Navigation (Nav2)**
  - 작성된 지도를 바탕으로 ROS 2 Nav2 스택을 활용한 자율 주행 및 동적 장애물 회피 알고리즘 최적화 (추후 연동 예정)

## 🛠️ Prerequisites
원활한 작동을 위해 시스템 환경이 다음 요구 사항을 충족하는지 확인해주세요:
- **OS**: Ubuntu 22.04 LTS
- **ROS 2**: [Humble Hawksbill](https://docs.ros.org/en/humble/Installation.html)
- **Robot**: Unitree Go2 Pro (Point-LIO 활성화 상태)

## 📦 Dependencies
RTAB-Map 메인 노드 및 시각화 구동을 위해 다음 의존성 패키지가 필요합니다.
```bash
sudo apt update
sudo apt install ros-humble-rtabmap-ros ros-humble-rtabmap
```

## ⚙️ Installation & Setup
1. 프로젝트 디렉토리로 이동 후 워크스페이스 빌드를 진행합니다.
```bash
cd ~/Desktop/sj/Go2_lidar_rtab
colcon build --symlink-install
```

2. 해당 터미널을 소스하여 환경을 반영합니다. 여러 터미널을 사용할 때 각 터미널에 적용해 주어야 합니다.
```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
```

## 📂 Project Structure
```text
Go2_lidar_rtab/
├── slam_concept_summary.md  # SLAM 맵핑 및 Deskew 클라우드 프레임의 이해/분석 이론 기반 문서
└── src/
    └── go2_mapping/         # 메인 ROS 2 패키지 포지션 
        ├── launch/
        │   ├── go2_rtabmap.launch.py   # RTAB-Map 코어 맵핑 및 비주얼라이제이션 실행 노드
        │   └── tf_setup.launch.py      # Base - Lidar 간 정적 TF 및 Odom Broadcasting 실행 패키지
        ├── package.xml
        └── setup.py
```

## 🏗️ Modules

### 1. Data Synchronization & TF Setup
원활한 실시간 맵핑을 하려면, Go2 내부의 Odometry와 Lidar의 정확하고 빠른 Transform 데이터 연결이 필수적입니다. 이 모듈은 센서 장착 물리 위치(`base_link` -> `utlidar_lidar`)에 대한 정적(Static) TF를 퍼블리시하고 `odom_tf_broadcaster`를 통해 동적 체인을 구성합니다.
> **💡 튜닝 노트**: Unitree 로봇 단에서 이미 global 포인트들(`odom` 기준)로 생성된 point cloud를 수신받아 다시 `base_link` 로컬 좌표로 역변환하는 중간 단축에서 생기는 지연이 맵의 정확도와 연관 깊습니다. 관련 상세 이론 및 문제 해결법은 `slam_concept_summary.md` 문서를 참고해주세요.

#### 🚀 How to Run
```bash
ros2 launch go2_mapping tf_setup.launch.py
```

### 2. 3D SLAM (RTAB-Map)
RTAB-Map을 활용하여 수신된 원본 클라우드 포인트(`scan_cloud`)와 오도메트리(`odom`)를 Approx Sync 기반으로 동기화 처리 후, 포인트-투-플레인(PointToPlane) ICP 매칭 기반의 단단한 스캔 정합 방식으로 실시간 3D 환경 맵핑과 안정적인 2D 점유 격자 지도(Grid Map)를 동시 생성합니다.

- **주요 최적화 파라미터**:
  - `approx_sync=True` / 큐 사이즈(`50`): 로봇과 PC 간의 무선 네트워크 타임스탬프 유실 및 딜레이 방어.
  - `Reg/Strategy=1`: Visual 연산 비활성화 및 라이다 데이터 기반 ICP 속도/안정성 최적화.
  - `Grid/MaxObstacleHeight=1.0` / `Grid/CellSize=0.05`: 로봇의 다리와 지형을 고려하여 15cm~1m 사이 5cm 정밀도의 최적 2D 장애물 맵 필터링.

#### 🚀 How to Run
```bash
ros2 launch go2_mapping go2_rtabmap.launch.py
```
> **💡 Tip**: 명령어 실행 시 `rtabmap_viz` 패키지가 3D 점군 지도 생성 현황을 오도메트리 이동선과 함께 즉시 직관적으로 시각화합니다.
