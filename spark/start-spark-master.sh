#!/bin/bash

# Start SSH service
service ssh start

# Start Spark Master
$SPARK_HOME/sbin/start-master.sh

# Keep the container running
tail -f /dev/null
