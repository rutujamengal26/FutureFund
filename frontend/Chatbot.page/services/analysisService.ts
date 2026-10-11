import { fetchAPI } from '../lib/api';

export interface FinancialProfile { profileId?: string; income?: string; expenses?: string; savings?: string; emi?: string; name?: string }
export interface DecisionRequest { question: string; profile?: FinancialProfile; conversationId?: string; transcript?: string }
export interface StressTestResult { incomeDrop: string; emergencyExpense: string; expenseIncrease: string; cashFlowImpact: string; savingsImpact: string; risk: 'Moderate' | 'High'; assumptions: string[] }
export interface UniverseResult { name: string; monthlyEmi: string; savings: string; netWorth: string; cashFlow: string; debtRemaining: string; tradeoff: string; graph?: { savings: number[]; expenses: number[] } }
export interface AutoPivotResult { name: string; monthlyEmi: string; totalInterest: string; savings: string; netWorth: string; risk: string }
export interface AISecondOpinionResult { summary: string; risks: string[]; assumptions: string[]; tradeoffs: string[]; resilience: string }
export interface DecisionAnalysis { id: string; question: string; summary: string; answer: string; createdAt: string; availableAnalyses: string[]; stressTest: StressTestResult; futures: UniverseResult[]; pivots: AutoPivotResult[]; secondOpinion: AISecondOpinionResult; graph?: { savings: number[]; expenses: number[] } }

export function mapBackendResponseToDecisionAnalysis(request: DecisionRequest, response: any): DecisionAnalysis {
  if (response.status === 'CLARIFICATION_REQUIRED') {
    return {
      id: response.analysis_id || crypto.randomUUID(),
      question: request.question,
      summary: 'Clarification Needed',
      answer: response.parsed_result?.clarification_question || 'We need more details to analyze this decision.',
      createdAt: new Date().toISOString(),
      availableAnalyses: [],
      stressTest: { incomeDrop: '', emergencyExpense: '', expenseIncrease: '', cashFlowImpact: '', savingsImpact: '', risk: 'Moderate', assumptions: [] },
      futures: [],
      pivots: [],
      secondOpinion: { summary: '', risks: [], assumptions: [], tradeoffs: [], resilience: '' }
    };
  }

  const futures: UniverseResult[] = (response.universes || []).map((u: any, index: number) => {
    let univGraph: { savings: number[]; expenses: number[] } | undefined;
    if (u.projection && Array.isArray(u.projection) && u.projection.length > 0) {
      const sArr = u.projection.map((p: any) => Math.round(p.closing_cash_balance_inr || 0));
      const eArr = u.projection.map((p: any) => {
        const living = (p.projected_rent_inr || 0) + (p.projected_essential_expenses_inr || 0) + (p.projected_variable_expenses_inr || 0);
        return Math.round(living > 0 ? living : (p.total_monthly_outflow_inr || 0));
      });
      univGraph = { savings: sArr, expenses: eArr };
    } else if (request.profile) {
      const emi = u.summary?.scheduled_emi_inr || 0;
      const savings = parseFloat(request.profile.savings?.toString() || '0');
      const income = parseFloat(request.profile.income?.toString() || '0');
      const expenses = parseFloat(request.profile.expenses?.toString() || '0');
      
      const tenureMonths = response.validated_decision?.tenure_months || 36;
      let currentSavings = savings;
      let currentExpenses = expenses;
      const savingsArray = [currentSavings];
      const expensesArray = [currentExpenses];
      
      const delay = u.summary?.decision_start_month ?? (u.summary?.universe_id === 'wait_prepare' ? 6 : (index === 1 ? 6 : 0));
      for (let m = 1; m <= tenureMonths; m++) {
        currentExpenses = currentExpenses * Math.pow(1.05, 1 / 12);
        const monthlyEmiVal = m > delay ? emi : 0;
        currentSavings += (income - currentExpenses - monthlyEmiVal);
        savingsArray.push(Math.round(currentSavings));
        expensesArray.push(Math.round(currentExpenses));
      }
      univGraph = { savings: savingsArray, expenses: expensesArray };
    }

    return {
      name: u.summary?.display_name || u.summary?.universe_id || 'Universe',
      monthlyEmi: `₹${u.summary?.scheduled_emi_inr || 0}`,
      savings: `₹${u.summary?.ending_projected_cash_balance_inr || 0}`,
      netWorth: `₹${u.summary?.ending_projected_cash_balance_inr || 0}`,
      cashFlow: `₹${u.summary?.monthly_surplus_start_inr || 0}`,
      debtRemaining: `₹${u.summary?.remaining_loan_balance_at_horizon_inr || 0}`,
      tradeoff: '',
      graph: univGraph
    };
  });

  if (futures.length === 0) {
     futures.push({ name: 'Act Now', monthlyEmi: '₹0', savings: '₹0', netWorth: '₹0', cashFlow: '₹0', debtRemaining: '₹0', tradeoff: '' });
     futures.push({ name: 'Wait & Prepare', monthlyEmi: '₹0', savings: '₹0', netWorth: '₹0', cashFlow: '₹0', debtRemaining: '₹0', tradeoff: '' });
     futures.push({ name: 'Reimagine the Plan', monthlyEmi: '₹0', savings: '₹0', netWorth: '₹0', cashFlow: '₹0', debtRemaining: '₹0', tradeoff: '' });
  }

  let secondOpinion: AISecondOpinionResult = { summary: '', risks: [], assumptions: [], tradeoffs: [], resilience: '' };
  if (response.second_opinion) {
      secondOpinion.summary = response.second_opinion.summary || '';
  } else {
     secondOpinion.summary = "Second opinion not available.";
  }

  const parsedIncome = request.profile?.income ? parseFloat(request.profile.income.toString()) : 0;
  const dynamicEmergency = parsedIncome > 0 ? `₹${(parsedIncome / 2).toLocaleString()}` : '₹30,000';
  let stressTest: StressTestResult = { incomeDrop: '-20%', emergencyExpense: dynamicEmergency, expenseIncrease: '+20%', cashFlowImpact: 'N/A', savingsImpact: 'N/A', risk: 'Moderate', assumptions: ['20% income reduction for 6 months', '₹50,000 emergency medical expense in month 3', '10% permanent increase in essential living expenses'] };
  const st = response.stress_tests?.act_now?.summary || response.stress_tests?.baseline?.summary;
  if (st) {
    stressTest.cashFlowImpact = `₹${st.stressed_monthly_surplus_at_horizon_inr || 0}`;
    stressTest.savingsImpact = `₹${st.stressed_ending_cash_balance_inr || 0}`;
    stressTest.risk = st.first_stressed_reserve_breach_month ? 'High' : 'Moderate';
  }

  let answerText = 'Your financial decision has been analyzed across three universes.';
  let graphData: { savings: number[]; expenses: number[] } | undefined;
  
  if (request.profile && response.universes) {
    const actNow = response.universes.find((u: any) => u.summary?.universe_id === 'act_now');
    if (actNow) {
       const emi = actNow.summary.scheduled_emi_inr || 0;
       const savings = parseFloat(request.profile.savings?.toString() || '0');
       const income = parseFloat(request.profile.income?.toString() || '0');
       const expenses = parseFloat(request.profile.expenses?.toString() || '0');
       
       const tenureMonths = response.validated_decision?.tenure_months || 36;
       let currentSavings = savings;
       let currentExpenses = expenses;
       const savingsArray = [currentSavings];
       const expensesArray = [currentExpenses];
       
       for(let m = 1; m <= tenureMonths; m++) {
           currentExpenses = currentExpenses * Math.pow(1.05, 1/12);
           currentSavings += (income - currentExpenses - emi);
           savingsArray.push(Math.round(currentSavings));
           expensesArray.push(Math.round(currentExpenses));
       }
       
       let projectionText = "";
       for(let m = 12; m <= tenureMonths; m += 12) {
           projectionText += `• Savings after ${m} months: ₹${savingsArray[m].toLocaleString()}\n`;
       }
       if (tenureMonths % 12 !== 0 && tenureMonths > 0) {
           projectionText += `• Savings after ${tenureMonths} months: ₹${savingsArray[tenureMonths].toLocaleString()}\n`;
       }
       
       answerText = `Here is your financial profile and analysis:\n\n` +
       `• Salary: ₹${income.toLocaleString()}\n` +
       `• Expenses: ₹${expenses.toLocaleString()}\n` +
       `• Current Savings: ₹${savings.toLocaleString()}\n\n` +
       `Based on your decision, your calculated EMI is ₹${Math.round(emi).toLocaleString()}.\n\n` +
       `**Savings Projection:**\n${projectionText}`;
       
       graphData = { savings: savingsArray, expenses: expensesArray };
    }
  }

  return {
    id: response.analysis_id || crypto.randomUUID(),
    question: request.question,
    summary: 'Analysis Complete',
    answer: answerText,
    createdAt: new Date().toISOString(),
    availableAnalyses: ['futures', 'stress', 'opinion'],
    stressTest,
    futures,
    pivots: [],
    secondOpinion,
    graph: graphData
  };
}

/** Adapter that connects to the real POST /api/v1/decisions/analyze endpoint. */
export async function analyzeDecision(request: DecisionRequest): Promise<DecisionAnalysis> {
  const profilePayload = request.profile ? {
    monthly_income_inr: request.profile.income ? parseFloat(request.profile.income) : 0,
    monthly_rent_inr: request.profile.expenses ? parseFloat(request.profile.expenses) * 0.4 : 0,
    essential_expenses_excluding_rent_inr: request.profile.expenses ? parseFloat(request.profile.expenses) * 0.4 : 0,
    variable_expenses_inr: request.profile.expenses ? parseFloat(request.profile.expenses) * 0.2 : 0,
    current_savings_inr: request.profile.savings ? parseFloat(request.profile.savings) : 0,
    existing_monthly_emi_inr: request.profile.emi ? parseFloat(request.profile.emi) : 0,
    other_income_inr: 0
  } : undefined;

  const payload: any = {
    text: request.transcript || request.question,
    profile: profilePayload,
    assumptions: {
      simulation_horizon_months: 36,
      annual_rent_inflation_pct: 5.0,
      annual_essential_expense_inflation_pct: 6.0,
      annual_variable_expense_inflation_pct: 4.0,
      annual_income_growth_pct: 10.0
    }
  };

  const response = await fetchAPI('/api/v1/decisions/analyze', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  return mapBackendResponseToDecisionAnalysis(request, response);
}
