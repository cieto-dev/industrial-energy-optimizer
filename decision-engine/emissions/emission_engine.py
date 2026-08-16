from emission_factors import get_emission_factor


def calculate_fuel_emissions(fuel, consumption_per_day):
    """
    Calculate daily CO2 emissions for a fuel.

    Energy = fuel consumption × NCV
    CO2 = energy × emission factor
    """

    fuel = fuel.lower().strip()

    data = get_emission_factor(fuel)

    ncv = data.get("ncv")
    emission_factor = data.get("emission_factor")

    if ncv is None:
        raise ValueError(
            f"NCV is not configured for fuel: {fuel}"
        )

    # NCV is stored as TJ/kt for solid/liquid fuels
    if data["ncv_unit"] == "TJ/kt":

        # kg/day -> kt/day
        consumption_kt_day = consumption_per_day / 1_000_000

        energy_tj_day = consumption_kt_day * ncv

    # Biogas is stored as MJ/m3
    elif data["ncv_unit"] == "MJ/m3":

        energy_mj_day = consumption_per_day * ncv

        energy_tj_day = energy_mj_day / 1_000_000

    else:
        raise ValueError(
            f"Unsupported NCV unit: {data['ncv_unit']}"
        )

    co2_tco2_day = energy_tj_day * emission_factor

    return {
        "fuel": fuel,
        "consumption_per_day": consumption_per_day,
        "energy_tj_day": round(energy_tj_day, 6),
        "emission_factor_tco2_tj": emission_factor,
        "co2_tco2_day": round(co2_tco2_day, 4),
        "co2_kg_day": round(co2_tco2_day * 1000, 2)
    }


if __name__ == "__main__":

    print("Emission Engine")
    print("---------------")

    # Example: 2000 kg/day coal
    result = calculate_fuel_emissions(
        fuel="coal",
        consumption_per_day=2000
    )

    for key, value in result.items():
        print(f"{key}: {value}")

    print()

    # Example: Biogas from our technology-engine result
    result = calculate_fuel_emissions(
        fuel="biogas",
        consumption_per_day=2263.58
    )

    for key, value in result.items():
        print(f"{key}: {value}")


def compare_fuels(
    existing_fuel,
    existing_consumption,
    replacement_fuel,
    replacement_consumption
):
    """
    Compare CO2 emissions of an existing fuel
    with a replacement fuel.
    """

    existing = calculate_fuel_emissions(
        existing_fuel,
        existing_consumption
    )

    replacement = calculate_fuel_emissions(
        replacement_fuel,
        replacement_consumption
    )

    difference = (
        existing["co2_kg_day"]
        - replacement["co2_kg_day"]
    )

    return {
        "existing_fuel": existing_fuel,
        "existing_co2_kg_day": existing["co2_kg_day"],
        "replacement_fuel": replacement_fuel,
        "replacement_co2_kg_day": replacement["co2_kg_day"],
        "co2_difference_kg_day": round(difference, 2)
    }
    comparison = compare_fuels(
    existing_fuel="coal",
    existing_consumption=2000,
    replacement_fuel="biogas",
    replacement_consumption=2263.58
)

print("\nFuel Comparison")
print("---------------")

for key, value in comparison.items():
    print(f"{key}: {value}")
