#!/bin/bash

# Start SSH service
service ssh start

# Start HBase RegionServer
$HBASE_HOME/bin/hbase-daemon.sh start regionserver

# Keep the container running
tail -f /dev/null
