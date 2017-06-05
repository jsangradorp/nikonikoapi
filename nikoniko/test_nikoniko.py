from .nikoniko import person


def test_person_returns_a_person():
    assert person(1) == {"id": 1}
