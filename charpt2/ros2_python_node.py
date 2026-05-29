import rclpy
from rclpy.node import Node

def main():
    rclpy.init()
    node = Node("python_node")
    node.get_logger().info('你好，第一个节点')
    rclpy.spin(node)
    rclpy.shutdown()

if __name__=="__main__":
    main()


# 可以设置环境变量 修改打印的日志格式
# export RCUTILS_CONSOLE_OUTPUT_FORMART=[{function_name}:{line_number}]:{message}