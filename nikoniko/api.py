"""
Provide an API to manage happiness logs (nikoniko) for teams
"""
import logging
import datetime

import os
import re
import hug
import jwt
import bcrypt
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import InvalidRequestError
from falcon import HTTP_404
from falcon import HTTP_401
from falcon import HTTP_403
from falcon import HTTP_204

from nikoniko.entities import DB
from nikoniko.entities import User, USER_SCHEMA
from nikoniko.entities import USERPROFILE_SCHEMA
from nikoniko.entities import Person, PERSON_SCHEMA, PEOPLE_SCHEMA
from nikoniko.entities import Board, BOARD_SCHEMA, BOARDS_SCHEMA
from nikoniko.entities import ReportedFeeling, REPORTEDFEELING_SCHEMA
from nikoniko.entities import InvalidatedToken

from nikoniko.hug_middleware_cors import CORSMiddleware


logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


def db_connstring_from_environment():
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
    LOGGER.debug(
        'db_connstring: [%s]',
        re.sub(
            r'(:.+?):.*?@',
            r'\1:XXXXXXX@',
            db_connstring))
    return db_connstring


MYDB = DB(db_connstring_from_environment(), echo=True)
MYDB.create_all()
SESSION = MYDB.session()

SECRET_KEY = os.environ['JWT_SECRET_KEY']  # may purposefully throw exception

API = hug.API(__name__)
API.http.add_middleware(CORSMiddleware(API))


def return_unauthorised(response, email, exception=None):
    ''' Update the response to mean unauthorised access '''
    response.status = HTTP_401
    return 'Invalid email and/or password for email: {} [{}]'.format(
        email, exception)


def token_verify(token):
    ''' hug authentication token verification function '''
    LOGGER.debug('Token: %s', token)
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithm='HS256')
        LOGGER.debug('Decoded token: %s', decoded_token)
    except jwt.DecodeError:
        return False
    try:
        SESSION.query(
            InvalidatedToken).filter_by(token=token).one()
        return False
    except NoResultFound:
        return decoded_token


TOKEN_KEY_AUTHENTICATION = \
    hug.authentication.token(  # pylint: disable=no-value-for-parameter
        token_verify)


#######################################
# Handlers

class NikonikoAPI:
    def login(email: hug.types.text, password: hug.types.text, response):
        '''Authenticate and return a token'''
        try:
            user = SESSION.query(User).filter_by(email=email).one()
            if bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                created = datetime.datetime.now()
                return {
                    'user': user.user_id,
                    'person': user.person_id,
                    'token': jwt.encode(
                        {
                            'user': user.user_id,
                            'created': created.isoformat(),
                            'exp':
                                (created + datetime.timedelta(days=1)).timestamp()
                        },
                        SECRET_KEY,
                        algorithm='HS256'
                    )}
            return return_unauthorised(response, email)
        except NoResultFound as exception:
            return return_unauthorised(response, email, exception)
    
    
    def update_password(
            user_id: hug.types.number,
            password: hug.types.text,
            request,
            response,
            authenticated_user: hug.directives.user):
        '''Updates a users' password '''
        try:
            found_user = SESSION.query(User).filter_by(user_id=user_id).one()
        except NoResultFound as exception:
            LOGGER.debug('User not found: %s', exception)
            response.status = HTTP_404
            return None
        if user_id != authenticated_user['user']:
            response.status = HTTP_401
            return '''Authenticated user isn\'t allowed to update \
                    the password for requested user'''
        LOGGER.debug(
            'user_id: %s, authenticated_user: %s',
            user_id,
            authenticated_user)
        if user_id != authenticated_user['user']:
            response.status = HTTP_401
            return '''Authenticated user isn\'t allowed to update \
                the password for requested user'''
        found_user.password_hash = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()).decode()
        SESSION.add(found_user)
        invalidated_token = InvalidatedToken(
            token=request.headers['AUTHORIZATION'],
            timestamp_invalidated=datetime.datetime.now())
        SESSION.add(invalidated_token)
        SESSION.commit()
        response.status = HTTP_204
    
    
    def get_user(user_id: hug.types.number, response,
                 authenticated_user: hug.directives.user):
        '''Returns a user'''
        LOGGER.debug('Authenticated user reported: %s', authenticated_user)
        try:
            res = SESSION.query(User).filter_by(user_id=user_id).one()
            boards = SESSION.query(
                Board).join(
                    Person.boards).filter(
                        Person.person_id == res.person_id).all()
            res.boards = boards
        except NoResultFound as exception:
            LOGGER.debug('User not found: %s', exception)
            response.status = HTTP_404
            return None
        return USER_SCHEMA.dump(res).data
    
    
    def get_user_profile(
            user_id: hug.types.number,
            response,
            authenticated_user: hug.directives.user):
        '''Returns a user profile'''
        LOGGER.debug('Authenticated user reported: %s', authenticated_user)
        try:
            res = SESSION.query(User).filter_by(user_id=user_id).one()
        except NoResultFound as exception:
            LOGGER.error('User not found: %s', exception)
            response.status = HTTP_404
            return None
        return USERPROFILE_SCHEMA.dump(res).data
    
    
    def patch_user_profile(  # pylint: disable=too-many-arguments
            user_id: hug.types.number,
            name: hug.types.text,
            email: hug.types.text,
            password: hug.types.text,
            request,
            response,
            authenticated_user: hug.directives.user):
        '''Patches a user's data '''
        LOGGER.debug(
            'User profile patch: <<"%s", "%s", "%s">>',
            name,
            email,
            password)
        LOGGER.debug('Authenticated user reported: %s', authenticated_user)
        LOGGER.debug('Token: %s', request.headers['AUTHORIZATION'])
        try:
            found_user = SESSION.query(User).filter_by(user_id=user_id).one()
        except NoResultFound as exception:
            LOGGER.error('User not found: %s', exception)
            response.status = HTTP_404
            return None
        if user_id != authenticated_user['user']:
            response.status = HTTP_401
            return '''Authenticated user isn\'t allowed to update \
                    the password for requested user'''
        if name:
            found_user.name = name
        if email:
            found_user.email = email
        if password:
            found_user.password_hash = bcrypt.hashpw(
                password.encode(),
                bcrypt.gensalt()).decode()
            SESSION.add(found_user)
            invalidated_token = InvalidatedToken(
                token=request.headers['AUTHORIZATION'],
                timestamp_invalidated=datetime.datetime.now())
            SESSION.add(invalidated_token)
        try:
            SESSION.commit()
            return
        except InvalidRequestError:
            response.status = HTTP_403
            return "User profile not updated"
    
    
    def get_person(person_id: hug.types.number, response):
        '''Returns a person'''
        try:
            res = SESSION.query(Person).filter_by(person_id=person_id).one()
        except NoResultFound:
            response.status = HTTP_404
            return None
        return PERSON_SCHEMA.dump(res).data
    
    
    def people():
        '''Returns all the people'''
        res = SESSION.query(Person).all()
        return PEOPLE_SCHEMA.dump(res).data
    
    
    def board(board_id: hug.types.number, response):
        '''Returns a board'''
        try:
            res = SESSION.query(Board).filter_by(board_id=board_id).one()
            for person in res.people:
                reportedfeelings = SESSION.query(
                    ReportedFeeling).filter(
                        ReportedFeeling.board_id == board_id).filter(
                            ReportedFeeling.person_id == person.person_id).all()
                person.reportedfeelings = reportedfeelings
        except NoResultFound:
            response.status = HTTP_404
            return None
        return BOARD_SCHEMA.dump(res).data
    
    
    def get_boards():
        '''Returns all boards'''
        res = SESSION.query(Board).all()
        return BOARDS_SCHEMA.dump(res).data
    
    
    def get_reported_feeling(
            board_id: hug.types.number,
            person_id: hug.types.number,
            date: hug.types.text,
            response):
        '''Returns a specific reported feeling for a board, person and date'''
        try:
            res = SESSION.query(ReportedFeeling).filter_by(
                board_id=board_id,
                person_id=person_id,
                date=date).one()
        except NoResultFound:
            response.status = HTTP_404
            return None
        return REPORTEDFEELING_SCHEMA.dump(res).data
    
    
    def create_reported_feeling(
            board_id: hug.types.number,
            person_id: hug.types.number,
            feeling: hug.types.text,
            date: hug.types.text):
        '''Creates a new reported_feeling'''
        try:
            reported_feeling = SESSION.query(ReportedFeeling).filter_by(
                board_id=board_id,
                person_id=person_id,
                date=date).one()
            reported_feeling.feeling = feeling
        except NoResultFound:
            reported_feeling = ReportedFeeling(
                person_id=person_id,
                board_id=board_id,
                date=datetime.datetime.strptime(
                    date,
                    "%Y-%m-%d").date(),
                feeling=feeling)
            SESSION.add(reported_feeling)
        SESSION.commit()
        return REPORTEDFEELING_SCHEMA.dump(reported_feeling).data

    def __init__(self):
        hug.post('/login', api=API)(login)
        hug.put('/password/{user_id}', api=API, requires=TOKEN_KEY_AUTHENTICATION)(update_password)
        hug.get('/users/{user_id}', api=API, requires=TOKEN_KEY_AUTHENTICATION)(get_user)
        hug.get('/userProfiles/{user_id}', api=API, requires=TOKEN_KEY_AUTHENTICATION)(get_user_profile)
        hug.patch('/userProfiles/{user_id}', api=API, requires=TOKEN_KEY_AUTHENTICATION)(patch_user_profile)
        hug.get('/people/{person_id}', api=API, requires=TOKEN_KEY_AUTHENTICATION)(get_person)
        hug.get('/people', api=API, requires=TOKEN_KEY_AUTHENTICATION)(people)
        hug.get('/boards/{board_id}', api=API, requires=TOKEN_KEY_AUTHENTICATION)(board)
        hug.get('/boards', api=API, requires=TOKEN_KEY_AUTHENTICATION)(get_boards)
        hug.get(
            '/reportedfeelings/boards/{board_id}/people/{person_id}/dates/{date}',
            api=API,
            requires=TOKEN_KEY_AUTHENTICATION)(get_reported_feeling)
        hug.post(
            '/reportedfeelings/boards/{board_id}/people/{person_id}/dates/{date}',
            api=API,
            requires=TOKEN_KEY_AUTHENTICATION)(create_reported_feeling)


def bootstrap_db():
    ''' Fill in the DB with initial data '''
    one_person = Person(person_id=1, label='Ann')
    other_person = Person(person_id=2, label='John')
    SESSION.add(one_person)
    SESSION.add(other_person)
    try:
        SESSION.commit()
    except InvalidRequestError as exception:
        print(exception)
        SESSION.rollback()
    one_user = User(
        user_id=1,
        name='John Smith',
        email='john@example.com',
        person_id=2,
        password_hash=bcrypt.hashpw(
            'whocares'.encode(),
            bcrypt.gensalt()).decode())
    SESSION.add(one_user)
    try:
        SESSION.commit()
    except InvalidRequestError as exception:
        print(exception)
        SESSION.rollback()
    one_board = Board(board_id=1, label='Global board')
    one_board.people.append(one_person)
    one_board.people.append(other_person)
    SESSION.add(one_board)
    another_board = Board(board_id=2, label='The A Team')
    another_board.people.append(one_person)
    another_board.people.append(other_person)
    SESSION.add(another_board)
    and_a_third__board = Board(board_id=3, label='The Harlem Globetrotters')
    and_a_third__board.people.append(one_person)
    and_a_third__board.people.append(other_person)
    SESSION.add(and_a_third__board)
    try:
        SESSION.commit()
    except InvalidRequestError as exception:
        print(exception)
        SESSION.rollback()


if os.getenv('DO_BOOTSTRAP_DB', 'false').lower() in [
        'yes', 'y', 'true', 't', '1']:
    LOGGER.info('Bootstrapping DB')
    bootstrap_db()

NIKONIKOAPI = NikonikoAPI()

