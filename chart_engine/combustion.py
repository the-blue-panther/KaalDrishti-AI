"""
Combustion & Planetary War (ग्रह युद्ध / मौढ्य)
=================================================

Implements combustion (Asta/Moudhya) detection and planetary war
(Graha Yuddha) calculation as per Vedic astrology principles.

Combustion (Moudhya / Asta):
When a planet comes too close to the Sun, it becomes "combust" —
its energy is overpowered by the Sun's brilliance, weakening its effects.

Combustion distances (BPHS Ch. 7, Shloka 38-39):
- Moon: 12° from Sun
- Mercury: 14° (12° if retrograde)
- Venus: 10° (8° if retrograde)
- Mars: 17°
- Jupiter: 11°
- Saturn: 15°

Planetary War (Graha Yuddha):
When two planets (excluding Sun and Moon) are within 1° of each other,
they are in planetary war. The planet with higher latitude (more northern)
wins the war.

Reference: Brihat Parashara Hora Shastra, Chapters 7, 83
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Planet(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"


# Combustion distance from Sun in degrees
# (direct motion, retrograde motion)
COMBUSTION_DISTANCES = {
    Planet.MOON: 12.0,
    Planet.MERCURY: 14.0,
    Planet.VENUS: 10.0,
    Planet.MARS: 17.0,
    Planet.JUPITER: 11.0,
    Planet.SATURN: 15.0,
}

# Retrograde combustion distances (reduced)
COMBUSTION_RETROGRADE = {
    Planet.MERCURY: 12.0,
    Planet.VENUS: 8.0,
    Planet.MARS: 17.0,
    Planet.JUPITER: 11.0,
    Planet.SATURN: 15.0,
}

# Planetary war proximity threshold (degrees)
WAR_THRESHOLD = 1.0


@dataclass
class CombustionResult:
    """Complete combustion and planetary war analysis."""
    combustion_status: Dict[str, bool]
    combustion_distance: Dict[str, float]
    combustion_severity: Dict[str, str]
    planetary_wars: List[Dict[str, str]]
    combustion_penalty: Dict[str, float]

    def to_dict(self) -> dict:
        return {
            "combustion_status": self.combustion_status,
            "combustion_distance": {
                k: round(v, 2) for k, v in self.combustion_distance.items()
            },
            "combustion_severity": self.combustion_severity,
            "planetary_wars": self.planetary_wars,
            "combustion_penalty": {
                k: round(v, 2) for k, v in self.combustion_penalty.items()
            },
        }


class CombustionEngine:
    """Engine for detecting combustion and planetary war."""

    @staticmethod
    def get_angular_distance(lon1: float, lon2: float) -> float:
        """Calculate the minimum angular distance between two longitudes."""
        diff = abs(lon1 - lon2) % 360.0
        return min(diff, 360.0 - diff)

    @staticmethod
    def detect_combustion(
        planet_longitudes: Dict[str, float],
        retrograde_status: Optional[Dict[str, bool]] = None
    ) -> CombustionResult:
        """
        Detect combustion status for all planets relative to the Sun.

        Args:
            planet_longitudes: Dict mapping planet name to sidereal longitude
            retrograde_status: Optional dict of planet name → is_retrograde bool

        Returns:
            CombustionResult with full combustion analysis
        """
        if retrograde_status is None:
            retrograde_status = {}

        sun_lon = planet_longitudes.get("Sun", 0.0)
        combustion_status: Dict[str, bool] = {}
        combustion_distance: Dict[str, float] = {}
        combustion_severity: Dict[str, str] = {}
        combustion_penalty: Dict[str, float] = {}

        for planet_name, planet_lon in planet_longitudes.items():
            if planet_name == "Sun":
                combustion_status[planet_name] = False
                combustion_distance[planet_name] = 0.0
                combustion_severity[planet_name] = "Not applicable"
                combustion_penalty[planet_name] = 0.0
                continue

            try:
                planet = Planet(planet_name)
            except ValueError:
                combustion_status[planet_name] = False
                combustion_distance[planet_name] = 0.0
                combustion_severity[planet_name] = "N/A (Node)"
                combustion_penalty[planet_name] = 0.0
                continue

            distance = CombustionEngine.get_angular_distance(sun_lon, planet_lon)
            combustion_distance[planet_name] = distance

            is_retro = retrograde_status.get(planet_name, False)
            if is_retro and planet in COMBUSTION_RETROGRADE:
                threshold = COMBUSTION_RETROGRADE[planet]
            elif planet in COMBUSTION_DISTANCES:
                threshold = COMBUSTION_DISTANCES[planet]
            else:
                combustion_status[planet_name] = False
                combustion_severity[planet_name] = "No combustion"
                combustion_penalty[planet_name] = 0.0
                continue

            is_combust = distance < threshold
            combustion_status[planet_name] = is_combust

            if is_combust:
                ratio = distance / threshold
                if ratio < 0.25:
                    severity = "Deep Combustion (Severe)"
                    penalty = 0.8
                elif ratio < 0.5:
                    severity = "Combustion (Moderate)"
                    penalty = 0.6
                elif ratio < 0.75:
                    severity = "Mild Combustion"
                    penalty = 0.4
                else:
                    severity = "Edge Combustion (Slight)"
                    penalty = 0.2
                combustion_severity[planet_name] = severity
                combustion_penalty[planet_name] = penalty
            else:
                combustion_severity[planet_name] = "No combustion"
                combustion_penalty[planet_name] = 0.0

        return CombustionResult(
            combustion_status=combustion_status,
            combustion_distance=combustion_distance,
            combustion_severity=combustion_severity,
            planetary_wars=[],
            combustion_penalty=combustion_penalty,
        )

    @staticmethod
    def detect_planetary_war(
        planet_longitudes: Dict[str, float],
        planet_latitudes: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, str]]:
        """
        Detect planetary wars (Graha Yuddha) between planets.

        Two planets (excluding Sun/Moon) within 1° of each other
        are in planetary war. The winner is the one with higher
        (more northern) latitude, or brighter if latitudes equal.

        Args:
            planet_longitudes: Dict of planet → longitude
            planet_latitudes: Optional dict of planet → latitude

        Returns:
            List of war descriptions
        """
        if planet_latitudes is None:
            planet_latitudes = {}

        wars = []
        planet_names = [
            n for n in planet_longitudes
            if n not in ("Sun", "Moon", "Rahu", "Ketu")
        ]

        for i in range(len(planet_names)):
            for j in range(i + 1, len(planet_names)):
                p1 = planet_names[i]
                p2 = planet_names[j]
                lon1 = planet_longitudes[p1]
                lon2 = planet_longitudes[p2]

                distance = CombustionEngine.get_angular_distance(lon1, lon2)

                if distance < WAR_THRESHOLD:
                    lat1 = planet_latitudes.get(p1, 0.0)
                    lat2 = planet_latitudes.get(p2, 0.0)

                    if lat1 > lat2:
                        winner = p1
                        loser = p2
                    elif lat2 > lat1:
                        winner = p2
                        loser = p1
                    else:
                        winner = p1
                        loser = p2

                    wars.append({
                        "planet1": p1,
                        "planet2": p2,
                        "distance": round(distance, 3),
                        "winner": winner,
                        "loser": loser,
                        "severity": "Severe" if distance < 0.25 else (
                            "Moderate" if distance < 0.5 else "Mild"
                        ),
                    })

        return wars

    @classmethod
    def full_analysis(
        cls,
        planet_longitudes: Dict[str, float],
        retrograde_status: Optional[Dict[str, bool]] = None,
        planet_latitudes: Optional[Dict[str, float]] = None
    ) -> CombustionResult:
        """Run complete combustion + planetary war analysis."""
        result = cls.detect_combustion(planet_longitudes, retrograde_status)
        wars = cls.detect_planetary_war(planet_longitudes, planet_latitudes)
        result.planetary_wars = wars
        return result

    @staticmethod
    def apply_combustion_penalty(
        planet_score: float,
        planet_name: str,
        combustion_result: CombustionResult
    ) -> float:
        """Apply combustion penalty to a planet's strength score."""
        penalty = combustion_result.combustion_penalty.get(planet_name, 0.0)
        return planet_score * (1.0 - penalty)


# ============================================================
# QUICK TEST
# ============================================================
if __name__ == "__main__":
    engine = CombustionEngine()

    test_longitudes = {
        "Sun": 45.0,
        "Moon": 150.0,
        "Mars": 50.0,
        "Mercury": 46.5,
        "Jupiter": 200.0,
        "Venus": 53.0,
        "Saturn": 300.0,
    }

    test_latitudes = {
        "Mars": 1.2,
        "Mercury": -2.0,
        "Venus": 3.1,
        "Jupiter": -1.0,
        "Saturn": 0.5,
    }

    result = engine.full_analysis(test_longitudes, {}, test_latitudes)

    print("=" * 60)
    print("COMBUSTION & PLANETARY WAR ANALYSIS")
    print("=" * 60)

    print("\nCombustion Status:")
    for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        status = "🔥 COMBUST" if result.combustion_status.get(p) else "✅ OK"
        dist = result.combustion_distance.get(p, 0)
        sev = result.combustion_severity.get(p, "N/A")
        pen = result.combustion_penalty.get(p, 0)
        print(f"  {p:10s}: {status} | Distance: {dist:.1f}° | {sev} | Penalty: {pen:.0%}")

    if result.planetary_wars:
        print("\n⚔️  Planetary Wars Detected:")
        for war in result.planetary_wars:
            print(
                f"  {war['planet1']} vs {war['planet2']} "
                f"({war['distance']}° apart) → "
                f"Winner: {war['winner']} | Loser: {war['loser']} "
                f"[{war['severity']}]"
            )
    else:
        print("\nNo planetary wars detected.")

    print("\n" + "=" * 60)
    print("SCORE IMPACT EXAMPLE:")
    base = 0.75
    for p in ["Mercury", "Venus", "Mars"]:
        adjusted = engine.apply_combustion_penalty(base, p, result)
        print(f"  {p}: {base:.2f} → {adjusted:.2f} ({(1-adjusted/base)*100:.0f}% reduction)")
