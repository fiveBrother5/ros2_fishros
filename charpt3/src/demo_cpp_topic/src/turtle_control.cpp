#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include <chrono>

using namespace std::chrono_literals;


class TurtlrControlNode: public rclcpp::Node
{
private:
    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr publisher_;

public:
    explicit TurtlrControlNode(const std::string& node_name):Node(node_name)
    {
        publisher_ = this->create_publisher<geometry_msgs::msg::Twist>("/turtle1/cmd_vel", 10);
        timer_ = this->create_wall_timer(1000ms, std::bind(&TurtlrControlNode::timer_callback, this));
    }
    void timer_callback()
    {
        auto msg = geometry_msgs::msg::Twist();
        msg.linear.x = 2.0;
        msg.angular.z = 0.8;
        std::cout<< "测试下"<<std::endl;
        publisher_ -> publish(msg);
    }

};


int main(int argc, char* argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<TurtlrControlNode>("turtle_control");
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}