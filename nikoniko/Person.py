from Base import Base
from sqlalchemy import Column, Integer, String, Sequence


class Person(Base):
    __tablename__ = 'people'
    id = Column(Integer, Sequence('person_id_seq'), primary_key=True)
    name = Column(String(50))
    fullname = Column(String(50))
    password = Column(String(12))

    def __repr__(self):
        return "<Person(name='%s', fullname='%s', password='%s')>" % (
            self.name, self.fullname, self.password)
