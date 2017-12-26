# Nikoniko API

An API to manage a collection of nikoniko calendars.

Python 3 mandatory.

## Secret files and how to generate

- server certificate and key (localhost.crt and localhost.key **only for
  development**):
  `openssl req -x509 -newkey rsa:4096 -sha256 -nodes -keyout conf/etc/nginx/localhost.key -out conf/etc/nginx/localhost.crt -subj "/CN=example.com" -days 3650`
  See also for example [this entry in Stack Overflow](https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl/41366949#41366949).

- dhparams.pem
  `openssl dhparam -out dhparams.pem 2048`

## Running
3 ways to run more or less out of the box:

- Local:
  `LOCAL="y" JWT_SECRET_KEY="example-local-jwt-key" ./scripts/run.sh`
- Docker:
  `docker-compose up`
- External host (for example, virtual machine):
  `./scripts/deploy.sh [IP address of the host]`
  You need to be able to ssh passwordless as root to the destination host for
  this to work.

### Bootstrapping a test DB

If the `DO_BOOSTRAP_DB` environment variable is set to `y`, example values
will be inserted in the DB on startup.

