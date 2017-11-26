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


class NikonikoAPI:
    def token_verify(self, token):
        ''' hug authentication token verification function '''
        self.logger.debug('Token: %s', token)
        try:
            decoded_token = jwt.decode(token, self.secret_key, algorithm='HS256')
            self.logger.debug('Decoded token: %s', decoded_token)
        except jwt.DecodeError:
            return False
        try:
            self.session.query(
                InvalidatedToken).filter_by(token=token).one()
            return False
        except NoResultFound:
            return decoded_token

    def return_unauthorised(self, response, email, exception=None):
        ''' Update the response to mean unauthorised access '''
        response.status = HTTP_401
        return 'Invalid email and/or password for email: {} [{}]'.format(
            email, exception)

    def login(self, email: hug.types.text, password: hug.types.text, response):
        '''Authenticate and return a token'''
        try:
            user = self.session.query(User).filter_by(email=email).one()
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
                        self.secret_key,
                        algorithm='HS256'
                    )}
            return return_unauthorised(response, email)
        except NoResultFound as exception:
            return return_unauthorised(response, email, exception)
    
    
    def update_password(
            self,
            user_id: hug.types.number,
            password: hug.types.text,
            request,
            response,
            authenticated_user: hug.directives.user):
        '''Updates a users' password '''
        try:
            found_user = self.session.query(User).filter_by(user_id=user_id).one()
        except NoResultFound as exception:
            self.logger.debug('User not found: %s', exception)
            response.status = HTTP_404
            return None
        if user_id != authenticated_user['user']:
            response.status = HTTP_401
            return '''Authenticated user isn\'t allowed to update \
                    the password for requested user'''
        self.logger.debug(
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
        self.session.add(found_user)
        invalidated_token = InvalidatedToken(
            token=request.headers['AUTHORIZATION'],
            timestamp_invalidated=datetime.datetime.now())
        self.session.add(invalidated_token)
        self.session.commit()
        response.status = HTTP_204
    
    
    def get_user(self, user_id: hug.types.number, response,
                 authenticated_user: hug.directives.user):
        '''Returns a user'''
        self.logger.debug('Authenticated user reported: %s', authenticated_user)
        try:
            res = self.session.query(User).filter_by(user_id=user_id).one()
            boards = self.session.query(
                Board).join(
                    Person.boards).filter(
                        Person.person_id == res.person_id).all()
            res.boards = boards
        except NoResultFound as exception:
            self.logger.debug('User not found: %s', exception)
            response.status = HTTP_404
            return None
        return USER_SCHEMA.dump(res).data
    
    
    def get_user_profile(
            self,
            user_id: hug.types.number,
            response,
            authenticated_user: hug.directives.user):
        '''Returns a user profile'''
        self.logger.debug('Authenticated user reported: %s', authenticated_user)
        try:
            res = self.session.query(User).filter_by(user_id=user_id).one()
        except NoResultFound as exception:
            self.logger.error('User not found: %s', exception)
            response.status = HTTP_404
            return None
        return USERPROFILE_SCHEMA.dump(res).data
    
    
    def patch_user_profile(  # pylint: disable=too-many-arguments
            self,
            user_id: hug.types.number,
            name: hug.types.text,
            email: hug.types.text,
            password: hug.types.text,
            request,
            response,
            authenticated_user: hug.directives.user):
        '''Patches a user's data '''
        self.logger.debug(
            'User profile patch: <<"%s", "%s", "%s">>',
            name,
            email,
            password)
        self.logger.debug('Authenticated user reported: %s', authenticated_user)
        self.logger.debug('Token: %s', request.headers['AUTHORIZATION'])
        try:
            found_user = self.session.query(User).filter_by(user_id=user_id).one()
        except NoResultFound as exception:
            self.logger.error('User not found: %s', exception)
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
            self.session.add(found_user)
            invalidated_token = InvalidatedToken(
                token=request.headers['AUTHORIZATION'],
                timestamp_invalidated=datetime.datetime.now())
            self.session.add(invalidated_token)
        try:
            self.session.commit()
            return
        except InvalidRequestError:
            response.status = HTTP_403
            return "User profile not updated"
    
    
    def get_person(self, person_id: hug.types.number, response):
        '''Returns a person'''
        try:
            res = self.session.query(Person).filter_by(person_id=person_id).one()
        except NoResultFound:
            response.status = HTTP_404
            return None
        return PERSON_SCHEMA.dump(res).data
    
    
    def people(self):
        '''Returns all the people'''
        res = self.session.query(Person).all()
        return PEOPLE_SCHEMA.dump(res).data
    
    
    def board(self, board_id: hug.types.number, response):
        '''Returns a board'''
        try:
            res = self.session.query(Board).filter_by(board_id=board_id).one()
            for person in res.people:
                reportedfeelings = self.session.query(
                    ReportedFeeling).filter(
                        ReportedFeeling.board_id == board_id).filter(
                            ReportedFeeling.person_id == person.person_id).all()
                person.reportedfeelings = reportedfeelings
        except NoResultFound:
            response.status = HTTP_404
            return None
        return BOARD_SCHEMA.dump(res).data
    
    
    def get_boards(self):
        '''Returns all boards'''
        res = self.session.query(Board).all()
        return BOARDS_SCHEMA.dump(res).data
    
    
    def get_reported_feeling(
            self,
            board_id: hug.types.number,
            person_id: hug.types.number,
            date: hug.types.text,
            response):
        '''Returns a specific reported feeling for a board, person and date'''
        try:
            res = self.session.query(ReportedFeeling).filter_by(
                board_id=board_id,
                person_id=person_id,
                date=date).one()
        except NoResultFound:
            response.status = HTTP_404
            return None
        return REPORTEDFEELING_SCHEMA.dump(res).data
    
    
    def create_reported_feeling(
            self,
            board_id: hug.types.number,
            person_id: hug.types.number,
            feeling: hug.types.text,
            date: hug.types.text):
        '''Creates a new reported_feeling'''
        try:
            reported_feeling = self.session.query(ReportedFeeling).filter_by(
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
            self.session.add(reported_feeling)
        self.session.commit()
        return REPORTEDFEELING_SCHEMA.dump(reported_feeling).data

    def __init__(self, api, session, secret_key, logger):
        self.api = api
        self.session = session
        self.secret_key = secret_key
        self.logger = logger

        self.api.http.add_middleware(CORSMiddleware(self.api))
        hug.post('/login', api=self.api)(self.login)
        TOKEN_KEY_AUTHENTICATION = \
            hug.authentication.token(  # pylint: disable=no-value-for-parameter
                self.token_verify)
        hug.put('/password/{user_id}', api=self.api, requires=TOKEN_KEY_AUTHENTICATION)(self.update_password)
        hug.get('/users/{user_id}', api=self.api, requires=TOKEN_KEY_AUTHENTICATION)(self.get_user)
        hug.get('/userProfiles/{user_id}', api=self.api, requires=TOKEN_KEY_AUTHENTICATION)(self.get_user_profile)
        hug.patch('/userProfiles/{user_id}', api=self.api, requires=TOKEN_KEY_AUTHENTICATION)(self.patch_user_profile)
        hug.get('/people/{person_id}', api=self.api, requires=TOKEN_KEY_AUTHENTICATION)(self.get_person)
        hug.get('/people', api=self.api, requires=TOKEN_KEY_AUTHENTICATION)(self.people)
        hug.get('/boards/{board_id}', api=self.api, requires=TOKEN_KEY_AUTHENTICATION)(self.board)
        hug.get('/boards', api=self.api, requires=TOKEN_KEY_AUTHENTICATION)(self.get_boards)
        hug.get(
            '/reportedfeelings/boards/{board_id}/people/{person_id}/dates/{date}',
            api=self.api,
            requires=TOKEN_KEY_AUTHENTICATION)(self.get_reported_feeling)
        hug.post(
            '/reportedfeelings/boards/{board_id}/people/{person_id}/dates/{date}',
            api=self.api,
            requires=TOKEN_KEY_AUTHENTICATION)(self.create_reported_feeling)


def bootstrap_db():
    ''' Fill in the DB with initial data '''
    one_person = Person(person_id=1, label='Ann')
    other_person = Person(person_id=2, label='John')
    self.session.add(one_person)
    self.session.add(other_person)
    try:
        self.session.commit()
    except InvalidRequestError as exception:
        print(exception)
        self.session.rollback()
    one_user = User(
        user_id=1,
        name='John Smith',
        email='john@example.com',
        person_id=2,
        password_hash=bcrypt.hashpw(
            'whocares'.encode(),
            bcrypt.gensalt()).decode())
    self.session.add(one_user)
    try:
        self.session.commit()
    except InvalidRequestError as exception:
        print(exception)
        self.session.rollback()
    one_board = Board(board_id=1, label='Global board')
    one_board.people.append(one_person)
    one_board.people.append(other_person)
    self.session.add(one_board)
    another_board = Board(board_id=2, label='The A Team')
    another_board.people.append(one_person)
    another_board.people.append(other_person)
    self.session.add(another_board)
    and_a_third__board = Board(board_id=3, label='The Harlem Globetrotters')
    and_a_third__board.people.append(one_person)
    and_a_third__board.people.append(other_person)
    self.session.add(and_a_third__board)
    try:
        self.session.commit()
    except InvalidRequestError as exception:
        print(exception)
        self.session.rollback()


#--------------------------------------------------------

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
