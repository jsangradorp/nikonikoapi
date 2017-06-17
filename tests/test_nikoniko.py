from .context import nikoniko
import logging
from nikoniko.entities import Session, Person
from nikoniko.api import person
import nikoniko.api
import hug
import json
import pytest
import sqlalchemy

logger = logging.getLogger(__name__)
session = Session()


class TestAPI(object):

    personLabel1 = "Julio"
    personLabel2 = "Andres"

    def test_person_returns_a_person(self):
        # Given
        # When
        person1 = Person(self.personLabel1)
        person2 = Person(self.personLabel1)
        # Then
        assert person1.label == person2.label

    def test_hug_tests_are_working(self):
        # Given
        person = Person(self.personLabel1)
        session.add(person)
        session.commit()
        id = person.id
        # When
        response = hug.test.get(nikoniko.api, '/person/{}'.format(id))  # Returns a Response object
        # Then
        assert(json.loads(response.data) == {"id": id, "label": self.personLabel1})
        # Then
        with pytest.raises(sqlalchemy.orm.exc.NoResultFound):
            response = hug.test.get(nikoniko.api, '/person/-1')  # Returns a Response object
