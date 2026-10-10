from decimal import Decimal
from typing import List, Optional, Any
from app.schemas.analysis import ProfileSchema, AssumptionsSchema
from app.schemas.simulation import UniverseConfiguration, MonthlyProjectionRecord, UniverseSummary, UniverseSimulationResult
from app.simulation.inflation import get_monthly_compounded_value
from app.financial.calculations import calculate_emi, generate_amortization_schedule

def simulate_universe(profile: ProfileSchema, config: UniverseConfiguration, assumptions: AssumptionsSchema, stress_events: Optional[List[Any]] = None) -> UniverseSimulationResult:
    # 1. Pre-calculate the fixed-rate loan amortization schedule
    if config.loan_amount_inr > 0:
        loan_schedule = generate_amortization_schedule(
            principal=config.loan_amount_inr,
            annual_interest_rate_pct=config.annual_interest_rate_pct,
            tenure_months=config.tenure_months
        )
        total_interest_full_loan = loan_schedule.total_interest
        scheduled_emi = float(calculate_emi(config.loan_amount_inr, config.annual_interest_rate_pct, config.tenure_months))
    else:
        loan_schedule = None
        total_interest_full_loan = 0.0
        scheduled_emi = 0.0

    records: List[MonthlyProjectionRecord] = []
    
    cash_balance = Decimal(str(profile.current_savings_inr))
    existing_emi = Decimal(str(profile.existing_monthly_emi_inr))
    
    cumulative_interest_paid = Decimal('0.00')
    remaining_loan_balance = Decimal('0.00')
    
    horizon = assumptions.simulation_horizon_months
    
    total_living_expenses_horizon = Decimal('0.00')
    total_income_horizon = Decimal('0.00')
    
    for month in range(horizon + 1):
        # Apply assumptions to get projected values for this month
        projected_income = get_monthly_compounded_value(profile.monthly_income_inr, assumptions.annual_income_growth_pct, month)
        projected_other_income = get_monthly_compounded_value(profile.other_income_inr, assumptions.annual_income_growth_pct, month)
        projected_rent = get_monthly_compounded_value(profile.monthly_rent_inr, assumptions.annual_rent_inflation_pct, month)
        projected_essential = get_monthly_compounded_value(profile.essential_expenses_excluding_rent_inr, assumptions.annual_essential_expense_inflation_pct, month)
        projected_variable = get_monthly_compounded_value(profile.variable_expenses_inr, assumptions.annual_variable_expense_inflation_pct, month)
        
        emergency_expense = Decimal('0.00')
        if stress_events and month > 0:
            for event in stress_events:
                if event.type == "income_reduction":
                    if event.start_month <= month < event.start_month + event.duration_months:
                        factor = Decimal(str(1 - (event.reduction_pct / 100.0)))
                        if event.applies_to in ["primary", "both"]:
                            projected_income *= factor
                        if event.applies_to in ["other", "both"]:
                            projected_other_income *= factor
                elif event.type == "income_interruption":
                    if event.start_month <= month < event.start_month + event.duration_months:
                        if event.applies_to in ["primary", "both"]:
                            projected_income = Decimal('0.00')
                        if event.applies_to in ["other", "both"]:
                            projected_other_income = Decimal('0.00')
                elif event.type == "emergency_expense":
                    if event.month == month:
                        emergency_expense += Decimal(str(event.amount_inr))
                elif event.type == "rent_increase":
                    if month >= event.start_month:
                        projected_rent *= Decimal(str(1 + (event.increase_pct / 100.0)))
                elif event.type == "essential_increase":
                    if month >= event.start_month:
                        projected_essential *= Decimal(str(1 + (event.increase_pct / 100.0)))
                elif event.type == "variable_increase":
                    if month >= event.start_month:
                        projected_variable *= Decimal(str(1 + (event.increase_pct / 100.0)))

        upfront_outflow = Decimal('0.00')
        if month == config.decision_delay_months:
            upfront_outflow = Decimal(str(config.upfront_cash_outflow_inr))
            remaining_loan_balance = Decimal(str(config.loan_amount_inr))
            
        new_emi = Decimal('0.00')
        loan_month_index = month - config.decision_delay_months
        if loan_month_index > 0 and loan_schedule and loan_month_index <= config.tenure_months:
            # We are in the repayment period for the new loan
            row = loan_schedule.schedule[loan_month_index - 1]
            new_emi = Decimal(str(row.scheduled_emi))
            remaining_loan_balance = Decimal(str(row.closing_balance))
            cumulative_interest_paid += Decimal(str(row.interest_component))
        elif loan_month_index > config.tenure_months:
            # Loan has been fully repaid
            remaining_loan_balance = Decimal('0.00')

        total_income_month = projected_income + projected_other_income
        total_living_expenses_month = projected_rent + projected_essential + projected_variable
        
        total_outflow_month = total_living_expenses_month + existing_emi + new_emi + emergency_expense
        monthly_surplus = total_income_month - total_outflow_month
        
        opening_cash = cash_balance
        
        # Month 0 calculation is the baseline state. Upfront cash happens if delay is 0.
        # Income and expenses do not affect cash balance in month 0.
        if month == 0:
            closing_cash = opening_cash - upfront_outflow
            cash_balance = closing_cash
            records.append(MonthlyProjectionRecord(
                month=0,
                projected_monthly_income_inr=float(projected_income),
                projected_other_income_inr=float(projected_other_income),
                projected_rent_inr=float(projected_rent),
                projected_essential_expenses_inr=float(projected_essential),
                projected_variable_expenses_inr=float(projected_variable),
                existing_monthly_emi_inr=float(existing_emi),
                new_monthly_emi_inr=float(new_emi),
                total_monthly_outflow_inr=float(total_outflow_month),
                monthly_surplus_inr=float(monthly_surplus),
                opening_cash_balance_inr=float(opening_cash),
                upfront_cash_outflow_inr=float(upfront_outflow),
                closing_cash_balance_inr=float(closing_cash),
                remaining_new_loan_balance_inr=float(remaining_loan_balance),
                cumulative_new_loan_interest_paid_inr=float(cumulative_interest_paid)
            ))
            continue
            
        # Normal monthly flow calculation for months 1 to horizon
        closing_cash = opening_cash - upfront_outflow + total_income_month - total_outflow_month
        cash_balance = closing_cash
        
        total_living_expenses_horizon += total_living_expenses_month
        total_income_horizon += total_income_month
        
        records.append(MonthlyProjectionRecord(
            month=month,
            projected_monthly_income_inr=float(projected_income),
            projected_other_income_inr=float(projected_other_income),
            projected_rent_inr=float(projected_rent),
            projected_essential_expenses_inr=float(projected_essential),
            projected_variable_expenses_inr=float(projected_variable),
            existing_monthly_emi_inr=float(existing_emi),
            new_monthly_emi_inr=float(new_emi),
            total_monthly_outflow_inr=float(total_outflow_month),
            monthly_surplus_inr=float(monthly_surplus),
            opening_cash_balance_inr=float(opening_cash),
            upfront_cash_outflow_inr=float(upfront_outflow),
            closing_cash_balance_inr=float(closing_cash),
            remaining_new_loan_balance_inr=float(remaining_loan_balance),
            cumulative_new_loan_interest_paid_inr=float(cumulative_interest_paid)
        ))

    # Compile the summary
    min_cash_record = min(records, key=lambda r: r.closing_cash_balance_inr)
    
    summary = UniverseSummary(
        universe_id=config.universe_id,
        display_name=config.display_name,
        configured_loan_amount_inr=config.loan_amount_inr,
        decision_start_month=config.decision_delay_months,
        scheduled_emi_inr=scheduled_emi,
        total_interest_full_loan_inr=total_interest_full_loan,
        interest_paid_within_horizon_inr=float(cumulative_interest_paid),
        monthly_surplus_start_inr=records[1].monthly_surplus_inr if horizon >= 1 else records[0].monthly_surplus_inr,
        monthly_surplus_end_inr=records[-1].monthly_surplus_inr,
        ending_projected_cash_balance_inr=records[-1].closing_cash_balance_inr,
        minimum_projected_cash_balance_inr=min_cash_record.closing_cash_balance_inr,
        month_of_minimum_cash_balance=min_cash_record.month,
        remaining_loan_balance_at_horizon_inr=records[-1].remaining_new_loan_balance_inr,
        total_projected_living_expenses_inr=float(total_living_expenses_horizon),
        total_projected_income_inr=float(total_income_horizon),
        assumptions=assumptions
    )
    
    return UniverseSimulationResult(summary=summary, projection=records)
