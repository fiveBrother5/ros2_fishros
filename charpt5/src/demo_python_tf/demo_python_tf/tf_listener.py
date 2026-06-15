import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from tf2_ros import TransformListener, Buffer
from tf_transformations import euler_from_quaternion
from rclpy.time import Time

class TFBroadcaster(Node):
    def __init__(self):
        super().__init__('dynamic_tf_broadcaster')
        self.buffer_ = Buffer()
        self.broadcaster_ = TransformListener(self.buffer_, self)
        self.timer_ = self.create_timer(1, self.get_transform)

    def get_transform(self):
        try:
            result = self.buffer_.lookup_transform('base_link', 'bottle_link',
                                                   Time(seconds=0.0), rclpy.time.Duration(seconds=1.0))
            transform = result.transform
            self.get_logger().info(f'平移：{transform.translation}')
            self.get_logger().info(f'旋转：{transform.rotation}')
            rotation_euler = euler_from_quaternion([
                transform.rotation.x,
                transform.rotation.y,
                transform.rotation.z,
                transform.rotation.w
            ])
            self.get_logger().info(f'旋转RPY:{rotation_euler}')

        except Exception as e:
            self.get_logger().error(f'获取坐标转换c错误 {str(e)}')
            

def main():
    rclpy.init()
    node = TFBroadcaster()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
