import espeakng
import threading
import rclpy
from rclpy.node import Node
from example_interfaces.msg import String
from queue import Queue
import time

class NovelSubNode(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.get_logger().info(f'{node_name} , 启动')
        self.novel_sub_queue = Queue()
        self.novel_sub_ = self.create_subscription(String, 'novel', self.call_back, 10)
        self.speak_thred_ = threading.Thread(target=self.speak_thread)
        self.speak_thred_.start()

    def call_back(self, msg):
        self.novel_sub_queue.put(msg.data)

    def speak_thread(self):
        speaker = espeakng.Speaker()
        speaker.voice = 'zh'
        while rclpy.ok():
            if self.novel_sub_queue.qsize() > 0:
                text = self.novel_sub_queue.get()
                self.get_logger().info(f'朗读的文字：{text}')
                speaker.say(text)
                speaker.wait()
            else:
                time.sleep(1)


def main():
    rclpy.init()
    node = NovelSubNode('nodvel_sub')
    rclpy.spin(node)
    rclpy.shutdown()