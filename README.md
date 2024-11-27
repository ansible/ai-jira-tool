# Usage

Requirements: Needs podman or docker.

./run.sh runs python with script name (\*.py not needed) and parameters, for example:

./run.sh clustering -f "data/input.csv"
./run.sh clustering --help prints help for this skript

This will search for file input.csv in ./data folder. Note that anything outside of data folder is invisible for docker container.

If you are running the script directly using python, then file visibility is not the problem.

# Input data

Script requires data in csv format separated by ;
Summary column is required.

# Rebuilding image

if needed, rebuild.sh rebuilds the image

run.sh also builds image, if not found and it will create container with volumes in /data folder.
