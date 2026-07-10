#ifndef MOTION_CONTROL_SYSTEM__MOTION_CONTROL_INTERFACE_HPP_
#define MOTION_CONTROL_SYSTEM__MOTION_CONTROL_INTERFACE_HPP_

#include <string>

#include "geometry_msgs/msg/twist.hpp"

namespace motion_control_system
{

class MotionControlInterface
{
public:
  virtual ~MotionControlInterface() = default;

  virtual void configure(double linear_speed, double angular_speed) = 0;

  virtual geometry_msgs::msg::Twist command() const = 0;

  virtual std::string name() const = 0;
};

}  // namespace motion_control_system

#endif  // MOTION_CONTROL_SYSTEM__MOTION_CONTROL_INTERFACE_HPP_
