#!/bin/bash

FULLSTATE=""
MONITOR=""
SYNCH=""
LOG=""
LOGLEVEL="101"
HIERARCHICALFSM=""
CROSSENTROPY=""
QLEARNING=""
GAMMA="1.0"
LAMBDA="0.5"
ALPHA="0.125"
INITIALWEIGHT="0.5"
BUILD="release"
LEARNING="--keeper-learn --keeper-policy=learned"
LEARNING="$LEARNING --taker-learn --taker-policy=learned"
LOGDIR="logs"
QFILE="Q"
KEEPERQFILE2=""
TAKERQFILE2=""
MEMORYCHECK=""

while getopts  "b:g:L:A:K:T:I:lfmsnzEMQ" flag; do
    case "$flag" in
        f) FULLSTATE="--fullstate" ;; 
        m) MONITOR="--monitor" ;;
        s) SYNCH="--synch-mode" ;;
        l) LOG="--log-dir=$LOGDIR --log-game --log-text --log-level $LOGLEVEL" ;;
        z) HIERARCHICALFSM="--hierarchical-fsm" ;;
        E) CROSSENTROPY="--crossEntropy" ;;
        Q) QLEARNING="--qlearning" ;;
        g) GAMMA="`echo $OPTARG | sed -e 's/[0]*$//g'`" ;;
        L) LAMBDA="`echo $OPTARG | sed -e 's/[0]*$//g'`" ;;
        A) ALPHA="`echo $OPTARG | sed -e 's/[0]*$//g'`" ;;
        I) INITIALWEIGHT="`echo $OPTARG | sed -e 's/[0]*$//g'`" ;;
        b) BUILD="$OPTARG" ;;
        n) LEARNING="--keeper-policy=learned! --taker-policy=learned!" ;;
        K) KEEPERQFILE2="$OPTARG" ;;
        T) TAKERQFILE2="$OPTARG" ;;
        M) MEMORYCHECK="--memory-check" ;;
    esac
done

echo Test range: $CROSSENTROPY

PORT="--port=`shuf -i 2000-65000 -n 1`"

if [ ! -z $GAMMA ]; then
    QFILE="${QFILE}_g${GAMMA}"
fi

if [ ! -z $LAMBDA ]; then
    QFILE="${QFILE}_l${LAMBDA}"
fi

if [ ! -z $ALPHA ]; then
    QFILE="${QFILE}_a${ALPHA}"
fi

if [ ! -z $INITIALWEIGHT ]; then
    QFILE="${QFILE}_w${INITIALWEIGHT}"
fi

if [ -z $FULLSTATE ]; then
    QFILE="${QFILE}_nfs"
fi

if [ ! -z $HIERARCHICALFSM ]; then
    QFILE="${QFILE}_fsm"
fi

if [ ! -z $CROSSENTROPY ]; then
    QFILE="${QFILE}_cem"
fi

if [ ! -z $QLEARNING ]; then
    QFILE="${QFILE}_ql"
fi

QFILE="${QFILE}.gz"
KEEPERQFILE="keeper_$QFILE"
TAKERQFILE="taker_$QFILE"

if [ ! -z $KEEPERQFILE2 ]; then
    KEEPERQFILE="$KEEPERQFILE2" # overwrite QFILE
fi

if [ ! -z $TAKERQFILE2 ]; then
    TAKERQFILE="$TAKERQFILE2" # overwrite QFILE
fi

if [ $BUILD != "none" ]; then
    make -j `nproc` $BUILD
fi

CONSOLE_LOG="$LOGDIR/`basename $QFILE .gz`.console"


ulimit -c unlimited

python3 keepaway_old.py --keeper-count=3 --taker-count=2 