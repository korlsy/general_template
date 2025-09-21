#!/bin/sh
#
# psql "host=127.0.0.1 port=5433 dbname=lsy user=lsy password=lsy"
# psql -W -h 127.0.0.1 -p 5433 -U lsy -d lsy
#

STS=`ps -ef | grep "port-forward" | grep "5433"|wc -l`

if [ $STS -gt 0 ]; then
  echo "already running port-forward 5433:5432"
  exit $?
fi

/usr/bin/nohup \
kubectl --namespace postgresql port-forward svc/postgresql 5433:5432 \
>/dev/null 2>&1 &