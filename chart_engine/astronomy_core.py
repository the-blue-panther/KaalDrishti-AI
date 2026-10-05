import swisseph as swe
import threading
from chart_engine.models import PlanetName, RawAstronomicalState

_EPHEMERIS_LOCK = threading.RLock()

# PySwissEph constant mapping
PLANET_MAP = {
    PlanetName.SUN: swe.SUN,
    PlanetName.MOON: swe.MOON,
    PlanetName.MARS: swe.MARS,
    PlanetName.MERCURY: swe.MERCURY,
    PlanetName.JUPITER: swe.JUPITER,
    PlanetName.VENUS: swe.VENUS,
    PlanetName.SATURN: swe.SATURN,
    PlanetName.RAHU: swe.MEAN_NODE, # Mean Node is classically heavily used for Vedic
}

class AstronomyCore:
    @staticmethod
    def calculate_raw_state(jd_ut: float) -> dict[PlanetName, RawAstronomicalState]:
        """
        Executes the computationally heavy swe.calc_ut for all classical planets ONCE.
        Calculations use Sidereal geometry guaranteed by core_config.py.
        """
        # Swiss Ephemeris keeps sidereal mode in process-global state. Set it
        # at the calculation boundary, not only during module import, because
        # another library in the same Python process may have changed it.
        with _EPHEMERIS_LOCK:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            raw_state_cache = {}

            for name, swe_id in PLANET_MAP.items():
                # FLG_SWIEPH may fall back to Moshier where data files are unavailable.
                flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
                result, ret_flag = swe.calc_ut(jd_ut, swe_id, flags)
                lon, lat, _dist, speed_lon, _speed_lat, _speed_dist = result
                raw_state_cache[name] = RawAstronomicalState(
                    planet_id=swe_id,
                    name=name,
                    longitude_ecliptic=lon,
                    latitude=lat,
                    speed=speed_lon,
                    ephemeris_flags=ret_flag,
                )

        # Ketu is geometrically the exact diametric opposite of Rahu (180 degrees)
        rahu_lon = raw_state_cache[PlanetName.RAHU].longitude_ecliptic
        ketu_lon = (rahu_lon + 180.0) % 360.0

        raw_state_cache[PlanetName.KETU] = RawAstronomicalState(
            planet_id=-1,
            name=PlanetName.KETU,
            longitude_ecliptic=ketu_lon,
            latitude=0.0,
            speed=raw_state_cache[PlanetName.RAHU].speed,
            ephemeris_flags=raw_state_cache[PlanetName.RAHU].ephemeris_flags,
        )

        return raw_state_cache

    @staticmethod
    def calculate_one_raw_state(jd_ut: float, name: PlanetName) -> RawAstronomicalState:
        """Calculate one Lahiri sidereal position for efficient transit searches."""
        if name not in PLANET_MAP and name != PlanetName.KETU:
            raise ValueError(f"unsupported ephemeris body: {name}")
        swe_id = swe.MEAN_NODE if name == PlanetName.KETU else PLANET_MAP[name]
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
        with _EPHEMERIS_LOCK:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            result, ret_flag = swe.calc_ut(jd_ut, swe_id, flags)
        lon, lat, _dist, speed_lon, _speed_lat, _speed_dist = result
        if name == PlanetName.KETU:
            lon = (lon + 180.0) % 360.0
            lat = 0.0
        return RawAstronomicalState(
            planet_id=-1 if name == PlanetName.KETU else swe_id,
            name=name,
            longitude_ecliptic=lon,
            latitude=lat,
            speed=speed_lon,
            ephemeris_flags=ret_flag,
        )
