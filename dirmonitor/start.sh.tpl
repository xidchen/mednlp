#!/bin/bash

MONDIR=${MONDIR}

core=('entity')

for core_item in ${core[@]}; do

    if [ ! -d $MONDIR/$core_item ]
    then
        mkdir -p $MONDIR/$core_item
    fi
	echo 'starting dir monitor:'$core_item
    python ./directory_monitor.py -r $MONDIR/$core_item -c $core_item -d -m .xml
	echo 'start dir monitor:'$core_item
done
