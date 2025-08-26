#!/bin/bash

# # Assign input arguments to variables
# DataPath=$1
# ConfigPath=$2

echo "=== Debugging Information ==="
echo "Current directory: $(pwd)"
echo "Current user: $(whoami)"
echo "Globus Connect Personal directory: $(find . -maxdepth 1 -type d -name "globusconnectpersonal-*" -print -quit)"

# Check if the binary exists and is executable
gcp_dir=$(find . -maxdepth 1 -type d -name "globusconnectpersonal-*" -print -quit)
if [ -n "$gcp_dir" ]; then
    echo "Found directory: $gcp_dir"
    echo "Binary exists: $(ls -la "$gcp_dir/globusconnectpersonal")"
    echo "Binary type: $(file "$gcp_dir/globusconnectpersonal")"
    echo "Binary permissions: $(stat -c "%a %n" "$gcp_dir/globusconnectpersonal")"
else
    echo "Error: globusconnectpersonal directory not found"
    exit 1
fi

echo "=== Starting Globus Setup ==="

# Inside the container: Setup the Globus Personal Endpoint
globus login --no-local-server

# Collect information about the endpoint
endpoint_info=$(globus endpoint create --personal myep 2>&1)

# Extract the Endpoint ID and Setup Key from the output
endpoint_id=$(echo "$endpoint_info" | grep -oP "Endpoint ID: \K[0-9a-f-]+")
setup_key=$(echo "$endpoint_info" | grep -oP "Setup Key: \K[0-9a-f-]+")

# Set the environment variables
export GLOBUS_ENDPOINT_ID="$endpoint_id"
export GLOBUS_SETUP_KEY="$setup_key"

# Change to the Globus Connect Personal directory
cd "$gcp_dir"

echo "=== Setting up endpoint ==="
echo "Setup Key: $setup_key"
echo "Current directory: $(pwd)"
echo "Binary path: $(pwd)/globusconnectpersonal"

# Finish the Endpoint Setup
./globusconnectpersonal -setup "$GLOBUS_SETUP_KEY"
echo "Finished the Endpoint Setup $GLOBUS_SETUP_KEY"

# Copy the Globus configuration to the host directory
cp -p -r /home/gridftp/.globus* /home/gridftp/globus_config

echo "=== Starting Globus Connect Personal ==="
./globusconnectpersonal -start &
echo "/home/gridftp/data,0,1" >> ~/.globusonline/lta/config-paths

# Copy the Globus configuration to the host directory
cp -p -r /home/gridftp/.globus* /home/gridftp/globus_config

echo "=== Setup Complete ==="