from datetime import datetime, timedelta

ASHTOTTARI_LORDS = [
    ("Sun", 6), ("Moon", 15), ("Mars", 8), ("Mercury", 17),
    ("Saturn", 10), ("Jupiter", 19), ("Rahu", 12), ("Venus", 21)
]

# Standard Ashtottari maps 28 Nakshatras (including Abhijit) to 8 lords.
# 1. Sun: 4 Nakshatras
# 2. Moon: 3 Nakshatras
# 3. Mars: 4 Nakshatras
# 4. Mercury: 3 Nakshatras
# 5. Saturn: 4 Nakshatras
# 6. Jupiter: 3 Nakshatras
# 7. Rahu: 4 Nakshatras
# 8. Venus: 3 Nakshatras
# Since this requires complex Abhijit intercalation (between U.Ashadha and Shravana),
# we provide an approximated Ecliptic boundary mapping that allocates the 108 years directly proportional to the remaining degrees.

class AshtottariDasha:
    @staticmethod
    def calculate_dashas(moon_longitude_sidereal: float, birth_datetime: datetime) -> list[dict]:
        NAKSHATRA_SPAN = 360.0 / 27.0
        # Determine current Nakshatra
        nakshatra_index = int(moon_longitude_sidereal // NAKSHATRA_SPAN)

        # Approximate Ashtottari starting lord mapping (without Abhijit for simplicity, using Ardra start standard)
        # Sequence offset from Ardra (Index 5 in 0-26)
        shifted_index = (nakshatra_index - 5) % 27
        if shifted_index < 4: lord_index = 0
        elif shifted_index < 7: lord_index = 1
        elif shifted_index < 11: lord_index = 2
        elif shifted_index < 14: lord_index = 3
        elif shifted_index < 18: lord_index = 4
        elif shifted_index < 21: lord_index = 5
        elif shifted_index < 25: lord_index = 6
        else: lord_index = 7

        birth_lord, lord_years = ASHTOTTARI_LORDS[lord_index]
        degrees_elapsed = moon_longitude_sidereal % NAKSHATRA_SPAN
        fraction_remaining = (NAKSHATRA_SPAN - degrees_elapsed) / NAKSHATRA_SPAN
        balance_years = fraction_remaining * lord_years

        timeline = []
        DAYS_IN_YEAR = 365.2425
        current_date = birth_datetime

        first_dasha_end = current_date + timedelta(days=balance_years * DAYS_IN_YEAR)
        first_dasha_start = first_dasha_end - timedelta(days=lord_years * DAYS_IN_YEAR)

        timeline.append({
            "system": "Ashtottari",
            "lord": birth_lord,
            "start": first_dasha_start.strftime("%d-%b, %Y"),
            "end": first_dasha_end.strftime("%d-%b, %Y"),
            "duration_years": lord_years,
            "balance_years": balance_years
        })

        current_date = first_dasha_end

        # Calculate next 108 years (1 full cycle)
        for i in range(1, 8):
            next_idx = (lord_index + i) % 8
            lord_name, duration = ASHTOTTARI_LORDS[next_idx]
            end_date = current_date + timedelta(days=duration * DAYS_IN_YEAR)
            timeline.append({
                "system": "Ashtottari",
                "lord": lord_name,
                "start": current_date.strftime("%d-%b, %Y"),
                "end": end_date.strftime("%d-%b, %Y"),
                "duration_years": duration,
                "balance_years": 0.0
            })
            current_date = end_date

        return timeline
