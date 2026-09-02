#!/bin/bash
set -e

IMAGE_NAME="easynav_playground:summit_rolling"
CONTAINER_NAME="playground_summits"
ROS_DOMAIN_ID="0"

# Allows the Docker the access to the graphic server X11
xhost +local:docker

docker run -it --rm \
    --net=host \
    -e DISPLAY=$DISPLAY \
    --device /dev/dri \
    --name "$CONTAINER_NAME" \
    --gpus all \
    -e ROS_DOMAIN_ID=$ROS_DOMAIN_ID \
    "$IMAGE_NAME"


# Revoke access to the graphical server
xhost -local:docker