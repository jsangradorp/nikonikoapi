#!/usr/bin/env bash

set -x

DEST="$@"
[ -z "$DEST" ] && DEST="-t nikonikoapi"

cd $(dirname $0)/..
rm -f dist/*
python setup.py bdist_wheel
cdist config -c conf/cdist -v $DEST
