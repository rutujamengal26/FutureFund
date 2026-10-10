import pytest
import math
from decimal import Decimal
from app.simulation.inflation import get_monthly_compounded_value

def test_zero_inflation():
    val = get_monthly_compounded_value(1000.0, 0.0, 6)
    assert float(val) == 1000.0

def test_monthly_compounding_reaches_annual_factor():
    val = get_monthly_compounded_value(1000.0, 10.0, 12)
    # 10% of 1000 is 100 -> 1100
    assert float(val) == 1100.0

def test_half_year_compounding():
    val = get_monthly_compounded_value(1000.0, 10.0, 6)
    expected = 1000.0 * math.pow(1.10, 0.5)
    assert float(val) == round(expected, 2)

def test_negative_rate_rejected():
    with pytest.raises(ValueError):
        get_monthly_compounded_value(1000.0, -5.0, 6)
