from launch import LaunchDescription
from launch.actions import ExecuteProcess, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Generate URDF from XACRO
    robot_description = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare("prac_robot_description"), "urdf", "prac_robot.urdf.xacro"]
            ),
        ]
    )

    return LaunchDescription([
        # Robot State Publisher
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            output="screen",
            parameters=[{"robot_description": robot_description}],
        ),

        # Gazebo (Harmonic)
        ExecuteProcess(
            cmd=["gz", "sim", "-v", "4", "-r", "empty.sdf"],
            output="screen",
        ),

        # Spawn Robot in Gazebo
        Node(
            package="ros_gz_sim",
            executable="create",
            arguments=[
                "-topic", "/robot_description",
                "-name", "prac_robot_description",
                "-z", "0.1",
            ],
            output="screen",
        ),

        # Load Controllers (Delayed until after spawn)
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=Node(
                    package="controller_manager",
                    executable="ros2_control_node",
                    parameters=[
                        {"robot_description": robot_description},
                        PathJoinSubstitution(
                            [FindPackageShare("prac_robot_description"), "config", "wheel_controllers.yaml"]
                        ),
                    ],
                ),
                on_exit=[
                    Node(
                        package="controller_manager",
                        executable="spawner",
                        arguments=["joint_state_broadcaster"],
                    ),
                    Node(
                        package="controller_manager",
                        executable="spawner",
                        arguments=["wheel_controller"],  # From your YAML
                    ),
                ],
            )
        ),
    ])