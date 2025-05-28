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
    DeclareLaunchArgument('z', default_value=['0.25'],
        description='z position'),
    DeclareLaunchArgument('yaw', default_value=['0'],
        description='yaw position'),
    DeclareLaunchArgument('electrode', default_value='true',
        choices=['true', 'false'],
        description='enable electrode'),
    DeclareLaunchArgument('controller',
        default_value='f310',
        choices=['f310', 'ps4'],
        description='which controller you are using'),
    DeclareLaunchArgument('sync', default_value='false',
                          choices=['true', 'false'],
                          description='Run async or sync SLAM'),
    DeclareLaunchArgument('localization', default_value='slam',
                          choices=['off', 'localization', 'slam'],
                          description='Whether to run localization or SLAM'),
    DeclareLaunchArgument('nav2', default_value='true',
                          choices=['true', 'false'],
                          description='Run nav2'),
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
    DeclareLaunchArgument('description', default_value='true',
                          choices=['true', 'false'],
                          description='Run description'),
    DeclareLaunchArgument('world', default_value='basic_map',
                          description='GZ World'),
    DeclareLaunchArgument(
        'map_yaml',
        default_value=[LaunchConfiguration('world'), '.yaml'],
        description='Map yaml'),
    DeclareLaunchArgument('cerebri_gdb', default_value='false',
                          choices=['true', 'false'],
                          description='Run cerebri with gdb debugger.'),
    DeclareLaunchArgument('spawn_model', default_value='true',
                          choices=['true', 'false'],
                          description='Spawn RDD2 Model'),
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
                          ('port', '4243'),
                          ('vehicle', 'rdd2'),
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
                          ('vehicle', 'rdd2')],
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge_gz_ros_clock',
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
        name='bridge_gz_ros_odom',
        output='screen',
        condition=IfCondition(LaunchConfiguration('bridge')),
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time')
            }],
        arguments=['/model/rdd2/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry'],
        remappings=[('/model/rdd2/odometry','/odom')
        ])

    lidar_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge_gz_ros_lidar',
        output='screen',
        condition=IfCondition(LaunchConfiguration('bridge')),
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }],
        arguments=[
            '/world/default/model/rdd2/link/lidar_link/sensor/lidar/scan' +
             '@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'
        ],
        remappings=[
            ('/world/default/model/rdd2/link/lidar_link/sensor/lidar/scan',
             '/scan')
        ])

    camera_info_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge_gz_ros_camera_info',
        output='screen',
        condition=IfCondition(LaunchConfiguration('bridge')),
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }],
        arguments=[
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo'
        ])

    camera_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        name='bridge_gz_ros_camera',
        output='screen',
        condition=IfCondition(LaunchConfiguration('bridge')),
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }],
        arguments=['/camera/image_raw'])

    # Robot description
    robot_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
        [get_package_share_directory('rdd2_description'), 'launch', 'robot_description.launch.py'])]),
        condition=IfCondition(LaunchConfiguration('description')),
        launch_arguments=[('use_sim_time', LaunchConfiguration('use_sim_time'))])

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        arguments=[
            '-world', 'default',
            '-name', 'rdd2',
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
            '-Y', LaunchConfiguration('yaw'),
            '-file', PathJoinSubstitution([get_package_share_directory(
                'rdd2_gz_resource'),
                'models/rdd2/model.sdf'])
        ],
        output='screen',
        condition=IfCondition(LaunchConfiguration("spawn_model")))

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
        [get_package_share_directory(
        'rdd2_nav2'), 'launch', 'nav2.launch.py'])]),
        condition=IfCondition(LaunchConfiguration('nav2')),
        launch_arguments=[('use_sim_time', LaunchConfiguration('use_sim_time'))])

    corti = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
        [get_package_share_directory('corti'), 'launch', 'corti.launch.py'])]),
        condition=IfCondition(LaunchConfiguration('corti')),
        launch_arguments=[('use_sim_time', LaunchConfiguration('use_sim_time'))])

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
        [get_package_share_directory(
        'rdd2_nav2'), 'launch', 'slam.launch.py'])]),
        condition=LaunchConfigurationEquals('localization', 'slam'),
        launch_arguments=[('use_sim_time', LaunchConfiguration('use_sim_time')),
            ('sync', LaunchConfiguration('sync'))])

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
        [get_package_share_directory(
        'rdd2_nav2'), 'launch', 'localization.launch.py'])]),
        condition=LaunchConfigurationEquals('localization', 'localization'),
        launch_arguments=[('use_sim_time', LaunchConfiguration('use_sim_time')),
            ('map', PathJoinSubstitution([get_package_share_directory(
                'rdd2_nav2'), 'maps', LaunchConfiguration('map_yaml')]))])

    odom_to_tf = Node(
        package='corti',
        executable='odom_to_tf',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            }],
        remappings=[
            ('/odom', '/cerebri/out/odometry')
            ])

    static_map_to_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        condition=LaunchConfigurationEquals('localization', 'off'),
        output='screen',
        arguments=['--child-frame-id', 'odom', '--frame-id', 'map'])

    electrode = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
            [get_package_share_directory('electrode'), 'launch', 'electrode.launch.py'])]),
        condition=IfCondition(LaunchConfiguration('electrode')),
        launch_arguments=[('rviz2', 'true'),
                          ('controller', LaunchConfiguration('controller')),
                          ('foxglove', 'false'),
                          ('vehicle', 'rdd2'),
                          ('sim', LaunchConfiguration('use_sim_time')),
                          ('joy', 'true'),
                        ]
    )


    # Define LaunchDescription variable
    return LaunchDescription(ARGUMENTS + [
        robot_description,
        synapse_ros,
        synapse_gz,
        gz_sim,
        cerebri,
        clock_bridge,
        odom_bridge,
        camera_bridge,
        camera_info_bridge,
        lidar_bridge,
        spawn_robot,
        nav2,
        corti,
        slam,
        localization,
        odom_to_tf,
        static_map_to_odom,
        electrode
    ])
