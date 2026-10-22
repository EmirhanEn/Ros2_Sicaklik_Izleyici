
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    sensor = Node(
        package='sicaklik_izleyici_py',
        executable='sensor',
        name='sicaklik_sensoru',
        output='screen'
    )

    izleyici = Node(
        package='sicaklik_izleyici_py',
        executable='izleyici',
        name='sicaklik_izleyici',
        output='screen',
        parameters=[{
            'esik_degeri': 30.0
        }]
    )

    arayuz = Node(
        package='sicaklik_izleyici_py',
        executable='arayuz',
        name='sicaklik_arayuzu',
        output='screen'
    )

    return LaunchDescription([
        sensor,
        izleyici,
        arayuz
    ])
