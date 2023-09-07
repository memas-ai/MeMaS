#!/bin/bash
# Init script for MeMaS. Sleeps for x seconds to wait for service initialization

# Check if an argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <number-of-secs-to-sleep>"
    exit 1
fi

num=$1
version="2023-09-06"

# Check if the entered value is a valid number
if ! [[ "$num" =~ ^[0-9]+$ ]]; then
    echo "Please enter a valid number."
    exit 1
fi

# TODO: introduce actual way of waiting for the dependencies reliably, instead of sleeping. (Note even after the current health checks path, scylla is still not ready)
echo "sleeping $num"
sleep $num


if [ ! -e /memas/first-init.lock ]
then
    # If initialization succeeded, create the lock file, and write our current version to it
    # FIXME: is running flask instead of gunicorn a security concern? Gunicorn keeps on trying to restart the worker thread despite we're intentionally exiting
    flask --app "memas.app:create_app(config_filename=\"$conf_file\", first_init=True)" run && touch /memas/first-init.lock; echo $version > /memas/first-init.lock
fi
