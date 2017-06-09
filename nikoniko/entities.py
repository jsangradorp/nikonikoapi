from sqlalchemy import Column, Integer, String, Sequence
from sqlalchemy import Table, Text
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

membership = \
    Table(
        'membership',
        Base.metadata,
        Column('person_id',
               ForeignKey('people.id'),
               primary_key=True),
        Column('community_id',
               ForeignKey('communities.id'),
               primary_key=True))


class Person(Base):
    __tablename__ = 'people'
    id = Column(Integer, Sequence('person_id_seq'), primary_key=True)
    label = Column(String(50))

    communities = relationship('Community', secondary=membership, back_populates='people')

    def __repr__(self):
        return "<Person(label='%s')>" % (self.label)


class Community(Base):
    __tablename__ = 'communities'
    id = Column(Integer, Sequence('community_id_seq'), primary_key=True)
    label = Column(String(50))

    people = relationship('Person', secondary=membership, back_populates='communities')

    def __repr__(self):
        return "<Community(label='%s')>" % (self.label)

Base.metadata.create_all(engine)
