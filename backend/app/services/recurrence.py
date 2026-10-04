import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.time import to_utc_naive
from app.models.calendar import RepeatType, Schedule


@dataclass(frozen=True)
class ScheduleOccurrence:
    schedule: Schedule
    start: datetime
    end: datetime


def _add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def expand_occurrences(
    schedule: Schedule,
    range_start: datetime,
    range_end: datetime,
) -> list[ScheduleOccurrence]:
    start = to_utc_naive(schedule.start_datetime)
    end = to_utc_naive(schedule.end_datetime)
    window_start = to_utc_naive(range_start)
    window_end = to_utc_naive(range_end)
    if window_end <= window_start:
        return []
    duration = end - start
    repeat_until = to_utc_naive(schedule.repeat_until) if schedule.repeat_until else None
    occurrences: list[ScheduleOccurrence] = []
    index = 0
    while True:
        if schedule.repeat_type == RepeatType.NONE:
            occurrence_start = start
        elif schedule.repeat_type == RepeatType.DAILY:
            occurrence_start = start + timedelta(days=index)
        elif schedule.repeat_type == RepeatType.WEEKLY:
            occurrence_start = start + timedelta(weeks=index)
        else:
            occurrence_start = _add_months(start, index)
        if repeat_until is not None and occurrence_start > repeat_until:
            break
        if occurrence_start >= window_end:
            break
        occurrence_end = occurrence_start + duration
        if occurrence_end > window_start:
            occurrences.append(ScheduleOccurrence(schedule, occurrence_start, occurrence_end))
        if schedule.repeat_type == RepeatType.NONE:
            break
        index += 1
    return occurrences


def expand_schedule_range(
    schedules: list[Schedule],
    range_start: datetime,
    range_end: datetime,
) -> list[ScheduleOccurrence]:
    occurrences = [
        occurrence
        for schedule in schedules
        for occurrence in expand_occurrences(schedule, range_start, range_end)
    ]
    return sorted(occurrences, key=lambda occurrence: (occurrence.start, occurrence.schedule.id))
