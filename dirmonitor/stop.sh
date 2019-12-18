#!/bin/bash

name='directory_monitor.py'
# ps aux | grep $name | grep -v grep | grep $USER | awk '{print $2}' | while read pid
ps -o ruser=userForLongName -e -o pid,ppid,c,stime,tty,time,cmd | grep $name | grep -v grep | grep $USER | awk '{print $2}' | while read pid
do
    echo "kill $name ($pid)"
    kill $pid
done

