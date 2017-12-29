''' Test the nikoniko package '''
import logging
import datetime
import os
from unittest.mock import patch
from smtplib import SMTPException

import pytest

import bcrypt
import hug
import jwt

from falcon import HTTP_401
from falcon import HTTP_404
from falcon import HTTP_409
from falcon import Request
from falcon.testing import StartResponseMock, create_environ
from sqlalchemy.exc import InvalidRequestError, OperationalError

from nikoniko.entities import DB, Person, \
        Board, ReportedFeeling, User, MEMBERSHIP
from nikoniko.entities import InvalidatedToken
from nikoniko.nikonikoapi import NikonikoAPI, check_password

TESTLOGGER = logging.getLogger(__name__)
TESTDB = DB('sqlite:///:memory:', echo=False)
TESTDB.create_all()
TESTSESSION = TESTDB.session()
TESTENGINE = TESTDB.engine
TESTAPI = hug.API(__name__)
TESTMAILER = dict(
    server=None,
    port=None,
    user=None,
    password=None,
    sender=None)

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

TESTCONFIG = dict(
    secret_key=SECRET_KEY,
    mailconfig=TESTMAILER,
    logger=TESTLOGGER)

NIKONIKOAPI = NikonikoAPI(
    TESTAPI,
    TESTSESSION,
    TESTCONFIG)
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
        config=dict(
            secret_key=SECRET_KEY,
            mailconfig=TESTMAILER,
            logger=TESTLOGGER))


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


@pytest.fixture()
def user1():
    user = User(
        user_id=1,
        name='Bob Brown',
        email='bob@example.com',
        person_id=2,
        password_hash=bcrypt.hashpw(
            'onepassword'.encode(),
            bcrypt.gensalt()
            )
        )
    TESTSESSION.add(user)
    TESTSESSION.commit()
    return user


@pytest.fixture()
def user2():
    user = User(
        user_id=2,
        name='Alice Brown',
        email='alice@example.com',
        person_id=1,
        password_hash=bcrypt.hashpw(
            'whocares'.encode(),
            bcrypt.gensalt()
            )
        )
    TESTSESSION.add(user)
    TESTSESSION.commit()
    return user


@pytest.fixture()
def reportedfeeling1(board1, person1):
    reportedfeeling = ReportedFeeling(
        board_id=board1.board_id,
        person_id=person1.person_id,
        date=datetime.datetime.strptime('2017-11-27', '%Y-%m-%d'),
        feeling='a-feeling'
    )
    TESTSESSION.add(reportedfeeling)
    TESTSESSION.commit()
    return reportedfeeling


@pytest.fixture()
def authenticated_user(user1):
    return {"user": user1.user_id}


@pytest.mark.usefixtures("empty_db", "api", "person1", "board1", "user1",
                         "user2", "authenticated_user", "monkeypatch",
                         "mocker")
class TestAPI(object):  # pylint: disable=no-self-use
    personLabel1 = "Julio"
    personLabel2 = "Marc"
    boardLabel1 = "Daganzo"
    boardLabel2 = "Sabadell"

    def test_connection_retry(self, monkeypatch):
        # Given
        # When
        monkeypatch.setattr('time.sleep', lambda x: None)
        # Then
        with pytest.raises(OperationalError):
            DB('postgresql://postgres@127.0.0.1:1/nodb', echo=False)

    def test_login_ok(self, api, user1):
        # Given
        # When
        login = api.login(user1.email, 'onepassword', None)
        # Then
        decoded_token = jwt.decode(
            login['token'], api.secret_key, algorithm='HS256')
        assert decoded_token['user'] == user1.user_id
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

    def test_login_bad_password(self, api, user1):
        # Given
        response = StartResponseMock()
        # When
        login = api.login(user1.email, 'wrongpassword', response)
        # Then
        assert login == ('Invalid email and/or password for email: '
                         'bob@example.com [None]')
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

    def test_get_specific_user(self, api, user1):
        # Given
        response = StartResponseMock()
        # When
        result = api.get_user(user1.user_id, response, None)
        # Then
        assert(result == {
            "user_id": user1.user_id,
            "name": user1.name,
            "email": user1.email,
            "person": user1.person,
            "boards": []
        })
        # When
        result = api.get_user(-1, response, None)
        # Then
        assert response.status == HTTP_404
        assert result is None

    def test_get_specific_user_profile(self, api, user1):
        # Given
        response = StartResponseMock()
        # When
        result = api.get_user_profile(user1.user_id, response, None)
        # Then
        assert(result == {
            "user_id": user1.user_id,
            "name": user1.name,
            "email": user1.email
        })
        # When
        result = api.get_user_profile(-1, response, None)
        # Then
        assert response.status == HTTP_404
        assert result is None

    def test_create_reported_feeling(self, api, board1, person1):
        # When
        result = api.create_reported_feeling(
            board1.board_id,
            person1.person_id,
            "good",
            "2017-12-01"
            )
        # Then
        assert result == {
            "board_id": board1.board_id,
            "person_id": person1.person_id,
            "feeling": "good",
            "date": "2017-12-01"
            }
        # When
        result = api.create_reported_feeling(
            board1.board_id,
            person1.person_id,
            "bad",
            "2017-12-01"
            )
        # Then
        assert result == {
            "board_id": board1.board_id,
            "person_id": person1.person_id,
            "feeling": "bad",
            "date": "2017-12-01"
            }

    def test_get_all_boards(self, api, board1, board2, person1):
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

    def test_get_reportedfeeling(self, api, reportedfeeling1):
        # Given
        response = StartResponseMock()
        # When
        result = api.get_reported_feeling(
            reportedfeeling1.board_id,
            reportedfeeling1.person_id,
            '2017-11-27',
            response)
        # Then
        assert result == {
            "board_id": reportedfeeling1.board_id,
            "person_id": reportedfeeling1.person_id,
            "date": "2017-11-27",
            "feeling": "a-feeling"
            }
        # When
        result = api.get_reported_feeling(
            reportedfeeling1.board_id,
            reportedfeeling1.person_id,
            '2038-01-01',
            response)
        # Then
        assert response.status == HTTP_404
        assert result is None

    def test_update_password(self, api, user1, user2, authenticated_user):
        # Given
        response = StartResponseMock()
        request = Request(create_environ(headers={'AUTHORIZATION': 'XXXX'}))
        # When
        result = api.update_password(
            user1.user_id,
            "newpassword",
            request,
            response,
            authenticated_user)
        # Then
        user = TESTSESSION.query(User).filter_by(user_id=user1.user_id).one()
        assert check_password(user, "newpassword") is True
        # When
        result = api.update_password(
            -1,
            "newpassword",
            request,
            response,
            authenticated_user)
        # Then
        assert response.status == HTTP_404
        assert result is None
        # When
        result = api.update_password(
            user2.user_id,
            "newpassword",
            request,
            response,
            authenticated_user)
        # Then
        assert response.status == HTTP_401
        assert result == ("Authenticated user isn't allowed to update the"
                          " password for requested user")

    def test_update_password_with_code(self, api, user1, mocker):
        code = ''

        def sendmail_trap(*args):
            nonlocal code
            code = args[1]  # pylint: disable=unused-variable
            return
        # Given
        response = StartResponseMock()
        mocker.patch.object(api, 'sendmail', sendmail_trap)
        api.password_reset_code(user1.email)
        # When
        result = api.update_password_with_code(
            code,
            "newpassword",
            response)
        # Then
        user = TESTSESSION.query(User).filter_by(user_id=user1.user_id).one()
        assert check_password(user, "newpassword") is True
        # When
        result = api.update_password_with_code(
            '12345678-1234-5678-1234-567812345678',
            "newpassword",
            response)
        # Then
        assert response.status == HTTP_409
        assert result == 'Invalid password reset code'
        # When
        result = api.update_password_with_code(
            'Invalid UUID string',
            "newpassword",
            response)
        # Then
        assert response.status == HTTP_409
        assert result == 'Invalid password reset code'

    def test_patch_user_profile(  # pylint: disable=too-many-arguments
            self,
            api,
            user1,
            user2,
            authenticated_user,
            mocker):
        # Given
        response = StartResponseMock()
        request = Request(create_environ(headers={'AUTHORIZATION': 'XXXX'}))
        # When
        result = api.patch_user_profile(
            user1.user_id,
            "newname",
            "newpassword",
            request,
            response,
            authenticated_user)
        # Then
        assert result == {
            "user_id": user1.user_id,
            "name": "newname",
            "email": "bob@example.com"
            }
        # When
        result = api.patch_user_profile(
            -1,
            "newname",
            "newpassword",
            request,
            response,
            authenticated_user)
        # Then
        assert response.status == HTTP_404
        assert result is None
        # When
        result = api.patch_user_profile(
            user2.user_id,
            "newname",
            "newpassword",
            request,
            response,
            authenticated_user)
        # Then
        assert response.status == HTTP_401
        assert result == ("Authenticated user isn't allowed to update the"
                          " profile for requested user")
        # When
        mocker.patch.object(api.session, 'commit')
        api.session.commit.side_effect = InvalidRequestError()
        result = api.patch_user_profile(
            user1.user_id,
            "newname",
            "newpassword",
            request,
            response,
            authenticated_user)
        # Then
        assert result == 'User profile not updated'

    @patch('nikoniko.nikonikoapi.SMTP_SSL')
    def test_password_reset_code(  # pylint: disable=unused-argument
            self,
            smtp_mock,
            api,
            user1,
            mocker):
        # Given
        mocker.spy(api, 'email_password_reset_code')
        mocker.spy(api.logger, 'error')
        # When
        api.password_reset_code("another@example.com")
        # Then
        assert (
            api.email_password_reset_code  # pylint: disable=no-member
            .call_count == 0)
        # When
        api.password_reset_code(user1.email)
        # Then
        assert (
            api.email_password_reset_code  # pylint: disable=no-member
            .call_count == 1)
        # When
        smtp_mock.side_effect = SMTPException()
        api.password_reset_code(user1.email)
        # Then
        assert (
            api.email_password_reset_code  # pylint: disable=no-member
            .call_count == 2)
        assert (
            api.logger.error.call_count == 1)
