#!/usr/bin/env python3

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


def limit_step(current, target, max_delta):
    if target > current + max_delta:
        return current + max_delta
    if target < current - max_delta:
        return current - max_delta
    return target


class CmdVelRelay(Node):
    def __init__(self):
        super().__init__('cmd_vel_relay')
        self.declare_parameter('input_topic', '/cmd_vel')
        self.declare_parameter(
            'output_topic',
            '/fishbot_diff_drive_controller/cmd_vel_unstamped',
        )
        self.declare_parameter('publish_rate', 50.0)
        self.declare_parameter('command_timeout', 0.7)
        self.declare_parameter('linear_accel_limit', 1.2)
        self.declare_parameter('angular_accel_limit', 6.0)

        self.input_topic = self.get_parameter('input_topic').value
        self.output_topic = self.get_parameter('output_topic').value
        self.publish_rate = self.get_parameter('publish_rate').value
        self.command_timeout = self.get_parameter('command_timeout').value
        self.linear_accel_limit = self.get_parameter('linear_accel_limit').value
        self.angular_accel_limit = self.get_parameter('angular_accel_limit').value

        self.target_cmd = Twist()
        self.current_cmd = Twist()
        self.last_cmd_time = self.get_clock().now()
        self.last_publish_time = self.get_clock().now()

        self.publisher = self.create_publisher(
            Twist,
            self.output_topic,
            10,
        )
        self.subscription = self.create_subscription(
            Twist,
            self.input_topic,
            self.relay_cmd_vel,
            10,
        )
        self.timer = self.create_timer(1.0 / self.publish_rate, self.publish_cmd)
        self.get_logger().info(
            f'Relaying {self.input_topic} to {self.output_topic} at '
            f'{self.publish_rate:.1f} Hz'
        )

    def relay_cmd_vel(self, msg):
        self.target_cmd = msg
        self.last_cmd_time = self.get_clock().now()

    def publish_cmd(self):
        now = self.get_clock().now()
        dt = (now - self.last_publish_time).nanoseconds * 1e-9
        self.last_publish_time = now

        target = self.target_cmd
        if (now - self.last_cmd_time).nanoseconds * 1e-9 > self.command_timeout:
            target = Twist()

        self.current_cmd.linear.x = limit_step(
            self.current_cmd.linear.x,
            target.linear.x,
            self.linear_accel_limit * dt,
        )
        self.current_cmd.angular.z = limit_step(
            self.current_cmd.angular.z,
            target.angular.z,
            self.angular_accel_limit * dt,
        )
        self.publisher.publish(self.current_cmd)


def main():
    rclpy.init()
    node = CmdVelRelay()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
