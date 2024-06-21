#!/bin/bash

# Start SSH service
service ssh start

# Start DataNode
hdfs --daemon start datanode
tail -f $HADOOP_HOME/logs/*.log

# Keep the container running
tail -f /dev/null
