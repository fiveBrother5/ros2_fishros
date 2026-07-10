cmake_minimum_required(VERSION 3.8)
project(motion_control_system)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rcl_interfaces REQUIRED)

add_library(motion_plugins SHARED
  src/plugins/circle_motion.cpp
  src/plugins/spin_motion.cpp
  src/plugins/straight_motion.cpp
)
target_include_directories(motion_plugins PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
ament_target_dependencies(motion_plugins
  geometry_msgs
  pluginlib
)

pluginlib_export_plugin_description_file(
  motion_control_system
  motion_plugins.xml
)

add_executable(motion_controller
  src/motion_controller.cpp
)
target_include_directories(motion_controller PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
ament_target_dependencies(motion_controller
  geometry_msgs
  pluginlib
  rclcpp
  rcl_interfaces
)

install(
  TARGETS motion_plugins motion_controller
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY include/
  DESTINATION include
)

install(
  DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_export_include_directories(include)
ament_export_dependencies(geometry_msgs pluginlib)

ament_package()
