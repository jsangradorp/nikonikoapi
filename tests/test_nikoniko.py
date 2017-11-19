''' Test the nikoniko package '''
import logging
import datetime
import os
import hug
import jwt

from nikoniko.entities import ENGINE, SESSION, Person, Board, \
        ReportedFeeling, User, MEMBERSHIP
import nikoniko.api

from falcon import HTTP_404

from .context import nikoniko


LOGGER = logging.getLogger(__name__)
SESSION = SESSION()


SECRET_KEY = os.environ['JWT_SECRET_KEY']  # may purposefully throw exception

TOKEN = jwt.encode(
    {
        'user': 1,
        'created': datetime.datetime.now().isoformat()
    },
    SECRET_KEY,
    algorithm='HS256'
).decode()


def delete_db_tables():
    ''' Delete all DB tables '''
    ENGINE.execute(
        MEMBERSHIP.delete())  # pylint: disable=no-value-for-parameter
    ENGINE.execute(User.__table__.delete())
    ENGINE.execute(ReportedFeeling.__table__.delete())
    ENGINE.execute(Person.__table__.delete())
    ENGINE.execute(Board.__table__.delete())


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
        SESSION.add(person)
        SESSION.commit()
        person_id = person.person_id
        # When
        response = hug.test.get(  # pylint: disable=no-member
            nikoniko.api,
            '/people/{}'.format(person_id),
            headers={'Authorization': TOKEN})
        # Then
        assert(response.data == {
            "person_id": person_id,
            "label": self.personLabel1
        })
        # Then
        response = hug.test.get(  # pylint: disable=no-member
            nikoniko.api,
            '/people/-1',
            headers={'Authorization': TOKEN})
        assert response.status == HTTP_404

    def test_get_all_people(self):
        ''' test getting all people '''
        # Given
        delete_db_tables()
        person1 = Person(label=self.personLabel1)
        person2 = Person(label=self.personLabel2)
        SESSION.add(person1)
        SESSION.add(person2)
        SESSION.commit()
        id1 = person1.person_id
        id2 = person2.person_id
        # When
        response = hug.test.get(  # pylint: disable=no-member
            nikoniko.api,
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
        SESSION.add(board1)
        SESSION.commit()
        id1 = board1.board_id
        pid1 = person1.person_id
        # When
        response = hug.test.get(  # pylint: disable=no-member
            nikoniko.api,
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
        SESSION.add(board1)
        board2 = Board(label=self.boardLabel2)
        SESSION.add(board2)
        SESSION.commit()
        id1 = board1.board_id
        pid1 = person1.person_id
        pid2 = person2.person_id
        id2 = board2.board_id
        # When
        response = hug.test.get(  # pylint: disable=no-member
            nikoniko.api,
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
