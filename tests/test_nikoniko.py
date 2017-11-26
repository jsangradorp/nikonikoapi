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
def person():
    TESTSESSION.expunge_all()
    person = Person(
        person_id=1,
        label='Julio')
    TESTSESSION.add(person)
    TESTSESSION.commit()
    return person


@pytest.mark.usefixtures("empty_db", "api", "person")
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

    def test_get_specific_person(self, person, api):
        # Given
        response = StartResponseMock()
        # When
        result = api.get_person(person.person_id, response)
        # Then
        assert(result == {
            "person_id": person.person_id,
            "label": person.label
        })
        # When
        result = api.get_person(-1, response)
        # Then
        assert response.status == HTTP_404
        assert result is None

    def test_get_all_people(self):
        # Given
        delete_db_tables()
        person1 = Person(label=self.personLabel1)
        person2 = Person(label=self.personLabel2)
        TESTSESSION.add(person1)
        TESTSESSION.add(person2)
        TESTSESSION.commit()
        id1 = person1.person_id
        id2 = person2.person_id
        # When
        response = hug.test.get(  # pylint: disable=no-member
            TESTAPI,
            '/people',
            headers={'Authorization': TOKEN})
        # Then
        assert(response.data == [
            {
                "person_id": id1,
                "label": self.personLabel1
            },
            {
                "person_id": id2,
                "label": self.personLabel2
            }
        ])

    def test_get_specific_board(self):
        # Given
        delete_db_tables()
        person1 = Person(label=self.personLabel1)
        board1 = Board(label=self.boardLabel1)
        board1.people.append(person1)
        TESTSESSION.add(board1)
        TESTSESSION.commit()
        id1 = board1.board_id
        pid1 = person1.person_id
        # When
        response = hug.test.get(  # pylint: disable=no-member
            TESTAPI,
            '/boards/{}'.format(id1),
            headers={'Authorization': TOKEN})
        # Then
        assert(response.data == {
            "board_id": id1,
            "label": self.boardLabel1,
            "people": [
                {
                    "person_id": pid1,
                    "label": self.personLabel1,
                    "reportedfeelings": []
                }
            ]
        })
        # When
        response = hug.test.get(  # pylint: disable=no-member
            TESTAPI,
            '/boards/-1',
            headers={'Authorization': TOKEN})
        # Then
        assert response.status == HTTP_404

    def test_get_all_boards(self):
        # Given
        delete_db_tables()
        person1 = Person(label=self.personLabel1)
        person2 = Person(label=self.personLabel2)
        board1 = Board(label=self.boardLabel1)
        board1.people.append(person1)
        board1.people.append(person2)
        TESTSESSION.add(board1)
        board2 = Board(label=self.boardLabel2)
        TESTSESSION.add(board2)
        TESTSESSION.commit()
        id1 = board1.board_id
        pid1 = person1.person_id
        pid2 = person2.person_id
        id2 = board2.board_id
        # When
        response = hug.test.get(  # pylint: disable=no-member
            TESTAPI,
            '/boards',
            headers={'Authorization': TOKEN})
        # Then
        assert(response.data == [
            {
                "board_id": id1,
                "label": self.boardLabel1,
                "people": [
                    {
                        "person_id": pid1,
                        "label": self.personLabel1
                    },
                    {
                        "person_id": pid2,
                        "label": self.personLabel2
                    }
                ]
            },
            {
                "board_id": id2,
                "label": self.boardLabel2,
                "people": [
                ]
            }
        ])
