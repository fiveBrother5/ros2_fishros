#include "motion_control_system/motion_controller.hpp"

#include <chrono>
#include <cmath>
#include <functional>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>

namespace motion_control_system
{

MotionController::MotionController()
: Node("motion_controller"),
  plugin_loader_(
    "motion_control_system",
    "motion_control_system::MotionControlInterface")
{
  plugin_name_ = declare_parameter<std::string>(
    "plugin_name", "motion_control_system/StraightMotion");
  linear_speed_ = declare_parameter<double>("linear_speed", 0.2);
  angular_speed_ = declare_parameter<double>("angular_speed", 0.5);
  const double publish_rate = declare_parameter<double>("publish_rate", 10.0);

  if (!std::isfinite(publish_rate) || publish_rate <= 0.0) {
    throw std::invalid_argument("publish_rate must be greater than zero");
  }

  command_publisher_ = create_publisher<geometry_msgs::msg::Twist>("cmd_vel", 10);

  std::string error_message;
  if (!load_plugin(plugin_name_, linear_speed_, angular_speed_, error_message)) {
    throw std::runtime_error(error_message);
  }

  parameter_callback_handle_ = add_on_set_parameters_callback(
    std::bind(&MotionController::on_parameters_changed, this, std::placeholders::_1));

  const auto period = std::chrono::duration<double>(1.0 / publish_rate);
  timer_ = create_wall_timer(
    std::chrono::duration_cast<std::chrono::nanoseconds>(period),
    std::bind(&MotionController::publish_command, this));

  const auto declared_plugins = plugin_loader_.getDeclaredClasses();
  RCLCPP_INFO(get_logger(), "Available motion plugins:");
  for (const auto & declared_plugin : declared_plugins) {
    RCLCPP_INFO(get_logger(), "  - %s", declared_plugin.c_str());
  }
}

bool MotionController::load_plugin(
  const std::string & plugin_name,
  double linear_speed,
  double angular_speed,
  std::string & error_message)
{
  try {
    auto plugin = plugin_loader_.createSharedInstance(plugin_name);
    plugin->configure(linear_speed, angular_speed);

    std::lock_guard<std::mutex> lock(plugin_mutex_);
    active_plugin_ = std::move(plugin);
    plugin_name_ = plugin_name;
    linear_speed_ = linear_speed;
    angular_speed_ = angular_speed;

    RCLCPP_INFO(
      get_logger(),
      "Loaded plugin '%s' (%s), linear_speed=%.3f, angular_speed=%.3f",
      plugin_name_.c_str(),
      active_plugin_->name().c_str(),
      linear_speed_,
      angular_speed_);
    return true;
  } catch (const pluginlib::PluginlibException & exception) {
    error_message =
      "Failed to load motion plugin '" + plugin_name + "': " + exception.what();
    RCLCPP_ERROR(get_logger(), "%s", error_message.c_str());
    return false;
  }
}

rcl_interfaces::msg::SetParametersResult MotionController::on_parameters_changed(
  const std::vector<rclcpp::Parameter> & parameters)
{
  auto next_plugin_name = plugin_name_;
  auto next_linear_speed = linear_speed_;
  auto next_angular_speed = angular_speed_;

  for (const auto & parameter : parameters) {
    if (parameter.get_name() == "plugin_name") {
      next_plugin_name = parameter.as_string();
    } else if (parameter.get_name() == "linear_speed") {
      next_linear_speed = parameter.as_double();
    } else if (parameter.get_name() == "angular_speed") {
      next_angular_speed = parameter.as_double();
    } else if (parameter.get_name() == "publish_rate") {
      rcl_interfaces::msg::SetParametersResult result;
      result.successful = false;
      result.reason = "publish_rate can only be changed when the node starts";
      return result;
    }
  }

  rcl_interfaces::msg::SetParametersResult result;
  if (next_plugin_name.empty()) {
    result.successful = false;
    result.reason = "plugin_name cannot be empty";
    return result;
  }

  if (!std::isfinite(next_linear_speed) || !std::isfinite(next_angular_speed)) {
    result.successful = false;
    result.reason = "motion speeds must be finite numbers";
    return result;
  }

  std::string error_message;
  result.successful = load_plugin(
    next_plugin_name, next_linear_speed, next_angular_speed, error_message);
  result.reason = result.successful ? "motion plugin updated" : error_message;
  return result;
}

void MotionController::publish_command()
{
  geometry_msgs::msg::Twist command;
  {
    std::lock_guard<std::mutex> lock(plugin_mutex_);
    if (!active_plugin_) {
      RCLCPP_WARN_THROTTLE(
        get_logger(), *get_clock(), 2000, "No active motion plugin");
      return;
    }
    command = active_plugin_->command();
  }

  command_publisher_->publish(command);
}

}  // namespace motion_control_system

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  try {
    rclcpp::spin(std::make_shared<motion_control_system::MotionController>());
  } catch (const std::exception & exception) {
    RCLCPP_FATAL(
      rclcpp::get_logger("motion_controller"),
      "Motion controller terminated: %s",
      exception.what());
    rclcpp::shutdown();
    return 1;
  }

  rclcpp::shutdown();
  return 0;
}
