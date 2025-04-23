# EasyNav Playground Summit

## Installation
```bash
cd <easynav-workspace>/src/
vcs import . < easynav_playground_summit/thirdparty.repos
cd ..
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install 
```

## Usage
```bash
ros2 launch easynav_playground_summit playground_summit.launch.py
```

or

```bash
ros2 launch easynav_playground_summit playground_summit.launch.py world:=<path-to-world>
```
