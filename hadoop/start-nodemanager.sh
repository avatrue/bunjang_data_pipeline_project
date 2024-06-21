#!/bin/bash

# Start SSH service
service ssh start

# Start NodeManager
yarn --daemon start nodemanager
tail -f $HADOOP_HOME/logs/*.log

# Keep the container running
tail -f /dev/null
