"""
Provide an API to manage happiness logs (nikoniko) for teams
"""
import datetime

import hug
import jwt
import bcrypt
import logging

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import InvalidRequestError
from falcon import HTTP_404
from falcon import HTTP_401
from falcon import HTTP_403
from falcon import HTTP_204

from nikoniko.entities import User, USER_SCHEMA
from nikoniko.entities import USERPROFILE_SCHEMA
from nikoniko.entities import Person, PERSON_SCHEMA, PEOPLE_SCHEMA
from nikoniko.entities import Board, BOARD_SCHEMA, BOARDS_SCHEMA
from nikoniko.entities import ReportedFeeling, REPORTEDFEELING_SCHEMA
from nikoniko.entities import InvalidatedToken

from nikoniko.hug_middleware_cors import CORSMiddleware

NULL_LOGGER = logging.getLogger(__name__)
NULL_LOGGER.addHandler(logging.NullHandler())


def return_unauthorised(response, email, exception=None):
    ''' Update the response to mean unauthorised access '''
    response.status = HTTP_401
    return 'Invalid email and/or password for email: {} [{}]'.format(
        email, exception)


class NikonikoAPI:
    ''' Wrapper around hug API for initialization, testing, etc. '''
    def token_verify(self, token):
        ''' hug authentication token verification function '''
        self.logger.debug('Token: %s', token)
        try:
            decoded_token = jwt.decode(
                token, self.secret_key, algorithm='HS256')
            self.logger.debug('Decoded token: %s', decoded_token)
        except jwt.DecodeError:
            return False
        try:
            self.session.query(
                InvalidatedToken).filter_by(token=token).one()
            return False
        except NoResultFound:
            return decoded_token

    def hash_password(self, password):
        password_hash = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()).decode()
        return password_hash

    def checkpw(self, email, password):
        try:
            user = self.session.query(User).filter_by(email=email).one()
            return bcrypt.checkpw(password.encode(), user.password_hash.encode())
        except NoResultFound:
            return False

    def login(self, email: hug.types.text, password: hug.types.text, response):
        '''Authenticate and return a token'''
        try:
            if self.checkpw(email, password):
                user = self.session.query(User).filter_by(email=email).one()
                created = datetime.datetime.now()
                return {
                    'user': user.user_id,
                    'person': user.person_id,
                    'token': jwt.encode(
                        {
                            'user': user.user_id,
                            'created': created.isoformat(),
                            'exp':
                                (created +
                                 datetime.timedelta(days=1)).timestamp()
                        },
                        self.secret_key,
                        algorithm='HS256'
                    )}
            return return_unauthorised(response, email)
        except NoResultFound as exception:
            return return_unauthorised(response, email, exception)

    def update_password(  # pylint: disable=too-many-arguments
            self,
            user_id: hug.types.number,
            password: hug.types.text,
            request,
            response,
            authenticated_user: hug.directives.user):
        '''Updates a users' password '''
        try:
            found_user = self.session.query(
                User).filter_by(user_id=user_id).one()
        except NoResultFound as exception:
            self.logger.debug('User not found: %s', exception)
            response.status = HTTP_404
            return None
        self.logger.debug(
            'user_id: %s, authenticated_user: %s',
            user_id,
            authenticated_user)
        if user_id != authenticated_user['user']:
            response.status = HTTP_401
            return ('Authenticated user isn\'t allowed to update'
                ' the password for requested user')
        found_user.password_hash = self.hash_password(password)
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
        self.logger.debug(
            'Authenticated user reported: %s', authenticated_user)
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
        self.logger.debug(
            'Authenticated user reported: %s', authenticated_user)
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
        self.logger.debug(
            'Authenticated user reported: %s', authenticated_user)
        self.logger.debug('Token: %s', request.headers['AUTHORIZATION'])
        try:
            found_user = self.session.query(
                User).filter_by(user_id=user_id).one()
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
            found_user.password_hash = self.hash_password(password)
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
            res = self.session.query(
                Person).filter_by(person_id=person_id).one()
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
                            ReportedFeeling.person_id ==
                            person.person_id).all()
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

    def __init__(
            self,
            api,
            session,
            secret_key,
            logger=NULL_LOGGER):
        self.api = api
        self.session = session
        self.secret_key = secret_key
        self.logger = logger

    def setup(self):
        self.setup_cors()
        self.setup_endpoints()

    def setup_cors(self):
        self.api.http.add_middleware(CORSMiddleware(self.api))

    def setup_endpoints(self):
        hug.post('/login', api=self.api)(self.login)
        token_key_authentication = \
            hug.authentication.token(  # pylint: disable=no-value-for-parameter
                self.token_verify)
        hug.put(
            '/password/{user_id}',
            api=self.api,
            requires=token_key_authentication)(self.update_password)
        hug.get(
            '/users/{user_id}',
            api=self.api,
            requires=token_key_authentication)(self.get_user)
        hug.get(
            '/userProfiles/{user_id}',
            api=self.api,
            requires=token_key_authentication)(self.get_user_profile)
        hug.patch(
            '/userProfiles/{user_id}',
            api=self.api,
            requires=token_key_authentication)(self.patch_user_profile)
        hug.get(
            '/people/{person_id}',
            api=self.api,
            requires=token_key_authentication)(self.get_person)
        hug.get(
            '/people',
            api=self.api,
            requires=token_key_authentication)(self.people)
        hug.get(
            '/boards/{board_id}',
            api=self.api,
            requires=token_key_authentication)(self.board)
        hug.get(
            '/boards',
            api=self.api,
            requires=token_key_authentication)(self.get_boards)
        hug.get(
            ('/reportedfeelings/boards/{board_id}'
             '/people/{person_id}/dates/{date}'),
            api=self.api,
            requires=token_key_authentication)(self.get_reported_feeling)
        hug.post(
            ('/reportedfeelings/boards/{board_id}'
             '/people/{person_id}/dates/{date}'),
            api=self.api,
            requires=token_key_authentication)(self.create_reported_feeling)