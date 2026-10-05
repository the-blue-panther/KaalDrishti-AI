import swisseph as swe
from datetime import datetime, timedelta, timezone
import pytz
import math

class TimeConverter:
    @staticmethod
    def julian_day_to_utc_datetime(jd_ut: float) -> datetime:
        """Convert UT Julian Day to a naive UTC datetime for legacy timeline APIs."""
        if not math.isfinite(float(jd_ut)):
            raise ValueError("jd_ut must be finite")
        year, month, day, hour = swe.revjul(float(jd_ut), swe.GREG_CAL)
        midnight = datetime(year, month, day)
        return midnight + timedelta(seconds=round(hour * 3600))

    @staticmethod
    def julian_day_to_local_datetime(jd_ut: float, timezone_str: str) -> datetime:
        """Convert UT Julian Day to an aware local datetime in an IANA zone."""
        utc_dt = TimeConverter.julian_day_to_utc_datetime(jd_ut).replace(tzinfo=timezone.utc)
        return utc_dt.astimezone(pytz.timezone(timezone_str))

    @staticmethod
    def utc_to_local_datetime(utc_dt: datetime, timezone_str: str) -> datetime:
        if utc_dt.tzinfo is None:
            raise ValueError("utc_dt must be timezone-aware")
        return utc_dt.astimezone(pytz.timezone(timezone_str))

    @staticmethod
    def utc_to_julian_day(utc_dt: datetime) -> float:
        """
        Converts a UTC datetime object tightly into the Universal Time Julian Day (JD).
        This is the mathematical root requirement by PySwissEph.
        """
        if utc_dt.tzinfo is None:
            raise ValueError("utc_dt must be timezone-aware")
        utc_dt = utc_dt.astimezone(timezone.utc)
        year = utc_dt.year
        month = utc_dt.month
        day = utc_dt.day
        hour_dec = utc_dt.hour + (utc_dt.minute / 60.0) + (utc_dt.second / 3600.0)

        # Calculate Julian Day in Universal Time (UT)
        jd_et, jd_ut = swe.utc_to_jd(year, month, day, int(utc_dt.hour), int(utc_dt.minute), utc_dt.second, swe.GREG_CAL)
        # ^ Note: swe.utc_to_jd returns (Ephemeris Time, Universal Time)
        return jd_ut

    @staticmethod
    def local_to_jd(local_dt_str: str, timezone_str: str) -> float:
        """
        Takes human readable local time input (e.g. '1990-12-01 10:30:00')
        and strict 'tz_database' timezone string (e.g. 'Europe/London')
        to extract the absolute Julian Day.
        """
        local_tz = pytz.timezone(timezone_str)
        local_dt = datetime.strptime(local_dt_str, "%Y-%m-%d %H:%M:%S")
        # Reject ambiguous/nonexistent wall times rather than silently choosing
        # one side of a DST transition and changing the historical chart.
        try:
            local_dt = local_tz.localize(local_dt, is_dst=None)
        except (pytz.AmbiguousTimeError, pytz.NonExistentTimeError) as exc:
            raise ValueError(f"ambiguous or nonexistent local birth time: {local_dt_str} in {timezone_str}") from exc
        utc_dt = local_dt.astimezone(pytz.UTC)
        return TimeConverter.utc_to_julian_day(utc_dt)
