#!/bin/bash

# 환경 변수 설정
export ZOOKEEPER_HOME=/opt/zookeeper
export ZOOCFGDIR=/conf
export ZOODATADIR=/data
export ZOOLOGDIR=/data/log
export PATH=$PATH:$ZOOKEEPER_HOME/bin

# ZooKeeper 시작
zkServer.sh start $ZOOCFGDIR/zoo.cfg

# 상태 확인 (선택 사항)
zkServer.sh status $ZOOCFGDIR/zoo.cfg

# 포그라운드로 유지
tail -f $ZOOLOGDIR/zookeeper.outs