#!/bin/bash

# Define the folder name
FOLDER="data"

# Check if the folder exists
if [ ! -d "$FOLDER" ]; then
  echo "Folder '$FOLDER' not found. Creating it now..."
  mkdir "$FOLDER"
  echo "Folder '$FOLDER' has been created."
fi

# Set the image name and container name
IMAGE_NAME="llm-tool_image"
CONTAINER_NAME="llm-tool_container"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # Directory of this script

# Check if Docker or Podman is installed
if command -v podman &> /dev/null; then
    CONTAINER_TOOL="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_TOOL="docker"
else
    echo "Neither Docker nor Podman is installed. Please install one of them."
    exit 1
fi

# Check if the image exists
if ! $CONTAINER_TOOL image inspect "$IMAGE_NAME" &> /dev/null; then
    echo "Image '$IMAGE_NAME' not found. Running rebuild.sh..."
    ./rebuild.sh
    if [ $? -ne 0 ]; then
        echo "Failed to rebuild the image. Exiting."
        exit 1
    fi
else
    echo "Image '$IMAGE_NAME' exists. No need to rebuild."
fi

# Check if the user provided the script to run
if [ -z "$1" ]; then
    echo "Please provide the script to run as the first argument. For example clustering.py"
    exit 1
fi

# Set the script and shift the arguments
SCRIPT_TO_RUN="$1"
if [[ "$SCRIPT_TO_RUN" != *.py ]]; then
    SCRIPT_TO_RUN="${SCRIPT_TO_RUN}.py"
fi
shift  # Shift removes the first argument, so $@ now contains only additional parameters

# Run the container with the specified script and any additional parameters
$CONTAINER_TOOL run --rm -it \
    --name $CONTAINER_NAME \
    -v "$SCRIPT_DIR/data:/app/data" \
    "$IMAGE_NAME" python "$SCRIPT_TO_RUN" "$@"
