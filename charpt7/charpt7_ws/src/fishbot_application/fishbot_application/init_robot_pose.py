#!/usr/bin/env python3

import math

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node


def yaw_to_quaternion(yaw):
    half_yaw = yaw * 0.5
    return 0.0, 0.0, math.sin(half_yaw), math.cos(half_yaw)


class InitialRobotPosePublisher(Node):
    def __init__(self):
        super().__init__('init_robot_pose')

        self.declare_parameter('topic', '/initialpose')
        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('x', 0.0)
        self.declare_parameter('y', 0.0)
        self.declare_parameter('z', 0.0)
        self.declare_parameter('yaw', 0.0)
        self.declare_parameter('publish_count', 5)
        self.declare_parameter('publish_period', 0.2)
        self.declare_parameter('covariance_x', 0.25)
        self.declare_parameter('covariance_y', 0.25)
        self.declare_parameter('covariance_yaw', 0.06853891909122467)

        self.topic = self.get_parameter('topic').value
        self.frame_id = self.get_parameter('frame_id').value
        self.x = float(self.get_parameter('x').value)
        self.y = float(self.get_parameter('y').value)
        self.z = float(self.get_parameter('z').value)
        self.yaw = float(self.get_parameter('yaw').value)
        self.publish_count = int(self.get_parameter('publish_count').value)
        self.publish_period = float(self.get_parameter('publish_period').value)
        self.covariance_x = float(self.get_parameter('covariance_x').value)
        self.covariance_y = float(self.get_parameter('covariance_y').value)
        self.covariance_yaw = float(self.get_parameter('covariance_yaw').value)

        self.publisher = self.create_publisher(
            PoseWithCovarianceStamped,
            self.topic,
            10,
        )
        self.published_count = 0
        self.timer = self.create_timer(self.publish_period, self.publish_pose)

        self.get_logger().info(
            f'Publishing initial pose on {self.topic}: '
            f'x={self.x:.3f}, y={self.y:.3f}, yaw={self.yaw:.3f}, '
            f'frame={self.frame_id}'
        )

    def create_pose_msg(self):
        msg = PoseWithCovarianceStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id

        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.position.z = self.z

        qx, qy, qz, qw = yaw_to_quaternion(self.yaw)
        msg.pose.pose.orientation.x = qx
        msg.pose.pose.orientation.y = qy
        msg.pose.pose.orientation.z = qz
        msg.pose.pose.orientation.w = qw

        msg.pose.covariance[0] = self.covariance_x
        msg.pose.covariance[7] = self.covariance_y
        msg.pose.covariance[35] = self.covariance_yaw
        return msg

    def publish_pose(self):
        self.publisher.publish(self.create_pose_msg())
        self.published_count += 1

        if self.published_count >= self.publish_count:
            self.get_logger().info('Initial pose published.')
            self.timer.cancel()
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = InitialRobotPosePublisher()
    try:
        rclpy.spin(node)
    finally:
        if rclpy.ok():
            rclpy.shutdown()
        node.destroy_node()


if __name__ == '__main__':
    main()
