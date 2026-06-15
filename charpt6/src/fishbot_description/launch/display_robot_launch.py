import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_share_path = get_package_share_directory('fishbot_description')
    urdf_path = os.path.join(package_share_path, 'urdf', 'first_robot.urdf')

    action_declare_arg_model_path = DeclareLaunchArgument(
        name='model',
        default_value=urdf_path,
        description='Absolute path to the robot URDF file',
    )

    robot_description = ParameterValue(
        Command(['cat ', LaunchConfiguration('model')]),
        value_type=str,
    )

    action_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
    )

    action_joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
    )

    action_rviz_node = Node(
        package='rviz2',
        executable='rviz2',
    )

    return LaunchDescription([
        action_declare_arg_model_path,
        action_robot_state_publisher,
        action_joint_state_publisher,
        action_rviz_node,
    ])
