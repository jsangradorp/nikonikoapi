import logging
from entities import Session, Person
from nikoniko import person
import nikoniko
import hug


logger = logging.getLogger(__name__)
session = Session()


class TestAPI(object):
    def test_person_returns_a_person(self):
        # Given
        # When
        person1 = Person("Julio")
        person2 = Person("Julio")
        # Then
        assert person1.label == person2.label

    def test_hug_tests(self):
        # Given
        person = Person("Andres")
        person.id = 25
        session = Session()
        session.add(person)
        session.commit()
        # import pdb; pdb.set_trace()
        response = hug.test.get(nikoniko, '/person', {'id': 25})  # Returns a Response object
        logger.info(response)
        assert(response.data == "Julio")
