import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/cvr/Desktop/sj/Go2_lidar_rtab/install/go2_mapping'
