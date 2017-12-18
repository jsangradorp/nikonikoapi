#!/usr/bin/env bash

DEST=$1
[ -z "$DEST" ] && DEST=192.168.69.185

set -x

cd $(dirname $0)/..
rm -f dist/*
python setup.py bdist_wheel
cdist config -c conf/cdist -v $DEST
