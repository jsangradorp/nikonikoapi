#!/usr/bin/env sh
if [ -z "$VIRTUAL_ENV" ] ; then
    . .venv/bin/activate
fi
nginx
uwsgi --pythonpath ./.venv/lib/python3.6/site-packages --logformat '%(addr) - %(user) [%(ltime)] "%(method) %(uri) %(proto)" %(status) %(size) "%(referer)" "%(uagent)"' --enable-threads --socket /tmp/uwsgi.sock --wsgi-file nikoniko/api.py --callable __hug_wsgi__
