#!/usr/bin/env python3

import math

import rclpy
from action_msgs.msg import GoalStatus
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node


def yaw_to_quaternion(yaw):
    half_yaw = yaw * 0.5
    return 0.0, 0.0, math.sin(half_yaw), math.cos(half_yaw)


class NavToPoseClient(Node):
    def __init__(self):
        super().__init__('nav_to_pose')

        self.declare_parameter('action_name', '/navigate_to_pose')
        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('x', 0.0)
        self.declare_parameter('y', 0.0)
        self.declare_parameter('z', 0.0)
        self.declare_parameter('yaw', 0.0)
        self.declare_parameter('behavior_tree', '')
        self.declare_parameter('server_timeout_sec', 10.0)

        self.action_name = self.get_parameter('action_name').value
        self.frame_id = self.get_parameter('frame_id').value
        self.x = float(self.get_parameter('x').value)
        self.y = float(self.get_parameter('y').value)
        self.z = float(self.get_parameter('z').value)
        self.yaw = float(self.get_parameter('yaw').value)
        self.behavior_tree = self.get_parameter('behavior_tree').value
        self.server_timeout_sec = float(
            self.get_parameter('server_timeout_sec').value
        )

        self.action_client = ActionClient(
            self,
            NavigateToPose,
            self.action_name,
        )

    def create_goal_msg(self):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = self.frame_id
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()

        goal_msg.pose.pose.position.x = self.x
        goal_msg.pose.pose.position.y = self.y
        goal_msg.pose.pose.position.z = self.z

        qx, qy, qz, qw = yaw_to_quaternion(self.yaw)
        goal_msg.pose.pose.orientation.x = qx
        goal_msg.pose.pose.orientation.y = qy
        goal_msg.pose.pose.orientation.z = qz
        goal_msg.pose.pose.orientation.w = qw

        goal_msg.behavior_tree = self.behavior_tree
        return goal_msg

    def send_goal(self):
        self.get_logger().info(
            f'Waiting for Nav2 action server: {self.action_name}'
        )

        if not self.action_client.wait_for_server(
                timeout_sec=self.server_timeout_sec):
            self.get_logger().error(
                f'Action server {self.action_name} is not available.'
            )
            rclpy.shutdown()
            return

        self.get_logger().info(
            f'Sending navigation goal: frame={self.frame_id}, '
            f'x={self.x:.3f}, y={self.y:.3f}, yaw={self.yaw:.3f} rad'
        )

        future = self.action_client.send_goal_async(
            self.create_goal_msg(),
            feedback_callback=self.feedback_callback,
        )
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().error('Navigation goal was rejected.')
            rclpy.shutdown()
            return

        self.get_logger().info('Navigation goal accepted.')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        navigation_time = (
            feedback.navigation_time.sec
            + feedback.navigation_time.nanosec * 1e-9
        )

        self.get_logger().info(
            f'Distance remaining: {feedback.distance_remaining:.3f} m, '
            f'navigation time: {navigation_time:.1f} s'
        )

    def result_callback(self, future):
        result = future.result()

        if result.status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('Navigation goal succeeded.')
        elif result.status == GoalStatus.STATUS_ABORTED:
            self.get_logger().error('Navigation goal was aborted.')
        elif result.status == GoalStatus.STATUS_CANCELED:
            self.get_logger().warn('Navigation goal was canceled.')
        else:
            self.get_logger().warn(
                f'Navigation finished with status: {result.status}'
            )

        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = NavToPoseClient()

    try:
        node.send_goal()
        rclpy.spin(node)
    finally:
        if rclpy.ok():
            rclpy.shutdown()
        node.destroy_node()


if __name__ == '__main__':
    main()
