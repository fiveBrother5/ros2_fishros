#include <string>

#include "motion_control_system/motion_control_interface.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace motion_control_system
{

class SpinMotion : public MotionControlInterface
{
public:
  void configure(double, double angular_speed) override
  {
    angular_speed_ = angular_speed;
  }

  geometry_msgs::msg::Twist command() const override
  {
    geometry_msgs::msg::Twist command;
    command.angular.z = angular_speed_;
    return command;
  }

  std::string name() const override
  {
    return "spin motion";
  }

private:
  double angular_speed_{0.0};
};

}  // namespace motion_control_system

PLUGINLIB_EXPORT_CLASS(
  motion_control_system::SpinMotion,
  motion_control_system::MotionControlInterface)
