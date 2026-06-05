import rclpy
from rclpy.node import Node
import requests
from example_interfaces.msg import String
from queue import Queue


class NovelPubNode(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.get_logger().info(f'{node_name} 已经启动')
        self.novel_queue_ = Queue()
        self.novel_publisher_ = self.create_publisher(String, 'novel', 10)
        self.create_timer(5, self.time_call_back)

    def time_call_back(self):
        if self.novel_queue_.qsize() > 0:
            text = self.novel_queue_.get()
            msg = String()
            msg.data = text
            self.novel_publisher_.publish(msg)
            self.get_logger().info(f'发布了,内容是{text}')
        
    
    def download(self, url):
        response = requests.get(url)
        response.encoding = 'utf-8'
        text = response.text
        for line in text.splitlines():
            self.novel_queue_.put(line)

        self.get_logger().info(f'下载{url}, 开始了,内容长度是：{len(text)}')

def main():
    rclpy.init()
    node = NovelPubNode('novel_pub')
    node.download('http://0.0.0.0:8000/novel1.txt')
    rclpy.spin(node)
    rclpy.shutdown()

