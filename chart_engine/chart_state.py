from datetime import datetime
from typing import Any

from pydantic import model_validator

from pydantic import BaseModel, ConfigDict, Field

from chart_engine.models import AstrologicalPosition, PlanetName, RawAstronomicalState, ZodiacSign


CHART_STATE_SCHEMA_VERSION = "1.4"


class FrozenDict(dict):
    """Recursively immutable dict that remains JSON/Pydantic serializable."""

    def _blocked(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("immutable mapping")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = _blocked

    def __ior__(self, other: Any):
        self._blocked()


def _deep_freeze(value: Any) -> Any:
    """Freeze nested mappings/sequences without breaking Pydantic JSON serialization."""
    if isinstance(value, dict):
        return FrozenDict({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_deep_freeze(item) for item in value)
    return value


class BirthContext(BaseModel):
    """Canonical birth input used for one chart computation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    local_time: str
    timezone: str
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    location_name: str = ""
    gender: str = "Male"


class ChartMetadata(BaseModel):
    """Canonical calculation metadata and uncertainty state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = CHART_STATE_SCHEMA_VERSION
    calculated_at_utc: datetime
    reference_time_utc: datetime
    julian_day: float
    sidereal_mode: str
    node_model: str = "Mean Node"
    ephemeris_source: str = "unknown"
    ephemeris_version: str = "unknown"
    timezone_data_version: str = "unknown"
    python_version: str = "unknown"
    dasha_year_days: float = 365.2425
    component_status: dict[str, str] = Field(default_factory=dict)
    ayanamsa: float
    house_system: str
    ascendant: ZodiacSign
    ascendant_longitude: float
    uncertainty_score: float = Field(ge=0.0, le=1.0)
    d1_stable_5min: bool
    d9_stable_5min: bool


class ChartState(BaseModel):
    """
    Canonical backend source of truth for a single chart calculation.

    Every downstream layer must consume this state or an explicit projection of it.
    No downstream layer should independently reconstruct chart geometry from raw input.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    birth: BirthContext
    metadata: ChartMetadata
    raw_astronomical_state: dict[PlanetName, RawAstronomicalState]
    planetary_positions: dict[PlanetName, AstrologicalPosition]
    divisional_charts: dict[str, dict[str, str]]
    dasha_timeline: dict[str, Any]
    panchang: dict[str, Any]
    current_transits: dict[str, str]
    current_transit_longitudes: dict[str, float]
    current_transit_latitudes: dict[str, float]
    current_transit_speeds: dict[str, float]
    current_transit_ephemeris_flags: dict[str, int]
    current_transit_houses: dict[str, int]
    shadbala: dict[str, Any]
    shadbala_summary: dict[str, Any]
    ashtakavarga: dict[str, Any]
    graha_drishti: dict[str, Any]
    combustion: dict[str, Any]
    jaimini_system: dict[str, Any]
    kp_system: dict[str, Any]
    vargottama: dict[str, bool]
    special_features: dict[str, Any]
    predictive_tech: dict[str, Any]
    navatara_chakra: dict[str, Any]

    @model_validator(mode="after")
    def enforce_deep_immutability(self) -> "ChartState":
        """Prevent mutation of nested chart data after canonical construction."""
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if isinstance(value, (dict, list, set)):
                object.__setattr__(self, field_name, _deep_freeze(value))
        return self

    def to_chart_payload(self) -> dict[str, Any]:
        """Serialize the canonical computational state for API/UI consumers."""
        payload = self.model_dump(mode="json")
        birth = payload.pop("birth")
        payload["metadata"].update(
            {
                "seeker_name": "",
                "local_time": birth["local_time"],
                "timezone": birth["timezone"],
                "location": birth["location_name"],
                "lat": birth["latitude"],
                "lon": birth["longitude"],
                "gender": birth["gender"],
            }
        )
        return payload
