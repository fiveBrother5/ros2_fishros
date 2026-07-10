from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    plugin_name = LaunchConfiguration("plugin_name")
    linear_speed = LaunchConfiguration("linear_speed")
    angular_speed = LaunchConfiguration("angular_speed")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "plugin_name",
                default_value="motion_control_system/StraightMotion",
            ),
            DeclareLaunchArgument("linear_speed", default_value="0.2"),
            DeclareLaunchArgument("angular_speed", default_value="0.5"),
            Node(
                package="motion_control_system",
                executable="motion_controller",
                name="motion_controller",
                output="screen",
                parameters=[
                    {
                        "plugin_name": plugin_name,
                        "linear_speed": linear_speed,
                        "angular_speed": angular_speed,
                    }
                ],
            ),
        ]
    )
