from sqlalchemy import Column, Integer, String, Date, Sequence
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

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
    reported_feelings = relationship('ReportedFeeling')

    def __init__(self, label):
        self.label = label

    def __repr__(self):
        return "<Person(label='%s')>" % (self.label)


class Community(Base):
    __tablename__ = 'communities'
    id = Column(Integer, Sequence('community_id_seq'), primary_key=True)
    label = Column(String(50))

    people = relationship('Person', secondary=membership, back_populates='communities')
    reported_feelings = relationship('ReportedFeeling')

    def __repr__(self):
        return "<Community(label='%s')>" % (self.label)


class ReportedFeeling(Base):
    __tablename__ = 'reportedfeelings'
    person_id = Column(Integer, ForeignKey('people.id'), primary_key=True)
    community_id = Column(Integer, ForeignKey('communities.id'), primary_key=True)
    date = Column(Date, primary_key=True)
    feeling = Column(String(10))

    person = relationship('Person', back_populates='reported_feelings')
    community = relationship('Community', back_populates='reported_feelings')

    def __repr__(self):
        return "<ReportedFeeling(person_id='%s', community_id='%s', date='%s', feeling='%s')>" % (
            self.label,
            self.community_id,
            self.date,
            self.feeling)

Base.metadata.create_all(engine)
