#!/usr/bin/env sh
uwsgi --pythonpath ./.venv/lib/python3.6/site-packages --logformat '%(addr) - %(user) [%(ltime)] "%(method) %(uri) %(proto)" %(status) %(size) "%(referer)" "%(uagent)"' --enable-threads --http 0.0.0.0:8000 --wsgi-file nikoniko/api.py --callable __hug_wsgi__
