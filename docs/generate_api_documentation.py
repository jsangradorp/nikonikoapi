''' Generate JSON documentation from API definition '''
import json

import hug
from nikoniko.nikonikoapi import NikonikoAPI


NIKONIKOAPI = NikonikoAPI(
    hug.API(__name__),
    None,
    None,
    None)
NIKONIKOAPI.setup()
print(
    json.dumps(
        NIKONIKOAPI.api.http.documentation(),
        sort_keys=True,
        indent=4))
