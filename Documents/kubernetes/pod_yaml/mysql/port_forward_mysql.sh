#!/bin/sh
#
# mysql -h 127.0.0.1 -P 3307 -u lsy -plsy --connect-timeout=5 --protocol=TCP
# mysql -h 127.0.0.1 -P 3307 -u lsy -plsy lsy
#

STS=`ps -ef | grep "port-forward" | grep "3307"|wc -l`

if [ $STS -gt 0 ]; then
  echo "already running port-forward 3307:3306"
  exit $?
fi

/usr/bin/nohup \
kubectl --namespace mysql port-forward svc/mysql 3307:3306 \
>/dev/null 2>&1 &