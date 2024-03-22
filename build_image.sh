#!/bin/bash

# Path to the Dockerfile directory
DOCKERFILE_PATH="$(dirname "$0")"

# Image name
IMAGE_NAME="keepaway"

# Build the Docker image
docker build -t "$IMAGE_NAME" "$DOCKERFILE_PATH"

