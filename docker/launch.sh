#!/bin/bash
set -e

IMAGE_NAME="easynav_playground:summit_jazzy"
CONTAINER_NAME="playground_summits"

# Allows the Docker the access to the graphic server X11
xhost +local:docker

docker run -it --rm \
    --net=host \
    -e DISPLAY=$DISPLAY \
    --device /dev/dri \
    --name "$CONTAINER_NAME" \
    "$IMAGE_NAME"


# Revoke access to the graphical server
xhost -local:docker