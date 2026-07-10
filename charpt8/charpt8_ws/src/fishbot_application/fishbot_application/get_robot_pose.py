#!/usr/bin/env python3

import math

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener


def quaternion_to_yaw(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class RobotPoseListener(Node):
    def __init__(self):
        super().__init__('get_robot_pose')

        self.declare_parameter('target_frame', 'map')
        self.declare_parameter('source_frame', 'base_footprint')
        self.declare_parameter('lookup_period', 1.0)
        self.declare_parameter('timeout_sec', 0.2)
        self.declare_parameter('once', False)

        self.target_frame = self.get_parameter('target_frame').value
        self.source_frame = self.get_parameter('source_frame').value
        self.lookup_period = float(self.get_parameter('lookup_period').value)
        self.timeout_sec = float(self.get_parameter('timeout_sec').value)
        self.once = bool(self.get_parameter('once').value)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.timer = self.create_timer(self.lookup_period, self.lookup_pose)

        self.get_logger().info(
            f'Looking up robot pose: {self.target_frame} -> {self.source_frame}'
        )

    def lookup_pose(self):
        try:
            transform = self.tf_buffer.lookup_transform(
                self.target_frame,
                self.source_frame,
                rclpy.time.Time(),
                timeout=Duration(seconds=self.timeout_sec),
            )
        except TransformException as error:
            self.get_logger().warn(
                f'Could not get transform {self.target_frame} -> '
                f'{self.source_frame}: {error}'
            )
            return

        translation = transform.transform.translation
        rotation = transform.transform.rotation
        yaw = quaternion_to_yaw(rotation)

        self.get_logger().info(
            'Robot pose: '
            f'x={translation.x:.3f}, '
            f'y={translation.y:.3f}, '
            f'z={translation.z:.3f}, '
            f'yaw={yaw:.3f} rad ({math.degrees(yaw):.1f} deg)'
        )

        if self.once:
            self.timer.cancel()
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = RobotPoseListener()
    try:
        rclpy.spin(node)
    finally:
        if rclpy.ok():
            rclpy.shutdown()
        node.destroy_node()


if __name__ == '__main__':
    main()
