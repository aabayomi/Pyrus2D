#!/bin/bash

# Your Docker image name
IMAGE_NAME="keepaway"

# Container name
CONTAINER_NAME="keepaway-test"

# Allow connections from localhost (for XQuartz)
xhost + 127.0.0.1

# Run the Docker container
docker run -d --name "$CONTAINER_NAME" \
    -e DISPLAY=host.docker.internal:0 \
    "$IMAGE_NAME"

