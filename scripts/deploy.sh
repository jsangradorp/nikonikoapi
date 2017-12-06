#!/usr/bin/env bash

DEST=$1
[ -z "$DEST" ] && DEST=192.168.69.185

set -x

cd $(dirname $0)/..
rm -f dist/*
python setup.py bdist_wheel
cksum dist/nikoniko*.whl > dist/checksum
cdist config -c conf/cdist -vvv $DEST
