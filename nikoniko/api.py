import hug
import logging
from nikoniko.entities import Session, Person
from sqlalchemy.orm import aliased


logger = logging.getLogger(__name__)
session = Session()


@hug.get('/person')
def person(id: hug.types.number):
    '''Returns a person'''
    return session.query(Person).filter(id == id).one().label

if __name__ == '__main__':
    print("Hello")
    print(Person.__table__.__dict__)
    ed_person = Person(label='ed')
    print(ed_person)
    session.add(ed_person)
    print("Eo")
    our_person = session.query(Person).filter_by(label='ed').first()
    print(our_person)
    print(ed_person is our_person)
    session.add_all([
        Person(label='wendy'),
        Person(label='mary'),
        Person(label='fred')])
    print(session.dirty)
    session.commit()
    print(ed_person.id)
    # rolling back
    ed_person.label = 'Edwardo'
    fake_person = Person(label='fakeperson')
    session.add(fake_person)
    print(session.query(Person).filter(Person.label.in_(['ed', 'fakeperson'])).all())
    session.rollback()
    print(ed_person.label)
    print(fake_person in session)
    print(session.query(Person).filter(Person.label.in_(['ed', 'fakeperson'])).all())
    # Queries
    for instance in session.query(Person).order_by(Person.id):
        print(instance.label)
    for label in session.query(Person.label):
        print(label)
    for row in session.query(Person, Person.label).all():
        print(row.Person, row.label)
    for row in session.query(Person.label.label('name_label')).all():
        print(row.name_label)
    person_alias = aliased(Person, name='person_alias')
    for row in session.query(person_alias, person_alias.label).all():
        print(row.person_alias)
    for u in session.query(Person).order_by(Person.id)[1:3]:
        print(u)
    for name, in session.query(Person.label).filter_by(label='ed'):
        print(name)
    for name, in session.query(Person.label).filter(Person.label == 'ed'):
        print(name)
    for person in session.query(Person).filter(Person.label == 'ed').filter(Person.label == 'ed'):
        print(person)
