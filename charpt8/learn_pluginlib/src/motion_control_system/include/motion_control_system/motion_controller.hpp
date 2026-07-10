#ifndef MOTION_CONTROL_SYSTEM__MOTION_CONTROLLER_HPP_
#define MOTION_CONTROL_SYSTEM__MOTION_CONTROLLER_HPP_

#include <memory>
#include <mutex>
#include <string>
#include <vector>

#include "geometry_msgs/msg/twist.hpp"
#include "motion_control_system/motion_control_interface.hpp"
#include "pluginlib/class_loader.hpp"
#include "rcl_interfaces/msg/set_parameters_result.hpp"
#include "rclcpp/rclcpp.hpp"

namespace motion_control_system
{

class MotionController : public rclcpp::Node
{
public:
  MotionController();

private:
  bool load_plugin(
    const std::string & plugin_name,
    double linear_speed,
    double angular_speed,
    std::string & error_message);

  rcl_interfaces::msg::SetParametersResult on_parameters_changed(
    const std::vector<rclcpp::Parameter> & parameters);

  void publish_command();

  pluginlib::ClassLoader<MotionControlInterface> plugin_loader_;
  std::shared_ptr<MotionControlInterface> active_plugin_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr command_publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr parameter_callback_handle_;

  std::mutex plugin_mutex_;
  std::string plugin_name_;
  double linear_speed_;
  double angular_speed_;
};

}  // namespace motion_control_system

#endif  // MOTION_CONTROL_SYSTEM__MOTION_CONTROLLER_HPP_
