#!/bin/bash
# Activate the Conda environment
source activate keepaway
# Execute the command passed to the Docker container
exec "$@"
