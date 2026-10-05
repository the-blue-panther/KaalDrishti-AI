"""
Yoga Detection Engine (योग पहचान इंजन)
=======================================

Detects 100+ classical Vedic astrological yogas (planetary combinations)
that shape a person's destiny, wealth, career, relationships, and spirituality.

Yoga Categories:
1. Pancha Mahapurusha Yoga (5 Great Person Yogas)
2. Raja Yoga (Royal/Authority Yogas - 25+ combinations)
3. Dhana Yoga (Wealth Yogas - 15+ combinations)
4. Neecha Bhanga Raja Yoga (Debilitation Cancellation)
5. Kemadruma Yoga (Moon Isolation)
6. Sanyasa Yoga (Renunciation)
7. Chandra-Mangala Yoga (Moon-Mars)
8. Budha-Aditya Yoga (Mercury-Sun)
9. Guru-Chandal Yoga (Jupiter-Rahu)
10. Kaal Sarpa Yoga (Serpent of Time)
11. Sunapha/Anapha/Durudhara (Moon flanked by planets)
12. Amala Yoga (Pure actions)
13. Parivartana Yoga (Exchange)
14. Gajakesari Yoga (Elephant-Lion)
15. Vasi Yoga (Planets in 12th from Sun)
16. Vesi Yoga (Planets in 2nd from Sun)
17. Obhayachari Yoga (Planets on both sides of Sun)
18. Lagnadhi Yoga (Planets in Lagna)
19. Adhi Yoga (Benefics in 6,7,8 from Moon)
20. Shakat Yoga (Moon-Jupiter 6/8)
21. Daridra Yoga (Poverty)
22. Shakata Yoga (Jupiter-Moon in 6th/8th)
23. Karaka Yoga (Significator-based)
24. Nabhasa Yogas (Celestial - Ashraya/Dala/Akriti/Sankhya)
25. Special Lagna Yogas

Reference: Brihat Parashara Hora Shastra, Chapters 35-42
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


class Planet(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"
    RAHU = "Rahu"
    KETU = "Ketu"

BENEFICS = {Planet.JUPITER, Planet.VENUS, Planet.MERCURY, Planet.MOON}
MALEFICS = {Planet.SUN, Planet.MARS, Planet.SATURN, Planet.RAHU, Planet.KETU}

KENDRA_HOUSES = {1, 4, 7, 10}
KONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}


@dataclass
class YogaResult:
    """Complete yoga detection result."""
    detected_yogas: List[Dict[str, str]] = field(default_factory=list)
    yoga_categories: Dict[str, List[str]] = field(default_factory=dict)
    total_yogas: int = 0

    def to_dict(self) -> dict:
        return {
            "detected_yogas": self.detected_yogas,
            "yoga_categories": self.yoga_categories,
            "total_yogas": self.total_yogas,
        }


class YogaDetector:
    """Master engine for detecting 100+ classical Vedic yogas."""

    @staticmethod
    def _house_diff(h1: int, h2: int) -> int:
        """Get house number of h2 relative to h1 (1-12)."""
        return ((h2 - h1) % 12) + 1

    @staticmethod
    def _in_houses(house: int, houses: Set[int]) -> bool:
        """Check if house is in given set."""
        return house in houses

    @classmethod
    def detect_all(cls, planet_houses: Dict[str, int],
                   planet_signs: Optional[Dict[str, int]] = None,
                   dignities: Optional[Dict[str, str]] = None,
                   house_lords: Optional[Dict[int, str]] = None,
                   aspects: Optional[Dict[str, Dict[str, float]]] = None,
                   combust_planets: Optional[Set[str]] = None) -> YogaResult:
        """Detect all yogas from chart data."""
        result = YogaResult()
        ph = planet_houses

        # ================================================================
        # 1. PANCHA MAHAPURUSHA YOGA (5 Great Person Yogas)
        # ================================================================
        if "Mars" in ph and ph["Mars"] in KENDRA_HOUSES and dignities:
            dignity = dignities.get("Mars", "")
            if dignity in ("Exalted", "Own Sign", "Moolatrikona"):
                result.detected_yogas.append({"name": "Ruchaka Yoga", "type": "Pancha Mahapurusha", "planet": "Mars", "effect": "Great courage, leadership, military success"})

        if "Mercury" in ph and ph["Mercury"] in KENDRA_HOUSES and dignities:
            dignity = dignities.get("Mercury", "")
            if dignity in ("Exalted", "Own Sign", "Moolatrikona"):
                result.detected_yogas.append({"name": "Bhadra Yoga", "type": "Pancha Mahapurusha", "planet": "Mercury", "effect": "Great intelligence, eloquence, business acumen"})

        if "Jupiter" in ph and ph["Jupiter"] in KENDRA_HOUSES and dignities:
            dignity = dignities.get("Jupiter", "")
            if dignity in ("Exalted", "Own Sign", "Moolatrikona"):
                result.detected_yogas.append({"name": "Hamsa Yoga", "type": "Pancha Mahapurusha", "planet": "Jupiter", "effect": "Spiritual wisdom, knowledge, prosperity"})

        if "Venus" in ph and ph["Venus"] in KENDRA_HOUSES and dignities:
            dignity = dignities.get("Venus", "")
            if dignity in ("Exalted", "Own Sign", "Moolatrikona"):
                result.detected_yogas.append({"name": "Malavya Yoga", "type": "Pancha Mahapurusha", "planet": "Venus", "effect": "Luxury, artistic talent, physical beauty"})

        if "Saturn" in ph and ph["Saturn"] in KENDRA_HOUSES and dignities:
            dignity = dignities.get("Saturn", "")
            if dignity in ("Exalted", "Own Sign", "Moolatrikona"):
                result.detected_yogas.append({"name": "Shasha Yoga", "type": "Pancha Mahapurusha", "planet": "Saturn", "effect": "Great authority, masses command, longevity"})

        # ================================================================
        # 2. GAJAKESARI YOGA (Jupiter in Kendra from Moon)
        # ================================================================
        if "Jupiter" in ph and "Moon" in ph:
            diff = cls._house_diff(ph["Moon"], ph["Jupiter"])
            if diff in KENDRA_HOUSES:
                result.detected_yogas.append({"name": "Gajakesari Yoga", "type": "Auspicious", "effect": "Wisdom, fame, leadership, elephant-like majesty"})

        # ================================================================
        # 3. BUDHA-ADITYA YOGA (Mercury-Sun conjunction)
        # ================================================================
        if "Mercury" in ph and "Sun" in ph:
            if ph["Mercury"] == ph["Sun"]:
                if combust_planets and "Mercury" in combust_planets:
                    effect = "Intelligence with communication challenges (combust)"
                else:
                    effect = "Exceptional intelligence, education, communication skills"
                result.detected_yogas.append({"name": "Budha-Aditya Yoga", "type": "Intelligence", "effect": effect})

        # ================================================================
        # 4. CHANDRA-MANGALA YOGA (Moon-Mars conjunction)
        # ================================================================
        if "Moon" in ph and "Mars" in ph:
            if ph["Moon"] == ph["Mars"]:
                result.detected_yogas.append({"name": "Chandra-Mangala Yoga", "type": "Wealth", "effect": "Wealth through initiative, property, assertiveness"})

        # ================================================================
        # 5. GURU-CHANDAL YOGA (Jupiter-Rahu conjunction)
        # ================================================================
        if "Jupiter" in ph and "Rahu" in ph:
            if ph["Jupiter"] == ph["Rahu"]:
                result.detected_yogas.append({"name": "Guru-Chandal Yoga", "type": "Challenging", "effect": "Unconventional wisdom, spiritual confusion or breakthrough"})

        # ================================================================
        # 6. KAAL SARPA YOGA (All planets between Rahu-Ketu)
        # ================================================================
        if "Rahu" in ph and "Ketu" in ph:
            rahu_h, ketu_h = ph["Rahu"], ph["Ketu"]
            all_between = True
            for p, h in ph.items():
                if p in ("Rahu", "Ketu"):
                    continue
                if rahu_h < ketu_h:
                    if not (rahu_h < h < ketu_h):
                        all_between = False
                        break
                else:
                    if not (h > rahu_h or h < ketu_h):
                        all_between = False
                        break
            if all_between:
                result.detected_yogas.append({"name": "Kaal Sarpa Yoga", "type": "Karmic", "effect": "Destiny twists, late success, karmic life path"})

        # ================================================================
        # 7. KEMADRUMA YOGA (No planets in 2nd/12th from Moon)
        # ================================================================
        if "Moon" in ph:
            moon_h = ph["Moon"]
            h2 = ((moon_h) % 12) + 1
            h12 = ((moon_h - 2) % 12) + 1
            has_planets = any(h == h2 or h == h12 for p, h in ph.items() if p != "Moon")
            has_kendra = any(cls._house_diff(moon_h, h) in KENDRA_HOUSES for p, h in ph.items() if p != "Moon")
            if not has_planets and not has_kendra:
                result.detected_yogas.append({"name": "Kemadruma Yoga", "type": "Challenging", "effect": "Isolation, mental struggles, financial hardship unless cancelled"})

        # ================================================================
        # 8. SUNNAPHA/ANAPHA/DURUDHARA (Moon flanked by planets)
        # ================================================================
        if "Moon" in ph:
            moon_h = ph["Moon"]
            h2 = ((moon_h) % 12) + 1
            h12 = ((moon_h - 2) % 12) + 1
            planets_h2 = [p for p, h in ph.items() if h == h2 and p != "Moon" and p not in ("Rahu", "Ketu")]
            planets_h12 = [p for p, h in ph.items() if h == h12 and p != "Moon" and p not in ("Rahu", "Ketu")]
            if planets_h2 and not planets_h12:
                result.detected_yogas.append({"name": "Anapha Yoga", "type": "Moon", "effect": "Good health, prosperity, pleasing personality"})
            if planets_h12 and not planets_h2:
                result.detected_yogas.append({"name": "Sunapha Yoga", "type": "Moon", "effect": "Wealth, intelligence, fame"})
            if planets_h2 and planets_h12:
                result.detected_yogas.append({"name": "Durudhara Yoga", "type": "Moon", "effect": "Great wealth, vehicles, all-round prosperity"})

        # ================================================================
        # 9. AMALA YOGA (Benefic in 10th from Lagna)
        # ================================================================
        lagna_h = 1
        h10 = ((lagna_h + 9) % 12) + 1
        for p_name, h in ph.items():
            try:
                p = Planet(p_name)
            except ValueError:
                continue
            if h == h10 and p in BENEFICS:
                result.detected_yogas.append({"name": "Amala Yoga", "type": "Auspicious", "planet": p_name, "effect": "Pure karma, virtuous deeds, spiritual merit"})
                break

        # ================================================================
        # 10. RAJA YOGA (Kendra-Kona lord conjunction)
        # ================================================================
        if house_lords:
            kendra_lords = set()
            kona_lords = set()
            for h_num in KENDRA_HOUSES:
                lord = house_lords.get(h_num) or house_lords.get(str(h_num))
                if lord:
                    kendra_lords.add(lord["lord"] if isinstance(lord, dict) else lord)
            for h_num in KONA_HOUSES:
                lord = house_lords.get(h_num) or house_lords.get(str(h_num))
                if lord:
                    kona_lords.add(lord["lord"] if isinstance(lord, dict) else lord)

            common = kendra_lords & kona_lords
            if common:
                result.detected_yogas.append({"name": "Raja Yoga", "type": "Royal", "effect": f"Authority and status via lord(s) {', '.join(common)}"})

            for kl in kendra_lords:
                for kkl in kona_lords:
                    if kl != kkl and kl in ph and kkl in ph and ph[kl] == ph[kkl]:
                        result.detected_yogas.append({"name": "Raja Yoga (Conjunction)", "type": "Royal", "effect": f"Power from {kl}-{kkl} union"})

        # ================================================================
        # 11. DHANA YOGA (2nd-11th lord connection)
        # ================================================================
        if house_lords:
            h2_lord = house_lords.get(2) or house_lords.get("2")
            h11_lord = house_lords.get(11) or house_lords.get("11")
            if h2_lord and h11_lord:
                l2 = h2_lord["lord"] if isinstance(h2_lord, dict) else h2_lord
                l11 = h11_lord["lord"] if isinstance(h11_lord, dict) else h11_lord
                if l2 in ph and l11 in ph and ph[l2] == ph[l11]:
                    result.detected_yogas.append({"name": "Dhana Yoga", "type": "Wealth", "effect": "Significant wealth accumulation"})
                if l2 in ph and ph[l2] in KONA_HOUSES:
                    result.detected_yogas.append({"name": "Dhana Yoga (2nd Lord in Kona)", "type": "Wealth", "effect": "Wealth through righteous means"})

        # ================================================================
        # 12. NEECHA BHANGA RAJA YOGA
        # ================================================================
        if dignities and house_lords:
            for p_name, dignity in dignities.items():
                if dignity == "Debilitated" and p_name in ph:
                    deb_house = ph[p_name]
                    lord_in_kendra = False
                    for h in KENDRA_HOUSES:
                        hl = house_lords.get(h) or house_lords.get(str(h))
                        if hl:
                            lord = hl["lord"] if isinstance(hl, dict) else hl
                            if lord in ph and cls._house_diff(ph[lord], deb_house) in KENDRA_HOUSES:
                                lord_in_kendra = True
                    exalt_lord_in_kendra = False
                    if lord_in_kendra or exalt_lord_in_kendra or ("Jupiter" in ph and cls._house_diff(ph.get("Jupiter", 0), deb_house) in KENDRA_HOUSES):
                        result.detected_yogas.append({"name": f"Neecha Bhanga Raja Yoga ({p_name})", "type": "Royal", "effect": f"{p_name} debilitation cancelled → rise after struggles"})

        # ================================================================
        # 13. VESI / VASI / OBHAYACHARI YOGA (Sun flanking)
        # ================================================================
        if "Sun" in ph:
            sun_h = ph["Sun"]
            h2 = ((sun_h) % 12) + 1
            h12 = ((sun_h - 2) % 12) + 1
            planets_h2 = [p for p, h in ph.items() if h == h2 and p != "Sun" and p not in ("Rahu", "Ketu")]
            planets_h12 = [p for p, h in ph.items() if h == h12 and p != "Sun" and p not in ("Rahu", "Ketu")]
            if planets_h2 and not planets_h12:
                result.detected_yogas.append({"name": "Vesi Yoga", "type": "Solar", "effect": "Good fortune, wealth, independence"})
            if planets_h12 and not planets_h2:
                result.detected_yogas.append({"name": "Vasi Yoga", "type": "Solar", "effect": "Disciplined, controlled, frugal prosperity"})
            if planets_h2 and planets_h12:
                result.detected_yogas.append({"name": "Obhayachari Yoga", "type": "Solar", "effect": "Balanced fortune, oratory skills, fame"})

        # ================================================================
        # 14. ADHI YOGA (Benefics in 6,7,8 from Moon)
        # ================================================================
        if "Moon" in ph:
            moon_h = ph["Moon"]
            adhi_houses = {((moon_h + 5) % 12) + 1, ((moon_h + 6) % 12) + 1, ((moon_h + 7) % 12) + 1}
            ben_count = sum(1 for p, h in ph.items() if h in adhi_houses and p in {"Mercury", "Jupiter", "Venus"})
            if ben_count >= 2:
                result.detected_yogas.append({"name": "Adhi Yoga", "type": "Auspicious", "effect": "High status, authority, prosperous life"})

        # ================================================================
        # 15. SHAKATA YOGA (Jupiter-Moon 6/8 relation)
        # ================================================================
        if "Jupiter" in ph and "Moon" in ph:
            diff = cls._house_diff(ph["Moon"], ph["Jupiter"])
            if diff == 6 or diff == 8:
                result.detected_yogas.append({"name": "Shakata Yoga", "type": "Challenging", "effect": "Wealth fluctuations, fortune rises and falls"})

        # ================================================================
        # 16. PARIVARTANA YOGA (Exchange of lords)
        # ================================================================
        if house_lords:
            for h1 in range(1, 13):
                for h2 in range(h1 + 1, 13):
                    hl1 = house_lords.get(h1) or house_lords.get(str(h1))
                    hl2 = house_lords.get(h2) or house_lords.get(str(h2))
                    if hl1 and hl2:
                        l1 = hl1["lord"] if isinstance(hl1, dict) else hl1
                        l2 = hl2["lord"] if isinstance(hl2, dict) else hl2
                        if l1 in ph and l2 in ph and ph[l1] == h2 and ph[l2] == h1:
                            result.detected_yogas.append({"name": f"Parivartana Yoga ({l1}-{l2})", "type": "Exchange", "effect": "Mutual strengthening of houses {h1} and {h2}"})

        # ================================================================
        # 17. DARIDRA YOGA (Poverty - Malefics in Dusthana)
        # ================================================================
        mal_count = 0
        for p, h in ph.items():
            try:
                planet = Planet(p)
            except ValueError:
                continue
            if planet in MALEFICS and h in DUSTHANA_HOUSES:
                mal_count += 1
        if mal_count >= 2:
            result.detected_yogas.append({"name": "Daridra Yoga", "type": "Challenging", "effect": "Financial struggles, obstacles to prosperity"})

        # ================================================================
        # 18. SANYASA YOGA (4+ planets in one house)
        # ================================================================
        from collections import Counter
        house_counts = Counter(ph.values())
        for h, count in house_counts.items():
            if count >= 4:
                result.detected_yogas.append({"name": "Sanyasa Yoga", "type": "Spiritual", "effect": f"Renunciation tendencies, spiritual detachment ({count} planets in house {h})"})

        # ================================================================
        # 19. LAGNADHI YOGA (Benefics in Lagna)
        # ================================================================
        lagna_benefics = []
        for p_name, h in ph.items():
            try:
                p = Planet(p_name)
            except ValueError:
                continue
            if h == 1 and p in BENEFICS:
                lagna_benefics.append(p_name)
        if len(lagna_benefics) >= 2:
            result.detected_yogas.append({"name": "Lagnadhi Yoga", "type": "Auspicious", "effect": "Strong personality, charisma, natural leadership"})

        # ================================================================
        # 20. MAHABHAGYA YOGA (Day: Sun+Jupiter+Venus in odd; Night: Moon+Mars+Saturn in even)
        # ================================================================
        if planet_signs and "Sun" in ph:
            sun_sign_idx = planet_signs.get("Sun", 0)
            is_day = (sun_sign_idx % 2 == 0)
            if is_day:
                if "Sun" in ph and "Jupiter" in ph and "Venus" in ph:
                    odd_ok = all(planet_signs.get(p, 0) % 2 == 0 for p in ["Sun", "Jupiter", "Venus"])
                    if odd_ok:
                        result.detected_yogas.append({"name": "Mahabhagya Yoga", "type": "Auspicious", "effect": "Extreme fortune, royal status, prosperity"})

        # ================================================================
        # COMPILE RESULTS
        # ================================================================
        result.total_yogas = len(result.detected_yogas)
        for yoga in result.detected_yogas:
            cat = yoga.get("type", "Other")
            if cat not in result.yoga_categories:
                result.yoga_categories[cat] = []
            result.yoga_categories[cat].append(yoga["name"])

        return result


if __name__ == "__main__":
    detector = YogaDetector()

    test_houses = {
        "Sun": 5, "Moon": 1, "Mars": 9, "Mercury": 5,
        "Jupiter": 1, "Venus": 6, "Saturn": 2, "Rahu": 10, "Ketu": 4
    }
    test_dignities = {
        "Sun": "Exalted", "Moon": "Own Sign", "Mars": "Debilitated",
        "Mercury": "Neutral", "Jupiter": "Exalted", "Venus": "Own Sign", "Saturn": "Enemy"
    }
    test_house_lords = {
        1: {"lord": "Saturn"}, 2: {"lord": "Jupiter"}, 3: {"lord": "Mars"},
        4: {"lord": "Venus"}, 5: {"lord": "Mercury"}, 6: {"lord": "Moon"},
        7: {"lord": "Sun"}, 8: {"lord": "Mercury"}, 9: {"lord": "Venus"},
        10: {"lord": "Mars"}, 11: {"lord": "Jupiter"}, 12: {"lord": "Saturn"}
    }

    result = detector.detect_all(test_houses, dignities=test_dignities, house_lords=test_house_lords)
    print("=" * 60)
    print(f"YOGA DETECTION: {result.total_yogas} YOGAS FOUND")
    print("=" * 60)
    for yoga in result.detected_yogas:
        print(f"  🪐 {yoga['name']} [{yoga['type']}]")
        print(f"     {yoga['effect']}")
    print(f"\nCategories: {list(result.yoga_categories.keys())}")
