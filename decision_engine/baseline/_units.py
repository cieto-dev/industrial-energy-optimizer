def standardize_daily_consumption(value: float, unit: str, target_unit: str) -> float:
    """
    Temporary strict unit conversion.
    Raises ValueError on unrecognized units instead of silently defaulting.
    Replace with backend/utils.py when built.
    """
    unit = unit.lower().strip()
    target_unit = target_unit.lower().strip()

    if unit == target_unit:
        return value

    # Valid conversions
    conversions = {
        ("tonnes/day", "kg/day"): 1000.0,
        ("t/day", "kg/day"): 1000.0,
    }

    factor = conversions.get((unit, target_unit))
    if factor is not None:
        return value * factor

    raise ValueError(f"Unrecognized or unsupported unit conversion from '{unit}' to '{target_unit}'.")
