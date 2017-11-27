''' Test the nikoniko package '''
import logging
import datetime
import os
import pytest

import bcrypt
import hug
import jwt

from falcon import HTTP_401
from falcon import HTTP_404
from falcon.testing import StartResponseMock

from nikoniko.entities import DB, Person, \
        Board, ReportedFeeling, User, MEMBERSHIP
from nikoniko.entities import InvalidatedToken
from nikoniko.nikonikoapi import NikonikoAPI

from .context import nikoniko


TESTLOGGER = logging.getLogger(__name__)
TESTDB = DB('sqlite:///:memory:', echo=False)
TESTDB.create_all()
TESTSESSION = TESTDB.session()
TESTENGINE = TESTDB.engine
TESTAPI = hug.API(__name__)

SECRET_KEY = os.environ['JWT_SECRET_KEY']  # may purposefully throw exception
TOKEN_OBJECT = {
    'user': 1,
    'created': datetime.datetime.now().isoformat()
}
TOKEN = jwt.encode(
    TOKEN_OBJECT,
    SECRET_KEY,
    algorithm='HS256'
).decode()

NIKONIKOAPI = NikonikoAPI(TESTAPI, TESTSESSION, SECRET_KEY, TESTLOGGER)
NIKONIKOAPI.setup()


def delete_db_tables():
    ''' Delete all DB tables '''
    TESTENGINE.execute(
        MEMBERSHIP.delete())  # pylint: disable=no-value-for-parameter
    TESTENGINE.execute(User.__table__.delete())
    TESTENGINE.execute(ReportedFeeling.__table__.delete())
    TESTENGINE.execute(Person.__table__.delete())
    TESTENGINE.execute(Board.__table__.delete())
    TESTENGINE.execute(InvalidatedToken.__table__.delete())


@pytest.fixture()
def empty_db():
    delete_db_tables()


@pytest.fixture()
def api():
    TESTSESSION.expunge_all()
    return NikonikoAPI(
            api=TESTAPI,
            session=TESTSESSION,
            secret_key=SECRET_KEY,
            logger=TESTLOGGER
            )


@pytest.fixture()
def person1():
    person = Person(
        person_id=1,
        label='Julio')
    TESTSESSION.add(person)
    TESTSESSION.commit()
    return person


@pytest.fixture()
def person2():
    person = Person(
        person_id=2,
        label='Marc')
    TESTSESSION.add(person)
    TESTSESSION.commit()
    return person


@pytest.fixture()
def board1(person1):
    board = Board(
        board_id=1,
        label='Daganzo')
    board.people.append(person1)
    TESTSESSION.add(board)
    TESTSESSION.commit()
    return board


@pytest.fixture()
def board2():
    board = Board(
        board_id=2,
        label='Sabadell')
    TESTSESSION.add(board)
    TESTSESSION.commit()
    return board


@pytest.mark.usefixtures("empty_db", "api", "person1", "board1")
class TestAPI(object):
    personLabel1 = "Julio"
    personLabel2 = "Marc"
    boardLabel1 = "Daganzo"
    boardLabel2 = "Sabadell"

    def test_login_ok(self, api):
        # Given
        valid_user = User(
                user_id=1,
                name='John Smith',
                email='john@example.com',
                person_id=2,
                password_hash=bcrypt.hashpw(
                    'whocares'.encode(),
                    bcrypt.gensalt()
                    ).decode()
                )
        TESTSESSION.add(valid_user)
        TESTSESSION.commit()
        # When
        login = api.login('john@example.com', 'whocares', None)
        # Then
        decoded_token = jwt.decode(
            login['token'], api.secret_key, algorithm='HS256')
        assert decoded_token['user'] == 1
        assert decoded_token['created'] is not None
        assert decoded_token['exp'] is not None

    def test_login_bad_user(self, api):
        # Given
        response = StartResponseMock()
        # When
        login = api.login('inexistent@example.com', 'whocares', response)
        # Then
        assert login == ('Invalid email and/or password for email: '
                         'inexistent@example.com [No row was found for one()]')
        assert response.status == HTTP_401

    def test_login_bad_password(self, api):
        # Given
        valid_user = User(
                user_id=1,
                name='John Smith',
                email='john@example.com',
                person_id=2,
                password_hash=bcrypt.hashpw(
                    'whocares'.encode(),
                    bcrypt.gensalt()
                    ).decode()
                )
        TESTSESSION.add(valid_user)
        TESTSESSION.commit()
        response = StartResponseMock()
        # When
        login = api.login('john@example.com', 'wrongpassword', response)
        # Then
        assert login == ('Invalid email and/or password for email: '
                         'john@example.com [None]')
        assert response.status == HTTP_401

    def test_valid_token(self, api):
        # Given
        valid_token = TOKEN
        # When
        decoded_token = api.token_verify(valid_token)
        # Then
        assert decoded_token == TOKEN_OBJECT

    def test_invalidated_token(self, api):
        # Given
        valid_token = TOKEN
        invalidated = InvalidatedToken(
            token=TOKEN, timestamp_invalidated=datetime.datetime.now())
        TESTSESSION.add(invalidated)
        TESTSESSION.commit()
        # When
        decoded_token = api.token_verify(valid_token)
        # Then
        assert decoded_token is False

    def test_invalid_token(self, api):
        # Given
        invalid_token = '#### INVALID TOKEN ####'
        # When
        decoded_token = api.token_verify(invalid_token)
        # Then
        assert decoded_token is False

    def test_get_specific_person(self, person1, api):
        # Given
        response = StartResponseMock()
        # When
        result = api.get_person(person1.person_id, response)
        # Then
        assert(result == {
            "person_id": person1.person_id,
            "label": person1.label
        })
        # When
        result = api.get_person(-1, response)
        # Then
        assert response.status == HTTP_404
        assert result is None

    def test_get_all_people(self, person2, person1, api):
        # When
        result = api.people()
        # Then
        assert(result == [
            {
                "person_id": person1.person_id,
                "label": person1.label
            },
            {
                "person_id": person2.person_id,
                "label": person2.label
            }
        ])

    def test_get_specific_board(self, api, board1, person1):
        # Given
        response = StartResponseMock()
        # When
        result = api.board(board1.board_id, response)
        # Then
        assert(result == {
            "board_id": board1.board_id,
            "label": board1.label,
            "people": [
                {
                    "person_id": person1.person_id,
                    "label": person1.label,
                    "reportedfeelings": []
                }]
        })
        # When
        result = api.board(-1, response)
        # Then
        assert response.status == HTTP_404
        assert result is None

    def test_get_all_boards(self, api, board1, board2, person1):
        # Given
        response = StartResponseMock()
        # When
        result = api.get_boards()
        # Then
        assert(result == [
            {
                "board_id": board1.board_id,
                "label": board1.label,
                "people": [
                    {
                        "person_id": person1.person_id,
                        "label": person1.label
                    }]
            },
            {
                "board_id": board2.board_id,
                "label": board2.label,
                "people": []
            }
        ])
