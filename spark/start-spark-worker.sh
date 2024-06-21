#!/bin/bash

# Start SSH service
service ssh start

# Start Spark Worker
$SPARK_HOME/sbin/start-worker.sh

# Keep the container running
tail -f /dev/null
