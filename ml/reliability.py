"""Conservative response-level reliability disclosure helpers.

No claim-level forecast/outcome cohort is currently configured for production,
so the runtime must report reliability as unavailable rather than infer a rate
from chart strength or offline model experiments.
"""

from __future__ import annotations

from typing import Any


def references_for_response(response: Any) -> tuple[str, list[dict[str, Any]]]:
    """Return response text and an empty reference list until evidence exists."""
    return str(response or ""), []


def append_reliability_disclosure(
    response: str,
    references: list[dict[str, Any]],
) -> str:
    """Disclose that empirical reliability is unavailable when no refs exist."""
    if references:
        return response
    disclosure = (
        "Empirical reliability references are unavailable for this response. "
        "Astrological interpretations are not validated personal probabilities."
    )
    if disclosure in response:
        return response
    return f"{response.rstrip()}\n\n{disclosure}" if response.strip() else disclosure
