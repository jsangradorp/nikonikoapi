#!/usr/bin/env sh

# DO_BOOTSTRAP_DB=true JWT_SECRET_KEY=pp LOCAL=y LOGLEVEL=DEBUG ./scripts/run.sh

cd $(dirname $0)/..

if [ -z "$VIRTUAL_ENV" ] ; then
    . .venv/bin/activate
fi

trap "kill_children" 0
kill_children() {
        echo
            [ -n "$proxypid"  ] && kill -9 $proxypid 2> /dev/null

}

if [ "$LOCAL" != "y" -a "$LOCAL" != "1" -a "$LOCAL" != "t" ] ; then
    SOCKET_OPTS="--socket /tmp/uwsgi.sock --chmod-socket"
else
    SOCKET_OPTS="--http :8080"
    local-ssl-proxy --source 8443 --target 8080 --cert conf/etc/nginx/localhost.crt --key conf/etc/nginx/localhost.key & proxypid=$!
fi
uwsgi --pythonpath ./.venv/lib/python3.6/site-packages --logformat '%(addr) - %(user) [%(ltime)] "%(method) %(uri) %(proto)" %(status) %(size) "%(referer)" "%(uagent)"' --enable-threads $SOCKET_OPTS --wsgi-file nikoniko/api.py --callable __hug_wsgi__

# alternative: JWT_SECRET_KEY="jhjh" uwsgi --pythonpath ./.venv/lib/python3.6/site-packages --logformat '%(addr) - %(user) [%(ltime)] "%(method) %(uri) %(proto)" %(status) %(size) "%(referer)" "%(uagent)"' --enable-threads --http :8080 --module nikoniko.api --callable __hug_wsgi__
