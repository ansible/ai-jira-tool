 #!/bin/bash

# Define the image name
IMAGE_NAME="ai-jira-tool-image"
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

# Always build the image, even if it exists
echo "Building the image with the name $IMAGE_NAME..."
$CONTAINER_TOOL build -t "$IMAGE_NAME" "$SCRIPT_DIR"

