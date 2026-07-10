import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_share_path = get_package_share_directory('fishbot_description')
    gazebo_ros_share_path = get_package_share_directory('gazebo_ros')
    xacro_path = os.path.join(package_share_path, 'urdf', 'first_robot_with_sensors.urdf.xacro')
    world_path = os.path.join(package_share_path, 'world', 'my-new-world.world')
    rviz_config_path = os.path.join(package_share_path, 'config', 'first_config.rviz')

    action_declare_arg_model_path = DeclareLaunchArgument(
        name='model',
        default_value=xacro_path,
        description='Absolute path to the robot xacro file for Gazebo',
    )
    action_declare_arg_world = DeclareLaunchArgument(
        name='world',
        default_value=world_path,
        description='Absolute path to the Gazebo world file',
    )
    action_declare_arg_gui = DeclareLaunchArgument(
        name='gui',
        default_value='true',
        description='Set to "false" to run Gazebo without the client GUI',
    )
    action_declare_arg_server = DeclareLaunchArgument(
        name='server',
        default_value='true',
        description='Set to "false" to skip starting gzserver',
    )
    action_declare_arg_rviz = DeclareLaunchArgument(
        name='rviz',
        default_value='false',
        description='Start RViz using the Gazebo TF and joint states',
    )

    robot_description = ParameterValue(
        Command(['xacro ', LaunchConfiguration('model')]),
        value_type=str,
    )

    action_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[
            {'use_sim_time': True},
            {'robot_description': robot_description},
        ],
    )

    action_gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_share_path, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={
            'world': LaunchConfiguration('world'),
        }.items(),
        condition=IfCondition(LaunchConfiguration('server')),
    )

    action_gazebo_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_share_path, 'launch', 'gzclient.launch.py')
        ),
        condition=IfCondition(LaunchConfiguration('gui')),
    )

    action_spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'fishbot',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.02',
        ],
        output='screen',
    )

    action_cmd_vel_relay = Node(
        package='fishbot_description',
        executable='cmd_vel_relay.py',
        name='cmd_vel_relay',
        output='screen',
    )

    action_rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config_path],
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    action_spawn_controllers = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=action_spawn_robot,
            on_exit=[
                Node(
                    package='controller_manager',
                    executable='spawner',
                    arguments=[
                        'fishbot_joint_state_broadcaster',
                        '--controller-manager',
                        '/controller_manager',
                    ],
                    output='screen',
                ),
                Node(
                    package='controller_manager',
                    executable='spawner',
                    arguments=[
                        'fishbot_diff_drive_controller',
                        '--controller-manager',
                        '/controller_manager',
                    ],
                    output='screen',
                ),
            ],
        )
    )

    return LaunchDescription([
        action_declare_arg_model_path,
        action_declare_arg_world,
        action_declare_arg_gui,
        action_declare_arg_server,
        action_declare_arg_rviz,
        action_gazebo_server,
        action_gazebo_client,
        action_robot_state_publisher,
        action_cmd_vel_relay,
        action_rviz_node,
        action_spawn_robot,
        action_spawn_controllers,
    ])
