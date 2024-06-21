#!/bin/bash

# Start SSH service
service ssh start

# Start ResourceManager
yarn --daemon start resourcemanager
tail -f $HADOOP_HOME/logs/*.log

# Keep the container running
tail -f /dev/null
