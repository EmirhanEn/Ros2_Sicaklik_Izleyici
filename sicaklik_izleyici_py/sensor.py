
import random

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class SicaklikSensoru(Node):
    def __init__(self):
        super().__init__('sicaklik_sensoru')

        self.publisher = self.create_publisher(
            Float32, '/sicaklik', 10
        )

        self.timer = self.create_timer(
            1.0, self.sicaklik_yayinla
        )

        self.get_logger().info('Sicaklik sensoru baslatildi.')

    def sicaklik_yayinla(self):
        mesaj = Float32()
        mesaj.data = float(random.uniform(20.0, 40.0))

        self.publisher.publish(mesaj)

        self.get_logger().info(
            f'Yayinlanan sicaklik: {mesaj.data:.2f} C'
        )


def main(args=None):
    rclpy.init(args=args)
    node = SicaklikSensoru()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
