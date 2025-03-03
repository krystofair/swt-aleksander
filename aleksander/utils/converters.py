import datetime


def read_datetime(dt):
    if isinstance(dt, datetime.datetime):
        return dt
    elif isinstance(dt, str):
        try:
            return datetime.datetime.fromisoformat(dt)
        except ValueError:
            try:
                return datetime.datetime.fromtimestamp(float(dt))
            except: pass
    elif isinstance(dt, (int, float)):
        try:
            return datetime.datetime.fromtimestamp(float(dt))
        except: pass
    raise ValueError("Cannot parse timestamp")

