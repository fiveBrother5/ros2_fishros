import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_share_path = get_package_share_directory('fishbot_description')
    xacro_path = os.path.join(package_share_path, 'urdf', 'first_robot_with_sensors.urdf.xacro')
    rviz_config_path = os.path.join(package_share_path, 'config', 'first_config.rviz')

    action_declare_arg_model_path = DeclareLaunchArgument(
        name='model',
        default_value=xacro_path,
        description='Absolute path to the robot xacro file with sensors',
    )
    action_declare_arg_robot_state_publisher = DeclareLaunchArgument(
        name='robot_state_publisher',
        default_value='false',
        description='Start robot_state_publisher for display-only use. Gazebo launch owns TF by default.',
    )
    action_declare_arg_joint_state_publisher = DeclareLaunchArgument(
        name='joint_state_publisher',
        default_value='false',
        description='Start joint_state_publisher for display-only use. Gazebo joint_state_broadcaster owns joint states by default.',
    )

    robot_description = ParameterValue(
        Command(['xacro ', LaunchConfiguration('model')]),
        value_type=str,
    )

    action_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        condition=IfCondition(LaunchConfiguration('robot_state_publisher')),
    )

    action_joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        condition=IfCondition(LaunchConfiguration('joint_state_publisher')),
    )

    action_rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config_path],
    )

    return LaunchDescription([
        action_declare_arg_model_path,
        action_declare_arg_robot_state_publisher,
        action_declare_arg_joint_state_publisher,
        action_robot_state_publisher,
        action_joint_state_publisher,
        action_rviz_node,
    ])
