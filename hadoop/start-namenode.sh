#!/bin/bash

# Start SSH service
service ssh start

# Format HDFS (only if not formatted yet)
if [ ! -d /opt/hadoop/hadoopdata/hdfs/namenode/current ]; then
  echo "Y" | $HADOOP_HOME/bin/hdfs namenode -format
fi

# Start Namenode
hdfs --daemon start namenode
tail -f $HADOOP_HOME/logs/*.log

# Keep the container running
tail -f /dev/null
