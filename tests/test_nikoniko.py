from .context import nikoniko
import logging
from nikoniko.entities import engine
from nikoniko.entities import Session, Person, Board
from nikoniko.api import person, people
import nikoniko.api
import hug
import json
import pytest
import sqlalchemy

logger = logging.getLogger(__name__)
session = Session()


class TestAPI(object):

    personLabel1 = "Julio"
    personLabel2 = "Marc"
    boardLabel1 = "Daganzo"
    boardLabel2 = "Sabadell"

    def test_get_specific_person(self):
        # Given
        engine.execute(Board.__table__.delete())
        engine.execute(Person.__table__.delete())
        person = Person(self.personLabel1)
        session.add(person)
        session.commit()
        id = person.id
        # When
        response = hug.test.get(nikoniko.api, '/people/{}'.format(id))
        # Then
        assert(json.loads(response.data) == {"id": id, "label": self.personLabel1})
        # Then
        with pytest.raises(sqlalchemy.orm.exc.NoResultFound):
            response = hug.test.get(nikoniko.api, '/people/-1')

    def test_get_people(self):
        # Given
        engine.execute(Board.__table__.delete())
        engine.execute(Person.__table__.delete())
        person1 = Person(self.personLabel1)
        person2 = Person(self.personLabel2)
        session.add(person1)
        session.add(person2)
        session.commit()
        id1 = person1.id
        id2 = person2.id
        # When
        response = hug.test.get(nikoniko.api, '/people')
        # Then
        assert(json.loads(response.data) == [{"id": id1, "label": self.personLabel1}, {"id": id2, "label": self.personLabel2}])

    def test_get_board(self):
        # Given
        engine.execute(Board.__table__.delete())
        engine.execute(Person.__table__.delete())
        person1 = Person(self.personLabel1)
        board1 = Board(label=self.boardLabel1)
        board1.people.append(person1)
        session.add(board1)
        session.commit()
        id1 = board1.id
        pid1 = person1.id
        # When
        response = hug.test.get(nikoniko.api, '/boards/{}'.format(id1))
        # Then
        assert(response.data == {
            "id": id1,
            "label": self.boardLabel1,
            "people": [
                {
                    "id": pid1,
                    "label": self.personLabel1
                }
            ]
        })
