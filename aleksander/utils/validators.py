"""
    Validators fields
    ~~~~~~~~~~~~~~~~~
    Store here all validators to not do mess in domain models,
    which should present interface in tidy way.
"""
import re

# from .. import exc


def match_season_format(instance, attribute, value):
    
    #: Cannot do backreference here, thats why.
    # hint: year = r'\d{4}'; short_year = r'\d{2}'
    pattern = r"(\d{2}|\d{4}){1}\/?(\d{2}|\d{4})?$"
    if not isinstance(value, str):
        #: as TypeError
        raise TypeError(f"Value of season has wrong type: {value.__class__}")
        # raise exc.BuildModelException(portal='sofascore', field=attribute.name, prototype=instance.json())
    if not re.match(pattern, value.strip()):
        #: as ValueError
        raise ValueError(f"Value of season does not fulfil requirement: {value}")
        # raise exc.BuildModelException(portal='sofascore', field=attribute.name, prototype=instance.json())