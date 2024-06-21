#!/bin/bash

# Start SSH service
service ssh start

# Start JournalNode
hdfs --daemon start journalnode
tail -f $HADOOP_HOME/logs/*.log

# Keep the container running
tail -f /dev/null
