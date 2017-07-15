import logging
import datetime

import hug
import jwt
from sqlalchemy.orm import aliased
from falcon import HTTP_404

from nikoniko.entities import Session
from nikoniko.entities import Person, person_schema, people_schema
from nikoniko.entities import Board, board_schema, boards_schema
from nikoniko.entities import ReportedFeeling, reportedfeeling_schema, reportedfeelings_schema

from nikoniko.hug_middleware_cors import CORSMiddleware

logger = logging.getLogger(__name__)
session = Session()

api = hug.API(__name__)
api.http.add_middleware(CORSMiddleware(api))


@hug.post('/login')
def login(username: hug.types.text, password: hug.types.text):
    '''Authenticate and return a token'''
    secret_key = 'super-secret-key-please-change'
    mockusername = 'admin'
    mockpassword = 'root'
    if mockpassword == password and mockusername == username: # This is an example. Don't do that.
        created = datetime.datetime.now()
        return {
            'user': 1,
            'token' : jwt.encode(
                {
                    'user': 1,
                    'created': created.isoformat(),
                    'exp': (created + datetime.timedelta(days=1)).timestamp()
                },
                secret_key,
                algorithm='HS256'
            )}
    return 'Invalid username and/or password for user: {0}'.format(username)


def token_verify(token):
    secret_key = 'super-secret-key-please-change'
    try:
        return jwt.decode(token, secret_key, algorithm='HS256')
    except jwt.DecodeError:
        return False


token_key_authentication = hug.authentication.token(token_verify)


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
        '/reportedfeelings/boards/{board_id}/people/{person_id}/date/{date}',
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
                        date=date
                        ).one()
    except:
        response.status = HTTP_404
        return None
    return reportedfeeling_schema.dump(res).data


@hug.post(
        '/reportedfeelings/boards/{board_id}/people/{person_id}/date/{date}',
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
                                    date=date
                                    ).one()
        reportedFeeling.feeling = feeling
    except:
        reportedFeeling = ReportedFeeling(
                            person_id=person_id,
                            board_id=board_id,
                            date=datetime.datetime.strptime(
                                date,
                                "%Y-%m-%d"
                                ).date(),
                            feeling=feeling
                            )
        session.add(reportedFeeling)
    session.commit()
    return reportedfeeling_schema.dump(reportedFeeling).data


def bootstrap_db():
    one_person = Person(id=1, label='Admin')
    session.add(one_person)
    try:
        session.commit()
    except:
        session.rollback()
    one_user = User(user_id=1, name='Administrator', email='admin@example.com', person_id=1, password_hash='')
    session.add(one_user)
    try:
        session.commit()
    except:
        session.rollback()
    one_board = Board(id=1, label='Global board')
    session.add(one_board)
    try:
        session.commit()
    except:
        session.rollback()


bootstrap_db()
