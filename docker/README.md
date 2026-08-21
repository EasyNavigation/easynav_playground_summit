# EasyNav ROS 2 Jazzy - Docker

This repository contains the 'Dockerfile' to use SummitXL playground, the image builds a ROS2 Jazzy environment and the EasyNav workspace ready to use. Also contains a launcher for a easy use of the docker.

## Instalation

```bash
sudo docker build -t easynav_playground:summit_jazzy .
```

## Usage

### Option A: using the script `run_docker.sh`
 
The first time Grant execute permissions to the script:
```bash
chmod +x run_docker.sh
```
 
Execute: 
```bash
./run_docker.sh
```
 
This script:

- Temporarily allows the Docker the access to the graphic server  (`xhost +local:docker`).
- Launch the docker allowing to see the Gazebo and RVIZ windows.
- When exiting Docker, revoke access to the graphical server.

### Option B: in our terminal
 
```bash
xhost +local:docker
 
docker run -it --rm \
  --net=host \
  -e DISPLAY=$DISPLAY \
  --device /dev/dri \
  --name playground_summit \
  easynav_playground:summit_jazzy
 
xhost -local:docker
```
