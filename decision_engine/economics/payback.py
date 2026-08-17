def calculate_payback(
    capex_min,
    capex_max,
    annual_savings
):
    """
    Calculate simple payback period as a range.

    Payback = CAPEX / Annual Savings

    Minimum payback:
        minimum CAPEX / annual savings

    Maximum payback:
        maximum CAPEX / annual savings
    """

    if annual_savings <= 0:

        return {
            "payback_min_years": None,
            "payback_max_years": None
        }

    if capex_min is None:
        raise ValueError(
            "capex_min is required."
        )

    payback_min = (
        capex_min
        / annual_savings
    )

    if capex_max is not None:

        payback_max = (
            capex_max
            / annual_savings
        )

    else:

        payback_max = None

    return {
        "payback_min_years": payback_min,
        "payback_max_years": payback_max
    }