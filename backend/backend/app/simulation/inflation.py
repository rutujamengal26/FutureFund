import math
from decimal import Decimal, ROUND_HALF_UP

def get_monthly_compounded_value(baseline_value: float, annual_rate_pct: float, month: int) -> Decimal:
    """
    Calculates the inflated or grown value at a specific month.
    Formula: monthly_value(m) = baseline_value * (1 + r)^(m / 12)
    where r is annual_rate_pct / 100.
    """
    if baseline_value == 0:
        return Decimal('0.00')
    if annual_rate_pct < 0:
        raise ValueError("Negative annual rates are not supported in this phase.")
        
    b = float(baseline_value)
    r = float(annual_rate_pct) / 100.0
    
    # Using math.pow for fractional exponent ensures numerical stability
    factor = math.pow(1.0 + r, month / 12.0)
    
    val = b * factor
    return Decimal(str(round(val, 4))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
