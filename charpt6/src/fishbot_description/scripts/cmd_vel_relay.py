#!/usr/bin/env python3

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class CmdVelRelay(Node):
    def __init__(self):
        super().__init__('cmd_vel_relay')
        self.publisher = self.create_publisher(
            Twist,
            '/fishbot_diff_drive_controller/cmd_vel_unstamped',
            10,
        )
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.relay_cmd_vel,
            10,
        )
        self.get_logger().info(
            'Relaying /cmd_vel to /fishbot_diff_drive_controller/cmd_vel_unstamped'
        )

    def relay_cmd_vel(self, msg):
        self.publisher.publish(msg)


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
