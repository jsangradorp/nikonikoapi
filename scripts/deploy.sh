#!/usr/bin/env bash

DEST=$1
[ -z "$DEST" ] && DEST=192.168.69.185

cd $(dirname $0)/..
cdist config -c conf/cdist -vv $DEST
