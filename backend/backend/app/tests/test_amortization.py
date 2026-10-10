import pytest
from app.financial.calculations import generate_amortization_schedule
import math

def test_amortization_standard():
    res = generate_amortization_schedule(500000, 12.0, 36)
    
    # Check total payments and final balance
    assert res.final_balance == 0.0
    assert len(res.schedule) == 36
    
    total_principal_repaid = sum(row.principal_component for row in res.schedule)
    assert math.isclose(total_principal_repaid, 500000.0, abs_tol=0.02)
    
    total_interest_charged = sum(row.interest_component for row in res.schedule)
    assert math.isclose(res.total_interest, total_interest_charged, abs_tol=0.02)
    
    assert math.isclose(res.total_paid, res.total_interest + 500000.0, abs_tol=0.02)

def test_amortization_zero_interest():
    res = generate_amortization_schedule(120000, 0.0, 12)
    assert res.final_balance == 0.0
    assert res.total_interest == 0.0
    assert res.total_paid == 120000.0
    assert len(res.schedule) == 12
    for row in res.schedule:
        assert row.scheduled_emi == 10000.0
        assert row.interest_component == 0.0
        assert row.principal_component == 10000.0

def test_amortization_no_negative_balance():
    # Test a small loan with potential rounding issues
    res = generate_amortization_schedule(100, 10.0, 3)
    assert res.final_balance == 0.0
    for row in res.schedule:
        assert row.closing_balance >= 0.0
