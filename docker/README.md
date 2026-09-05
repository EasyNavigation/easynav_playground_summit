# EasyNav ROS 2 Jazzy - Docker

This repository contains the 'Dockerfile' to use SummitXL playground, the image builds a ROS2 Jazzy environment and the EasyNav workspace ready to use. Also contains a launcher for a easy use of the docker.

## Instalation

```bash
cd <easynav-playground_kobuki>/docker/

sudo docker build -t easynav_playground:summit_jazzy .
```

## Usage

### Option A: using the script `launch.sh`

The first time Grant execute permissions to the script:
```bash
cd <easynav-playground_kobuki>/docker/

chmod +x launch.sh
```

Execute:
We can launch the docker with different options. --auto or alone and the script will detect the graphic server, --wayland if you have wayland in your computer or --x11.

```bash
cd <easynav-playground_kobuki>/docker/

./launch.sh --auto
```

This script:

- Temporarily allows the Docker the access to the graphic server  (`xhost +local:docker`).
- Launch the docker allowing to see the Gazebo and RVIZ windows.
- When exiting Docker, revoke access to the graphical server.

### Option B: in our terminal

```bash
cd <easynav-playground_kobuki>/docker/

xhost +local:docker
 
docker run -it --rm \
    --net=host \
    -e DISPLAY=$DISPLAY \
    -e NVIDIA_VISIBLE_DEVICES=all \
    -e NVIDIA_DRIVER_CAPABILITIES=all \
    -e QT_X11_NO_MITSHM=1 \
    -e XDG_RUNTIME_DIR=/tmp/runtime-root \
    --device /dev/dri \
    --name playground_summits \
    --gpus all \
    -e ROS_DOMAIN_ID=$ROS_DOMAIN_ID \
    "$IMAGE_NAME"
 
xhost -local:docker
```
### Troubleshooting
In case of using wayland instead of x11 we may need to export the following:
```bash
export __NV_PRIME_RENDER_OFFLOAD=1
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export __VK_LAYER_NV_optimus=NVIDIA_only
```