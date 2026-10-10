import pytest
import math
from decimal import Decimal
from app.financial.calculations import calculate_emi

def test_calculate_emi_standard():
    # 5L @ 12% for 36 months should be ~16607.15
    emi = calculate_emi(500000, 12.0, 36)
    assert float(emi) == 16607.15

def test_calculate_emi_zero_interest():
    # 120000 @ 0% for 12 months = 10000
    emi = calculate_emi(120000, 0.0, 12)
    assert float(emi) == 10000.0

def test_calculate_emi_one_month():
    emi = calculate_emi(1000, 12.0, 1)
    # interest = 10
    assert float(emi) == 1010.0

def test_calculate_emi_invalid_principal():
    with pytest.raises(ValueError):
        calculate_emi(-5000, 12.0, 36)
    with pytest.raises(ValueError):
        calculate_emi(0, 12.0, 36)
    with pytest.raises(ValueError):
        calculate_emi(math.nan, 12.0, 36)

def test_calculate_emi_invalid_tenure():
    with pytest.raises(ValueError):
        calculate_emi(50000, 12.0, -5)
    with pytest.raises(ValueError):
        calculate_emi(50000, 12.0, 0)
    with pytest.raises(ValueError):
        calculate_emi(50000, 12.0, 2.5) # type: ignore

def test_calculate_emi_invalid_interest_rate():
    with pytest.raises(ValueError):
        calculate_emi(50000, -1.0, 36)
    with pytest.raises(ValueError):
        calculate_emi(50000, math.inf, 36)
