import swisseph as swe
from datetime import datetime, timezone, timedelta
import math
from chart_engine.time_converter import TimeConverter
from chart_engine.astronomy_core import AstronomyCore
from chart_engine.coordinate_transformer import CoordinateTransformer, ZODIAC_ORDER
from chart_engine.models import PlanetName, ZodiacSign

class TransitEngine:
    @staticmethod
    def _normalize_utc(value: datetime, *, argument_name: str) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{argument_name} must be timezone-aware")
        return value.astimezone(timezone.utc)

    @staticmethod
    def _julian_day_ut(utc_instant: datetime) -> float:
        jd_epoch = 2440587.5
        unix_epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        return jd_epoch + (utc_instant - unix_epoch).total_seconds() / 86400.0

    @staticmethod
    def get_current_transit_data(reference_time: datetime | None = None) -> tuple[dict, dict]:
        """
        Calculates planetary transit signs for one explicit reference instant.

        Passing the reference time keeps a ChartState internally consistent:
        all time-dependent calculations are anchored to the same instant.
        """
        snapshot = TransitEngine.get_current_transit_snapshot(reference_time)
        return snapshot["signs"], snapshot["longitudes"]

    @staticmethod
    def get_current_transit_snapshot(reference_time: datetime | None = None) -> dict:
        """Return auditable transit sign/longitude/latitude/speed/flag maps."""
        now_utc = (
            datetime.now(timezone.utc)
            if reference_time is None
            else TransitEngine._normalize_utc(reference_time, argument_name="reference_time")
        )
        # Preserve the full reference instant rather than truncating it to whole seconds.
        jd_ut = TransitEngine._julian_day_ut(now_utc)

        # Get raw states (which automatically locks to Lahiri Sidereal in our config)
        raw_states = AstronomyCore.calculate_raw_state(jd_ut)

        # Transform to Astrological positions
        astrological_positions = CoordinateTransformer.transform_to_astrological(raw_states)

        transit_map = {}
        longitude_map = {}
        latitude_map = {}
        speed_map = {}
        ephemeris_flag_map = {}
        for name, pos in astrological_positions.items():
            transit_map[name.value] = pos.sign.value if hasattr(pos.sign, "value") else str(pos.sign)
            longitude_map[name.value] = pos.longitude_ecliptic
            latitude_map[name.value] = pos.latitude
            speed_map[name.value] = pos.speed
            ephemeris_flag_map[name.value] = raw_states[name].ephemeris_flags
        return {
            "reference_time_utc": now_utc,
            "julian_day_ut": jd_ut,
            "signs": transit_map,
            "longitudes": longitude_map,
            "latitudes": latitude_map,
            "speeds": speed_map,
            "ephemeris_flags": ephemeris_flag_map,
        }

    @staticmethod
    def get_current_transits(reference_time: datetime | None = None) -> dict:
        """Backwards-compatible sign-only view of current transit data."""
        transit_map, _ = TransitEngine.get_current_transit_data(reference_time)
        return transit_map

    @staticmethod
    def find_sign_ingresses(
        planet: str | PlanetName,
        start_utc: datetime,
        end_utc: datetime,
        *,
        sample_hours: float = 12.0,
        tolerance_seconds: float = 1.0,
    ) -> list[dict]:
        """Find sidereal rashi ingresses on (start_utc, end_utc].

        Uses explicit UTC samples and bisection, so the returned event times
        are reproducible. The 12-hour maximum step is deliberately shorter
        than the Moon's time to cross one 30-degree sign; callers cannot
        increase it and silently skip faster sign changes.
        """
        planet_name = planet.value if isinstance(planet, PlanetName) else str(planet)
        try:
            planet_key = PlanetName(planet_name)
        except ValueError as exc:
            raise ValueError(f"unknown transit planet: {planet_name}") from exc
        start = TransitEngine._normalize_utc(start_utc, argument_name="start_utc")
        end = TransitEngine._normalize_utc(end_utc, argument_name="end_utc")
        if end <= start:
            raise ValueError("end_utc must be later than start_utc")
        if not math.isfinite(sample_hours) or not 0.0 < sample_hours <= 12.0:
            raise ValueError("sample_hours must be finite and in (0, 12]")
        if not math.isfinite(tolerance_seconds) or not 0.01 <= tolerance_seconds <= 60.0:
            raise ValueError("tolerance_seconds must be finite and in [0.01, 60]")

        def state_at(instant: datetime) -> tuple[str, float]:
            utc_instant = TransitEngine._normalize_utc(instant, argument_name="instant")
            state = AstronomyCore.calculate_one_raw_state(
                TransitEngine._julian_day_ut(utc_instant), planet_key
            )
            sign_index = int(state.longitude_ecliptic // 30.0)
            return ZODIAC_ORDER[sign_index].value, state.longitude_ecliptic

        events: list[dict] = []
        left_time = start
        left_sign, _ = state_at(left_time)
        step = timedelta(hours=sample_hours)

        while left_time < end:
            right_time = min(left_time + step, end)
            right_sign, _ = state_at(right_time)
            if right_sign != left_sign:
                lo, hi = left_time, right_time
                while (hi - lo).total_seconds() > tolerance_seconds:
                    mid = lo + (hi - lo) / 2
                    mid_sign, _ = state_at(mid)
                    if mid_sign == left_sign:
                        lo = mid
                    else:
                        hi = mid

                ingress_sign, lon_after = state_at(hi)
                _, lon_before = state_at(lo)
                signed_delta = (lon_after - lon_before + 180.0) % 360.0 - 180.0
                events.append({
                    "planet": planet_key.value,
                    "ingress_time_utc": hi.isoformat().replace("+00:00", "Z"),
                    "from_sign": left_sign,
                    "to_sign": ingress_sign,
                    "direction": "direct" if signed_delta >= 0.0 else "retrograde",
                    "longitude_before_deg": lon_before,
                    "longitude_after_deg": lon_after,
                })

            left_time, left_sign = right_time, right_sign

        return events

    @staticmethod
    def find_gochar_house_ingresses(
        planet: str | PlanetName,
        natal_ascendant: str | ZodiacSign,
        start_utc: datetime,
        end_utc: datetime,
        *,
        sample_hours: float = 12.0,
        tolerance_seconds: float = 1.0,
    ) -> list[dict]:
        """Find whole-sign house ingresses relative to a natal Lagna."""
        ascendant = natal_ascendant.value if isinstance(natal_ascendant, ZodiacSign) else str(natal_ascendant)
        try:
            ascendant_index = next(i for i, sign in enumerate(ZODIAC_ORDER) if sign.value == ascendant)
        except StopIteration as exc:
            raise ValueError(f"unknown natal ascendant sign: {ascendant}") from exc
        events = TransitEngine.find_sign_ingresses(
            planet, start_utc, end_utc,
            sample_hours=sample_hours, tolerance_seconds=tolerance_seconds,
        )
        for event in events:
            sign_index = next(i for i, sign in enumerate(ZODIAC_ORDER) if sign.value == event["to_sign"])
            event["to_house_from_natal_ascendant"] = (sign_index - ascendant_index) % 12 + 1
        return events

    @staticmethod
    def find_stations(
        planet: str | PlanetName,
        start_utc: datetime,
        end_utc: datetime,
        *,
        sample_hours: float = 24.0,
        tolerance_seconds: float = 1.0,
    ) -> list[dict]:
        """Find longitude-speed zero crossings (direct/retrograde stations)."""
        planet_name = planet.value if isinstance(planet, PlanetName) else str(planet)
        try:
            planet_key = PlanetName(planet_name)
        except ValueError as exc:
            raise ValueError(f"unknown transit planet: {planet_name}") from exc
        start = TransitEngine._normalize_utc(start_utc, argument_name="start_utc")
        end = TransitEngine._normalize_utc(end_utc, argument_name="end_utc")
        if end <= start:
            raise ValueError("end_utc must be later than start_utc")
        if not math.isfinite(sample_hours) or not 0.0 < sample_hours <= 24.0:
            raise ValueError("sample_hours must be finite and in (0, 24]")
        if not math.isfinite(tolerance_seconds) or not 0.01 <= tolerance_seconds <= 60.0:
            raise ValueError("tolerance_seconds must be finite and in [0.01, 60]")

        def state_at(instant: datetime):
            utc_instant = TransitEngine._normalize_utc(instant, argument_name="instant")
            return AstronomyCore.calculate_one_raw_state(
                TransitEngine._julian_day_ut(utc_instant), planet_key
            )

        events: list[dict] = []
        left_time = start
        left_state = state_at(left_time)
        step = timedelta(hours=sample_hours)
        while left_time < end:
            right_time = min(left_time + step, end)
            right_state = state_at(right_time)
            left_sign = 1 if left_state.speed > 0.0 else -1 if left_state.speed < 0.0 else 0
            right_sign = 1 if right_state.speed > 0.0 else -1 if right_state.speed < 0.0 else 0
            if left_sign != 0 and right_sign != 0 and left_sign != right_sign:
                lo, hi = left_time, right_time
                for _ in range(64):
                    if (hi - lo).total_seconds() <= tolerance_seconds:
                        break
                    mid = lo + (hi - lo) / 2
                    mid_speed = state_at(mid).speed
                    mid_sign = 1 if mid_speed > 0.0 else -1 if mid_speed < 0.0 else 0
                    if mid_sign == left_sign:
                        lo = mid
                    else:
                        hi = mid
                station_state = state_at(hi)
                before_direction = "direct" if left_sign > 0 else "retrograde"
                after_direction = "direct" if right_sign > 0 else "retrograde"
                events.append({
                    "planet": planet_key.value,
                    "event": "station_retrograde" if after_direction == "retrograde" else "station_direct",
                    "station_time_utc": hi.isoformat().replace("+00:00", "Z"),
                    "direction_before": before_direction,
                    "direction_after": after_direction,
                    "longitude_deg": station_state.longitude_ecliptic,
                    "speed_before_deg_per_day": left_state.speed,
                    "speed_at_estimate_deg_per_day": station_state.speed,
                    "speed_after_deg_per_day": right_state.speed,
                    "ephemeris_flags": station_state.ephemeris_flags,
                    "time_tolerance_seconds": tolerance_seconds,
                })
            left_time, left_state = right_time, right_state
        return events

    @staticmethod
    def find_exact_contacts(
        planet1: str | PlanetName,
        planet2: str | PlanetName,
        angle_degrees: float,
        start_utc: datetime,
        end_utc: datetime,
        *,
        sample_hours: float = 12.0,
        tolerance_seconds: float = 1.0,
    ) -> list[dict]:
        """Find ecliptic-longitude exactitudes for a configured angle.

        Non-directional angles (for example 60, 90, 120 degrees) are checked
        on both sides of the circle. This reports geometric contacts only;
        traditional aspect sets and their meanings are left to an explicit
        caller profile.
        """
        names = []
        for body in (planet1, planet2):
            name = body.value if isinstance(body, PlanetName) else str(body)
            try:
                names.append(PlanetName(name))
            except ValueError as exc:
                raise ValueError(f"unknown transit planet: {name}") from exc
        first, second = names
        if first == second:
            raise ValueError("planet1 and planet2 must be different")
        if not math.isfinite(angle_degrees) or not 0.0 <= angle_degrees <= 180.0:
            raise ValueError("angle_degrees must be finite and in [0, 180]")

        start = TransitEngine._normalize_utc(start_utc, argument_name="start_utc")
        end = TransitEngine._normalize_utc(end_utc, argument_name="end_utc")
        if end <= start:
            raise ValueError("end_utc must be later than start_utc")
        if not math.isfinite(sample_hours) or not 0.0 < sample_hours <= 12.0:
            raise ValueError("sample_hours must be finite and in (0, 12]")
        if not math.isfinite(tolerance_seconds) or not 0.01 <= tolerance_seconds <= 60.0:
            raise ValueError("tolerance_seconds must be finite and in [0.01, 60]")

        def relative_at(instant: datetime) -> tuple[float, int]:
            jd_ut = TransitEngine._julian_day_ut(
                TransitEngine._normalize_utc(instant, argument_name="instant")
            )
            pos1 = AstronomyCore.calculate_one_raw_state(jd_ut, first)
            pos2 = AstronomyCore.calculate_one_raw_state(jd_ut, second)
            return (pos2.longitude_ecliptic - pos1.longitude_ecliptic) % 360.0, (
                pos1.ephemeris_flags | pos2.ephemeris_flags
            )

        oriented_angles = [angle_degrees]
        if 0.0 < angle_degrees < 180.0:
            oriented_angles.append(360.0 - angle_degrees)

        events: list[dict] = []
        left_time = start
        left_rel, _ = relative_at(left_time)
        left_unwrapped = left_rel
        step = timedelta(hours=sample_hours)
        while left_time < end:
            right_time = min(left_time + step, end)
            right_rel, right_flags = relative_at(right_time)
            delta = (right_rel - left_rel + 180.0) % 360.0 - 180.0
            right_unwrapped = left_unwrapped + delta
            low, high = sorted((left_unwrapped, right_unwrapped))

            targets = []
            for oriented_angle in oriented_angles:
                min_k = math.floor((low - oriented_angle) / 360.0) - 1
                max_k = math.ceil((high - oriented_angle) / 360.0) + 1
                for cycle in range(min_k, max_k + 1):
                    target = oriented_angle + 360.0 * cycle
                    if left_unwrapped < right_unwrapped:
                        crossed = left_unwrapped < target <= right_unwrapped
                    elif right_unwrapped < left_unwrapped:
                        crossed = right_unwrapped <= target < left_unwrapped
                    else:
                        crossed = False
                    if crossed:
                        targets.append((target, oriented_angle))

            for target_unwrapped, oriented_angle in sorted(
                targets, key=lambda item: item[0], reverse=left_unwrapped > right_unwrapped
            ):
                lo_time, hi_time = left_time, right_time
                lo_unwrapped = left_unwrapped
                lo_rel = left_rel
                ascending = right_unwrapped > left_unwrapped
                for _ in range(64):
                    if (hi_time - lo_time).total_seconds() <= tolerance_seconds:
                        break
                    mid_time = lo_time + (hi_time - lo_time) / 2
                    mid_rel, _ = relative_at(mid_time)
                    mid_unwrapped = lo_unwrapped + (mid_rel - lo_rel + 180.0) % 360.0 - 180.0
                    if (mid_unwrapped < target_unwrapped) == ascending:
                        lo_time, lo_unwrapped, lo_rel = mid_time, mid_unwrapped, mid_rel
                    else:
                        hi_time = mid_time

                event_rel, flags = relative_at(hi_time)
                oriented_target = oriented_angle % 360.0
                residual = (event_rel - oriented_target + 180.0) % 360.0 - 180.0
                events.append({
                    "planet1": first.value,
                    "planet2": second.value,
                    "event": "exact_longitude_contact",
                    "event_time_utc": hi_time.isoformat().replace("+00:00", "Z"),
                    "aspect_angle_deg": min(oriented_angle, 360.0 - oriented_angle),
                    "oriented_separation_deg": oriented_target,
                    "orientation": "ahead" if oriented_target <= 180.0 else "behind",
                    "longitude_residual_deg": residual,
                    "ephemeris_flags": flags | right_flags,
                    "time_tolerance_seconds": tolerance_seconds,
                })

            left_time, left_rel, left_unwrapped = right_time, right_rel, right_unwrapped

        events.sort(key=lambda event: event["event_time_utc"])
        return events
