import logging

import hug
import json
from sqlalchemy.orm import aliased

from nikoniko.entities import Session, Person, person_schema, people_schema

logger = logging.getLogger(__name__)
session = Session()


@hug.get('/people')
def people():
    '''Returns all the people'''
    res = session.query(Person).all()
    return json.dumps(people_schema.dump(res).data)


@hug.get('/people/{id}')
def person(id: hug.types.number):
    '''Returns a person'''
    res = session.query(Person).filter_by(id=id).one()
    return json.dumps(person_schema.dump(res).data)
