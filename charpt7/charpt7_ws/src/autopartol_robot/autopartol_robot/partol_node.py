#!/usr/bin/env python3

from datetime import datetime
import math
import os
from pathlib import Path
import re
import time

import cv2
import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
from nav2_simple_commander.robot_navigator import TaskResult
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String


def yaw_to_quaternion(yaw):
    half_yaw = yaw * 0.5
    return 0.0, 0.0, math.sin(half_yaw), math.cos(half_yaw)


def make_pose(navigator, frame_id, x, y, yaw, z=0.0):
    pose = PoseStamped()
    pose.header.frame_id = frame_id
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.position.z = float(z)

    qx, qy, qz, qw = yaw_to_quaternion(float(yaw))
    pose.pose.orientation.x = qx
    pose.pose.orientation.y = qy
    pose.pose.orientation.z = qz
    pose.pose.orientation.w = qw
    return pose


def get_default_config_path():
    package_share_dir = get_package_share_directory('autopartol_robot')
    return os.path.join(package_share_dir, 'config', 'patrol_points.yaml')


def get_default_capture_dir():
    package_share_dir = Path(
        get_package_share_directory('autopartol_robot')
    ).resolve()
    workspace_root = package_share_dir.parents[3]
    source_package_dir = workspace_root / 'src' / 'autopartol_robot'

    if source_package_dir.is_dir():
        return source_package_dir / 'captures'

    return package_share_dir / 'captures'


def load_patrol_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file) or {}

    frame_id = config.get('frame_id', 'map')
    initial_pose = config.get('initial_pose', {})
    waypoints = config.get('waypoints', [])

    if not waypoints:
        raise RuntimeError(f'No waypoints found in config: {config_path}')

    return frame_id, initial_pose, waypoints


class PatrolRobot(BasicNavigator):
    def __init__(self):
        super().__init__('autopartol_robot')
        self.declare_parameter('config_file', '')
        self.declare_parameter('loop', False)
        self.declare_parameter('wait_nav2_active', True)
        self.declare_parameter('log_interval_sec', 1.0)
        self.declare_parameter('voice_enabled', True)
        self.declare_parameter('voice_topic', '/patrol_voice/text')
        self.declare_parameter('capture_enabled', True)
        self.declare_parameter(
            'camera_topic',
            '/camera_sensor/image_raw',
        )
        self.declare_parameter('capture_directory', '')
        self.declare_parameter('capture_wait_timeout_sec', 3.0)
        self.declare_parameter('capture_jpeg_quality', 95)

        self.config_file = self.get_parameter('config_file').value
        self.loop = bool(self.get_parameter('loop').value)
        self.wait_nav2_active = bool(self.get_parameter('wait_nav2_active').value)
        self.log_interval_sec = float(
            self.get_parameter('log_interval_sec').value
        )
        self.voice_enabled = bool(self.get_parameter('voice_enabled').value)
        self.voice_topic = self.get_parameter('voice_topic').value
        self.voice_pub = self.create_publisher(String, self.voice_topic, 10)
        self.capture_enabled = bool(
            self.get_parameter('capture_enabled').value
        )
        self.camera_topic = self.get_parameter('camera_topic').value
        capture_directory = self.get_parameter('capture_directory').value
        self.capture_wait_timeout_sec = float(
            self.get_parameter('capture_wait_timeout_sec').value
        )
        self.capture_jpeg_quality = int(
            self.get_parameter('capture_jpeg_quality').value
        )
        self.capture_directory = Path(
            capture_directory
        ) if capture_directory else get_default_capture_dir()
        self.capture_directory.mkdir(parents=True, exist_ok=True)

        self.cv_bridge = CvBridge()
        self.latest_image = None
        self.image_sub = self.create_subscription(
            Image,
            self.camera_topic,
            self.image_callback,
            qos_profile_sensor_data,
        )

        if not self.config_file:
            self.config_file = get_default_config_path()

        self.info(f'订阅摄像头图像: {self.camera_topic}')
        self.info(f'巡检抓拍保存目录: {self.capture_directory}')

    def image_callback(self, msg):
        self.latest_image = msg

    def wait_for_camera_image(self):
        if self.latest_image is not None:
            return True

        deadline = time.monotonic() + self.capture_wait_timeout_sec
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.latest_image is not None:
                return True

        return False

    def save_waypoint_image(self, waypoint_name):
        if not self.capture_enabled:
            return None

        if not self.wait_for_camera_image():
            self.warn(
                f'到达 {waypoint_name}，但没有收到摄像头图像，'
                f'请检查话题 {self.camera_topic}'
            )
            return None

        safe_name = re.sub(
            r'[\\/:*?"<>|\s]+',
            '_',
            waypoint_name,
        ).strip('_')
        if not safe_name:
            safe_name = 'waypoint'

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        image_path = self.capture_directory / (
            f'{timestamp}_{safe_name}.jpg'
        )

        try:
            cv_image = self.cv_bridge.imgmsg_to_cv2(
                self.latest_image,
                desired_encoding='bgr8',
            )
            saved = cv2.imwrite(
                str(image_path),
                cv_image,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    self.capture_jpeg_quality,
                ],
            )
        except Exception as exc:
            self.error(f'保存 {waypoint_name} 图像失败: {exc}')
            return None

        if not saved:
            self.error(f'保存 {waypoint_name} 图像失败: {image_path}')
            return None

        self.info(f'已保存 {waypoint_name} 图像: {image_path}')
        return image_path

    def publish_voice(self, text):
        if not self.voice_enabled:
            return

        msg = String()
        msg.data = text
        self.voice_pub.publish(msg)
        self.info(f'发送语音播报: {text}')

    def pose_from_config(self, frame_id, pose_config):
        return make_pose(
            self,
            frame_id,
            pose_config.get('x', 0.0),
            pose_config.get('y', 0.0),
            pose_config.get('yaw', 0.0),
            pose_config.get('z', 0.0),
        )

    def waypoint_from_config(self, frame_id, waypoint):
        return make_pose(
            self,
            frame_id,
            waypoint['x'],
            waypoint['y'],
            waypoint.get('yaw', 0.0),
            waypoint.get('z', 0.0),
        )

    def set_initial_pose_from_config(self, frame_id, initial_pose):
        pose = self.pose_from_config(frame_id, initial_pose)
        self.setInitialPose(pose)
        self.info(
            '已设置机器人初始位置: '
            f'x={pose.pose.position.x:.3f}, '
            f'y={pose.pose.position.y:.3f}, '
            f'yaw={initial_pose.get("yaw", 0.0):.3f} rad'
        )

    def get_current_pose(self):
        if not self.initial_pose_received:
            return None
        return self.initial_pose

    def wait_until_nav2_ready(self):
        if self.wait_nav2_active:
            self.info('等待 Nav2 和 AMCL 就绪...')
            self.waitUntilNav2Active()
        else:
            self.info('跳过 Nav2 active 等待，请确认 Nav2 已经启动完成。')

    def log_feedback(self, name, feedback):
        if feedback is None:
            return

        distance_remaining = getattr(feedback, 'distance_remaining', None)
        navigation_time = getattr(feedback, 'navigation_time', None)

        if distance_remaining is None:
            self.info(f'正在前往 {name}...')
            return

        if navigation_time is not None:
            elapsed = navigation_time.sec + navigation_time.nanosec * 1e-9
            self.info(
                f'正在前往 {name}: 剩余距离 {distance_remaining:.3f} m, '
                f'已导航 {elapsed:.1f} s'
            )
        else:
            self.info(
                f'正在前往 {name}: 剩余距离 {distance_remaining:.3f} m'
            )

    def patrol_once(self, frame_id, waypoints):
        for index, waypoint in enumerate(waypoints, start=1):
            name = waypoint.get('name', f'巡检点{index}')
            goal_pose = self.waypoint_from_config(frame_id, waypoint)

            self.info(
                f'开始前往 {name}: '
                f'x={goal_pose.pose.position.x:.3f}, '
                f'y={goal_pose.pose.position.y:.3f}, '
                f'yaw={waypoint.get("yaw", 0.0):.3f} rad'
            )

            self.clearAllCostmaps()
            if not self.goToPose(goal_pose):
                self.error(f'{name} 目标被拒绝，停止巡检。')
                return False

            last_log_time = 0.0
            while not self.isTaskComplete():
                now = time.monotonic()
                if now - last_log_time >= self.log_interval_sec:
                    self.log_feedback(name, self.getFeedback())
                    last_log_time = now

            result = self.getResult()
            if result == TaskResult.SUCCEEDED:
                self.info(f'已到达 {name}')
                self.save_waypoint_image(name)
                voice_text = waypoint.get('voice_text', f'已到达{name}')
                self.publish_voice(voice_text)
                continue

            if result == TaskResult.CANCELED:
                self.warn(f'{name} 导航被取消，停止巡检。')
            else:
                self.error(f'{name} 导航失败，停止巡检。')
            return False

        return True

    def run(self):
        self.info(f'读取巡检配置: {self.config_file}')
        frame_id, initial_pose, waypoints = load_patrol_config(self.config_file)

        self.set_initial_pose_from_config(frame_id, initial_pose)
        self.wait_until_nav2_ready()
        self.info(f'巡检点数量: {len(waypoints)}')

        round_index = 1
        while rclpy.ok():
            self.info(f'开始第 {round_index} 轮巡检')
            success = self.patrol_once(frame_id, waypoints)

            if not success:
                self.error('巡检任务异常结束。')
                return False

            self.info(f'第 {round_index} 轮巡检完成')
            if not self.loop:
                return True

            round_index += 1

        return False


def main(args=None):
    rclpy.init(args=args)
    navigator = PatrolRobot()

    try:
        navigator.run()
    finally:
        navigator.destroyNode()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
