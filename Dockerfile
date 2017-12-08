FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG dbhost
ARG dbuser

ENV DB_HOST=$dbhost DB_USERNAME=$dbuser
CMD [ "uwsgi", "./conf/uwsgi.ini" ]
