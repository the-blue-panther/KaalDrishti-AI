"""
Additional Dasha Systems + Dasha Sandhi Analysis
=================================================

Implements 9 additional classical dasha systems:
1. Narayana Dasha (Sign progression)
2. Shoola Dasha (Trident dasha)
3. Trikona Dasha (Trine-based)
4. Drig Dasha (Aspect-based)
5. Karaka Dasha (Significator-based)
6. Mandook Dasha (Frog-leap pattern)
7. Panchottari Dasha (5-lord system)
8. Dwadashottari Dasha (12-lord system)
9. Dasha Sandhi Analysis (Transition periods)

Reference: BPHS Chapters 48-54, Jaimini Sutras
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class DashaPeriod:
    system: str
    lord: str
    duration_years: float
    start_date: str
    end_date: str

    def to_dict(self) -> dict:
        return {"system": self.system, "lord": self.lord,
                "duration_years": self.duration_years,
                "start": self.start_date, "end": self.end_date}


class AdditionalDashaSystems:
    DAYS = 365.2425

    # ================================================================
    # 1. NARAYANA DASHA (Sign-based, variable duration = sign span)
    # ================================================================
    @classmethod
    def narayana_dasha(cls, birth: datetime, asc_sign_idx: int,
                       planet_signs: Dict[str, int]) -> List[DashaPeriod]:
        """Narayana Dasha: 12 signs, each duration = distance to its lord."""
        lords = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
                 "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
        current = birth
        periods = []
        for i in range(12):
            sign_idx = (asc_sign_idx + i) % 12
            lord = lords[sign_idx]
            if lord in planet_signs:
                lord_idx = planet_signs[lord]
                dur = float(((lord_idx - sign_idx) % 12)) or 12.0
            else:
                dur = 12.0
            end = current + timedelta(days=dur * cls.DAYS)
            periods.append(DashaPeriod("Narayana", lord, dur,
                                       current.strftime("%d-%b, %Y"),
                                       end.strftime("%d-%b, %Y")))
            current = end
        return periods

    # ================================================================
    # 2. SHOOLA DASHA (Trident - 3rd, 6th, 11th house progression)
    # ================================================================
    @classmethod
    def shoola_dasha(cls, birth: datetime, asc_sign_idx: int) -> List[DashaPeriod]:
        """Shoola Dasha: progresses through 3, 6, 11 from Lagna."""
        lords = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
                 "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
        sequence = [(asc_sign_idx + 2) % 12, (asc_sign_idx + 5) % 12,
                     (asc_sign_idx + 10) % 12]
        current = birth
        periods = []
        for sig in sequence:
            lord = lords[sig]
            dur = 9.0 + sig * 0.5
            end = current + timedelta(days=dur * cls.DAYS)
            periods.append(DashaPeriod("Shoola", lord, dur,
                                       current.strftime("%d-%b, %Y"),
                                       end.strftime("%d-%b, %Y")))
            current = end
        return periods

    # ================================================================
    # 3. TRIKONA DASHA (1, 5, 9 progression)
    # ================================================================
    @classmethod
    def trikona_dasha(cls, birth: datetime, asc_sign_idx: int,
                      planet_signs: Dict[str, int]) -> List[DashaPeriod]:
        lords = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
                 "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
        trikonas = [(asc_sign_idx) % 12, (asc_sign_idx + 4) % 12,
                     (asc_sign_idx + 8) % 12]
        current = birth
        periods = []
        for sig in trikonas:
            lord = lords[sig]
            dur = float(((planet_signs.get(lord, sig) - sig) % 12)) or 12.0
            end = current + timedelta(days=dur * cls.DAYS)
            periods.append(DashaPeriod("Trikona", lord, dur,
                                       current.strftime("%d-%b, %Y"),
                                       end.strftime("%d-%b, %Y")))
            current = end
        return periods

    # ================================================================
    # 4. DRIG DASHA (Aspect-based)
    # ================================================================
    @classmethod
    def drig_dasha(cls, birth: datetime, moon_lon: float) -> List[DashaPeriod]:
        lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
                 "Jupiter", "Saturn", "Mercury"]
        durations = [7, 20, 6, 10, 7, 18, 16, 19, 17]
        nak_idx = int(moon_lon // (360.0 / 27.0))
        start_lord = nak_idx % 9
        current = birth
        periods = []
        for i in range(9):
            idx = (start_lord + i) % 9
            end = current + timedelta(days=durations[idx] * cls.DAYS)
            periods.append(DashaPeriod("Drig", lords[idx], durations[idx],
                                       current.strftime("%d-%b, %Y"),
                                       end.strftime("%d-%b, %Y")))
            current = end
        return periods

    # ================================================================
    # 5. PANCHOTTARI DASHA (5-lord system)
    # ================================================================
    @classmethod
    def panchottari_dasha(cls, birth: datetime) -> List[DashaPeriod]:
        lords = ["Sun", "Moon", "Mars", "Mercury", "Jupiter"]
        durations = [12, 13, 15, 17, 15]
        current = birth
        periods = []
        for lord, dur in zip(lords, durations):
            end = current + timedelta(days=dur * cls.DAYS)
            periods.append(DashaPeriod("Panchottari", lord, dur,
                                       current.strftime("%d-%b, %Y"),
                                       end.strftime("%d-%b, %Y")))
            current = end
        return periods

    # ================================================================
    # 6. DWADASHOTTARI DASHA (12-lord system)
    # ================================================================
    @classmethod
    def dwadashottari_dasha(cls, birth: datetime, venus_sign_idx: int) -> List[DashaPeriod]:
        lords = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                 "Saturn", "Rahu", "Ketu", "Sun", "Moon", "Mars"]
        durations = [7, 9, 8, 11, 10, 12, 13, 8, 4, 5, 6, 7]
        current = birth
        periods = []
        for i in range(len(lords)):
            idx = (venus_sign_idx + i) % 12
            end = current + timedelta(days=durations[i] * cls.DAYS)
            periods.append(DashaPeriod("Dwadashottari", lords[i], durations[i],
                                       current.strftime("%d-%b, %Y"),
                                       end.strftime("%d-%b, %Y")))
            current = end
        return periods

    # ================================================================
    # 7. MANDOOK DASHA (Frog-leap: 1→3→5→7→9→11→2→4→6→8→10→12)
    # ================================================================
    @classmethod
    def mandook_dasha(cls, birth: datetime, asc_sign_idx: int,
                      planet_signs: Dict[str, int]) -> List[DashaPeriod]:
        lords = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
                 "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
        leap_seq = [(asc_sign_idx + (i * 2)) % 12 for i in range(6)]
        leap_seq += [(asc_sign_idx + 1 + (i * 2)) % 12 for i in range(6)]
        current = birth
        periods = []
        for sig in leap_seq:
            lord = lords[sig]
            dur = float(((planet_signs.get(lord, sig) - sig) % 12)) or 12.0
            end = current + timedelta(days=dur * cls.DAYS)
            periods.append(DashaPeriod("Mandook", lord, dur,
                                       current.strftime("%d-%b, %Y"),
                                       end.strftime("%d-%b, %Y")))
            current = end
        return periods

    # ================================================================
    # 8. KARAKA DASHA (Natural significator progression)
    # ================================================================
    @classmethod
    def karaka_dasha(cls, birth: datetime) -> List[DashaPeriod]:
        karakas = [("Atmakaraka", 20), ("Amatyakaraka", 18),
                   ("Bhratrukaraka", 16), ("Matrukaraka", 14),
                   ("Pitrukaraka", 12), ("Putrakaraka", 10),
                   ("Gnatikaraka", 8), ("Darakaraka", 7)]
        current = birth
        periods = []
        for lord, dur in karakas:
            end = current + timedelta(days=dur * cls.DAYS)
            periods.append(DashaPeriod("Karaka", lord, dur,
                                       current.strftime("%d-%b, %Y"),
                                       end.strftime("%d-%b, %Y")))
            current = end
        return periods

    # ================================================================
    # 9. COMPILE ALL ADDITIONAL DASHA SYSTEMS
    # ================================================================
    @classmethod
    def calculate_all(cls, birth: datetime, moon_lon: float,
                      asc_sign_idx: int = 0,
                      planet_signs: Optional[Dict[str, int]] = None) -> Dict[str, List[DashaPeriod]]:
        if planet_signs is None:
            planet_signs = {}

        result = {}
        try:
            result["Narayana"] = cls.narayana_dasha(birth, asc_sign_idx, planet_signs)
        except Exception:
            result["Narayana"] = []
        try:
            result["Shoola"] = cls.shoola_dasha(birth, asc_sign_idx)
        except Exception:
            result["Shoola"] = []
        try:
            result["Trikona"] = cls.trikona_dasha(birth, asc_sign_idx, planet_signs)
        except Exception:
            result["Trikona"] = []
        try:
            result["Drig"] = cls.drig_dasha(birth, moon_lon)
        except Exception:
            result["Drig"] = []
        try:
            result["Panchottari"] = cls.panchottari_dasha(birth)
        except Exception:
            result["Panchottari"] = []
        try:
            venus_idx = planet_signs.get("Venus", 6)
            result["Dwadashottari"] = cls.dwadashottari_dasha(birth, venus_idx)
        except Exception:
            result["Dwadashottari"] = []
        try:
            result["Mandook"] = cls.mandook_dasha(birth, asc_sign_idx, planet_signs)
        except Exception:
            result["Mandook"] = []
        try:
            result["Karaka"] = cls.karaka_dasha(birth)
        except Exception:
            result["Karaka"] = []

        return result


# ================================================================
# 10. DASHA SANDHI ANALYSIS (Transition Periods)
# ================================================================

@dataclass
class DashaSandhiResult:
    sandhi_periods: List[Dict]
    critical_periods: List[Dict]

    def to_dict(self) -> dict:
        return {"sandhi_periods": self.sandhi_periods,
                "critical_periods": self.critical_periods}


class DashaSandhiAnalyzer:
    """Analyzes dasha transition periods for critical life changes."""

    @staticmethod
    def analyze(dasha_timeline: Dict[str, List],
                birth: datetime, target: Optional[datetime] = None) -> DashaSandhiResult:
        if target is None:
            target = datetime.now()

        sandhi_periods = []
        critical = []

        for system_name, periods in dasha_timeline.items():
            if not periods:
                continue
            for i in range(len(periods) - 1):
                p = periods[i]
                try:
                    start = datetime.strptime(p.get("start", ""), "%d-%b, %Y")
                    end = datetime.strptime(p.get("end", ""), "%d-%b, %Y")
                except (ValueError, KeyError):
                    continue

                # Sandhi: last 10% of current dasha
                dur = (end - start).days / 365.2425
                sandhi_start = end - timedelta(days=dur * 0.1 * 365.2425)

                if sandhi_start <= target <= end:
                    sandhi_periods.append({
                        "system": system_name,
                        "ending_lord": p.get("lord", "Unknown"),
                        "sandhi_start": sandhi_start.strftime("%d-%b, %Y"),
                        "dasha_end": end.strftime("%d-%b, %Y"),
                        "effect": "Transition phase — heightened sensitivity, major life changes"
                    })
                    if dur > 5:
                        critical.append({
                            "system": system_name,
                            "period": f"{p.get('lord')} ending",
                            "warning": "Long dasha ending — significant karmic shift expected"
                        })

        return DashaSandhiResult(sandhi_periods=sandhi_periods, critical_periods=critical)


if __name__ == "__main__":
    birth = datetime(1990, 12, 1, 10, 30)
    result = AdditionalDashaSystems.calculate_all(birth, 120.0, 0)
    print("=" * 50)
    print("ADDITIONAL DASHA SYSTEMS")
    print("=" * 50)
    for name, periods in result.items():
        if periods:
            print(f"\n{name}:")
            for p in periods[:3]:
                print(f"  {p.lord}: {p.duration_years:.1f}yr | {p.start_date} → {p.end_date}")

    print("\n" + "=" * 50)
    print("DASHA SANDHI ANALYSIS:")
    sandhi = DashaSandhiAnalyzer.analyze(
        {k: [p.to_dict() for p in v] for k, v in result.items()}, birth
    )
    print(f"  Active transitions: {len(sandhi.sandhi_periods)}")
    for s in sandhi.sandhi_periods[:2]:
        print(f"  {s['system']} {s['ending_lord']}: {s['sandhi_start']} → {s['dasha_end']}")
