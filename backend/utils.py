def mj_to_kwh(mj: float) -> float:
    """Convert megajoules to kilowatt-hours."""
    return mj / 3.6


def kwh_to_mj(kwh: float) -> float:
    """Convert kilowatt-hours to megajoules."""
    return kwh * 3.6


def tonnes_to_kg(tonnes: float) -> float:
    """Convert tonnes to kilograms."""
    return tonnes * 1000


def kg_to_tonnes(kg: float) -> float:
    """Convert kilograms to tonnes."""
    return kg / 1000


def round_value(value: float, decimals: int = 2) -> float:
    """Round a numerical value to the required decimal places."""
    return round(value, decimals)