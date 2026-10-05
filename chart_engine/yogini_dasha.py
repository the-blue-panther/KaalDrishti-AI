from datetime import datetime, timedelta

YOGINI_LORDS = [
    ("Mangala", 1), ("Pingala", 2), ("Dhanya", 3), ("Bhramari", 4),
    ("Bhadrika", 5), ("Ulka", 6), ("Siddha", 7), ("Sankata", 8)
]

class YoginiDasha:
    @staticmethod
    def calculate_dashas(moon_longitude_sidereal: float, birth_datetime: datetime) -> list[dict]:
        NAKSHATRA_SPAN = 360.0 / 27.0
        nakshatra_index = int(moon_longitude_sidereal // NAKSHATRA_SPAN)

        # Yogini Formula: (Nakshatra Number + 3) mod 8
        # Nakshatra Number is 1-indexed (Ashwini = 1)
        yogini_index = ((nakshatra_index + 1) + 3) % 8
        if yogini_index == 0: yogini_index = 8
        start_index = yogini_index - 1

        birth_lord, lord_years = YOGINI_LORDS[start_index]
        degrees_elapsed = moon_longitude_sidereal % NAKSHATRA_SPAN
        fraction_remaining = (NAKSHATRA_SPAN - degrees_elapsed) / NAKSHATRA_SPAN
        balance_years = fraction_remaining * lord_years

        timeline = []
        DAYS_IN_YEAR = 365.2425
        current_date = birth_datetime

        first_dasha_end = current_date + timedelta(days=balance_years * DAYS_IN_YEAR)
        first_dasha_start = first_dasha_end - timedelta(days=lord_years * DAYS_IN_YEAR)

        timeline.append({
            "system": "Yogini",
            "lord": birth_lord,
            "start": first_dasha_start.strftime("%d-%b, %Y"),
            "end": first_dasha_end.strftime("%d-%b, %Y"),
            "duration_years": lord_years,
            "balance_years": balance_years
        })

        current_date = first_dasha_end

        # Calculate next 36 years (1 full cycle)
        for i in range(1, 8):
            next_idx = (start_index + i) % 8
            lord_name, duration = YOGINI_LORDS[next_idx]
            end_date = current_date + timedelta(days=duration * DAYS_IN_YEAR)
            timeline.append({
                "system": "Yogini",
                "lord": lord_name,
                "start": current_date.strftime("%d-%b, %Y"),
                "end": end_date.strftime("%d-%b, %Y"),
                "duration_years": duration,
                "balance_years": 0.0
            })
            current_date = end_date

        return timeline
