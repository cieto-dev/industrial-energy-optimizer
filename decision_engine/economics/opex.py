def calculate_annual_fuel_cost(
    annual_fuel_consumption,
    fuel_price
):
    """
    Calculate annual fuel cost.

    annual_fuel_consumption:
        Annual quantity of fuel consumed.

    fuel_price:
        Price per unit of fuel.
    """

    if annual_fuel_consumption < 0:
        raise ValueError(
            "Annual fuel consumption cannot be negative."
        )

    if fuel_price < 0:
        raise ValueError(
            "Fuel price cannot be negative."
        )

    return (
        annual_fuel_consumption
        * fuel_price
    )


def calculate_annual_electricity_cost(
    annual_electricity_consumption,
    electricity_price
):
    """
    Calculate annual electricity cost.
    """

    if annual_electricity_consumption < 0:
        raise ValueError(
            "Annual electricity consumption cannot be negative."
        )

    if electricity_price < 0:
        raise ValueError(
            "Electricity price cannot be negative."
        )

    return (
        annual_electricity_consumption
        * electricity_price
    )


def calculate_maintenance_cost(
    capex,
    maintenance_percentage
):
    """
    Calculate annual maintenance cost
    as a percentage of CAPEX.
    """

    if capex < 0:
        raise ValueError(
            "CAPEX cannot be negative."
        )

    if maintenance_percentage < 0:
        raise ValueError(
            "Maintenance percentage cannot be negative."
        )

    return (
        capex
        * maintenance_percentage
        / 100
    )


def calculate_annual_opex(
    fuel_cost=0,
    electricity_cost=0,
    maintenance_cost=0,
    labour_cost=0,
    other_cost=0
):
    """
    Calculate total annual OPEX.
    """

    costs = {
        "fuel_cost": fuel_cost,
        "electricity_cost": electricity_cost,
        "maintenance_cost": maintenance_cost,
        "labour_cost": labour_cost,
        "other_cost": other_cost
    }

    for name, value in costs.items():

        if value < 0:
            raise ValueError(
                f"{name} cannot be negative."
            )

    annual_opex = sum(
        costs.values()
    )

    return {
        **costs,
        "annual_opex": annual_opex
    }


def calculate_annual_savings(
    baseline_annual_opex,
    proposed_annual_opex
):
    """
    Calculate annual operating-cost savings.

    Positive value = saving
    Negative value = additional cost
    """

    return (
        baseline_annual_opex
        - proposed_annual_opex
    )