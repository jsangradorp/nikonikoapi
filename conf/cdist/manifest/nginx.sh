#!/bin/sh -e
__cdistmarker

# __package_update_index
# __package_upgrade_all --apt-dist-upgrade --apt-clean

__package nginx

require="__package/nginx" __file /etc/nginx/sites-available/nikonikoapi.conf --source conf/etc/nginx/nikonikoapi.conf
require="__package/nginx" __link /etc/nginx/sites-enabled/nikonikoapi.conf --source /etc/nginx/sites-available/nikonikoapi.conf --type symbolic
require="__package/nginx" __file /etc/nginx/localhost.key --source conf/etc/nginx/localhost.key
require="__package/nginx" __file /etc/nginx/localhost.crt --source conf/etc/nginx/localhost.crt
require="__package/nginx" __file /etc/nginx/uwsgi_params --source conf/etc/nginx/uwsgi_params
require="__package/nginx" __file /etc/nginx/dhparams.pem --source conf/etc/nginx/dhparams.pem

require="__package/nginx" __start_on_boot nginx
