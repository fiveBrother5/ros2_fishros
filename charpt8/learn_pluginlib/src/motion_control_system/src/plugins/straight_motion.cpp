#include <string>

#include "motion_control_system/motion_control_interface.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace motion_control_system
{

class StraightMotion : public MotionControlInterface
{
public:
  void configure(double linear_speed, double) override
  {
    linear_speed_ = linear_speed;
  }

  geometry_msgs::msg::Twist command() const override
  {
    geometry_msgs::msg::Twist command;
    command.linear.x = linear_speed_;
    return command;
  }

  std::string name() const override
  {
    return "straight motion";
  }

private:
  double linear_speed_{0.0};
};

}  // namespace motion_control_system

PLUGINLIB_EXPORT_CLASS(
  motion_control_system::StraightMotion,
  motion_control_system::MotionControlInterface)
