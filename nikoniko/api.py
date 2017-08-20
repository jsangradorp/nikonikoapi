import logging
import datetime

import os
import hug
import jwt
import bcrypt
from sqlalchemy.orm import aliased
from falcon import HTTP_404
from falcon import HTTP_401
from falcon import HTTP_204

from nikoniko.entities import Session
from nikoniko.entities import User, user_schema, users_schema
from nikoniko.entities import Person, person_schema, people_schema
from nikoniko.entities import Board, board_schema, boards_schema
from nikoniko.entities import ReportedFeeling, reportedfeeling_schema
from nikoniko.entities import reportedfeelings_schema

from nikoniko.hug_middleware_cors import CORSMiddleware

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
session = Session()

secret_key = os.environ['JWT_SECRET_KEY']  # may purposefully throw exception

api = hug.API(__name__)
api.http.add_middleware(CORSMiddleware(api))


@hug.post('/login')
def login(email: hug.types.text, password: hug.types.text, response):
    '''Authenticate and return a token'''
    try:
        user = session.query(User).filter_by(email=email).one()
    except:
        response.status = HTTP_401
        return 'Invalid email and/or password for email: {0}'.format(email)
    if (bcrypt.checkpw(password.encode(), user.password_hash.encode())):
        created = datetime.datetime.now()
        return {
            'user': user.user_id,
            'person': user.person_id,
            'token': jwt.encode(
                {
                    'user': user.user_id,
                    'created': created.isoformat(),
                    'exp': (created + datetime.timedelta(days=1)).timestamp()
                },
                secret_key,
                algorithm='HS256'
            )}
    else:
        response.status = HTTP_401
        return 'Invalid email and/or password for email: {0}'.format(email)


def token_verify(token):
    try:
        return jwt.decode(token, secret_key, algorithm='HS256')
    except jwt.DecodeError:
        return False


token_key_authentication = \
    hug.authentication.token(  # pylint: disable=no-value-for-parameter
        token_verify)


@hug.put('/password/{user_id}', requires=token_key_authentication)
def password(user_id: hug.types.number, password: hug.types.text, response, authenticated_user: hug.directives.user):
    '''Update a users' password '''
    try:
        found_user = session.query(User).filter_by(user_id=user_id).one()
    except:
        response.status = HTTP_404
        return None
    logger.debug('user_id: {}, authenticated_user: {}'.format(user_id, authenticated_user))
    if user_id != authenticated_user['user']:
        response.status = HTTP_401
        return 'Authenticated user isn\'t allowed to update the password for requested user'
    found_user.password_hash=bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()).decode()
    session.add(found_user)
    session.commit()
    response.status = HTTP_204


@hug.get('/users/{user_id}', requires=token_key_authentication)
def user(user_id: hug.types.number, response, user: hug.directives.user):
    '''Returns a user'''
    logger.debug('Authenticated user reported: {}'.format(user))
    try:
        res = session.query(User).filter_by(user_id=user_id).one()
        boards = session.query(
            Board).join(
                Person.boards).filter(
                    Person.id == res.person_id).all()
        res.boards = boards
    except Exception as e:
        response.status = HTTP_404
        return None
    return user_schema.dump(res).data


@hug.get('/people/{id}', requires=token_key_authentication)
def person(id: hug.types.number, response, user: hug.directives.user):
    '''Returns a person'''
    try:
        res = session.query(Person).filter_by(id=id).one()
    except:
        response.status = HTTP_404
        return None
    return person_schema.dump(res).data


@hug.get('/people', requires=token_key_authentication)
def people():
    '''Returns all the people'''
    res = session.query(Person).all()
    return people_schema.dump(res).data


@hug.get('/boards/{id}', requires=token_key_authentication)
def board(id: hug.types.number, response):
    '''Returns a board'''
    try:
        res = session.query(Board).filter_by(id=id).one()
        for person in res.people:
            reportedfeelings = session.query(
                ReportedFeeling).filter(
                    ReportedFeeling.board_id == id).filter(
                        ReportedFeeling.person_id == person.id).all()
            person.reportedfeelings = reportedfeelings
    except:
        response.status = HTTP_404
        return None
    return board_schema.dump(res).data


@hug.get('/boards', requires=token_key_authentication)
def boards():
    '''Returns all boards'''
    res = session.query(Board).all()
    return boards_schema.dump(res).data


@hug.get(
    '/reportedfeelings/boards/{board_id}/people/{person_id}/dates/{date}',
    requires=token_key_authentication)
def get_reportedFeeling(
        board_id: hug.types.number,
        person_id: hug.types.number,
        date: hug.types.text,
        response):
    '''Returns a specific reported feeling for a board, person and date'''
    try:
        res = session.query(ReportedFeeling).filter_by(
            board_id=board_id,
            person_id=person_id,
            date=date).one()
    except:
        response.status = HTTP_404
        return None
    return reportedfeeling_schema.dump(res).data


@hug.post(
    '/reportedfeelings/boards/{board_id}/people/{person_id}/dates/{date}',
    requires=token_key_authentication)
def create_reportedFeeling(
        board_id: hug.types.number,
        person_id: hug.types.number,
        feeling: hug.types.text,
        date: hug.types.text):
    '''Creates a new reportedFeeling'''
    try:
        reportedFeeling = session.query(ReportedFeeling).filter_by(
            board_id=board_id,
            person_id=person_id,
            date=date).one()
        reportedFeeling.feeling = feeling
    except:
        reportedFeeling = ReportedFeeling(
            person_id=person_id,
            board_id=board_id,
            date=datetime.datetime.strptime(
                date,
                "%Y-%m-%d").date(),
            feeling=feeling)
        session.add(reportedFeeling)
    session.commit()
    return reportedfeeling_schema.dump(reportedFeeling).data


def bootstrap_db():
    one_person = Person(id=1, label='Ann')
    other_person = Person(id=2, label='John')
    session.add(one_person)
    session.add(other_person)
    try:
        session.commit()
    except Exception as e:
        print(e)
        session.rollback()
    one_user = User(
        user_id=1,
        name='John Smith',
        email='john@example.com',
        person_id=2,
        password_hash=bcrypt.hashpw(
            'whocares'.encode(),
            bcrypt.gensalt()).decode())
    session.add(one_user)
    try:
        session.commit()
    except Exception as e:
        print(e)
        session.rollback()
    one_board = Board(id=1, label='Global board')
    one_board.people.append(one_person)
    one_board.people.append(other_person)
    session.add(one_board)
    another_board = Board(id=2, label='The A Team')
    another_board.people.append(one_person)
    another_board.people.append(other_person)
    session.add(another_board)
    and_a_third__board = Board(id=3, label='The Harlem Globetrotters')
    and_a_third__board.people.append(one_person)
    and_a_third__board.people.append(other_person)
    session.add(and_a_third__board)
    try:
        session.commit()
    except Exception as e:
        print(e)
        session.rollback()


if os.getenv('DO_BOOTSTRAP_DB', 'false').lower() in [
        'yes', 'y', 'true', 't', '1']:
    logger.info('Bootstrapping DB')
    bootstrap_db()
