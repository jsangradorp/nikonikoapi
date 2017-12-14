''' Generate JSON documentation from API definition '''
import json

import hug
from nikoniko.nikonikoapi import NikonikoAPI


NIKONIKOAPI = NikonikoAPI(
    hug.API(__name__),
    None,
    config=dict(
        secret_key='',
        mailconfig=dict(
            server=None,
            port=None,
            user=None,
            password=None,
            sender=None),
        logger=None
    ))
NIKONIKOAPI.setup()
print(
    json.dumps(
        NIKONIKOAPI.api.http.documentation(),
        sort_keys=True,
        indent=4))
