import hug
import logging
from sqlalchemy.orm import aliased
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from Person import Person
from Base import Base


logger = logging.getLogger(__name__)


def person(id):
    return {"id": id}

if __name__ == '__main__':
    engine = create_engine('sqlite:///:memory:', echo=True)
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    print("Hello")
    print(Person.__table__.__dict__)
    ed_person = Person(name='ed', fullname='Ed Jones', password='edspassword')
    print(ed_person)
    session = Session()
    session.add(ed_person)
    print("Eo")
    our_person = session.query(Person).filter_by(name='ed').first()
    print(our_person)
    print(ed_person is our_person)
    session.add_all([
        Person(name='wendy', fullname='Wendy Williams', password='foobar'),
        Person(name='mary', fullname='Mary Contrary', password='xxg527'),
        Person(name='fred', fullname='Fred Flinstone', password='blah')])
    ed_person.password = 'f8s7ccs'
    print(session.dirty)
    session.commit()
    print(ed_person.id)
    # rolling back
    ed_person.name = 'Edwardo'
    fake_person = Person(name='fakeperson', fullname='Invalid', password='12345')
    session.add(fake_person)
    print(session.query(Person).filter(Person.name.in_(['Edwardo', 'fakeperson'])).all())
    session.rollback()
    print(ed_person.name)
    print(fake_person in session)
    print(session.query(Person).filter(Person.name.in_(['ed', 'fakeperson'])).all())
    # Queries
    for instance in session.query(Person).order_by(Person.id):
        print(instance.name, instance.fullname)
    for name, fullname in session.query(Person.name, Person.fullname):
        print(name, fullname)
    for row in session.query(Person, Person.name).all():
        print(row.Person, row.name)
    for row in session.query(Person.name.label('name_label')).all():
        print(row.name_label)
    person_alias = aliased(Person, name='person_alias')
    for row in session.query(person_alias, person_alias.name).all():
        print(row.person_alias)
    for u in session.query(Person).order_by(Person.id)[1:3]:
        print(u)
    for name, in session.query(Person.name).filter_by(fullname='Ed Jones'):
        print(name)
    for name, in session.query(Person.name).filter(Person.fullname == 'Ed Jones'):
        print(name)
    for person in session.query(Person).filter(Person.name == 'ed').filter(Person.fullname == 'Ed Jones'):
        print(person)
