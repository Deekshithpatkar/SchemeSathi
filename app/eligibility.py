import logging
from typing import Any, Optional


def check_rule_match(profile: dict[str, Any], rules: dict[str, Any], scheme_state: Optional[str]) -> tuple[bool, str]:
    """Check if a profile satisfies scheme rules using deterministic Python logic."""
    # State check: null scheme_state means all-India scheme
    user_state = profile.get("state")
    if scheme_state and user_state:
        if user_state.strip().lower() != scheme_state.strip().lower():
            return False, f"Scheme is restricted to {scheme_state} residents."
    elif scheme_state and not user_state:
        return False, f"Requires residence in {scheme_state}."

    # Occupation check
    allowed_occupations = rules.get("occupation")
    if allowed_occupations:
        user_occ = profile.get("occupation")
        if not user_occ:
            return False, "Occupation required but not specified."
        matched = any(occ.lower() in user_occ.strip().lower() for occ in allowed_occupations)
        if not matched:
            return False, f"Occupation '{user_occ}' does not match required: {allowed_occupations}."

    # Age checks
    user_age = profile.get("age")
    min_age = rules.get("min_age")
    if min_age is not None:
        if user_age is None:
            return False, f"Minimum age of {min_age} required but age not provided."
        if user_age < min_age:
            return False, f"Age {user_age} is below minimum requirement of {min_age}."

    max_age = rules.get("max_age")
    if max_age is not None:
        if user_age is None:
            return False, f"Maximum age of {max_age} required but age not provided."
        if user_age > max_age:
            return False, f"Age {user_age} exceeds maximum limit of {max_age}."

    # Land holding check
    user_land = profile.get("land_acres")
    max_land = rules.get("max_land_acres")
    if max_land is not None and user_land is not None:
        if user_land > max_land:
            return False, f"Land size {user_land} acres exceeds limit of {max_land} acres."

    # Income check
    user_income = profile.get("annual_income")
    max_income = rules.get("max_income")
    if max_income is not None and user_income is not None:
        if user_income > max_income:
            return False, f"Annual income {user_income} exceeds ceiling of {max_income}."

    # Gender check
    rule_gender = rules.get("gender")
    if rule_gender:
        user_gender = profile.get("gender")
        if not user_gender or user_gender.strip().lower() != rule_gender.strip().lower():
            return False, f"Scheme is specific to {rule_gender} applicants."

    return True, "Profile meets all eligibility requirements."


def check_eligibility(profile: dict[str, Any], schemes: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Evaluate profile against a list of schemes and return eligible ones with reasons."""
    logging.info("Checking eligibility for profile: %s", profile)
    eligible: list[dict[str, str]] = []

    for scheme in schemes:
        rules = scheme.get("rules", {})
        scheme_state = scheme.get("state")
        is_eligible, reason = check_rule_match(profile, rules, scheme_state)
        if is_eligible:
            eligible.append({
                "slug": scheme.get("slug", ""),
                "name": scheme.get("name", ""),
                "reason": reason,
            })

    logging.info("Found %d eligible schemes for profile", len(eligible))
    return eligible
