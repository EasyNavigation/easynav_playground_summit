<!--
Copyright 2026 Intelligent Robotics Lab
SPDX-License-Identifier: Apache-2.0
-->

# EasyNav Summit Playground

Gazebo Harmonic simulation of a Robotnik Summit XL in the URJC excavation, an outdoor 3D terrain, integrated with EasyNav and NavMap. The package is self-contained: the robot model, the world, the maps and the EasyNav configurations are all included, so you only need this package plus EasyNav (core and plugins) and NavMap.

## Build

From the ROS 2 workspace root:

```bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-up-to easynav_playground_summit
source install/setup.bash
```

## Launch EasyNav

Each `easynav_<config>.launch.yaml` starts Gazebo, the Summit XL, EasyNav with that configuration and RViz2:

```bash
ros2 launch easynav_playground_summit easynav_bonxai_amcl.launch.yaml
```

Once RViz2 is up, send a goal with the **2D Goal Pose** tool.

### NavMap configurations

All of them plan with A* over the NavMap (`maps/excavation_urjc.navmap`).

| Launch file | Controller | Localizer | Notes |
| --- | --- | --- | --- |
| `easynav_bonxai_amcl.launch.yaml` | Regulated Pure Pursuit | NavMap AMCL | AMCL corrects against the Bonxai 3D map (`maps/excavation_urjc.pcd`) |
| `easynav_mppi.launch.yaml` | MPPI | NavMap AMCL | |
| `easynav_mpc.launch.yaml` | MPC | NavMap AMCL | |
| `easynav_gps.launch.yaml` | Regulated Pure Pursuit | GPS (UKF) | `FusionLocalizer` fusing the GPS position, wheel odometry and IMU heading; no Bonxai map |
| `easynav_navmap_dummy.launch.yaml` | — | — | Only loads and shows `maps/excavation_urjc_2.navmap` |

### Localization

The terrain is smooth and the Bonxai cloud is sparse, so NavMap AMCL has little to correct against: it keeps the heading from the IMU, but its position can drift 0.5–1 m from the true one. The GPS configuration is the accurate one outdoors (about 0.15 m): its map frame is the Gazebo world's (`latitude_origin`/`longitude_origin` are the world's `spherical_coordinates`).

### Launch arguments

| Argument | Default | Description |
| --- | --- | --- |
| `params_file` | Per launch file | EasyNav parameters file |
| `rviz_config` | Per launch file | RViz2 configuration file |
| `gui` | `true` | Set to `false` to run Gazebo headless |
| `rviz` | `true` | Set to `false` to skip RViz2 |

For example, to run headless with your own parameters:

```bash
ros2 launch easynav_playground_summit easynav_bonxai_amcl.launch.yaml gui:=false params_file:=/path/to/my.params.yaml
```

### Real-time cycles

The configurations run EasyNav's real-time cycle (`use_real_time: true`) at 50 Hz (`system_node.rt_freq`; the default 200 Hz is too tight for this simulation). The recovery system watches it: if many cycles in a row start late, it holds the mission, asks for human assistance and finally cancels it. See "Real-time system setup" in the EasyNav docs.

## Simulation only

To run Gazebo and the Summit XL without EasyNav or RViz2:

```bash
ros2 launch easynav_playground_summit gazebo_sim.launch.yaml
```

To spawn the robot in a running simulation, use `summit.launch.yaml` with a spawn pose (`x`, `y`, `z`).

The simulated Summit XL publishes:

| Topic | Type |
| --- | --- |
| `/front_laser/points` | `sensor_msgs/PointCloud2` (Robosense Helios 16P) |
| `/front_camera/depth/color/points` | `sensor_msgs/PointCloud2` (ZED2) |
| `/imu/data` | `sensor_msgs/Imu` |
| `/gps/fix` | `sensor_msgs/NavSatFix` |
| `/robotnik_base_control/odom` | `nav_msgs/Odometry` |
| `/ground_truth` | `nav_msgs/Odometry` |

It also publishes TF, and listens on `/cmd_vel` (`geometry_msgs/Twist`). `twist_stamper` forwards it to the diff drive controller, which takes `TwistStamped` on `/robotnik_base_control/cmd_vel`.

## Package layout

| Directory | Contents |
| --- | --- |
| `launch/` | Launch files, in YAML |
| `params/` | EasyNav parameters, one file per configuration |
| `maps/` | Maps: `excavation_urjc.navmap`, `excavation_urjc_2.navmap` (NavMap) and `excavation_urjc.pcd` (Bonxai) |
| `rviz/` | RViz2 configurations |
| `config/` | ros2_control controllers and ROS–Gazebo bridge topics |
| `urdf/`, `meshes/` | Summit XL model |
| `worlds/`, `models/` | URJC excavation world |

## Attribution and licensing

This package is licensed under Apache-2.0; see [LICENSE](./LICENSE). It includes third-party assets under their own licenses:

- The Summit XL model (`urdf/`, `meshes/`, `config/`) comes from [robot_description](https://github.com/Summit-Harmonic/robot_description) and [robotnik_sensors](https://github.com/Summit-Harmonic/robotnik_sensors) (`ros2-devel` branch), under the BSD 3-Clause license; see [LICENSE-BSD](./LICENSE-BSD).
- The URJC excavation world (`worlds/`, `models/`) comes from [urjc-excavation-world](https://github.com/juanscelyg/urjc-excavation-world) (`main` branch). Its license file is GPL-3.0; see [models/LICENSE](./models/LICENSE).

Only the files these simulations use were copied. Changes to the robot model, all for the simulation:

- Paths point to this package; the sensors are reduced to the ones the Summit XL carries, and the unused omni-wheel option was dropped.
- Collisions are boxes and cylinders instead of meshes (mesh-vs-terrain contacts overflowed the physics engine), and the wheels have lower sideways friction, so the skid steering turns as commanded (`wheel_separation_multiplier` in `config/summit_controllers.yaml` is calibrated against Gazebo's ground truth).
- The ZED's two RGB cameras are not simulated (nothing uses them); the depth camera runs at quarter resolution and 10 Hz.
- The IMU has noise and its frame id, the GPS runs at 5 Hz, and the odometry has no zero variances: filters need realistic covariances.
