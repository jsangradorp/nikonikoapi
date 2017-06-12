import logging
from entities import Person
from nikoniko.nikoniko import person
import hug


logger = logging.getLogger(__name__)


def test_person_returns_a_person():
    # Given
    # When
    person1 = Person("Julio")
    person2 = Person("Julio")
    # Then
    assert person1.label == person2.label


def test_hug_tests():
    response = hug.test.get(person, 'happy_birthday', {'name': 'Timothy', 'age': 25})  # Returns a Response object
    logger.info(response)
    assert(response is None)
