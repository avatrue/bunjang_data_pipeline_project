#!/bin/bash

# Start SSH service
service ssh start

# Start HBase Master
$HBASE_HOME/bin/start-hbase.sh

# Keep the container running
tail -f /dev/null
