#!/bin/sh

set -e

service mysql restart


# We need this sleep, otherwise the script won't be executed and container will be in a loop

while true; do
  sleep 1000
done
