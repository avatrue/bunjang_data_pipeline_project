#!/bin/bash

# Start SSH service
service ssh start

# Start Secondary Namenode
hdfs --daemon start secondarynamenode
tail -f $HADOOP_HOME/logs/*.log

# Keep the container running
tail -f /dev/null
