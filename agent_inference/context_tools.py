"""Small, allowlisted on-demand dasha and transit context tools for the LLM."""
from datetime import datetime, timedelta, timezone
from typing import Any

from chart_engine.coordinate_transformer import ZODIAC_ORDER
from chart_engine.models import PlanetName
from chart_engine.transits import TransitEngine

MAX_TOOL_CALLS = 2
MAX_DASHA_RANGE_DAYS = 3652
MAX_TRANSIT_RANGE_DAYS = 1096
MAX_TRANSIT_PLANETS = 3
MAX_RESULT_ITEMS = 100
ALLOWED_DASHA_SYSTEMS = {"Vimshottari"}
ALLOWED_DASHA_LEVELS = {"mahadasha", "antardasha", "pratyantardasha"}
ALLOWED_TRANSIT_KINDS = {"snapshot", "sign_ingresses", "house_ingresses"}
ALLOWED_PLANETS = {planet.value for planet in PlanetName}


def _date(value: Any, label: str, default: datetime) -> datetime:
    if value is None:
        return default.astimezone(timezone.utc)
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO-8601 string")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone, for example Z")
    return result.astimezone(timezone.utc)


def _period_date(period: dict, key: str) -> datetime | None:
    value = period.get(f"{key}_exact") or period.get(key)
    if not value:
        return None
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        try:
            result = datetime.strptime(str(value), "%d-%b, %Y")
        except ValueError:
            return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def _overlaps(period: dict, start: datetime, end: datetime) -> bool:
    p_start, p_end = _period_date(period, "start"), _period_date(period, "end")
    return p_start is not None and p_end is not None and p_start < end and start < p_end


def _selected_fields(period: dict, level: str, parent_lords: list[str]) -> dict:
    result = {"level": level, "lord": period.get("lord") or period.get("planet") or period.get("name")}
    for key in ("start", "end", "start_exact", "end_exact"):
        if period.get(key) is not None:
            result[key] = period[key]
    if parent_lords:
        result["parent_lords"] = parent_lords
    return result


def _dasha(chart, arguments: dict) -> dict:
    system = arguments.get("system", "Vimshottari")
    if system not in ALLOWED_DASHA_SYSTEMS:
        raise ValueError("Unsupported dasha system")
    reference = chart.metadata.reference_time_utc.astimezone(timezone.utc)
    start = _date(arguments.get("start_utc"), "start_utc", reference)
    end = _date(arguments.get("end_utc"), "end_utc", start + timedelta(days=365 * 2))
    if end <= start:
        raise ValueError("end_utc must be later than start_utc")
    if (end - start).days > MAX_DASHA_RANGE_DAYS:
        raise ValueError("Dasha query range is limited to 10 years")
    levels = arguments.get("levels", ["mahadasha", "antardasha"])
    if not isinstance(levels, list) or not levels or any(level not in ALLOWED_DASHA_LEVELS for level in levels):
        raise ValueError("levels must be a non-empty list of supported dasha levels")
    try:
        limit = max(1, min(int(arguments.get("limit", 48)), MAX_RESULT_ITEMS))
    except (TypeError, ValueError):
        raise ValueError("limit must be an integer")

    timeline = chart.dasha_timeline.get(system, [])
    results = []
    if not isinstance(timeline, (list, tuple)):
        timeline = []
    for major in timeline:
        if not isinstance(major, dict):
            continue
        if system == "Vimshottari" and "mahadasha" in levels and _overlaps(major, start, end):
            results.append(_selected_fields(major, "mahadasha", []))
        for antar in major.get("antardashas", ()):
            if not isinstance(antar, dict):
                continue
            parent = [str(major.get("lord", ""))]
            if "antardasha" in levels and _overlaps(antar, start, end):
                results.append(_selected_fields(antar, "antardasha", parent))
            for pratyantar in antar.get("pratyantardashas", ()):
                if (isinstance(pratyantar, dict) and "pratyantardasha" in levels
                        and _overlaps(pratyantar, start, end)):
                    results.append(_selected_fields(
                        pratyantar, "pratyantardasha", parent + [str(antar.get("lord", ""))]
                    ))
        if len(results) >= limit:
            break

    status = chart.metadata.component_status.get("vimshottari", "unknown") if system == "Vimshottari" else chart.metadata.component_status.get(system.lower(), "unverified")
    return {
        "tool": "get_dasha",
        "system": system,
        "range_utc": {"start": start.isoformat(), "end": end.isoformat()},
        "levels": levels,
        "component_status": status,
        "periods": results[:limit],
        "truncated": len(results) >= limit,
    }


def _transits(chart, arguments: dict) -> dict:
    kind = arguments.get("kind", "snapshot")
    if kind not in ALLOWED_TRANSIT_KINDS:
        raise ValueError("Unsupported transit query kind")
    planets = arguments.get("planets")
    if planets is None and kind == "snapshot":
        planets = [planet.value for planet in PlanetName]
    if not isinstance(planets, list) or not planets:
        raise ValueError("planets must be a non-empty list for this transit lookup")
    if any(not isinstance(planet, str) or planet not in ALLOWED_PLANETS for planet in planets):
        raise ValueError("One or more transit planets are unsupported")
    planets = list(dict.fromkeys(planets))
    if kind != "snapshot" and len(planets) > MAX_TRANSIT_PLANETS:
        raise ValueError("A transit query can request at most three planets")

    if kind == "snapshot":
        requested_time = arguments.get("at_utc")
        if requested_time is None:
            signs = chart.current_transits
            longitudes = chart.current_transit_longitudes
            latitudes = chart.current_transit_latitudes
            speeds = chart.current_transit_speeds
            houses = chart.current_transit_houses
            reference = chart.metadata.reference_time_utc.astimezone(timezone.utc)
        else:
            reference = _date(requested_time, "at_utc", chart.metadata.reference_time_utc)
            snapshot = TransitEngine.get_current_transit_snapshot(reference)
            signs = snapshot["signs"]
            longitudes = snapshot["longitudes"]
            latitudes = snapshot["latitudes"]
            speeds = snapshot["speeds"]
            asc_index = next(i for i, sign in enumerate(ZODIAC_ORDER) if sign.value == chart.metadata.ascendant.value)
            houses = {
                planet: (next(i for i, sign in enumerate(ZODIAC_ORDER) if sign.value == signs[planet]) - asc_index) % 12 + 1
                for planet in signs
            }
        return {
            "tool": "get_transits",
            "kind": kind,
            "reference_time_utc": reference.isoformat(),
            "planets": {
                planet: {
                    "sign": signs.get(planet),
                    "longitude_deg": longitudes.get(planet),
                    "latitude_deg": latitudes.get(planet),
                    "speed_deg_per_day": speeds.get(planet),
                    "house_from_natal_ascendant": houses.get(planet),
                }
                for planet in planets
            },
        }

    start = _date(arguments.get("start_utc"), "start_utc", chart.metadata.reference_time_utc)
    end = _date(arguments.get("end_utc"), "end_utc", start + timedelta(days=365))
    if end <= start:
        raise ValueError("end_utc must be later than start_utc")
    if (end - start).days > MAX_TRANSIT_RANGE_DAYS:
        raise ValueError("Transit ingress range is limited to three years")

    ingress_fn = TransitEngine.find_sign_ingresses if kind == "sign_ingresses" else TransitEngine.find_gochar_house_ingresses
    events = []
    for planet in planets:
        if kind == "house_ingresses":
            events.extend(ingress_fn(planet, chart.metadata.ascendant, start, end))
        else:
            events.extend(ingress_fn(planet, start, end))
    events.sort(key=lambda item: item.get("ingress_time_utc", ""))
    return {
        "tool": "get_transits",
        "kind": kind,
        "range_utc": {"start": start.isoformat(), "end": end.isoformat()},
        "events": events[:MAX_RESULT_ITEMS],
        "truncated": len(events) > MAX_RESULT_ITEMS,
    }


def execute_context_tool(name: str, arguments: dict, chart) -> dict:
    """Run one allowlisted, bounded chart context lookup; never execute code."""
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object")
    allowed_arguments = {
        "get_dasha": {"system", "start_utc", "end_utc", "levels", "limit"},
        "get_transits": {"kind", "planets", "at_utc", "start_utc", "end_utc"},
    }
    if name not in allowed_arguments:
        raise ValueError("Unknown context tool")
    if set(arguments) - allowed_arguments[name]:
        raise ValueError("Tool request contains unsupported arguments")
    if name == "get_dasha":
        return _dasha(chart, arguments)
    if name == "get_transits":
        return _transits(chart, arguments)
    raise ValueError("Unknown context tool")
