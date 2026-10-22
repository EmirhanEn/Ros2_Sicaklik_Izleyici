
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class SicaklikIzleyici(Node):
    def __init__(self):
        super().__init__('sicaklik_izleyici')

        self.declare_parameter('esik_degeri', 30.0)

        self.subscription = self.create_subscription(
            Float32,
            '/sicaklik',
            self.sicaklik_kontrol,
            10
        )

        self.get_logger().info('Sicaklik izleyici baslatildi.')

    def sicaklik_kontrol(self, mesaj):
        sicaklik = mesaj.data

        esik = self.get_parameter(
            'esik_degeri'
        ).value

        self.get_logger().info(
            f'Olculen sicaklik: {sicaklik:.2f} C'
        )

        if sicaklik > esik:
            self.get_logger().warn(
                f'UYARI! Sicaklik yuksek: '
                f'{sicaklik:.2f} C (Esik: {esik} C)'
            )


def main(args=None):
    rclpy.init(args=args)
    node = SicaklikIzleyici()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
