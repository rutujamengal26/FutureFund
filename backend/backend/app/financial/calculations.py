from decimal import Decimal, ROUND_HALF_UP
from typing import List
import math
from app.schemas.financial import AmortizationRow, AmortizationSchedule, FinancialPosition
from app.schemas.analysis import ProfileSchema

def _validate_loan_inputs(principal: float, annual_interest_rate_pct: float, tenure_months: int):
    if not isinstance(principal, (int, float, Decimal)) or principal <= 0 or math.isnan(principal) or math.isinf(principal):
        raise ValueError("Principal must be a positive finite number.")
    if not isinstance(tenure_months, int) or tenure_months <= 0:
        raise ValueError("Tenure must be a positive integer.")
    if not isinstance(annual_interest_rate_pct, (int, float, Decimal)) or annual_interest_rate_pct < 0 or math.isnan(annual_interest_rate_pct) or math.isinf(annual_interest_rate_pct):
        raise ValueError("Annual interest rate must be a non-negative finite number.")

def calculate_emi(principal: float, annual_interest_rate_pct: float, tenure_months: int) -> Decimal:
    _validate_loan_inputs(principal, annual_interest_rate_pct, tenure_months)
    
    p = Decimal(str(principal))
    r_annual = Decimal(str(annual_interest_rate_pct))
    
    if r_annual == Decimal('0'):
        emi = p / Decimal(tenure_months)
    else:
        r_monthly = (r_annual / Decimal('100')) / Decimal('12')
        n = Decimal(tenure_months)
        # EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
        factor = (Decimal('1') + r_monthly) ** n
        emi = p * r_monthly * factor / (factor - Decimal('1'))
        
    return emi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def generate_amortization_schedule(principal: float, annual_interest_rate_pct: float, tenure_months: int) -> AmortizationSchedule:
    _validate_loan_inputs(principal, annual_interest_rate_pct, tenure_months)
    emi = calculate_emi(principal, annual_interest_rate_pct, tenure_months)
    
    p = Decimal(str(principal))
    r_annual = Decimal(str(annual_interest_rate_pct))
    r_monthly = (r_annual / Decimal('100')) / Decimal('12') if r_annual > Decimal('0') else Decimal('0')
    
    balance = p
    schedule: List[AmortizationRow] = []
    total_paid = Decimal('0')
    total_interest = Decimal('0')
    
    for month in range(1, tenure_months + 1):
        interest_for_month = (balance * r_monthly).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Adjust last payment or overpayment
        if month == tenure_months:
            principal_for_month = balance
            payment_for_month = principal_for_month + interest_for_month
        else:
            payment_for_month = emi
            principal_for_month = payment_for_month - interest_for_month
            
            # Prevent overpayment if balance is smaller than scheduled principal (rare but possible due to rounding)
            if principal_for_month > balance:
                principal_for_month = balance
                payment_for_month = principal_for_month + interest_for_month
                
        balance -= principal_for_month
        if balance < Decimal('0'):
            balance = Decimal('0')
            
        schedule.append(AmortizationRow(
            month=month,
            opening_balance=float((balance + principal_for_month).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            scheduled_emi=float(payment_for_month.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            interest_component=float(interest_for_month),
            principal_component=float(principal_for_month.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            closing_balance=float(balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        ))
        
        total_paid += payment_for_month
        total_interest += interest_for_month
        
    return AmortizationSchedule(
        schedule=schedule,
        total_paid=float(total_paid.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
        total_interest=float(total_interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
        final_balance=float(balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    )

def calculate_financial_position(profile: ProfileSchema, proposed_emi: float = 0.0) -> FinancialPosition:
    total_income = Decimal(str(profile.monthly_income_inr)) + Decimal(str(profile.other_income_inr))
    # Rent is separate, don't double count
    living_expenses = Decimal(str(profile.monthly_rent_inr)) + Decimal(str(profile.essential_expenses_excluding_rent_inr)) + Decimal(str(profile.variable_expenses_inr))
    existing_emi = Decimal(str(profile.existing_monthly_emi_inr))
    current_outflow = living_expenses + existing_emi
    current_surplus = total_income - current_outflow
    
    proposed_emi_dec = Decimal(str(proposed_emi))
    surplus_after_proposed = current_surplus - proposed_emi_dec
    total_debt_payments = existing_emi + proposed_emi_dec
    
    if total_income > Decimal('0'):
        dti = (total_debt_payments / total_income) * Decimal('100')
    else:
        dti = None
        
    savings = Decimal(str(profile.current_savings_inr))
    proposed_total_outflow = current_outflow + proposed_emi_dec
    
    reserve_coverage_current = (savings / current_outflow) if current_outflow > Decimal('0') else None
    reserve_coverage_proposed = (savings / proposed_total_outflow) if proposed_total_outflow > Decimal('0') else None

    def _to_float(dec_val):
        if dec_val is None:
            return None
        return float(dec_val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
    return FinancialPosition(
        total_monthly_income_inr=_to_float(total_income),
        current_monthly_living_expenses_inr=_to_float(living_expenses),
        current_monthly_outflow_inr=_to_float(current_outflow),
        current_monthly_surplus_inr=_to_float(current_surplus),
        proposed_loan_emi_inr=_to_float(proposed_emi_dec),
        monthly_surplus_after_proposed_loan_inr=_to_float(surplus_after_proposed),
        total_monthly_debt_payments_inr=_to_float(total_debt_payments),
        debt_to_income_ratio_pct=_to_float(dti),
        reserve_coverage_months_current=_to_float(reserve_coverage_current),
        reserve_coverage_months_proposed=_to_float(reserve_coverage_proposed)
    )
