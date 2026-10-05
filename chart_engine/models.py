from pydantic import BaseModel, ConfigDict
from enum import Enum

class PlanetName(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"
    RAHU = "Rahu"
    KETU = "Ketu"

class ZodiacSign(str, Enum):
    ARIES = "Aries"
    TAURUS = "Taurus"
    GEMINI = "Gemini"
    CANCER = "Cancer"
    LEO = "Leo"
    VIRGO = "Virgo"
    LIBRA = "Libra"
    SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN = "Capricorn"
    AQUARIUS = "Aquarius"
    PISCES = "Pisces"

class RawAstronomicalState(BaseModel):
    """
    Represents the mathematical truth coordinates of a Planet at an exact Julian Day.
    Frozen immutability prevents any downstream system from accidentally altering core math.
    """
    model_config = ConfigDict(frozen=True)
    planet_id: int
    name: PlanetName
    longitude_ecliptic: float
    latitude: float
    speed: float
    ephemeris_flags: int = 0

class AstrologicalPosition(BaseModel):
    """
    Represents the derived astrological state built from RawAstronomicalState.

    This model is immutable so downstream consumers cannot silently mutate the
    canonical positional facts after chart construction.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: PlanetName
    longitude_ecliptic: float
    latitude: float
    speed: float
    sign: ZodiacSign
    house_number: int
    nakshatra_index: int
    nakshatra_pada: int
    is_retrograde: bool
