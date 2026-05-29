#!/usr/bin/env python3
import os
import rosbag
import cv2
from cv_bridge import CvBridge

BAG_PATH = "/catkin_ws/src/FAST-Calib/calib_data/ros2_bagfile.bag"
OUT_DIR = "/catkin_ws/src/FAST-Calib/calib_data/fastcalib_scenes"

IMAGE_TOPIC = "/image_raw"
LIDAR_TOPIC = "/livox/lidar"

OUT_IMAGE_PATH = os.path.join(OUT_DIR, "ros2_bagfile.png")
OUT_BAG_PATH = os.path.join(OUT_DIR, "ros2_bagfile.bag")

# 중간 image timestamp 기준 LiDAR를 앞뒤 몇 초까지 포함할지
WINDOW = 2.0  # ±2 seconds

os.makedirs(OUT_DIR, exist_ok=True)

bridge = CvBridge()

images = []
lidars = []

print("[INFO] Reading bag:", BAG_PATH)

with rosbag.Bag(BAG_PATH, "r") as bag:
    for topic, msg, t in bag.read_messages(topics=[IMAGE_TOPIC, LIDAR_TOPIC]):
        if topic == IMAGE_TOPIC:
            images.append((t, msg))
        elif topic == LIDAR_TOPIC:
            lidars.append((t, msg))

print(f"[INFO] Images: {len(images)}")
print(f"[INFO] Lidars: {len(lidars)}")

if len(images) == 0:
    raise RuntimeError("No image messages found.")
if len(lidars) == 0:
    raise RuntimeError("No LiDAR messages found.")

# 1. 중간 image 하나만 저장
mid_idx = len(images) // 2
t_img, img_msg = images[mid_idx]

cv_img = bridge.imgmsg_to_cv2(img_msg, desired_encoding="bgr8")
cv2.imwrite(OUT_IMAGE_PATH, cv_img)

print("[INFO] Saved middle image:")
print(f"       index = {mid_idx}")
print(f"       time  = {t_img.to_sec():.6f}")
print(f"       path  = {OUT_IMAGE_PATH}")

# 2. 중간 image timestamp 기준 ±2초 LiDAR만 선택
near_lidars = []

for t_lidar, lidar_msg in lidars:
    dt = abs((t_lidar - t_img).to_sec())
    if dt <= WINDOW:
        near_lidars.append((t_lidar, lidar_msg))

print(f"[INFO] Selected LiDAR messages within ±{WINDOW:.1f} sec:")
print(f"       count = {len(near_lidars)} / {len(lidars)}")

if len(near_lidars) == 0:
    raise RuntimeError("No LiDAR messages found within the selected time window.")

# 3. 선택된 LiDAR message만 하나의 bag으로 저장
with rosbag.Bag(OUT_BAG_PATH, "w") as outbag:
    for t_lidar, lidar_msg in near_lidars:
        outbag.write(LIDAR_TOPIC, lidar_msg, t_lidar)

print("[INFO] Saved LiDAR bag:")
print(f"       path = {OUT_BAG_PATH}")

print("[DONE]")
