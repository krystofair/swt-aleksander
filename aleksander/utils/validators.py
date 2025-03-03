"""
    Validators fields
    ~~~~~~~~~~~~~~~~~
    Store here all validators to not do mess in domain models,
    which should present interface in tidy way.
"""
import re
from datetime import datetime, timedelta

from aleksander import exc


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
        raise ValueError(f"Value of season does not fulfill requirement: {value}")
        # raise exc.BuildModelException(portal='sofascore', field=attribute.name, prototype=instance.json())

def now_is_after_3h_since_it(instance, attribute, value):
    """
        Validate if start datetime is after 3h from when happend.
        So if current time is after `value` with 3h offset.
        With assumption that no event will be last longer that 3 hours.
    """
    starttime_plus_3h = value + timedelta(hours=3)
    #: Value should be in datetime type already.
    if starttime_plus_3h > datetime.now():
        raise exc.FeatureNotImplemented(
            feature="future events",
            message="In according to my logic, event has not ended yet.")
