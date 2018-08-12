#!/usr/bin/env bash

cd $(dirname $0)/..

if [ -z "$VIRTUAL_ENV" ] ; then
    [ ! -d .venv ] && python3 -m venv .venv
    . .venv/bin/activate
fi

kill_children() {
        echo
            [ -n "$proxypid"  ] && kill -9 $proxypid 2> /dev/null

}
trap "kill_children" 0

if [ "$LOCAL" != "y" -a "$LOCAL" != "1" -a "$LOCAL" != "t" ] ; then
    SOCKET_OPTS="--socket /tmp/uwsgi.sock --chmod-socket"
else
    SOCKET_OPTS="--http :8080"
    local-ssl-proxy --source 8443 --target 8080 --cert conf/etc/nginx/localhost.crt --key conf/etc/nginx/localhost.key & proxypid=$!
fi

uwsgi --pythonpath "${VIRTUAL_ENV}/lib/python3.6/site-packages" --logformat '%(addr) - %(user) [%(ltime)] "%(method) %(uri) %(proto)" %(status) %(size) "%(referer)" "%(uagent)"' --enable-threads $SOCKET_OPTS --module nikoniko.api --callable __hug_wsgi__
