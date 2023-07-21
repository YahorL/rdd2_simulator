from os import environ
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.actions import ExecuteProcess
from launch.conditions import LaunchConfigurationEquals, IfCondition
from launch_ros.actions import Node


ARGUMENTS = [
    DeclareLaunchArgument('x', default_value=['0'],
        description='x position'),
    DeclareLaunchArgument('y', default_value=['0'],
        description='y position'),
    DeclareLaunchArgument('z', default_value=['0'],
        description='z position'),
    DeclareLaunchArgument('yaw', default_value=['0'],
        description='yaw position'),
    DeclareLaunchArgument('rviz', default_value='true',
                          choices=['true', 'false'],
                          description='Start rviz.'),
    DeclareLaunchArgument('corti', default_value='true',
                          choices=['true', 'false'],
                          description='Run corti'),
    DeclareLaunchArgument('cerebri', default_value='true',
                          choices=['true', 'false'],
                          description='Run cerebri'),
    DeclareLaunchArgument('bridge', default_value='true',
                          choices=['true', 'false'],
                          description='Run bridges'),
    DeclareLaunchArgument('synapse_ros', default_value='true',
                          choices=['true', 'false'],
                          description='Run synapse_ros'),
    DeclareLaunchArgument('synapse_gz', default_value='true',
                          choices=['true', 'false'],
                          description='Run synapse_gz'),
    DeclareLaunchArgument('joy', default_value='true',
                          choices=['true', 'false'],
                          description='Run joy'),
    DeclareLaunchArgument('description', default_value='true',
                          choices=['true', 'false'],
                          description='Run description'),
    DeclareLaunchArgument('world', default_value='depot',
                          description='GZ World'),
    DeclareLaunchArgument('cerebri_gdb', default_value='false',
                          choices=['true', 'false'],
                          description='Run cerebri with gdb debugger.'),
    DeclareLaunchArgument('uart_shell', default_value='false',
                          choices=['true', 'false'],
                          description='Run cerebri with UART shell.'),
    DeclareLaunchArgument('spawn_model', default_value='true',
                          choices=['true', 'false'],
                          description='Spawn RDDRONE Model'),
    DeclareLaunchArgument('use_sim_time', default_value='true',
                          choices=['true', 'false'],
                          description='Use sim time'),
    DeclareLaunchArgument('log_level', default_value='error',
                          choices=['info', 'warn', 'error'],
                          description='log level'),
]


def generate_launch_description():
    synapse_ros = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
            [get_package_share_directory('synapse_ros'), 'launch', 'synapse_ros.launch.py'])]),
        condition=IfCondition(LaunchConfiguration('synapse_ros')),
        launch_arguments=[('host', ['192.0.2.1']),
                          ('port', '4242'),
                          ('use_sim_time', LaunchConfiguration('use_sim_time'))]
    )

    synapse_gz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
            [get_package_share_directory('synapse_gz'), 'launch', 'synapse_gz.launch.py'])]),
        condition=IfCondition(LaunchConfiguration('synapse_gz')),
        launch_arguments=[('host', ['127.0.0.1']),
                          ('port', '4241'),
                          ('use_sim_time', LaunchConfiguration('use_sim_time'))]
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
            [get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py'])]),
        launch_arguments=[('gz_args', [
            LaunchConfiguration('world'), '.sdf', ' -v 0', ' -r'
            ])]
    )

    cerebri = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
            [get_package_share_directory('cerebri_bringup'), 'launch', 'cerebri.launch.py'])]),
        condition=IfCondition(LaunchConfiguration('cerebri')),
        launch_arguments=[('gdb', LaunchConfiguration('cerebri_gdb')),
                          ('vehicle', 'rddrone'),
                          ('uart_shell', LaunchConfiguration('uart_shell'))],
    )

    joy = Node(
        package='joy',
        executable='joy_node',
        output='screen',
        arguments=['--ros-args', '--log-level', LaunchConfiguration('log_level')],
        condition=IfCondition(LaunchConfiguration('joy')),
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time')
            }],
        remappings=[('/joy', '/cerebri/in/joy')]
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        condition=IfCondition(LaunchConfiguration('bridge')),
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time')
            }],
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
    )

    odom_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        condition=IfCondition(LaunchConfiguration('bridge')),
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time')
            }],
        arguments=[
            '/model/rddrone/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry'
            ],
        remappings=[
            ('/model/rddrone/odometry', '/odom')
            ])

    odom_base_tf_bridge = Node(
        package='ros_gz_bridge', 
        executable='parameter_bridge',
        output='screen',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        condition=IfCondition(LaunchConfiguration('bridge')),
        arguments=[
           ['/model/rddrone/pose' +
            '@tf2_msgs/msg/TFMessage' +
            '[gz.msgs.Pose_V']
        ],
        remappings=[
           (['/model/rddrone/pose'], '/tf')
        ])

    pose_bridge = Node(
        package='ros_gz_bridge', 
        executable='parameter_bridge',
        output='screen',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        condition=IfCondition(LaunchConfiguration('bridge')),
        arguments=[
           ['/model/rddrone/pose' +
            '@tf2_msgs/msg/TFMessage' +
            '[gz.msgs.Pose_V']
        ],
        remappings=[
           (['/model/rddrone/pose'],
            '/_internal/sim_ground_truth_pose')
        ])


    # Robot description
    robot_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
        [get_package_share_directory('rddrone_description'), 'launch', 'robot_description.launch.py'])]),
        condition=IfCondition(LaunchConfiguration('description')),
        launch_arguments=[('use_sim_time', LaunchConfiguration('use_sim_time'))])

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        arguments=[
            '-world', 'default',
            '-name', 'rddrone',
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
            '-Y', LaunchConfiguration('yaw'),
            '-file', PathJoinSubstitution([get_package_share_directory(
                'rddrone_gz_resource'),
                'models/rddrone/model.sdf'])
        ],
        output='screen',
        condition=IfCondition(LaunchConfiguration("spawn_model")))

    rviz2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
        [get_package_share_directory(
        'rddrone_rviz'), 'launch', 'view_robot.launch.py'])]),
        condition=IfCondition(LaunchConfiguration('rviz')),
        launch_arguments=[('use_sim_time', LaunchConfiguration('use_sim_time'))])

    corti = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
        [get_package_share_directory('corti'), 'launch', 'corti.launch.py'])]),
        condition=IfCondition(LaunchConfiguration('corti')),
        launch_arguments=[('use_sim_time', LaunchConfiguration('use_sim_time'))])

    tf_to_odom = Node(
        condition=IfCondition(LaunchConfiguration('corti')),
        package='corti',
        executable='tf_to_odom',
        output='screen',
        parameters=[{
            'base_frame': 'map',
            'target_frame': 'base_link',
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            }],
        remappings=[
            ('/odom', '/cerebri/in/odometry')
            ])

    # Define LaunchDescription variable
    return LaunchDescription(ARGUMENTS + [
        robot_description,
        synapse_ros,
        synapse_gz,
        gz_sim,
        cerebri,
        joy,
        odom_bridge,
        clock_bridge,
        odom_base_tf_bridge,
        pose_bridge,
        rviz2,
        spawn_robot,
        corti,
        tf_to_odom
    ])
