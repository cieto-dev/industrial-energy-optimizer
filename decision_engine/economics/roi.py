def calculate_roi(
    capex_min,
    capex_max,
    annual_savings,
    lifetime_years
):
    """
    Calculate simple lifetime ROI as a range.

    Total savings:
        annual savings × lifetime

    Net return:
        total savings - CAPEX

    ROI:
        (net return / CAPEX) × 100
    """

    if annual_savings <= 0:

        return {
            "roi_min_percent": None,
            "roi_max_percent": None
        }

    if lifetime_years is None:
        return {
            "roi_min_percent": None,
            "roi_max_percent": None
        }

    if lifetime_years <= 0:
        raise ValueError(
            "Lifetime must be greater than zero."
        )

    if capex_min is None:
        raise ValueError(
            "capex_min is required."
        )

    total_savings = (
        annual_savings
        * lifetime_years
    )

    # Worst case:
    # maximum CAPEX
    if capex_max is not None:

        roi_min = (
            (total_savings - capex_max)
            / capex_max
        ) * 100

    else:

        roi_min = None

    # Best case:
    # minimum CAPEX
    roi_max = (
        (total_savings - capex_min)
        / capex_min
    ) * 100

    return {
        "roi_min_percent": roi_min,
        "roi_max_percent": roi_max
    }