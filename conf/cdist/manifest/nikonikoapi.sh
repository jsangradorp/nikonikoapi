#!/bin/sh -e
__cdistmarker

export CDIST_ORDER_DEPENDENCY=on

# __package_update_index
# __package_upgrade_all --apt-dist-upgrade --apt-clean

__package build-essential
__package python3-dev
__package python3-pip
__package python3-setuptools

__package_pip uwsgi --pip /usr/bin/pip3

FILENAME=$(cd dist && ls -x nikoniko*.whl)
__file ${FILENAME} --source dist/${FILENAME}
__package_pip ${FILENAME} --pip /usr/bin/pip3 --name /${FILENAME}

unset CDIST_ORDER_DEPENDENCY

__hosts nikonikoapi --ip 127.0.0.1

__group uwsgi --gid 1001 --system
require="__group/uwsgi" __user uwsgi --system --uid 1001 --gid 1001

__config_file /etc/init.d/nikonikoapi --source conf/etc/init.d/nikonikoapi --mode 0700
__config_file /etc/uwsgi.ini --source conf/etc/uwsgi.ini
__config_file /etc/default/nikonikoapi.sample --source conf/etc/default/nikonikoapi.sample
if [ -r conf/etc/default/nikonikoapi ]; then
    __config_file /etc/default/nikonikoapi --source conf/etc/default/nikonikoapi --state exists
else
    __config_file /etc/default/nikonikoapi --source conf/etc/default/nikonikoapi.sample --state exists
fi
require="__package_pip/uwsgi \
         __package_pip/${FILENAME} \
         __config_file/etc/init.d/nikonikoapi \
         __config_file/etc/uwsgi.ini \
         __config_file/etc/default/nikonikoapi \
         __user/uwsgi" \
    __process uwsgi --start="/etc/init.d/nikonikoapi"
require="__config_file/etc/init.d/nikonikoapi" __start_on_boot nikonikoapi
