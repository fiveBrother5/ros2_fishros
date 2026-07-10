#include <string>

#include "motion_control_system/motion_control_interface.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace motion_control_system
{

class CircleMotion : public MotionControlInterface
{
public:
  void configure(double linear_speed, double angular_speed) override
  {
    linear_speed_ = linear_speed;
    angular_speed_ = angular_speed;
  }

  geometry_msgs::msg::Twist command() const override
  {
    geometry_msgs::msg::Twist command;
    command.linear.x = linear_speed_;
    command.angular.z = angular_speed_;
    return command;
  }

  std::string name() const override
  {
    return "circle motion";
  }

private:
  double linear_speed_{0.0};
  double angular_speed_{0.0};
};

}  // namespace motion_control_system

PLUGINLIB_EXPORT_CLASS(
  motion_control_system::CircleMotion,
  motion_control_system::MotionControlInterface)
