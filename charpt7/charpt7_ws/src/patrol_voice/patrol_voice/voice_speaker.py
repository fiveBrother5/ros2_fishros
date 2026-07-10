#!/usr/bin/env python3

import shutil
import subprocess

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class VoiceSpeaker(Node):
    def __init__(self):
        super().__init__('patrol_voice_speaker')

        self.declare_parameter('topic', '/patrol_voice/text')
        self.declare_parameter('engine', 'espeak-ng')
        self.declare_parameter('voice', 'zh')
        self.declare_parameter('speed', 150)
        self.declare_parameter('volume', 100)
        self.declare_parameter('log_only', False)

        self.topic = self.get_parameter('topic').value
        self.engine = self.get_parameter('engine').value
        self.voice = self.get_parameter('voice').value
        self.speed = int(self.get_parameter('speed').value)
        self.volume = int(self.get_parameter('volume').value)
        self.log_only = bool(self.get_parameter('log_only').value)

        self.subscription = self.create_subscription(
            String,
            self.topic,
            self.speak_callback,
            10,
        )

        if not self.log_only and shutil.which(self.engine) is None:
            self.get_logger().warn(
                f'找不到语音命令 {self.engine}，将只打印播报文本。'
            )
            self.log_only = True

        self.get_logger().info(f'语音播报节点已启动，订阅话题: {self.topic}')

    def speak_callback(self, msg):
        text = msg.data.strip()
        if not text:
            return

        self.get_logger().info(f'语音播报: {text}')
        if self.log_only:
            return

        command = [
            self.engine,
            '-v',
            self.voice,
            '-s',
            str(self.speed),
            '-a',
            str(self.volume),
            text,
        ]

        try:
            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            self.get_logger().error(f'语音播报启动失败: {exc}')


def main(args=None):
    rclpy.init(args=args)
    node = VoiceSpeaker()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
