def calculate_npv(
    annual_savings: float | None,
    discount_rate_pct: float | None,
    lifetime_years: float | None,
    capex_estimate: float | None
) -> float | None:
    """
    Calculate the Net Present Value (NPV) of a project.

    NPV = Sum(Annual_savings / (1 + r)^t) - CAPEX_estimate
    where:
    - r = discount rate (decimal)
    - t = year (from 1 to lifetime_years)

    Returns None if any of the required inputs are missing or invalid.
    """
    if annual_savings is None or annual_savings <= 0:
        return None
        
    if discount_rate_pct is None or discount_rate_pct < 0:
        return None
        
    if lifetime_years is None or lifetime_years <= 0:
        return None
        
    if capex_estimate is None or capex_estimate < 0:
        return None

    r = discount_rate_pct / 100.0
    lifetime_int = int(lifetime_years)
    
    # Calculate present value of savings
    pv_savings = sum(
        annual_savings / ((1 + r) ** t)
        for t in range(1, lifetime_int + 1)
    )
    
    return pv_savings - capex_estimate
