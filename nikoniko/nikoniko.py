import hug
import logging
from sqlalchemy.orm import aliased
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from User import User
from Base import Base


logger = logging.getLogger(__name__)


def person(id):
    return {"id": id}

if __name__ == '__main__':
    engine = create_engine('sqlite:///:memory:', echo=True);
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    print("Hello")
    print(User.__table__.__dict__)
    ed_user = User(name='ed', fullname='Ed Jones', password='edspassword')
    print(ed_user)
    session = Session()
    session.add(ed_user)
    print("Eo")
    our_user = session.query(User).filter_by(name='ed').first()
    print(our_user)
    print(ed_user is our_user)
    session.add_all([
	User(name='wendy', fullname='Wendy Williams', password='foobar'),
	User(name='mary', fullname='Mary Contrary', password='xxg527'),
	User(name='fred', fullname='Fred Flinstone', password='blah')])
    ed_user.password = 'f8s7ccs'
    print(session.dirty)
    session.commit()
    print(ed_user.id)
    # rolling back
    ed_user.name = 'Edwardo'
    fake_user = User(name='fakeuser', fullname='Invalid', password='12345')
    session.add(fake_user)
    print(session.query(User).filter(User.name.in_(['Edwardo', 'fakeuser'])).all())
    session.rollback()
    print(ed_user.name)
    print(fake_user in session)
    print(session.query(User).filter(User.name.in_(['ed', 'fakeuser'])).all())
    # Queries
    for instance in session.query(User).order_by(User.id):
        print(instance.name, instance.fullname)
    for name, fullname in session.query(User.name, User.fullname):
        print(name, fullname)
    for row in session.query(User, User.name).all():
        print(row.User, row.name)
    for row in session.query(User.name.label('name_label')).all():
        print(row.name_label)
    user_alias = aliased(User, name='user_alias')
    for row in session.query(user_alias, user_alias.name).all():
        print(row.user_alias)
    for u in session.query(User).order_by(User.id)[1:3]:
        print(u)
    for name, in session.query(User.name).filter_by(fullname='Ed Jones'):
        print(name)
    for name, in session.query(User.name).filter(User.fullname=='Ed Jones'):
        print(name)
    for user in session.query(User).filter(User.name=='ed').filter(User.fullname=='Ed Jones'):
        print(user)
