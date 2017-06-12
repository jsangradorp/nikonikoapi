from entities import Person


def test_person_returns_a_person():
    # Given
    # When
    person1 = Person("Julio")
    person2 = Person("Julio")
    # Then
    assert person1.label == person2.label
