import logging

import hug
import json
from sqlalchemy.orm import aliased

from nikoniko.entities import Session, Person, person_schema

logger = logging.getLogger(__name__)
session = Session()


@hug.get('/person/{id}')
def person(id: hug.types.number):
    '''Returns a person'''
    res = session.query(Person).filter_by(id=id).one()
    result = person_schema.dump(res)
    return json.dumps(result.data)

