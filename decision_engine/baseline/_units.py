def standardize_daily_consumption(value: float, unit: str, target_unit: str) -> float:
    """
    Convert a daily fuel consumption value from one unit to the target unit.

    Raises ValueError on unrecognized unit pairs so callers get a clear error.

    Density / conversion assumptions (standard conditions):
    - Natural gas: 1 SCM ≈ 0.7 kg  (density of ~0.7 kg/m³ at 15°C, 1 atm)
    - Diesel (HSD): 1 L ≈ 0.85 kg  (density ≈ 850 kg/m³)
    - LPG: 1 L ≈ 0.54 kg           (density ≈ 540 kg/m³)
    """
    unit = unit.lower().strip()
    target_unit = target_unit.lower().strip()

    if unit == target_unit:
        return value

    # Valid conversions: (from_unit, to_unit) -> multiplication factor
    conversions = {
        # ── Solid fuels / biomass ── target: kg/day ────────────────────────
        ("kg", "kg/day"):              1.0,
        ("kg/day", "kg/day"):          1.0,
        ("tonnes", "kg/day"):          1000.0,
        ("tonnes/day", "kg/day"):      1000.0,
        ("t", "kg/day"):               1000.0,
        ("t/day", "kg/day"):           1000.0,
        # Gas (density-based: 1 SCM natural gas ≈ 0.7 kg)
        ("scm", "kg/day"):             0.7,
        ("scm/day", "kg/day"):         0.7,
        ("m3", "kg/day"):              0.7,
        ("m3/day", "kg/day"):          0.7,
        ("nm3", "kg/day"):             0.7,
        ("nm3/day", "kg/day"):         0.7,
        # Liquid fuels (density-based: 1 L diesel ≈ 0.85 kg)
        ("l", "kg/day"):               0.85,
        ("l/day", "kg/day"):           0.85,
        ("litre", "kg/day"):           0.85,
        ("litres", "kg/day"):          0.85,
        ("liter", "kg/day"):           0.85,
        ("liters", "kg/day"):          0.85,
        ("kl", "kg/day"):              850.0,
        ("kl/day", "kg/day"):          850.0,

        # ── Natural gas ── target: scm/day ─────────────────────────────────
        ("scm", "scm/day"):            1.0,
        ("scm/day", "scm/day"):        1.0,
        ("m3", "scm/day"):             1.0,
        ("m3/day", "scm/day"):         1.0,
        ("nm3", "scm/day"):            1.0,
        ("nm3/day", "scm/day"):        1.0,
        ("mscm", "scm/day"):           1000.0,
        # Mass → volume (1 kg natural gas ≈ 1/0.7 SCM)
        ("kg", "scm/day"):             1.0 / 0.7,
        ("kg/day", "scm/day"):         1.0 / 0.7,

        # ── Liquid fuels ── target: l/day ──────────────────────────────────
        ("l", "l/day"):                1.0,
        ("l/day", "l/day"):            1.0,
        ("litre", "l/day"):            1.0,
        ("litres", "l/day"):           1.0,
        ("liter", "l/day"):            1.0,
        ("liters", "l/day"):           1.0,
        ("kl", "l/day"):               1000.0,
        ("kl/day", "l/day"):           1000.0,
        # Mass → volume (1 kg diesel ≈ 1/0.85 L)
        ("kg", "l/day"):               1.0 / 0.85,
        ("kg/day", "l/day"):           1.0 / 0.85,

        # ── Solid fuels ── target: tonnes/day ──────────────────────────────
        ("tonnes", "tonnes/day"):      1.0,
        ("tonnes/day", "tonnes/day"):  1.0,
        ("t", "tonnes/day"):           1.0,
        ("t/day", "tonnes/day"):       1.0,
        ("kg", "tonnes/day"):          0.001,
        ("kg/day", "tonnes/day"):      0.001,
    }

    factor = conversions.get((unit, target_unit))
    if factor is not None:
        return value * factor

    raise ValueError(
        f"Unrecognized or unsupported unit conversion from '{unit}' to '{target_unit}'."
    )
