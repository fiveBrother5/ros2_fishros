# motion_control_system

这是一个 ROS 2 `pluginlib` 学习示例。运动控制器只依赖统一接口，
具体速度指令由运行时加载的运动插件生成。

## 插件

- `motion_control_system/StraightMotion`：直行，只设置 `linear.x`
- `motion_control_system/SpinMotion`：原地旋转，只设置 `angular.z`
- `motion_control_system/CircleMotion`：圆周运动，同时设置 `linear.x` 和 `angular.z`

## 编译

```bash
cd ~/ros_fish_dev/src/ros2_fishros/charpt8/learn_pluginlib
source /opt/ros/humble/setup.bash
colcon build --packages-select motion_control_system
source install/setup.bash
```

## 运行

启动默认的直行插件：

```bash
ros2 launch motion_control_system motion_control_demo.launch.py
```

启动指定插件：

```bash
ros2 launch motion_control_system motion_control_demo.launch.py \
  plugin_name:=motion_control_system/CircleMotion \
  linear_speed:=0.3 angular_speed:=0.6
```

查看控制器发布的速度：

```bash
ros2 topic echo /cmd_vel
```

## 运行时切换插件

控制器运行期间可以直接修改参数，无需重启节点：

```bash
ros2 param set /motion_controller plugin_name motion_control_system/SpinMotion
ros2 param set /motion_controller angular_speed 1.0
ros2 param set /motion_controller plugin_name motion_control_system/CircleMotion
```

插件切换失败时，参数修改会被拒绝，控制器继续使用上一个有效插件。
