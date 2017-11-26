import hug
import logging
import os
import re

from nikoniko.nikonikoapi import NikonikoAPI
from nikoniko.entities import DB

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

def db_connstring_from_environment(logger=logging.getLogger(__name__)):
    ''' compose the connection string based on environment vars values '''
    db_driver = os.getenv('DB_DRIVER', 'postgresql')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_dbname = os.getenv('DB_DBNAME', 'nikoniko')
    db_username = os.getenv('DB_USERNAME', os.getenv('USER', None))
    db_password = os.getenv('DB_PASSWORD', None)
    db_connstring = '{}://{}{}{}{}:{}/{}'.format(
        db_driver,
        db_username if db_username else '',
        ':{}'.format(db_password) if db_password else '',
        '@' if db_username else '',
        db_host,
        db_port,
        db_dbname)
    logger.debug(
        'db_connstring: [%s]',
        re.sub(
            r'(:.+?):.*?@',
            r'\1:XXXXXXX@',
            db_connstring))
    return db_connstring

MYDB = DB(db_connstring_from_environment(LOGGER), echo=True)
MYDB.create_all()
SESSJION = MYDB.session()
SECRET_KEY = os.environ['JWT_SECRET_KEY']  # may purposefully throw exception

if os.getenv('DO_BOOTSTRAP_DB', 'false').lower() in [
        'yes', 'y', 'true', 't', '1']:
    LOGGER.info('Bootstrapping DB')
    bootstrap_db(LOGGER)

NIKONIKOAPI = NikonikoAPI(hug.API(__name__), SESSJION, SECRET_KEY, LOGGER)
