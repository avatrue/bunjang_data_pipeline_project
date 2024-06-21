#!/bin/bash

# Start SSH service
service ssh start

# Start Spark Worker
$SPARK_HOME/sbin/start-slave.sh spark://spark-master:7077

# Keep the container running
tail -f /dev/null
