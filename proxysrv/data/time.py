import calendar
from datetime import UTC, date, datetime, timedelta
from typing import Final


class Time:
    """Utilities for working with Unix timestamps and UTC calendar dates.

    All timestamps are integer seconds since the Unix epoch (1970-01-01 UTC).
    Calendar calculations use UTC, and weeks begin on Monday.

    Period-ending methods return the beginning of the next period, preserving
    the original API's exclusive-end convention.
    """

    SECONDS_IN_MINUTE: Final[int] = 60
    SECONDS_IN_HOUR: Final[int] = 3_600
    SECONDS_IN_DAY: Final[int] = 86_400
    SECONDS_IN_WEEK: Final[int] = 604_800

    _EPOCH: Final[date] = date(1970, 1, 1)

    @staticmethod
    def _utc_today() -> date:
        """Return today's date in UTC."""
        return datetime.now(UTC).date()

    @staticmethod
    def _date_from_timestamp(timestamp: int | float) -> date:
        """Convert a Unix timestamp to a UTC calendar date."""
        return datetime.fromtimestamp(timestamp, UTC).date()

    @staticmethod
    def _timestamp_from_datetime(value: datetime) -> int:
        """Convert a datetime to an integer Unix timestamp."""
        return calendar.timegm(value.utctimetuple())

    @staticmethod
    def now() -> int:
        """Return the current Unix timestamp in UTC."""
        return int(datetime.now(UTC).timestamp())

    @staticmethod
    def end_of_today() -> int:
        """Return the Unix timestamp for the beginning of tomorrow in UTC."""
        tomorrow = Time._utc_today() + timedelta(days=1)
        return calendar.timegm(tomorrow.timetuple())

    @staticmethod
    def beginning_of_today() -> int:
        """Return the Unix timestamp for the beginning of today in UTC."""
        today = Time._utc_today()
        return calendar.timegm(today.timetuple())

    @staticmethod
    def end_of_this_week() -> int:
        """Return the Unix timestamp for the beginning of next week in UTC."""
        today = Time._utc_today()
        monday = today - timedelta(days=today.weekday())
        next_monday = monday + timedelta(weeks=1)
        return calendar.timegm(next_monday.timetuple())

    @staticmethod
    def beginning_of_this_week() -> int:
        """Return the Unix timestamp for the beginning of this week in UTC."""
        today = Time._utc_today()
        monday = today - timedelta(days=today.weekday())
        return calendar.timegm(monday.timetuple())

    @staticmethod
    def end_of_this_month() -> int:
        """Return the Unix timestamp for the beginning of next month in UTC."""
        today = Time._utc_today()
        return Time.timestamp_from_date(today.year, today.month + 1)

    @staticmethod
    def beginning_of_this_month() -> int:
        """Return the Unix timestamp for the beginning of this month in UTC."""
        today = Time._utc_today()
        first_day = date(today.year, today.month, 1)
        return calendar.timegm(first_day.timetuple())

    @staticmethod
    def todays_date() -> list[int]:
        """Return today's UTC date as [year, month, day]."""
        today = Time._utc_today()
        return [today.year, today.month, today.day]

    @staticmethod
    def yesterdays_date() -> list[int]:
        """Return yesterday's UTC date as [year, month, day]."""
        yesterday = Time._utc_today() - timedelta(days=1)
        return [yesterday.year, yesterday.month, yesterday.day]

    @staticmethod
    def week_in_days_since_epoch(timestamp: int | None = None) -> int:
        """Return the epoch-relative day number of the week's Monday.

        If a timestamp is provided, calculate the result for that timestamp
        instead of the current date. The Unix epoch's date is day zero.
        """
        current_date = (
            Time._utc_today()
            if timestamp is None
            else Time._date_from_timestamp(timestamp)
        )
        monday = current_date - timedelta(days=current_date.weekday())
        return (monday - Time._EPOCH).days

    @staticmethod
    def days_into_year(timestamp: int | None = None) -> list[int]:
        """Return [year, day_of_year], with January 1 represented as day 1."""
        current_date = (
            Time._utc_today()
            if timestamp is None
            else Time._date_from_timestamp(timestamp)
        )
        return [current_date.year, current_date.timetuple().tm_yday]

    @staticmethod
    def days_into_month(timestamp: int | None = None) -> int:
        """Return the day of the month, starting at 1."""
        current_date = (
            Time._utc_today()
            if timestamp is None
            else Time._date_from_timestamp(timestamp)
        )
        return current_date.day

    @staticmethod
    def days_into_week(timestamp: int | None = None) -> int:
        """Return the weekday index: Monday is 0 and Sunday is 6."""
        current_date = (
            Time._utc_today()
            if timestamp is None
            else Time._date_from_timestamp(timestamp)
        )
        return current_date.weekday()

    @staticmethod
    def timestamp_from_date(
        year: int,
        month: int = 1,
        day: int = 1,
    ) -> int:
        """Return the UTC Unix timestamp for a given year, month, and day.

        The month supports out-of-range indexing. For example, month 13
        represents January of the following year, and month 0 represents
        December of the preceding year.
        """
        year_offset, normalized_month = divmod(month - 1, 12)
        year += year_offset
        month = normalized_month + 1

        value = datetime(year, month, day, tzinfo=UTC)
        return calendar.timegm(value.utctimetuple())

    @staticmethod
    def date_from_timestamp(timestamp: int) -> list[int]:
        """Return a UTC date as [year, month, day]."""
        value = Time._date_from_timestamp(timestamp)
        return [value.year, value.month, value.day]

    @staticmethod
    def format(timestamp: int, formatstr: str) -> str:
        """Format a Unix timestamp as a string using UTC."""
        return datetime.fromtimestamp(timestamp, UTC).strftime(formatstr)
