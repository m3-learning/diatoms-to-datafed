#!/bin/env bash

# Set permissions for shared-data
mkdir -p /shared-data
chmod -R 777 /shared-data

# Create the log file directory
mkdir -p $(dirname "$FILE_PATH/backup_log.json")
touch "$FILE_PATH/backup_log.json"
chmod 666 "$FILE_PATH/backup_log.json"


if [ "$START_GLOBUS" = "true" ]; then
    echo "Starting Globus Connect Personal"
    su gridftp -c "cd /home/gridftp && source ./globus-connect-personal.sh"
else
    su gridftp -c "cd /home/gridftp && source ./initialization.sh"

fi

echo setup complete

# Keep the terminal open
tail -f /dev/null