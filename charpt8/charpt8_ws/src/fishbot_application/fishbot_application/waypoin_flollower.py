#!/usr/bin/env python3

import math

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import FollowWaypoints
from rclpy.action import ActionClient
from rclpy.node import Node


def yaw_to_quaternion(yaw):
    half_yaw = yaw * 0.5
    return 0.0, 0.0, math.sin(half_yaw), math.cos(half_yaw)


class WaypointFollowerClient(Node):
    def __init__(self):
        super().__init__('waypoint_follower_client')

        self.declare_parameter('action_name', '/follow_waypoints')
        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('server_timeout_sec', 10.0)

        self.action_name = self.get_parameter('action_name').value
        self.frame_id = self.get_parameter('frame_id').value
        self.server_timeout_sec = float(
            self.get_parameter('server_timeout_sec').value
        )

        self.action_client = ActionClient(
            self,
            FollowWaypoints,
            self.action_name,
        )

        # 默认导航点，单位：m / rad。需要换点时直接改这里即可。
        self.waypoints = [
            {'x': 1.0, 'y': 0.0, 'yaw': 0.0},
            {'x': 1.0, 'y': 1.0, 'yaw': 1.57},
            {'x': 0.0, 'y': 1.0, 'yaw': 3.14},
            {'x': 0.0, 'y': 0.0, 'yaw': 0.0},
        ]

    def create_pose(self, x, y, yaw, z=0.0):
        pose = PoseStamped()
        pose.header.frame_id = self.frame_id
        pose.header.stamp = self.get_clock().now().to_msg()

        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.position.z = float(z)

        qx, qy, qz, qw = yaw_to_quaternion(float(yaw))
        pose.pose.orientation.x = qx
        pose.pose.orientation.y = qy
        pose.pose.orientation.z = qz
        pose.pose.orientation.w = qw

        return pose

    def create_goal_msg(self):
        goal_msg = FollowWaypoints.Goal()
        goal_msg.poses = [
            self.create_pose(point['x'], point['y'], point['yaw'])
            for point in self.waypoints
        ]
        return goal_msg

    def send_goal(self):
        self.get_logger().info(
            f'Waiting for Nav2 waypoint action server: {self.action_name}'
        )

        if not self.action_client.wait_for_server(
                timeout_sec=self.server_timeout_sec):
            self.get_logger().error(
                f'Action server {self.action_name} is not available.'
            )
            rclpy.shutdown()
            return

        self.get_logger().info('Sending waypoint navigation goal:')
        for index, point in enumerate(self.waypoints, start=1):
            self.get_logger().info(
                f'  {index}: frame={self.frame_id}, '
                f'x={point["x"]:.3f}, y={point["y"]:.3f}, '
                f'yaw={point["yaw"]:.3f} rad'
            )

        future = self.action_client.send_goal_async(
            self.create_goal_msg(),
            feedback_callback=self.feedback_callback,
        )
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().error('Waypoint goal was rejected.')
            rclpy.shutdown()
            return

        self.get_logger().info('Waypoint goal accepted.')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        current_waypoint = feedback_msg.feedback.current_waypoint
        self.get_logger().info(
            f'Currently navigating to waypoint index: {current_waypoint}'
        )

    def result_callback(self, future):
        result = future.result()
        missed_waypoints = list(result.result.missed_waypoints)

        if result.status == GoalStatus.STATUS_SUCCEEDED:
            if missed_waypoints:
                self.get_logger().warn(
                    f'Waypoint navigation finished, but missed: '
                    f'{missed_waypoints}'
                )
            else:
                self.get_logger().info(
                    'Waypoint navigation succeeded. All waypoints reached.'
                )
        elif result.status == GoalStatus.STATUS_ABORTED:
            self.get_logger().error(
                f'Waypoint navigation was aborted. Missed: '
                f'{missed_waypoints}'
            )
        elif result.status == GoalStatus.STATUS_CANCELED:
            self.get_logger().warn(
                f'Waypoint navigation was canceled. Missed: '
                f'{missed_waypoints}'
            )
        else:
            self.get_logger().warn(
                f'Waypoint navigation finished with status '
                f'{result.status}. Missed: {missed_waypoints}'
            )

        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = WaypointFollowerClient()

    try:
        node.send_goal()
        rclpy.spin(node)
    finally:
        if rclpy.ok():
            rclpy.shutdown()
        node.destroy_node()


if __name__ == '__main__':
    main()
