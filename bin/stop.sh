#!/bin/bash

set -x

PIDFILE=.cdss.pid
CIDFILE=.cdss.cid


if [ -f $PIDFILE ]
then
	for pid in `cat $PIDFILE`
	do
		kill -9 $(pstree $pid -a -p -l| grep 'service'|cut -d, -f2|cut -d' ' -f1)
	done
    rm -f $PIDFILE
else
    echo "no cdss service is running"
fi

if [ -f $CIDFILE ]
then
	for cid in `cat $CIDFILE`
	do
		docker stop $cid
		echo $cid
	done
    rm -f $CIDFILE
else
    echo "no running container"
fi
