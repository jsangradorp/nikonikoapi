""" "Main" entry point to run the Nikoniko API """

import logging
import os
import re

import bcrypt
import hug

from sqlalchemy.exc import InvalidRequestError

from nikoniko.entities import DB
from nikoniko.entities import User
from nikoniko.entities import Person
from nikoniko.entities import Board

from nikoniko.nikonikoapi import NikonikoAPI


def db_connstring_from_environment(logger=logging.getLogger(__name__)):
    """ compose the connection string based on environment vars values """
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


def mailer_config_from_environment(logger=logging.getLogger(__name__)):
    """ Calculate and return mailer configuration based on environment """
    mailer_config = dict(
        server=os.getenv('MAILER_HOST', 'localhost'),
        port=os.getenv('MAILER_PORT', '25'),
        user=os.getenv('MAILER_USER', 'coral@example.com'),
        password=os.getenv('MAILER_PASSWORD', 'mailerpassword'),
        sender=os.getenv('MAILER_SENDER', 'noreply@nikonikoboards.com'))
    logger.debug('MAILER: [%s]', mailer_config)
    return mailer_config


def bootstrap_db(session):
    """ Fill in the DB with initial data """
    one_person = Person(person_id=1, label='Ann')
    other_person = Person(person_id=2, label='John')
    session.add(one_person)
    session.add(other_person)
    try:
        session.commit()
    except InvalidRequestError as exception:
        print(exception)
        session.rollback()
    one_user = User(
        user_id=1,
        name='John Smith',
        email='john@example.com',
        person_id=2,
        password_hash=bcrypt.hashpw(
            'whocares'.encode(),
            bcrypt.gensalt()))
    session.add(one_user)
    try:
        session.commit()
    except InvalidRequestError as exception:
        print(exception)
        session.rollback()
    one_board = Board(board_id=1, label='Global board')
    one_board.people.append(one_person)
    one_board.people.append(other_person)
    session.add(one_board)
    another_board = Board(board_id=2, label='The A Team')
    another_board.people.append(one_person)
    another_board.people.append(other_person)
    session.add(another_board)
    and_a_third__board = Board(board_id=3, label='The Harlem Globetrotters')
    and_a_third__board.people.append(one_person)
    and_a_third__board.people.append(other_person)
    session.add(and_a_third__board)
    try:
        session.commit()
    except InvalidRequestError as exception:
        print(exception)
        session.rollback()


logging.basicConfig()
LOG_LEVEL = getattr(logging, os.getenv('LOGLEVEL', 'INFO').upper())
if not isinstance(LOG_LEVEL, int):
    raise ValueError('Invalid log level: {}'.format(LOG_LEVEL))
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(LOG_LEVEL)
LOGGER.info('Log level set to %s', LOG_LEVEL)

NIKONIKODB = DB(
    db_connstring_from_environment(LOGGER),
    echo=(LOGGER.isEnabledFor(logging.DEBUG)))
NIKONIKODB.create_all()
SESSION = NIKONIKODB.session()
SECRET_KEY = os.environ['JWT_SECRET_KEY']  # may purposefully throw exception

if os.getenv('DO_BOOTSTRAP_DB', 'false').lower() in [
        'yes', 'y', 'true', 't', '1']:
    LOGGER.info('Bootstrapping DB')
    bootstrap_db(SESSION)

MAILCONFIG = mailer_config_from_environment(LOGGER)

CONFIG = dict(
    secret_key=SECRET_KEY,
    mailconfig=MAILCONFIG,
    logger=LOGGER)

NIKONIKOAPI = NikonikoAPI(
    hug.API(__name__),
    SESSION,
    CONFIG)
NIKONIKOAPI.setup()
