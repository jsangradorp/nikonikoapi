''' Test the nikoniko package '''
import logging
import datetime
import os
import hug
import jwt

from nikoniko.entities import DB, Person, \
        Board, ReportedFeeling, User, MEMBERSHIP
from nikoniko.nikonikoapi import NikonikoAPI

from falcon import HTTP_404

from .context import nikoniko


SECRET_KEY = os.environ['JWT_SECRET_KEY']  # may purposefully throw exception
TOKEN = jwt.encode(
    {
        'user': 1,
        'created': datetime.datetime.now().isoformat()
    },
    SECRET_KEY,
    algorithm='HS256'
).decode()


TESTLOGGER = logging.getLogger(__name__)
TESTDB = DB('sqlite:///:memory:', echo=False)
TESTDB.create_all()
TESTSESSION = TESTDB.session()
TESTENGINE = TESTDB.engine
TESTAPI = hug.API(__name__)

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


class TestAPI(object):
    ''' API testing class '''
    personLabel1 = "Julio"
    personLabel2 = "Marc"
    boardLabel1 = "Daganzo"
    boardLabel2 = "Sabadell"

    def test_get_specific_person(self):
        ''' test getting a specific person '''
        # Given
        delete_db_tables()
        person = Person(label=self.personLabel1)
        TESTSESSION.add(person)
        TESTSESSION.commit()
        person_id = person.person_id
        # When
        response = hug.test.get(  # pylint: disable=no-member
            TESTAPI,
            '/people/{}'.format(person_id),
            headers={'Authorization': TOKEN})
        # Then
        assert(response.data == {
            "person_id": person_id,
            "label": self.personLabel1
        })
        # Then
        response = hug.test.get(  # pylint: disable=no-member
            TESTAPI,
            '/people/-1',
            headers={'Authorization': TOKEN})
        assert response.status == HTTP_404

    def test_get_all_people(self):
        ''' test getting all people '''
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

    def test_get_board(self):
        ''' test getting a specific board '''
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

    def test_get_all_boards(self):
        ''' test getting all boards '''
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
