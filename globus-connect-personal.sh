#!/bin/env bash

# Summary: This shell script will check for a Globus Connect Personal (GCP) 
# endpoint & start it if it exists, otherwise it will sleep for an hour giving 
# the user time to login and configure the GCP endpoint.

# Note: This script assumes that the user follows the directions in the README.

# Author: Kyle Krick <kkrick@sdsu.edu>

###  Variables  ###

echo "Running Globus Connect Personal script"

# GCP config is stored in the .globusonline directory
gcpconfigdir=".globusonline"
# GCP installation directory, version, and path may change so find dynamically
gcpdir=$(find . -maxdepth 1 -type d -name "globusconnectpersonal-*" -print -quit)

###  Script Start  ###
cd /home/gridftp || exit 1

# Check to make sure globusconnectpersonal exists
if [ ! -d "$gcpdir" ]; then
    echo "Globus Connect Personal directory not found."
    exit 1
fi

check_login(){
  # Run the globus whoami command and capture the output and exit status
    output=$(globus whoami 2>&1)
    status=$?

    # Check if the command failed with a MissingLoginError
    if [[ $status -ne 0 && "$output" == *"MissingLoginError"* ]]; then
        return 0
    else
        return 1
    fi
}


# Function to start Globus Connect Personal and wait until it is running
start_globus() {
    # Start Globus Connect Personal in the background
    nohup "./$gcpdir/globusconnectpersonal" -start &

    # Wait until the service is running
    while check_login; do
        echo "Waiting for Globus Connect Personal to start..."
        sleep 1
    done

    output=$(globus whoami 2>&1)
    echo "$output"
    echo "$output" > /shared-data/globus-whoami.txt

    echo "Globus Connect Personal is now running."
}

# Check /home/gridftp for existing GCP config
if [ -d "$gcpconfigdir" ]; then
    # GCP endpoint config exists, start the endpoint
    start_globus
else
    # Check /data/globus-save for GCP endpoint config
    if [ -d "/home/gridftp/globus_config/$gcpconfigdir" ]; then
        # Copy existing config and then start GCP endpoint
        cp -p -r /home/gridftp/globus_config/.glob* ~
        start_globus
    else
        # Can't find GCP config, sleep for an hour to let user set up config
        echo "GCP config not found. Sleeping for an hour to allow user setup..."
        sleep 3600
    fi
fi
# Extract the Endpoint ID from the output
GLOBUS_ENDPOINT_ID=$(globus endpoint local-id 2>&1)

echo "$GLOBUS_ENDPOINT_ID" > /shared-data/globus-endpoint_id.txt

# Output the Endpoint ID
echo "Endpoint ID: $GLOBUS_ENDPOINT_ID"

