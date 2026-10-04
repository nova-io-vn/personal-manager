from datetime import date, datetime, time, timezone


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_timezone():
    return datetime.now().astimezone().tzinfo


def utc_to_local(value: datetime) -> datetime:
    aware = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return aware.astimezone(local_timezone())


def to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def local_day_utc_bounds(day: date) -> tuple[datetime, datetime]:
    zone = local_timezone()
    start = datetime.combine(day, time.min, tzinfo=zone).astimezone(timezone.utc).replace(tzinfo=None)
    end = datetime.combine(day, time.max, tzinfo=zone).astimezone(timezone.utc).replace(tzinfo=None)
    return start, end
