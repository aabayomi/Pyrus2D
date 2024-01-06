#!/bin/bash

for i in `seq 1 10`; do
    kill -INT `pidof lt-rcssserver` 1>/dev/null 2>&1 &
    kill -INT `pidof rcssserver` 1>/dev/null 2>&1 &
    killall -9 rcssserver 1>/dev/null 2>&1 &
    killall -9 rcssmonitor 1>/dev/null 2>&1 &
    killall -9 rcsslogplayer 1>/dev/null 2>&1 &
    killall -9 lt-rcssserver 1>/dev/null 2>&1 &
    killall -9 run.sh 1>/dev/null 2>&1 &
    killall -9 python 1>/dev/null 2>&1 &
done 

wait
